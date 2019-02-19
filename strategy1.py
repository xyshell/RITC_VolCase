from RIT_api_VolCase import VolCaseClient
from apiUlt import url, apikey
from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_vollib.black_scholes_merton.greeks.analytical import delta, vega
import pandas as pd
import re 
import time 

''' dealing with hill & valley implied vol'''

# Case Params
r = 0
q = 0

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
    S_ask = api.price(ticker="RTM",kind='ask')
    S_bid = api.price(ticker="RTM",kind='bid')
    S_last = api.price(ticker="RTM",kind='last')
    ava_ticker = list(prc_bid.index)
    call_list = [i for i in ava_ticker if 'C' in i]
    put_list = list(reversed([i for i in ava_ticker if 'P' in i]))

    # log
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
            print(e)
            iv = 0
        vol_dict[call] = iv
    for put in put_list:
        K = int(re.findall(r'\d+', put)[0])
        flag = 'p'
        try:
            iv = implied_volatility(prc_ask[put], S_ask, K, t, r, flag)
        except Exception as e:
            print(e)
            iv = 0
        vol_dict[put] = iv
    iv_s = pd.Series(vol_dict)
    
    # computation -- stats of implied vol
    hill_list = list(iv_s.index[iv_s >= iv_s.quantile(.90)])
    valley_list = list(iv_s.index[iv_s == iv_s.min()])
    plain_list = list(iv_s.index[
        (iv_s <= iv_s.quantile(.80)) & (iv_s >= iv_s.quantile(.20))])
    exculde_list = ['RTM45C',"RTM45P"]
    hill_signal = list(set(hill_list) - set(exculde_list))
    valley_signal = list(set(hill_list) - set(exculde_list))
    new_hill = list(set(hill_signal) - set(pos_ticker))
    new_valley = list(set(valley_signal) - set(pos_ticker))

    # signals and execution
    # short hills
    if len(pos_ticker) == 0 and len(new_hill) != 0:
        for short_ticker in new_hill:
            api.market_sell(short_ticker, 50)
    elif len(pos_ticker) == 2 and len(new_hill) != 0:
        if len(new_hill) == 1:
            api.market_sell(new_hill[0], 50)
        elif len(new_hill) == 2:
            for short_ticker in new_hill:
                api.market_sell(short_ticker, 50)
    elif len(pos_ticker) >= 3:
        pass
    # long valleys
    if len(new_valley) != 0:
        api.market_buy(valley_signal[0], 50)

    # close positions
    for option_ticker in pos_ticker[1:]:
        if option_ticker in plain_list:
            api.close_pos(option_ticker)


    # hedge
    # vega hedge
    pos = api.position()
    pos_ticker = list(pos[pos!=0].index)
    sum_vega = 0
    for option_ticker in pos_ticker:
        if 'C' in option_ticker:
            flag = 'c'
        elif 'P' in option_ticker:
            flag = 'p'
        else:
            continue
        K = int(re.findall(r'\d+', option_ticker)[0])
        sigma = iv_s[option_ticker]
        opt_vega = vega(flag, S_last, K, t, r, sigma, q)
        sum_vega +=  pos[option_ticker] * opt_vega

    if sum_vega > 0:
        opt_ticker = list(iv_s.index[iv_s == iv_s.median])[0]
        if 'C' in opt_ticker:
            flag = 'c'
        elif 'P' in opt_ticker:
            flag = 'p'
        K = int(re.findall(r'\d+', opt_ticker)[0])
        sigma = iv_s[opt_ticker]
        heg_vega = vega(flag, S_last, K, t, r, sigma, q)
        api.market_sell(opt_ticker, sum_vega / heg_vega)


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
