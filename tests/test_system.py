import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import pytest
from research.calendar import due,next_session
from research.quant import rank,validate_bars,indicators
from research.providers import MockProvider
from research.render import poster

def test_schedule():
    assert due(datetime.fromisoformat('2026-07-06T21:29:00+00:00')) is None
    assert due(datetime.fromisoformat('2026-07-06T21:30:00+00:00'))=='2026-07-06'
    assert due(datetime.fromisoformat('2026-01-05T22:30:00+00:00'))=='2026-01-05'
    assert due(datetime.fromisoformat('2026-07-04T01:00:00+00:00')) is None
    assert due(datetime.fromisoformat('2026-11-27T22:30:00+00:00'))=='2026-11-27'
    assert due(datetime.fromisoformat('2026-07-07T05:00:00+00:00'))=='2026-07-06'
    assert next_session('2026-07-02')=='2026-07-06'
def test_normalization():
    weights=json.loads(Path('config/settings.json').read_text())['weights']
    f=pd.DataFrame({'symbol':['A','B'],'liquidity':[1e12,1e13],'relative_volume':[1,2],'momentum':[1,2],'attention':[None,None],'events':[None,None],'technical':[1,2]})
    ranked=rank(f,weights,300)
    assert ranked.iloc[0].symbol=='B'
    assert ranked.iloc[0].score==1
    assert ranked.iloc[0].coverage==pytest.approx(.75)
    f.liquidity*=100
    assert rank(f,weights,300).score.tolist()==ranked.score.tolist()
def test_no_lookahead():
    b=MockProvider(['test']*25).bars('SIM0001','2026-10-16')
    assert indicators(b).iloc[250].ma20==pytest.approx(indicators(b.iloc[:251]).iloc[-1].ma20)
    validate_bars(b,'2026-10-16')
    with pytest.raises(ValueError): validate_bars(b,'2026-10-15')
@pytest.mark.parametrize('template',['black_gold','navy','ivory'])
def test_empty_poster(tmp_path,template):
    layout=poster(tmp_path/'test.png','06 Quantum Computing',[],'2026-10-16','2026-10-19',True,template)
    assert all(0<=v['box'][0]<v['box'][2]<=1080 and v['box'][3]<=1920 for v in layout)
def test_outputs():
    p=Path('runs/mock/2026-10-16')
    if not p.exists(): pytest.skip('run E2E fixture first')
    reports=json.loads((p/'reports.json').read_text())
    assert len(reports)==len({r['symbol'] for r in reports})==300
    assert len(list((p/'stocks').glob('*.html')))==300
    assert len(list((p/'stocks').glob('*.csv')))==300
    assert len(list((p/'posters').glob('*.png')))==25
    assert all(r['simulated'] and r['probability_up'] is None for r in reports)
    for entries in json.loads((p/'layout.json').read_text()).values():
        assert all(e['box'][2]<=1080 and e['box'][3]<=1920 for e in entries)
        assert all(e['text'].isascii() for e in entries)

def test_invalid_weights():
    with pytest.raises(ValueError): rank(pd.DataFrame(),{'liquidity':1},300)
def test_mock_universe():
    u=MockProvider(['x']*25).universe()
    assert len({s.symbol for s in u})==380
    assert sum(s.kind=='CS' for s in u)==360

def test_provider_real_parsing():
    from research.polygon import PolygonProvider
    provider=PolygonProvider('unit-test-placeholder')
    class FakeHTTP:
        def get(self,url,params=None,ttl=None):
            if '/range/' in url:
                return {'results':[{'t':int(pd.Timestamp('2026-10-16 04:00',tz='UTC').timestamp()*1000),'o':10,'h':12,'l':9,'c':11,'v':10000}]}
            if '/news' in url:
                return {'results':[{'title':'before cutoff','published_utc':'2026-10-16T20:00:00Z','article_url':'https://example.com/1'},{'title':'future','published_utc':'2026-10-17T01:00:00Z'}]}
            return {'results':{'sic_description':'TEST SECTOR'}}
    provider.http=FakeHTTP()
    b=provider.bars('A','2026-10-16')
    assert str(b.index[0].date())=='2026-10-16' and b.iloc[0].close==11
    ctx=provider.context('A','2026-10-16')
    assert ctx['attention']==1 and ctx['sector']=='TEST SECTOR'
    assert 'social' in ctx['missing'] and 'earnings' in ctx['missing']

def test_untrusted_provider_url(tmp_path):
    from research.providers import CachedHTTP
    client=CachedHTTP('secret',cache=tmp_path)
    with pytest.raises(ValueError): client.get('https://evil.example/news')
