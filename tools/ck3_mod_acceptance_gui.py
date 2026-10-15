"""Explicit official-UI fallback behind the common mod acceptance entry.

No native bridge is loaded. GUI/business qualification needs a separate direct
review; process exit and STOP/WM_CLOSE never supply that qualification.
"""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid

from ck3_mod_acceptance_keeper import check_pin, pin, read_json, require, utc, write_new
from ck3_mod_acceptance_launcher import check_fresh_frame, recent
from ck3_mod_acceptance_prepare import _outer_from_inner, checked_copy, materialize_product_profile


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, 'Configured module unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def path_at(value, base):
    path = Path(value)
    return (path if path.is_absolute() else base / path).resolve()


def inventory(directory):
    directory = Path(directory)
    return {p.relative_to(directory).as_posix(): pin(p)
            for p in sorted(directory.rglob('*')) if p.is_file()}


def exact_formal(staging, reference):
    check_pin(reference)
    manifest = read_json(reference['path'])
    rows = manifest['files']
    if isinstance(rows, dict):
        rows = [dict(value, path=key) for key, value in rows.items()]
    require(isinstance(rows, list) and rows, 'Nonempty formal file inventory required')
    actual = inventory(staging)
    expected = {}
    for row in rows:
        relative = row['path']
        require(relative not in expected, 'Duplicate formal file')
        expected[relative] = {'bytes': row.get('bytes', row.get('size')), 'sha256': row['sha256'].lower()}
    require(set(expected) == set(actual), 'Formal staging file set differs')
    require(all({k: actual[name][k] for k in ('bytes', 'sha256')} == row
                for name, row in expected.items()), 'Formal staging bytes differ')
    require('descriptor.mod' in actual, 'Formal descriptor required')
    return actual


def budget(value, name, maximum=None):
    require(type(value) in (int, float) and math.isfinite(value) and value > 0,
            'Positive finite budget required: ' + name)
    require(maximum is None or value <= maximum, 'Budget exceeds bound: ' + name)
    return value


def chinese_settings(content):
    pattern = r'(?s)("language"\s*=\s*\{[^{}]*?\bvalue\s*=\s*)"[^"\n]*"'
    updated, count = re.subn(pattern, r'\1"l_simp_chinese"', content)
    require(count == 1, 'Settings seed must contain exactly one language value block')
    return updated


