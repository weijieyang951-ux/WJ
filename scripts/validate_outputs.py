"""Validate every generated file before uploading an accepted daily report."""
import json,sys,zipfile
from pathlib import Path
from PIL import Image
p=Path(sys.argv[1]); reports=json.loads((p/'reports.json').read_text())
assert len(reports)==len({r['symbol'] for r in reports})==300
for suffix in ['json','csv','html']: assert len(list((p/'stocks').glob('*.'+suffix)))==300
images=list((p/'posters').glob('*.png')); assert len(images)==25
for path in images:
    with Image.open(path) as im: assert im.size==(1080,1920); im.verify()
layout=json.loads((p/'layout.json').read_text())
assert len(layout)==25
for entries in layout.values():
    for e in entries:
        assert e['text'].isascii(),e['text']
        x0,y0,x1,y1=e['box']; assert 0<=x0<x1<=1080 and 0<=y0<y1<=1920
members=json.loads((p/'poster-members.json').read_text()); symbols={r['symbol'] for r in reports}
assert all(len(v)<=15 and set(v)<=symbols for v in members.values())
with zipfile.ZipFile(p/'posters.zip') as z: assert len(z.namelist())==25 and z.testzip() is None
print('PASS: 300 reports, 25 English 1080x1920 posters, ZIP, bounds and membership')
