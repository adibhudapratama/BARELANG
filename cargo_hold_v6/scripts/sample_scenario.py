from pathlib import Path
import json,math,bisect
import numpy as np
from kinematics import fk
R=Path(__file__).resolve().parents[1]
D=json.loads((R/'config/scenario.json').read_text());F=D['frames'];TS=[s['t'] for s in F]
def sample(t):
 if t>=TS[-1]:return dict(F[-1])
 i=max(0,bisect.bisect_right(TS,t)-1);a,b=F[i],F[i+1];u=(t-a['t'])/(b['t']-a['t']);s=u*u*(3-2*u)
 q={k:(1-s)*a['q'].get(k,0)+s*b['q'].get(k,0) for k in set(a['q'])|set(b['q'])}
 base=[(1-s)*x+s*y for x,y in zip(a['base'],b['base'])];bags={}
 for n in set(a['bags'])|set(b['bags']):
  if n not in a['bags']:bags[n]=b['bags'][n]
  elif n not in b['bags']:
   if s<1:bags[n]=a['bags'][n]
  else:bags[n]=[(1-s)*x+s*y for x,y in zip(a['bags'][n],b['bags'][n])]
 held=b['held'] if a['held'] and b['held'] and a['held']['name']==b['held']['name'] else None
 if held:
  mat=fk(q,base)['jaw_frame_link'];p=mat@np.array([.34,0,held['rel'],1]);bags[held['name']]=list(p[:3])+[base[3]+q.get('conveyor_yaw_joint',0)]
 return dict(t=t,q=q,base=base,bags=bags,held=held,feeder_x=(1-s)*a['feeder_x']+s*b['feeder_x'],bridge_x=(1-s)*a['bridge_x']+s*b['bridge_x'],label=b['label'],stage=b['stage'],loaded=a['loaded'],unloaded=a['unloaded'])
if __name__=='__main__':
 from scipy.spatial.transform import Rotation
 import csv
 m=json.loads((R/'config/design_manifest.json').read_text());links=['base_link']+[j['child'] for j in m['joints']]
 tracks=[['cargo_robot_replay',n] for n in links]+[[f'active_{i}','body'] for i in range(1,5)]+[['external_feeder','body'],['service_bridge','body']]
 (R/'config/tracks.json').write_text(json.dumps(tracks,indent=2))
 with (R/'config/trajectory.csv').open('w') as f:
  f.write('# t_s; each track: x y z qw qx qy qz; tracks in tracks.txt; SI\n')
  for n,t in enumerate(np.arange(0,D['duration_s']+.05,.1)):
   s=sample(float(t));trans=fk(s['q'],s['base']);vals=[f'{t:.1f}']
   for link in links:
    mat=trans[link];quat=Rotation.from_matrix(mat[:3,:3]).as_quat();v=list(mat[:3,3])+[quat[3],*quat[:3]];vals.extend(f'{float(x):.7f}' for x in v)
   for i in range(1,5):
    p=s['bags'].get(f'active_{i}',[0,0,-10,0]);vals.extend(f'{float(x):.7f}' for x in [*p[:3],math.cos(p[3]/2),0,0,math.sin(p[3]/2)])
   vals.extend(f'{float(x):.7f}' for x in [s['feeder_x'],-1.5-(s['feeder_x']-1)*1.1/3.2,0,1,0,0,0]);vals.extend(f'{float(x):.7f}' for x in [s['bridge_x'],0,0,1,0,0,0]);f.write(','.join(vals)+'\n')
 (R/'config/tracks.txt').write_text('\n'.join('/'.join(t) for t in tracks)+'\n')
 print('Generated',n+1,'samples with',len(tracks),'tracks')
