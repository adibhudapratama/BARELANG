from pathlib import Path
import json,copy,math
import xml.etree.ElementTree as E
import cadquery as cq
R=Path(__file__).resolve().parents[1];hg=json.loads((R/'config/hold_geometry.json').read_text());sc=json.loads((R/'config/scenario.json').read_text())
def el(p,t,v=None,**a):
 n=E.SubElement(p,t,a)
 if v is not None:n.text=str(v)
 return n
def visual(link,name,kind,dim,pose,col):
 v=el(link,'visual',name=name);el(v,'pose',' '.join(map(str,pose)));g=el(v,'geometry');k=el(g,kind)
 if kind=='box':el(k,'size',' '.join(map(str,dim)))
 elif kind=='cylinder':el(k,'radius',dim[0]);el(k,'length',dim[1])
 elif kind=='mesh':el(k,'uri',dim)
 ma=el(v,'material');c=' '.join(map(str,[*col,1]));el(ma,'ambient',c);el(ma,'diffuse',c);return v
def model(w,name,static=True):
 m=el(w,'model',name=name);el(m,'static',str(static).lower());l=el(m,'link',name='body');return m,l
# Detailed rounded luggage reusable mesh groups, metres.
d=R/'models/luggage/meshes';d.mkdir(parents=True,exist_ok=True)
body=cq.Workplane('XY').box(.642,.352,.252).edges().fillet(.025).val();details=[]
for x in [-.24+i*.08 for i in range(7)]:details.append(cq.Workplane('XY').box(.024,.26,.009).edges('|Z').fillet(.004).translate((x,0,.127)).val())
body=cq.Compound.makeCompound([body,*details]);trim=[]
for y in [-.178,.178]:trim.append(cq.Workplane('XY').box(.572,.005,.008).translate((0,y,.012)).val())
for x in [-.32,.32]:trim.append(cq.Workplane('XY').box(.005,.305,.008).translate((x,0,.012)).val())
trim.append(cq.Workplane('XY').box(.17,.023,.025).edges('|Z').fillet(.01).translate((0,-.179,.02)).val())
for x in [-.28,.28]:
 for y in [-.14,.14]:
  trim.append(cq.Workplane('XY').box(.06,.05,.014).edges('|Z').fillet(.006).translate((x,y,.123)).val())
  trim.append(cq.Solid.makeCylinder(.014,.018,cq.Vector(x,y-.009,-.116),cq.Vector(0,1,0)))
