"""Actual public CLI run without ambient SDK paths; no game or host executes."""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from ck3_mod_acceptance import _case_sdk_imports_v1


def public_timer_verify_fixture(root: Path) -> subprocess.CompletedProcess[str]:
    """Author seven Save inputs, then verify them through an SDK-free public CLI.

    The existing TimerPort supplies authored I/O and startup binding. The child
    runs the actual Selection, timer verifier and native projector without mocks.
    No host/game starts and no real scene evidence is consumed or rewritten.
    """
    from unittest.mock import patch
    from test_ck3_mod_acceptance import SharedEntryTests
    import ck3_mod_acceptance as entry

    prior = list(sys.path)
    sys.path.insert(0, str(ROOT / "mod_living_artifacts/tools"))
    import mod_living_artifacts.tools.test_suppression_timer_acceptance_adapter as authored

    fixture = SharedEntryTests(methodName="test_run_delegates_existing_launcher_without_executing_host")
    fixture.setUp()
    try:
        context = authored.context_fixture(root)
        source = Path(str(context["shared_source_root"]))
        bridge = source / "xar_autoplayer/bridge"
        bridge.mkdir(parents=True)
        (source / "xar_autoplayer/__init__.py").write_text("", encoding="utf-8")
        (bridge / "__init__.py").write_text("", encoding="utf-8")
        contract = "campaign_interaction_boundary_v1.py"
        (bridge / contract).write_bytes((ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge" / contract).read_bytes())
        fixture.runtime["repo_root"] = str(ROOT)
        fixture.runtime["game_dir"] = str(context["game_dir"])
        fixture.runtime["paths"]["source_root"] = str(source)
        fixture.manifest["machine_id"] = "unit-machine"
        fixture.manifest["game"] = context["shared_game"]
        fixture.manifest["entry_environment"] = {"PYTHONPATH_parts": [{"path_key": "source_root"}]}
        fixture.write(fixture.manifest_path, fixture.manifest)
        fixture.runtime["manifest"] = entry.pin(fixture.manifest_path)
        fixture.write(fixture.runtime_path, fixture.runtime)
        case = json.loads((ROOT / "mod_living_artifacts/tools/suppression_timer.registry.json").read_text(encoding="utf-8"))
        case["startup"]["state_dir"] = context["state_dir"]
        case["initial_plan"] = str(fixture.files["initial"])
        fixture.products["product_inventory"] = str(fixture.files["inventory"])
        fixture.products["products"] = {"living-artifacts": {"cases": [case]}}
        fixture.write(fixture.products_path, fixture.products)
        run = root / "unit-run"
        (run / "case-output").mkdir(parents=True)
        frozen = run / "frozen-argv.json"
        fixture.write(frozen, {})
        context_path = fixture.root / "timer-context.json"
        allocated = {"schema": entry.CONTEXT_SCHEMA, "run_id": run.name, "run_dir": str(run),
                     "reviewer": "unit-root", "case_inputs": context["case_inputs"], "frozen_argv": entry.pin(frozen)}
        fixture.write(context_path, allocated)
        selected = entry.Selection(fixture.runtime_path, fixture.products_path, "living-artifacts", "suppression_timer", context_path)
        fixture.write(frozen, {"run_id": run.name, "argv": selected.argv,
                               "runtime_environment": selected.runtime_environment, "reviewer": "unit-root"})
        allocated["frozen_argv"] = entry.pin(frozen)
        fixture.write(context_path, allocated)
        actual_context = selected.adapter_context()
        port = authored.TimerPort(actual_context)
        binding = authored.StartupActorBinding(91, 124, "9", 53144328, 12801, "a" * 64, "b" * 64)
        with patch.object(authored.StartupActorBinding, "parse", return_value=binding):
            result = authored.timer.run_case(actual_context, port)
        if result["status"] != "PASS" or (port.saves, port.day) != (7, 198):
            raise AssertionError("Original authored timer producer must complete its seven Save fixture: " + str(result.get("error")))
        result_path = port.output / authored.timer.RESULT_NAME
        original = result_path.read_bytes()
        fixture.write(port.output / "normal-close-result.json", {"normal_close_qualified": True, "authored_no_game": True})
        arguments = ["verify", "--runtime", str(fixture.runtime_path), "--products", str(fixture.products_path),
                     "--product", "living-artifacts", "--case", "suppression_timer", "--run-context", str(context_path)]
        script = """import copy,importlib.util,json,pathlib,sys
if importlib.util.find_spec('xar_autoplayer') is not None:
    raise RuntimeError('Independent verify received an ambient SDK')
sys.path.insert(0, sys.argv[1])
import ck3_mod_acceptance as entry
status = entry.main(sys.argv[3:])
if status:
    raise SystemExit(status)
from xar_autoplayer.bridge import campaign_interaction_boundary_v1 as boundary
source = pathlib.Path(sys.argv[2])
if pathlib.Path(boundary.__file__).resolve() != (source/'xar_autoplayer/bridge/campaign_interaction_boundary_v1.py').resolve():
    raise RuntimeError('Verify imported a foreign pending-interaction contract')
from ck3_mod_acceptance_native_day import project_native_day
allocated = json.loads(pathlib.Path(sys.argv[-1]).read_text(encoding='utf-8'))
output = pathlib.Path(allocated['run_dir'])/'case-output'
projection = json.loads(next(output.glob('case-natural-day-*.native-day-projection.json')).read_text(encoding='utf-8'))
raw = json.loads(pathlib.Path(projection['raw_public_row_path']).read_text(encoding='utf-8'))['rows'][0]
pending = {'instance_id':33554443,'sender_character_id':31408,'auto_accept_notification':False,'source':'native'}
raw['after_snapshot']['pending_character_interaction'] = pending
raw['result']['pending_character_interaction'] = pending
before = projection['row']['result']['before']
projected = project_native_day(raw, before, allow_event_boundary=True)
if projected['result']['event_boundary']['pending_character_interaction'] != pending:
    raise RuntimeError('Real readonly pending boundary was lost')
wrong = copy.deepcopy(raw)
wrong['after_snapshot']['pending_character_interaction']['instance_id'] = True
try:
    project_native_day(wrong, before, allow_event_boundary=True)
except ValueError:
    pass
else:
    raise RuntimeError('Boolean pending identity must remain refused')
"""
        unrelated = root / "unrelated-cwd"
        unrelated.mkdir()
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        completed = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", "-c", script,
                                    str(ROOT / "tools"), str(source), *arguments], cwd=unrelated, env=environment,
                                   capture_output=True, text=True, encoding="utf-8", timeout=120, check=False)
        if result_path.read_bytes() != original:
            raise AssertionError("Public read-only verify rewrote its original timer result")
        return completed
    finally:
        fixture.doCleanups()
        sys.path[:] = prior


class CaseImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prior_path = list(sys.path)
        self.cached = {name: sys.modules.pop(name) for name in tuple(sys.modules)
                       if name == "xar_autoplayer" or name.startswith("xar_autoplayer.")}
        self.temporary = tempfile.TemporaryDirectory(prefix="case-import-")
        self.source = Path(self.temporary.name) / "sdk"
        (self.source / "xar_autoplayer").mkdir(parents=True)
        (self.source / "xar_autoplayer/__init__.py").write_text("FROZEN = True\n", encoding="utf-8")

    def tearDown(self) -> None:
        for name in tuple(sys.modules):
            if name == "xar_autoplayer" or name.startswith("xar_autoplayer."):
                del sys.modules[name]
        sys.modules.update(self.cached)
        sys.path[:] = self.prior_path
        self.temporary.cleanup()

    def test_selected_sdk_is_bound_and_path_restored_on_exception(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "case failure"):
            with _case_sdk_imports_v1(self.source, {"PYTHONPATH": str(self.source)}):
                module = importlib.import_module("xar_autoplayer")
                self.assertEqual(Path(str(module.__file__)).parent, self.source / "xar_autoplayer")
                raise RuntimeError("case failure")
        self.assertEqual(sys.path, self.prior_path)

    def test_cached_foreign_sdk_is_rejected_before_case(self) -> None:
        foreign = ModuleType("xar_autoplayer")
        foreign.__file__ = str(Path(self.temporary.name) / "foreign/xar_autoplayer/__init__.py")
        sys.modules["xar_autoplayer"] = foreign
        with self.assertRaisesRegex(ValueError, "escaped selected runtime"):
            with _case_sdk_imports_v1(self.source, {"PYTHONPATH": str(self.source)}):
                self.fail("foreign SDK must never reach the case")
        self.assertEqual(sys.path, self.prior_path)

    def test_wrong_missing_and_empty_environment_paths_are_rejected(self) -> None:
        for environment in ({"PYTHONPATH": None}, {"PYTHONPATH": True}, {"PYTHONPATH": ""},
                            {"PYTHONPATH": str(self.source) + os.pathsep},
                            {"PYTHONPATH": str(self.source.parent)}):
            with self.subTest(environment=environment), self.assertRaises(ValueError):
                with _case_sdk_imports_v1(self.source, environment):
                    self.fail("invalid frozen SDK declaration")

    def test_existing_sdk_free_environment_does_not_claim_a_binding(self) -> None:
        with _case_sdk_imports_v1(self.source.parent, {}) as selected:
            self.assertIsNone(selected)
        self.assertEqual(sys.path, self.prior_path)

    def test_public_cli_run_imports_original_lazy_consumers_without_pythonpath(self) -> None:
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        completed = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__).resolve()),
                                    "--cli-fixture"], cwd=self.temporary.name, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   encoding="utf-8", timeout=60, check=False)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        value = json.loads(completed.stdout)
        self.assertTrue(value["case_result"]["original_pending_contract_imported"])
        self.assertTrue(value["case_result"]["original_native_day_imported"])
        self.assertEqual(value["launcher_exit_code"], 0)
        self.assertFalse(value["case_result"]["game_started"])

    def test_public_allocate_prelaunch_reducer_without_ambient_sdk(self) -> None:
        environment = dict(os.environ)
        environment.pop('PYTHONPATH', None)
        completed = subprocess.run(
            [sys.executable, '-I', '-B', '-X', 'utf8', str(Path(__file__).resolve()),
             '--allocate-prelaunch-import-fixture'], cwd=self.temporary.name,
            env=environment, capture_output=True, text=True, encoding='utf-8',
            timeout=60, check=False)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        value = json.loads(completed.stdout)
        for key in ('actual_public_dispatch', 'actual_observed_prelaunch_reducer',
                    'actual_running_input_contract', 'stopped_before_machine_writer',
                    'counter_unchanged'):
            self.assertIs(value[key], True)
        self.assertIs(value['game_started'], False)

    def test_public_allocate_freezes_all_three_guard_filepins_before_claim(self) -> None:
        environment = dict(os.environ)
        environment.pop('PYTHONPATH', None)
        completed = subprocess.run(
            [sys.executable, '-I', '-B', '-X', 'utf8', str(Path(__file__).resolve()),
             '--allocate-prelaunch-filepins-fixture'], cwd=self.temporary.name,
            env=environment, capture_output=True, text=True, encoding='utf-8',
            timeout=60, check=False)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        value = json.loads(completed.stdout)
        self.assertEqual(value['additional_phase_guard_filepins_frozen'], 10)
        for key in ('actual_public_dispatch', 'actual_observed_prelaunch_reducer',
                    'actual_running_input_contract', 'stopped_before_machine_writer',
                    'counter_unchanged'):
            self.assertIs(value[key], True)
        self.assertIs(value['game_started'], False)

    def test_real_verify_and_cli_validate_json_result_and_preserve_encoded_sequences(self) -> None:
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        for kind in ("top-level", "key", "value", "valid"):
            with self.subTest(kind=kind):
                completed = subprocess.run(
                    [sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__).resolve()),
                     "--verify-json-fixture", kind], cwd=self.temporary.name, env=env,
                    capture_output=True, text=True, encoding="utf-8", timeout=60, check=False)
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                value = json.loads(completed.stdout)
                self.assertEqual(value["cli_returncode"], 2)
                self.assertFalse(value["game_started"])
                if kind == "valid":
                    self.assertEqual(value["result"]["authored_payload"],
                                     {"sequence": [1, "two", None, {"enabled": True}],
                                      "identity_decimal": "18446744073709551615", "empty": []})
                    self.assertFalse(value["result"]["case_acceptance_pass"])
                    self.assertTrue(value["direct_cli_json_equal"])
                else:
                    self.assertTrue(value["direct_rejected"])
                    self.assertEqual(value["result"]["status"], "BLOCKED")


