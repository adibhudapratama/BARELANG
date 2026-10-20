"""Generic bulk cargo hold, SI scene metadata and real OCCT STEP solids.
Not an OEM aircraft model. CAD length unit millimetres; mesh metres.
"""
from pathlib import Path
import json, math
import cadquery as cq
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs, STEPControl_Reader
from OCP.Interface import Interface_Static
R=Path(__file__).resolve().parents[1]
D=R/'models/aircraft_hold/meshes';D.mkdir(parents=True,exist_ok=True)
parts=[]
def add(name,s,col,group='floor'):
 if isinstance(s,cq.Workplane):s=s.val()
 assert s.isValid() and s.Volume()>0,name
 parts.append(dict(name=name,shape=s,color=col,group=group))
def box(name,size,pos,col,group='floor',r=0):
 s=cq.Workplane('XY').box(*size)
 if r:s=s.edges('|Z').fillet(r)
 add(name,s.translate(pos),col,group)
def tube(name,r,h,pos,col,group='floor',axis=(0,0,1)):
 add(name,cq.Solid.makeCylinder(r,h,cq.Vector(*pos),cq.Vector(*axis)),col,group)
# Recessed panelled floor; finished walkable surface exactly z=0.
box('floor_sandwich',[4500,2200,45],[2250,0,-34.5],[.35,.4,.44])
for i in range(9):
 for j in range(4):
  x=250+500*i;y=-825+550*j
  box(f'floor_panel_{i}_{j}',[496,546,12],[x,y,-6],[.46+.025*(i%2),.49,.51],r=4)
  for dx in [-230,230]:
   for dy in [-252,252]:tube(f'flush_fastener_{i}_{j}_{dx}_{dy}',4,1.5,(x+dx,y+dy,-1.5),[.17,.19,.2])
# Recessed tie-down rails, flush to avoid becoming robot obstacles.
for y in [-1010,1010]:
 box('tie_down_recess_'+str(y),[4440,28,4],[2250,y,-2],[.13,.16,.18])
 for i,x in enumerate(range(120,4400,180)):
  tube(f'tie_socket_{y}_{i}',9,2,(x,y,-2),[.65,.68,.7])
  tube(f'tie_socket_hole_{y}_{i}',4,2.2,(x,y,-2.1),[.08,.09,.1])
# Bowed sides widen above the floor. Split port wall around the 1.30 m side door.
def profile(sign,z0=0,z1=1200,thick=18):
 zs=[z0+(z1-z0)*i/36 for i in range(37)]
 inner=[(sign*(1100+250*math.sin(math.pi*z/2400)),z) for z in zs]
 outer=[(sign*(1100+250*math.sin(math.pi*z/2400)+thick),z) for z in reversed(zs)]
 return inner+outer
for side in [-1,1]:
 spans=[(0,350),(1650,4500)] if side==-1 else [(0,4500)]
 for n,(a,b) in enumerate(spans):
  s=cq.Workplane('YZ').polyline(profile(side)).close().extrude(b-a).translate((a,0,0))
  add(f'curved_liner_{side}_{n}',s,[.76,.79,.78], 'near_wall' if side==-1 else 'far_wall')
 if side==-1:
  add('door_header_liner',cq.Workplane('YZ').polyline(profile(side,1050,1200)).close().extrude(1300).translate((350,0,0)),[.76,.79,.78],'near_wall')
 for x in range(60,4500,250):
  if side==-1 and 320<x<1680:continue
  rib=cq.Workplane('YZ').polyline(profile(side,0,1200,35)).close().extrude(25).translate((x,0,0))
  add(f'external_former_{side}_{x}',rib,[.35,.4,.43],'near_wall' if side==-1 else 'far_wall')
  for z in [150,450,750,1050]:
   y=side*(1100+250*math.sin(math.pi*z/2400)+20)
   tube(f'rivet_{side}_{x}_{z}',4,8,(x+12,y,z),[.65,.68,.7],'near_wall' if side==-1 else 'far_wall',axis=(0,side,0))
# Bulkheads and removable ceiling panels.
for x,gr in [(-18,'front_wall'),(4518,'rear_wall')]:
 box(gr,[36,2700,1200],[x,0,600],[.72,.76,.76],gr)
 for y in [-900,-450,0,450,900]:box(f'{gr}_stiffener_{y}',[22,24,1140],[x+(24 if x>0 else -24),y,600],[.38,.43,.46],gr)