class GuiSelection:
    def __init__(self, args):
        self.args = args
        self.runtime_path = Path(args.runtime).resolve()
        self.runtime = read_json(self.runtime_path)
        require(self.runtime.get('schema') == 'ck3-mod-acceptance-runtime-v1', 'Common runtime schema required')
        self.base = self.runtime_path.parent
        self.manifest_ref = dict(self.runtime['manifest'])
        self.manifest_ref['path'] = str(path_at(self.manifest_ref['path'], self.base))
        check_pin(self.manifest_ref)
        self.manifest = read_json(self.manifest_ref['path'])
        require(self.manifest.get('schema') == 'ck3-mod-acceptance-shared-runtime-v1' and
                self.manifest.get('execution_mode') == 'gui_only', 'Explicit common GUI-only manifest required')
        require(not self.manifest.get('native'), 'GUI-only manifest must not select a native binary')
        self.paths = {name: path_at(self.runtime[name], self.base) for name in
                      ('python', 'repo_root', 'game_dir', 'userdir_root', 'artifacts_root')}
        self.products_path = Path(args.products).resolve()
        products = read_json(self.products_path)
        require(products.get('schema') == 'ck3-mod-acceptance-products-v1', 'Common products schema required')
        self.product = products['products'][args.product]
        matches = [x for x in self.product['cases'] if x['id'] == args.case]
        require(len(matches) == 1, 'Exactly one GUI business case required')
        self.case = matches[0]
        for obj in (self.product, self.case):
            require(not set(obj) & {'host', 'source_root', 'source_index', 'native', 'dll', 'injector',
                                   'engine', 'host_args', 'host_features', 'profile_features', 'execution_mode'},
                    'Products cannot choose the shared runtime')
        self.budgets = self.case['budgets']
        for name in ('timeout', 'quit_timeout', 'max_prepare_bytes'):
            budget(self.budgets[name], name)
        budget(self.budgets['poll_interval'], 'poll_interval', 5)
        require(self.budgets['poll_interval'] >= .1, 'Poll interval must be at least .1 seconds')
        self.prepared = read_json(args.prepared_case) if args.prepared_case else None
        self.context = read_json(args.run_context) if args.run_context else None
        for obj in (self.prepared, self.context):
            if obj:
                require(obj.get('product') == args.product and obj.get('case') == args.case and
                        obj.get('runtime_manifest') == self.manifest_ref, 'Prepared/context identity differs')

    @property
    def exe(self):
        return self.paths['game_dir'] / 'binaries/ck3.exe'

    def lease(self):
        config = self.runtime['allocation']
        check_pin(config['lease_module'])
        check_pin(config['task_bus'])
        module = load_module(config['lease_module']['path'], 'gui_acceptance_screen_lease')
        source = Path(config['task_bus']['path']).resolve()
        bus = path_at(config['bus_dir'], self.base)
        sha = config['task_bus']['sha256'].upper()
        module.checked_cli_pair(source, bus / 'bin/codex_task_bus.py', sha)
        repo = path_at(config['lease_repo'], self.base)
        return module, source, bus, sha, repo

    def preflight(self):
        checked = [check_pin(self.manifest_ref)]
        for name in ('python', 'repo_root', 'game_dir'):
            require(self.paths[name].exists(), 'Configured path missing: ' + name)
        require(pin(self.exe)['sha256'] == self.manifest['game']['exe_sha256'].lower(),
                'Installed game differs from the selected shared GUI runtime')
        module, _, _, _, repo = self.lease()
        head = module.checkout_head(repo)
        source_head = module.checkout_head(self.paths['repo_root'])
        if self.prepared:
            for row in self.prepared['inputs']:
                checked.append(check_pin(row))
            for row in self.prepared['profile_files'].values():
                checked.append(check_pin(row))
            profile = Path(self.prepared['profile'])
            settings = (profile / 'pdx_settings.txt').read_text(encoding='utf-8-sig')
            require(chinese_settings(settings) == settings,
                    'Prepared profile language differs')
            if self.prepared.get('product_source'):
                item = self.prepared['product_source']
                require(module.checkout_head(Path(item['repo'])) == item['head'], 'Frozen product checkout changed')
        return {'status': 'READY', 'runtime_status': 'NOT_RUN', 'business_pass': False,
                'lease_head': head, 'source_head': source_head, 'checked_inputs': checked}


