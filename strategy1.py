from RIT_api_VolCase import VolCaseClient
from apiUlt import url, apikey
from stratUlt import *
from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_vollib.black_scholes_merton.greeks.analytical import delta, vega
import pandas as pd
import re 
import time 

''' dealing with hill & valley implied vol'''

# Waiting for start
api = VolCaseClient(url, apikey)
while api.case_status() == False:
    time.sleep(0.2)
    pass 

# case begins
i = 0
ann_vol = 0.2
# delta_limit = api.news("Delta")
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

    # if now_tick == [150, 300, 450]:
    #     vol_news = api.news("Announcement",True)["Body"]
    #     ann_vol = int(re.findall(r"\d+", vol_news)[0])
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
        except Exception:
            iv_u = 0
        try:
            iv_d = implied_volatility(prc_last[call]-0.02, S_last+0.02, K, t, r, flag)
        except Exception:
            iv_d = 0
        try:
            iv_m = implied_volatility(prc_last[call], S_last, K, t, r, flag)
        except Exception:
            iv_m = 0
        callvol_dict_u[call] = iv_u
        callvol_dict_d[call] = iv_d
        callvol_dict_m[call] = iv_m
    for put in put_list:
        K = int(re.findall(r'\d+', put)[0])
        flag = 'p'
        try:
            iv_uu = implied_volatility(prc_last[put]+0.02, S_last+0.02, K, t, r, flag)
        except Exception:
            iv_uu = 0
        try:
            iv_dd = implied_volatility(prc_last[put]-0.02, S_last-0.02, K, t, r, flag)
        except Exception:
            iv_dd = 0
        try:
            iv_mm = implied_volatility(prc_last[put], S_last, K, t, r, flag)
        except Exception:
            iv_mm = 0           
        putvol_dict_u[put] = iv_uu
        putvol_dict_d[put] = iv_dd
        putvol_dict_m[put] = iv_mm
    
    calliv_u = pd.Series(callvol_dict_u)
    calliv_d = pd.Series(callvol_dict_d)
    calliv_m = pd.Series(callvol_dict_m)
    putiv_u = pd.Series(putvol_dict_u)
    putiv_d = pd.Series(putvol_dict_d)
    putiv_m = pd.Series(putvol_dict_m)
    

    # signals and execution
    # short hills & long valley
    hill_call = list(calliv_m[calliv_d.values > putiv_u.values].index)
    valley_call = list(calliv_m[calliv_u.values < putiv_d.values].index)
    hill_put = list(putiv_m[putiv_d.values > calliv_u.values].index)
    valley_put = list(putiv_m[putiv_u.values < calliv_d.values].index)

    # open position
    if len(pos_ticker) == 0:
        if len(hill_call) != 0:
            for call in hill_call:
                print(call, calliv_m[call],"vs",putiv_m[c2p_dict[call]])
                api.market_sell(call, 50)
                print(call, "sell at", prc_bid[call])
                api.market_buy(c2p_dict[call], 50)
                print(c2p_dict[call], "buy at", prc_ask[c2p_dict[call]])

        if len(valley_call) != 0:
            for call in valley_call:
                print(call, calliv_m[call],"vs",putiv_m[c2p_dict[call]])
                api.market_buy(call, 50)
                print(call, "buy at", prc_ask[call])
                api.market_sell(c2p_dict[call], 50)
                print(c2p_dict[call], "sell at", prc_bid[c2p_dict[call]])

        # if len(hill_put) != 0:
        #     for put in hill_put:
        #         print(put, putiv_m[put],"vs",calliv_m[p2c_dict[put]])
        #         api.market_sell(put, 50)
        #         print(put, "sell at", prc_bid[put])
        #         api.market_buy(p2c_dict[put], 50)      
        #         print(p2c_dict[put], "buy at", prc_ask[p2c_dict[put]])
          
        # if len(valley_put) != 0:
        #     for put in valley_put:
        #         print(put, putiv_m[put],"vs",calliv_m[p2c_dict[put]])
        #         api.market_buy(put, 50)
        #         print(put, "buy at", prc_ask[put])
        #         api.market_sell(p2c_dict[put], 50)      
        #         print(p2c_dict[put], "sell at", prc_bid[p2c_dict[put]])
             
    # close position
    if len(pos_ticker) != 0:
        for opt in pos_ticker:
            if opt == "RTM" or opt in put_list:
                continue
            if opt in call_list and calliv_m[opt] < putiv_u[c2p_dict[opt]] and calliv_m[opt] > putiv_d[c2p_dict[opt]]:
                print(opt, "close at", prc_last[opt])
                print(c2p_dict[opt], "close at", prc_last[c2p_dict[opt]])
                api.close_pos(opt)
                api.close_pos(c2p_dict[opt])
            # if opt in put_list and putiv_m[opt] < calliv_u[p2c_dict[opt]] and putiv_m[opt] > calliv_d[p2c_dict[opt]]:
            #     print(opt, "close at", prc_last[opt])
            #     print(p2c_dict[opt], "close at", prc_last[p2c_dict[opt]])
            #     api.close_pos(opt)
            #     api.close_pos(p2c_dict[opt])

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
        if sum_delta > 10000:
            api.market_sell("RTM", 10000)
        api.market_sell("RTM", sum_delta)
    elif sum_delta < 0:
        if sum_delta < -10000:
            api.market_buy("RTM", 10000)
        api.market_buy("RTM", -sum_delta)



    # feedbacks

    pass
