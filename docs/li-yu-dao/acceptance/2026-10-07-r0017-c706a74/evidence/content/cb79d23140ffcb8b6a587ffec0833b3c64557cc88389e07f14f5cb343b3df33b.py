"""Explicit ROOT inputs; loading never starts a client, SDK, game or lease."""
from pathlib import Path
import hashlib,json

def ref(path):
    path=Path(path);raw=path.read_bytes()
    return {'path':path.as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')

def need(condition,message):
    if not condition:raise ValueError(message)

def load(path,formal=False):
    path=Path(path).resolve();b=json.loads(path.read_bytes())
    need(b.get('schema')=='lyd.root.formal-runtime-bindings.v1','explicit runtime bindings schema required')
    for key in ['source_head','run_id','run_root','repo_root','queue_helper','queue_helper_sha256','queue_dir','client_dir','dispatch_output']:
        need(isinstance(b.get(key),str) and bool(b[key]),'actual ROOT input required: '+key)
    need(len(b['source_head'])==40 and all(c in '0123456789abcdef' for c in b['source_head']),'full actual source HEAD required')
    need(ref(b['queue_helper'])['sha256']==b['queue_helper_sha256'],'queue helper actual hash differs')
    for key in ['run_root','repo_root','queue_dir','client_dir','dispatch_output']:
        need(Path(b[key]).is_absolute(),'absolute actual path required: '+key)
    if formal:
        for key in ['profile','profile_sha256','session_id','checkpoint_path']:
            need(isinstance(b.get(key),str) and bool(b[key]),'actual ROOT input required: '+key)
        need(ref(b['profile'])['sha256']==b['profile_sha256'],'actual profile bytes differ')
        for key in ['game_pid','connection_generation','actor_id']:
            need(type(b.get(key)) is int and b[key]>0,'new actual positive integer required: '+key)
        need(type(b.get('date_raw')) is int,'actual date_raw required')
        for key in ['gold','piety','prestige']:
            wallet=b.get('wallet',{}).get(key)
            need(isinstance(wallet,dict) and set(wallet)=={'raw','scale'} and type(wallet['raw']) is int and type(wallet['scale']) is int and wallet['scale']>0,'actual raw wallet required: '+key)
    b['_binding_path']=path.as_posix();b['_binding_ref']=ref(path)
    return b

def check_snapshot(s,revision,b,wallet=None):
    need(s['revision']==revision and s['native_revision']==revision-1,'public/native revision mismatch')
    need(s['snapshot_id']=='native:'+str(revision-1),'snapshot ID mismatch')
    need(s['paused'] is True and s['date_raw']==b['date_raw'],'paused/date guard failed')
    need(s['played_character']['character_id']==b['actor_id'],'actual actor mismatch')
    expected=b['wallet'] if wallet is None else wallet
    for currency in ['gold','piety','prestige']:
        need(s['played_character_'+currency]==expected[currency],'actual '+currency+' wallet guard failed')

def original_native_text(payload):
    """Extract existing JSON text bytes; never reconstruct a native receipt."""
    candidates=[]
    for block in payload.get('content',[]):
        if block.get('type')!='text' or not isinstance(block.get('text'),str):continue
        try:body=json.loads(block['text'])
        except ValueError:continue
        if isinstance(body,dict) and body.get('schema')=='ck3.native-profile-receipt.v1':
            candidates.append((block['text'].encode('utf-8'),body))
    need(len(candidates)==1,'exactly one original native-profile receipt text block required')
    raw,body=candidates[0]
    structured=payload.get('structuredContent')
    if structured is not None:need(structured==body,'SDK structuredContent differs from original native JSON block')
    return raw,body

def validate_author_template(template):
    keys={'schema','profile','source_export_report','compiled_result','metadata_result','original_baseline','reader_request_template','windows','sdk_metadata_variant','sdk_metadata_artifact','sdk_codec_artifact','business_migration_registry','checkpoint_receipt','preserved_checkpoint','G2_receipt','G3_receipt','window','output'}
    need(set(template)==keys,'frozen author v2 exact input keys required')
    need(template['schema']=='lyd.versioned-source.actual-checkpoint-author-request.v2','frozen author request v2 required')
    dynamic={'checkpoint_receipt','preserved_checkpoint','G2_receipt','G3_receipt','window','output'}
    for key in keys-dynamic:need(template[key] is not None,'fill actual author producer input before save: '+key)
    return template

def author_input(template,checkpoint,G2,G3,preserved,window,output):
    validate_author_template(template)
    value=dict(template);value.update(checkpoint_receipt=str(checkpoint),preserved_checkpoint=preserved,G2_receipt=str(G2),G3_receipt=str(G3),window=window,output=str(output))
    return value
