from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
class Unproved(RuntimeError):
	pass
def need(v, label):
	if not v:
		raise Unproved(label)
def ni(v, label, minimum=0):
	need(type(v) is int and v >= minimum, label)
	return v
def hd(v):
	need(isinstance(v, str) and re.fullmatch(r'[0-9a-f]{40}', v), 'exact ')
	return v
def object_pairs(pairs):
	result = {}
	for name, v in pairs:
		need(name not in result, 'dup: ' + name)
		result[name] = v
	return result
def finite_float(v):
	parsed = float(v)
	need(math.isfinite(parsed), 'nonfin')
	return parsed
def reject_constant(v):
	raise Unproved('constant: ' + v)
def canonical(v):
	return json.dumps(v, ensure_ascii=False, sort_keys=True,
					  separators=(',', ':'), allow_nan=False).encode('utf-8')
def agg(rows):
	result = hashlib.sha256()
	for row in rows:
		result.update(canonical(row))
		result.update(b'\n')
	return result.hexdigest()
def absolute(v, cwd=None):
	need(isinstance(v, str) and v and '\0' not in v, 'path t')
	path = Path(v)
	if not path.is_absolute():
		need(cwd is not None, 'abs: ' + v)
		parent = Path(cwd)
		need(parent.is_absolute(), 'absolu')
		path = parent / path
	return path
def pk(v, cwd=None):
	return os.path.normcase(str(absolute(v, cwd).resolve(strict=False)))
def within(path, roots):
	candidate = pk(str(path))
	for root in roots:
		root_key = pk(root)
		try:
			if os.path.commonpath([candidate, root_key]) == root_key:
				return True
		except ValueError:
			continue
	return False
def identity(info):
	return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
def read_file(path, roots, limit, capture=False):
	ni(limit, 'bound', 1)
	need(isinstance(roots, list) and roots, 'explic')
	sel = absolute(path).resolve(strict=True)
	need(within(sel, roots), 'outside: ' + str(sel))
	before = sel.stat()
	need(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit, 'bounde')
	hasher, chunks, total = hashlib.sha256(), [], 0
	with sel.open('rb') as stream:
		opened = os.fstat(stream.fileno())
		need(identity(before) == identity(opened), 'refere')
		while True:
			block = stream.read(min(1048576, limit - total + 1))
			if not block:
				break
			total += len(block)
			need(total <= limit, 'refere')
			hasher.update(block)
			if capture:
				chunks.append(block)
		after = os.fstat(stream.fileno())
	need(identity(opened) == identity(after) == identity(sel.stat()) and
		 total == after.st_size, 'refere')
	ref = {'path': str(sel), 'bytes': total, 'sha256': hasher.hexdigest()}
	return ref, b''.join(chunks) if capture else None
def json_file(path, roots, limit):
	ref, data = read_file(path, roots, limit, True)
	try:
		v = json.loads(data.decode('utf-8'), object_pairs_hook=object_pairs,
						   parse_float=finite_float, parse_constant=reject_constant)
	except (UnicodeError, ValueError, RecursionError) as error:
		raise Unproved('JSON: ' + str(path)) from error
	need(isinstance(v, dict), 'object: ' + str(path))
	return ref, v
def eq(left, right, label, cwd=None):
	need(pk(left, cwd) == pk(right), label)
def stage_refs(j, roots, jb):
	base = absolute(j['job_root']) / 'stage'
	qr, request = json_file(str(base.with_suffix('.request.json')), roots, jb)
	rr, result = json_file(str(base.with_suffix('.result.json')), roots, jb)
	for v in (request, result):
		need(v['job_id'] == j['job_id'] and v['argv'] == j['argv'], 'actual')
		eq(v['cwd'], j['cwd'], 'actual')
		need(v['environment_settings'] == j['environment'] and v['shell'] is False and
			 v['automatic_retry'] is False, 'actual')
	need(request['status'] == 'NOT_STARTED' and request['process_started'] is False and
		 request['exit_code'] is None and request['pid'] is None, 'prelau')
	need(result['status'] == 'PROCESS_EXIT_OBSERVED' and result['process_started'] is True and
		 result['exit_observed'] is True and result['direct_child_reaped'] is True and
		 type(result['exit_code']) is int and result['exit_code'] == 0, 'actual')
	ni(result['pid'], 'PID', 1)
	return {'request': qr, 'result': rr}, result
