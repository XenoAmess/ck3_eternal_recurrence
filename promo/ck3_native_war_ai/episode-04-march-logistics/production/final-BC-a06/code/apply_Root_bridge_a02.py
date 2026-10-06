"""Exact single-paragraph Root-requested bridge; historical story a01 unchanged."""
from pathlib import Path
from datetime import datetime,timezone
import copy
import hashlib
import importlib.util
import json

ROOT=Path(__file__).resolve().parent
OLD=ROOT/'actual-story-a01'
OUT=ROOT/'actual-story-a02';OUT.mkdir(exist_ok=False)
def pin(path):
    path=Path(path);raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=value if isinstance(value,bytes) else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with path.open('xb') as stream:stream.write(raw)
TOOL=ROOT.parent/'e04-final-BC-oral-preparation-a01/main-scope-connection-a05/final_bc_increment.py'
spec=importlib.util.spec_from_file_location('pinned_single_bridge',TOOL)
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
old_raw=(OLD/'six-chapter-final-BC-Chinese-a06.md').read_bytes()
assert pin(OLD/'six-chapter-final-BC-Chinese-a06.md')['sha256']=='aa5336e4a57dd58baad2c9cabb88a9a870e27494e2c9366e89c0577223b6a5ef'
old=tool.paragraphs(old_raw)
assert old['C05-14'].endswith('A和C的实际到达观测各自保留。')
bridge=old['C05-14']+'下面回到整军直走的A。'
new_raw=old_raw.replace(old['C05-14'].encode(),bridge.encode(),1)
new=tool.paragraphs(new_raw)
assert [key for key in old if old[key]!=new[key]]==['C05-14']
body=OUT/'six-chapter-final-BC-Chinese-a06.md';write(body,new_raw)
ledger=json.loads((OLD/'claim-ledger-final-BC-a06.json').read_bytes())
assert pin(OLD/'claim-ledger-final-BC-a06.json')['sha256']=='225596f54939e9aba215c2acaeaed1a87ae323efa3b909b53bed7713ebfe4928'
for row in ledger['claims']:
    if row['id']=='C05-14':row['claim_summary']=bridge
ledger['Root_single_bridge_revision']={'previous_body':pin(OLD/'six-chapter-final-BC-Chinese-a06.md'),
 'previous_ledger':pin(OLD/'claim-ledger-final-BC-a06.json'),
 'changed_only_paragraph':'C05-14','appended_exact_Chinese':'下面回到整军直走的A。',
 'other68_Chinese_paragraphs_exact':True,'stable_C05_15_audio_not_changed':True,
 'required_picture_A_label_at_C05_15_16_start':True}
