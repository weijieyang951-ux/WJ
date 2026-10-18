"""Live API acceptance probe. Does not log credentials or raw request exceptions."""
import json,os,sys
from datetime import datetime,timedelta
from pathlib import Path
from research.calendar import sessions,NY
from research.polygon import PolygonProvider
from research.quant import validate_bars
out=Path('runs/api-smoke'); out.mkdir(parents=True,exist_ok=True)
try:
    key=os.getenv('POLYGON_API_KEY','')
    if not key: raise RuntimeError('POLYGON_API_KEY missing from GitHub Secrets')
    provider=PolygonProvider(key)
    day=str(sessions(datetime.now(NY).date()-timedelta(days=14),datetime.now(NY).date()-timedelta(days=1)).index[-1].date())
    bars=provider.bars('AAPL',day); validate_bars(bars,day)
    result={'status':'passed','session':day,'symbol':'AAPL','bars':len(bars),'requests':provider.http.requests,'simulated':False}
except Exception as e:
    result={'status':'failed','reason':str(e) if isinstance(e,RuntimeError) else type(e).__name__}
(out/'acceptance.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result)); sys.exit(0 if result['status']=='passed' else 1)
