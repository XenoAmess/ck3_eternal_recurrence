"""Only the changed Native dependency boundary; no graph or Native qualification."""
import ast, importlib, json, re, sys, types
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import prepare_c19_canonical_controls_v1 as p


def before_label_fix():
    raw = Path(p.__file__).read_text(encoding='utf8')
    node = next(node for node in ast.parse(raw).body
        if isinstance(node, ast.FunctionDef) and node.name == '_qualified_label')
    previous = """def _qualified_label(transition):
 require(transition.source_fixture is False,'fixture transition cannot create an adopted graph')
 label=transition.target_native['native_build_label']
 require(isinstance(label,str) and label.startswith('Native30 ')
  and not any(x in label.upper() for x in ('UNQUALIFIED','SOURCE-ONLY','PLACEHOLDER')),
  'qualified Native30 full label required')
 return label"""
    raw = raw.replace(ast.get_source_segment(raw, node), previous, 1)
    raw = raw.replace('import ast,hashlib,importlib,re,sys', 'import ast,hashlib,importlib,sys', 1)
    raw = raw.replace(p.NATIVE_TRANSITION_SHA, '129e3e07afc397b27d20b85df6c671bf78d61756d1976cada0aa9bb31f97e466', 1)
    assert p.sha(raw.encode()) == '349b801e093454fcb5cf69c5ed06df162e0d88d5af3c45263a7518175d90f237'
    return raw


def dependency_boundary():
    raw = before_label_fix()
    old = raw.replace(p.NATIVE_TRANSITION_SHA, '01513090dff778d5aad566cf740214504a6d2eeae7b2ce1548acc2389c76bb91')
    old = old.replace(p.NATIVE_TOOLS['export_native30_immutable_sdk_views_v1.py'], '6fff517a40656a854d22703e20a40ebbb72857822ab2912fd9962b1217963417')
    old = old.replace(" 'native30_resume_fixture_chain_v1.py':'" + p.NATIVE_TOOLS['native30_resume_fixture_chain_v1.py'] + "',\n", '', 1)
    start = old.index(' for name in NATIVE_TOOLS:', old.index(' transition=module.read_native_transition_v1('))
    end = old.index(' label=_qualified_label(transition)', start)
    old = old[:start] + old[end:]
    assert p.sha(old.encode()) == '9ee87a910f755cefe3e94be6037b0f3a426dddbcef9c1fab384ab035ebb3f53e'
    for name, digest in p.NATIVE_TOOLS.items():
        assert p.sha((p.OWN/name).read_bytes()) == digest
    loader = importlib.import_module('export_native30_immutable_sdk_views_v1')
    args = dict(base_freeze_ref={}, base_native_ref={}, capacity_ref={}, machine_id=p.MACHINE)
    key = 'g2_saved_campaign.native30_resume_fixture_chain_v1'
    prior = sys.modules.get(key)
    calls = []
    try:
        for late in (False, True):
            def sentinel(**kwargs):
                assert kwargs == dict(args, source_fixture=False)
                calls.append(late)
                if late:
                    sys.modules[key] = types.SimpleNamespace(__file__=str(p.OWN/'foreign-helper.py'))
                return types.SimpleNamespace(source_fixture=True)
            with patch.object(loader, 'read_native_transition_v1', sentinel):
                try:
                    p.build_sources(native_transition_inputs=args)
                except ValueError as error:
                    expected = 'lazy dependency imported from a foreign package' if late else 'fixture transition'
                    assert expected in str(error)
                else:
                    raise AssertionError('unqualified or foreign dependency reached graph composition')
    finally:
        if prior is None:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = prior
    assert calls == [False, True]
    files = [Path(p.__file__), Path(__file__)]
    print(json.dumps(dict(machine_id=p.MACHINE, observed_at_utc=datetime.now(timezone.utc).isoformat(),
        files={path.name:[path.stat().st_size,p.sha(path.read_bytes())] for path in files},
        dependency_pins=p.NATIVE_TOOLS, original_producer_inverse_sha256=p.sha(old.encode()),
        new_cases_passed=2, four_refs_source_fixture_false=True, late_foreign_import_rejected=True,
        graph_regenerated=False, old_matrix_repeated=False, actual_Native06_qualified=False,
        D_Task_Game_Native_calls=0)))


