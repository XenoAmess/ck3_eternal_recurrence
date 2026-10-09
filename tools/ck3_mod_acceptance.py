"""Select one shared CK3 runtime, inspect a product case, or launch its frozen host.

This entry delegates Steam review, keeper custody, launch and normal cleanup to
the existing reviewed launcher and shared host. Host exit is not product signoff.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys


RUNTIME_SCHEMA = "ck3-mod-acceptance-runtime-v1"
MANIFEST_SCHEMA = "ck3-mod-acceptance-shared-runtime-v1"
PRODUCTS_SCHEMA = "ck3-mod-acceptance-products-v1"
CONTEXT_SCHEMA = "ck3-mod-acceptance-run-context-v1"
BUDGET_FLAGS = {
    "command_timeout": "--command-timeout", "readiness_timeout": "--readiness-timeout",
    "timeout": "--timeout", "poll_interval": "--poll-interval", "hold_seconds": "--hold-seconds",
}
SAVED_FLAGS = {
    "save": "--saved-campaign-save", "bytes": "--saved-campaign-save-bytes",
    "sha256": "--saved-campaign-save-sha256", "player_id": "--saved-campaign-player-id",
    "date_raw": "--saved-campaign-date-raw", "product_inventory": "--saved-campaign-product-inventory",
}
SHA = re.compile(r"^[0-9a-fA-F]{64}$")


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def path_at(value: str, base: Path) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("Nonempty path required")
    path = Path(value)
    return (path if path.is_absolute() else base / path).resolve()


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def check_pin(path: Path, expected: dict) -> dict:
    if type(expected.get("bytes")) is not int or not SHA.fullmatch(str(expected.get("sha256", ""))):
        raise ValueError(f"Exact bytes/SHA required: {path}")
    actual = pin(path)
    if actual["bytes"] != expected["bytes"] or actual["sha256"] != expected["sha256"].lower():
        raise ValueError(f"Pinned input changed: {path}")
    return actual


def host_cli_flags(path: Path) -> set[str]:
    """Inspect declared argparse flags without importing or starting the host."""
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    return {
        argument.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        for argument in node.args
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
        and argument.value.startswith("--")
    }


class Selection:
    def __init__(self, runtime_path: Path, products_path: Path, product_key: str,
                 case_id: str, context_path: Path | None = None, prepared_path: Path | None = None):
        self.runtime_path = runtime_path.resolve()
        self.products_path = products_path.resolve()
        self.runtime = read_json(self.runtime_path)
        self.products = read_json(self.products_path)
        if self.runtime.get("schema") != RUNTIME_SCHEMA or self.products.get("schema") != PRODUCTS_SCHEMA:
            raise ValueError("Unsupported runtime/products schema")
        base = self.runtime_path.parent
        self.blockers: list[str] = []
        def configured(key, value):
            if value is None:
                self.blockers.append("Shared machine path unbound: " + key)
                return base / ("<unbound-" + key + ">")
            return path_at(value, base)
        self.paths = {key: configured(key, value) for key, value in self.runtime.get("paths", {}).items()}
        self.locations = {key: configured(key, self.runtime[key]) for key in
                          ("python", "repo_root", "game_dir", "userdir_root", "artifacts_root")}
        manifest_ref = self.runtime["manifest"]
        self.manifest_path = path_at(manifest_ref["path"], base)
        self.manifest = read_json(self.manifest_path)
        if self.manifest.get("schema") != MANIFEST_SCHEMA:
            raise ValueError("Unsupported shared runtime manifest schema")
        self.product_key = product_key
        self.product = self.products["products"][product_key]
        cases = ([self.products["workshop_cache_case"]] if case_id == "workshop_cache"
                 else [case for case in self.product["cases"] if case["id"] == case_id])
        if len(cases) != 1:
            raise ValueError("Exactly one product case required")
        self.case = json.loads(json.dumps(cases[0]))
        self.prepared_path = prepared_path.resolve() if prepared_path else None
        self.prepared = read_json(self.prepared_path) if self.prepared_path else None
        if self.prepared:
            if self.prepared.get('schema') != 'ck3-mod-acceptance-prepared-case-v1' or (
                    self.prepared.get('product') != product_key or self.prepared.get('case') != case_id):
                raise ValueError('Prepared case belongs to another product/case')
            if self.prepared.get('runtime_manifest') != pin(self.manifest_path):
                raise ValueError('Prepared case selected another shared runtime')
            self.case['startup'].update(self.prepared['startup'])
            if self.prepared.get('initial_plan'):
                self.case['initial_plan'] = self.prepared['initial_plan']
        for forbidden in ("host", "source_root", "source_index", "native", "dll", "injector", "engine", "host_args", "host_features"):
            if forbidden in self.product or forbidden in self.case:
                raise ValueError(f"Product case cannot select shared runtime: {forbidden}")
        self.context_path = context_path.resolve() if context_path else None
        self.context = read_json(self.context_path) if self.context_path else {}
        if self.context and self.context.get("schema") != CONTEXT_SCHEMA:
            raise ValueError("Unsupported actual run context schema")
        inputs=self.prepared.get('case_inputs',{}) if self.prepared else self.context.get('case_inputs',{})
        for key,value in inputs.get('budgets',{}).items():
            if key not in BUDGET_FLAGS or self.case['budgets'].get(key) is not None:
                raise ValueError('Budget latebinding can only fill a declared null field: '+key)
            if type(value) not in (int,float) or value<0 or value==0 and key!='hold_seconds':
                raise ValueError('Invalid explicit shared case budget: '+key)
            self.case['budgets'][key]=value
        run_id = self.context.get("run_id", "<allocated-run-id>")
        if self.context and (not isinstance(run_id, str) or not run_id or Path(run_id).name != run_id):
            raise ValueError("Actual allocated run_id required")
        self.run_dir = path_at(self.context["run_dir"], self.context_path.parent) if self.context else self.locations["artifacts_root"] / run_id
        self.values = {key: str(value) for key, value in self.locations.items()}
        self.values.update(run_id=run_id, run_dir=str(self.run_dir))
        self.runtime_environment = {}
        for key, value in self.runtime.get("runtime_environment", {}).items():
            if key == "PYTHONPATH":
                if not isinstance(value, list):
                    raise ValueError("Runtime PYTHONPATH must be explicit path strings")
                self.runtime_environment[key] = os.pathsep.join(str(path_at(item, base)) for item in value)
            elif key in ("PYTHONUTF8", "PYTHONDONTWRITEBYTECODE") and value == "1":
                self.runtime_environment[key] = value
            else:
                raise ValueError("Only shared Python import environment is configured here")
        declared_environment = self.manifest.get("entry_environment", {})
        if declared_environment:
            parts = []
            for row in declared_environment["PYTHONPATH_parts"]:
                parts.append(self.paths[row["path_key"]] if "path_key" in row else
                             self.paths[row["root_key"]] / row["relative_path"])
            shared_environment = {"PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1",
                                  "PYTHONPATH": os.pathsep.join(map(str, parts))}
            if self.runtime_environment and self.runtime_environment != shared_environment:
                raise ValueError("Machine Python environment differs from the one shared manifest")
            self.runtime_environment = shared_environment
        self.required_pins: list[tuple[Path, dict]] = [(self.manifest_path, manifest_ref)]
        if self.prepared_path:
            self.required_pins.append((self.prepared_path, pin(self.prepared_path)))
        adapter = self.case.get('adapter')
        if adapter:
            if 'path' in adapter:self.adapter_path = self.case_path(adapter['path'])
            else:
                module=adapter['module']
                if not re.fullmatch(r'tools\.ck3_mod_acceptance_cases\.[a-z0-9_]+',module):
                    raise ValueError('Adapter module must name product case data below tools')
                self.adapter_path=self.locations['repo_root']/Path(*module.split('.')).with_suffix('.py')
            self.adapter_config = self.locations['repo_root']/adapter['config'] if adapter['config'].startswith('tools/') else self.case_path(adapter['config'])
        else:
            self.adapter_path = self.adapter_config = None
        self.argv = self.build_argv()

    def manifest_path_key(self, row: dict) -> Path:
        key = row["path_key"]
        if key not in self.paths:
            raise ValueError(f"Shared runtime path_key missing from machine config: {key}")
        return self.paths[key]

    def shared_file(self, row: dict | None, name: str = "") -> Path:
        if row is None:
            self.blockers.append("Shared manifest pin unbound: " + name)
            return self.paths[name]
        path = self.manifest_path_key(row)
        self.required_pins.append((path, row))
        return path

    def expand(self, text: str) -> str:
        try:
            return text.format_map(self.values)
        except KeyError as error:
            raise ValueError(f"Unknown product path template: {error.args[0]}") from None

    def case_path(self, reference: str | dict) -> Path:
        text = reference["path"] if isinstance(reference, dict) else reference
        path = path_at(self.expand(text), self.products_path.parent)
        if isinstance(reference, dict):
            self.required_pins.append((path, reference))
        return path

    def build_argv(self) -> list[str]:
        host = self.shared_file(self.manifest["host"], "host")
        source = self.manifest_path_key(self.manifest["source_root"])
        for name in ("source_index", "native_source_index"):
            self.shared_file(self.manifest[name], name)
        for row in self.manifest.get("imports", []):
            self.shared_file(row["index"])
        native = self.manifest["native"]
        dll, injector = self.shared_file(native["dll"]), self.shared_file(native["injector"])
        startup = self.case["startup"]
        state = self.case_path(startup["state_dir"])
        self.state_dir = state
        pipe = "\\\\.\\pipe\\ck3_mod_acceptance_" + self.values["run_id"]
        argv = [str(self.locations["python"]), "-B", "-X", "utf8", str(host),
                "--agent-source-root", str(source), "--game-dir", str(self.locations["game_dir"]),
                "--bridge-dll", str(dll), "--bridge-injector", str(injector),
                "--bridge-pipe", pipe, "--output", str(self.run_dir / "native-report.json"),
                "--state-dir", str(state), "--plan", str(self.case_path(self.case["initial_plan"])),
                "--control-plan-dir", str(self.run_dir / "controls")]
        features = self.manifest.get("host_features", {})
        if not isinstance(features, dict) or set(features) - {"succession_title_readonly"}:
            raise ValueError("Unknown shared host feature")
        if any(type(value) is not bool for value in features.values()):
            raise ValueError("Shared host features require explicit booleans")
        if features.get("succession_title_readonly"):
            argv += ["--private-succession-title-readonly"]
        budgets = self.case["budgets"]
        for key, flag in BUDGET_FLAGS.items():
            value = budgets[key]
            if value is None:
                self.blockers.append('Original case budget unbound: '+key)
                continue
            if type(value) not in (int, float) or value < 0 or (value == 0 and key != "hold_seconds"):
                raise ValueError(f"Invalid original case budget: {key}")
            argv += [flag, str(value)]
        if startup["mode"] == "fixture":
            argv += ["--fixture-profile", "--frontend-robert-bootstrap", "--frontend-fixture-start-policy",
                     str(self.case_path(startup["fixture_start_policy"]))]
            if startup.get("frontend_rules_plan"):
                argv += ["--frontend-rules-plan", str(self.case_path(startup["frontend_rules_plan"]))]
            if startup.get('startup_case_contract'):
                argv += ['--frontend-fixture-startup-case-contract',str(self.case_path(startup['startup_case_contract']))]
        elif startup["mode"] == "workshop_cache":
            argv += ["--fixture-profile", "--frontend-mod-load-observation"]
        elif startup["mode"] == "saved_campaign":
            argv += ['--fixture-profile']
            saved = dict(startup["saved_campaign"])
            for key, value in self.context.get("saved_campaign", {}).items():
                if key not in SAVED_FLAGS or saved.get(key) is not None:
                    raise ValueError(f"Saved latebinding can only fill a declared null field: {key}")
                saved[key] = value
            for key, flag in SAVED_FLAGS.items():
                value = saved.get(key)
                if value is None:
                    self.blockers.append(f"Saved campaign input unbound: {key}")
                    continue
                if key in ("save", "product_inventory"):
                    value = str(self.case_path(value))
                elif key in ("bytes", "player_id", "date_raw"):
                    if type(value) is not int or value <= 0:
                        raise ValueError(f"Positive saved integer required: {key}")
                elif not SHA.fullmatch(str(value)):
                    raise ValueError("Saved campaign exact SHA required")
                argv += [flag, str(value)]
            self.saved = saved
        else:
            raise ValueError("Only existing fixture, saved_campaign and workshop_cache startup modes are supported")
        return argv

    def describe(self) -> dict:
        return {"schema": "ck3-mod-acceptance-plan-v1", "product": self.product_key,
                "case": self.case["id"], "case_status": self.case.get("status"),
                "shared_manifest": str(self.manifest_path), "run_id": self.values["run_id"],
                "host_argv": self.argv, "required_mcp_tools": self.case.get("required_mcp_tools", []),
                "runtime_environment": self.runtime_environment,
                "phases": self.case.get("phases", []), "budgets": self.case["budgets"],
                "fixture_prepare": self.case.get("fixture_prepare"),
                "adapter": self.case.get('adapter'),
                "normal_close": self.case.get("normal_close"), "gui_contract": self.case.get("gui_contract"),
                "outputs": self.case.get("outputs"), "blockers": list(self.blockers),
                "runtime_status": "NOT_RUN", "business_acceptance": "NOT_ASSESSED"}

    def preflight(self) -> dict:
        checks = []
        errors = list(self.blockers)
        for path, expected in self.required_pins:
            try:
                checks.append(check_pin(path, expected))
            except (OSError, ValueError) as error:
                errors.append(str(error))
        for key in ("python", "repo_root", "game_dir", "userdir_root"):
            if not self.locations[key].exists():
                errors.append(f"Configured location missing: {key}: {self.locations[key]}")
        host = self.paths["host"] if self.manifest["host"] is None else self.manifest_path_key(self.manifest["host"])
        try:
            missing = sorted({value for value in self.argv if value.startswith("--")} - host_cli_flags(host))
            if missing:
                errors.append("Selected canonical host lacks declared CLI: " + ", ".join(missing))
        except (OSError, SyntaxError) as error:
            errors.append(str(error))
        game = self.manifest["game"]
        exe = self.locations["game_dir"] / "binaries" / "ck3.exe"
        try:
            identity = pin(exe)
            if identity["sha256"] != game["exe_sha256"].lower():
                errors.append("Actual installed game differs from the one shared manifest")
            checks.append(identity)
        except OSError as error:
            errors.append(str(error))
        for flag in ("--plan", "--frontend-fixture-start-policy", "--frontend-rules-plan",
                     "--saved-campaign-save", "--saved-campaign-product-inventory",'--frontend-fixture-startup-case-contract'):
            if flag in self.argv:
                path = Path(self.argv[self.argv.index(flag) + 1])
                if not path.is_file():
                    errors.append(f"Prepared case input missing: {flag}: {path}")
        if "--frontend-fixture-start-policy" in self.argv:
            source = self.manifest_path_key(self.manifest["source_root"])
            import_root = source / "ck3_autonomous_player" / "src"
            if not import_root.is_dir():
                import_root = source / "src"
            sys.path.insert(0, str(import_root))
            try:
                contract = importlib.import_module("xar_autoplayer.bridge.frontend_fixture_start_contract")
                if not Path(contract.__file__).resolve().is_relative_to(import_root.resolve()):
                    raise ValueError("Fixture validator import differs from the selected shared source")
                policy = Path(self.argv[self.argv.index("--frontend-fixture-start-policy") + 1])
                contract.validate_fixture_start_policy(read_json(policy))
            except (ImportError, OSError, ValueError) as error:
                errors.append("Selected shared fixture policy validator: " + str(error))
            finally:
                sys.path.remove(str(import_root))
        capabilities = self.manifest.get("capabilities", {})
        tool_status = {}
        for tool in self.case.get("required_mcp_tools", []):
            status = capabilities.get(tool)
            tool_status[tool] = status
            if not status or status.get("source_build_ready") is not True:
                errors.append(f"Required MCP tool has no shared build-ready evidence: {tool}")
        if self.case.get("status") != "ready":
            errors.append("Product case is explicitly blocked; preserve its pending adapter/contract")
        if self.adapter_path:
            try:
                checks.extend((check_pin(self.adapter_path,self.prepared['adapter']),check_pin(self.adapter_config,self.prepared['contract']))
                              if self.prepared else (pin(self.adapter_path),pin(self.adapter_config)))
                module = self.load_adapter()
                for name in ('prepare_case','run_case','verify_case'):
                    if not callable(getattr(module,name,None)):
                        errors.append('Actual case adapter lacks '+name)
                if callable(getattr(module,'validate_contract',None)):
                    module.validate_contract(self.adapter_context())
            except (ImportError,OSError,ValueError) as error:
                errors.append('Case adapter: '+str(error))
        if '--frontend-fixture-startup-case-contract' in self.argv:
            try:
                hook_path=Path(self.argv[self.argv.index('--frontend-fixture-startup-case-contract')+1]);hook=read_json(hook_path)
                if set(hook)!={'schema','state_dir','handler','dependencies'} or hook['schema']!='ck3-frontend-fixture-startup-case-contract-v1':
                    raise ValueError('Unsupported startup-case contract')
                if Path(hook['state_dir']).resolve()!=self.state_dir.resolve() or hook['handler']['function']!='admit_startup_event':
                    raise ValueError('Startup-case handler crossed actual prepared state/function')
                for row in [hook['handler'],*hook['dependencies']]:checks.append(check_pin(Path(row['path']),row))
            except (OSError,KeyError,ValueError) as error:errors.append('Startup-case contract: '+str(error))
        if self.context:
            try:
                frozen_ref = self.context["frozen_argv"]
                frozen_path = path_at(frozen_ref["path"], self.context_path.parent)
                checks.append(check_pin(frozen_path, frozen_ref))
                frozen = read_json(frozen_path)
                if frozen["run_id"] != self.values["run_id"] or frozen.get("argv") != self.argv:
                    errors.append("Actual allocated frozen argv differs from the one shared runtime/case selection")
                if frozen.get("runtime_environment", {}) != self.runtime_environment:
                    errors.append("Actual frozen shared Python environment differs from runtime config")
            except (KeyError, OSError, ValueError) as error:
                errors.append(str(error))
        if hasattr(self, "saved") and all(self.saved.get(key) is not None for key in SAVED_FLAGS):
            try:
                checks.append(check_pin(self.case_path(self.saved["save"]), self.saved))
            except (OSError, ValueError) as error:
                errors.append(str(error))
        result = self.describe()
        result.update(status="BLOCKED" if errors else "READY_FOR_EXISTING_REVIEWED_LAUNCH",
                      blockers=errors, checked_inputs=checks, tool_status=tool_status,
                      capability_limit="Source/build evidence only; actual live tool and product gates remain mandatory")
        return result

    def load_adapter(self):
        if not self.adapter_path:
            raise ValueError('Product case has no implemented business adapter')
        # All product modules share the public client/prepare package. Runtime
        # source, native bridge and host never come from these modules.
        repo=str(self.locations['repo_root'])
        if repo not in sys.path:sys.path.insert(0,repo)
        sys.path.insert(0,str(self.adapter_path.parent.parent))
        try:
            package=importlib.import_module('ck3_mod_acceptance_cases')
            if str(self.adapter_path.parent) not in package.__path__:
                package.__path__.append(str(self.adapter_path.parent))
            spec=importlib.util.spec_from_file_location('ck3_mod_acceptance_cases.'+self.adapter_path.stem,self.adapter_path)
            module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
            spec.loader.exec_module(module)
            return module
        finally:
            sys.path.remove(str(self.adapter_path.parent.parent))

    def adapter_context(self, output=None, inputs=None):
        case_inputs = inputs if inputs is not None else self.prepared.get('case_inputs',{}) if self.prepared else self.context.get('case_inputs',{})
        return {'repo_root':str(self.locations['repo_root']),'run_dir':str(self.run_dir),
            'state_dir':str(self.state_dir),'output':str(output or self.run_dir/'case-output'),
            'run_id':self.context.get('run_id'),'game_dir':str(self.locations['game_dir']),
            'product':self.product_key,'case':self.case['id'],'case_spec':self.case,
            'shared_source_root':str(self.manifest_path_key(self.manifest['source_root'])),
            'shared_game':self.manifest['game'],'case_contract':read_json(self.adapter_config),
            'product_spec':self.product,'canonical_products_path':str(self.case_path(self.products['product_inventory'])),
            'case_inputs':case_inputs,'saved_campaign':self.prepared.get('startup',{}).get('saved_campaign',{}) if self.prepared else self.context.get('saved_campaign',{}),
            'runtime_manifest':pin(self.manifest_path)}

    def prepare(self, inputs_path, output):
        if self.context:
            raise ValueError('Preparation precedes allocation; do not rewrite allocated input')
        if self.case.get('status')!='ready':
            raise ValueError('Explicitly blocked product adapter cannot prepare')
        inputs=read_json(inputs_path)
        for key,value in inputs.get('case_inputs',{}).get('budgets',{}).items():
            if key not in BUDGET_FLAGS or self.case['budgets'].get(key) is not None:
                raise ValueError('Prepare budget latebinding can only fill declared null fields: '+key)
            if type(value) not in (int,float) or value<0 or value==0 and key!='hold_seconds':
                raise ValueError('Invalid explicit shared case budget: '+key)
            self.case['budgets'][key]=value
        if any(v is None for v in self.case['budgets'].values()):
            raise ValueError('Preparation requires explicit binding of each declared null original budget')
        output=output.resolve()
        if output.exists():raise ValueError('New preparation output required; never replay')
        state=path_at(inputs['state_dir'],inputs_path.parent)
        if state.exists():raise ValueError('Unused prepared state required')
        output.mkdir(parents=True)
        context=self.adapter_context(output,inputs.get('case_inputs',{}))
        context.update(run_dir=str(output),state_dir=str(state),run_id=None)
        context['saved_campaign']=inputs.get('saved_campaign',{})
        result=self.load_adapter().prepare_case(context)
        from ck3_mod_acceptance_prepare import write_json
        prepared={'schema':'ck3-mod-acceptance-prepared-case-v1','product':self.product_key,'case':self.case['id'],
            'runtime_manifest':pin(self.manifest_path),'case_inputs':context['case_inputs'],
            'startup':result['startup'],'initial_plan':result.get('initial_plan',self.case['initial_plan']),
            'adapter':pin(self.adapter_path),'contract':pin(self.adapter_config),'preparation':result,
            'runtime_status':'NOT_RUN','business_acceptance':'NOT_ASSESSED'}
        path=output/'prepared-case.json';write_json(path,prepared)
        return {'status':'CASE_PREPARED_NOT_ALLOCATED_NOT_RUN','prepared_case':pin(path),'preparation':result}

    def verify(self):
        if not self.context:raise ValueError('Verify requires one actual allocated run context')
        context=self.adapter_context()
        result=self.load_adapter().verify_case(context)
        closed_path=Path(context['output'])/'normal-close-result.json'
        close=read_json(closed_path) if closed_path.is_file() else None
        result.update(normal_close=close)
        result['case_acceptance_pass']=bool(result.get('case_contract_qualified') is True and
            result.get('gui_contract_qualified') is True and close and close.get('normal_close_qualified') is True)
        # A case boundary or one core cell cannot certify the whole product.
        # Preserve the adapter's explicit business applicability and credit.
        result['qualified_boundary_pass']=result['case_acceptance_pass']
        result['business_pass']=bool(result.get('business_pass') is True and
                                    result.get('business_contract_applicable',True) is True and result['case_acceptance_pass'])
        result['product_release_pass']=False
        return result

    def run(self) -> dict:
        result = self.preflight()
        if result["blockers"]:
            raise ValueError("Preflight blocked: " + "; ".join(result["blockers"]))
        if not self.context:
            raise ValueError("Run requires actual allocated frozen argv and current reviewed launcher context")
        launcher_ref = self.runtime["reviewed_launcher"]
        launcher = path_at(launcher_ref["path"], self.runtime_path.parent)
        check_pin(launcher, launcher_ref)
        context = self.context
        for key in ("keeper_root", "proof", "challenge", "observed_nonce", "reviewer"):
            if not context.get(key):
                raise ValueError(f"Existing reviewed launcher context missing: {key}")
        argv = [str(self.locations["python"]), "-B", "-X", "utf8", str(launcher),
                "--run-root", str(self.run_dir), "--keeper-root", str(path_at(context["keeper_root"], self.context_path.parent)),
                "--proof", str(path_at(context["proof"], self.context_path.parent)),
                "--challenge", str(path_at(context["challenge"], self.context_path.parent)),
                "--observed-nonce", context["observed_nonce"], "--reviewer", context["reviewer"]]
        environment = dict(os.environ)
        environment.update(self.runtime_environment)
        environment.update(PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        completed = subprocess.run(argv, cwd=self.locations["repo_root"], env=environment, check=False)
        result.update(status="REVIEWED_LAUNCHER_RETURNED" if completed.returncode == 0 else "LAUNCHER_FAILED",
                      launcher_argv=argv, launcher_exit_code=completed.returncode,
                      runtime_status="LAUNCH_REQUESTED" if completed.returncode == 0 else "LAUNCH_FAILED",
                      business_acceptance="NOT_ASSESSED")
        if completed.returncode==0 and self.adapter_path:
            from ck3_mod_acceptance_client import CaseClient,write_once
            client=CaseClient(self)
            adapter=self.load_adapter()
            context=self.adapter_context(client.output)
            failure=None
            try:
                client.wait_hold()
                result['case_result']=adapter.run_case(context,client)
            except BaseException as error:
                failure=type(error).__name__+': '+str(error)
                write_once(client.output/'case-error-preserved.json',{'error':failure,'run_id':self.context['run_id'],
                    'business_pass':False,'submitted_steps_never_replayed':True})
                result['case_error']=failure
            finally:
                try:
                    if client._handle is not None:
                        result['normal_close']=client.normal_close('business_failure_preserved' if failure else 'actual_case_evidence_recorded')
                except BaseException as error:
                    result['normal_close_error']=type(error).__name__+': '+str(error)
                    write_once(client.output/'normal-close-error-preserved.json',{'error':result['normal_close_error'],'business_pass':False})
                client.close_handle()
            result['business_acceptance']='RED_OR_INCOMPLETE' if failure else 'ACTUAL_EVIDENCE_REQUIRES_VERIFICATION'
            write_once(client.output/'entry-run-result.json',result)
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "prepare", "allocate", "preflight", "run", "verify"))
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--products", type=Path, required=True)
    parser.add_argument("--product", required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--run-context", type=Path)
    parser.add_argument('--prepared-case',type=Path)
    parser.add_argument('--case-inputs',type=Path)
    parser.add_argument('--prepare-output',type=Path)
    parser.add_argument('--attempt')
    parser.add_argument('--keeper-output',type=Path)
    parser.add_argument('--previous-live',type=Path)
    parser.add_argument('--previous-keeper',type=Path)
    parser.add_argument('--previous-release',type=Path)
    parser.add_argument('--latest-screen-release',type=Path)
    args = parser.parse_args(argv)
    try:
        selection = Selection(args.runtime, args.products, args.product, args.case, args.run_context,args.prepared_case)
        if args.mode=='prepare':
            if not args.case_inputs or not args.prepare_output:raise ValueError('prepare requires --case-inputs and --prepare-output')
            result=selection.prepare(args.case_inputs,args.prepare_output)
        elif args.mode=='allocate':
            from ck3_mod_acceptance_allocate import allocate_and_keep
            result=allocate_and_keep(selection,args)
        elif args.mode=='verify':result=selection.verify()
        else:result=selection.describe() if args.mode=='plan' else selection.preflight() if args.mode=='preflight' else selection.run()
    except (OSError, KeyError, ValueError, TypeError) as error:
        print(json.dumps({"status": "BLOCKED", "error": str(error), "runtime_status": "NOT_RUN",
                          "business_acceptance": "NOT_ASSESSED"}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    incomplete_verify = args.mode == 'verify' and result.get('case_acceptance_pass') is not True
    incomplete_close = (args.mode == 'run' and 'normal_close' in result and
                        (not isinstance(result['normal_close'], dict) or
                         result['normal_close'].get('normal_close_qualified') is not True))
    return 2 if (result.get("blockers") or result.get("launcher_exit_code", 0) or
                 result.get('case_error') or result.get('normal_close_error') or
                 incomplete_verify or incomplete_close) else 0


if __name__ == "__main__":
    raise SystemExit(main())
