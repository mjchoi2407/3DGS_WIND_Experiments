import json,pathlib,hashlib,collections
import numpy as np,trimesh
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
ROOT=pathlib.Path('experiments/artifacts/datasets/mesh_candidates_extra_20260912')
OUT=pathlib.Path('experiments/mesh_candidate_audit/evidence/extra');OUT.mkdir(exist_ok=True,parents=True)
def topology(v,f):
 edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1)
 e,counts=np.unique(edges,axis=0,return_counts=True)
 g=coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(len(v),len(v))).tocsr()
 n,lab=connected_components(g,directed=False)
 labels=lab[f[:,0]];sizes=np.bincount(labels,minlength=n)
 boundary=e[counts==1]; bcnt=np.bincount(lab[boundary[:,0]],minlength=n)
 comps=[]
 for i in np.flatnonzero(sizes):
  ids=np.flatnonzero(lab==i);pts=v[ids];s=np.linalg.svd(pts-pts.mean(0),compute_uv=False)
  comps.append(dict(vertices=len(ids),faces=int(sizes[i]),boundary_edges=int(bcnt[i]),flatness=float(s[-1]/max(s[0],1e-30))))
 comps.sort(key=lambda x:x['faces'],reverse=True)
 return dict(vertices=len(v),faces=len(f),components=len(comps),boundary_edges=int((counts==1).sum()),nonmanifold_edges=int((counts>2).sum()),components_closed=sum(c['boundary_edges']==0 for c in comps),component_face_histogram=dict(collections.Counter(c['faces'] for c in comps)),components_detail=comps)
def meshstats(m):
 v=np.array(m.vertices);f=np.array(m.faces);vv,inv=np.unique(v,axis=0,return_inverse=True);ff=inv[f]
 t=topology(vv,ff)
 # Exact-coordinate weld only for diagnostics; source and UVs remain untouched.
 area=m.area_faces;length=np.linalg.norm(v[f]-v[f[:,[1,2,0]]],axis=2)
 q=4*np.sqrt(3)*area/np.maximum((length*length).sum(axis=1),1e-30)
 t.update(raw_vertices=len(v),bbox_extent=np.ptp(v,axis=0).tolist(),area=float(area.sum()),degenerate_faces=int((area<=max(float(area.max()),1e-30)*1e-12).sum()),duplicate_geometric_faces=int(len(ff)-len(np.unique(np.sort(ff,axis=1),axis=0))),triangle_quality_p01_p50=np.quantile(q,[.01,.5]).tolist(),finite=bool(np.isfinite(v).all()))
 return t
results=[]
for d in sorted(ROOT.iterdir()):
 paths=list(d.glob('*.gltf')) if d.is_dir() else []
 if not paths:continue
 p=paths[0];doc=json.loads(p.read_text());scene=trimesh.load_scene(p,process=False)
 textures=[]
 for imfile in (d/'textures').iterdir():
  try:
   with Image.open(imfile) as im:textures.append(dict(file=imfile.name,size=list(im.size),mode=im.mode))
  except Exception:pass
 mats=[]
 for mat in doc.get('materials',[]):
  b=mat.get('pbrMetallicRoughness',{}).get('baseColorTexture',{}).get('index'); uri=None
  if b is not None:uri=doc['images'][doc['textures'][b]['source']].get('uri')
  mats.append(dict(name=mat.get('name'),alphaMode=mat.get('alphaMode','OPAQUE'),doubleSided=mat.get('doubleSided',False),baseColorImage=uri))
 geoms=[]
 for name,m in scene.geometry.items():
  t=meshstats(m);t['raw_nonmanifold_edges']=topology(np.asarray(m.vertices),np.asarray(m.faces))['nonmanifold_edges'];t['name']=name;t['material']=getattr(m.visual.material,'name',None);uv=getattr(m.visual,'uv',None)
  t['uv_valid']=bool(uv is not None and len(uv)==len(m.vertices) and np.isfinite(uv).all());t['uv_range']=np.array([uv.min(0),uv.max(0)]).tolist() if uv is not None else None
  alphas=[x for x in (d/'textures').glob('*alpha*') if t['material'] and t['material'].lower() in x.name.lower()]
  if len(alphas)==1 and uv is not None:
   with Image.open(alphas[0]) as im:
    a=np.array(im);a=a.astype(float)/(65535 if a.dtype.itemsize>1 else 255)
   bcs=np.array([[1/3]*3,[.6,.2,.2],[.2,.6,.2],[.2,.2,.6],[.8,.1,.1],[.1,.8,.1],[.1,.1,.8]])
   uvs=np.einsum('sk,fkj->fsj',bcs,uv[m.faces]);h,w=a.shape
   ix=np.clip(np.rint(uvs[...,0]*(w-1)).astype(int),0,w-1);iy=np.clip(np.rint((1-uvs[...,1])*(h-1)).astype(int),0,h-1)
   visible=(a[iy,ix]>=.5).mean(1)
   t['alpha_visible_area_fraction_7samples']=float(np.sum(visible*m.area_faces)/m.area)
  geoms.append(t)
 result=dict(asset=d.name,nodes=doc.get('nodes'),mesh_count=len(geoms),faces=sum(x['faces'] for x in geoms),exact_weld_components=sum(x['components'] for x in geoms),materials=mats,textures=textures,geometries=geoms)
 results.append(result);print(d.name,'faces',result['faces'],'components',result['exact_weld_components'],[(x['name'],x['components'],round(x.get('alpha_visible_area_fraction_7samples',-1),3)) for x in geoms],flush=True)
(OUT/'polyhaven_structure.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