def label_crosscase():
    previous = before_label_fix()
    contract_path = p.OWN/'native29_to30_export_contract_v1.py'
    contract = contract_path.read_bytes()
    assert p.sha(contract) == p.NATIVE_TRANSITION_SHA
    guards = [node.args[0] for node in ast.walk(ast.parse(contract))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == 'require' and len(node.args) == 2
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == 'non-placeholder actual Native30 label required']
    assert len(guards) == 1
    condition = compile(ast.Expression(guards[0]), str(contract_path), 'eval')
    def contract_accepts(label):
        return bool(eval(condition, {'re': re, 'label': label}))
    def transition(label, fixture=False):
        return types.SimpleNamespace(source_fixture=fixture, target_native={'native_build_label': label})
    label = 'native30-contract-crosscase'
    assert contract_accepts(label)
    assert p._qualified_label(transition(label)) == label
    for rejected in ('native30-placeholder', 'native30-fixture'):
        assert not contract_accepts(rejected)
        try:
            p._qualified_label(transition(rejected))
        except ValueError:
            pass
        else:
            raise AssertionError('contract placeholder/fixture label accepted')
    try:
        p._qualified_label(transition(label, fixture=True))
    except ValueError:
        pass
    else:
        raise AssertionError('fixture transition accepted')
    files = [Path(p.__file__), Path(__file__)]
    print(json.dumps(dict(machine_id=p.MACHINE, observed_at_utc=datetime.now(timezone.utc).isoformat(),
        files={path.name:[path.stat().st_size,p.sha(path.read_bytes())] for path in files},
        producer_inverse_sha256=p.sha(previous.encode()), contract_sha256=p.sha(contract),
        new_label_crosscase_passed=1, contract_expression_extracted=True,
        syntactic_positive_label=label, syntactic_label_is_actual_qualification=False,
        placeholder_and_fixture_rejected=True, old_5_57_12_and_2_cases_repeated=False,
        graph_regenerated=False, actual_Native06_qualified=False, D_Task_Game_Native_calls=0)))