def prepare(selection):
    args = selection.args
    require(args.case_inputs and args.prepare_output, 'prepare requires case-inputs and prepare-output')
    selection.preflight()
    inputs = read_json(args.case_inputs)
    required = {'staging', 'formal_manifest', 'settings', 'mcp_fallback_evidence'}
    require(required <= inputs.keys(), 'Missing explicit GUI case inputs')
    staging = Path(inputs['staging']).resolve()
    rows = exact_formal(staging, inputs['formal_manifest'])
    require(inputs['mcp_fallback_evidence'], 'Actual MCP fallback evidence required')
    pins = [pin(args.case_inputs), pin(selection.products_path), pin(selection.runtime_path),
            check_pin(inputs['formal_manifest']), check_pin(inputs['settings'])]
    pins.extend(check_pin(row) for row in inputs['mcp_fallback_evidence'])
    pins.extend(rows.values())
    require(type(inputs.get('debug_mode', False)) is bool, 'debug_mode must be an explicit boolean')
    saved = check_pin(inputs['save']) if inputs.get('save') else None
    if saved:
        pins.append(saved)
    cache = inventory(inputs['warm_cache']) if inputs.get('warm_cache') else {}
    total = sum(row['bytes'] for row in rows.values()) + sum(row['bytes'] for row in cache.values())
    total += pins[4]['bytes']
    total += saved['bytes'] if saved else 0
    require(total <= selection.budgets['max_prepare_bytes'], 'Prepared input exceeds allocated byte budget')
    require(shutil.disk_usage(selection.paths['userdir_root'].parent).free > total,
            'Insufficient free space for declared preparation')
    out = Path(args.prepare_output).resolve()
    require(not out.exists(), 'Use a new prepare output')
    out.mkdir(parents=True)
    state = selection.paths['userdir_root'] / ('gui-' + uuid.uuid4().hex)
    profile = state / 'profile'
    if inputs.get('plain_configuration'):
        configuration = dict(inputs['plain_configuration'])
        configuration['pdx_settings.txt'] = inputs['settings']
        result = materialize_product_profile({'state_dir': str(state), 'output': str(out)}, staging, configuration)
        profile = Path(result['profile'])
    else:
        # Product-only helper requires four legacy plain files. This route has
        # only a settings seed; reuse its copier and outer-descriptor projection.
        profile.mkdir(parents=True)
        checked_copy(inputs['settings'], profile / 'pdx_settings.txt')
        target = profile / 'mod-content/product'
        shutil.copytree(staging, target)
        (profile / 'mod').mkdir()
        (profile / 'mod/product.mod').write_text(_outer_from_inner(target / 'descriptor.mod', target), encoding='utf-8')
        write_new(profile / 'dlc_load.json', {'enabled_mods': ['mod/product.mod'], 'disabled_dlcs': []})
    settings = profile / 'pdx_settings.txt'
    content = settings.read_text(encoding='utf-8-sig')
    settings.write_text(chinese_settings(content), encoding='utf-8', newline='\n')
    exact_formal(profile / 'mod-content/product', inputs['formal_manifest'])
    if cache:
        for relative, row in cache.items():
            checked_copy(row, profile / 'shadercache' / relative)
    if saved:
        checked_copy(saved, profile / 'save games' / Path(saved['path']).name)
    result = {'schema': 'ck3-mod-acceptance-gui-prepared-v1', 'product': args.product, 'case': args.case,
              'runtime_manifest': selection.manifest_ref, 'inputs': pins, 'profile': str(profile),
              'profile_files': inventory(profile), 'case_inputs': inputs, 'prepared_bytes': total,
              'runtime_status': 'NOT_RUN', 'business_pass': False}
    if inputs.get('source_repo'):
        module, _, _, _, _ = selection.lease()
        product_repo = Path(inputs['source_repo']).resolve()
        result['product_source'] = {'repo': str(product_repo), 'head': module.checkout_head(product_repo)}
    write_new(out / 'prepared-case.json', result)
    return result


def ck3_pids():
    import psutil
    return [row.info['pid'] for row in psutil.process_iter(['pid', 'name'])
            if (row.info['name'] or '').lower() == 'ck3.exe']