def hashed(path, cx):
	sel = absolute(path).resolve(strict=True)
	k = pk(str(sel))
	cache = cx['file_cache']
	if k in cache:
		saved, before = cache[k]
		need(identity(sel.stat()) == before, 'changed: ' + str(sel))
		return saved
	ref, _ = read_file(str(sel), cx['roots'], cx['artifact_bound'])
	cache[k] = (ref, identity(sel.stat()))
	return ref
def sdkfile(path, want_sha, cx):
	sel = absolute(path).resolve(strict=True)
	sdk = absolute(cx['sdk_root']).resolve(strict=True)
	need(within(sel, [str(sdk)]), 'manage')
	ref = hashed(str(sel), cx)
	need(ref['sha256'] == want_sha, 'select')
	return ref
def deps(j, cx):
	spec = j['dependencies']
	need(spec['policy'] == 'fresh_capture' and spec['required'] is True and
		 spec['accepted_versions'] == cx['accepted_versions'], 'fresh ')
	ref, pkt = json_file(j['dependencies_file'], cx['roots'], cx['json_bound'])
	need(isinstance(pkt.get('Version'), str) and pkt['Version'] in cx['accepted_versions'] and
		 isinstance(pkt.get('Data'), dict), 'suppor')
	data = pkt['Data']
	need(isinstance(data.get('Source'), str), 'MSVC D')
	eq(data['Source'], j['source'], 'MSVC Data.Source', j['cwd'])
	need(spec['source_sha256'] == j['source_sha256'], 'depend')
	sr = sdkfile(j['source'], j['source_sha256'], cx)
	includes = data.get('Includes')
	need(isinstance(includes, list) and all(isinstance(v, str) and v for v in includes), 'MSVC D')
	rows, keys = [], set()
	for text in includes:
		path = absolute(text, j['cwd']).resolve(strict=True)
		need(within(path, spec['allowed_roots']), 'per-jo')
		k = pk(str(path))
		keys.add(k)
		ref = hashed(str(path), cx)
		if within(path, [cx['sdk_root']]):
			sdkfile(str(path), ref['sha256'], cx)
		else:
			need(not within(path, cx['project_header_roots']) and
				 within(path, cx['external_dependency_roots']), 'unadmi')
		rows.append(ref)
		cx['seen_headers'].add(k)
	for changed in cx['changed_headers']:
		path, pinned = changed['path'], changed['sha256']
		sdkfile(path, pinned, cx)
		need(not j['index'] in changed.get('known_required_owner_indices', []) or pk(path) in keys, 'actual')
		need(all(pk(r['path']) == pk(path) for r in rows
				 if Path(r['path']).name.casefold() == Path(path).name.casefold()), 'mixed ')
	need(all(pk(v) in keys for v in spec.get('required_includes', [])), 'requir')
	return ref, sr, rows, pkt
def argv_option(argv, flag):
	values = []
	for i, token in enumerate(argv):
		if token.casefold() == flag.casefold():
			need(i + 1 < len(argv), 'missin')
			values.append(argv[i + 1])
		elif token.casefold().startswith(flag.casefold()) and len(token) > len(flag):
			values.append(token[len(flag):])
	need(len(values) == 1 and values[0], 'option: ' + flag)
	return values[0]
