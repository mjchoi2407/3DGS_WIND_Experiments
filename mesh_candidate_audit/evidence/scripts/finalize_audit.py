import pathlib,json,hashlib,numpy as np,trimesh
from PIL import Image
ROOT=pathlib.Path('experiments/artifacts/datasets/mesh_candidates_20260912');OUT=pathlib.Path('experiments/mesh_candidate_audit/evidence')
x=json.loads((OUT/'polyhaven_structure.json').read_text())
for a in x:
 s=trimesh.load_scene(ROOT/a['asset']/(a['asset']+'_4k.gltf'),process=False)
 for g in a['geometries']:
  m=s.geometry[g['name']];e=np.sort(m.edges,axis=1);_,cnt=np.unique(e,axis=0,return_counts=True)
  g['raw_index_nonmanifold_edges']=int((cnt>2).sum());g['raw_index_boundary_edges']=int((cnt==1).sum())
  g['raw_index_winding_consistent']=bool(m.is_winding_consistent)
 # No embedded alpha in downloaded JPG; supplemental PNG is not referenced by glTF.
 for m in a['materials']:
  if m['baseColorImage']:
   with Image.open(ROOT/a['asset']/m['baseColorImage']) as im:m['base_color_has_alpha']='A' in im.getbands()
(OUT/'polyhaven_structure.json').write_text(json.dumps(x,ensure_ascii=False,indent=2))
files=[]
for p in sorted(ROOT.rglob('*')):
 if not p.is_file() or p.suffix=='.txt' or '__MACOSX' in p.parts or p.name.startswith('.'):continue
 # Inventory downloaded archives and canonical glTF assets, not every extracted file.
 if 'berkeley_garments' in p.parts:continue
 files.append(dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
report=dict(date='2026-09-12',artifact_root='experiments/artifacts/datasets/mesh_candidates_20260912',polyhaven_downloads=json.loads((ROOT/'download_manifest.json').read_text()),other_sources={'berkeley':{'url':'http://graphics.berkeley.edu/resources/GarmentLibrary/garmentlibrary.zip','zip_crc_verified':True,'note':'HTTPS 인증서 호스트 불일치. 공식 HTTP 배포 경로 사용; SHA256은 로컬 보존값이며 배포자 인증 해시는 아님.'},'flag':json.loads((ROOT/'flag_simple/download_manifest.json').read_text()),'ficus':{'status':'blocked','reason':'공식 다운로드 페이지 Sign in to download; 원본 미다운로드'},'rose':{'status':'blocked','reason':'Sketchfab 웹 403; 공개 download API 202 빈 응답; 원본 미다운로드'},'clothes_line':{'status':'blocked','reason':'Sketchfab 웹 403; 공개 download API 202 빈 응답; 원본 미다운로드'}},files=files,software={'numpy':np.__version__,'trimesh':trimesh.__version__},limits=['물리 시뮬레이션 미실행','셀프 교차·두께·재료 물성 미검증','렌더러 통합·광학 정확도 미검증','정확히 같은 위치의 정점 병합은 진단용 사본에서만 수행; 원본 미변경'])
(OUT/'acquisition_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
for a in x:
 print(a['asset'],'raw nonmanifold',sum(g['raw_index_nonmanifold_edges'] for g in a['geometries']),'weld nonmanifold',sum(g['nonmanifold_edges'] for g in a['geometries']))
