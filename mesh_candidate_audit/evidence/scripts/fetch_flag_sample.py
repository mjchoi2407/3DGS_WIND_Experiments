import pathlib,requests,struct,json,hashlib
p=pathlib.Path('experiments/artifacts/datasets/mesh_candidates_20260912/flag_simple');p.mkdir(exist_ok=True)
u='https://storage.googleapis.com/dm-meshgraphnets/flag_simple/valid.tfrecord'
r=requests.get(u,headers={'Range':'bytes=0-11'},timeout=60);r.raise_for_status();assert r.status_code==206
n=struct.unpack('<Q',r.content[:8])[0];assert n<100_000_000
r=requests.get(u,headers={'Range':f'bytes=0-{n+15}'},timeout=90);r.raise_for_status();assert r.status_code==206 and len(r.content)==n+16
(p/'valid_first_record.tfrecord').write_bytes(r.content)
(p/'download_manifest.json').write_text(json.dumps(dict(url=u,byte_range=[0,n+15],bytes=n+16,sha256=hashlib.sha256(r.content).hexdigest(),note='검증 분할의 첫 TFRecord 레코드만 다운로드; 전체 데이터 아님'),indent=2,ensure_ascii=False))
print('FlagSimple 첫 궤적',n+16,'bytes',flush=True)