def allocate(selection):
    require(selection.prepared and not selection.context, 'One unused prepared case required')
    checked = selection.preflight()
    require(not ck3_pids(), 'CK3 already running')
    module, source, bus, sha, repo = selection.lease()
    current = module.call_bus(source, bus, sha, 'list', '--stale-after', '600')
    require(not any('ck3-screen:acquired' in row.get('resources', []) for row in current['tasks']),
            'Screen already owned')
    state = Path(selection.prepared['profile']).parent
    require(not (state / 'allocation.json').exists(), 'Prepared profile already allocated')
    config = selection.runtime['allocation']
    from ck3_live_run_id import allocate_live_run_id
    identity = allocate_live_run_id(selection.product.get('runtime_mod_key', selection.args.product),
                                   state_root=path_at(config['state_root'], selection.base),
                                   external_mod=selection.product.get('external_mod', False))
    run_dir = selection.paths['artifacts_root'] / identity.run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    task = config['task_prefix'] + identity.run_id
    require(len(task) <= 128, 'Screen task ID exceeds bus contract')
    module.call_bus(source, bus, sha, 'register', '--task', task, '--repo', str(repo),
                    '--resource', 'ck3-screen:acquired', '--summary', 'Common GUI-only mod acceptance',
                    '--next-step', 'Fresh Steam review then retained official UI run')
    packet = module.call_bus(source, bus, sha, 'list', '--stale-after', '600')
    owner = next(row for row in packet['tasks'] if row['task_id'] == task)
    module.checked_owner(packet['tasks'], task, owner['last_sequence'], repo, checked['lease_head'])
    context = {'schema': 'ck3-mod-acceptance-gui-context-v1', 'product': selection.args.product,
               'case': selection.args.case, 'runtime_manifest': selection.manifest_ref,
               'run_id': identity.run_id, 'identity': identity.to_dict(), 'run_dir': str(run_dir),
               'screen_task': task, 'sequence': owner['last_sequence'], 'lease_head': checked['lease_head'],
               'source_head': checked['source_head'], 'prepared_case': pin(selection.args.prepared_case),
               'implementation': pin(__file__), 'runtime_status': 'NOT_RUN', 'business_pass': False}
    write_new(state / 'allocation.json', context)
    write_new(run_dir / 'run-context.json', context)
    return context


def validate_review(selection, reference):
    review = read_json(reference)
    require(review.get('run_id') == selection.context['run_id'] and
            review.get('runtime_manifest') == selection.manifest_ref and
            review.get('direct_image_review') is True and review.get('steam_offline_confirmed') is True and
            isinstance(review.get('reviewer'), str) and review['reviewer'].strip(),
            'Current direct Steam offline review bound to this run required')
    reviewed = recent(review['reviewed_at_utc'])
    check_pin(review['frame']); check_pin(review['image'])
    frame, captured = check_fresh_frame(review['frame']['path'], review['image']['path'])
    require(captured <= reviewed, 'Review predates its actual Steam frame')
    import psutil
    require(psutil.Process(frame['steam_pid']).name().lower() in ('steam.exe', 'steamwebhelper.exe'),
            'Reviewed Steam process no longer exists')
    return pin(reference)


def request_window_close(pid):
    """Official title-bar close request; it is not a normal in-game Quit proof."""
    import win32con
    import win32gui
    import win32process
    windows = []
    def visit(hwnd, unused):
        if win32gui.IsWindowVisible(hwnd) and win32process.GetWindowThreadProcessId(hwnd)[1] == pid:
            windows.append(hwnd)
    win32gui.EnumWindows(visit, None)
    for hwnd in windows:
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    return windows


def wait_original(child, root, budgets, keeper, check_source):
    """Retain the exact process until exit, even after an unsuccessful close."""
    started = time.monotonic()
    close = None
    problem = None
    next_check = 0
    while child.poll() is None:
        now = time.monotonic()
        try:
            keeper.require_live()
            if now >= next_check:
                check_source()
                next_check = now + 5
        except Exception as error:
            problem = repr(error)
        expired = now - started > budgets['timeout']
        stopped = (root / 'STOP').exists()
        if close is None and (expired or stopped or problem):
            reason = 'timeout' if expired else 'STOP' if stopped else 'lease_or_source_failure'
            try:
                windows = request_window_close(child.pid)
                close = {'at_utc': utc(), 'reason': reason, 'windows': windows,
                         'normal_gui_quit': False, 'business_pass': False}
            except Exception as error:
                close = {'at_utc': utc(), 'reason': reason, 'error': repr(error), 'normal_gui_quit': False}
            write_new(root / 'window-close-request.json', close)
            close['requested_monotonic'] = now
        if close and now - close['requested_monotonic'] > budgets['quit_timeout'] and not (root / 'ROOT_STOP_REQUIRED.json').exists():
            write_new(root / 'ROOT_STOP_REQUIRED.json', {'at_utc': utc(), 'pid': child.pid,
                'reason': 'Original CK3 still running; retained handle and lease kept until operator closes it',
                'normal_gui_quit': False, 'business_pass': False})
        time.sleep(budgets['poll_interval'])
    code = child.wait()
    return {'at_utc': utc(), 'pid': child.pid, 'returncode': code, 'actual_original_popen_wait': True,
            'window_close_requested': close is not None, 'error': problem,
            'process_pass': code == 0 and close is None and problem is None,
            'normal_gui_quit': None, 'business_pass': False}


