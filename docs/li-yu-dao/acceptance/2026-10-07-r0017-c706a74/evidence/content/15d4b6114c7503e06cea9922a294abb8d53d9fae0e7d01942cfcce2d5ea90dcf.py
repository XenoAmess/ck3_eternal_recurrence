"""Materialize one actual new HEAD/export/production registry; pending refuses."""
from pathlib import Path
import argparse,json,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent/'reader'))
import business_contract_migration_v2 as migration
import actual_reader_lineage_v2 as reader_lineage
def write(p,obj):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--export-report',type=Path,required=True);p.add_argument('--production-manifest',type=Path,required=True)
 p.add_argument('--production-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 policy,old=migration.policy() # NULL registration fails before future artifact reads.
 export=migration.jread(a.export_report.read_bytes());head=export['source']['head'];root=Path(export['source_root'])
 current={rel:migration.reference(root/'mod_li_yu_dao'/rel)['sha256'] for rel in old}
 migration.verify_business_map(current)
 changed={rel:migration.reference(root/'mod_li_yu_dao'/rel) for rel in migration.ALLOWED}
 ast_proof=migration.verify_two_complete_AST({rel:migration.read_ref(desc) for rel,desc in changed.items()})
 migration.need(not a.output.exists(),'new registry output required');a.output.mkdir(parents=True,exist_ok=False)
 write(a.output/'BUSINESS-MANIFEST69.actual.json',{'schema':'lyd.actual-business-manifest69.v2','source_head':head,'files':current})
 reg={'schema':'lyd.business-contract-migration-registry.r17-ordering.v3','policy_sha256':migration.POLICY_SHA,'source_head':head,
  'source_export_report':migration.reference(a.export_report),'source_root':export['source_root'],'production_root':a.production_root.as_posix(),
  'production_manifest':migration.reference(a.production_manifest),'business_manifest':migration.reference(a.output/'BUSINESS-MANIFEST69.actual.json'),
  'changed_source_files':changed,'AST_projection':ast_proof,
  'executing_reader_artifact':migration.reference(root/'tools/lyd_i3b_checkpoint_readback/reader/i3b_checkpoint_reader.py'),
  'saved_faith_semantics_artifact':migration.reference(root/'tools/lyd_i3b_checkpoint_readback/reader/dependencies/saved_faith_semantics_12003.json')}
 write(a.output/'BUSINESS-MIGRATION-REGISTRY.actual.json',reg)
 try:
  qualification=migration.verify_registry(reg,head,current)
  qualification['executing_reader_lineage']=reader_lineage.verify_reader_lineage(reg,reg['executing_reader_artifact'],reg['saved_faith_semantics_artifact'])
  write(a.output/'REGISTRY-QUALIFICATION.actual.json',qualification)
 except Exception as error:
  write(a.output/'REGISTRY-FAILURE.actual.json',{'status':'RED_PRESERVED','error_type':type(error).__name__,'error':str(error),'actual_acceptance_credit':None});raise
 print(json.dumps({'registry':migration.reference(a.output/'BUSINESS-MIGRATION-REGISTRY.actual.json'),'source_head':head,'actual_acceptance_credit':None},indent=2))
 return 0
if __name__=='__main__':raise SystemExit(main())
