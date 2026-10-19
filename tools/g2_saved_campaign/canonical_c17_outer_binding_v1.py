"""Future C17 outer wiring only. No Task registration, Game launch, or global MCP patch.

All functions that acquire custody require an explicit source-enabled caller.
The policy locates frozen inputs; inherited kernel resources establish custody.
"""
from contextlib import asynccontextmanager
import hashlib
import importlib
import json
import os
from pathlib import Path
import site
import sys
import threading

MACHINE = 'xenoamess-full-tower-eb9d2c1186'
CREATORS = {'canonical_native_provider_chain_v1.py': '54475da0a10dce93fe306880df502e977cd41c056195b3a429bd7465e79a1ef4',
    'mcp_owned_stdio_binding_v1.py': 'a893edf1c792e73ce9e405c6d6f3e83de8adb4e89eaac8e21b8f805db6c01f08',
    'sdk_process_custody.py': '55e4409b2b0920085d432cd4a7ef9eef316a49762856db33e07d802128c274cc'}


def require(ok, why):
    if not ok:
        raise ValueError('C17 canonical outer binding denied: ' + why)


def checked(ref, limit=1048576):
    path = Path(ref['path']).resolve(strict=True)
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit and len(raw) == ref['bytes']
        and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'frozen input changed: ' + str(path))
    return json.loads(raw)


