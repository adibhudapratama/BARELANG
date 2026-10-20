"""Encode native 1920x1080 CAD frames; 6 fps rendering -> 24 fps temporal interpolation.
Titles remain sampled, avoiding optical-flow deformation of changing text.
Can encode while capture.cjs is still producing frames.
"""
from pathlib import Path
import subprocess,json,time,sys,math,tempfile,os
R=Path(__file__).resolve().parents[1];pov=sys.argv[1] if len(sys.argv)>1 else 'overview';sc=json.loads((R/'config/scenario.json').read_text());fps=6;n=math.ceil(sc['duration_s']/10*fps)+1
name={'overview':'01_Overview_HD.mp4','interior':'02_Interior_HD.mp4','tracking':'03_Robot_Follow_HD.mp4'}[pov]
# Avoid interpolating the caption bands. Use native frames for captions and temporal interpolation for geometry.
flt='[0:v]split=3[a][b][c];[a]crop=1920:94:0:0,fps=24[top];[b]crop=1920:884:0:94,minterpolate=fps=24:mi_mode=blend[mid];[c]crop=1920:102:0:978,fps=24[bottom];[top][mid][bottom]vstack=inputs=3:shortest=1,format=yuv420p[v]'
fd,tmpname=tempfile.mkstemp(prefix='encode_',suffix='.mp4',dir=R/'video');os.close(fd);temporary=Path(tmpname)
cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-threads','1','-f','image2pipe','-framerate','6','-vcodec','mjpeg','-i','-','-filter_complex_threads','1','-filter_complex',flt,'-map','[v]','-c:v','libx264','-preset','fast','-crf','18','-threads','1','-movflags','+faststart',str(temporary)]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for i in range(n):
 path=R/'render'/('frames_'+pov)/f'{i:05d}.jpg';deadline=time.monotonic()+1800
 while True:
  if path.exists():
   data=path.read_bytes()
   if len(data)>1000 and data[-2:]==b'\xff\xd9':break
  if time.monotonic()>deadline:p.kill();raise RuntimeError(f'Timeout waiting for {path}')
  time.sleep(.25)
 p.stdin.write(data)
 if i%100==0:print(pov,'encoded input',i,'/',n,flush=True)
# Repeat the last native frame twice so minterpolate flushes the final pose.
p.stdin.write(data);p.stdin.write(data);p.stdin.close();rc=p.wait()
if rc:raise SystemExit(rc)
# Commit a fresh file atomically; do not reuse an interrupted encoder's output inode.
subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(temporary)],check=True,stdout=subprocess.DEVNULL)
os.replace(temporary,R/'video'/name)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(R/'video'/name)]))
stream=probe['streams'][0];assert stream['width']==1920 and stream['height']==1080 and stream['r_frame_rate']=='24/1'
(R/'validation'/('video_'+pov+'.json')).write_text(json.dumps(dict(file=name,native_frames=n,native_render_fps=6,output_fps=24,temporal_blend_interpolation=True,width=1920,height=1080,duration_s=float(probe['format']['duration']),bytes=int(probe['format']['size']),source='Native CAD rendering, same kinematic scenario as Gazebo replay; NOT Gazebo capture'),indent=2))
print('Finished',name,flush=True)