def compile_one(j, owner, cx):
	need(type(j['index']) is int and j['owner_tuple'] == owner, 'indepe')
	need(within(absolute(j['job_root']), [cx['build_root']]) and
		 within(absolute(j['output']), [j['job_root']]) and
		 within(absolute(j['dependencies_file']), [j['job_root']]), 'fresh ')
	argv = j['argv']
	need(isinstance(argv, list) and argv and Path(argv[0]).name.casefold() == 'cl.exe' and
		 all(isinstance(v, str) and '\0' not in v for v in argv) and
		 not any(v.startswith('@') for v in argv), 'actual')
	i = j['source_arg_index']
	need(type(i) is int and 0 <= i < len(argv), 'actual')
	eq(argv[i], j['source'], 'actual source operand', j['cwd'])
	eq(argv_option(argv, '/Fo'), j['output'], 'actual /Fo binding', j['cwd'])
	eq(argv_option(argv, '/sourceDependencies'), j['dependencies_file'], 'actual deps binding', j['cwd'])
	need(hashed(argv[0], cx)['sha256'] == j['tool_sha256'], 'actual')
	stages, _ = stage_refs(j, cx['roots'], cx['json_bound'])
	vr, verified = json_file(str(absolute(j['job_root']) / 'stage.verified.json'),
									  cx['roots'], cx['json_bound'])
	need(verified['job_id'] == j['job_id'] and verified['index'] == j['index'] and
		 verified['owner_tuple'] == owner and verified['recipe_kind'] == j['recipe_kind'] and
		 verified['old_actual_recipe_claimed'] == j.get('old_actual_recipe_claimed'), 'actual')
	dep_ref, sr, includes, pkt = deps(j, cx)
	a = verified['dependencies']
	need(a['Version'] == pkt['Version'] and a['Includes'] == pkt['Data']['Includes'] and
		 a['include_sha256'] == [r['sha256'] for r in includes], 'actual')
	eq(a['Source'], j['source'], 'actual verified source', j['cwd'])
	object_ref = hashed(j['output'], cx)
	need(object_ref['sha256'] == verified['object_sha256'], 'actual')
	return {'index': j['index'], 'owner': owner, 'source': sr, 'object': object_ref,
			'dependencies': dep_ref, 'includes_digest': agg(includes),
			'stages': stages, 'verification': vr}
def raw_ref(v, ctx, decode=False):
	need(isinstance(v, dict), 'raw re')
	a, data = json_file(v['path'], ctx['roots'], ctx['json_bound']) if decode else (
		hashed(v['path'], ctx), None)
	need(a['sha256'] == v['sha256'], 'raw re')
	if 'bytes' in v: need(type(v['bytes']) is int and a['bytes'] == v['bytes'], 'raw si')
	return a, data
def check_stage(v, j, ctx):
	refs, a = stage_refs(j, ctx['roots'], ctx['json_bound'])
	need(v['argv'] == j['argv'] and type(v['exit_code']) is int and v['exit_code'] == 0 and
		 v['pid'] == a['pid'], 'actual')
	eq(v['cwd'], j['cwd'], 'actual')
	for name in ('request', 'result'): need(raw_ref(v[name + '_ref'], ctx)[0] == refs[name], 'stage ')
def link_tokens(j, ctx, manifest_sha):
	tokens, roles = [], []
	rsps = {pk(r['path']): r for r in j.get('responsefiles', [])}
	for token, role in zip(j['argv'][1:], j['token_roles'][1:]):
		if not token.startswith('@'): tokens.append(token); roles.append(role); continue
		r = rsps[pk(token[1:])]
		_, q = json_file(r['receipt'], ctx['roots'], ctx['json_bound'])
		need(role == 'responsefile' and q['manifest_sha256'] == manifest_sha and
			 hashed(token[1:], ctx)['sha256'] == q['raw_sha256'] and
			 hashlib.sha256(canonical(r['tokens'])).hexdigest() == q['ordered_tokens_sha256'] and
			 hashlib.sha256(canonical(r['token_roles'])).hexdigest() == q['ordered_token_roles_sha256'], 'actual')
		need(len(r['tokens']) == len(r['token_roles']) and not any(t.startswith('@') for t in r['tokens']), 'rsp')
		tokens.extend(r['tokens']); roles.extend(r['token_roles'])
	return tokens, roles
