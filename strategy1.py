from RIT_api_VolCase import VolCaseClient
from apiUlt import url, apikey
from py_vollib.black_scholes.implied_volatility import implied_volatility
import pandas as pd
import re 
import time 

''' dealing with 0 implied vol'''

# Case Params
r = 0

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

    print(now_tick) # timer

    # get data
    pos = api.position()
    prc_bid = api.price(kind='bid')
    prc_ask = api.price(kind='ask')
    S_ask = api.price(ticker="RTM",kind='ask')
    S_bid = api.price(ticker="RTM",kind='bid')

    t = (600 - now_tick)/ 30/ 252 

    if (pos == 0).all():
        # computation
        vol_dict = {}
        for option_ticker in prc_ask.index[1:]:
            K = int(re.findall(r'\d+', option_ticker)[0])
            flag = option_ticker[-1].lower()
            try:
                iv = implied_volatility(prc_ask[option_ticker], S_bid, K, t, r, flag)
            except Exception as e:
                iv = 0
            vol_dict[option_ticker] = iv 
        iv_s = pd.Series(vol_dict)
    else:
                # computation
        vol_dict = {}
        for option_ticker in prc_ask.index[1:]:
            K = int(re.findall(r'\d+', option_ticker)[0])
            flag = option_ticker[-1].lower()
            try:
                iv = implied_volatility(prc_bid[option_ticker], S_ask, K, t, r, flag)
            except Exception as e:
                iv = 0
            vol_dict[option_ticker] = iv 
        iv_s = pd.Series(vol_dict)

    # signals and execution
    if len(iv_s[iv_s == 0]) == 0 and (pos == 0).all():
        continue 
    elif len(iv_s[iv_s == 0]) != 0 and (pos == 0).all():
        buy_ticker = list(iv_s[iv_s == 0].index)[0]
        api.market_buy(buy_ticker, 100)
        api.market_sell("RTM", 10000)
    elif (pos != 0).any():
        hold_option = pos[1:][pos != 0].index[0]
        if iv_s[hold_option] != 0:
            api.market_buy("RTM", 10000)
            api.market_sell(hold_option, 100)
        else:
            continue

    # feedbacks

    pass