def verify_json_fixture(kind: str) -> int:
    """Exercise actual Selection.verify and CLI; author only the adapter boundary."""
    if kind not in ("top-level", "key", "value", "valid"):
        raise ValueError("Unknown authored JSON boundary case")
    sys.path.insert(0, str(ROOT))
    from contextlib import redirect_stdout
    from io import StringIO
    from test_ck3_mod_acceptance import SharedEntryTests
    from ck3_mod_acceptance_background_types import json_object
    import ck3_mod_acceptance as entry

    fixture = SharedEntryTests(methodName="test_run_delegates_existing_launcher_without_executing_host")
    fixture.setUp()
    try:
        source = fixture.locations["source"]
        bridge = source / "xar_autoplayer/bridge"
        bridge.mkdir(parents=True)
        (source / "xar_autoplayer/__init__.py").write_text("", encoding="utf-8")
        (bridge / "__init__.py").write_text("", encoding="utf-8")
        contract_name = "campaign_interaction_boundary_v1.py"
        (bridge / contract_name).write_bytes((ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge" / contract_name).read_bytes())
        fixture.manifest["entry_environment"] = {"PYTHONPATH_parts": [{"path_key": "source_root"}]}
        fixture.write(fixture.manifest_path, fixture.manifest)
        fixture.runtime["manifest"] = entry.pin(fixture.manifest_path)
        fixture.write(fixture.runtime_path, fixture.runtime)
        adapter = fixture.root / "cases/json_adapter.py"
        adapter.parent.mkdir()
        adapter.write_text('''from pathlib import Path
def verify_case(context: dict[str, object]) -> object:
    from ck3_mod_acceptance_native_day import pending_instance
    assert pending_instance(None) is None
    kind = ''' + repr(kind) + '''
    if kind == "top-level": return []
    if kind == "key": return {7: "invalid JSON key"}
    if kind == "value": return {"value": Path("not-a-JSON-value")}
    from mod_living_artifacts.tools.acceptance_contract import object_value
    return object_value({"status": "AUTHORED_JSON_BOUNDARY_ONLY", "case_contract_qualified": False,
        "gui_contract_qualified": False, "business_pass": False, "product_release_pass": False,
        "authored_payload": {"sequence": (1, "two", None, {"enabled": True}),
            "identity_decimal": "18446744073709551615", "empty": []}})
''', encoding="utf-8")
        contract = adapter.with_suffix(".json")
        fixture.write(contract, {})
        fixture.products["product_inventory"] = str(fixture.files["inventory"])
        fixture.products["products"]["xqol"]["cases"][0]["adapter"] = {"path": str(adapter), "config": str(contract)}
        fixture.write(fixture.products_path, fixture.products)
        context_path, _, _, context = fixture.context()
        context["reviewer"] = "authored-json-boundary-reviewer"
        fixture.write(context_path, context)
        selected = entry.Selection(fixture.runtime_path, fixture.products_path, "xqol", "core", context_path)
        direct: object = None
        rejected = False
        try:
            direct = selected.verify()
        except ValueError:
            if kind == "valid":
                raise
            rejected = True
        if kind != "valid" and not rejected:
            raise AssertionError("Real Selection.verify accepted an invalid adapter JSON result")
        captured = StringIO()
        with redirect_stdout(captured):
            status = entry.main(["verify", "--runtime", str(fixture.runtime_path), "--products", str(fixture.products_path),
                                 "--product", "xqol", "--case", "core", "--run-context", str(context_path)])
        result = json_object(json.loads(captured.getvalue()))
        if status != 2:
            raise AssertionError("Authored incomplete or invalid case must retain the real public CLI exit2")
        same = kind == "valid" and json_object(json.loads(json.dumps(direct))) == result
        if kind == "valid" and not same:
            raise AssertionError("Real verifier and CLI changed the producer's encoded JSON content")
        print(json.dumps({"cli_returncode": status, "result": result, "direct_rejected": rejected,
                          "direct_cli_json_equal": same, "game_started": False}))
        return 0
    finally:
        fixture.doCleanups()


def allocate_prelaunch_import_fixture(*, phase_guard_files: bool = False,
                                     prebuilt_case_inputs: Path | None = None) -> int:
    """Actual dispatch/allocation/reducer; synthetic R21-shaped no-game inputs.

    Only OS/bus/preflight observations are fixtures. The actual selected SDK,
    complete observed-prelaunch reducer and running-input guard execute. Stop
    at the first post-reducer git check, or after assembling all three guards'
    frozen inputs at the claim sentinel, before intent/SCREEN/ID/ledger/keeper.
    """
    import argparse
    from contextlib import ExitStack
    from unittest.mock import patch
    from ck3_mod_acceptance_background_types import FilePin, json_object, object_field, text_field
    from test_ck3_mod_acceptance_unrun_stages import RootAllocatorTripletTests
    import ck3_mod_acceptance as entry
    import ck3_mod_acceptance_allocate as allocator
    import ck3_mod_acceptance_unrun as unrun
    import ck3_live_run_id as ids
    if importlib.util.find_spec('xar_autoplayer') is not None:
        raise RuntimeError('Allocate fixture received an ambient SDK')
    fixture = RootAllocatorTripletTests()
    fixture.setUp()
    try:
        external_pins: list[FilePin] = []
        if prebuilt_case_inputs is not None:
            from test_ck3_mod_acceptance import SharedEntryTests
            from ck3_mod_acceptance_prepare import prebuilt_fixture_source_pins
            public = SharedEntryTests()
            public.setUp()
            fixture.addCleanup(public.doCleanups)
            produced = json_object(json.loads(prebuilt_case_inputs.read_bytes()))
            case_inputs = object_field(produced, 'case_inputs')
            preparation = object_field(produced, 'preparation')
            startup = object_field(preparation, 'startup')
            profile = object_field(preparation, 'profile_preparation')
            profile_receipt = object_field(profile, 'preparation')
            entry.check_pin(Path(text_field(profile_receipt, 'path')), dict(profile_receipt))
            if startup.get('mode') != 'saved_campaign':
                raise AssertionError('The real cold fixture must keep its produced saved startup')
            case = public.products['products']['xqol']['cases'][0]
            case.update(id='cold_reload', startup=startup)
            public.products['products'] = {'religious-ritual-fusion': {'cases': [case]}}
            public.write(public.products_path, public.products)
            prepared_path = public.root / 'prebuilt-prepared.json'
            public.write(prepared_path, {'schema': 'ck3-mod-acceptance-prepared-case-v1',
                'product': 'religious-ritual-fusion', 'case': 'cold_reload',
                'runtime_manifest': entry.pin(public.manifest_path.resolve()), 'startup': startup,
                'initial_plan': preparation['initial_plan'], 'preparation': preparation,
                'case_inputs': case_inputs})
            actual = entry.Selection(public.runtime_path, public.products_path,
                'religious-ritual-fusion', 'cold_reload', prepared_path=prepared_path)
            result = actual.preflight()
            if result['blockers']:
                raise AssertionError('Actual Selection/preflight rejected snapshot inputs: ' + repr(result['blockers']))
            if actual.state_dir != Path(text_field(startup, 'state_dir')).resolve():
                raise AssertionError('Actual Selection lost the materialized cold profile')
            external_pins = prebuilt_fixture_source_pins(case_inputs)
            if any(reference not in result['checked_inputs'] for reference in external_pins):
                raise AssertionError('Actual Selection omitted snapshot input pins')
        bundle, live, keeper, _ = fixture.prelaunch_fixture(observed_root=True, phase_guards=phase_guard_files)
        # Author digest-domain frozen inputs for this fixture, never live files.
        freeze = json_object(json.loads((live / 'frozen-argv.json').read_bytes()))
        files = object_field(freeze, 'files')
        freeze['files'] = {name: {key: object_field(files, name)[key]
                                 for key in ('bytes', 'sha256')} for name in files}
        (live / 'frozen-argv.json').write_text(json.dumps(freeze), encoding='utf-8')
        bundle['frozen'] = fixture.reference(live / 'frozen-argv.json')
        ready = json_object(json.loads((live / 'ready-context.json').read_bytes()))
        ready['frozen_argv'] = json_object(bundle['frozen'])
        for name, key in (('ready-context.json', 'ready'), ('allocated-context.json', 'allocated_context')):
            (live / name).write_text(json.dumps(ready), encoding='utf-8')
            bundle[key] = fixture.reference(live / name)
        armed_path = Path(text_field(json_object(bundle['prelaunch_guard_armed']), 'path'))
        armed = json_object(json.loads(armed_path.read_bytes()))
        armed['ready_context'] = json_object(bundle['ready'])
        armed_path.write_text(json.dumps(armed), encoding='utf-8')
        bundle['prelaunch_guard_armed'] = fixture.reference(armed_path)
        expected_phase_pins: list[FilePin] = []
        if phase_guard_files:
            output = armed_path.parent
            for label in ('DEADLINE-GUARD-1', 'DEADLINE-GUARD-2'):
                path = output / (label + '.ARMED.actual.json')
                row = json_object(json.loads(path.read_bytes()))
                row['ready_context'] = json_object(bundle['ready'])
                path.write_text(json.dumps(row), encoding='utf-8')
            phase_rows = unrun._phase_guard_evidence(output)
            bundle['prelaunch_phase_guards'] = phase_rows
            expected_phase_pins = [row[key] for row in phase_rows
                for key in ('intent', 'started', 'armed', 'cancel', 'original_wait')]
        close = fixture.root / 'observed-prelaunch-close.json'
        close.write_text(json.dumps(bundle), encoding='utf-8')
        release_path = Path(text_field(json_object(bundle['admin_done']), 'path'))
        release = json_object(json.loads(release_path.read_bytes()))
        packet = {'tasks': [{**object_field(release, 'task'), 'age_seconds': 0, 'stale': False}]}
        id_root = Path(text_field(object_field(freeze, 'identity_allocation'), 'state_root')).resolve()
        counter = Path(text_field(json_object(bundle['counter']), 'path'))
        counter_before = counter.read_bytes()
        bus = fixture.root / 'next-bus/bin/codex_task_bus.py'
        bus.parent.mkdir(parents=True)
        bus.write_bytes(b'# authored bus; never executed\n')
        selected = object.__new__(entry.Selection)
        selected.prepared_path = fixture.root / 'next-prepared.json'
        selected.context = {}
        selected.product = {'external_mod': False}
        selected.product_key = 'living-artifacts'
        selected.state_dir = fixture.root / 'next-state'
        selected.runtime_path = fixture.root / 'next-runtime.json'
        selected.locations = {'repo_root': ROOT}
        selected.manifest = {'source_root': {'path_key': 'source_root'}}
        selected.paths = {'source_root': ROOT}
        selected.runtime_environment = {'PYTHONPATH': str(ROOT / 'ck3_autonomous_player/src')}
        selected.runtime = {'allocation': {'lease_repo': str(fixture.repo),
            'task_prefix': 'fixture-next-', 'screen_keeper': entry.pin(Path(__file__)),
            'task_bus': entry.pin(bus)},
            'reviewed_launcher': entry.pin(ROOT / 'tools/ck3_mod_acceptance_launcher.py')}
        args = argparse.Namespace(mode='allocate', runtime=None, products=None,
            product=None, case=None, run_context=None, prepared_case=None, attempt='a02',
            keeper_output=fixture.root / 'never-created-keeper', previous_live=live,
            previous_keeper=keeper, previous_failure_close=close,
            previous_release=release_path, first_machine_bootstrap=None, latest_screen_release=None)
        if phase_guard_files:
            selected.prepared_path.write_text('{}', encoding='utf-8')
            selected.runtime_path.write_text('{}', encoding='utf-8')
            selected.products_path = fixture.root / 'prelaunch-products.json'
            selected.prepared = {'preparation': {}}
            selected.case = {'startup': {'mode': 'saved'}}
            selected.adapter_path = None
            selected.runtime['control_queue'] = entry.pin(ROOT / 'tools/ck3_mod_acceptance_queue.py')
            (selected.state_dir / 'profile').mkdir(parents=True)
            for relative in ('tools/codex_task_bus.py', 'promo/ck3_native_war_ai/integration/screen_bus_lease.py'):
                target = fixture.repo / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())

        class BeforeMachineWriter(RuntimeError):
            pass

        def before_writer(argv: list[str], **kwargs: object) -> object:
            if argv != ['git', 'status', '--porcelain']:
                raise AssertionError('Unexpected subprocess before the writer boundary')
            if phase_guard_files:
                return subprocess.CompletedProcess(argv, 0, stdout=b'', stderr=b'')
            raise BeforeMachineWriter('No admission, SCREEN, ID, ledger or keeper')

        claim_reached = False
        def before_claim(*claim_args: object) -> object:
            nonlocal claim_reached
            claim_reached = True
            import inspect
            frame = inspect.currentframe()
            caller = frame.f_back if frame is not None else None
            if caller is None or caller.f_code.co_name != '_allocate_and_keep_impl':
                raise AssertionError('Claim sentinel must observe the real allocator caller')
            actual_files = caller.f_locals.get('files')
            if not isinstance(actual_files, dict) or len(expected_phase_pins) != 10:
                raise AssertionError('Actual allocator frozen file table or ten guard Pins missing')
            for value in expected_phase_pins:
                reference = json_object(value)
                if actual_files.get(Path(text_field(reference, 'path')).resolve()) != reference:
                    raise AssertionError('Actual allocator omitted or changed an additional guard Pin')
            for reference in external_pins:
                if actual_files.get(Path(reference['path']).resolve()) != reference:
                    raise AssertionError('Actual allocator omitted a snapshot external input Pin')
            raise BeforeMachineWriter('All ten guard Pins frozen; no machine writer entered')

        prior_path = list(sys.path)
        with ExitStack() as stack:
            stack.enter_context(patch.object(entry, 'Selection', return_value=selected))
            stack.enter_context(patch.object(type(selected), 'preflight', return_value={'blockers': [], 'checked_inputs': external_pins}))
            observers: dict[str, object] = {'actual_machine_binding': {'machine_id': fixture.machine,
                    'state_root': str(id_root), 'admission_root': str(fixture.root / 'never-created-admission')},
                'shared_bus_history': ([], True), 'current_screen_absent': packet,
                'runtime_process_inventory': {'blockers': []}}
            for name, value in observers.items():
                stack.enter_context(patch.object(allocator, name, return_value=value))
            stack.enter_context(patch.object(ids, 'current_machine_id', return_value=fixture.machine))
            stack.enter_context(patch.object(ids, 'default_state_root', return_value=id_root))
            reducer = stack.enter_context(patch.object(unrun, 'validate_allocated_unrun', wraps=unrun.validate_allocated_unrun))
            guard = stack.enter_context(patch.object(unrun, '_recovery_input_validation', wraps=unrun._recovery_input_validation))
            stack.enter_context(patch.object(subprocess, 'run', side_effect=before_writer))
            stack.enter_context(patch.object(allocator, 'claim_machine_admission', new=before_claim))
            try:
                entry.native_dispatch(args)
            except BeforeMachineWriter:
                pass
            else:
                raise AssertionError('Actual allocate did not stop before its first writer')
            if reducer.call_count != 1 or guard.call_count != 1:
                raise AssertionError('Actual observed-prelaunch reducer/input guard did not execute')
            if claim_reached is not phase_guard_files:
                raise AssertionError('Unexpected original writer-boundary call count')
        if sys.path != prior_path:
            raise AssertionError('Selected SDK context did not restore the original search path')
        contract = sys.modules.get('xar_autoplayer.bridge.runtime_input_contract_v1')
        expected = ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/runtime_input_contract_v1.py'
        if contract is None or Path(str(contract.__file__)).resolve() != expected.resolve():
            raise AssertionError('Reducer imported another running-input contract')
        if (counter.read_bytes() != counter_before or args.keeper_output.exists()
                or (fixture.root / 'never-created-admission').exists()):
            raise AssertionError('Read-only regression consumed an allocator-owned input')
        print(json.dumps({'actual_public_dispatch': True, 'actual_observed_prelaunch_reducer': True,
            'actual_running_input_contract': True, 'stopped_before_machine_writer': True,
            'counter_unchanged': True, 'game_started': False,
            'additional_phase_guard_filepins_frozen': len(expected_phase_pins) if phase_guard_files else 0,
            'prebuilt_external_filepins_frozen': len(external_pins)}))
        return 0
    finally:
        fixture.doCleanups()


def cli_fixture() -> int:
    """Test-only owned launcher/client; execute real Selection/preflight/run/CLI."""
    from unittest.mock import patch
    sys.path.insert(0, str(ROOT / "tools"))
    sys.path.insert(0, str(ROOT))
    if importlib.util.find_spec("xar_autoplayer") is not None:
        raise RuntimeError("CLI fixture accidentally received an ambient SDK")
    from test_ck3_mod_acceptance import SharedEntryTests
    import ck3_mod_acceptance as entry
    import ck3_mod_acceptance_client as client_module
    fixture = SharedEntryTests(methodName="test_run_delegates_existing_launcher_without_executing_host")
    fixture.setUp()
    try:
        source = fixture.locations["source"]
        bridge = source / "xar_autoplayer/bridge"
        bridge.mkdir(parents=True)
        (source / "xar_autoplayer/__init__.py").write_text("", encoding="utf-8")
        (bridge / "__init__.py").write_text("", encoding="utf-8")
        for name in ("campaign_interaction_boundary_v1.py",):
            (bridge / name).write_bytes((ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge" / name).read_bytes())
        fixture.manifest["entry_environment"] = {"PYTHONPATH_parts": [{"path_key": "source_root"}]}
        fixture.write(fixture.manifest_path, fixture.manifest)
        fixture.runtime["manifest"] = entry.pin(fixture.manifest_path)
        fixture.write(fixture.runtime_path, fixture.runtime)
        adapter = fixture.root / "cases/lazy_adapter.py"
        adapter.parent.mkdir()
        adapter.write_text('''from pathlib import Path
def prepare_case(context: dict[str, object]) -> dict[str, object]:
    return {}
def verify_case(context: dict[str, object]) -> dict[str, object]:
    return {}
def run_case(context: dict[str, object], client: object) -> dict[str, object]:
    from ck3_mod_acceptance_native_day import pending_instance
    assert pending_instance(None) is None
    pending = {'instance_id':33554443,'sender_character_id':31408,'auto_accept_notification':False,'source':'native'}
    assert pending_instance(pending) == 33554443
    try:
        pending_instance({**pending, 'instance_id': True})
    except ValueError:
        pass
    else:
        raise AssertionError('Original lazy consumer accepted a Boolean pending identity')
    from xar_autoplayer.bridge import campaign_interaction_boundary_v1 as boundary
    assert Path(boundary.__file__).resolve().is_relative_to(Path(str(context['shared_source_root'])).resolve())
    return {'original_pending_contract_imported': True, 'original_native_day_imported': True, 'game_started': False}
''', encoding="utf-8")
        contract = adapter.with_suffix(".json")
        fixture.write(contract, {})
        fixture.products["product_inventory"] = str(fixture.files["inventory"])
        fixture.products["products"]["xqol"]["cases"][0]["adapter"] = {"path": str(adapter), "config": str(contract)}
        fixture.write(fixture.products_path, fixture.products)
        context, _, _, value = fixture.context()
        value["reviewer"] = "synthetic-cli-reviewer"
        fixture.write(context, value)

        class OwnedClient:
            def __init__(self, selection: object) -> None:
                self.output = fixture.root / "case-output"
                self.output.mkdir()
                self._handle: object | None = object()

            def wait_hold(self) -> None:
                return None

            def retain_held_process(self, wait: bool = False) -> bool:
                return False

            def normal_close(self, reason: str) -> dict[str, object]:
                return {"normal_close_qualified": True, "synthetic_owned_client": True, "game_started": False}

            def close_handle(self) -> None:
                return None

        with patch.object(client_module, "CaseClient", OwnedClient):
            code = entry.main(["run", "--runtime", str(fixture.runtime_path), "--products", str(fixture.products_path),
                               "--product", "xqol", "--case", "core", "--run-context", str(context)])
            if type(code) is not int:
                raise TypeError("public CLI must return its actual integer exit code")
            return code
    finally:
        fixture.doCleanups()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == '--allocate-prebuilt-inputs-fixture':
        raise SystemExit(allocate_prelaunch_import_fixture(phase_guard_files=True, prebuilt_case_inputs=Path(sys.argv[2])))
    if sys.argv[1:] == ["--allocate-prelaunch-filepins-fixture"]:
        raise SystemExit(allocate_prelaunch_import_fixture(phase_guard_files=True))
    if sys.argv[1:] == ["--allocate-prelaunch-import-fixture"]:
        raise SystemExit(allocate_prelaunch_import_fixture())
    if sys.argv[1:] == ["--cli-fixture"]:
        raise SystemExit(cli_fixture())
    if len(sys.argv) == 3 and sys.argv[1] == "--verify-json-fixture":
        raise SystemExit(verify_json_fixture(sys.argv[2]))
    unittest.main(verbosity=2)
