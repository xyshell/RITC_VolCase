from RIT_api_v1 import RitClient
from apiUlt import url, apikey
import pandas as pd

api = RitClient(url, apikey)
api.news_info().to_csv('news2.csv')

ava_ticker = list(api.market().index)
df = pd.DataFrame(columns = ava_ticker)
for ticker in ava_ticker:
    s = api.history(ticker)['close'].rename(columns = {'close':ticker})
    df[ticker] = s
df.to_csv('hist_data2.csv')