class OuterBindingV1:
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)
        self.freeze = json.loads((self.root / 'ROOT-FINAL-SDK-FREEZE-P37C17.json').read_bytes())
        self.policy = checked(self.freeze['canonical_preload_policy'])
        require(self.freeze['machine_id'] == self.policy['machine_id'] == MACHINE
            and self.policy['schema'] == 'xar.c17.canonical-preload-policy/v1'
            and self.policy['generation'] == 'P37C17', 'source generation/machine differs')
        self.sdk_root = Path(self.freeze['source_root']).resolve(strict=True)
        require(self.sdk_root == Path(self.policy['sdk_source_root']).resolve(strict=True), 'immutable SDK root differs')
        self.tools_root = Path(self.policy['creator_tools_root']).resolve(strict=True)
        self.dependency_root = Path(self.policy['dependency_root']).resolve(strict=True)
        self.direct_python = Path(self.policy['direct_python']['path']).resolve(strict=True)
        checked_python = self.policy['direct_python']
        with self.direct_python.open('rb') as stream:
            raw = stream.read(16 * 1024**2 + 1)
        require(len(raw) == checked_python['bytes'] and len(raw) <= 16 * 1024**2
            and hashlib.sha256(raw).hexdigest() == checked_python['sha256'], 'direct Python source changed')
        require(self.direct_python == Path(sys._base_executable).resolve(strict=True)
            and Path(sys.executable).resolve(strict=True) == self.direct_python,
            'the actual creator must already be the direct base Python image')
        deps = checked(self.policy['dependency_sources'])
        require(deps['machine_id'] == MACHINE and Path(deps['root']).resolve(strict=True) == self.dependency_root
            and deps['mcp_version'] == '2.0.0', 'frozen dependency environment differs')
        for ref in deps['files']:
            path = Path(ref['path']).resolve(strict=True)
            require(path.is_relative_to(self.dependency_root), 'dependency file escaped admitted root')
            with path.open('rb') as stream:
                raw = stream.read(1048577)
            require(len(raw) <= 1048576 and len(raw) == ref['bytes']
                and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'dependency source changed')
        if str(self.dependency_root) not in sys.path:
            site.addsitedir(str(self.dependency_root))
        sys.path.insert(0, str(self.sdk_root))
        sys.path.insert(0, str(self.tools_root))
        self.result = self.io = self.control = self.factory = self.chain = self.plan = None
        self.owner = self.server_thread = None
        self.attempted = self.revoked = False
        required = {'root_native30_supervisor_c17.py', 'root_checkpoint_bootstrap_c17.py',
            'launch_sdk_p37c17_owner.py', 'root_p37c17_sdk_queue.py',
            'root_p37c17_mcp_entry.py', 'root_c17_canonical_outer.py'}
        require(required <= {Path(row[0]).name for row in self.policy['entry_source_pins']},
            'all actual outer entry/helper sources must belong to the creator closure')

    def tools(self):
        for name, digest in CREATORS.items():
            path = self.tools_root / 'g2_saved_campaign' / name
            require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'creator tool changed: ' + name)
            module_name = 'g2_saved_campaign.' + path.stem
            prior = sys.modules.get(module_name)
            require(prior is None or Path(prior.__file__).resolve() == path.resolve(),
                'foreign cached creator module: ' + module_name)
        module = importlib.import_module('g2_saved_campaign.canonical_native_provider_chain_v1')
        for name in CREATORS:
            actual = sys.modules.get('g2_saved_campaign.' + Path(name).stem)
            if actual is not None:
                require(Path(actual.__file__).resolve() == (self.tools_root / 'g2_saved_campaign' / name).resolve(),
                    'creator import did not use the frozen tools bundle')
        return module

    def verify_runtime_sources(self, host_root, final_root):
        require(Path(final_root).resolve() == self.sdk_root, 'creator SDK path differs')
        rows = {r['relative']: r for r in self.freeze['files']}
        for relative in ('xar_autoplayer/environment.py', 'xar_autoplayer/runtime.py'):
            host_ref = self.policy['host_input_pins'][relative]
            require(Path(host_ref['path']).resolve() == (Path(host_root) / relative).resolve(), 'Host input path differs')
            host_raw = Path(host_ref['path']).read_bytes()
            require(len(host_raw) == host_ref['bytes'] and hashlib.sha256(host_raw).hexdigest() == host_ref['sha256'],
                'fixed Host input changed')
            sdk_raw = (self.sdk_root / relative).read_bytes(); row = rows[relative]
            require(len(sdk_raw) == row['bytes'] and hashlib.sha256(sdk_raw).hexdigest() == row['sha256'],
                'new SDK runtime/environment is not the frozen source')

    def prepare_factory(self, dll_sha256):
        chain = self.tools()
        from xar_autoplayer.bridge.native_loaded_provider_windows_v1 import WindowsNativeCustodyFacadeV1
        self.factory = chain.CanonicalPreloadFactoryV1(facade=WindowsNativeCustodyFacadeV1(enabled=True),
            machine_id=MACHINE, expected_dll_sha256=dll_sha256,
            entry_source_pins=self.policy['entry_source_pins'], enabled=True)
        return self.factory

    def receive(self, role, argv):
        chain = self.tools()
        from xar_autoplayer.bridge.native_loaded_provider_windows_v1 import WindowsNativeCustodyFacadeV1
        clean, hints = chain.consume_private_bootstrap_args_v1(list(argv), enabled=True)
        require(isinstance(hints, dict) and hints.get('role') == role, 'actual created child private bootstrap required')
        self.result, self.io, self.control = chain.receive_child_bootstrap_v1(
            hints, facade=WindowsNativeCustodyFacadeV1(enabled=True), enabled=True)
        self.chain = chain
        sys.argv[:] = clean
        return self

    def child_env(self, original):
        env = dict(original)
        env['XAR_FRESH_SDK_DEPENDENCY_ROOT'] = str(self.dependency_root)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        return env

    def spawn_queue(self, argv, *, stdout, stderr):
        require(self.result is not None and self.result.holder._creation_role_v1 == 'owner', 'actual received owner required')
        command = [str(self.direct_python), '-B', '-S', '-X', 'utf8', *argv[4:]]
        self.plan = self.chain.prepare_child_v1(self.result.holder, role='Queue', command=command,
            env=self.child_env(os.environ), cwd=str(self.root), entry_source=command[5], enabled=True)
        edge = self.chain.spawn_owned_popen_v1(self.plan, stdout=stdout, stderr=stderr)
        self.chain.export_actual_child_chain_v1(self.result, self.io, self.control, edge)
        return self.plan.child

    def install_service(self, service):
        require(self.result is not None and self.result.holder._creation_role_v1 == 'MCPApp', 'actual received App required')
        self.chain.export_actual_child_chain_v1(self.result, self.io, self.control)
        self.owner = self.chain.install_received_provider_bootstrap_v1(service, self.result, enabled=True)

    def maybe_create_owner(self, game):
        gate_path = self.root / 'ROOT-C17-SDKOWNER-CREATE-ADMITTED.json'
        if self.attempted or not gate_path.exists():
            return
        gate = json.loads(gate_path.read_bytes())
        require(gate['machine_id'] == MACHINE and gate['schema'] == 'xar.c17.sdkowner-create-admission/v1',
            'source owner creation admission differs')
        launch = checked(gate['actual_game']); first = checked(gate['first_frame_admission'])
        require(launch['pid'] == game.pid and launch['creation_filetime'] == game.creation_filetime
            and first['status'] == 'GREEN' and first['reviewer'] == '/root'
            and first['game_pid'] == game.pid and first['game_creation_filetime'] == game.creation_filetime,
            'existing actual Root recording/map admission differs')
        checked(gate['owner_input_pins'])
        require(self.factory is not None and self.factory.holder is not None
            and self.factory.origin is not None, 'same actual pre-resume factory required')
        self.attempted = True
        self.server_thread = threading.Thread(target=self.factory.origin.serve,
            name='C17-canonical-origin', daemon=True)
        self.server_thread.start()
        entry = self.root / 'launch_sdk_p37c17_owner.py'
        command = [str(self.direct_python), '-B', '-S', '-X', 'utf8', str(entry)]
        chain = self.tools()
        self.plan = chain.prepare_child_v1(self.factory.holder, role='owner', command=command,
            env=self.child_env(os.environ), cwd=str(self.root), entry_source=str(entry), enabled=True)
        # Keep original Popen, inherited resource plan and exclusive log streams alive.
        self.owner_logs = ((self.root / 'C17-CANONICAL-OWNER.stdout.log').open('xb'),
                           (self.root / 'C17-CANONICAL-OWNER.stderr.log').open('xb'))
        edge = chain.spawn_owned_popen_v1(self.plan, stdout=self.owner_logs[0], stderr=self.owner_logs[1])
        self.factory.origin.bind_actual_chain(edge)

    def revoke(self):
        if self.factory is not None and self.factory.origin is not None and not self.revoked:
            self.factory.origin.revoke_before_close()
            self.revoked = True

    def close(self):
        if self.factory is not None:
            self.revoke()
            if self.plan is not None and self.plan.child is not None:
                # Original SDK pair shutdown already ran. Retain this new actual
                # ancestor on a timeout; never replace it or synthesize exit zero.
                self.plan.child.wait(timeout=5)
                for stream in self.owner_logs:
                    stream.close()
            return self.factory.close()
        if self.result is not None:
            if self.owner is not None:
                from xar_autoplayer.bridge.native_loaded_provider_custody_v1 import invalidate_loaded_native_provider_v1
                return invalidate_loaded_native_provider_v1(self.owner, reason='outer_entry_closed')
            return self.result.holder.close()


def prepare_supervisor(root, *, enabled=False):
    return OuterBindingV1(root) if enabled is True else None


def receive_entry(root, role, argv, *, enabled=False):
    return OuterBindingV1(root).receive(role, argv) if enabled is True else None


@asynccontextmanager
async def owned_stdio(binding, stock, params, *, errlog, capture_factory):
    if binding is None:
        async with capture_factory(stock, expected_executable=params.command) as captured:
            async with stock.stdio_client(params, errlog=errlog) as streams:
                yield streams, captured.require_generation()
        return
    binding.plan = binding.chain.prepare_child_v1(binding.result.holder, role='MCPApp',
        command=[params.command, *params.args], env=binding.child_env(params.env), cwd=params.cwd,
        entry_source=str(binding.root / 'root_p37c17_mcp_entry.py'), enabled=True)
    async with binding.chain.spawn_owned_mcp_v1(binding.plan, errlog=errlog) as (edge, streams, generation):
        binding.chain.export_actual_child_chain_v1(binding.result, binding.io, binding.control, edge)
        yield streams, generation
