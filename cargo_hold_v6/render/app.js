import * as THREE from 'three';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';
import {STLLoader} from 'three/examples/jsm/loaders/STLLoader.js';
import {RoundedBoxGeometry} from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import {mergeGeometries} from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import URDFLoader from 'urdf-loader';
const W=1920,H=1080;
const scene=new THREE.Scene();scene.background=new THREE.Color('#c9d5db');
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setSize(W,H);renderer.setPixelRatio(1);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.18;document.body.appendChild(renderer.domElement);
const camera=new THREE.PerspectiveCamera(40,W/H,.01,80);camera.up.set(0,0,1);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=false;
scene.add(new THREE.HemisphereLight(0xf4fbff,0x515c64,2.3));
for(const [c,p,i] of [[0xfff4e2,[-2,-4,7],3.0],[0xaed7f0,[3,3,5],2.0],[0xffffff,[6,-1,3],1.5]]){const l=new THREE.DirectionalLight(c,i);l.position.set(...p);scene.add(l)}
const ground=new THREE.Mesh(new THREE.PlaneGeometry(30,30),new THREE.MeshStandardMaterial({color:0xa8bac5,roughness:1}));ground.position.z=-1.6;scene.add(ground);
const env=new THREE.Group();scene.add(env);const holdgroups={};
const materials={};function mat(c){const key=c.toString();return materials[key]??=new THREE.MeshStandardMaterial({color:c,metalness:.25,roughness:.58})}
function box(size,pos,color,parent=env){const m=new THREE.Mesh(new THREE.BoxGeometry(...size),mat(color));m.position.set(...pos);parent.add(m);return m;}
function cyl(r,h,pos,color,parent=env,axis='z'){const m=new THREE.Mesh(new THREE.CylinderGeometry(r,r,h,16),mat(color));if(axis==='z')m.rotation.x=Math.PI/2;if(axis==='x')m.rotation.z=Math.PI/2;m.position.set(...pos);parent.add(m);return m;}
function stripe(a,b,c=0xf3bd33){const len=Math.hypot(b[0]-a[0],b[1]-a[1]);const m=box([len,.022,.0015],[(a[0]+b[0])/2,(a[1]+b[1])/2,.002],c);m.rotation.z=Math.atan2(b[1]-a[1],b[0]-a[0]);}
for(const [a,b]of [[[.08,-1],[1.98,-1]],[[1.98,-1],[1.98,1]],[[1.98,1],[.08,1]],[[.08,1],[.08,-1]]])stripe(a,b);
function label(text,size,pos,rot=[0,0,0],color='#203e4b',parent=env){const c=document.createElement('canvas');c.width=1024;c.height=128;const x=c.getContext('2d');x.fillStyle=color;x.font='bold 68px Arial';x.textAlign='center';x.fillText(text,512,92);const tex=new THREE.CanvasTexture(c);const mesh=new THREE.Mesh(new THREE.PlaneGeometry(size,size/8),new THREE.MeshBasicMaterial({map:tex,transparent:true,depthWrite:false,side:THREE.DoubleSide}));mesh.position.set(...pos);mesh.rotation.set(...rot);parent.add(mesh);return mesh;}
label('KEEP CLEAR / AREA PUTAR',1.6,[1,0,.005]);label('CARGO BAY 01',1.7,[4.49,0,.97],[Math.PI/2,0,-Math.PI/2]);
// Level service bridge. The mobile feeder is parked aside during entry / exit.
const bridge=new THREE.Group();scene.add(bridge);
box([3.2,2.15,.12],[1.4,-2.175,-.065],0x63717c,bridge);
for(const x of [-.1,1.4,2.9])for(const y of [-1.4,-3]){box([.10,.10,1.4],[x,y,-.8],0x43525e,bridge);box([.35,.35,.08],[x,y,-1.52],0x38434c,bridge)}
for(let i=0;i<30;i++)box([3.15,.008,.004],[1.4,-3.2+i*.069,-.002],0x83919b,bridge);
for(const x of [-.2,3]){box([.035,2.1,.035],[x,-2.2,.65],0xf3b83f,bridge);for(const y of [-3.2,-2.2,-1.2])box([.035,.035,.65],[x,y,.325],0xf3b83f,bridge)}
const feeder=new THREE.Group();scene.add(feeder);
box([.54,.8,.03],[0,0,.351],0x273641,feeder);
for(const x of [-.29,.29]){box([.04,.88,.06],[x,0,.31],0xbac7ce,feeder);box([.045,.045,1.75],[x,-.3,-.59],0x778994,feeder)}
for(const y of [-.39,.39])cyl(.025,.57,[0,y,.34],0x8495a0,feeder,'x');
for(let i=0;i<15;i++)box([.52,.006,.002],[0,-.35+i*.05,.368],0x455760,feeder);
const incline=new THREE.Group();incline.position.set(0,-.89,-.02);incline.rotation.x=Math.atan2(.72,1);feeder.add(incline);box([.54,1.23,.034],[0,0,0],0x354752,incline);for(const x of [-.29,.29])box([.045,1.28,.065],[x,0,-.015],0xaab9c2,incline);
box([.11,.16,.11],[.37,.28,.28],0x293642,feeder);cyl(.054,.08,[.32,.28,.28],0xa2b2bd,feeder,'x');
for(const x of [-.25,.25])for(const y of [-.3,.3])cyl(.035,.025,[x,y,-1.5],0x182832,feeder,'x');
// Visual-only 1 mm vertex clustering; original full CAD meshes remain in Gazebo/URDF.
function visualLOD(geo,cell=.001){const p=geo.getAttribute('position'),map=new Map(),pts=[],counts=[],ids=new Uint32Array(p.count);for(let i=0;i<p.count;i++){const x=p.getX(i),y=p.getY(i),z=p.getZ(i),key=Math.round(x/cell)+','+Math.round(y/cell)+','+Math.round(z/cell);let j=map.get(key);if(j===undefined){j=pts.length/3;map.set(key,j);pts.push(0,0,0);counts.push(0)}pts[j*3]+=x;pts[j*3+1]+=y;pts[j*3+2]+=z;counts[j]++;ids[i]=j;}for(let j=0;j<counts.length;j++)for(let k=0;k<3;k++)pts[j*3+k]/=counts[j];const idx=[];for(let i=0;i<ids.length;i+=3){const a=ids[i],b=ids[i+1],c=ids[i+2];if(a!==b&&a!==c&&b!==c)idx.push(a,b,c)}const out=new THREE.BufferGeometry();out.setAttribute('position',new THREE.Float32BufferAttribute(pts,3));out.setIndex(idx);out.computeVertexNormals();geo.dispose();return out;}
const colors=[0x2b768c,0xd78e35,0x658562,0xae5360,0x566c9d,0x7d687d,0xa5a299];
function bagTemplate(color){const g=new THREE.Group();const buckets=new Map();
 function add(geo,pos,c,rot=[0,0,0]){geo=geo.toNonIndexed();const M=new THREE.Matrix4().compose(new THREE.Vector3(...pos),new THREE.Quaternion().setFromEuler(new THREE.Euler(...rot)),new THREE.Vector3(1,1,1));geo.applyMatrix4(M);const list=buckets.get(c)||[];list.push(geo);buckets.set(c,list)}
 add(new RoundedBoxGeometry(.642,.352,.252,3,.026),[0,0,0],color);
 // Zipper seam, moulded ribs, corner bumpers, side handle and four spinner wheels.
 for(const y of [-.178,.178])add(new THREE.BoxGeometry(.572,.005,.008),[0,y,.012],0x25343b);
 for(const x of [-.320,.320])add(new THREE.BoxGeometry(.005,.305,.008),[x,0,.012],0x25343b);
 for(let i=0;i<7;i++)add(new RoundedBoxGeometry(.024,.26,.009,2,.004),[-.24+i*.08,0,.127],color);
 for(const x of [-.28,.28])for(const y of [-.14,.14]){add(new RoundedBoxGeometry(.06,.05,.014,2,.006),[x,y,.123],0x27333b);add(new THREE.CylinderGeometry(.014,.014,.018,12),[x,y,-.116],0x15242d,[Math.PI/2,0,0]);}
 add(new RoundedBoxGeometry(.17,.023,.025,2,.010),[0,-.179,.02],0x24333c);
 for(const x of [-.06,.06])add(new THREE.BoxGeometry(.015,.01,.04),[x,-.182,.02],0x9aa8ac);
 add(new THREE.BoxGeometry(.075,.05,.001),[.19,-.09,.133],0xe4dfd0);
 for(const[c,gs]of buckets){const m=new THREE.Mesh(mergeGeometries(gs),mat(c));g.add(m)}
 return g;}
