from RIT_api_v1 import RitClient
from RIT_api_VolCase import VolCaseClient
from apiUlt import url, apikey
from py_vollib.black_scholes.implied_volatility import implied_volatility
import pandas as pd
import re 
import time 

api1 = RitClient(url, apikey)
api2 = VolCaseClient(url, apikey)
print(
    api2.price(ticker="RTM")
)