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

c2p_dict = {
    'RTM45C' : 'RTM45P', 'RTM46C' : 'RTM46P', 'RTM47C' : 'RTM47P',
    'RTM48C' : 'RTM48P', 'RTM49C' : 'RTM49P', 'RTM50C' : 'RTM50P',
    'RTM51C' : 'RTM51P', 'RTM52C' : 'RTM52P', 'RTM53C' : 'RTM53P',
    'RTM54C' : 'RTM54P',
}
p2c_dict = {
    'RTM45P' : 'RTM45C', 'RTM46P' : 'RTM46C', 'RTM47P' : 'RTM47C',
    'RTM48P' : 'RTM48C', 'RTM49P' : 'RTM49C', 'RTM50P' : 'RTM50C',
    'RTM51P' : 'RTM51C', 'RTM52P' : 'RTM52C', 'RTM53P' : 'RTM53C',
    'RTM54P' : 'RTM54C',
}

# Waiting for start
api = VolCaseClient(url, apikey)
while api.case_status() == False:
    time.sleep(0.2)
    pass 

# case begins
i = 0
ann_vol = 0.2
delta_limit = api.news("Delta")
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
    ava_ticker = list(prc_bid.index)
    call_list = [i for i in ava_ticker if 'C' in i]
    put_list = [i for i in ava_ticker if 'P' in i]

    if now_tick == [150, 300, 450]:
        vol_news = api.news("Announcement",True)["Body"]
        ann_vol = int(re.findall(r"\d+", vol_news)[0])
    t = (600 - now_tick)/ 30/ 252

    # log
    print(now_tick)
    
    # computation -- implied vol
    callvol_dict_u = {}
    callvol_dict_d = {}
    callvol_dict_m = {}
    putvol_dict_u = {}
    putvol_dict_d = {}
    putvol_dict_m = {}
    for call in call_list:
        K = int(re.findall(r'\d+', call)[0])
        flag = 'c'
        try:
            iv_u = implied_volatility(prc_last[call]+0.02, S_last-0.02, K, t, r, flag)
        except Exception as e:
            print(e)
            iv_u = 0
        try:
            iv_d = implied_volatility(prc_last[call]-0.02, S_last+0.02, K, t, r, flag)
        except Exception as e:
            print(e)
            iv_d = 0
        try:
            iv_m = implied_volatility(prc_last[call], S_last, K, t, r, flag)
        except Exception as e:
            print(e)
            iv_m = 0
        callvol_dict_u[call] = iv_u
        callvol_dict_d[call] = iv_d
        callvol_dict_m[call] = iv_m
    for put in put_list:
        K = int(re.findall(r'\d+', put)[0])
        flag = 'p'
        try:
            iv_uu = implied_volatility(prc_last[put]+0.02, S_last+0.02, K, t, r, flag)
        except Exception as e:
            print(e)
            iv_uu = 0
        try:
            iv_dd = implied_volatility(prc_last[put]-0.02, S_last-0.02, K, t, r, flag)
        except Exception as e:
            print(e)
            iv_dd = 0
        try:
            iv_mm = implied_volatility(prc_last[put], S_last, K, t, r, flag)
        except Exception as e:
            print(e)
            iv_mm = 0           
        putvol_dict_u[put] = iv_uu
        putvol_dict_d[call] = iv_dd
        putvol_dict_m[call] = iv_mm
    
    calliv_u = pd.Series(iv_u)
    calliv_d = pd.Series(iv_d)
    calliv_m = pd.Series(iv_m)
    putiv_u = pd.Series(iv_uu)
    putiv_d = pd.Series(iv_dd)
    putiv_m = pd.Series(iv_mm)
    

    # signals and execution
    # short hills & long valley
    hill_call = list(calliv_m[calliv_m > putiv_u].index)
    valley_call = list(calliv_m[calliv_m < putiv_d].index)
    hill_put = list(putiv_m[putiv_m > calliv_u].index)
    valley_put = list(putiv_m[putiv_m < calliv_d].index)

    # open position
    if len(pos_ticker) == 0:
        if len(hill_call) != 0:
            for call in hill_call:
                api.market_sell(call, 500)
                api.market_buy(c2p_dict[call], 500)
        if len(valley_call) != 0:
            for call in valley_call:
                api.market_buy(call, 500)
                api.market_sell(c2p_dict[call], 500)
        if len(hill_put) != 0:
            for put in hill_put:
                api.market_sell(put, 500)
                api.market_buy(p2c_dict[put], 500)                
        if len(valley_put) != 0:
            for put in valley_put:
                api.market_buy(put, 500)
                api.market_sell(p2c_dict[put], 500)                   
    # close position
    if len(pos_ticker) != 0:
        for opt in pos_ticker:
            if opt == "RTM":
                continue
            if opt in call_list and calliv_m[opt] < putiv_u and calliv_m[opt] > putiv_d:
                api.close_pos(opt)
                api.close_pos(c2p_dict[opt])
            if opt in put_list and putiv_m[opt] < calliv_u and putiv_m[opt] > calliv_d:
                api.close_pos(opt)
                api.close_pos(p2c_dict[opt])

    # hedge
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
        if option_ticker in call_list:
            sigma = calliv_m[option_ticker]
        elif option_ticker in put_list:
            sigma = putiv_m[option_ticker]
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