const templates=colors.map(bagTemplate),active={};let robot,scenario,manifest;const errors=[];
const sliders={};
function followers(q){const h=.12+(q.lift_height_joint||0),a=Math.asin(h/.65)-Math.asin(.12/.65),x=Math.sqrt(.65**2-h*h)-Math.sqrt(.65**2-.12**2);return{...q,lower_slider_joint:x,upper_slider_joint:x,left_up_arm_joint:-a,right_up_arm_joint:-a,left_down_arm_joint:a,right_down_arm_joint:a};}
function sample(t){const f=scenario.frames;if(t>=f.at(-1).t)return structuredClone(f.at(-1));let i=0;while(i<f.length-2&&f[i+1].t<=t)i++;const a=f[i],b=f[i+1],u=(t-a.t)/(b.t-a.t),s=u*u*(3-2*u),q={},bags={};for(const k of new Set([...Object.keys(a.q),...Object.keys(b.q)]))q[k]=(1-s)*(a.q[k]||0)+s*(b.q[k]||0);for(const n of new Set([...Object.keys(a.bags),...Object.keys(b.bags)])){if(!a.bags[n])bags[n]=b.bags[n];else if(!b.bags[n]){if(s<1)bags[n]=a.bags[n]}else bags[n]=a.bags[n].map((v,j)=>(1-s)*v+s*b.bags[n][j]);}return{q,bags,base:a.base.map((v,j)=>(1-s)*v+s*b.base[j]),held:a.held&&b.held&&a.held.name===b.held.name?b.held:null,feeder_x:(1-s)*a.feeder_x+s*b.feeder_x,bridge_x:(1-s)*a.bridge_x+s*b.bridge_x,label:b.label,stage:b.stage,loaded:a.loaded,unloaded:a.unloaded};}
function setView(name,s){const b=s.base;let p,target;const before=s.stage==='ENTRY'&&b[1]<-.6||s.stage==='EXIT'&&b[1]<-.6;
 if(name==='overview'){p=[6.3,-6.7,5.6];target=[2.05,-.45,.25];camera.fov=39;}
 else if(name==='interior'){if(before){p=[.18,-2.9,1.0];target=[1,.15,.45];camera.fov=65}else{p=[.16,.83,1.035];target=[2.35,-.10,.43];camera.fov=69}}
 else {p=[b[0]-1.45,b[1]-1.75,1.55];target=[b[0]+.25,b[1],.45];camera.fov=49;}
 for(const[g,items]of Object.entries(holdgroups))for(const m of items)m.visible=name==='interior'?!['front_wall','door'].includes(g):!['front_wall','near_wall','roof','door'].includes(g);
 camera.position.set(...p);controls.target.set(...target);camera.updateProjectionMatrix();controls.update();}
