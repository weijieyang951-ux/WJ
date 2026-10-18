"""Polygon.io REST adapter. Never falls back to synthetic data."""
import json, os
from datetime import timedelta
from pathlib import Path
import pandas as pd
from .models import Security
from .providers import CachedHTTP

class PolygonProvider:
    simulated=False
    base='https://api.polygon.io'
    def __init__(self,key):
        if not key: raise ValueError('POLYGON_API_KEY is required')
        self.http=CachedHTTP(key,rpm=int(os.getenv('POLYGON_RPM','5')))
        self.themes=json.loads(Path('config/themes.json').read_text())
    def universe(self):
        url=self.base+'/v3/reference/tickers'; params={'market':'stocks','locale':'us','active':'true','type':'CS','limit':1000}
        result=[]
        while url:
            data=self.http.get(url,params,ttl=3600)
            for x in data.get('results',[]):
                if x.get('primary_exchange') not in ('XNYS','XNAS','XASE'): continue
                symbol=x['ticker']
                result.append(Security(symbol=symbol,name=x.get('name',symbol),kind=x.get('type','unknown'),active=x.get('active',False),exchange=x.get('primary_exchange',''),themes=[t for t,m in self.themes.items() if symbol in m]))
            url=data.get('next_url'); params={}
        if not result: raise RuntimeError('Empty provider universe')
        return result
    def bars(self,symbol,day):
        from urllib.parse import quote
        start=str((pd.Timestamp(day)-pd.Timedelta(days=800)).date())
        data=self.http.get(self.base+f'/v2/aggs/ticker/{quote(symbol,safe="")}/range/1/day/{start}/{day}',{'adjusted':'true','sort':'asc','limit':50000})
        rows=data.get('results',[])
        if not rows: raise ValueError('Missing daily bars')
        b=pd.DataFrame(rows).rename(columns={'o':'open','h':'high','l':'low','c':'close','v':'volume'})
        b.index=pd.to_datetime(b.t,unit='ms',utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None).dt.normalize()
        return b[['open','high','low','close','volume']]
    def context(self,symbol,day):
        missing=['social','earnings']; news=[]; sources=['Polygon adjusted daily aggregates','Polygon active US common-stock reference']
        from urllib.parse import quote
        sector='未分类'
        try:
            detail=self.http.get(self.base+'/v3/reference/tickers/'+quote(symbol,safe=''),{'date':day},ttl=86400).get('results',{})
            sector=detail.get('sic_description') or '未分类'
        except RuntimeError: missing.append('sector')
        try:
            start=(pd.Timestamp(day)-pd.Timedelta(days=1)).date().isoformat()
            end=(pd.Timestamp(day)+pd.Timedelta(days=1)).date().isoformat()
            data=self.http.get(self.base+'/v2/reference/news',{'ticker':symbol,'published_utc.gte':start,'published_utc.lt':end,'limit':100,'sort':'published_utc','order':'desc'})
            # Cut off at 17:30 ET for this session; never use later articles.
            cutoff=pd.Timestamp(day+' 17:30',tz='America/New_York').tz_convert('UTC')
            articles=[a for a in data.get('results',[]) if pd.Timestamp(a['published_utc'])<=cutoff]
            news=[a['title']+' | '+a.get('article_url','') for a in articles[:5]]
            attention=len(articles); sources.append('Polygon news (capped 100 articles; social unavailable)')
        except (RuntimeError,KeyError,ValueError):
            attention=None; missing.append('news')
        return {'attention':attention,'events':None,'news':news,'missing':missing,'sources':sources,'sector':sector}
