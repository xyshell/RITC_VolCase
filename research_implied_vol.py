import pandas as pd 
import re
from py_vollib.black_scholes.implied_volatility import implied_volatility

hist_data = pd.read_csv('hist_data2.csv')
hist_data = hist_data.sort_values(by='tick').set_index('tick')
ava_ticker = list(hist_data.columns)
call_list = [ticker for ticker in ava_ticker if 'C' in ticker]
put_list = [ticker for ticker in ava_ticker if 'P' in ticker]
# price, S, K, t, r, flag

iv_df = pd.DataFrame(columns=call_list+put_list)
r = 0
for i in range(600):
    hist_slice = hist_data.iloc[i,:]
    t = (600 - i)/ 30/ 252 
    vol_dict = {}
    for call in call_list:
        prc = hist_slice[call]
        S = hist_slice['RTM']
        K = int(re.findall(r'\d+', call)[0])
        flag = 'c'
        try:
            iv = implied_volatility(prc, S, K, t, r, flag)
        except Exception as e:
            print(e)
            iv = 0
        vol_dict[call] = iv

    for put in put_list:
        prc = hist_slice[put]
        S = hist_slice['RTM']
        K = int(re.findall(r'\d+', put)[0])
        flag = 'p'
        try:
            iv = implied_volatility(prc, S, K, t, r, flag)
        except Exception as e:
            print(e)
            iv = 0
        vol_dict[put] = iv

    iv_df = iv_df.append(vol_dict, ignore_index=True)
    
iv_df.to_csv('implied_volatility2.csv')