def run(selection):
    require(selection.context and selection.prepared, 'Allocated context and prepared case required')
    context = selection.context
    check_pin(context['prepared_case']); check_pin(context['implementation'])
    require(context['prepared_case'] == pin(selection.args.prepared_case), 'Allocated prepared case differs')
    root = Path(context['run_dir'])
    require(not (root / 'game-started.json').exists(), 'Run already consumed')
    require(getattr(selection.args, 'gui_review', None), 'run requires --gui-review')
    checked = selection.preflight()
    require(checked['lease_head'] == context['lease_head'] and checked['source_head'] == context['source_head'],
            'Frozen checkout HEAD changed')
    review = validate_review(selection, selection.args.gui_review)
    module, source, bus, sha, repo = selection.lease()
    abort = threading.Event()
    keeper = module.ScreenLeaseKeeper(source=source, bus_dir=bus, expected_sha=sha,
        task_id=context['screen_task'], sequence=context['sequence'], repo=repo,
        journal=root / 'lease-journal.jsonl', abort=abort, interval_seconds=180,
        audit_dir=root / 'lease-audit')
    # This source path belongs to the selected shared runtime, never the product.
    import_root = selection.paths['repo_root'] / 'ck3_autonomous_player/src'
    sys.path.insert(0, str(import_root))
    from xar_autoplayer.locking import exclusive_launch_lock
    child = None
    exited = None
    failure = None
    try:
        keeper.start()
        with exclusive_launch_lock(selection.exe):
            with keeper.process_create_gate():
                require(not ck3_pids(), 'CK3 already running at process creation')
                profile = Path(selection.prepared['profile'])
                argv = [str(selection.exe), '-userdir=' + str(profile)]
                if selection.prepared['case_inputs'].get('debug_mode', False):
                    argv.append('-debug_mode')
                module.call_bus(source, bus, sha, 'poll', '--task', context['screen_task'], '--ack')
                with (root / 'stdout.log').open('xb') as stdout, (root / 'stderr.log').open('xb') as stderr:
                    child = subprocess.Popen(argv, cwd=selection.exe.parent, stdout=stdout, stderr=stderr)
                write_new(root / 'game-started.json', {'at_utc': utc(), 'run_id': context['run_id'],
                    'pid': child.pid, 'argv': argv, 'retained_original_popen': True,
                    'native_injection': False, 'language': 'simp_chinese', 'review': review})
            def frozen_source():
                require(module.checkout_head(repo) == context['lease_head'], 'Frozen lease checkout changed')
                require(module.checkout_head(selection.paths['repo_root']) == context['source_head'],
                        'Frozen shared source changed')
                if selection.prepared.get('product_source'):
                    item = selection.prepared['product_source']
                    require(module.checkout_head(Path(item['repo'])) == item['head'], 'Frozen product source changed')
            exited = wait_original(child, root, selection.budgets, keeper, frozen_source)
            write_new(root / 'game-exit.json', exited)
    except BaseException as error:
        failure = repr(error)
        if child is not None and child.poll() is None:
            # Never lose the original handle or terminate the game to invent OS0.
            (root / 'STOP').touch(exist_ok=True)
            exited = wait_original(child, root, selection.budgets, keeper, lambda: None)
            exited['error'] = failure
            exited['process_pass'] = False
            if not (root / 'game-exit.json').exists():
                write_new(root / 'game-exit.json', exited)
        elif child is not None and not (root / 'game-exit.json').exists():
            exited = {'at_utc': utc(), 'pid': child.pid, 'returncode': child.wait(),
                      'actual_original_popen_wait': True, 'process_pass': False,
                      'error': failure, 'business_pass': False}
            write_new(root / 'game-exit.json', exited)
    finally:
        keeper.stop()
        report = keeper.report()
        write_new(root / 'keeper-report.json', report)
        if not ck3_pids() and report['thread_exited']:
            release = module.call_bus(source, bus, sha, 'release-screen-cas', '--task', context['screen_task'],
                '--expected-sequence', str(report['last_sequence']), '--summary', 'GUI-only original process closed')
            write_new(root / 'screen-release.json', release)
        sys.path.remove(str(import_root))
    return {'status': 'COMPLETED' if exited and exited['process_pass'] and not failure else 'RED',
            'process': exited, 'error': failure, 'business_pass': False, 'native_injection': False}


