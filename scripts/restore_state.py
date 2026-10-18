"""Fail closed if an existing history artifact cannot be restored."""
import io, os, zipfile
from pathlib import Path
import requests
base='https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']
s=requests.Session(); s.headers['Authorization']='Bearer '+os.environ['GH_TOKEN']
r=s.get(base+'/actions/artifacts',params={'name':'research-state','per_page':100},timeout=30); r.raise_for_status()
items=[a for a in r.json()['artifacts'] if not a['expired']]
if items:
    a=max(items,key=lambda a:a['created_at'])
    response=s.get(a['archive_download_url'],timeout=60); response.raise_for_status()
    dest=Path('state'); dest.mkdir(exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        for name in z.namelist():
            target=(dest/name).resolve()
            if not target.is_relative_to(dest.resolve()): raise ValueError('Unsafe archive path')
        z.extractall(dest)
else: print('No unexpired state: first run or history retention expired')
