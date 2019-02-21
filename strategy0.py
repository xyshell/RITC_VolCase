from RIT_api_VolCase import VolCaseClient
from apiUlt import url, apikey
from stratUlt import *
from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_vollib.black_scholes_merton.greeks.analytical import delta
import pandas as pd
import re 
import time 

# Case Params
rng_d = 0.195
rng_u = 0.205

# Waiting for start
api = VolCaseClient(url, apikey)
while api.case_status() == False:
    time.sleep(0.2)
    pass 

# case begins
i = 0
while api.case_status() == True:

    # skip same tick
    if i == 0:
        now_tick = api.case_tick()[0][0]
        i = 1
    else:
        if api.case_tick()[0][0] == now_tick:
            continue
        else:
            now_tick = api.case_tick()[0][0]

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

    if now_tick in vol_time:
        vol_news = api.news_kind("Announcement",True)["body"]
        real_vol = int(re.findall(r"\d+", vol_news.values[0])[0]) / 100
    
    # define safe zone
    if now_tick <= 450:
        rng_d = real_vol - 0.01
        rng_u = real_vol + 0.01
    else:
        rng_d = real_vol - 0.1
        rng_u = real_vol + 0.1
    if now_tick in rng_time:
        range_news = api.news_kind("News",True)["body"]
        rng_d = int(re.findall(r"\d+", range_news.values[0])[0]) / 100
        rng_u = int(re.findall(r"\d+", range_news.values[0])[1]) / 100


    # log time
    print(now_tick) 
    t = (600 - now_tick)/ 30/ 252 

    # computation -- implied vol
    vol_dict = {}
    for call in call_list:
        K = int(re.findall(r'\d+', call)[0])
        flag = 'c'
        try:
            iv = implied_volatility(prc_ask[call], S_bid, K, t, r, flag)
        except Exception as e:
            iv = 0
        vol_dict[call] = iv
    for put in put_list:
        K = int(re.findall(r'\d+', put)[0])
        flag = 'p'
        try:
            iv = implied_volatility(prc_ask[put], S_ask, K, t, r, flag)
        except Exception as e:
            iv = 0
        vol_dict[put] = iv
    iv_s = pd.Series(vol_dict)

    # find at-the-money option and its iv
    at_money_opt = []
    for i in iv_s.index:
        if str(int(round(S_last))) in i:
            at_money_opt.append(i)
            print("real_vol", real_vol, i, "iv", iv_s[i])
    
    now_iv = iv_s[at_money_opt].mean()
    if now_iv > rng_u:
        for opt in at_money_opt:
            api.market_sell(opt, int((now_iv - rng_u)/0.1*5+1))
        print("sell straddle at", prc_bid[at_money_opt].sum(), "by", int((now_iv - rng_u)/0.1*5+1))
    elif now_iv < rng_d:
        for opt in at_money_opt:
            api.market_buy(opt, int((rng_d - now_iv)/0.1*5+1))
        print("buy straddle at", prc_ask[at_money_opt].sum(), "by", int((rng_d - now_iv)/0.1*5+1))
    else:
        for ticker in pos_ticker:
            amount = api.close_pos(ticker)
            print("close", ticker, "by", amount)

    # hedge
    # vega hedge
    # pos = api.position()
    # pos_ticker = list(pos[pos!=0].index)
    # sum_vega = 0
    # for option_ticker in pos_ticker:
    #     if 'C' in option_ticker:
    #         flag = 'c'
    #     elif 'P' in option_ticker:
    #         flag = 'p'
    #     else:
    #         continue
    #     K = int(re.findall(r'\d+', option_ticker)[0])
    #     sigma = iv_s[option_ticker]
    #     opt_vega = vega(flag, S_last, K, t, r, sigma, q)
    #     sum_vega +=  pos[option_ticker] * opt_vega

    # opt_ticker = list(iv_s.index[
    #     (iv_s >= iv_s.quantile(.45)) & (iv_s <= iv_s.quantile(.55))])[0]
    # if 'C' in opt_ticker:
    #     flag = 'c'
    # elif 'P' in opt_ticker:
    #     flag = 'p'
    # K = int(re.findall(r'\d+', opt_ticker)[0])
    # sigma = iv_s[opt_ticker]
    # heg_vega = vega(flag, S_last, K, t, r, sigma, q)
    # if sum_vega > 0:
    #     api.market_sell(opt_ticker, sum_vega / heg_vega)
    # elif sum_vega < 0:
    #     api.market_buy(opt_ticker, -sum_vega / heg_vega)

    # delta hedge
    pos = api.position()
    pos_ticker = list(pos[pos!=0].index)
    sum_delta = 0
    for option_ticker in pos_ticker:
        if 'C' in option_ticker:
            flag = 'c'
        elif 'P' in option_ticker:
            flag = 'p'
        else:
            sum_delta += pos[option_ticker] * 1
            continue
        K = int(re.findall(r'\d+', option_ticker)[0])
        sigma = iv_s[option_ticker]
        opt_delta = delta(flag, S_last, K, t, r, sigma, q)
        sum_delta +=  pos[option_ticker] * 100 * opt_delta
    if sum_delta > 0:
        api.market_sell("RTM", sum_delta)
    elif sum_delta < 0:
        api.market_buy("RTM", -sum_delta)
    else:
        pass


    # feedbacks

    pass
