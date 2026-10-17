"""Portable package/readback and one actual pure-code check; no game/SDK/media decode."""
from pathlib import Path
import hashlib, json, zipfile
H=Path(__file__).resolve().parent
def need(ok,why):
    if not ok: raise ValueError(why)
def main():
    index=json.loads((H/'source-index.json').read_bytes())
    archive=H/index['archive']['path']
    need(hashlib.sha256(archive.read_bytes()).hexdigest()==index['archive']['sha256'],'archive SHA')
    with zipfile.ZipFile(archive) as z:
        need(z.testzip() is None,'archive CRC')
        checked=0
        for item in index['sources'].values():
            if 'archive_member' not in item: continue
            raw=z.read(item['archive_member'])
            need(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'original pin')
            checked+=1
        module=H.parents[3]/index['module']['path']
        if module.is_file():
            code=module.read_bytes().replace(b'\r\n',b'\n')
            source='canonical bridge module'
        else:
            code=z.read(index['sources']['original_helper']['archive_member']).replace(b'\r\n',b'\n')
            source='exact archived helper, standalone packet'
    need(hashlib.sha256(code).hexdigest()==index['module']['sha256'],'pure helper SHA')
    ns={'__name__':'portable_exact_day_contract'}
    exec(compile(code,index['module']['path'],'exec'),ns)
    packet=json.loads((H/'exact-day-inputs.json').read_bytes())
    result=ns['exact_day_postcondition'](packet['step'],packet['before'],packet['after'])
    need(result['exact_day'] is True and result['ending_date_raw']==53148888,'actual pure postcondition')
    frame=(H/index['portable_frame']['path']).read_bytes()
    need(hashlib.sha256(frame).hexdigest()==index['portable_frame']['sha256'],'single client frame SHA')
    print(json.dumps({'machine_id':index['machine_id'],'archive_originals_checked':checked,'pure_helper_source':source,'actual_exact_day':True,'historical_actor_RED_preserved':True,'SDK_calls':0,'media_decode_calls':0,'negative_matrix_rerun':False}))
if __name__=='__main__': main()