ledger_path=OUT/'claim-ledger-final-BC-a06.json';write(ledger_path,ledger)
for source in sorted((OLD/'sources').glob('*')):write(OUT/'sources'/source.name,source.read_bytes())
oral=json.loads((OLD/'oral-final-request-PENDING-ROOT-REVIEW.json').read_bytes())
oral['current_partial_draft_body']=pin(body)
oral['future']['final_chinese_body']=pin(body);oral['future']['final_claim_ledger']=pin(ledger_path)
write(OUT/'oral-final-request-PENDING-ROOT-REVIEW.json',oral)
tool.load_request(OUT/'oral-final-request-PENDING-ROOT-REVIEW.json')
review=json.loads((OLD/'ROOT-SOURCE-REVIEW-REQUEST.json').read_bytes())
review['chinese_body_sha256']=pin(body)['sha256'];review['chinese_ledger_sha256']=pin(ledger_path)['sha256']
review['Root_prior_semantic_review']='Root read full prior69 actual Chinese; B/C numeric boundaries,15deviations/no strictwinner/1percent getter/no payments/historyunknown/terminalMain passed. Only C05-14 bridge requested; final exact a02 review pending.'
write(OUT/'ROOT-SOURCE-REVIEW-REQUEST.json',review)
changed=review['changed_paragraph_ids']
rows=[row for row in ledger['claims'] if row['id'] in changed]
summary={'schema':'ck3.e04.final-BC-Root-seven-claims-review.v1','body':pin(body),'ledger':pin(ledger_path),
 'source_review_template':pin(OUT/'ROOT-SOURCE-REVIEW-REQUEST.json'),
 'required_final_source_review_fields':{
  'source_review_status':'NO_BLOCK','final_freeze':True,
  'changed_paragraph_ids':changed,'subtitle_changed_ids':review['subtitle_changed_ids'],
  'chinese_body_sha256':pin(body)['sha256'],'chinese_ledger_sha256':pin(ledger_path)['sha256'],
  'C_terminal_source_sha256':review['C_terminal_source_sha256'],
  'C_sampling_Root_receipt_sha256':review['C_sampling_Root_receipt_sha256'],
  'C_Main_scope_source_sha256':review['C_Main_scope_source_sha256'],
  'C_subject_scope':review['C_subject_scope'],'C_controlled_comparison_eligibility':'NOT_GRANTED',
  'ABC_results':review['ABC_results'],'ABC_winner':None},
 'reviewer_metadata_required':{'reviewer':'/root','reviewed_utc':'actual reviewer timestamp','review_basis':'exactbody+ledger hashes and actual source pins'},
 'required_fields_are_contract_not_an_actual_NO_BLOCK_receipt':True,
 'claim_summaries':[{ 'id':row['id'],'text_zh':row['claim_summary'],'source_keys':row['source_keys'],'limits':row['assumptions_and_limits']} for row in rows]}
write(OUT/'ROOT-SEVEN-CLAIMS-AND-REVIEW-FIELDS.json',summary)
write(OUT/'ROOT-SEVEN-FULL-CLAIM-ROWS.json',{'body':pin(body),'ledger':pin(ledger_path),'claims':rows})
write(OUT/'SINGLE-BRIDGE-RECEIPT.json',{'status':'PASS_EXACT_SINGLE_ROOT_REQUESTED_BRIDGE','actual_changed_since_a01':['C05-14'],
 'other68_exact':True,'all7_voice_diff_vsA_unchanged':changed,'C05_01_03_15_exact_old_Chinese':True,
 'C05_15_16_picture_A_label_required':True,'new_TTS_requests':0,'human_signoff':False})
write(OUT/'ROOT-DELIVERY.json',{'status':'ACTUAL_FINAL_BODY_LEDGER_WITH_REQUESTED_BRIDGE_PENDING_ROOT_NO_BLOCK',
 'Chinese':pin(body),'ledger':pin(ledger_path),'review_request':pin(OUT/'ROOT-SOURCE-REVIEW-REQUEST.json'),
 'seven_summary_and_review_fields':pin(OUT/'ROOT-SEVEN-CLAIMS-AND-REVIEW-FIELDS.json'),
 'seven_full_claim_rows':pin(OUT/'ROOT-SEVEN-FULL-CLAIM-ROWS.json'),
 'oral_request':pin(OUT/'oral-final-request-PENDING-ROOT-REVIEW.json'),
 'single_bridge':pin(OUT/'SINGLE-BRIDGE-RECEIPT.json'),'changed_paragraph_ids':changed,
 'current_C_terminal':oral['future']['final_C_terminal_source'],'current_Root_review':oral['current_C_Root_basis_source'],
 'current_Main_scope':oral['current_C_Main_scope_source'],'new_TTS_requests':0,'human_signoff':False})
print(json.dumps({'status':'ACTUAL_ROOT_BRIDGE_READY','delivery':pin(OUT/'ROOT-DELIVERY.json'),
 'body':pin(body),'ledger':pin(ledger_path),'review_template':pin(OUT/'ROOT-SOURCE-REVIEW-REQUEST.json'),
 'seven_claim_summary':pin(OUT/'ROOT-SEVEN-CLAIMS-AND-REVIEW-FIELDS.json')}))