def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('input_manifest')
	args = parser.parse_args()
	need(os.name == 'nt', 'Window')
	cfg_path = absolute(args.input_manifest).resolve(strict=True)
	ir, cfg = json_file(str(cfg_path), [str(cfg_path.parent)], 65536)
	need(cfg['schema'] == 'xar.native.whole917.normalizer-input.v1', 'input ')
	ctx = dict(roots=cfg['read_roots'], json_bound=33554432, artifact_bound=cfg['artifact_max_bytes'],
	   sdk_root=cfg['sdk_source_root'], build_root=None, file_cache={},
			   project_header_roots=cfg['project_header_roots'],
			   external_dependency_roots=cfg['qualified_external_header_roots'])
	need(ctx['project_header_roots'] and ctx['external_dependency_roots'], 'explic')
	head = hd(cfg['source_head'])
	mr, m = raw_ref(cfg['manifest_reference'], ctx, True)
	rr, result = raw_ref(cfg['native_result_reference'], ctx, True)
	cr, cn = raw_ref(cfg['canonical_reference'], ctx, True)
	need(m['schema'] == 'xar.native.parallel.production/v1' and m['mode'] == 'rebuild917' and
		 m['retained_objects'] == [] and m['source_head'] == head and result['source_head'] == head and
		 result['manifest_sha256'] == mr['sha256'], 'whole ')
	ctx['build_root'] = m['output_root']
	names = dict(actual_owner_inventory='ACTUAL-OWNER-INVENTORY.json',
	actual_compile_commands='ACTUAL-COMPILE-COMMANDS.json',
	actual_object_lineage='ACTUAL-OBJECT-LINEAGE.json',
	actual_dependency_verification='ACTUAL-DEPENDENCY-VERIFICATION.json',
	actual_archive_members='ACTUAL-ARCHIVE-MEMBERS.json', actual_link_inputs='ACTUAL-LINK-INPUTS.json',
	actual_link_result='ACTUAL-LINK-RESULT.json', source_freeze='source_freeze')
	refs, packets = {}, {}
	for name, original in names.items():
		refs[name], packets[name] = raw_ref(result['actual_packets'][original], ctx, True)
		if name != 'source_freeze':
			need(packets[name]['source_head'] == head and packets[name]['evidence_kind'] == 'actual_production', 'packet')
	paths = [Path(v['path']) for v in refs.values()]
	need(all(not p.samefile(q) for i,p in enumerate(paths) for q in paths[i+1:]), 'distinct refs')
	f = packets['source_freeze']
	eq(f['source_root'], ctx['sdk_root'], 'qualif')
	need(f['source_head'] == head and f['tree_verified'] is True and f['status'] == 'FROZEN_SOURCE_INPUT' and
		 f['contract'] == 'Root_normalized_source_qualification/v1' and f['abi_inputs'] == m['abi_inputs'] == cn['abi_inputs'], 'freeze')
	evidence = f['actual_freeze_evidence']
	raw_ref(evidence, ctx)
	need(type(evidence['exit_code']) is int and evidence['exit_code'] == 0 and evidence['complete'] is True and
		 evidence['all5_verified'] is True and len(evidence['all5_evidence_refs']) == 5, 'actual')
	for path in evidence['all5_evidence_refs']: hashed(path, ctx)
	need(raw_ref(result['actual_packets']['native_canonical'], ctx)[0] == cr and
		 cn['schema'] == 'xar.native.production.actual/v1' and cn['source_head'] == head, 'actual')
	eq(cn['sdk_source_root'], ctx['sdk_root'], 'canoni')
	_, policy = json_file(m['environment_policy'], ctx['roots'], ctx['json_bound'])
	_, admitted = json_file(m['selected_owner_admission'], ctx['roots'], ctx['json_bound'])
	need(policy['manifest_sha256'] == admitted['manifest_sha256'] == mr['sha256'], 'admiss')
	ctx['seen_headers'] = set()
	ctx['accepted_versions'], ctx['changed_headers'] = policy['accepted_dependency_versions'], m['abi_inputs']
	need(ctx['accepted_versions'] and ctx['changed_headers'], 'explic')
	for h in ctx['changed_headers']:
		need(all(type(i) is int and 1 <= i <= 917 for i in h.get('known_required_owner_indices', [])), 'consum')
	jobs = m['compile_jobs']
	need(len(jobs) == 917 and len({pk(j['output']) for j in jobs}) == len({pk(j['dependencies_file']) for j in jobs}) == 917, 'fresh ')
	need([j['index'] for j in jobs] == list(range(1, 918)), 'declar')
	inventory = packets['actual_owner_inventory']['items']
	need([r['index'] for r in inventory] == [r['index'] for r in admitted['owners']] == list(range(1, 918)), 'invent')
	rows = [packets[n][k] for n, k in (('actual_compile_commands','rows'), ('actual_object_lineage', 'objects'),
									 ('actual_dependency_verification','rows'))]
	need(all([r['index'] for r in rs] == list(range(1, 918)) for rs in rows), 'actual')
	cs = admitted['candidate_compile_inputs']
	need(len(cs)==917 and all(type(v['index']) is int for v in cs), 'owners')
	mapped = {v['index']: v for v in cs}
	need(set(mapped) == set(range(1, 918)), 'mapping')
	verified, objects = [], {}
	for j, inv, independent, command, lineage, dep in zip(jobs, inventory, admitted['owners'], *rows):
		owner = inv['owner_tuple']
		need(owner == independent['owner_tuple'] == j['owner_tuple'] and owner['target'] == j['target'], 'owner ')
		c = mapped[j['index']]
		need(all(c[k] == j[k] for k in ('target','source','source_sha256','source_mapping_rule_ref','original_native88_source_ref')), 'mapped source')
		v = compile_one(j, owner, ctx); verified.append(v); objects[j['index']] = v['object']
		for row in (command, lineage, dep):
			need(row['owner_tuple'] == owner and row['target'] == j['target'] and row['source_head'] == head and
				 row['header_head'] == head and row['header_bytes'] == m['abi_inputs'], 'actual')
			eq(row['sdk_source_root'], ctx['sdk_root'], 'row SD')
			need(raw_ref(row['verified_ref'], ctx)[0] == v['verification'], 'verifi')
		check_stage(command, j, ctx)
		eq(lineage['source'], j['source'], 'lineag')
		need(lineage['source_sha256'] == v['source']['sha256'] and lineage['object_sha256'] == v['object']['sha256'], 'lineag')
		eq(lineage['object'], j['output'], 'lineag')
		for row in (lineage, dep): need(raw_ref(row['raw_dependencies_ref'], ctx)[0] == v['dependencies'], 'deps o')
		need(dep['include_sha256'] == json_file(str(absolute(j['job_root']) / 'stage.verified.json'),
			 ctx['roots'], ctx['json_bound'])[1]['dependencies']['include_sha256'], 'depend')
	need(all(pk(h['path']) in ctx['seen_headers'] for h in ctx['changed_headers']), 'header consumer')
	members, covered = [], []
	ars = packets['actual_archive_members']['archives']
	need(len(ars) == len(m['archives']), 'archiv')
	for j, record in zip(m['archives'], ars):
		need(record['job_id'] == j['job_id'], 'archiv')
		check_stage(record['actual_stage'], j, ctx)
		need([pk(v['path']) for v in record['ordered_inputs']] == [pk(objects[i]['path']) for i in j['member_indices']] and
			 [v['sha256'] for v in record['ordered_inputs']] == [objects[i]['sha256'] for i in j['member_indices']], 'archiv')
		listing = record['actual_members']; inspection = j['inspection_job']
		check_stage(listing['actual_inspection'], inspection, ctx)
		raw, data = read_file(listing['stdout_ref']['path'], ctx['roots'], ctx['json_bound'], True)
		need(raw['sha256'] == listing['stdout_ref']['sha256'], 'actual')
		names = [line.strip() for line in data.decode(inspection['stdout_encoding']).splitlines() if line.strip()]
		values = listing['ordered_members']
		need(names == [v['actual_member'] for v in values] and [v['index'] for v in values] == j['member_indices'], 'actual')
		need(len(set(Path(objects[i]['path']).name.casefold() for i in j['member_indices'])) == len(values), 'member')
		for v in values:
			i = ni(v['index'], 'member', 1)
			need(Path(v['actual_member']).name.casefold() == Path(objects[i]['path']).name.casefold(), 'member')
			eq(v['object'], objects[i]['path'], 'actual')
			members.append(i - 1); covered.append(i)
		need(raw_ref(record['output_ref'], ctx)[0] == hashed(j['output'], ctx), 'archiv')
	need(len(members) == len(set(members)) == 597, 'archiv')
	link, a, li = m['link'], packets['actual_link_result'], packets['actual_link_inputs']
	check_stage(a['actual_stage'], link, ctx); check_stage(li['actual_stage'], link, ctx)
	tokens, roles = link_tokens(link, ctx, mr['sha256'])
	need((tokens, roles) == (li['expanded_tokens'], li['token_roles']), 'actual')
	wanted = [hashed(p, ctx) for p in link['inputs']]
	need([pk(v['path']) for v in li['ordered_inputs']] == [pk(v['path']) for v in wanted] and
		 [v['sha256'] for v in li['ordered_inputs']] == [v['sha256'] for v in wanted], 'actual')
	covered += link['direct_object_indices']
	need(len(covered) == 917 and set(covered) == set(range(1, 918)), 'all ow')
	dll = hashed(link['output'], ctx); eq(a['dll_path'], dll['path'], 'actual')
	need(a['dll_sha256'] == dll['sha256'] and raw_ref(a['output_ref'], ctx)[0] == dll, 'DLL re')
	own = hashed(str(Path(__file__).resolve()), ctx)
	proof = dict(schema='xar.native.whole917.closure-proof.v1',
		status='ACTUAL_WHOLE917_COMPILE_DEPS_ARCHIVE_LINK_CLOSURE_VERIFIED',
		source_head=head, compiled_native_source_head=head, runtime_archive_source_head=head, sdk_source_head=head,
		sdk_source_root=str(absolute(ctx['sdk_root']).resolve()), mixed_source_pins=False,
		all_cpp_at_new_head=True, all_cpp_compiled_at_declared_source_head=True,
		candidate_header_compatibility_verified=True, all_actual_dependencies_verified=True,
		fresh_compiler_invocations_verified=917, reused_owner_count=0, archive_member_exact_order_verified=True,
		link_input_closure_verified=True, owner_index_base=0, actual_receipt_index_base=1,
		verified_owner_indices=list(range(917)), archive_member_owner_indices=members,
		family_qualifications={}, live_qualified=False, production_live_qualified=False,
		native_result_reference=rr, canonical_reference=cr, manifest_reference=mr,
		input_manifest=ir, normalizer_source=own, dll_identity=dll, **refs,
		normalizer_execution=dict(receipt_path=cfg['normalizer_execution_receipt_path'],
			expected_input_manifest_sha256=ir['sha256'], normalizer_source_sha256=own['sha256']),
		actual_owner_aggregate_sha256=agg(verified))
	output = absolute(cfg['proof_output'])
	need(within(output, [ctx['build_root']]) and not output.exists(), 'create')
	need(not absolute(cfg['normalizer_execution_receipt_path']).exists(), 'postex')
	encoded = canonical(proof)
	need(len(encoded) <= 65536, 'normal')
	with output.open('xb') as stream: stream.write(encoded)
	need(hashed(str(output), ctx)['sha256'] == hashlib.sha256(encoded).hexdigest(), 'proof ')
	return 0
if __name__ == '__main__':
	try:
		raise SystemExit(main())
	except (Unproved, KeyError, TypeError, ValueError, OSError) as error:
		print(str(error), file=sys.stderr)
		raise SystemExit(2)
