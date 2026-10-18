import json
import pytest
import requests
from research.providers import CachedHTTP

def response(code,data=None,headers=None):
    class R:
        status_code=code
        def json(self): return data or {'results':[]}
    r=R(); r.headers=headers or {}; return r

def test_retry_cache_auth_and_rate_limit(tmp_path,monkeypatch):
    sleeps=[]; clock=[100.]
    monkeypatch.setattr('research.providers.time.monotonic',lambda:clock[0])
    def sleep(delay): sleeps.append(delay); clock[0]+=delay
    monkeypatch.setattr('research.providers.time.sleep',sleep)
    client=CachedHTTP('not-a-real-api-key',cache=tmp_path,rpm=5)
    answers=iter([response(429,headers={'Retry-After':'2'}),response(503),response(200)])
    calls=[]
    def get(url,**kwargs): calls.append((url,kwargs)); return next(answers)
    client.session.get=get
    client.get('https://api.polygon.io/v3/reference/tickers?apiKey=discard')
    client.get('https://api.polygon.io/v3/reference/tickers?apiKey=discard')
    assert len(calls)==3 and client.hits==1
    assert any(n>=10 for n in sleeps)
    assert all('apiKey' not in url and not kw['allow_redirects'] for url,kw in calls)
    assert all('not-a-real-api-key' not in f.read_text() for f in tmp_path.iterdir())

def test_transport_redacts_exceptions(tmp_path,monkeypatch):
    monkeypatch.setattr('research.providers.time.sleep',lambda _:None)
    client=CachedHTTP('credential-placeholder',cache=tmp_path,rpm=300)
    def fail(*a,**kw): raise requests.ConnectionError('credential-placeholder')
    client.session.get=fail
    with pytest.raises(RuntimeError) as exc: client.get('https://api.polygon.io/test')
    assert 'credential-placeholder' not in str(exc.value)
    assert client.requests==5

def test_response_cannot_cache_credential(tmp_path):
    client=CachedHTTP('credential-placeholder',cache=tmp_path,rpm=300)
    client.session.get=lambda *a,**kw: response(200,{'secret':'credential-placeholder'})
    with pytest.raises(RuntimeError): client.get('https://api.polygon.io/test')
    assert not list(tmp_path.iterdir())

def test_symbols_cannot_escape_output_directory():
    from pydantic import ValidationError
    from research.models import Security
    with pytest.raises(ValidationError): Security(symbol='../escape',name='invalid')
    assert Security(symbol='BRK.B',name='Berkshire').symbol=='BRK.B'
