import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import AverageTrueRange

def indicators(b):
    c=b.close
    out=b.copy()
    out['rsi']=RSIIndicator(c).rsi()
    m=MACD(c); out['macd']=m.macd(); out['macd_signal']=m.macd_signal()
    for n in (20,50,200): out[f'ma{n}']=c.rolling(n).mean()
    out['atr']=AverageTrueRange(b.high,b.low,c).average_true_range()
    out['relative_volume']=b.volume/b.volume.shift(1).rolling(20).mean()
    out['return']=c.pct_change(); out['momentum']=c.pct_change(20)
    out['support']=b.low.rolling(20).min(); out['resistance']=b.high.rolling(20).max()
    out['signal']=np.where((c>out.ma20)&(out.macd>out.macd_signal),1,np.where((c<out.ma20)&(out.macd<out.macd_signal),-1,0))
    return out

def validate_bars(b,day):
    if len(b)<220 or b.index.has_duplicates or not b.index.is_monotonic_increasing: raise ValueError('insufficient/duplicate/unordered bars')
    if str(b.index[-1].date())!=day: raise ValueError('stale session')
    cols=['open','high','low','close','volume']
    if not np.isfinite(b[cols].to_numpy()).all() or (b[cols]<=0).any().any(): raise ValueError('invalid OHLCV')
    if ((b.high<b[['open','close','low']].max(axis=1))|(b.low>b[['open','close','high']].min(axis=1))).any(): raise ValueError('invalid range')

def rank(frame,weights,n):
    if set(weights)!=set(['liquidity','relative_volume','momentum','attention','events','technical']) or any(v<0 for v in weights.values()) or not np.isclose(sum(weights.values()),1): raise ValueError('invalid weights')
    f=frame.copy(); total=pd.Series(0.,index=f.index); available=total.copy()
    for k,w in weights.items():
        norm=f[k].rank(pct=True,method='average') # per-day cross-sectional percentile
        f['normalized_'+k]=norm
        total+=norm.fillna(0)*w; available+=norm.notna()*w
    f['coverage']=available
    f['score']=total/available.replace(0,np.nan)
    return f.dropna(subset=['score']).sort_values(['score','symbol'],ascending=[False,True]).head(n)

def backtest(b):
    f=indicators(b); rows=[]
    # Expanding chronological folds; deterministic rule fixed before evaluation.
    for start in range(220,len(f)-1,40):
        end=min(start+40,len(f)-1); test=f.iloc[start:end]
        actual=f.close.shift(-1)/f.close-1
        net=(test.signal*actual.loc[test.index]-.001*test.signal.diff().fillna(test.signal).abs())
        rows.append({'train_end':str(f.index[start-1].date()),'test_start':str(test.index[0].date()),'test_end':str(test.index[-1].date()),'n':len(test),'mean_net_return':float(net.mean()),'direction_accuracy':float(((actual.loc[test.index]>0)==(test.signal>0))[test.signal!=0].mean()) if (test.signal!=0).any() else None})
    return {'folds':rows,'cost_bps':10,'probability_enabled':False,'calibration':'not fitted; no probabilities emitted','limitations':['current universe survivorship bias','not a historical Top300 selection backtest','no short borrow or slippage model']}
