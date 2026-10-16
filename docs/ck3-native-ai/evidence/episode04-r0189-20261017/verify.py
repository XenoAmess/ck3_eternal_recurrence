from pathlib import Path
import hashlib,json,struct
ROOT=Path(__file__).resolve().parent
def need(ok,why):
    if not ok:raise ValueError(why)
def read(name):return json.loads((ROOT/name).read_bytes())
idx=read('source-index.json')
for row in idx['originals']:
    b=(ROOT/row['local']).read_bytes();p=row['source']
    need(len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'],row['local'])
for row in idx['exact_slices']:
    b=(ROOT/row['local']).read_bytes();need(len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],'slice')
for row in idx['generated']:
    b=(ROOT/row['local']).read_bytes();need(hashlib.sha256(b).hexdigest()==row['sha256'],'generated')
f=read('facts.derived-a01.json')
for i in range(1,9):
    d=read('days/r189-film-a01-d%02d-complete.actual.json'%i)
    need(d['date_raw']==53149080+24*i,'day date')
    need(d['sentinel']['state']=='triggered' and d['sentinel']['overshoot_days']==0,'sentinel')
need(read('receipts/r189-film-a01-film-result.actual.json')['completed_days']==8,'completed days')
army=read('selected/d09-player-armies.exact-fragment.json')[0]
need(army['army_id']==18 and army['in_combat'] is True and army['army_state']=='combat','day9 combat')
header=(ROOT/'receipts/r189-film-a01-identity-ready-r189-a01-header-first2048.actual.bin').read_bytes()
need(header[48:56]==b'1.20.0.4' and header[754:756].hex()=='1400' and struct.unpack_from('<I',header,756)[0]==31254,'typed header tag and payload offsets')
for n in [2610,2644]:
    d=read('responses/r189-preview-%d-once-a01.json'%n)
    need(d['is_error'] is True and d['body'] is None,'unavailable SDK')
r=read('raw-result.json');need(r['state']=='NORMAL_TREE_EMPTY' and r['job']['returncode']==0 and r['job']['job_active_processes']==0,'recorder close')
need(r['capture_source']['client_screen_rect']==[640,360,1920,1080] and r['capture_source']['direct_hwnd_capture'] is False,'client capture')
m=read('media/portable-media-facts.actual-a01.json')
need(m['video']['timeline']['frames']==744 and m['encoded_frame_end_seconds']==24.8 and m['full_AV_decode_exit']==0,'decoded facts')
need(m['min100_wall_met'] is False and m['configured_min_wall_met'] is False,'duration')
b=read('close/BOOTSTRAP-OBSERVED.actual.json');need(b['normal_exit_zero'] is True,'normal game exit')
s=read('close/SCREEN-RELEASE.actual.json');t=json.loads(s['stdout'])['task']
need(s['exit_code']==0 and t['state']=='done' and t['resources']==[] and t['last_sequence']==5870,'release')
need(f['close']['date_raw']==53149296 and f['film']['day9_counted_complete'] is False,'save date is not completed day')
need(all(x['military_t0_frame_ready'] and not x['normal_t0_saved'] and not x['r01_research_core_closed'] for x in f['R01']['conditional_goals']),'R01 boundary')
need(f['R06']['eligible_provider_RVAs']==[] and not f['R06']['frontier8_definition_known'],'R06 boundary')
need(f['qualification']['dynamic_video']=='0/11' and f['qualification']['human_signoff'] is False,'credit boundary')
print(json.dumps({'status':'PASS','machine_id':idx['machine_id'],'exact_originals':len(idx['originals']),'exact_slices':len(idx['exact_slices']),'portable_only':True,'external_large_bodies_opened':False}))
