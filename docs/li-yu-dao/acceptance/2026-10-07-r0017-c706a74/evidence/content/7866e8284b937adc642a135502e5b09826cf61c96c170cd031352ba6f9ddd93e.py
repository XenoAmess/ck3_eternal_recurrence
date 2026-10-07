"""Exact new executing reader artifacts, separate from historical protocol hash."""
from pathlib import Path
from business_contract_migration_v2 import need,read_ref,jread,sha
READER_SHA='eb68af08c5d636e4b91caa4e0290bb889ae912ca5b7e0158f4e4d99f85958736'
SEMANTICS_SHA='dfdf5a12ea0159db8b4a6d644e61baf3e73538b32007844208ad9c1485afad90'
def verify_reader_lineage(registry,executing_reader_artifact,saved_faith_semantics_artifact,source_archive_sha256=None):
 need(executing_reader_artifact==registry['executing_reader_artifact'] and saved_faith_semantics_artifact==registry['saved_faith_semantics_artifact'],'executing reader artifact descriptors differ')
 root=Path(registry['source_root']).resolve()/'tools/lyd_i3b_checkpoint_readback/reader'
 need(Path(executing_reader_artifact['path']).resolve()==(root/'i3b_checkpoint_reader.py').resolve(),'executing reader must be exact new clean source export artifact')
 need(Path(saved_faith_semantics_artifact['path']).resolve()==(root/'dependencies/saved_faith_semantics_12003.json').resolve(),'saved Faith semantics must be exact new clean source export artifact')
 reader_bytes=read_ref(executing_reader_artifact);semantics_bytes=read_ref(saved_faith_semantics_artifact)
 need(sha(reader_bytes)==READER_SHA and sha(semantics_bytes)==SEMANTICS_SHA,'unreviewed executing reader or semantic model')
 model=jread(semantics_bytes);need(model['schema']=='lyd.ck3-1.20.0.3.saved-Faith-semantics.v2','actual semantics artifact model differs')
 export=jread(read_ref(registry['source_export_report']))
 if source_archive_sha256 is not None:need(export['source_archive']['sha256']==source_archive_sha256,'migration export archive differs from actual provenance')
 return {'schema':'lyd.executing-reader-artifact-lineage.v2','executing_reader_artifact':executing_reader_artifact,
         'saved_faith_semantics_artifact':saved_faith_semantics_artifact,'actual_source_head':registry['source_head'],
         'legacy_protocol_source_head':'632f0a57a07aa6299052004589ed6f7632e7d8f7','native_predicate_observed':None,'actual_acceptance_credit':None}
