"""Render the three frozen presentation consumers of the foreground contract.

This module transforms source bytes only. It imports no UI, process or SDK API.
The caller seals every returned body in its normal source manifest afterwards.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib

CONTRACT_SHA256 = "61740518484fc72a0d5ed64ae50d045afc359f267a9f472e0749298bc9808fa4"


@dataclass(frozen=True, slots=True)
class BackgroundDisplaySourcesV1:
    actor: bytes
    obs_desktop: bytes
    capture_worker: bytes


def _replace(source: str, old: str, new: str, count: int = 1) -> str:
    if source.count(old) != count:
        raise ValueError("Frozen background consumer seam differs: " + old[:120])
    return source.replace(old, new)


def _replace_function(source: str, name: str, replacement: str) -> str:
    tree = ast.parse(source)
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
             and node.name == name]
    if len(nodes) != 1 or nodes[0].end_lineno is None:
        raise ValueError("Unique frozen function required: " + name)
    node = nodes[0]
    lines = source.splitlines(keepends=True)
    return "".join(lines[:node.lineno - 1]) + replacement.rstrip() + "\n" + "".join(lines[node.end_lineno:])


# The dependency prefix used by historical actors replaces PYTHONPATH. Restore
# the current frozen namespace afterwards, without deleting a cached module.
_NAMESPACE = '''
def _background_namespace_v1() -> None:
    import os
    roots = [str(N), str(N / 'tools/g2_saved_campaign')]
    sys.path[:0] = roots
    os.environ['PYTHONPATH'] = os.pathsep.join(roots + [os.environ.get('PYTHONPATH', '')])

def _placement_foreground_permitted_v1(value: object, game_pid: int) -> bool:
    import hashlib
    from importlib.util import find_spec
    _background_namespace_v1()
    name = 'tools.g2_saved_campaign.background_foreground_contract_v1'
    expected = (N / 'tools/g2_saved_campaign/background_foreground_contract_v1.py').resolve(strict=True)
    spec = find_spec(name)
    cached = sys.modules.get(name)
    package = sys.modules.get(name.rsplit('.', 1)[0])
    leaf = name.rsplit('.', 1)[1]
    if (spec is None or spec.origin is None or Path(spec.origin).resolve(strict=True) != expected
            or (cached is not None and Path(getattr(cached, '__file__', '')).resolve(strict=True) != expected)
            or (package is not None and hasattr(package, leaf)
                and (cached is None or getattr(package, leaf) is not cached))
            or hashlib.sha256(expected.read_bytes()).hexdigest() != '__CONTRACT_SHA__'):
        raise ValueError('Exact frozen foreground contract required')
    from tools.g2_saved_campaign import background_foreground_contract_v1 as contract
    if not isinstance(value, dict):
        raise ValueError('Placement receipt must be an object')
    observation = contract.parse_current_saved_launch_foreground_v1(value['foreground_observation'])
    if (observation.game_pid != game_pid or observation.owned_auxiliary_pids
            or type(value['foreground_before']) is not int or type(value['foreground_after']) is not int
            or type(value['foreground_unchanged']) is not bool
            or value['foreground_before'] != observation.foreground_before
            or value['foreground_after'] != observation.foreground_after
            or value['foreground_unchanged'] is not observation.foreground_unchanged
            or value['current_desktop_id'] != observation.desktop_before
            or value['current_desktop_after'] != observation.desktop_after):
        raise ValueError('Placement foreground fields differ from the shared observation')
    return observation.permitted
'''

_CAPTURE_FOREGROUND = '''def _foreground_observation(
    before: int, desktop_before: str, game_pid: int, owned_obs_pid: int,
) -> LaunchForegroundObservationV1:
    _generation_helpers()
    name = "tools.g2_saved_campaign.background_foreground_contract_v1"
    expected = (Path(__file__).resolve().parents[1] / "tools/g2_saved_campaign/background_foreground_contract_v1.py").resolve(strict=True)
    spec = importlib.util.find_spec(name)
    cached = sys.modules.get(name)
    package = sys.modules.get(name.rsplit('.', 1)[0])
    leaf = name.rsplit('.', 1)[1]
    if (spec is None or spec.origin is None or Path(spec.origin).resolve(strict=True) != expected
            or (cached is not None and Path(getattr(cached, "__file__", "")).resolve(strict=True) != expected)
            or _sha(expected) != "__CONTRACT_SHA__"):
        raise RuntimeError("Exact frozen background foreground contract required")
    from tools.g2_saved_campaign import background_foreground_contract_v1 as contract
    import win32gui
    import win32process
    from tools.g2_saved_campaign import managed_desktop1_placement as managed
    _, first_desktop = managed.desktop_inventory()
    after = win32gui.GetForegroundWindow()
    try:
        pid = win32process.GetWindowThreadProcessId(after)[1] if after else None
    except OSError:
        pid = None
    if pid == 0:
        pid = None
    desktop_after = managed.desktop_inventory()[1]
    final_after = win32gui.GetForegroundWindow()
    if final_after != after:
        after, pid = final_after, None
    if first_desktop != desktop_after:
        raise RuntimeError("User desktop changed during foreground sampling")
    return contract.classify_current_saved_launch_foreground_v1({
        "foreground_before": before, "foreground_after": after, "foreground_after_pid": pid,
        "desktop_before": desktop_before, "desktop_after": desktop_after,
        "game_pid": game_pid, "owned_auxiliary_pids": [owned_obs_pid],
    })
'''

_GENERATION_HELPERS = 'def _generation_helpers() -> tuple[\n    type[ProcessGeneration], Callable[[object], ProcessGeneration],\n    Callable[[ProcessGeneration, int], None], Callable[[str], None],\n]:\n    root = Path(__file__).resolve().parents[1]\n    for name, relative, pin in (\n        ("tools.g2_saved_campaign.background_foreground_contract_v1",\n         "tools/g2_saved_campaign/background_foreground_contract_v1.py", "__CONTRACT_SHA__"),\n        ("tools.g2_saved_campaign.managed_desktop1_placement",\n         "tools/g2_saved_campaign/managed_desktop1_placement.py", "__PLACEMENT_SHA__"),\n    ):\n        expected = (root / relative).resolve(strict=True)\n        spec = importlib.util.find_spec(name)\n        cached = sys.modules.get(name)\n        package = sys.modules.get(name.rsplit(".", 1)[0])\n        leaf = name.rsplit(".", 1)[1]\n        if (spec is None or spec.origin is None or Path(spec.origin).resolve(strict=True) != expected\n                or (cached is not None and Path(getattr(cached, "__file__", "")).resolve(strict=True) != expected)\n                or (package is not None and hasattr(package, leaf)\n                    and (cached is None or getattr(package, leaf) is not cached))\n                or _sha(expected) != pin):\n            raise RuntimeError("Exact frozen background generation helper required: " + name)\n    from tools.g2_saved_campaign.managed_desktop1_placement import (\n        ProcessGeneration, game_generation, check_game_window, deadline_check,\n    )\n    return ProcessGeneration, game_generation, check_game_window, deadline_check\n'

_OBS_HELPERS = '''from contextlib import ExitStack
from typing import Callable, ContextManager, MutableMapping, Protocol, TypedDict
from importlib.util import find_spec
import importlib
import sys

def _require_foreground_contract_origin_v1() -> None:
    name = 'tools.g2_saved_campaign.background_foreground_contract_v1'
    expected = (Path(__file__).resolve().parents[1] / 'tools/g2_saved_campaign/background_foreground_contract_v1.py').resolve(strict=True)
    spec = find_spec(name)
    cached = sys.modules.get(name)
    package = sys.modules.get(name.rsplit('.', 1)[0])
    leaf = name.rsplit('.', 1)[1]
    if (spec is None or spec.origin is None or Path(spec.origin).resolve(strict=True) != expected
            or (cached is not None and Path(getattr(cached, '__file__', '')).resolve(strict=True) != expected)):
        raise ValueError('Exact frozen foreground contract origin differs')
    with expected.open('rb') as stream:
        raw = stream.read(5303)
    if len(raw) != 5302 or hashlib.sha256(raw).hexdigest() != '__CONTRACT_SHA__':
        raise ValueError('Exact frozen foreground contract pin differs')
    module = importlib.import_module(name)
    if Path(module.__file__).resolve(strict=True) != expected:
        raise ValueError('Actual foreground contract origin differs')

def _require_obs_placement_origin_v1() -> None:
    name = 'tools.g2_saved_campaign.managed_desktop1_placement'
    expected = (Path(__file__).resolve().parents[1] / 'tools/g2_saved_campaign/managed_desktop1_placement.py').resolve(strict=True)
    spec = find_spec(name)
    cached = sys.modules.get(name)
    package = sys.modules.get(name.rsplit('.', 1)[0])
    leaf = name.rsplit('.', 1)[1]
    if (spec is None or spec.origin is None or Path(spec.origin).resolve(strict=True) != expected
            or (cached is not None and Path(getattr(cached, '__file__', '')).resolve(strict=True) != expected)
            or (package is not None and hasattr(package, leaf)
                and (cached is None or getattr(package, leaf) is not cached))):
        raise ValueError('Exact frozen placement module origin differs')
    with expected.open('rb') as stream:
        raw = stream.read(32769)
    if len(raw) > 32768 or hashlib.sha256(raw).hexdigest() != '__PLACEMENT_SHA__':
        raise ValueError('Exact frozen placement module pin differs')

_require_foreground_contract_origin_v1()
_require_obs_placement_origin_v1()
from tools.g2_saved_campaign.background_foreground_contract_v1 import (
    JsonObject, LaunchForegroundObservationV1, classify_current_saved_launch_foreground_v1)

class _ObsGenerationV1(Protocol):
    pid: int
    creation_filetime: int
    executable: Path
    def check(self) -> None: ...

class _ObsProcessV1(Protocol):
    pid: int

class _ObsBeforeV1(TypedDict):
    schema: str
    machine_id: str | None
    hwnd: int
    pid: int
    creation_filetime: int
    executable: str
    window_class: str
    window_title: str
    desktop_ids: list[str]
    current_desktop_id: str
    captured_before_obs_launch: bool
    observed_at_utc: str
    source_sha256: str
    foreground_observation: JsonObject

class _ObsLaunchV1(TypedDict):
    machine_id: str

class _ObsJobV1(TypedDict):
    pid: int
    hwnd: int
    desktop_id: str
    launch: _ObsLaunchV1
    receipt_root: str

class _ObsEngineV1(Protocol):
    process: _ObsProcessV1 | None
    generation: _ObsGenerationV1 | None
    before_foreground: _ObsBeforeV1
    before_foreground_generation: _ObsGenerationV1

class _ObsGuiV1(Protocol):
    def GetForegroundWindow(self) -> int: ...
    def IsWindow(self, hwnd: int) -> bool: ...
    def GetParent(self, hwnd: int) -> int: ...
    def GetClassName(self, hwnd: int) -> str: ...
    def GetWindowText(self, hwnd: int) -> str: ...
    def IsWindowVisible(self, hwnd: int) -> bool: ...
    def IsIconic(self, hwnd: int) -> bool: ...
    def ShowWindow(self, hwnd: int, command: int) -> bool: ...
    def EnumWindows(self, callback: Callable[[int, object], bool], extra: object) -> None: ...

class _ObsProcessesV1(Protocol):
    def GetWindowThreadProcessId(self, hwnd: int) -> tuple[int, int]: ...

def _sample_obs_foreground_v1(gui: _ObsGuiV1, processes: _ObsProcessesV1) -> tuple[int, int | None]:
    hwnd = gui.GetForegroundWindow()
    if type(hwnd) is not int or not 0 <= hwnd <= (1 << 53) - 1:
        raise ValueError('Exact safe integer foreground HWND required')
    if hwnd == 0:
        return hwnd, None
    try:
        pid = processes.GetWindowThreadProcessId(hwnd)[1] if gui.IsWindow(hwnd) else 0
        after = gui.GetForegroundWindow()
    except OSError:
        return gui.GetForegroundWindow(), None
    if after != hwnd or type(pid) is not int or not 1 <= pid <= (1 << 32) - 1:
        return after, None
    return hwnd, pid

def _observe_obs_foreground_v1(*, before: int, desktop_before: str, game_pid: int,
        owned_auxiliary_pids: tuple[int, ...], target_desktop_id: str,
        gui: _ObsGuiV1, processes: _ObsProcessesV1,
        desktop_inventory: Callable[[], tuple[list[str], str]]) -> LaunchForegroundObservationV1:
    ids, current = desktop_inventory()
    if current != desktop_before or target_desktop_id not in ids or target_desktop_id == current:
        raise ValueError('Current user desktop or actual inactive Game target differs')
    hwnd, pid = _sample_obs_foreground_v1(gui, processes)
    after_ids, after_current = desktop_inventory()
    if target_desktop_id not in after_ids:
        raise ValueError('Actual Game target desktop no longer exists')
    return classify_current_saved_launch_foreground_v1({
        'foreground_before': before, 'foreground_after': hwnd, 'foreground_after_pid': pid,
        'desktop_before': desktop_before, 'desktop_after': after_current,
        'game_pid': game_pid, 'owned_auxiliary_pids': list(owned_auxiliary_pids)})
'''

_OBS_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ('def retain_before_foreground(engine,job,expected_hwnd,custody,ProcessGeneration,write):',
     '''def retain_before_foreground(engine: _ObsEngineV1, job: _ObsJobV1, expected_hwnd: int,
        custody: ExitStack, ProcessGeneration: Callable[[int, Path], ContextManager[_ObsGenerationV1]],
        write: Callable[[Path, object], None]) -> None:'''),
    ('''    if engine.process is not None or not expected_hwnd or gui.GetForegroundWindow()!=expected_hwnd:
        raise ValueError('Exact non-null attempt foreground must be captured before owned OBS launch')
    pid=processes.GetWindowThreadProcessId(expected_hwnd)[1]''',
     '''    if engine.process is not None:
        raise ValueError('Attempt observation must precede the owned OBS launch')
    ids,current=managed.desktop_inventory()
    observed=_observe_obs_foreground_v1(before=expected_hwnd,desktop_before=current,game_pid=job['pid'],
        owned_auxiliary_pids=(),target_desktop_id=job['desktop_id'],gui=gui,processes=processes,
        desktop_inventory=managed.desktop_inventory)
    if not observed.permitted:
        raise ValueError('Pre-launch foreground policy refused: '+observed.classification)
    expected_hwnd=observed.foreground_after;pid=observed.foreground_after_pid
    if pid is None:raise ValueError('Actual foreground owner is required')'''),
    ('''    generation.check()
    if (not gui.IsWindow(expected_hwnd) or processes.GetWindowThreadProcessId(expected_hwnd)[1]!=pid
            or gui.GetClassName(expected_hwnd)!=classname or gui.GetForegroundWindow()!=expected_hwnd
            or managed.desktop_inventory()!=(ids,current)):
        raise ValueError('Foreground window or user desktop changed during its pre-launch observation')''',
     '''    observed=_observe_obs_foreground_v1(before=expected_hwnd,desktop_before=current,game_pid=job['pid'],
        owned_auxiliary_pids=(),target_desktop_id=job['desktop_id'],gui=gui,processes=processes,
        desktop_inventory=managed.desktop_inventory)
    if not observed.permitted:
        raise ValueError('Pre-launch foreground policy refused: '+observed.classification)'''),
    ("        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}\n    write(Path(job['receipt_root'])/'obs-attempt-before-foreground.json',context)",
     "        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),\n        'foreground_observation':observed.to_wire()}\n    write(Path(job['receipt_root'])/'obs-attempt-before-foreground.json',context)"),
    ("    context={'schema':'xar.ck3.obs-attempt-before-foreground/v1'", "    context: _ObsBeforeV1={'schema':'xar.ck3.obs-attempt-before-foreground/v1'"),
    ('''def place_core(engine, job, record, *, gui, processes, desktop_inventory, desktop_read,
               monotonic=time.monotonic, sleep=time.sleep):''',
     '''def place_core(engine: _ObsEngineV1, job: _ObsJobV1, record: MutableMapping[str, object], *,
        gui: _ObsGuiV1, processes: _ObsProcessesV1,
        desktop_inventory: Callable[[], tuple[list[str], str]],
        desktop_read: Callable[[int], dict[str, object]],
        monotonic: Callable[[], float]=time.monotonic,
        sleep: Callable[[float], None]=time.sleep) -> MutableMapping[str, object]:'''),
    ("    generation=engine.generation;generation.check()\n    if generation.pid!=engine.process.pid or generation.pid!=record['obs_pid']:",
     "    generation=engine.generation\n    if generation is None or engine.process is None:raise ValueError('Retained owned OBS process is required')\n    generation.check()\n    if generation.pid!=engine.process.pid or generation.pid!=record['obs_pid']:"),
    ('''    def prior_identity():
        prior.check()
        if (not gui.IsWindow(context['hwnd']) or processes.GetWindowThreadProcessId(context['hwnd'])[1]!=prior.pid
                or gui.GetClassName(context['hwnd'])!=context['window_class']):
            raise ValueError('Exact pre-launch user foreground HWND/generation changed')
    prior_identity()
''', ''),
    ('    def collect(hwnd,_):', '    def collect(hwnd: int, _: object) -> bool:'),
    ('    def owned():', '    def owned() -> None:'),
    ("    if (ids,current)!=(context['desktop_ids'],context['current_desktop_id']):", "    if current!=context['current_desktop_id']:"),
    ("    record.update(stage='obs_hidden_desktop_read',foreground_before_minimize=gui.GetForegroundWindow())",
     '''    observations: list[JsonObject]=[]
    record['foreground_observations']=observations
    def probe(*, allow_transient_owned: bool=False) -> LaunchForegroundObservationV1:
        owned()
        observation=_observe_obs_foreground_v1(before=context['hwnd'],
            desktop_before=context['current_desktop_id'],game_pid=job['pid'],
            owned_auxiliary_pids=(generation.pid,),target_desktop_id=target,gui=gui,processes=processes,
            desktop_inventory=desktop_inventory)
        owned()
        observations.append(observation.to_wire())
        if not observation.permitted and not (allow_transient_owned
                and observation.classification=='OWNED_AUXILIARY_FOREGROUND'
                and observation.foreground_after==hwnd and observation.foreground_after_pid==generation.pid):
            raise ValueError('Background foreground policy refused: '+observation.classification)
        return observation
    record.update(stage='obs_hidden_desktop_read',foreground_before_minimize=probe(allow_transient_owned=True).foreground_after)'''),
    ('''    current_foreground=gui.GetForegroundWindow()
    if current_foreground not in (hwnd,context['hwnd']):
        raise ValueError('Unknown foreground transition; no owned minimize or move permitted')''', '    current_foreground=probe(allow_transient_owned=True).foreground_after'),
    ('''        if desktop_inventory()!=(ids,current):raise ValueError('User desktop changed before the one permitted minimize')
        prior_identity()
        current_foreground=gui.GetForegroundWindow()
        if current_foreground not in (hwnd,context['hwnd']):
            raise ValueError('Foreground changed before owned minimize; no action permitted')''', '        current_foreground=probe(allow_transient_owned=True).foreground_after'),
    ('        # is only used when the original user foreground already remains exact.', '        # is only used for an observed permitted non-owned user foreground.'),
    ('''            owned();prior_identity();probes+=1
            if desktop_inventory()!=(ids,current):raise ValueError('User desktop changed while the iconic Shell view was pending')''', '''            owned();probes+=1
            foreground_observation=probe(allow_transient_owned=True)'''),
    ('            foreground_now=gui.GetForegroundWindow()', '            foreground_now=foreground_observation.foreground_after'),
    ('''            if foreground_now not in (0,hwnd,context['hwnd']):
                raise ValueError('Windows selected another foreground; original exact foreground is required and will not be restored')
''', ''),
    ("                    if foreground_now==context['hwnd']:", '                    if foreground_observation.permitted:'),
    ("            if monotonic()>=deadline:raise TimeoutError('Owned OBS iconic mapping and exact pre-launch foreground did not both become observable within 2 seconds')", "            if monotonic()>=deadline:raise TimeoutError('Owned OBS iconic mapping and permitted user foreground were not observable within 2 seconds')"),
    ('    owned();prior_identity()', '    owned()'),
    ('    observed_foreground=gui.GetForegroundWindow()', '    observed_foreground=probe().foreground_after'),
    ("    if (observed_ids,observed_current)!=(ids,current) or after['desktop_id']!=current:", "    if observed_current!=current or target not in observed_ids or after['desktop_id']!=current:"),
    ('''    if observed_foreground!=context['hwnd']:
        raise ValueError('Exact original foreground is not preserved; no restoration attempted')
''', ''),
    ('''    if desktop_inventory()!=(ids,current) or gui.GetForegroundWindow()!=context['hwnd']:
        raise ValueError('Final exact foreground/current-desktop observation differs')''',
     "    final_observation=probe()\n    record['foreground_observation']=final_observation.to_wire()\n    record['foreground_after']=final_observation.foreground_after"),
    ("    record.update(stage='minimized_verified_original_foreground_guard_pending',", "    record.update(stage='minimized_verified_background_foreground_guard_pending',"),
    ('        user_window_restore_calls=0,gameplay_input_calls=0,final_original_foreground_guard_required=True,', '        user_window_restore_calls=0,gameplay_input_calls=0,final_background_foreground_guard_required=True,'),
    ('    windows=[]', '    windows: list[int]=[]'),
    ('def _shell_mapping_missing(error):', 'def _shell_mapping_missing(error: object) -> bool:'),
)


def _render_obs(original: bytes, placement_sha256: str) -> bytes:
    if len(original) != 14041 or hashlib.sha256(original).hexdigest() != "74c9f4ce9d800dd5d51159ca8080035f2abd159fcdaf0d42a531f624cd9eb204":
        raise ValueError("Exact frozen OBS desktop helper input required")
    source = original.decode("utf-8")
    for old, new in _OBS_REPLACEMENTS:
        source = _replace(source, old, new, 2 if old == '    owned();prior_identity()' else 1)
    helper = _OBS_HELPERS.replace("__CONTRACT_SHA__", CONTRACT_SHA256).replace("__PLACEMENT_SHA__", placement_sha256)
    source = _replace(source, "\ndef _read_pin(reference):", "\n" + helper + "\ndef _read_pin(reference):")
    source = _replace(source, "    import managed_desktop1_placement as managed", "    from tools.g2_saved_campaign import managed_desktop1_placement as managed", 2)
    return source.encode("utf-8")


def _render_capture(original: bytes, placement_sha256: str) -> bytes:
    if len(original) != 78278 or hashlib.sha256(original).hexdigest() != "458a747c4f1909ab8e8cf67b98d2ff2d8c6d67b1a724f170f2fb83eed3aaa1ce":
        raise ValueError("Exact frozen native capture worker input required")
    source = original.decode("utf-8")
    source = _replace(source, "from typing import Callable\n", "from typing import Callable, TYPE_CHECKING, Literal, TypedDict\nif TYPE_CHECKING:\n    from tools.g2_saved_campaign.background_foreground_contract_v1 import LaunchForegroundObservationV1, JsonObject\n    from tools.g2_saved_campaign.managed_desktop1_placement import ProcessGeneration\n")
    source = _replace_function(source, "_foreground_observation", _CAPTURE_RECEIPT + "\n" + _CAPTURE_FOREGROUND.replace("__CONTRACT_SHA__", CONTRACT_SHA256))
    generation = _GENERATION_HELPERS.replace("__PLACEMENT_SHA__", placement_sha256).replace("__CONTRACT_SHA__", CONTRACT_SHA256)
    source = _replace_function(source, "_generation_helpers", generation)
    source = _replace(source, "    foreground = win32gui.GetForegroundWindow()\n", "")
    source = _replace(source, "            guard()\n            if with_decision:\n                before_path=", "            guard()\n            from tools.g2_saved_campaign import managed_desktop1_placement as managed\n            foreground_desktop = managed.desktop_inventory()[1]\n            foreground = win32gui.GetForegroundWindow()\n            if with_decision:\n                before_path=")
    source = _replace(source, """            foreground_observation = _foreground_observation(foreground, engine.process.pid)
            _write_new(root / "foreground-observation.json", foreground_observation)
            if foreground_observation["foreground_changed"] and foreground_observation["foreground_after_is_owned_obs"]:
                raise RuntimeError("OBS startup changed the user foreground; no restoration attempted")""", """            engine.check()
            foreground_observation = _foreground_observation(
                foreground, foreground_desktop, job["pid"], engine.process.pid)
            _write_new(root / "foreground-observation.json", foreground_observation.to_wire())
            if not foreground_observation.permitted:
                raise RuntimeError("OBS startup foreground rejected: " + foreground_observation.classification)""")
    source = _replace(source,
        '            _write_new(root / "foreground-observation.json", foreground_observation.to_wire())',
        _CAPTURE_FOREGROUND_WRITE)
    return source.encode("utf-8")


def _render_actor(original: bytes, old_capture: bytes, new_capture: bytes, placement_sha256: str) -> bytes:
    source = original.decode("utf-8")
    source = _replace(source, "        and placement['status']=='GREEN' and placement['foreground_unchanged'] is True", "        and placement['status']=='GREEN' and _placement_foreground_permitted_v1(placement,a.game_pid)")
    source = _replace(source, "\ndef main():", "\n" + _NAMESPACE.replace("__CONTRACT_SHA__", CONTRACT_SHA256) + "\ndef main():")
    prefix = "        {'__file__':str(hotfix_path),'__name__':'_reviewed_dependency_prefix'})"
    source = _replace(source, prefix, prefix + "\n    _background_namespace_v1()", 2)
    source = _replace(source, "'managed_desktop1_placement'", "'tools.g2_saved_campaign.managed_desktop1_placement'", 2)
    source = _replace(source, str(len(old_capture)), str(len(new_capture)), 2)
    source = _replace(source, hashlib.sha256(old_capture).hexdigest(), hashlib.sha256(new_capture).hexdigest(), 3)
    source = _replace(source, "    require(hashlib.sha256(helper.read_bytes()).hexdigest()==\n        '2f40965ea2af7b010a25750fccaecebb0964d1381d975a8bf4403bdbbae3f493',", "    require(helper.resolve()==(N/'tools/g2_saved_campaign/managed_desktop1_placement.py').resolve(strict=True)\n        and hashlib.sha256(helper.read_bytes()).hexdigest()==\n        '" + placement_sha256 + "',")
    return source.encode("utf-8")


def render_current_saved_background_display_v1(*, actor: bytes, obs_desktop: bytes,
                                              capture_worker: bytes, placement_sha256: str) -> BackgroundDisplaySourcesV1:
    """Reject foreign preimages, render actual consumers, then compile each body."""
    if type(actor) is not bytes or type(obs_desktop) is not bytes or type(capture_worker) is not bytes:
        raise ValueError("Frozen display sources must be exact bytes")
    if type(placement_sha256) is not str or len(placement_sha256) != 64 or any(c not in "0123456789abcdef" for c in placement_sha256):
        raise ValueError("Exact placement SHA256 required")
    capture = _render_capture(capture_worker, placement_sha256)
    obs = _render_obs(obs_desktop, placement_sha256)
    start = _render_actor(actor, capture_worker, capture, placement_sha256)
    for name, raw in (("start_new_game_display.py", start), ("obs_owned_desktop.py", obs),
                      ("ck3_obs_capture_png_retry_c23.py", capture)):
        compile(raw, name, "exec")
    return BackgroundDisplaySourcesV1(start, obs, capture)

_CAPTURE_RECEIPT = 'class _CaptureForegroundReceiptV1(TypedDict):\n    schema: Literal["xar.ck3.capture-foreground-observation/v1"]\n    machine_id: str\n    observed_at_utc: str\n    foreground_observation: JsonObject\n\ndef _parse_capture_foreground_receipt_v1(\n    value: object, *, expected_machine_id: str,\n) -> _CaptureForegroundReceiptV1:\n    import re\n    _generation_helpers()\n    from tools.g2_saved_campaign.background_foreground_contract_v1 import parse_current_saved_launch_foreground_v1\n    if (type(expected_machine_id) is not str\n            or re.fullmatch(r"[a-z0-9][a-z0-9-]{0,127}", expected_machine_id) is None):\n        raise ValueError("Actual canonical machine identity required")\n    if (not isinstance(value, dict) or type(value) is not dict\n            or set(value) != {"schema", "machine_id", "observed_at_utc", "foreground_observation"}\n            or value["schema"] != "xar.ck3.capture-foreground-observation/v1"\n            or type(value["machine_id"]) is not str or value["machine_id"] != expected_machine_id):\n        raise ValueError("Exact capture foreground envelope and current machine required")\n    observed: object = value["observed_at_utc"]\n    if type(observed) is not str or not observed:\n        raise ValueError("Actual foreground observation UTC required")\n    stamp = datetime.fromisoformat(observed)\n    if stamp.tzinfo is None or stamp.utcoffset() != timezone.utc.utcoffset(stamp):\n        raise ValueError("Foreground observation time must have UTC offset")\n    observation = parse_current_saved_launch_foreground_v1(value["foreground_observation"])\n    return {"schema": "xar.ck3.capture-foreground-observation/v1",\n            "machine_id": expected_machine_id, "observed_at_utc": observed,\n            "foreground_observation": observation.to_wire()}\n\ndef _capture_foreground_receipt_v1(\n    observation: LaunchForegroundObservationV1,\n) -> _CaptureForegroundReceiptV1:\n    _generation_helpers()\n    from tools.g2_saved_campaign import managed_desktop1_placement as managed\n    from tools.g2_saved_campaign.background_foreground_contract_v1 import LaunchForegroundObservationV1\n    if not isinstance(observation, LaunchForegroundObservationV1):\n        raise ValueError("Actual typed foreground observation required")\n    machine: object = managed.ck3_live_run_id.current_machine_id()\n    if not isinstance(machine, str):\n        raise ValueError("Current machine identity provider must return text")\n    value: _CaptureForegroundReceiptV1 = {\n        "schema": "xar.ck3.capture-foreground-observation/v1",\n        "machine_id": machine, "observed_at_utc": datetime.now(timezone.utc).isoformat(),\n        "foreground_observation": observation.to_wire()}\n    return _parse_capture_foreground_receipt_v1(value, expected_machine_id=machine)\n'

_CAPTURE_FOREGROUND_WRITE = '            _write_new(root / "foreground-observation.json", _capture_foreground_receipt_v1(foreground_observation))'