cq.exporters.export(body,str(d/'shell.stl'),tolerance=.0006,angularTolerance=.2);cq.exporters.export(cq.Compound.makeCompound(trim),str(d/'trim.stl'),tolerance=.0006,angularTolerance=.2)
colors=[[.17,.46,.55],[.84,.56,.21],[.4,.52,.38],[.68,.33,.38],[.34,.42,.62],[.49,.41,.49],[.65,.64,.6]]
for cut in [False,True]:
 root=E.Element('sdf',version='1.9');w=el(root,'world',name='cargo_hold')
 phy=el(w,'physics',name='timing',type='ignored');el(phy,'max_step_size',.01);el(phy,'real_time_factor',1);el(w,'gravity','0 0 -9.81')
 # No Physics plugin in the deterministic replay world: pose trajectories are prescribed.
 el(w,'plugin',filename='gz-sim-scene-broadcaster-system',name='gz::sim::systems::SceneBroadcaster');el(w,'plugin',filename='gz-sim-user-commands-system',name='gz::sim::systems::UserCommands');el(w,'plugin',filename='libScenarioReplay.so',name='cargo::ScenarioReplay')
 scene=el(w,'scene');el(scene,'ambient','.65 .68 .7 1');el(scene,'background','.70 .76 .8 1');el(scene,'shadows','true')
 sun=el(w,'light',name='key',type='directional');el(sun,'pose','0 0 5 0 0 0');el(sun,'diffuse','.95 .96 1 1');el(sun,'specular','.2 .2 .2 1');el(sun,'direction','-.4 .3 -1');el(sun,'cast_shadows','true')
 _,l=model(w,'aircraft_hold')
 for m in hg['meshes']:
  if cut and m['group'] in ['near_wall','front_wall','roof','door']:continue
  visual(l,m['name'],'mesh','model://aircraft_hold/meshes/'+Path(m['mesh']).name,[0]*6,m['color'])
 _,l=model(w,'service_bridge',False);visual(l,'deck','box',[3.2,2.15,.12],[1.4,-2.175,-.065,0,0,0],[.4,.45,.49])
 for x in [-.1,1.4,2.9]:
  for y in [-1.4,-3]:visual(l,f'leg{x}{y}','box',[.10,.1,1.4],[x,y,-.8,0,0,0],[.28,.33,.37])
 for x in [-.2,3]:
  visual(l,'guard'+str(x),'box',[.035,2.1,.035],[x,-2.2,.65,0,0,0],[.95,.72,.24])
  for y in [-3.2,-2.2,-1.2]:visual(l,f'post{x}{y}','box',[.035,.035,.65],[x,y,.325,0,0,0],[.95,.72,.24])
 _,l=model(w,'external_feeder',False);el(l,'pose','4.2 -2.6 0 0 0 0')
 visual(l,'belt','box',[.54,.8,.03],[0,0,.351,0,0,0],[.15,.21,.26])
 for x in [-.29,.29]:
  visual(l,'rail'+str(x),'box',[.04,.88,.06],[x,0,.31,0,0,0],[.73,.78,.81]);visual(l,'leg'+str(x),'box',[.045,.045,1.75],[x,-.3,-.59,0,0,0],[.46,.54,.58])
 visual(l,'inclined_belt','box',[.54,1.23,.034],[0,-.89,-.02,math.atan2(.72,1),0,0],[.21,.28,.32])
 visual(l,'servo_motor','box',[.11,.16,.11],[.37,.28,.28,0,0,0],[.16,.21,.26])
 for y in [-.39,.39]:visual(l,'drum'+str(y),'cylinder',[.025,.57],[0,y,.34,0,math.pi/2,0],[.52,.58,.63])
 for x in [-.25,.25]:
  for y in [-.3,.3]:visual(l,f'wheel{x}{y}','cylinder',[.035,.025],[x,y,-1.5,0,math.pi/2,0],[.09,.15,.2])
 rm=E.parse(R/'models/cargo_robot/model.sdf').getroot().find('model');rm=copy.deepcopy(rm);rm.set('name','cargo_robot_replay')
 for n in list(rm):
  if n.tag!='link':rm.remove(n)
 for lnk in rm.findall('link'):
  for n in list(lnk):
   if n.tag not in ['pose','visual']:lnk.remove(n)
 w.append(rm)
 for b in sc['fixed_bags']+[dict(name=f'active_{i}',pose=[0,0,-10,0],color=i-1) for i in range(1,5)]:
  _,l=model(w,b['name'],not b['name'].startswith('active'));p=b['pose'];el(l,'pose',' '.join(map(str,[*p[:3],0,0,p[3]])))
  visual(l,'case','mesh','model://luggage/meshes/shell.stl',[0]*6,colors[b['color']]);visual(l,'details','mesh','model://luggage/meshes/trim.stl',[0]*6,[.14,.2,.24])
 gui=el(w,'gui',fullscreen='false');plug=el(gui,'plugin',filename='MinimalScene',name='3D View');el(plug,'engine','ogre2');el(plug,'scene','scene');el(plug,'ambient_light','.65 .68 .7');el(plug,'background_color','.70 .76 .8');el(plug,'camera_pose','5.9 -6.5 4.8 0 .48 2.15')
 el(gui,'plugin',filename='CameraTracking',name='Camera Tracking');rec=el(gui,'plugin',filename='VideoRecorder',name='Video Recorder');rv=el(rec,'record_video');el(rv,'use_sim_time','true');el(rv,'lockstep','true');el(rv,'bitrate',12000000)
 el(gui,'plugin',filename='GzSceneManager',name='Scene Manager');el(gui,'plugin',filename='InteractiveViewControl',name='Interactive View Control');el(gui,'plugin',filename='SceneTree',name='Scene Tree');el(gui,'plugin',filename='WorldControl',name='World Control');el(gui,'plugin',filename='WorldStats',name='World Stats')
 E.indent(root);E.ElementTree(root).write(R/'worlds'/('cargo_hold_cutaway.sdf' if cut else 'cargo_hold_full.sdf'),encoding='utf-8',xml_declaration=True)
print('Built detailed bags and two replay worlds')
