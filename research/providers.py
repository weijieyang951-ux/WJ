from typing import Protocol
from pathlib import Path
import hashlib, time, json
import numpy as np
import pandas as pd
from .models import Security
from .calendar import sessions
class Provider(Protocol):
    simulated: bool
    def universe(self) -> list[Security]: ...
    def bars(self,symbol: str,day: str) -> pd.DataFrame: ...
    def context(self,symbol: str,day: str) -> dict: ...
class MockProvider:
    simulated=True
    def __init__(self,themes): self.themes=themes
    def universe(self):
        return [Security(symbol=f"SIM{i:04d}",name=f"模拟公司 {i:04d}",sector=self.themes[i%20],themes=[self.themes[i%20]],kind="ETF" if i>=360 else "CS") for i in range(380)]
    def bars(self,symbol,day):
        seed=int(hashlib.sha256(symbol.encode()).hexdigest()[:8],16)
        rng=np.random.default_rng(seed); dates=sessions(pd.Timestamp(day)-pd.Timedelta(days=800),day).index[-420:]
        c=(10+seed%250)*np.exp(np.cumsum(rng.normal(.0003,.018,len(dates))))
        return pd.DataFrame({'open':c*(1+rng.normal(0,.003,len(c))),'high':c*1.015,'low':c*.985,'close':c,'volume':rng.integers(500000,20000000,len(c))},index=dates)
    def context(self,symbol,day):
        return {'attention':None,'events':None,'news':[], 'missing':['news','social','earnings'],'sources':['deterministic synthetic fixture; NOT market data']}
class CachedHTTP:
    def __init__(self,key,cache=Path('.cache/http'),rpm=5):
        import requests
        self.session=requests.Session(); self.key=key; self.cache=cache; self.cache.mkdir(parents=True,exist_ok=True)
        if rpm<=0: raise ValueError('RPM must be positive')
        self.interval=60/rpm; self.last=0.; self.requests=0; self.hits=0
    def get(self,url,params=None,ttl=21600):
        from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
        parsed=urlparse(url)
        if parsed.scheme!='https' or parsed.hostname!='api.polygon.io' or parsed.username or parsed.password or parsed.port not in (None,443): raise ValueError('untrusted provider URL')
        params=dict(params or {}); params.pop('apiKey',None)
        clean=urlunparse(parsed._replace(query=urlencode([(k,v) for k,v in parse_qsl(parsed.query) if k!='apiKey'])))
        path=self.cache/(hashlib.sha256((clean+json.dumps(params,sort_keys=True)).encode()).hexdigest()+'.json')
        if path.exists() and time.time()-path.stat().st_mtime<ttl:
            self.hits+=1; return json.loads(path.read_text())
        for attempt in range(5):
            time.sleep(max(0,self.interval-(time.monotonic()-self.last))); self.last=time.monotonic(); self.requests+=1
            try:
                r=self.session.get(clean,params=params,headers={'Authorization':'Bearer '+self.key},timeout=45,allow_redirects=False)
                if r.status_code==429 or r.status_code>=500:
                    retry_after=r.headers.get('Retry-After','')
                    delay=min(60,float(retry_after)) if retry_after.isdigit() else min(60,2**attempt)
                    time.sleep(delay); continue
                if r.status_code!=200: raise RuntimeError(f'Provider HTTP {r.status_code}; request URL redacted')
                data=r.json()
                if not isinstance(data,dict): raise RuntimeError('Invalid provider JSON')
                serialized=json.dumps(data)
                if self.key and self.key in serialized: raise RuntimeError('Provider response contained credential; refusing cache')
                path.write_text(serialized); return data
            except __import__('requests').RequestException:
                if attempt==4: raise RuntimeError('Provider transport failure; credentials redacted') from None
                time.sleep(2**attempt)
        raise RuntimeError('Provider retries exhausted')
