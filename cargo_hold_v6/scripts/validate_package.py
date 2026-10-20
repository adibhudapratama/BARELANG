from pathlib import Path
import json,xml.etree.ElementTree as E,subprocess,py_compile,math
import numpy as np
R=Path(__file__).resolve().parents[1]
checks=[]
def check(n,b,**detail):checks.append(dict(name=n,passed=bool(b),**detail))
for p in (R/'worlds').glob('*.sdf'):
 r=subprocess.run(['gz','sdf','-k',str(p)],capture_output=True,text=True);check('SDF '+p.name,r.returncode==0,output=r.stdout.strip(),error=r.stderr.strip())
 for u in E.parse(p).findall('.//mesh/uri'):
  if u.text.startswith('model://'):check('mesh '+u.text,(R/'models'/u.text[8:]).is_file())
u=E.parse(R/'ros2_ws/src/cargo_robot_description/urdf/cargo_robot.urdf').getroot();links=u.findall('link');joints=u.findall('joint');ln={x.get('name') for x in links};children={j.find('child').get('link') for j in joints}
check('URDF tree',len(links)==71 and len(joints)==70 and ln-children=={'base_link'},links=len(links),joints=len(joints))
for mesh in u.findall('.//mesh'):
 f=mesh.get('filename').replace('package://cargo_robot_description/','');check('URDF mesh '+f,(R/'ros2_ws/src/cargo_robot_description'/f).is_file())
for p in [*R.glob('scripts/*.py'),*R.glob('cad/*.py')]:
 try:py_compile.compile(str(p),doraise=True);b=True
 except Exception:b=False
 check('Python '+p.name,b)
# Actual Gazebo ECM poses recorded by the compiled plugin versus CSV source.
probe=np.loadtxt(R/'validation/ecm_probe.csv',delimiter=',');want_times=set(np.round(probe[:,0],5));expected=[]
with (R/'config/trajectory.csv').open() as f:
 for line in f:
  if line.startswith('#'):continue
  t=float(line.split(',',1)[0])
  if round(t,5) in want_times:expected.append(np.fromstring(line,sep=','))
expected=np.array(expected);a=expected[:,1:].reshape(len(expected),-1,7);b=probe[:,1:].reshape(len(probe),-1,7)
poserr=float(np.max(np.abs(a[:,:,:3]-b[:,:,:3])))
# q and -q encode the same rotation; Slerp may choose the opposite sign.
qerr=float(np.max(np.minimum(np.max(np.abs(a[:,:,3:]-b[:,:,3:]),axis=2),np.max(np.abs(a[:,:,3:]+b[:,:,3:]),axis=2))))
err=max(poserr,qerr)
check('compiled plugin on SDF-created Gazebo ECM',expected.shape==probe.shape and err<1e-6,checkpoint_rows=len(probe),tracks=(probe.shape[1]-1)//7,max_position_error_m=poserr,max_sign_invariant_quaternion_error=qerr,full_server=False)
cl=json.loads((R/'validation/scenario_clearance.json').read_text());check('sampled other-luggage clearance',cl['collisions_count']==0,samples=cl['samples'])
s=json.loads((R/'config/scenario.json').read_text());check('4 loading and 4 unloading',s['frames'][-1]['loaded']==4 and s['frames'][-1]['unloaded']==4,peak_bags=s['peak_count'],fixed_remaining=s['fixed_count'])
check('same replay duration',float(probe[-1,0])==s['duration_s'],duration_s=s['duration_s'])
result=dict(passed=sum(c['passed'] for c in checks),failed=[c for c in checks if not c['passed']],checks=checks,server_status='Blocked by environment network socket restriction: getifaddrs / ZeroMQ ip_resolver Operation not permitted. No completed Gazebo Server or GUI run.',tested_gazebo='Harmonic 8.15.0',video_source='Three.js native CAD rendering of same scenario; not Gazebo recording')
(R/'validation/package_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
if result['failed']:raise SystemExit(1)
