"""Extend the frozen v6 variable reader with exact saved native basehealth."""
import argparse
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import re

LEGACY=Path(__file__).with_name('inspect_save_readback.py')
def sha(p: Path) -> str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def inspect(args: argparse.Namespace) -> None:
 args.output_dir.mkdir(exist_ok=False)
 spec=importlib.util.spec_from_file_location('retained_sxad_v6',LEGACY)
 if spec is None or spec.loader is None:raise ValueError('retained v6 decoder is unavailable')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 data=module.inspect(args.run,args.save_dir,args.sdk,args.player_id,args.output_dir,native_save=args.native_save)
 for c in data['characters']:
  raw_path=args.output_dir/f'character-{c["character_id"]}.txt'
  text=raw_path.read_text(encoding='utf-8')
  health=re.findall(r'(?m)^\s*health=(-?\d+(?:\.\d+)?)\s*$',text)
  if len(health)!=1:raise ValueError(f'unique native basehealth missing for{c["character_id"]}: {health}')
  raw=health[0];ticks=Decimal(raw)*100000
  if ticks!=ticks.to_integral_value():raise ValueError('basehealth finer thanQ100000')
  c['base_health_saved']={'field':'alive_data.health','raw_text':raw,'decimal':str(Decimal(raw)),'q100000_ticks':int(ticks)}
  for v in c['variables'].values():
   if v.get('type')=='value':
    signed=v['signed_identity']
    v['fixed5_ticks_exact']=signed
    assert v['integer_exact']==(signed//100000 if signed%100000==0 else None)
  for m in c['modifiers']:
   q=Decimal(m['scale_decimal'])*100000
   m['scale_q100000_ticks_exact']=int(q) if q==q.to_integral_value() else None
 data['schema']='sxad.real-save-health1.1.0-readback.v1'
 data['decoder_script_sha256']=sha(Path(__file__))
 data['retained_v6_decoder']={'path':LEGACY.as_posix(),'sha256':sha(LEGACY)}
 data['readback_scope']='Independently saved base skills/basehealth, signed variables and sampled modifier scale; native effective health comes from separate player query or recorded scripted getters.'
 output=args.output_dir/'health-readback.json'
 with output.open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'output':str(output),'sha256':sha(output),'counts':[data['pass_count'],data['fail_count'],data['missing_count']],'characters':len(data['characters'])}))

def _shared_pin(path):
    path = Path(path).resolve(strict=True)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def _shared_checked(reference):
    if not isinstance(reference, dict) or set(reference) != {'path', 'bytes', 'sha256'}:
        raise ValueError('exact file Pin shape required')
    if type(reference['bytes']) is not int:
        raise ValueError('Pin bytes must be a true integer')
    actual = _shared_pin(reference['path'])
    if (actual['bytes'], actual['sha256']) != (reference['bytes'], reference['sha256']):
        raise ValueError('input file changed: ' + reference['path'])
    return actual


def _shared_values(block, key):
    if not isinstance(block, dict) or block.get('type') != 'block':
        raise ValueError('complete AST block required')
    return [entry['value'] for entry in block['entries'] if entry['key'] == key]


def _shared_one(block, key, required=True):
    values = _shared_values(block, key)
    if not values and not required:
        return None
    if len(values) != 1:
        raise ValueError('unique AST field required: ' + key)
    return values[0]


def _shared_atom(block, key, required=True):
    value = _shared_one(block, key, required)
    if value is None:
        return None
    if value.get('type') != 'atom':
        raise ValueError('atomic field required: ' + key)
    return value['token']


def _shared_text(value):
    return json.loads(value) if value.startswith('"') else value


