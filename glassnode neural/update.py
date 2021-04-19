import json
import requests
import pandas as pd
from datetime import datetime
from numpy import array
import numpy as np

### daystillhalving ozel ilgi istiyor 'indicators/stock_to_flow_ratio'

API_KEY = '1qw7PqyizkXgWik1pZkm1CBxRGM'
metrics = ['addresses/new_non_zero_count', 'addresses/active_count', 
           'addresses/sending_count', 'addresses/receiving_count', 'addresses/count',
           'blockchain/block_height', 'blockchain/block_count', 'blockchain/block_interval_mean',
           'blockchain/block_interval_median', 'blockchain/block_size_sum', 'blockchain/block_size_mean',
           'fees/volume_sum', 'fees/volume_mean', 'market/price_drawdown_relative', 'market/marketcap_usd',
           'supply/current', 'transactions/count', 'transactions/rate',
           'transactions/size_sum', 'transactions/size_mean', 'transactions/transfers_volume_sum',
           'transactions/transfers_volume_mean', 'transactions/transfers_volume_median', 'blockchain/utxo_created_count','market/price_usd_close']
           #'blockchain/utxo_spent_count']#,'blockchain/utxo_count']
           #'blockchain/utxo_count', 'blockchain/utxo_created_value_mean', 'blockchain/utxo_created_value_median',
           #'blockchain/utxo_spent_value_sum', 'blockchain/utxo_spent_value_mean', 'blockchain/utxo_spent_value_median'
           # sigmayanlar
           #'fees/volume_median', 'mining/difficulty_latest','mining/hash_rate_mean','indicators/difficulty_ribbon']
           # bunlari csv'den okuman gerekiyor
           # market/price_usd_ohlc bunu da parcalara ayirip taglemen lazim 


def getIndicator(metric):

    now = int(datetime.now().timestamp())
    since = datetime.date(2017, 1, 1)
    res = requests.get('https://api.glassnode.com/v1/metrics/{}'.format(metric),
        params={'api_key': API_KEY, 'a':'BTC', 's':since, 'u':now, 'i':"24h"})

    df = pd.read_json(res.text, convert_dates=['t'])
    del df['t']
    df = array(df)
    df_min = np.amin(df)
    df_max = np.amax(df)

    if metric == 'market/price_usd_close':
        print("")
    else:
    #normalization
        with np.nditer(df, op_flags=['readwrite']) as it:
            for x in it:
                x[...] = (x - df_min)/(df_max - df_min)
    return df