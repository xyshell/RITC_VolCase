import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TKAgg")
import matplotlib.pyplot as plt
import time

implied_vol = pd.read_csv("data/implied_volatility3.csv")
for i in range(len(implied_vol)):
    if i <= 0 :
        continue
    print(i)

    
    cp_vol = implied_vol.iloc[i,1:]
    print(
        "0%", round(cp_vol.min(),3), "25%", round(cp_vol.quantile(.25),3),
        "50%", round(cp_vol.median(),3), "75%", round(cp_vol.quantile(.75),3),
        "100%", round(cp_vol.max(),3))
    print(cp_vol.index[cp_vol >= cp_vol.quantile(.85)])
    
    plt.figure(figsize=(8,10))
    
    implied_vol.iloc[i,1:].plot()
    xaxis = [i[3:] for i in implied_vol.columns[1:]]
    plt.xticks(range(len(xaxis)),tuple(xaxis))

    call_vol = implied_vol.iloc[i,1:11]
    put_vol = implied_vol.iloc[i,11:]
    plt.plot([0, 9], [call_vol.median(), call_vol.median()])
    plt.plot([10, 19], [put_vol.median(), put_vol.median()])
    plt.show()
    plt.close()

