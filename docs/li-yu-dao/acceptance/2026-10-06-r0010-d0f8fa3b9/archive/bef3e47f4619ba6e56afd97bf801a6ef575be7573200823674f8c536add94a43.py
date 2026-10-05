import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;records=[]
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def copy(name,source,mapping):
    p=BASE/source/name;text=p.read_text(encoding='utf-8')
    if mapping:
        matcher=re.compile('|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True)));text=matcher.sub(lambda m:mapping[m.group()],text)
    dest=HERE/name
    with dest.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    records.append({'source':pin(p),'new':pin(dest),'parameter_changes':mapping})
copy('prepare_request.py','r10-actual-fifth-post-cancel-readback-20261005-001',{'r10-actual-fifth-open-join-readback-20261005-001':'r10-actual-seventh-open-join-readback-20261006-001','r10-actual-fourth-post-cancel-readback-20261005-001':'r10-actual-sixth-post-cancel-readback-20261006-001','0125-fifth-post-cancel-save':'0167-seventh-post-cancel-save','91535983':'91538159','55b352c47d89ee41ef86479026627f84ebcb35736848daa4e70178bb06a74db2':'4aa783a16d446f8d9a7e1e1e622eaf77e39400ebe814ae40f4841fa5e2a7b3e9','0125-':'0167-','5206437':'6925653','7a9768a2e921c36e6625e04d807cb9b7a417a45f9cff9f1771b76e73a67b1b09':'c950b7fd3d4905df2d8290ac9a5ae828d181ebf2a99da65783d2d76ac3b9cd64','fifth post-cancel':'seventh post-cancel','SDK125':'SDK167','fifth-post-explicit':'seventh-post-explicit','fifth_open_before111':'seventh_open_before153','fourth_cancel_baseline107':'sixth_cancel_baseline149'})
copy('collect_controls.py','r10-actual-sixth-post-cancel-readback-20261006-001',{'0145-':'0163-','0146-':'0164-','0147-':'0165-','0148-':'0166-','0150-':'0168-','5d8ba33c2db114aa6dd786f8fd8179c5cc0a56804252254d577a0fb2d8f30bbe':'b49d1a7cadd9f3c887d635e34f878cc01171ed21b7d25fa9e4783b04e2d56fa0','f6329772afbe437c17b222b392ebc39a73455f3528d0f18a6172f2526c038189':'a5a0f132d7ad48ef2aa89d8c53c19314eac6dc777406c5960cbc44d9f4463e0d','750c399c25872ac0b724aedd7c7b5bdca21baa41be3d6d8ffc232b89ee928c26':'f201af078bd94aebb5da780ac44551f09acf6fb955118786e85b90f7da137723','c8ff563db0ec21d6f5ac0f8c8b3534d76ade85969f40e354b8401dafab975694':'f493f12b8e4c6e24bda55b1c5e5f1a6438824e952f75d0c8f7b57cb36977d369','27fff1d1a7533e83d39b72684a33f43a637c1dbb56110f0d9fe1c8cbfb8534ee':'39991b82931f66aa1a421d5e95ccd4b54a3508fb5e2bc294344cb2fe5183b3f8','sixth-explicit':'seventh-explicit','fresh150':'fresh168'})
copy('inspect_new.py','r10-actual-sixth-post-cancel-readback-20261006-001',{})
with (HERE/'TOOL-REUSE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'records':records,'old_save_reparsed':False,'old_package_writes':False},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'new_external_scripts':len(records),'HERE':str(HERE)},ensure_ascii=False))