const output=document.createElement('canvas');output.width=W;output.height=H;const ctx=output.getContext('2d');
window.setFrame=(t,pov='overview')=>{const s=sample(t);const defaults=Object.fromEntries(manifest.joints.filter(j=>j.type!=='fixed'&&!j.mimic).map(j=>[j.name,0]));robot.setJointValues({...defaults,...followers(s.q)});robot.position.set(...s.base.slice(0,3));robot.rotation.z=s.base[3];robot.updateMatrixWorld(true);
 if(s.held){const p=robot.links.jaw_frame_link.localToWorld(new THREE.Vector3(.34,0,s.held.rel));s.bags[s.held.name]=[...p.toArray(),s.base[3]+(s.q.conveyor_yaw_joint||0)]}
 for(const[n,g]of Object.entries(active)){const p=s.bags[n];g.visible=!!p;if(p){g.position.set(...p.slice(0,3));g.rotation.z=p[3]}}
 bridge.position.x=s.bridge_x;feeder.position.set(s.feeder_x,-1.5-(s.feeder_x-1)*1.1/3.2,0);setView(pov,s);renderer.render(scene,camera);
 ctx.drawImage(renderer.domElement,0,0);ctx.fillStyle='rgba(13,31,43,.94)';ctx.fillRect(0,0,W,94);ctx.fillStyle='#f6f7f2';ctx.font='bold 33px Arial';ctx.fillText('CARGO-LIFT  /  AIRCRAFT HOLD',45,42);ctx.font='19px Arial';ctx.fillStyle='#b5c9d4';ctx.fillText('V5 robot  •  V6 environment  •  4 load + 4 unload  •  generic bulk hold',46,73);
 ctx.textAlign='right';ctx.fillStyle='#fac468';ctx.font='bold 24px Arial';ctx.fillText(({overview:'01  OVERVIEW CUTAWAY',interior:'02  INTERIOR / DOOR',tracking:'03  ROBOT FOLLOW'})[pov],1874,41);ctx.font='19px Arial';ctx.fillStyle='#d4e1e7';ctx.fillText('LOAD '+s.loaded+'/4     UNLOAD '+s.unloaded+'/4     t = '+t.toFixed(1)+' s',1874,73);ctx.textAlign='left';
 ctx.fillStyle='rgba(13,31,43,.94)';ctx.fillRect(0,H-101,W,101);ctx.fillStyle='#fac468';ctx.font='bold 21px Arial';ctx.fillText(s.stage,45,H-66);ctx.fillStyle='#fff';ctx.font='25px Arial';ctx.fillText(s.label,210,H-65);ctx.fillStyle='#aec4ce';ctx.font='17px Arial';ctx.fillText('Animasi kinematik dari lintasan yang sama dengan Gazebo replay; bukan hasil uji gaya/kontak. Waktu video 10x.',45,H-28);ctx.fillStyle='#3b5666';ctx.fillRect(0,H-5,W,5);ctx.fillStyle='#edb858';ctx.fillRect(0,H-5,W*t/scenario.duration_s,5);
 window.lastState={...s,t,pov};return s.label;};
