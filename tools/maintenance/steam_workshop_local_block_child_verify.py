from pathlib import Path
import json,sys
import steam_workshop_local_block as m

def main():
 m.require_reviewed_machine()
 backup=json.loads(Path(sys.argv[1]).read_text('utf-8'))
 if backup.get('machine_id')!=m.MACHINE or backup.get('item_ids')!=m.IDS:raise RuntimeError('Wrong machine/items')
 parents=[Path(x['path']) for x in backup['parents']]
 originals=[(Path(x['path']),m.s.ConvertStringSecurityDescriptorToSecurityDescriptor(x['original_sddl'],1),None) for x in backup['parents']]
 rows=m.adversarial(parents,originals)
 passed=all(x.get('blocked',x.get('success',False)) for x in rows)
 m.save(sys.argv[2],{'machine_id':m.MACHINE,'observed_at_utc':m.now(),'inherited_rollback_handles':False,'tests':rows,'all_blocked_and_siblings_ok':passed})
 print(json.dumps({'tests':len(rows),'passed':passed}))
 return 0 if passed else 2

if __name__=='__main__':sys.exit(main())
