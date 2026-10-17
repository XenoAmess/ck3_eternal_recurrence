"""One bounded R204 literal replay. Standard library only; no producer imports/SDK."""
from pathlib import Path
import hashlib, json, re, struct, zipfile
H=Path(__file__).resolve().parent
def need(ok,why):
    if not ok: raise ValueError(why)
def main():
    ix=json.loads((H/'source-index.json').read_bytes());a=(H/ix['archive']['path']).read_bytes()
    need(hashlib.sha256(a).hexdigest()==ix['archive']['sha256'],'archive SHA')
    with zipfile.ZipFile(H/ix['archive']['path']) as z:
        need(z.testzip() is None,'archive CRC');obj={}
        for key,item in ix['sources'].items():
            raw=z.read(item['archive_member'])
            need(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'original '+key)
            obj[key]=raw if key.startswith('historical_') else json.loads(raw)
    summary=obj['window_summary'];need(summary['machine_id']==ix['machine_id'],'machine')
    date=53148888
    for key in ix['day_chain_keys']:
        d=obj[key];p=d.get('postcondition',d.get('composite_plus_independent_postcondition',{}))
        need(p.get('exact_day') is True and p['starting_date_raw']==date and p['ending_date_raw']==date+24,'day chain '+key)
        need(p['first_take_historical_RED_relabelled'] is False,'historical RED')
        date=p['ending_date_raw']
    need(len(ix['day_chain_keys'])==32 and date==53149656,'32 contiguous actual days')
    need(obj['advance_a01_RED']['primary_error']=='RuntimeError: bounded existing request ID required','original request RED')
    need(obj['advance_a01_RED']['actual_qualified_new_days']==1 and obj['advance_a02']['actual_qualified_new_days']==26,'attempt split')
    seam=ix['request_suffix_correction'];base=obj['historical_actor_a01'].decode();overlay=obj['historical_overlay_a02'].decode()
    need(base.count(seam['original_seam'])==1 and ".lower()" in overlay,'exact suffix correction seam')
    name='r204-check'+'-'+'D01-natural'
    need(re.fullmatch(r'r204-[a-z0-9-]{1,75}',name) is None,'reproduce rejected uppercase suffix')
    name='r204-check'+'-'+'D01-natural'.lower()
    need(re.fullmatch(r'r204-[a-z0-9-]{1,75}',name) is not None,'new lowercase suffix accepted')
    rows=summary['records'];need(len(rows)==7,'seven retained rows')
    need(sum(r['kind']==0 for r in rows)==6 and sum(r['kind']==2 for r in rows)==1,'record kinds')
    cash=next(r for r in rows if r['kind']==2)
    need(cash['characterFullID']==[31254,31254] and cash['amount_raw']==206846 and cash['returnRVA']=='0x28a6d7c','personal cash literal')
    need(cash['personal_balance_bits'][1]-cash['personal_balance_bits'][0]==206846,'personal balance delta')
    n=summary['natural'];need(n['count']==64 and n['phase_counts']=={'1':32,'2':32},'natural phases')
    need(n['status']['overwritten_records']==0 and n['status']['failed_appends']==0,'natural read scope')
    c=obj['collect_consumer'];need(c['zero_rows_not_zero_payment'] is True and c['military_paid_raw'] is None and c['resource4_records_literal']==[],'zero rows boundary')
    clean=obj['manual_cleanup'];need(clean['actual_cleanup_complete'] is True,'manual cleanup')
    need(all(clean['explicit_Root_inline_actor_cleanup'][k] is True for k in ['payment_disabled','payment_independent_clear','natural_disabled','natural_independent_off']),'independent OFF/clear')
    need(obj['normal_save']['date_raw']==date and obj['screen_release']['normal_exit_zero'] is True and obj['screen_release']['task_done_resources_empty'] is True,'normal close')
    qa=obj['media_QA'];need(qa['video_frame_count']==698 and qa['container_duration_seconds']=='23.266000','media literal')
    png=(H/ix['frame']['path']).read_bytes();need(hashlib.sha256(png).hexdigest()==ix['frame']['sha256'] and struct.unpack('>II',png[16:24])==(1280,720),'one client PNG')
    print(json.dumps({'machine_id':ix['machine_id'],'exact_originals':len(ix['sources']),'contiguous_days':32,'ending_date_raw':date,'records':7,'personal_cash_add_raw':206846,'historical_RED_preserved':True,'zero_rows_not_zero_payment':True,'SDK_calls':0,'producer_imports':0,'media_decode_calls':0}))
if __name__=='__main__':main()