def whole_public_graph():
    """Only JSON reads are simulated; all production callees run unchanged."""
    previous = before_label_fix()
    label = 'Native30 continuous hotspot tracking and idle realm overview'
    fixture_pins = {
        'test_native30_export_transition_v1.py': 'a540da9994244e2a1201bbc7168e04e8e3a191ab4f31630ba44bad0683a881f6',
        'test_native30_resume_fixture_chain_v1.py': '9f47c142ef469834a675b71310e1eba3993e19bb2c909995c0b8ca3f745c35cb'}
    for name, digest in fixture_pins.items():
        assert p.sha((p.OWN/name).read_bytes()) == digest
    for name, digest in p.NATIVE_TOOLS.items():
        assert p.sha((p.OWN/name).read_bytes()) == digest
    loader = importlib.import_module('export_native30_immutable_sdk_views_v1')
    fixtures = importlib.import_module('g2_saved_campaign.test_native30_export_transition_v1')
    resume = importlib.import_module('g2_saved_campaign.test_native30_resume_fixture_chain_v1')
    for module in (fixtures, resume):
        assert Path(module.__file__).resolve() == (p.OWN/Path(module.__file__).name).resolve()
    assert fixtures.contract.NATIVE30_BUILD_LABEL == label
    assert p.sha((p.OWN/'prepare_canonical_c17_outer_sources_v1.py').read_bytes()) == p.PINS['prepare_canonical_c17_outer_sources_v1.py']
    def values(failed=False):
        with patch.object(fixtures, 'MACHINE', p.MACHINE), patch.object(resume, 'MACHINE', p.MACHINE):
            return resume.resume_corpus(lambda rows: rows['result'].update(status='FAILED') if failed else None)
    def documents_for(corpus):
        base, native, evidence, card, _ = corpus
        documents = {doc.reference['path']: doc for doc in (base, native, card, *evidence.values())}
        arguments = dict(base_freeze_ref=base.reference, base_native_ref=native.reference,
            capacity_ref=card.reference, machine_id=p.MACHINE)
        return documents, arguments
    documents, arguments = documents_for(values())
    reads = []
    def memory_read(reference):
        doc = documents[reference['path']]
        assert reference == doc.reference
        reads.append(reference['path'])
        return doc
    # These are invented receipt bytes, not the actual FAILED06 documents.
    # The real loader, pure contract, and complete graph creator remain active.
    with patch.object(loader, '_read_document', memory_read), \
         patch.object(loader, 'validate_native_transition_v1', wraps=loader.validate_native_transition_v1) as validation, \
         patch.object(p.canonical, 'build_sources', wraps=p.canonical.build_sources) as creation:
        graph, report = p.build_sources(native_transition_inputs=arguments)
        assert validation.call_count == creation.call_count == 1
        assert validation.call_args.kwargs['source_fixture'] is False
        assert creation.call_args.kwargs == dict(enabled=True, native_build_label=label)
        assert report['native_transition_metadata']['target_native_build_label'] == label
        assert report['native_transition_metadata']['build_chain_provenance']['attempt02_status_preserved'] == 'FAILED'
        assert report['canonical_enabled'] is True and report['FULL_wall_and_rows'] is True
        assert report['control_probe_enabled'] is False and report['actual_runtime_admitted'] is False
        p.assert_true_graph(graph)
        factory = ast.parse(graph['root_p37c19_cold_resume.py'])
        native_label_guards = [node for node in ast.walk(factory) if isinstance(node, ast.Compare)
            and isinstance(node.left, ast.Subscript) and isinstance(node.left.slice, ast.Constant)
            and node.left.slice.value == 'native_build_label']
        assert len(native_label_guards) == 1
        assert isinstance(native_label_guards[0].comparators[0], ast.Constant)
        assert native_label_guards[0].comparators[0].value == label
        assert '@_full_rows_v1(enabled=True)' in graph['root_p37c19_sdk_queue.py'].decode()
        assert 'admission_getter=lambda queue: None' in graph['root_p37c19_sdk_queue.py'].decode()
        assert dict(report['entry_source_pins_after_all_edits']) == {
            str(p.T/name):p.sha(raw) for name, raw in graph.items()}
        documents, arguments = documents_for(values(failed=True))
        try:
            p.build_sources(native_transition_inputs=arguments)
        except ValueError:
            pass
        else:
            raise AssertionError('FAILED fixture06 reached graph creation')
        assert validation.call_count == 2 and creation.call_count == 1
    files = [Path(p.__file__), Path(__file__)]
    print(json.dumps(dict(machine_id=p.MACHINE, observed_at_utc=datetime.now(timezone.utc).isoformat(),
        files={path.name:[path.stat().st_size,p.sha(path.read_bytes())] for path in files},
        producer_inverse_sha256=p.sha(previous.encode()), fixture_source_pins=fixture_pins,
        dependency_pins=p.NATIVE_TOOLS, root_metadata_label=label, new_whole_public_crosscase_passed=1,
        graph={name:[len(raw),p.sha(raw)] for name,raw in graph.items()},
        graph_bytes=sum(map(len,graph.values())), graph_materialized=False,
        real_loader_contract_and_enabled_creator=True, JSON_reads_simulated=len(reads),
        source_fixture_false_forwarded=True, synthetic_FAILED06_graph_rejected=True,
        synthetic_receipts_only=True, actual_Native_qualification=False,
        old_5_57_12_2_and_label_leaf_cases_repeated=False, D_Task_Game_Native_calls=0)))


if __name__ == '__main__':
    whole_public_graph()