def _shared_variables(actor):
    """Full ACTOR absence stays absent; never scan another record for a name."""
    alive = _shared_one(actor, 'alive_data', False)
    if alive is None:
        return {}
    variables = _shared_one(alive, 'variables', False)
    if variables is None:
        return {}
    data = _shared_one(variables, 'data', False)
    if data is None:
        # A present unexpected variables container is not evidence of absence.
        raise ValueError('variables/data layout is unknown')
    result = {}
    for entry in data['entries']:
        slot = entry['value']
        name = _shared_text(_shared_atom(slot, 'flag'))
        if not name.startswith(('sxat_', 'sxad_')):
            continue
        if name in result:
            raise ValueError('duplicate saved variable: ' + name)
        value = _shared_one(slot, 'data')
        kind = _shared_atom(value, 'type', False)
        raw = _shared_atom(value, 'identity', False)
        identity = int(raw) if raw is not None else None
        row = {'present': True, 'type': kind, 'identity': identity,
               'raw_slot_ast': slot}
        if kind == 'value':
            if identity is None:
                # The retained v6 inspector explicitly derives zero for this
                # exact typed-default representation, while retaining null.
                # Missing scopes/unknown type/container do NOT take this path.
                if [e['key'] for e in value['entries']] != ['type']:
                    raise ValueError('unknown omitted-identity value structure: ' + name)
                signed = 0
                row['exact_legacy_typed_default_zero'] = True
            else:
                if identity < -(1 << 63) or identity >= (1 << 64):
                    raise ValueError('saved fixed5 identity outside exact64: ' + name)
                signed = identity - (1 << 64) if identity >= (1 << 63) else identity
            row.update(signed_identity=signed, fixed5_ticks_exact=signed,
                       integer_exact=signed // 100000 if signed % 100000 == 0 else None,
                       signed_number_decimal=str(Decimal(signed) / Decimal(100000)))
        elif kind == 'char':
            # A missing character identity is unresolved, never character0.
            if identity is None or identity < 0:
                raise ValueError('actual char identity missing: ' + name)
            row['character_id'] = identity
        result[name] = row
    return result


def _shared_modifiers(alive):
    result = []
    def visit(block):
        for entry in block['entries']:
            value = entry['value']
            if value.get('type') != 'block':
                continue
            if entry['key'] == 'modifier' and _shared_values(value, 'modifier'):
                key = _shared_text(_shared_atom(value, 'modifier'))
                scales = [(k, _shared_atom(value, k, False)) for k in ('scale', 'multiplier')]
                scales = [(k, v) for k, v in scales if v is not None]
                if len(scales) > 1:
                    raise ValueError('ambiguous modifier scale: ' + key)
                source, raw = scales[0] if scales else (None, None)
                decimal = Decimal(raw) if raw is not None else Decimal(1)
                ticks = decimal * Decimal(100000)
                if not decimal.is_finite() or ticks != ticks.to_integral_value():
                    raise ValueError('modifier scale is not exactQ100000: ' + key)
                result.append({'key': key, 'scale_raw': raw, 'scale_source_key': source,
                    'scale_default': 1 if raw is None else None, 'scale_decimal': str(decimal),
                    'scale_q100000_ticks_exact': int(ticks), 'saved_modifier_ast': value,
                    'raw_record': None, 'record_source': 'ACTUAL_FULL_ACTOR_AST; no original raw-text substring fabricated'})
            visit(value)
    visit(alive)
    return result


def _shared_character(scope, reference_names):
    actor = scope['ast']
    identity = int(scope['path'][-1])
    alive = _shared_one(actor, 'alive_data', False)
    if alive is None:
        raise ValueError('required health role is not a complete living ACTOR: ' + str(identity))
    health = _shared_atom(alive, 'health')
    decimal = Decimal(health)
    ticks = decimal * Decimal(100000)
    if not decimal.is_finite() or ticks != ticks.to_integral_value():
        raise ValueError('native saved basehealth finer thanQ100000')
    fields = [(k, _shared_one(actor, k, False)) for k in ('skill', 'skills', 'base_skill', 'base_skills')]
    fields = [(k, v) for k, v in fields if v is not None]
    if len(fields) != 1:
        raise ValueError('unique base skill vector missing: ' + str(identity))
    key, vector = fields[0]
    if any(e['key'] != '' or e['value']['type'] != 'atom' for e in vector['entries']):
        raise ValueError('saved base skill vector layout unknown')
    skills = [int(e['value']['token']) for e in vector['entries']]
    if len(skills) != 6:
        raise ValueError('six actual base skill elements required')
    variables = _shared_variables(actor)
    return {'character_id': identity, 'alive': True, 'save_record_level': 1,
        'role_flags': [key for key in variables if key.startswith(('sxat_receiver_', 'sxat_donor_'))],
        'root_reference_names': reference_names,
        'base_skill_save_field': {'field': key, 'array': skills},
        'base_health_saved': {'field': 'alive_data.health', 'raw_text': health,
            'decimal': str(decimal), 'q100000_ticks': int(ticks)},
        'variables': variables, 'modifiers': _shared_modifiers(alive),
        'raw_character_sha256': None,
        'canonical_actor_token_sha256': scope['canonicalTokenSha256'],
        'raw_actor_ast': actor,
        'raw_text_unavailable_not_fabricated': True}


