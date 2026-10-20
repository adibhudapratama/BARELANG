from pathlib import Path
import json,itertools,math
import numpy as np
from sample_scenario import sample,D
from kinematics import fk
R=Path(__file__).resolve().parents[1];B=json.loads((R/'config/component_bounds.json').read_text());names=list(B)
groups={}
for i,n in enumerate(names):groups.setdefault(B[n]['link'],[]).append(i)
corners=np.array([list(itertools.product(*zip(B[n]['lo'],B[n]['hi']))) for n in names])
fixed={b['name']:b['pose'] for b in D['fixed_bags']};bad=[];highest=0;minwall=99
for t in np.linspace(0,D['duration_s'],2203):
 s=sample(float(t));tf=fk(s['q'],s['base']);lo=np.empty((len(names),3));hi=lo.copy()
 for link,ix in groups.items():
  m=tf[link];p=corners[ix]@m[:3,:3].T+m[:3,3];lo[ix]=p.min(1);hi[ix]=p.max(1)
 inside=(hi[:,1]>-1.10)&(lo[:,0]>=0)&(hi[:,0]<=4.5)
 if inside.any():highest=max(highest,float(hi[inside,2].max()))
 # Other luggage vs all physical part AABBs. Intended active target contacts
 # are excluded ONLY for pad and supporting blade surfaces when touching.
 for n,p in {**fixed,**s['bags']}.items():
  if p[2]<0:continue
  if s['held'] and n==s['held']['name']:continue # previously checked v5 payload corridor, tested separately
  a=p[3];ext=np.array([abs(math.cos(a))*.325+abs(math.sin(a))*.18,abs(math.sin(a))*.325+abs(math.cos(a))*.18,.13])
  blo=np.array(p[:3])-ext;bh=np.array(p[:3])+ext
  # Strip 2 mm at bottom/top: intentional support contacts, not intrusion.
  blo[2]+=.002;bh[2]-=.002
  hits=np.flatnonzero((np.minimum(hi,bh)-np.maximum(lo,blo)>.0002).all(1))
  if len(hits):
   # On active receiving/releasing bags allow only pad contacts; not posts/rails.
   hn=[names[i] for i in hits if not(n.startswith('active') and ('pad_' in names[i] or 'left_pad' in names[i] or 'right_pad' in names[i]))]
   if hn:bad.append(dict(t=round(float(t),2),label=s['label'],bag=n,parts=hn[:10]))
result=dict(samples=2203,cad_parts=len(names),fixed_bags=len(fixed),highest_sampled_robot_point_m=highest,collisions_count=len(bad),collisions=bad[:100],scope='Conservative transformed CAD-part AABBs versus other luggage; carried bag excluded (v5 passage validation). Discrete rigid-envelope check, not contact simulation.')
(R/'validation/scenario_clearance.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='collisions'},indent=2));print(json.dumps(bad[:8],indent=2))
