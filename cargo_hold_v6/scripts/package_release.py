from pathlib import Path
import json,zipfile,hashlib,shutil
R=Path(__file__).resolve().parents[1];O=R.parent
# Build reproducible source/data packages; machine-specific build and intermediate frames excluded.
def files(include_video=True):
 for p in sorted(R.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(R)
  if any(x in ['build','node_modules','__pycache__','.venv'] or x.startswith('frames_') for x in rel.parts):continue
  if rel.suffix in ['.pyc','.zip','.o','.so'] or rel.name=='ecm_probe.csv':continue
  if not include_video and rel.parts[0]=='video':continue
  yield p,rel
assert not json.loads((R/'validation/package_validation.json').read_text())['failed']
for v in ['overview','interior','tracking']:
 render=json.loads((R/'validation'/f'render_{v}.json').read_text());assert not render['errors'] and render['frames']==662
 d=json.loads((R/'validation'/f'video_{v}.json').read_text());assert d['width']==1920 and d['height']==1080 and d['duration_s']>109
for p in R.glob('cad/*.step'):assert p.stat().st_size>1000000
# Per-file checksums, useful for detecting incomplete copies.
items=[(p,rel) for p,rel in files() if rel.name!='SHA256SUMS.txt']
(R/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(rel)+'\n' for p,rel in items))
results=[]
for name,with_video in [('Cargo_Hold_v6_Gazebo_Full.zip',True)]:
 path=O/name
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p,rel in files(with_video):
   # Videos already compressed: avoid spending time recompressing.
   z.write(p,str(Path('cargo_hold_v6')/rel),compress_type=zipfile.ZIP_STORED if p.suffix=='.mp4' else zipfile.ZIP_DEFLATED)
 with zipfile.ZipFile(path) as z:assert z.testzip() is None;count=len(z.namelist())
 results.append(dict(file=name,bytes=path.stat().st_size,files=count,crc_passed=True,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(O/'release_validation_v6.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
