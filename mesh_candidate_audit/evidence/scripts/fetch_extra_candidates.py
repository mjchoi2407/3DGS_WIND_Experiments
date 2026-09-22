import concurrent.futures as cf, hashlib, json, pathlib, requests, time
ROOT=pathlib.Path('experiments/artifacts/datasets/mesh_candidates_extra_20260912')
ASSETS=['grass_medium_01','fern_02','celandine_01']
ROOT.mkdir(parents=True,exist_ok=True)
def get(url):
 for attempt in range(3):
  try:
   r=requests.get(url,timeout=90);r.raise_for_status();return r.content
  except Exception:
   if attempt==2: raise
   time.sleep(1)
def one(a):
 d=ROOT/a;d.mkdir(exist_ok=True)
 raw=get('https://api.polyhaven.com/files/'+a);(d/'files.json').write_bytes(raw);x=json.loads(raw)
 item=x['gltf']['4k']['gltf']; entries={a+'_4k.gltf':item,**item['include']}
 for name,info in x['blend']['4k']['blend']['include'].items():
  if 'alpha' in name.lower() or 'transluc' in name.lower():entries[name]=info
 records=[]
 for name,info in entries.items():
  p=d/name;p.parent.mkdir(exist_ok=True,parents=True)
  b=p.read_bytes() if p.exists() else get(info['url'])
  assert len(b)==info['size'],name
  assert hashlib.md5(b).hexdigest()==info['md5'],name
  if not p.exists():p.write_bytes(b)
  records.append(dict(path=str(p.relative_to(ROOT)),url=info['url'],bytes=len(b),md5=info['md5'],sha256=hashlib.sha256(b).hexdigest()))
 result=dict(asset=a,source='https://polyhaven.com/a/'+a,license='CC0',resolution='4k',files=records,status='downloaded')
 (d/'download_manifest.json').write_text(json.dumps(result,indent=2))
 print(a,'다운로드·해시 확인 완료',sum(t['bytes'] for t in records),flush=True)
 return result
results=[]
with cf.ThreadPoolExecutor(max_workers=3) as pool:
 futures={pool.submit(one,a):a for a in ASSETS}
 for f in cf.as_completed(futures):
  try:results.append(f.result())
  except Exception as e:results.append(dict(asset=futures[f],status='error',error=str(e)));print(futures[f],str(e),flush=True)
(ROOT/'download_manifest.json').write_text(json.dumps(results,indent=2))
