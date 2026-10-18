import argparse, csv, html, json, logging, os, shutil, sqlite3, time, zipfile
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
from .models import Report
from .providers import MockProvider
from .quant import indicators, validate_bars, rank, backtest
from .calendar import due, next_session, sessions
from .render import poster

def save(path,data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def run(provider,day,out,state,settings):
    out=Path(out); state=Path(state); out.mkdir(parents=True,exist_ok=True); state.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(filename=out/'execution.log',level=logging.INFO,force=True)
    start=time.monotonic(); rows=[]; histories={}; contexts={}; excluded=[]
    universe=provider.universe(); seen=set()
    for sec in universe:
        if sec.symbol in seen or not sec.active or sec.kind!='CS' or sec.exchange not in ('XNYS','XNAS','XASE'): continue
        seen.add(sec.symbol)
        try:
            b=provider.bars(sec.symbol,day); validate_bars(b,day); f=indicators(b); v=f.iloc[-1]
            if v.close<settings['min_price'] or v.close*v.volume<settings['min_dollar_volume']: continue
            ctx=provider.context(sec.symbol,day); sec.sector=ctx.get('sector',sec.sector); contexts[sec.symbol]=ctx; histories[sec.symbol]=b
            rows.append(dict(symbol=sec.symbol,security=sec,liquidity=float(v.close*v.volume),relative_volume=float(v.relative_volume),momentum=float(abs(v.momentum)+v.atr/v.close),attention=ctx['attention'],events=ctx['events'],technical=float(abs(v.rsi-50)/50+abs(v.macd-v.macd_signal)/v.close)))
        except Exception as e:
            excluded.append({'symbol':sec.symbol,'reason':str(e)}); logging.warning('Excluded %s: %s',sec.symbol,e)
    save(out/'exclusions.json',excluded)
    if len(rows)<settings['top_n']: raise RuntimeError(f'Only {len(rows)} qualified stocks; refusing to fabricate Top 300')
    selected=rank(pd.DataFrame(rows),settings['weights'],settings['top_n'])
    db=sqlite3.connect(state/('mock.sqlite' if provider.simulated else 'live.sqlite'))
    db.execute('create table if not exists predictions(session text,symbol text,rank integer,close real,outlook text,payload text,primary key(session,symbol))')
    previous_day=db.execute('select max(session) from predictions where session < ?',(day,)).fetchone()[0]
    old=dict(db.execute('select symbol,rank from predictions where session=?',(previous_day,)))
    reports=[]; bt={}; next_day=next_session(day); (out/'stocks').mkdir(exist_ok=True)
    for i,(_,row) in enumerate(selected.iterrows(),1):
        sec=row.security; b=histories[sec.symbol]; v=indicators(b).iloc[-1]; ctx=contexts[sec.symbol]
        outlook={1:'看涨',0:'震荡',-1:'看跌'}[int(v.signal)]
        r=Report(symbol=sec.symbol,name=sec.name,sector=sec.sector,themes=sec.themes,session=day,next_session=next_day,simulated=provider.simulated,close=float(v.close),change_pct=float(v['return']*100),dollar_volume=float(v.close*v.volume),relative_volume=float(v.relative_volume),indicators={k:float(v[k]) for k in ['rsi','macd','macd_signal','ma20','ma50','ma200','atr']},support=float(v.support),resistance=float(v.resistance),outlook=outlook,scenarios={'看涨':f'若突破 {v.resistance:.2f}，关注量能确认','基准':f'在 {v.support:.2f} 至 {v.resistance:.2f} 区间震荡','看跌':f'若跌破 {v.support:.2f}，警惕回撤扩大'},catalysts=ctx['news'] or ['外部催化数据缺失，未推断'],risks=['隔夜跳空风险','技术信号可能失效','当前股票池存在幸存者偏差'],sources=ctx['sources'],missing=ctx['missing'],score=float(row.score),rank=i,rank_change=old.get(sec.symbol,i)-i if sec.symbol in old else None,summary=f'{sec.name}：均线与 MACD 条件判断为{outlook}。关注支撑 {v.support:.2f}、阻力 {v.resistance:.2f}；不输出未经校准的上涨概率。')
        reports.append(r); payload=r.model_dump(); save(out/'stocks'/f'{r.symbol}.json',payload)
        pd.json_normalize(payload).to_csv(out/'stocks'/f'{r.symbol}.csv',index=False)
        (out/'stocks'/f'{r.symbol}.html').write_text('<meta charset="utf-8"><h1>'+html.escape(r.symbol+' '+r.name)+'</h1><pre>'+html.escape(json.dumps(payload,ensure_ascii=False,indent=2))+'</pre>',encoding='utf-8')
        bt[r.symbol]=backtest(b)
    save(out/'reports.json',[r.model_dump() for r in reports]); pd.json_normalize([r.model_dump() for r in reports]).to_csv(out/'reports.csv',index=False)
    selected.drop(columns=['security']).to_csv(out/'ranking.csv',index=False)
    save(out/'backtest.json',bt)
    (out/'posters').mkdir(exist_ok=True); layouts={}; manifests={}
    for i,theme in enumerate(settings['themes'],1):
        members=[r for r in reports if theme in r.themes]
        if i==21: members=sorted(reports,key=lambda r:r.dollar_volume,reverse=True)
        if i==22: members=sorted([r for r in reports if r.change_pct>0],key=lambda r:r.change_pct,reverse=True)
        if i==23: members=sorted([r for r in reports if r.change_pct<0],key=lambda r:r.change_pct)
        if i==24: members=sorted(reports,key=lambda r:r.relative_volume,reverse=True)
        if i==25: members=sorted(reports,key=lambda r:r.score,reverse=True)
        members=members[:15]; filename=f'{i:02d}.png'; manifests[filename]=[r.symbol for r in members]
        layouts[filename]=poster(out/'posters'/filename,f'{i:02d} '+settings['poster_titles'][i-1],members,day,next_day,provider.simulated,settings['template'])
    save(out/'poster-members.json',manifests); save(out/'layout.json',layouts)
    if len(list((out/'posters').glob('*.png')))!=25 or len(reports)!=300 or len({r.symbol for r in reports})!=300: raise ValueError('invalid output counts')
    with zipfile.ZipFile(out/'posters.zip','w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted((out/'posters').glob('*.png')): z.write(f,'posters/'+f.name)
    market={'session':day,'next_session':next_day,'simulated':provider.simulated,'qualified':len(rows),'analyzed':len(reports),'missing_news':sum('news' in r.missing for r in reports),'outlooks':{k:sum(r.outlook==k for r in reports) for k in ['看涨','震荡','看跌']},'method':'cross-sectional percentile normalization; missing weights reallocated per stock','limitations':['No calibrated probability model','No LLM calls; deterministic Chinese summaries','Theme mapping is curated and requires maintenance','Close × volume is estimated dollar turnover, not trade-level exact notional']}
    save(out/'market.json',market)
    (out/'market.html').write_text('<meta charset="utf-8"><h1>美股每日研究 '+day+('</h1><h2>模拟数据 · 非真实行情</h2>' if provider.simulated else '</h1>')+'<pre>'+html.escape(json.dumps(market,ensure_ascii=False,indent=2))+'</pre>'+''.join('<p><a href="stocks/'+r.symbol+'.html">'+html.escape(r.symbol+' '+r.name)+'</a> '+html.escape(r.summary)+'</p>' for r in reports),encoding='utf-8')
    http=getattr(provider,'http',None)
    save(out/'costs.json',{'http_requests':http.requests if http else 0,'cache_hits':http.hits if http else 0,'llm_tokens':0,'llm_usd':0,'provider_usd':None,'provider_cost_status':'subscription/entitlement dependent; not estimated','elapsed_seconds':round(time.monotonic()-start,2)})
    with db:
        for r in reports: db.execute('insert or replace into predictions values(?,?,?,?,?,?)',(day,r.symbol,r.rank,r.close,r.outlook,r.model_dump_json()))
    pd.read_sql_query('select * from predictions order by session,symbol',db).to_csv(out/'prediction-history.csv',index=False)
    # Resolve prior predictions only with actually observed next-session close.
    resolved=[]
    for session,symbol,close,outlook in db.execute('select session,symbol,close,outlook from predictions where session < ?',(day,)):
        target=next_session(session); b=histories.get(symbol)
        if b is not None and pd.Timestamp(target) in b.index:
            actual=float(b.loc[pd.Timestamp(target),'close']/close-1)
            resolved.append({'session':session,'symbol':symbol,'target':target,'actual_return':actual,'outlook':outlook})
    save(out/'resolved-predictions.json',resolved); db.close()
    logging.info('Validated %s stocks and 25 posters',len(reports))
    return market

def main():
    p=argparse.ArgumentParser(); p.add_argument('--provider',choices=['mock','polygon'],default='mock'); p.add_argument('--date'); p.add_argument('--scheduled',action='store_true'); p.add_argument('--out',default='runs'); p.add_argument('--state',default='state'); p.add_argument('--template',choices=['black_gold','navy','ivory']); a=p.parse_args()
    day=a.date or (due(datetime.now(timezone.utc)) if a.scheduled else str(sessions(pd.Timestamp.now(tz='America/New_York').date()-pd.Timedelta(days=14),pd.Timestamp.now(tz='America/New_York').date()-pd.Timedelta(days=1)).index[-1].date()))
    if day is None: print('Not due: trading-calendar / 17:30 ET gate'); return
    if sessions(day,day).empty: raise ValueError('Not a trading session')
    settings=json.loads(Path('config/settings.json').read_text()); settings['template']=a.template or settings['template']
    if a.provider=='mock': provider=MockProvider(settings['themes'])
    else:
        from .polygon import PolygonProvider
        provider=PolygonProvider(os.getenv('POLYGON_API_KEY',''))
    state=Path(a.state); state.mkdir(exist_ok=True,parents=True)
    marker=state/f'{a.provider}-{day}.done'
    if a.scheduled and marker.exists(): print('Already completed'); return
    dest=Path(a.out)/a.provider/day; temp=dest.with_name(day+'.partial')
    if temp.exists(): shutil.rmtree(temp)
    run(provider,day,temp,state,settings)
    if dest.exists(): shutil.rmtree(dest)
    temp.rename(dest); marker.write_text('validated')
    print(f'Validated 300 stocks, 25 posters: {dest}')
if __name__=='__main__': main()
