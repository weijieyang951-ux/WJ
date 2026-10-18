import csv
import json
import os
import zipfile
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import numpy as np
import pandas as pd
import yfinance as yf
from PIL import Image, ImageDraw, ImageFont

from .sectors import SECTORS, SEED

OUT = Path("output")
NY = ZoneInfo("America/New_York")


def eligible_now():
    now = datetime.now(NY)
    cal = xcals.get_calendar("XNYS")
    today = pd.Timestamp(now.date())
    if not cal.is_session(today):
        return False
    close = cal.session_close(today).tz_convert(NY).to_pydatetime()
    target = max(close + timedelta(minutes=30), datetime.combine(now.date(), time(17, 30), NY))
    return target <= now < target + timedelta(hours=3)


def indicators(frame):
    close = frame["Close"].astype(float)
    volume = frame["Volume"].astype(float)
    if len(close) < 60 or close.iloc[-1] <= 0:
        return None
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = up.iloc[-1] / max(down.iloc[-1], 1e-10)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    tr = pd.concat([(frame["High"]-frame["Low"]).abs(), (frame["High"]-close.shift()).abs(), (frame["Low"]-close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1]
    rv = volume.iloc[-1] / max(volume.iloc[-21:-1].mean(), 1)
    change = (close.iloc[-1] / close.iloc[-2] - 1) * 100
    return dict(price=round(float(close.iloc[-1]), 2), change_pct=round(float(change), 2),
                dollar_volume=float(close.iloc[-1]*volume.iloc[-1]), relative_volume=round(float(rv), 2),
                rsi=round(float(100-100/(1+rs)), 2), macd=round(float(macd.iloc[-1]), 4),
                macd_signal=round(float(signal.iloc[-1]), 4), sma20=round(float(close.tail(20).mean()), 2),
                sma50=round(float(close.tail(50).mean()), 2), atr=round(float(atr), 2),
                support=round(float(frame["Low"].tail(20).min()), 2),
                resistance=round(float(frame["High"].tail(20).max()), 2),
                momentum_20d=float(close.iloc[-1]/close.iloc[-21]-1),
                volatility_20d=float(close.pct_change().tail(20).std()))


def normalized(series):
    v = pd.to_numeric(series, errors="coerce")
    if v.notna().sum() < 2 or v.max() == v.min():
        return pd.Series(0.5, index=series.index)
    lo, hi = v.quantile([0.05, 0.95])
    if hi == lo:
        return pd.Series(0.5, index=series.index)
    return ((v.clip(lo, hi)-lo)/(hi-lo)).fillna(0.5)


def rank(records):
    df = pd.DataFrame(records)
    features = {
        "liquidity": np.log1p(df.dollar_volume),
        "volume": df.relative_volume,
        "momentum": df.momentum_20d.abs() + df.volatility_20d,
        "technical": (df.rsi-50).abs() + (df.macd-df.macd_signal).abs(),
    }
    weights = {"liquidity": .25, "volume": .20, "momentum": .20, "technical": .10}
    # Missing news/social (.15) and events (.10) are not fabricated.
    # Renormalize available weights; expose coverage on every record.
    df["score"] = sum(normalized(features[k])*w for k,w in weights.items()) / sum(weights.values())
    df["score_coverage"] = sum(weights.values())
    return df.sort_values(["score","ticker"], ascending=[False,True]).head(300)


def font(size):
    path="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size)


def poster(name, rows, destination):
    im=Image.new("RGB",(1080,1920),(9,13,21))
    d=ImageDraw.Draw(im)
    gold=(227,188,100)
    d.text((65,65),"WALL STREET  |  DAILY RESEARCH",font=font(32),fill=gold)
    d.text((65,150),name.upper(),font=font(55),fill=(245,245,245))
    d.text((65,245),datetime.now(NY).strftime("%Y-%m-%d  ET"),font=font(29),fill=gold)
    d.line((65,315,1015,315),fill=gold,width=3)
    for i,r in enumerate(rows[:15]):
        y=350+i*92
        label=f"{r['ticker']:<7}  ${r['price']:>9.2f}  {r['change_pct']:+7.2f}%"
        d.text((68,y),label,font=font(34),fill=(235,235,235))
        d.text((70,y+43),f"NEXT SESSION: {r['outlook']}  |  RSI {r['rsi']:.1f}",font=font(22),fill=gold)
    d.text((65,1790),"Scenario-based research | Not investment advice",font=font(25),fill=gold)
    d.text((65,1830),"Source: Yahoo Finance via yfinance | Missing feeds excluded",font=font(20),fill=(190,190,190))
    im.save(destination)


def main():
    if os.getenv("FORCE_RUN","false").lower() != "true" and not eligible_now():
        print("Outside NYSE research window; skipped.")
        return
    OUT.mkdir(exist_ok=True)
    records=[]
    for ticker in dict.fromkeys(SEED):
        try:
            data=yf.download(ticker,period="6mo",auto_adjust=True,progress=False,threads=False,timeout=15)
            if data.empty:
                continue
            if isinstance(data.columns,pd.MultiIndex):
                data.columns=data.columns.get_level_values(0)
            result=indicators(data)
            if result is None:
                continue
            result.update(ticker=ticker,sector_tags=[name for name, symbols in SECTORS.items() if ticker in symbols],
                          source="Yahoo Finance (yfinance)",news_social=None,earnings_events=None,
                          data_quality="partial: news and events unavailable")
            records.append(result)
        except Exception as exc:
            print(f"FETCH_FAILED {ticker}: {type(exc).__name__}: {exc}")
    if not records:
        raise RuntimeError("No verified market data; refusing to generate synthetic reports")
    ranked=rank(records)
    ranked["outlook"]=np.where((ranked.price>ranked.sma20)&(ranked.macd>ranked.macd_signal),"BULLISH",
                         np.where((ranked.price<ranked.sma20)&(ranked.macd<ranked.macd_signal),"BEARISH","MIXED"))
    ranked["bull_case"]="Close above resistance with confirming volume"
    ranked["base_case"]="Range-bound near 20-day moving average"
    ranked["bear_case"]="Break below support with elevated volatility"
    ranked["risk_factors"]="Volatility, macro releases, earnings and liquidity"
    ranked["catalysts"]="Technical breakout or market-wide repricing; unverified event feed"
    ranked["as_of"]=datetime.now(NY).isoformat()
    ranked["rank"]=range(1,len(ranked)+1)
    ranked["sector_tags"]=ranked.sector_tags.map(json.dumps)
    ranked.to_csv(OUT/"top300.csv",index=False)
    items=ranked.to_dict("records")
    (OUT/"top300.json").write_text(json.dumps(items,indent=2,default=str),encoding="utf-8")
    ranked.to_html(OUT/"top300.html",index=False,escape=True)
    poster_dir=OUT/"posters"
    poster_dir.mkdir(exist_ok=True)
    for n,(sector,symbols) in enumerate(SECTORS.items(),1):
        chosen=[r for r in items if r["ticker"] in symbols]
        if sector=="Dollar Volume Leaders": chosen=sorted(items,key=lambda x:x["dollar_volume"],reverse=True)
        if sector=="Top Gainers": chosen=sorted(items,key=lambda x:x["change_pct"],reverse=True)
        if sector=="Top Decliners": chosen=sorted(items,key=lambda x:x["change_pct"])
        if sector=="Unusual Volume": chosen=sorted(items,key=lambda x:x["relative_volume"],reverse=True)
        if sector=="Next Session Watchlist": chosen=items
        poster(sector,chosen[:15],poster_dir/f"{n:02d}.png")
    with zipfile.ZipFile(OUT/"posters.zip","w",zipfile.ZIP_DEFLATED) as z:
        for path in sorted(poster_dir.glob("*.png")):
            z.write(path,path.name)
    (OUT/"market_summary.json").write_text(json.dumps({"count":len(items),"as_of":datetime.now(NY).isoformat(),"coverage":"seed universe; incomplete news/events","probabilities":"not calibrated; not published"},indent=2))
    (OUT/"backtest_status.json").write_text(json.dumps({"status":"not_validated","probabilities_enabled":False,"reason":"rolling out-of-sample evaluation not yet implemented"},indent=2))
    assert len(list(poster_dir.glob("*.png")))==25
    print(f"Generated {len(items)} verified stock records and 25 posters")


if __name__=="__main__":
    main()