window.capture=()=>output.toDataURL('image/png');window.captureJPEG=()=>output.toDataURL('image/jpeg',.95);
async function start(){[scenario,manifest]=await Promise.all([fetch('../config/scenario.json').then(r=>r.json()),fetch('../config/design_manifest.json').then(r=>r.json())]);const hg=await fetch('../config/hold_geometry.json').then(r=>r.json());const stl=new STLLoader();
 await Promise.all(hg.meshes.map(async m=>{const geo=await stl.loadAsync('../'+m.mesh);const mesh=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color:new THREE.Color(...m.color),metalness:.18,roughness:.72,side:THREE.DoubleSide}));scene.add(mesh);(holdgroups[m.group]??=[]).push(mesh)}));
 const manager=new THREE.LoadingManager();manager.onError=u=>errors.push(u);const loader=new URDFLoader(manager);loader.packages={cargo_robot_description:'../ros2_ws/src/cargo_robot_description'};robot=await new Promise((ok,no)=>loader.load('../ros2_ws/src/cargo_robot_description/urdf/cargo_robot.urdf',ok,undefined,no));
 await new Promise(resolve=>{if(Object.values(robot.links).length)manager.onLoad=resolve;setTimeout(resolve,7000)});scene.add(robot);robot.traverse(o=>{if(o.isMesh){o.geometry=visualLOD(o.geometry);const c=o.material.color.clone().convertSRGBToLinear();o.material=new THREE.MeshStandardMaterial({color:c,metalness:.38,roughness:.48})}});
 for(const b of scenario.fixed_bags){const g=templates[b.color].clone();g.position.set(...b.pose.slice(0,3));g.rotation.z=b.pose[3];scene.add(g)}
 for(let i=1;i<=4;i++){const g=templates[i-1].clone();scene.add(g);active['active_'+i]=g;}
 window.debug={ready:true,errors,links:Object.keys(robot.links).length,duration:scenario.duration_s,triangles:renderer.info.render.triangles};window.setFrame(507,'overview');
}
start().catch(e=>{window.debug={ready:false,error:e.stack};console.error(e)});
