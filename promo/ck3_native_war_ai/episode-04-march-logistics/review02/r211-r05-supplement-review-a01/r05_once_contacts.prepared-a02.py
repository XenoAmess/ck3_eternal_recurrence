"""Prepared R211 controlled-zero720-frame contact scope only. New R05 source-bound cap and Root one-Popen grant required."""
import argparse,csv,datetime,gzip,hashlib,io,json,os,re,subprocess,threading,time
from pathlib import Path
from PIL import Image
import psutil
from fractions import Fraction

def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def filepin(p):
 b=Path(p).read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def need(ok,message):
 if not ok:raise ValueError(message)
def usage(root):
 out=dict(contacts=0,fullres=0,metadata=0)
 for p in root.rglob('*'):
  if p.is_file():out['contacts' if p.name.startswith('contact-') else 'fullres' if p.name.startswith('full-') else 'metadata']+=p.stat().st_size
 out['aggregate']=sum(out.values());return out
def jpeg_read(stream):
 def readn(n):
  data=stream.read(n)
  if len(data)!=n:raise EOFError('Incomplete JPEG or pipe EOF')
  return data
 data=bytearray(readn(2));need(data==b'\xff\xd8','JPEG SOI differs');marker=None
 while True:
  need(len(data)<=2*1024*1024,'Single JPEG memory limit exceeded')
  if marker is None:
   need(readn(1)==b'\xff','JPEG marker prefix differs');c=readn(1)
   while c==b'\xff':c=readn(1)
   marker=c[0];data.extend((255,marker))
  if marker==217:return bytes(data)
  need(marker not in (0,216),'Invalid JPEG marker')
  if marker==1 or 208<=marker<=215:marker=None;continue
  length=readn(2);data.extend(length);n=int.from_bytes(length,'big');need(n>=2,'JPEG segment length differs');data.extend(readn(n-2))
  if marker!=218:marker=None;continue
  while True:
   c=readn(1);data.extend(c)
   if c!=b'\xff':continue
   c=readn(1);data.extend(c)
   while c==b'\xff':c=readn(1);data.extend(c)
   if c==b'\x00' or 208<=c[0]<=215:continue
   marker=c[0];break

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--recipe',required=True);ap.add_argument('--recipe-sha',required=True)
 ap.add_argument('--capacity',required=True);ap.add_argument('--capacity-sha',required=True);a=ap.parse_args()
 need(filepin(a.recipe)['sha256']==a.recipe_sha,'Recipe differs')
 need(filepin(a.capacity)['sha256']==a.capacity_sha,'Actual new capacity differs')
 recipe=json.loads(Path(a.recipe).read_text(encoding='utf8'));cap=json.loads(Path(a.capacity).read_text(encoding='utf8'))
 need(cap.get('machine_id')==recipe['machine_id'],'Actual capacity machine differs')
 need(cap.get('source_bound_single_extraction_execution_admitted') is True and cap.get('FFmpeg_execution_admitted') is True,'Financial/planning-only is not source execution admission')
 O=Path(recipe['output_root']);need(not (O/'ONCE-CLAIM.actual.json').exists() and not (O/'EXTRACTION.actual.json').exists() and not any(O.glob('contact-*.jpg')),'R05 execution outputs already exist; no retry')
 O.mkdir(parents=True,exist_ok=True)
 deadline=datetime.datetime.fromisoformat(recipe['hard_deadline_utc'].replace('Z','+00:00')).timestamp()
 need(time.time()<deadline-60,'Too little original time for bounded extraction and closure')
 def save(name,x):
  p=O/name;need(not p.exists(),'Create-only actual exists: '+name)
  p.write_text(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8');return filepin(p)
 save('ONCE-CLAIM.actual.json',dict(machine_id=recipe['machine_id'],observed_at_utc=stamp(),recipe=filepin(a.recipe),capacity=filepin(a.capacity),runner=filepin(__file__),Root_authorization='Actual new R05 source-bound cap and subsequent Root single-source R211 execution grant; no R07 budget reused',conditional_fullres=False))
 # Meaningful parser sanity on in-memory synthetic JPEG only, no extra FFmpeg/image file.
 test=io.BytesIO();Image.new('RGB',(2,2)).save(test,format='JPEG');raw=test.getvalue()
 need(jpeg_read(io.BytesIO(raw))==raw,'JPEG boundary parser failed small deterministic sanity')
 save('PARSER-SANITY.actual.json',dict(kind='In-memory2x2 synthetic JPEG boundary parser equality only',file_or_FFmpeg_or_source_calls=0,passed=True))
 latest=subprocess.run(['gh','release','view','--repo','XenoAmess/xar_promo_toolchain','--json','tagName,isDraft,isPrerelease,publishedAt,url'],capture_output=True,timeout=20)
 save('LATEST-RELEASE.actual.json',dict(observed_at_utc=stamp(),returncode=latest.returncode,stdout=latest.stdout.decode('utf8','replace'),stderr=latest.stderr.decode('utf8','replace'),no_download=True))
 need(latest.returncode==0,'Latest formal Release readonly query failed')
 release=json.loads(latest.stdout);need(not release['isDraft'] and not release['isPrerelease'],'Latest release is not formal')
 source=Path(recipe['retained_source']['path']);st=source.stat();expected=recipe['retained_source_stat']
 actual=dict(bytes=st.st_size,mtime_ns=st.st_mtime_ns,st_dev=st.st_dev,st_ino=st.st_ino)
 need(actual=={k:expected[k] for k in actual},'Retained raw stat identity differs')
 live=[p.info for p in psutil.process_iter(['pid','name']) if (p.info['name'] or '').lower()=='ffmpeg.exe']
 need(not live,'Another FFmpeg is active')
 save('SOURCE-STAT-BEFORE.actual.json',dict(machine_id=recipe['machine_id'],observed_at_utc=stamp(),actual=actual,body_rehashed=False))
 save('COMMAND.actual.json',dict(argv=recipe['argv'],cwd=recipe['cwd'],expected_dimensions=recipe['expected_sheet_dimensions'],new_raw_probe=False))
 stderr_path=O/'ffmpeg-stderr.actual.log.gz';trace=[];timebases=[];sheets=[];reason=None;thread_error=[];raw_log_hash=hashlib.sha256();raw_log_bytes=[0]
 diagnostics=(O/'image-dimensions.actual.jsonl').open('x',encoding='utf8')
 usages=(O/'usage-by-sheet.actual.csv').open('x',encoding='utf8',newline='');usage_writer=csv.writer(usages);usage_writer.writerow(['sheet','JPEG_bytes','contacts_bytes','metadata_bytes','aggregate_bytes'])
 started=stamp();clock=time.monotonic()
 proc=subprocess.Popen(recipe['argv'],cwd=recipe['cwd'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 save('OWNED-PROCESS.actual.json',dict(pid=proc.pid,started_at_utc=started,actual_priority=psutil.Process(proc.pid).nice()))
 def stderr_reader():
  try:
   with gzip.open(stderr_path,'xb',compresslevel=6) as log:
    for rawline in iter(proc.stderr.readline,b''):
     log.write(rawline);raw_log_hash.update(rawline);raw_log_bytes[0]+=len(rawline)
     tb=re.search(rb'config in time_base:\s*(\d+)/(\d+)',rawline)
     if tb:timebases.append((int(tb[1]),int(tb[2])))
     m=re.search(rb'n:\s*(\d+)\s+pts:\s*(-?\d+)\s+pts_time:([^ ]+)',rawline)
     if m:trace.append((int(m[1]),int(m[2]),m[3].decode()))
     if usage(O)['metadata']>196608:
      thread_error.append('Metadata approaching256KiB cap, preserving full compressed stderr');proc.terminate();break
  except BaseException as e:thread_error.append(type(e).__name__+': '+str(e))
 def watchdog():
  nonlocal reason
  while proc.poll() is None:
   if time.time()>=deadline-20:reason='Original1830deadline closure reserve';proc.terminate();break
   time.sleep(.05)
 thread=threading.Thread(target=stderr_reader,daemon=True);thread.start();threading.Thread(target=watchdog,daemon=True).start()
 try:
  for i in range(45):
   data=jpeg_read(proc.stdout);digest=hashlib.sha256(data).hexdigest()
   with Image.open(io.BytesIO(data)) as image:
    dimensions=list(image.size)
    diagnostics.write(json.dumps(dict(sheet=i,actual_dimensions=dimensions,expected_dimensions=recipe['expected_sheet_dimensions'],JPEG_bytes=len(data),sha256=digest))+'\n');diagnostics.flush()
    image.load()
   need(dimensions==recipe['expected_sheet_dimensions'],'Actual JPEG geometry '+str(dimensions)+' differs from '+str(recipe['expected_sheet_dimensions']))
   u=usage(O)
   if u['contacts']+len(data)>4194304 or u['aggregate']+len(data)+131072>5242880:
    reason='Next exact JPEG exceeds4MiB contacts or5MiB total with metadata reserve';proc.terminate();break
   path=O/('contact-%03d.jpg'%i)
   with path.open('xb') as stream:stream.write(data)
   lo=i*16;hi=min(lo+16,720)
   sheets.append(dict(sheet_id=i,image=dict(path=str(path),bytes=len(data),sha256=digest),PTS_grid_indices_half_open=[26640+lo,26640+hi],physical_original_ordinal_range=None,local_frames_half_open=[lo,hi],valid_cells=hi-lo,actual_dimensions=dimensions))
   u=usage(O);usage_writer.writerow([i,len(data),u['contacts'],u['metadata'],u['aggregate']]);usages.flush()
   if i%8==7:print(json.dumps(dict(sheets=i+1,usage=u)),flush=True)
 except BaseException as e:
  reason=reason or type(e).__name__+': '+str(e)
  if proc.poll() is None:proc.terminate()
 code=proc.wait(timeout=10);thread.join(timeout=5);diagnostics.close();usages.close()
 with (O/'source-frame-PTS.actual.csv').open('x',encoding='utf8',newline='') as f:
  writer=csv.writer(f);writer.writerow(['frame','PTS_ticks','PTS_seconds']);writer.writerows(trace)
 for s in sheets:
  lo,hi=s['local_frames_half_open'];s['actual_PTS_ticks_first_last']=[trace[lo][1],trace[hi-1][1]] if len(trace)>=hi else None
 complete=code==0 and reason is None and not thread_error and len(sheets)==45 and len(trace)==720 and [t[0] for t in trace]==list(range(720)) and bool(timebases) and timebases[0][1]>0 and abs(Fraction(trace[0][1])*Fraction(*timebases[0])-888)<=Fraction(1,1000) and abs(Fraction(trace[-1][1])*Fraction(*timebases[0])-(Fraction(888)+Fraction(719,30)))<=Fraction(1,1000) and all(abs(Fraction(b[1]-a[1])*Fraction(*timebases[0])-Fraction(1,30))<=Fraction(1,1000) for a,b in zip(trace,trace[1:]))
 after=source.stat();after_stat=dict(bytes=after.st_size,mtime_ns=after.st_mtime_ns,st_dev=after.st_dev,st_ino=after.st_ino)
 need(after_stat==actual,'Source raw stat changed during read')
 result=dict(schema='xar.R211.controlledzero.720-window-contact-extraction.v1',machine_id=recipe['machine_id'],observed_at_utc=stamp(),status='EXTRACTION_COMPLETE_AI_REVIEW_PENDING' if complete else 'PARTIAL_FAILED_PRESERVED_NO_RETRY',
  original_Popen_pid=proc.pid,original_Popen_wait_returned=True,exit_code=code,elapsed_seconds=time.monotonic()-clock,reason=reason,reader_error=thread_error,
  source_filter_timebases=timebases,trace_frame_is_window_local=True,PTS_grid_index_not_physical_original_ordinal=True,physical_original_ordinal=None,whole_raw_PTS_QA_known=False,source_trace_count=len(trace),source_trace=filepin(O/'source-frame-PTS.actual.csv'),complete_sheets=len(sheets),materialized_valid_cells=sum(s['valid_cells'] for s in sheets),sheets=sheets,
  dimensions_diagnostics=filepin(O/'image-dimensions.actual.jsonl'),usage_by_sheet=filepin(O/'usage-by-sheet.actual.csv'),
  full_stderr_lossless_gzip=filepin(stderr_path),uncompressed_stderr_bytes=raw_log_bytes[0],uncompressed_stderr_SHA256=raw_log_hash.hexdigest(),stderr_truncated=False,
  actual_source_stat_after=after_stat,raw_hash_or_probe_or_copy=False,old_fullraw_QA_repeated=False,fullraw_EOF_claim=False,
  clean=False,human1x=False,human_signoff=False,formal_credit=0,remaining_heavy=0,usage_before_result=usage(O))
 resultpin=save('EXTRACTION.actual.json',result);u=usage(O)
 need(u['contacts']<=4194304 and u['metadata']<=262144 and u['aggregate']<=5242880,'Final cap differs')
 print(json.dumps(dict(result=resultpin,status=result['status'],usage=u,remaining_heavy=0)),flush=True)

if __name__=='__main__':main()
