import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;SOURCE=BASE/'r10-actual-seventh-open-join-readback-20261006-001';records=[]
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def copy(name,mapping,extra=None):
    p=SOURCE/name;text=p.read_text(encoding='utf-8')
    if mapping:
        matcher=re.compile('|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True)));text=matcher.sub(lambda m:mapping[m.group()],text)
    if extra:text=extra(text)
    dest=HERE/name
    with dest.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    records.append({'source':pin(p),'new':pin(dest),'parameter_changes':mapping})
copy('prepare_request.py',{'r10-actual-sixth-post-cancel-readback-20261006-001':'r10-actual-seventh-post-cancel-readback-20261006-001','0153-seventh-open-save':'0171-eighth-open-save','91541371':'91542565','a984d4f1d5e4365c2d1812c21c7a3ef4adc5ec8f98afaee989b61e91ab96bb2a':'04b22b41900f89b73f75d1295b12d4acd8021dd7081eab0bfdae9f813062c487','0153-':'0171-','6235331':'6933331','1346a75473b2ee7a2b0e7b8a94d23e8286eaff41892bac5b35acadda562b8532':'54c200e59829320a26f01f69b9727bf2c3e6e370e13d589525e9a5c482cd969b','seventh-open':'eighth-open','SDK153':'SDK171','seventh-formal':'eighth-formal','after-sixth-cancellation':'after-seventh-cancellation','sixth_cancel_before149':'seventh_cancel_before167'})
def extra(text):
    comment='# This task did not supply a separate permit SHA; actual parent/permit bytes are still exactly verified against the current claim lineage above.'
    if text.count(comment)!=1:raise ValueError('Need exact prior permit parameter comment')
    text=text.replace(comment,"if permitref['sha256']!='abcaa729aca5bfcdee96ccc61c88d473bc4af5ef758394d11faa493f7fae0b06':raise ValueError('Root actual permit exact SHA mismatch')")
    return text.replace("'permit_root_supplied_sha':None","'permit_root_supplied_sha':'abcaa729aca5bfcdee96ccc61c88d473bc4af5ef758394d11faa493f7fae0b06'")
copy('collect_controls.py',{'seventh-player-options':'eighth-player-options','2f10fcafa46b99d6fab71adeb4a5ad8b1ae3571c50c89ff745465c75c5977604':'c3c294d740e1532649a3388d646bda1c5f658cbc1fb60aee5bf6934def177b6b','==154':'==172','typed154':'typed172','0151-':'0169-','0152-':'0170-','0154-':'0172-','21721efc900d1b41b2c01664daeb5b0c9d1e6771f581c01a159704193b1ea40c':'2af6ac611ba6f593cfefb69310b81c8f4660a78b2e5dc82f6e920d99b3980930','4d8956229d7f369a1884e0c6a9bdbe92c44522a80741d861f62418b67f630c71':'38252c3e782ed63afb33630a200c7565d7412652b3288199a4e0d0fe91ac4b96','Fresh151':'Fresh169','Initiate152':'Initiate170','Typed154':'Typed172',"claim['claim_ordinal']==6":"claim['claim_ordinal']==7", "parent['claim_ordinal']==5":"parent['claim_ordinal']==6",'ordinal6':'ordinal7','parent_ordinal5':'parent_ordinal6','ordinary-interaction-ce6f9c27e43f4d1c9057fb7746fcb815':'ordinary-interaction-cf364b502ddb47e58fb8ccbf5832a44f','before149_frame70_native69':'before167_frame79_native78',"claim['binding']['revision']==70":"claim['binding']['revision']==79", "claim['binding']['native_revision']==69":"claim['binding']['native_revision']==78",'seventh-lineage':'eighth-lineage','seventh-open':'eighth-open','save153':'save171'},extra)
copy('inspect_new.py',{})
with (HERE/'TOOL-REUSE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'records':records,'old_save_reparsed':False,'old_package_writes':False},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'new_external_scripts':len(records),'HERE':str(HERE)},ensure_ascii=False))