def verify(selection):
    require(selection.context, 'Allocated run context required')
    root = Path(selection.context['run_dir'])
    process = read_json(root / 'game-exit.json') if (root / 'game-exit.json').exists() else {}
    start = read_json(root / 'game-started.json') if (root / 'game-started.json').exists() else {}
    process_pass = (process.get('process_pass') is True and process.get('actual_original_popen_wait') is True and
                    process.get('pid') == start.get('pid') and start.get('run_id') == selection.context['run_id'])
    closure = False
    if (root / 'keeper-report.json').exists() and (root / 'screen-release.json').exists():
        keeper = read_json(root / 'keeper-report.json')
        release = read_json(root / 'screen-release.json')
        closure = keeper.get('thread_exited') is True and keeper.get('failure') is None and release.get('ok') is True
    review_path = root / 'business-review.json'
    business = False
    reviewed = []
    if review_path.exists():
        review = read_json(review_path)
        require(review.get('run_id') == selection.context['run_id'] and
                review.get('case') == selection.args.case and review.get('direct_image_review') is True and
                isinstance(review.get('reviewer'), str) and review['reviewer'].strip(),
                'Business review must bind the actual run/case and reviewer')
        required = selection.case['required_business_evidence']
        require(isinstance(required, list) and required and len(required) == len(set(required)), 'Explicit case evidence keys required')
        facts = review.get('facts', {})
        for key in required:
            fact = facts.get(key, {})
            require(fact.get('passed') is True and fact.get('evidence'), 'Missing or failed business evidence: ' + key)
            reviewed.extend(check_pin(row) for row in fact['evidence'])
        require(review.get('normal_gui_quit') is True and review.get('normal_quit_evidence'),
                'Actual normal in-game Quit evidence required')
        reviewed.extend(check_pin(row) for row in review['normal_quit_evidence'])
        business = review.get('passed') is True
    passed = bool(process_pass and closure and business)
    return {'status': 'PASS' if passed else 'INCOMPLETE', 'process_pass': bool(process_pass),
            'closure_pass': closure, 'gui_business_pass': business, 'case_acceptance_pass': passed,
            'business_pass': passed, 'product_release_pass': False, 'native_capability_pass': False,
            'evidence': reviewed}


def dispatch(args):
    """Public main delegates here only for its selected global GUI manifest."""
    selection = GuiSelection(args)
    if args.mode == 'plan':
        return {'execution_mode': 'gui_only', 'runtime_manifest': selection.manifest_ref,
                'product': args.product, 'case': args.case, 'budgets': selection.budgets,
                'required_business_evidence': selection.case['required_business_evidence'],
                'runtime_status': 'NOT_RUN', 'business_pass': False}
    if args.mode == 'preflight':
        return selection.preflight()
    return {'prepare': prepare, 'allocate': allocate, 'run': run, 'verify': verify}[args.mode](selection)
