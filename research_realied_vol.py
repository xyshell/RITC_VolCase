import numpy as np
import pandas as pd 
import ffn
from py_vollib.black_scholes.implied_volatility import implied_volatility
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

hist_data = pd.read_csv('hist_data.csv')
hist_data = hist_data.sort_values(by='tick').set_index('tick')

timing_list = [150, 300, 450, 600]
for i in range(len(timing_list)): 
    if i == 0: 
        RTM_prc = hist_data.ix[:timing_list[i], 'RTM']
    else:
        RTM_prc = hist_data.ix[timing_list[i-1]:timing_list[i], 'RTM']
    RTM_ret = ffn.to_returns(RTM_prc)
    RTM_std = RTM_ret.std() * np.sqrt(30 * 252)

    print('t =', timing_list[i], RTM_std)