"""Small, source-bound mechanism animation producer. No game, desktop or TTS.

Each step adds a new semantic panel; the permanent source-only disclosure is
drawn into every frame. JSON specifications and source excerpts are immutable.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

FPS=30
GEOMETRY=(2560,1440)
MAX_SECONDS=20
LABEL='源码图解 · 非实机画面 · 不代表已发生的业务结果'

def now():return datetime.now(timezone.utc).isoformat()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def pin(path):
    path=Path(path).resolve();b=path.read_bytes()
    return {'path':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def bound(binding):
    if set(binding)!={'path','bytes','sha256'} or pin(binding['path'])!=binding:
        raise ValueError('Exact immutable path/bytes/SHA input required')
    return Path(binding['path'])
def write(path,obj):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(obj,stream,ensure_ascii=False,indent=2);stream.write('\n')

def verify_sources(catalog):
    if catalog.get('schema')!='ck3-faith-power-local-motion-source-catalog-v1':
        raise ValueError('Current-machine source catalog required')
    refs={}
    for source in catalog['sources']:
        path=bound(source['file'])
        lines=path.read_text(encoding='utf-8-sig').splitlines()
        first,last=source['first_line'],source['last_line']
        text='\n'.join(lines[first-1:last])+'\n'
        if (not 1<=first<=last<=len(lines) or text!=source['excerpt'] or
            hashlib.sha256(text.encode()).hexdigest()!=source['excerpt_sha256']):
            raise ValueError('Actual local source excerpt changed')
        if source['id'] in refs:raise ValueError('Duplicate source reference')
        refs[source['id']]=source
    return refs

def inspect_spec(spec):
    if spec.get('schema')!='ck3-faith-power-mechanism-motion-spec-v1':
        raise ValueError('Unknown source-motion spec')
    if spec.get('live_result_depicted') is not False or spec.get('permanent_disclosure')!=LABEL:
        raise ValueError('Permanent source-only disclosure required')
    duration=spec['duration_seconds']
    if not 0<duration<=MAX_SECONDS or abs(duration*FPS-round(duration*FPS))>1e-5:
        raise ValueError('Source motion must be frame aligned and at most 20 seconds')
    refs=verify_sources(read(bound(spec['source_catalog'])))
    steps=spec['steps']
    if not 2<=len(steps)<=3:raise ValueError('Two or three semantic additions required')
    cursor=0;semantic=set()
    for step in steps:
        if step['start_seconds']!=cursor or step['end_seconds']<=cursor:
            raise ValueError('Contiguous positive semantic step intervals required')
        cursor=step['end_seconds']
        if abs(cursor*FPS-round(cursor*FPS))>1e-5:raise ValueError('Step timing not frame aligned')
        if not step['semantic_change'] or step['semantic_change'] in semantic:
            raise ValueError('Each step must add a distinct semantic fact')
        semantic.add(step['semantic_change'])
        if not step['claim_ids'] or not step['source_ref_ids'] or any(r not in refs for r in step['source_ref_ids']):
            raise ValueError('Every semantic step needs bound claims and source references')
        if not 1<=len(step['panel']['rows'])<=3:raise ValueError('One to three panel rows required')
        if any(len(row['label'])>40 or len(row['value'])>40 for row in step['panel']['rows']):
            raise ValueError('Panel labels must stay concise')
    if cursor!=duration:raise ValueError('Steps must cover exactly the output duration')
    return duration,steps

def smooth(v):
    v=max(0.,min(1.,v));return v*v*(3.-2.*v)

class Painter:
    def __init__(self,spec,font):
        self.spec=spec;self.fontpath=str(font)
        self.fonts={size:ImageFont.truetype(str(font),size) for size in [28,30,32,36,40,44,48,56,68,76]}
        self._stable_cache={}
        self.bg=(26,23,23);self.ink=(239,226,203);self.muted=(185,177,165)
        self.gold=(214,169,96);self.green=(135,192,153);self.red=(216,148,134)
    def text(self,draw,xy,text,size=36,fill=None):
        draw.text(xy,text,font=self.fonts[size],fill=fill or self.ink)
    def wrapped(self,draw,xy,text,width,size=36,fill=None,max_lines=3):
        lines=[];current='';font=self.fonts[size]
        for char in text:
            if char=='\n' or draw.textlength(current+char,font=font)>width:
                lines.append(current);current='' if char=='\n' else char
            else:current+=char
        if current:lines.append(current)
        if len(lines)>max_lines:raise ValueError('Authored text exceeds visual safety area')
        for i,line in enumerate(lines):self.text(draw,(xy[0],xy[1]+i*(size+15)),line,size,fill)
    def frame(self,t):
        active=max(i for i,s in enumerate(self.spec['steps']) if s['start_seconds']<=t)
        stable=t-self.spec['steps'][active]['start_seconds']>=1.6
        if stable and active in self._stable_cache:
            image=self._stable_cache[active].copy();d=ImageDraw.Draw(image)
            d.rectangle((100,1108,2460,1114),fill=(69,58,47))
            d.rectangle((100,1108,100+round(2360*t/self.spec['duration_seconds']),1114),fill=self.gold)
            return image
        image=Image.new('RGB',GEOMETRY,self.bg);d=ImageDraw.Draw(image)
        d.rectangle((0,0,2560,102),fill=(45,33,29));self.text(d,(100,29),LABEL,36,self.gold)
        self.text(d,(100,145),self.spec['title'],68)
        self.text(d,(104,250),self.spec['subtitle'],36,self.muted)
        self.text(d,(104,310),self.spec['scope_note'],28,self.muted)
        d.line((100,370,2460,370),fill=(106,79,54),width=3)
        active=0
        for i,step in enumerate(self.spec['steps']):
            local=t-step['start_seconds']
            if local<0:continue
            active=i;reveal=smooth(local/.55)
            x=100+i*825;y=405+round((1-reveal)*68);w=710
            panel=step['panel'];accent=self.gold if i==0 else self.green if i==1 else self.red
            layer=Image.new('RGBA',GEOMETRY,(0,0,0,0));p=ImageDraw.Draw(layer)
            p.rounded_rectangle((x,y,x+w,y+560),radius=24,fill=(44,40,37,255),outline=accent+(255,),width=4)
            self.text(p,(x+34,y+28),f'{i+1:02d}',40,accent)
            self.wrapped(p,(x+34,y+100),panel['title'],w-68,44,max_lines=2)
            for j,row in enumerate(panel['rows']):
                progress=smooth((local-.32-j*.22)/.5)
                if progress<=0:continue
                yy=y+225+j*103
                self.text(p,(x+34,yy),row['label'],30,self.muted)
                self.wrapped(p,(x+34,yy+42),row['value'],w-68,40,accent,max_lines=1)
            self.text(p,(x+34,y+505),self.spec.get('proof_label','固定来源 · 条件结构'),28,self.muted)
            if reveal<1:layer.putalpha(layer.getchannel('A').point(lambda a:round(a*reveal)))
            image=Image.alpha_composite(image.convert('RGBA'),layer).convert('RGB');d=ImageDraw.Draw(image)
            if i and self.spec.get('connectors')=='sequence':
                end_x=x-25;start_x=x-90;yy=650
                length=round((end_x-start_x)*reveal)
                d.line((start_x,yy,start_x+length,yy),fill=self.gold,width=6)
                if reveal>.98:d.polygon([(end_x,yy),(end_x-18,yy-13),(end_x-18,yy+13)],fill=self.gold)
        step=self.spec['steps'][active]
        self.wrapped(d,(105,990),step['caption'],2340,40,max_lines=2)
        if stable:self._stable_cache[active]=image.copy()
        d.rectangle((100,1108,2460,1114),fill=(69,58,47))
        d.rectangle((100,1108,100+round(2360*t/self.spec['duration_seconds']),1114),fill=self.gold)
        return image

def command_log(output,label,argv):
    started=now();result=subprocess.run(argv,capture_output=True,check=False)
    (output/(label+'.stdout')).write_bytes(result.stdout);(output/(label+'.stderr')).write_bytes(result.stderr)
    record={'argv':list(map(str,argv)),'started_at_utc':started,'finished_at_utc':now(),'exit_code':result.returncode,
            'stdout':pin(output/(label+'.stdout')),'stderr':pin(output/(label+'.stderr'))}
    write(output/(label+'.command.json'),record)
    if result.returncode:raise RuntimeError(label+' failed; no retry performed')
    return result,record

def build(spec_path,output,*,repo,package_root,ledger,allocation_reader,qualification,qualification_sha256,machine,ffmpeg,ffprobe,font,peak_bytes=16*1024**2):
    spec_path=Path(spec_path).resolve();output=Path(output).resolve();repo=Path(repo).resolve()
    if output.exists():raise ValueError('Write-once output directory already exists')
    spec=read(spec_path);duration,steps=inspect_spec(spec)
    catalog=read(bound(spec['source_catalog']))
    if spec['machine_id']!=machine or catalog['machine_id']!=machine:raise ValueError('Source catalog/spec machine mismatch')
    qual=read(qualification)
    if (not re.fullmatch(r'[0-9a-f]{64}',qualification_sha256) or pin(qualification)['sha256']!=qualification_sha256
        or qual['passed'] is not True or qual['machine_id']!=machine
        or not qual.get('checks') or any(value is not True for value in qual['checks'].values())
        or qual['checks'].get('latest_final') is not True):
        raise ValueError('Explicit exact same-machine successful latest-final qualification required')
    latest=qual['official_release']['tag'].removeprefix('v')
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',latest) or qual['installed']['version']!=latest:
        raise ValueError('Installed version must equal the actual official latest final release')
    official_digest=qual['official_release']['wheel']['digest'].removeprefix('sha256:')
    if qual['installed']['direct_url']['archive_info']['hashes']['sha256']!=official_digest:
        raise ValueError('Installed wheel must match actual official latest-final asset digest')
    if any(pin(p)!=qual['tools'][name] for name,p in [('ffmpeg',ffmpeg),('ffprobe',ffprobe)]):raise ValueError('Exact qualified binaries required')
    sys.path.insert(0,str(repo/'promo/ck3_faith_and_power/integration/src'))
    sys.path.insert(0,str(package_root))
    from faith_power_promo.storage_carry_v3 import admit_v3
    admission=admit_v3(repo,ledger,package_root,output,machine,peak_bytes,allocation_reader)
    output.mkdir(parents=True)
    write(output/'storage-admission-v3.json',admission)
    write(output/'frozen-spec.json',spec)
    write(output/'frozen-source-catalog.json',catalog)
    video=output/'mechanism-motion.mp4';frames=round(duration*FPS)
    max_media=math.ceil((3000000*duration+3000000)/8*1.05)
    if max_media+1024**2>peak_bytes:raise ValueError('Concrete clip peak must cover capped media plus metadata/QA')
    argv=[str(ffmpeg),'-nostdin','-n','-hide_banner','-loglevel','error','-threads','2','-filter_threads','2',
          '-f','rawvideo','-pixel_format','rgb24','-video_size','2560x1440','-framerate',str(FPS),'-i','pipe:0',
          '-an','-c:v','libx264','-preset','veryfast','-crf','21','-maxrate','3000000','-bufsize','3000000',
          '-threads','2','-pix_fmt','yuv420p','-frames:v',str(frames),'-fs',str(max_media),'-movflags','+faststart',str(video)]
    started=now();painter=Painter(spec,font)
    with (output/'encode.stderr').open('xb') as err:
        process=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=err)
        try:
            for frame_no in range(frames):process.stdin.write(painter.frame(frame_no/FPS).tobytes())
            process.stdin.close();code=process.wait(timeout=120)
        except BaseException:
            if process.stdin:process.stdin.close()
            if process.poll() is None:process.terminate();process.wait(timeout=10)
            raise
    write(output/'encode.command.json',{'argv':argv,'started_at_utc':started,'finished_at_utc':now(),'exit_code':code,'stderr':pin(output/'encode.stderr')})
    if code or video.stat().st_size>=max_media:raise RuntimeError('Encode failed or reached file cap; no retry performed')
    probe,probe_record=command_log(output,'probe',[str(ffprobe),'-v','error','-show_streams','-show_format','-of','json',str(video)])
    frames_result,pts_record=command_log(output,'frame-pts',[str(ffprobe),'-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(video)])
    decoded,decode_record=command_log(output,'full-decode',[str(ffmpeg),'-nostdin','-hide_banner','-v','error','-xerror','-err_detect','explode','-threads','2','-i',str(video),'-map','0:v:0','-f','null','-'])
    pts=[float(f['best_effort_timestamp_time']) for f in json.loads(frames_result.stdout)['frames']]
    media=json.loads(probe.stdout);streams=media['streams']
    if (len(streams)!=1 or streams[0]['codec_type']!='video' or streams[0]['width']!=2560 or streams[0]['height']!=1440
        or len(pts)!=frames or any(abs(t-i/FPS)>0.000001 for i,t in enumerate(pts))
        or abs(float(media['format']['duration'])-duration)>1/FPS or decoded.stderr):
        raise ValueError('Full decode / CFR PTS / geometry check failed')
    for name,t in [('step1',1.5),('step2',min(3.8,duration-1/FPS)),('step3',duration-1/FPS)]:
        painter.frame(t).save(output/(name+'.jpg'),quality=84)
    close=admit_v3(repo,ledger,package_root,output,machine,1,allocation_reader)
    write(output/'storage-close-v3.json',close)
    source_catalog=pin(output/'frozen-source-catalog.json')
    receipt={'schema':'ck3-faith-power-source-motion-v1','machine_id':machine,'observed_at_utc':now(),
      'evidence_source':'Exact current local script files and narrow excerpts; source-only Pillow frames piped once into qualified FFmpeg',
      'video':pin(video),'spec':pin(output/'frozen-spec.json'),'source_catalog':source_catalog,'producer':pin(__file__),
      'toolchain_qualification':pin(qualification),'font':pin(font),'permanent_disclosure':LABEL,
      'live_result_depicted':False,'game_or_screen_access':False,'TTS_requested':False,'human_1x_signoff':False,
      'full_decode_exit_code':decode_record['exit_code'],
      'frames':{'count':len(pts),'last_pts':pts[-1],'cfr_fps':FPS,'duration_seconds':duration,'width':2560,'height':1440,'first_pts':pts[0]},
      'steps':[{k:s[k] for k in ['id','start_seconds','end_seconds','semantic_change','claim_ids','source_ref_ids']} for s in steps],
      'claim_ids':sorted({x for s in steps for x in s['claim_ids']}),'source_ref_ids':sorted({x for s in steps for x in s['source_ref_ids']}),
      'encode':pin(output/'encode.command.json'),'probe':pin(output/'probe.command.json'),'PTS':pin(output/'frame-pts.stdout'),
      'full_decode':pin(output/'full-decode.command.json'),'storage_admission':pin(output/'storage-admission-v3.json'),'storage_close':pin(output/'storage-close-v3.json'),
      'review_stills_kind':'Direct Pillow source frames; actual encoded output separately full decoded/PTS checked',
      'review_stills':[pin(output/(x+'.jpg')) for x in ['step1','step2','step3']],
      'qualification_freshness_owner':'Calling round must acquire fresh official latest-final qualification before build; no cached-version inference',
      'visible_content_safety_rectangle':[0,0,2560,1114],
      'retention':{'category':'derived','review_at_utc':(datetime.now(timezone.utc)+timedelta(hours=48)).isoformat(),'reason':'Active formal-episode mechanism motion candidate; no automatic old input lifetime extension','old_asset_lifetimes_changed':False}}
    write(output/'source-motion-v1.json',receipt)
    return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['spec','output','repo','package-root','ledger','allocation-reader','qualification','qualification-sha256','machine','ffmpeg','ffprobe','font']:p.add_argument('--'+name,required=True)
    p.add_argument('--peak-bytes',type=int,default=16*1024**2)
    a=p.parse_args();args=vars(a);spec=args.pop('spec');output=args.pop('output')
    result=build(spec,output,**{k.replace('-','_'):v for k,v in args.items()})
    print(json.dumps({'receipt':str(Path(output)/'source-motion-v1.json'),'video':result['video'],'frames':result['frames']},ensure_ascii=False),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
