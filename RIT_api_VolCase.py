from RIT_api_v1 import RitClient

class VolCaseClient(RitClient):

    def __init__(self, url, apikey):
        RitClient.__init__(self, url, apikey)

    def portfolio(self):
        return self.market()
    
    def price(self, ticker=None, kind='last'):
        if ticker == None:
            return self.market()[kind]
        else:
            return self.market().loc[ticker][kind]

    def position(self, ticker=None):
        '''get position (by ticker) '''
        if ticker == None:
            return self.market()['position']
        else:
            return self.market()['position'][ticker]
    
    def pending_order(self, ticker):
        '''get pending order (by ticker) '''
        if ticker == None:
            return self.order()
        else:
            return self.order()[self.order()['ticker']==ticker]

    def close_pos(self, ticker):
        '''close positions using market order (by ticker) '''
        now_pos = self.position(ticker)
        chg = 0 - now_pos
        if chg > 0:
            if chg > 100 and ticker!="RTM":
                self.market_buy(ticker, 100)
            self.market_buy(ticker, chg)
        elif chg < 0:
            if chg < -100 and ticker!="RTM":
                self.market_sell(ticker, 100)
            self.market_sell(ticker, -chg)
        else:
            pass
        return chg
    
    def news_kind(self, kind, is_last=False):
        '''get news by headline'''
        all_news = self.news_info()
        kind_news = all_news[all_news["headline"].apply(lambda x: kind in x )]
        if is_last == True:
            return kind_news.head(1)
        else:
            return kind_news
        
    