for i in range(9):
 box(f'ceiling_panel_{i}',[496,2700,14],[250+i*500,0,1207],[.78,.80,.79],'roof',r=4)
 box(f'ceiling_frame_{i}',[28,2780,28],[30+i*500,0,1234],[.36,.41,.44],'roof')
for side in [-1,1]:
 for i in range(5):
  box(f'LED_housing_{side}_{i}',[650,36,16],[400+i*820,side*810,1186],[.24,.29,.31],'roof',r=8)
  box(f'LED_diffuser_{side}_{i}',[620,22,4],[400+i*820,side*810,1177],[.95,.98,1],'roof',r=4)
# Side-door frame lies outside the clear 1.30 x 1.05 m aperture.
for x in [327,1673]:box(f'door_jamb_{x}',[42,80,1080],[x,-1130,540],[.36,.42,.46],'near_wall',r=4)
box('door_header',[1384,75,45],[1000,-1280,1075],[.36,.42,.46],'near_wall',r=4)
box('flush_sill',[1300,95,8],[1000,-1132,-4],[.68,.7,.7])
# Open door hung above the service bridge, represented in open state only.
box('open_door_skin',[1270,1000,25],[1000,-1790,1330],[.83,.85,.84],'door',r=20)
for x in [520,1480]:
 box(f'door_reinforcement_{x}',[25,900,25],[x,-1790,1355],[.38,.43,.46],'door')
 tube(f'door_hinge_{x}',20,95,(x-47.5,-1290,1320),[.52,.56,.6],'door',axis=(1,0,0))
# Caution threshold strip / door numbering plate, no intrusion into travel surface.
box('threshold_mark',[1290,20,1],[1000,-1095,-.5],[.97,.69,.12])
box('identification_plate',[240,3,90],[2050,-1170,980],[.12,.2,.25],'near_wall',r=1)
# Grouped, correctly-scaled meshes shared by Gazebo and HD renderer.
manifest=[]
for g in sorted({p['group'] for p in parts}):
 cs=sorted({tuple(p['color']) for p in parts if p['group']==g})
 for j,col in enumerate(cs):
  ps=[p for p in parts if p['group']==g and tuple(p['color'])==col]
  shape=cq.Compound.makeCompound([p['shape'] for p in ps]);fn=f'{g}_{j}.stl'
  cq.exporters.export(shape.scale(.001),str(D/fn),tolerance=.0004,angularTolerance=.15)
  manifest.append(dict(name=f'{g}_{j}',group=g,color=list(col),mesh='models/aircraft_hold/meshes/'+fn,parts=len(ps)))
def step(path,ps):
 shape=cq.Compound.makeCompound([p['shape'] for p in ps])
 Interface_Static.SetCVal_s('write.step.schema','AP214IS');Interface_Static.SetCVal_s('write.step.unit','MM');Interface_Static.SetIVal_s('write.step.assembly',0)
 w=STEPControl_Writer();w.Transfer(shape.wrapped,STEPControl_AsIs);temp=path.with_suffix('.step.tmp');assert int(w.Write(str(temp)))==1
 path.write_bytes(temp.read_bytes());temp.unlink()
 r=STEPControl_Reader();assert int(r.ReadFile(str(path)))==1;r.TransferRoots();s=cq.Shape.cast(r.OneShape())
 solids=s.Solids();assert len(solids)==len(shape.Solids()) and all(x.isValid() and x.Volume()>0 for x in solids)
 return dict(file=path.name,solids=len(solids),valid=True,units='mm',volume_mm3=s.Volume())
checks=[step(R/'cad/Bagasi_Pesawat_Generic_Full.step',parts),step(R/'cad/Bagasi_Pesawat_Generic_Cutaway.step',[p for p in parts if p['group'] not in ['near_wall','front_wall','roof','door']])]
(R/'config/hold_geometry.json').write_text(json.dumps(dict(meshes=manifest,dimensions=dict(length_m=4.5,floor_width_m=2.2,height_m=1.2,door_width_m=1.3,door_height_m=1.05),parts=len(parts),oem_aircraft=False),indent=2))
(R/'validation/hold_step_validation.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(dict(parts=len(parts),mesh_groups=len(manifest),step_checks=checks),indent=2))