def inspect_shared(index_path, output_dir):
    index_path = Path(index_path).resolve(strict=True)
    index = json.loads(index_path.read_bytes())
    if index.get('schema') != 'sxad.health.shared-inspection-index.v1':
        raise ValueError('explicit shared-inspection index schema required')
    if index.get('machine_id') != 'desktop-3fevhd2-1c74096080':
        raise ValueError('wrong machine source')
    fixture_pin = _shared_checked(index['fixture'])
    fixture = json.loads(Path(fixture_pin['path']).read_bytes())
    if len(fixture['base_skill_contract']) != 20 or len(fixture['expected_pass_markers']) != 20:
        raise ValueError('original twenty-case fixture required')
    root_id = str(index['root_actor_id'])
    if not root_id.isdecimal():
        raise ValueError('actual runtime root ID required')
    save_pin = _shared_checked(index['save'])
    scopes, provenance, stream = {}, [], None
    if not index['reports'] or len(index['reports']) > 42:
        raise ValueError('finite root plus narrow role batches required')
    actual_date = None
    for source in index['reports']:
        for key in ('request', 'report', 'execution'):
            _shared_checked(source[key])
        if source['report']['bytes'] > 1048576:
            raise ValueError('original1MiB report cap exceeded')
        report = json.loads(Path(source['report']['path']).read_bytes())
        execution = json.loads(Path(source['execution']['path']).read_bytes())
        if (report['schema'] != 'ck3-save-inspection-v4' or report['businessAssessment'] != 'NOT_ASSESSED'
                or report['gameStarted'] is not False or execution['original_wait_returncode'] != 0
                or execution['stop_reason'] is not None or execution.get('job_active_after_original_wait') != 0
                or not execution['source_Save_decoder_java_App55_4JAR_source9_pins_unchanged']):
            raise ValueError('original reader EOF/wait/Job/pins unavailable')
        actual_request = json.loads(Path(source['request']['path']).read_bytes())
        if report['request'] != actual_request:
            raise ValueError('request/report input binding mismatch')
        for key in ('request', 'report'):
            recorded = execution[key]
            expected = source[key]
            if (Path(recorded['path']).resolve(), recorded['bytes'], recorded['sha256']) != (Path(expected['path']).resolve(), expected['bytes'], expected['sha256']):
                raise ValueError('execution/' + key + ' exact Pin link mismatch')
        decoded = report['decoded']
        for pin in (decoded['save'], report['request']['save']):
            if (Path(pin['path']).resolve(), pin['bytes'], pin['sha256']) != (Path(save_pin['path']).resolve(), save_pin['bytes'], save_pin['sha256']):
                raise ValueError('cross-save report rejected')
        if decoded['exitCode'] != 0 or decoded['saveUnchanged'] is not True:
            raise ValueError('complete decoder EOF not proven')
        observed_stream = (decoded['streamBytes'], decoded['streamSha256'])
        if stream is not None and stream != observed_stream:
            raise ValueError('mixed decoded streams')
        stream = observed_stream
        projection = decoded['projection']
        dates = [e['value']['token'] for e in projection['rootScalars'] if e['key'] == 'date']
        if len(dates) != 1 or actual_date not in (None, dates[0]):
            raise ValueError('mixed or unknown physical Saved date')
        actual_date = dates[0]
        for scope in projection['scopes']:
            if scope['kind'] != 'ACTOR':
                continue
            if scope['coverage'] != 'FULL_RECORD' or scope['path'][:1] != ['living'] or len(scope['path']) != 2:
                raise ValueError('actual FULL living ACTOR required')
            identity = scope['path'][-1]
            if identity in scopes and scopes[identity] != scope:
                raise ValueError('conflicting full actor material')
            scopes[identity] = scope
        provenance.append(source)
    if root_id not in scopes:
        raise ValueError('actual full root record absent')
    root_variables = _shared_variables(scopes[root_id]['ast'])
    references = {}
    for contract in fixture['base_skill_contract']:
        for role in ('receiver', 'donor'):
            name = contract[role + '_root_reference']
            value = root_variables.get(name)
            if not value or value['type'] != 'char' or 'character_id' not in value:
                raise ValueError('actual typed role ref absent: ' + name)
            references[name] = value['character_id']
    wanted = {str(cid) for cid in references.values()} | {root_id}
    if set(scopes) != wanted:
        raise ValueError('exact actual root/role actor set required; missing or unrelated extra actor')
    characters = [_shared_character(scopes[cid], [name for name, identity in references.items() if str(identity) == cid])
                  for cid in sorted(wanted, key=int)]
    root = next(c for c in characters if str(c['character_id']) == root_id)
    names = ['sxat_case_' + marker.removeprefix('SXAT: PASS ').replace('-', '_')
             for marker in fixture['expected_pass_markers']]
    results = {name: root_variables.get(name) for name in names}
    result = {'schema': 'sxad.real-save-health1.1.0-readback.shared-inspection-v4.v1',
        'run_id': index.get('run_id'), 'melted_sha256': stream[1], 'save_input': save_pin,
        'decoder_script_sha256': sha(Path(__file__)), 'fixture_manifest_sha256': fixture_pin['sha256'],
        'root_character': root, 'root_references': references, 'case_results': results, 'characters': characters,
        'pass_count': sum(v is not None and v.get('integer_exact') == 1 for v in results.values()),
        'fail_count': sum(v is not None and v.get('integer_exact') == 0 for v in results.values()),
        'missing_count': sum(v is None for v in results.values()), 'actual_root_date': actual_date,
        'shared_index': _shared_pin(index_path), 'actual_complete_EOF_reports': provenance,
        'original_Inspection_businessAssessment': 'NOT_ASSESSED, unmodified',
        'readback_scope': 'Actual full ACTOR AST normalized field by field for unchanged verify_health_readback.py; not generic-v4 relabeling. No Native physical flag or effective health/trait-render credit.',
        'raw_text_boundary': 'Canonical ACTOR token digest/AST retained; original character raw text SHA and modifier raw substring are null, never fabricated.',
        'numeric_boundary': 'Only int/Decimal. Complete canonical typed-value omitted identity follows explicit retained-v6 zero-default semantics with original identity=null; missing/unknown scopes/types/containers never synthesize zero.'}
    if _shared_checked(index['save']) != save_pin:
        raise ValueError('save changed before derived DTO publication')
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=False)
    destination = output_dir / 'health-readback.json'
    with destination.open('x', encoding='utf-8', newline='\n') as stream_out:
        json.dump(result, stream_out, ensure_ascii=False, indent=2)
        stream_out.write('\n')
    print(json.dumps({'output': str(destination), 'sha256': sha(destination),
        'counts': [result['pass_count'], result['fail_count'], result['missing_count']], 'characters': len(characters)}))


def shared_main():
    p = argparse.ArgumentParser(description='Explicit actual shared Inspection report adapter; no JVM/Game')
    p.add_argument('--shared-inspection-index', required=True, type=Path)
    p.add_argument('--output-dir', required=True, type=Path)
    a = p.parse_args()
    inspect_shared(a.shared_inspection_index, a.output_dir)



def main() -> None:
 import sys
 if "--shared-inspection-index" in sys.argv[1:]:
  shared_main()
  return
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['run','sdk','output-dir']:p.add_argument('--'+name,required=True,type=Path)
 source=p.add_mutually_exclusive_group(required=True)
 source.add_argument('--save-dir',type=Path)
 source.add_argument('--native-save',type=Path)
 p.add_argument('--player-id',required=True,type=int)
 inspect(p.parse_args())
if __name__=='__main__':main()
