from RIT_api_VolCase import VolCaseClient
from apiUlt import url, apikey
from stratUlt import ava_ticker, c2p_dict, p2c_dict
from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_vollib.black_scholes_merton.greeks.analytical import delta
import numpy as np
import pandas as pd
import re 
import time 

# Case Params
r = 0   # risk free rate
q = 0   # dividend rate
real_vol = 0.2 # real volatility at the beginning 
rng_time = np.concatenate(
    (np.arange(75,150), np.arange(225, 300), np.arange(375, 450))) # efficient predicting zone

# Strat Params
alpha = 30 # order intensity
safe_rng = 0.1 # safe range width
rng_d = real_vol - safe_rng # downside safe zone
rng_u = real_vol + safe_rng # upside safe zone

# Connect and Wait for start
api = VolCaseClient(url, apikey) 
while api.case_status() == False:
    time.sleep(0.2)

# Case begins
now_tick = api.case_tick()[0][0]
while api.case_status() == True:

    # skip same tick
    if api.case_tick()[0][0] == now_tick:
        continue
    else:
        now_tick = api.case_tick()[0][0]

    print(now_tick) 
    t = (600 - now_tick)/ 30/ 252 # time to maturity

    # get data
    pos = api.position()
    pos_ticker = list(pos[pos!=0].index)
    prc_bid = api.price(kind='bid')
    prc_ask = api.price(kind='ask')
    prc_last = api.price(kind='last')
    S_ask = api.price(ticker="RTM",kind='ask')
    S_bid = api.price(ticker="RTM",kind='bid')
    S_last = api.price(ticker="RTM",kind='last')
    call_list = [i for i in ava_ticker if 'C' in i]
    put_list = [i for i in ava_ticker if 'P' in i]

    try:
        vol_news = api.news_kind("Announcement",is_last=True)["body"]
        real_vol = int(re.findall(r"\d+", vol_news.values[0])[0]) / 100
    except:
        pass

    # define safe zone piecewise
    if now_tick <= 450:
        rng_d = real_vol - 0.01
        rng_u = real_vol + 0.01
    else:
        rng_d = real_vol - 0.1
        rng_u = real_vol + 0.1
    if now_tick in rng_time:
        range_news = api.news_kind("News",is_last=True)["body"]
        rng_d = int(re.findall(r"\d+", range_news.values[0])[0]) / 100
        rng_u = int(re.findall(r"\d+", range_news.values[0])[1]) / 100
    
    # computation -- implied vol
    vol_dict = {}
    for call in call_list:
        K = int(re.findall(r'\d+', call)[0])
        flag = 'c'
        try:
            iv = implied_volatility(prc_last[call], S_last, K, t, r, flag)
        except Exception:
            iv = 0
        vol_dict[call] = iv
    for put in put_list:
        K = int(re.findall(r'\d+', put)[0])
        flag = 'p'
        try:
            iv = implied_volatility(prc_last[put], S_last, K, t, r, flag)
        except Exception:
            iv = 0
        vol_dict[put] = iv
    iv_s = pd.Series(vol_dict)

    # find at-the-money option and its iv
    at_money_opt = []
    for i in iv_s.index:
        if str(int(round(S_last))) in i:
            at_money_opt.append(i)
    now_iv = iv_s[at_money_opt].mean()
    print("rv =", real_vol,  "iv =", round(now_iv,2), "safe range", round(rng_d,2), "~", round(rng_u,2))
    if now_iv > rng_u:
        amount = int((now_iv - rng_u)/0.1*alpha+1) 
        for opt in at_money_opt:
            api.market_sell(opt, amount)
        exec_prc = prc_bid[at_money_opt].sum()
        print("sell straddle at", round(exec_prc,2), "by", amount)
    elif now_iv < rng_d:
        amount =int((rng_d - now_iv)/0.1*alpha+1)
        for opt in at_money_opt:
            api.market_buy(opt, amount)
        exec_prc = prc_ask[at_money_opt].sum()
        print("buy straddle at", round(exec_prc,2), "by", amount)
    else:
        for ticker in pos_ticker:
            amount = api.close_pos(ticker)
            print("close", ticker, "by", amount)

    # hedge
    # delta hedge
    pos = api.position()
    pos_ticker = list(pos[pos!=0].index)
    sum_delta = 0
    for opt_ticker in pos_ticker:
        if 'C' in opt_ticker:
            flag = 'c'
        elif 'P' in opt_ticker:
            flag = 'p'
        else:
            sum_delta += pos[opt_ticker] * 1
            continue
        K = int(re.findall(r'\d+', opt_ticker)[0])
        if opt_ticker in call_list:
            sigma = iv_s[opt_ticker]
        elif opt_ticker in put_list:
            sigma = iv_s[opt_ticker]
        opt_delta = delta(flag, S_last, K, t, r, sigma, q)
        sum_delta +=  pos[opt_ticker] * 100 * opt_delta
    if sum_delta > 0:
        while sum_delta > 10000:
            api.market_sell("RTM", 10000)
            sum_delta -= 10000
        api.market_sell("RTM", sum_delta)
    elif sum_delta < 0:
        while sum_delta < -10000:
            api.market_buy("RTM", 10000)
            sum_delta += 10000
        api.market_buy("RTM", -sum_delta)

    pass
