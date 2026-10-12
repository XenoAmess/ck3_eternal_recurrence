"""Source13 data renderer; no compiler, process, or game actions."""
import hashlib
import json
import ntpath
import sys
from pathlib import Path

MAX_INPUT_BYTES = 64 * 1024 * 1024
MAX_ARGC = 2048
MAX_TOKEN_BYTES = 32768
REQUIRED_OBJECTS = 917
MANIFEST_QUALIFICATION = "draft/fresh_recipe_requires_root_review"
NATIVE88 = "D:/codex-ck3-background-spill/g2-native87-production01/attempt03"
CAND = "D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-resume-20261012/sdk85-source-preparation/sdk86-candidates"
FROZEN_METADATA = {
    "source11_legacy": CAND + "/m7-mailbox-argv-source11/WINDOWS-ARGV-DATA.json",
}

class RenderBlocked(ValueError):
    """A missing or conflicting proof blocks manifest rendering."""

def require(condition, message):
    if not condition:
        raise RenderBlocked(message)

def reject_constant(value):
    raise RenderBlocked("nonstandard JSON constant")

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result

def scalar_string(value, label, limit=MAX_TOKEN_BYTES):
    require(isinstance(value, str) and bool(value), label + " must be nonempty text")
    require("\x00" not in value and len(value.encode("utf-8")) <= limit, label + " contains NUL or exceeds byte limit")
    return value

def strict_integer(value, label, minimum=0):
    require(type(value) is int and value >= minimum, label + " must be an integer")
    return value

def windows_path(value, label):
    value = scalar_string(value, label)
    drive, _tail = ntpath.splitdrive(value)
    require(bool(drive) and ntpath.isabs(value), label + " must be an explicit absolute Windows path")
    return ntpath.normpath(value).replace("\\", "/").casefold()

def digest_text(value, label):
    require(isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value), label + " must be a lowercase SHA256")
    return value

def load_document(path, expected_sha256):
    """Read each explicit input once; bind decoded data to its exact bytes."""
    expected_sha256 = digest_text(expected_sha256, "input SHA256")
    path = Path(scalar_string(path, "input path"))
    require(path.stat().st_size <= MAX_INPUT_BYTES, "input exceeds 64 MiB")
    with path.open("rb") as handle:
        raw = handle.read(MAX_INPUT_BYTES + 1)
    require(len(raw) <= MAX_INPUT_BYTES, "input grew beyond 64 MiB")
    require(hashlib.sha256(raw).hexdigest() == expected_sha256, "input byte SHA256 mismatch")
    value = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique_object, parse_constant=reject_constant)
    require(isinstance(value, dict), "input JSON root must be an object")
    return value

def pointer_token(value):
    return str(value).replace("~", "~0").replace("/", "~1")

def decode_pointer_token(value):
    position = 0
    while position < len(value):
        if value[position] == "~":
            require(position + 1 < len(value) and value[position + 1] in "01", "invalid JSON pointer escape")
            position += 2
        else:
            position += 1
    return value.replace("~1", "/").replace("~0", "~")

def resolve_pointer(root, pointer):
    require(isinstance(pointer, str) and (pointer == "" or pointer.startswith("/")), "invalid JSON pointer")
    current = root
    if pointer == "":
        return current
    for raw in pointer[1:].split("/"):
        token = decode_pointer_token(raw)
        if isinstance(current, dict):
            require(token in current, "JSON pointer field missing")
            current = current[token]
        elif isinstance(current, list):
            require(token == "0" or token.isascii() and token.isdigit() and not token.startswith("0"), "invalid JSON pointer array locator")
            index = int(token)
            require(index < len(current), "JSON pointer locator outside array")
            current = current[index]
        else:
            raise RenderBlocked("JSON pointer traverses scalar")
    return current

def primary_identity(row):
    require(isinstance(row, dict), "object row must be an object")
    return (scalar_string(row.get("target"), "target"), ntpath.normpath(scalar_string(row.get("cpp"), "logical cpp")).replace("\\", "/").casefold(), windows_path(row.get("object_path"), "object_path"))

def validate_objects(document):
    rows = document.get("objects")
    require(isinstance(rows, list) and len(rows) == REQUIRED_OBJECTS, "lineage must contain exactly 917 objects")
    identities = [primary_identity(row) for row in rows]
    require(len(set(identities)) == REQUIRED_OBJECTS, "lineage primary identities are not unique")
    return rows

def typed_arguments(value, label):
    require(isinstance(value, list) and 0 < len(value) <= MAX_ARGC, label + " must be a nonempty bounded argument array")
    return [scalar_string(token, label + " token") for token in value]

class InputSnapshot:
    """Root input ids and exact pointers."""
    def __init__(self, declarations):
        require(isinstance(declarations, dict) and declarations, "Root input declarations")
        self.documents = {}
        self.references = {}
        for input_id, declaration in declarations.items():
            scalar_string(input_id, "input id", 256)
            require(isinstance(declaration, dict), "input declaration")
            path = declaration.get("path")
            windows_path(path, "input path")
            digest = declaration.get("sha256")
            if input_id in FROZEN_METADATA:
                require(windows_path(path, "input path") == windows_path(FROZEN_METADATA[input_id], "frozen input path"), "frozen input path")
            self.documents[input_id] = load_document(path, digest)
            self.references[input_id] = {"path": path, "sha256": digest}

    def resolve(self, reference):
        require(isinstance(reference, dict) and set(reference) == {"input_id", "pointer"}, "reference id and pointer")
        input_id = reference["input_id"]
        require(input_id in self.documents, "undeclared input")
        return resolve_pointer(self.documents[input_id], reference["pointer"])

    def proof(self, reference):
        self.resolve(reference)
        return {"input_id": reference["input_id"], "pointer": reference["pointer"], **self.references[reference["input_id"]]}

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

def value_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def scoped(path, root):
    key, base = windows_path(str(path), "write"), windows_path(str(root), "root")
    require(key.startswith(base.rstrip("/") + "/"), "write scope")
    return str(path)

def absolute(value, cwd):
    return ntpath.normpath(value if ntpath.isabs(value) else ntpath.join(cwd, value))

def source_sha(path):
    require(Path(path).stat().st_size <= MAX_INPUT_BYTES, "source size")
    with Path(path).open("rb") as handle: data = handle.read(MAX_INPUT_BYTES + 1)
    require(len(data) <= MAX_INPUT_BYTES, "source growth")
    return hashlib.sha256(data).hexdigest()

def map_path(value, cwd, rules, root, immutable=()):
    original = absolute(scalar_string(value, "operand"), cwd)
    key = windows_path(original, "operand"); found = []
    for rule in rules:
        require(isinstance(rule, list) and len(rule) == 2, "mapping pair")
        old, component = windows_path(rule[0], "old root"), scalar_string(rule[1], "component")
        require(not ntpath.isabs(component) and not ntpath.splitdrive(component)[0] and ".." not in component.replace("\\", "/").split("/"), "relative component")
        if key == old or key.startswith(old.rstrip("/") + "/"):
            found.append(ntpath.normpath(ntpath.join(root, component, ntpath.relpath(original, rule[0]))))
    require(len(found) <= 1, "mapping ambiguity")
    if found: return found[0]
    require(any(key == windows_path(path, "include") or key.startswith(windows_path(path, "include").rstrip("/") + "/") for path in immutable), "unmapped path")
    return original

def override_for(entries, identity):
    found = [entry for entry in entries if primary_identity(entry["actualowner_primary"]) == identity]
    require(len(found) <= 1, "owner override ambiguity")
    return found[0] if found else None

def operand_roles(argv, cwd, source):
    """Case-sensitive MSVC valued flags exclude their values from source operands."""
    roles = ["option"] * len(argv); roles[0] = "tool"
    located = {role: [] for role in ("source", "include", "object", "pdb", "deps", "other_write")}
    flags = {"/I": "include", "-I": "include", "/external:I": "include", "/FI": "include", "/FU": "include", "/AI": "include", "/Fo": "object", "/Fd": "pdb", "/sourceDependencies": "deps", "/Fp": "other_write", "/Fa": "other_write", "/Fe": "other_write", "/FR": "other_write", "/Fr": "other_write", "/D": "value", "-D": "value", "/U": "value", "-U": "value", "/Tc": "typed_source", "/Tp": "typed_source"}
    prefixes = sorted(flags, key=len, reverse=True); index = 1
    while index < len(argv):
        token = argv[index]
        require(not token.startswith("@") and not any(value in token for value in ("\x00", "\n", "\r")), "control/rsp token")
        if token in flags:
            require(index + 1 < len(argv), "missing option value")
            role = flags[token]; roles[index + 1] = "option_value"
            require(role != "typed_source", "typed source needs fresh override")
            if role in located: located[role].append((index + 1, "", argv[index + 1]))
            index += 2; continue
        prefix = next((flag for flag in prefixes if token.startswith(flag) and len(token) > len(flag)), None)
        if prefix:
            role = flags[prefix]
            require(role != "typed_source", "attached source needs fresh override")
            if role in located: located[role].append((index, prefix, token[len(prefix):]))
        elif not token.startswith(("/", "-")) or bool(ntpath.splitdrive(token)[0]) and ntpath.isabs(token):
            require(ntpath.splitext(token)[1].lower() in (".c", ".cc", ".cpp", ".cxx"), "unknown bare operand")
            located["source"].append((index, "", token)); roles[index] = "source_operand"
        index += 1
    require(len(located["source"]) == 1 and windows_path(absolute(located["source"][0][2], cwd), "source") == windows_path(source, "bound source"), "unique true source operand")
    return roles, located

def rewrite_compile(argv, cwd, old_source, new_source, job, policy, proof):
    require(sum(argv.count(flag) for flag in ("/c", "-c")) == 1 and not any(token.lower() in ("/link", "-link") or token.lower().startswith(("/ld", "-ld", "/fe", "-fe")) for token in argv), "compile-only grammar")
    original = list(argv); roles, positions = operand_roles(original, cwd, old_source)
    if proof is not None:
        require(isinstance(proof.get("original_tokens"), dict), "override token proofs")
        for position, token in proof["original_tokens"].items():
            require(isinstance(position, str) and position.isdigit() and int(position) < len(original) and original[int(position)] == token, "override original token")
        if "token_roles" in proof: require(proof["token_roles"] == roles, "override roles conflict")
    changes, includes = [], []
    def replace(position, prefix, value):
        changes.append({"original": original[position], "argv_index": position, "final": prefix + value})
        argv[position] = prefix + value
    source_index = positions["source"][0][0]; replace(source_index, "", new_source)
    for position, prefix, value in positions["include"]:
        mapped = map_path(value, cwd, policy["include_mapping_rules"], policy["_source_root"], policy.get("immutable_include_roots", []))
        require(prefix or original[position - 1] in ("/I", "-I", "/FI", "/external:I", "/FU", "/AI"), "include flag role")
        replace(position, prefix, mapped); includes.append(position if prefix else position - 1)
    for role, field, flag in (("object", "output", "/Fo"), ("pdb", "pdb_file", "/Fd"), ("deps", "dependencies_file", "/sourceDependencies")):
        require(len(positions[role]) <= 1, "multiple write operands")
        if positions[role]:
            position, prefix, _old = positions[role][0]; replace(position, prefix, job[field])
        else:
            require(role != "object" and policy.get("add_missing_" + role) is True, "missing write role policy")
            if role == "pdb": argv.append(flag + job[field])
            else: argv.extend((flag, job[field]))
            changes.append({"original": None, "argv_index": len(argv) - 1, "final": argv[-1], "policy_added_role": role})
    require(not positions["other_write"], "undeclared compiler write")
    final_roles, final = operand_roles(argv, job["cwd"], new_source)
    for role, field in (("object", "output"), ("pdb", "pdb_file"), ("deps", "dependencies_file")):
        require(len(final[role]) == 1 and windows_path(absolute(final[role][0][2], job["cwd"]), role) == windows_path(job[field], field), "private write operand")
    return argv, final_roles, source_index, includes, changes

def fresh_environment(settings, job):
    require(isinstance(settings, dict), "environment settings")
    environment = {}
    for name, setting in settings.items():
        require(isinstance(name, str) and name and "=" not in name and "\x00" not in name, "environment name")
        require(isinstance(setting, dict) and setting.get("state") in ("value", "unset", "empty"), "environment state")
        if setting["state"] == "value": require(isinstance(setting.get("value"), str) and "\x00" not in setting["value"], "environment value")
        environment[name] = dict(setting)
    require(len({name.casefold() for name in environment}) == len(environment), "environment case collision")
    for name in ("CL", "_CL_"): require(name in environment and environment[name]["state"] in ("unset", "empty"), "fresh CL policy")
    for name in ("TMP", "TEMP"):
        require(not any(key.casefold() == name.casefold() and key != name for key in environment), "TEMP case collision")
        environment[name] = {"state": "value", "value": job[name.lower()]}
    return environment

def make_job(root, job_id, bounds, settings, kind, index=None):
    directory = str(Path(root) / "jobs" / job_id)
    output = "native-p" + format(index, "04d") + ".obj" if kind == "compile" else "archive.lib" if kind == "archive" else "inspection.json" if kind == "archive_inspection" else "native.dll"
    job = {"job_id": job_id, "job_root": directory, "cwd": directory, "tmp": str(Path(directory) / "tmp"), "temp": str(Path(directory) / "temp"), "output": str(Path(directory) / output), "pdb_file": str(Path(directory) / ("compiler.pdb" if kind == "compile" else "linker.pdb")), "dependencies_file": str(Path(directory) / "dependencies.json"), "kind": kind}
    for name in ("memory_reserve_bytes", "output_reserve_bytes", "timeout_seconds"): job[name] = strict_integer(bounds.get(name), name, 1)
    for name in ("job_root", "cwd", "tmp", "temp", "output", "pdb_file", "dependencies_file"): scoped(job[name], root)
    job["environment"] = fresh_environment(settings, job)
    return job

def expand(template, replacements):
    argv = typed_arguments(template, "Root template"); result = []
    for token in argv:
        for name, value in replacements.items(): token = token.replace("{" + name + "}", value)
        require("{" not in token and "}" not in token, "unknown placeholder")
        result.append(token)
    return result

def tool_digest(argv, tools):
    matches = [tool for tool in tools if windows_path(tool["path"], "tool") == windows_path(argv[0], "argv tool")]
    require(len(matches) == 1, "Root unique tool")
    return digest_text(matches[0]["sha256"], "tool hash")

def token_sha(roles):
    require(all(role in ("tool", "option", "option_value", "source_operand", "input_operand", "defaultlib", "wholearchive", "responsefile") for role in roles), "token role")
    return value_sha(roles)

def row_proof(store, declarations, name, index):
    pointer = declarations[name].get("pointer", "").rstrip("/") + "/" + str(index)
    return store.proof({"input_id": name, "pointer": pointer})

def closure_job(spec, kind, ordinal, store, object_map, archive_map, config):
    record = store.resolve(spec["recipe_ref"])
    require(isinstance(record, dict) and isinstance(record.get("independent_refs"), list) and record["independent_refs"], "independent closure refs")
    recipe_proof = store.proof(spec["recipe_ref"])
    independent = [store.proof(ref) for ref in record["independent_refs"]]
    require(any(ref["pointer"] != recipe_proof["pointer"] or not Path(ref["path"]).samefile(recipe_proof["path"]) for ref in independent), "closure metadata self-reference")
    argv = typed_arguments(record.get("argv"), "actual closure tokens"); original = list(argv)
    cwd = scalar_string(record.get("cwd"), "closure cwd"); windows_path(cwd, "closure cwd")
    roles = record.get("option_roles")
    require(isinstance(roles, list) and len(roles) == len(argv) and roles[0] == "tool", "closure roles")
    token_sha(roles)
    require("responsefile" not in roles and not any(token.startswith("@") for token in argv), "expanded closure tokens required")
    job = make_job(config["output_root"], ("a" if kind == "archive" else "l") + format(ordinal, "04d"), spec.get("bounds", config["closure_defaults"]), config["environment_settings"], kind)
    immutable = record.get("immutable_inputs")
    require(isinstance(immutable, list), "immutable input list")
    frozen = {windows_path(item["path"], "immutable"): item for item in immutable}
    require(len(frozen) == len(immutable), "immutable duplicate")
    inputs, members, direct, selected, mappings, bindings, writes = [], [], [], [], [], [], set()
    for position, (token, role) in enumerate(zip(original, roles)):
        if position == 0: continue
        if role in ("input_operand", "wholearchive", "defaultlib"):
            require(not token.upper().startswith(("/OUT:", "/IMPLIB:", "/PDB:")), "write option is not input")
            prefix = "/WHOLEARCHIVE:" if role == "wholearchive" else "/DEFAULTLIB:" if role == "defaultlib" else ""
            require(not prefix or token.upper().startswith(prefix), "option input role")
            require(prefix or not token.startswith(("/", "-")) or bool(ntpath.splitdrive(token)[0]) and ntpath.isabs(token), "bare input operand")
            operand = token[len(prefix):] if prefix else token
            key = windows_path(absolute(operand, cwd), "closure input")
            if key in object_map:
                require(role == "input_operand", "bare object role")
                index, final = object_map[key]; (members if kind == "archive" else direct).append(index)
            elif key in archive_map:
                require(kind == "link", "archive nesting"); final = archive_map[key]; selected.append(key)
            else:
                binding = next((item for item in record.get("defaultlib_bindings", []) if item.get("token_index") == position - 1 and item.get("token") == token), None) if role == "defaultlib" else frozen.get(key)
                require(binding is not None, "exact external input binding")
                final = binding["path"]; digest_text(binding["sha256"], "immutable hash")
                require(windows_path(final, "bound library") in frozen, "immutable binding set")
                require(binding["sha256"] == frozen[windows_path(final, "library")]["sha256"], "immutable binding hash")
                if role == "defaultlib": bindings.append(dict(binding, token=token[:len(prefix)] + final))
            inputs.append(final); argv[position] = token[:len(prefix)] + final
            mappings.append({"original": token, "argv_index": position, "final": argv[position]})
        elif role == "option":
            prefix = next((value for value in ("/OUT:", "/IMPLIB:", "/PDB:") if token.upper().startswith(value)), None)
            if prefix:
                require(prefix not in writes, "duplicate output flag"); writes.add(prefix)
                final = job["output"] if prefix == "/OUT:" else str(Path(job["job_root"]) / "native.lib") if prefix == "/IMPLIB:" else job["pdb_file"]
                argv[position] = token[:len(prefix)] + final
                mappings.append({"original": token, "argv_index": position, "final": argv[position]})
        else: require(role == "option_value", "closure operand role")
    expected = scalar_string(spec.get("original_output"), "independent closure output")
    actual = [token[5:] for token, role in zip(original, roles) if role == "option" and token.upper().startswith("/OUT:")]
    require(len(actual) == 1 and windows_path(absolute(actual[0], cwd), "actual OUT") == windows_path(expected, "independent OUT"), "closure OUT identity")
    job.update({"argv": argv, "tool_sha256": digest_text(record["tool_sha256"], "actual tool hash"), "token_roles": roles, "mappings": mappings, "inputs": inputs, "immutable_inputs": immutable, "responsefiles": [], "original_argv": original, "recipe_ref": recipe_proof, "independent_refs": independent, "defaultlib_bindings": bindings})
    require(job["tool_sha256"] == tool_digest(argv, config["recipe_policy"]["tools"]), "Root closure tool match")
    if bindings: job["defaultlib_binding_receipt"] = config["approved_receipt_paths"]["defaultlib_bindings"][job["job_id"]]
    if kind == "archive": job["member_indices"] = members
    else: job.update({"direct_object_indices": direct, "selected_original_archives": selected})
    return job, windows_path(expected, "old archive")

def render_manifest(config, config_sha, config_path):
    require(config.get("schema") == "xar.native.parallel.render-config/v1", "render config schema")
    declarations = config.get("rootinput_refs")
    require(isinstance(declarations, dict) and len(declarations) <= 16 and all(key in declarations for key in ("lineage", "commands", "build_plan", "result", "sdk_freeze", "source11_legacy")), "Root input refs")
    for name, leaf in (("lineage", "ACTUAL-OBJECT-LINEAGE.json"), ("commands", "ACTUAL-COMPILE-COMMANDS.json"), ("build_plan", "ACTUAL-BUILD-PLAN.json"), ("result", "ROOT-NATIVE87-RESULT.json")):
        require(windows_path(declarations[name]["path"], name) == windows_path(NATIVE88 + "/" + leaf, "frozen Native88"), "actual Native88 path")
    store = InputSnapshot(declarations)
    views = {name: resolve_pointer(store.documents[name], ref.get("pointer", "")) for name, ref in declarations.items()}
    legacy = views["source11_legacy"]
    require(isinstance(legacy, dict) and isinstance(legacy.get("row_values"), list) and len(legacy["row_values"]) == 203, "Source11 metadata-only rows")
    rows, commands = views["lineage"], views["commands"]
    validate_objects({"objects": rows}); require(isinstance(commands, list), "commands rows")
    by_identity = {}
    for locator, row in enumerate(commands):
        identity = primary_identity(row); require(identity not in by_identity, "command tuple duplicate")
        by_identity[identity] = (locator, row)
    require(len(by_identity) == 714 and set(by_identity) <= {primary_identity(row) for row in rows}, "714 unique command subset")
    freeze, head = views["sdk_freeze"], scalar_string(config.get("source_head"), "Root head", 40)
    require(head == "50a1a5451227d1b30f42394dd02ddfbaea26a1ff", "Root selected SDK91 head")
    require(isinstance(freeze, dict) and freeze.get("status") == "FROZEN_SOURCE_INPUT" and freeze.get("contract") == "Root_normalized_source_qualification/v1" and freeze.get("source_head") == head and freeze.get("sdk_name") == "SDK91" and freeze.get("tree_verified") is True, "SDK91 actual freeze wrapper")
    source_root = scalar_string(freeze.get("source_root"), "source root"); windows_path(source_root, "source root")
    evidence = freeze.get("actual_freeze_evidence", {})
    require(type(evidence.get("exit_code")) is int and evidence["exit_code"] == 0 and evidence.get("complete") is True and evidence.get("all5_verified") is True and isinstance(evidence.get("all5_evidence_refs"), list) and len(evidence["all5_evidence_refs"]) == 5 and all(isinstance(item, str) and item for item in evidence["all5_evidence_refs"]), "actual complete/all5 refs")
    policy = dict(config["recipe_policy"]); policy["_source_root"] = source_root
    require(policy.get("mode") == "typed_when_present_else_fresh" and policy.get("effective_write_roles_reviewed") is True, "reviewed recipe policy")
    require(isinstance(policy.get("target_templates"), dict) and isinstance(policy.get("source_mapping_rules"), list) and isinstance(policy.get("include_mapping_rules"), list), "templates/mapping rules")
    header = policy["mailbox_header"]; scoped(header["path"], source_root)
    require(header["sha256"] == freeze.get("mailbox_header_sha256") and source_sha(header["path"]) == digest_text(header["sha256"], "header hash"), "frozen candidate header")
    versions = policy.get("accepted_dependency_versions")
    require(isinstance(versions, list) and versions and len({canonical(value) for value in versions}) == len(versions), "dependency Version policy")
    consumers = {primary_identity(item) for item in policy["required_mailbox_owner_selectors"]}
    require(len(consumers) == len(policy["required_mailbox_owner_selectors"]) and consumers <= {primary_identity(row) for row in rows}, "mailbox primary selectors")
    build_root, render_root = config["output_root"], config["render_output_root"]
    build_key, render_key = windows_path(build_root, "fresh build root"), windows_path(render_root, "render root")
    require(ntpath.dirname(build_key) == ntpath.dirname(render_key) and build_key != render_key, "separate sibling roots")
    require(not Path(build_root).exists(), "build root must remain uncreated")
    require(not render_key.startswith(windows_path(CAND, "source budget")), "production render independent scope")
    source_key = windows_path(source_root, "immutable source root")
    require(all(not key.startswith(source_key + "/") and not source_key.startswith(key + "/") and key != source_key for key in (build_key, render_key)), "source/output root isolation")
    abi = config["abi_inputs"]
    require(isinstance(abi, list) and abi and abi == freeze.get("abi_inputs"), "ABI freeze binding")
    for name in ("ck3_12002_semantic_adapter.hpp", "main_thread_query_mailbox_v1.hpp"):
        expected = ntpath.join(source_root, "ck3_autonomous_player/native_bridge/include/xar_bridge", name)
        records = [item for item in abi if isinstance(item, dict) and windows_path(item.get("path"), "ABI path") == windows_path(expected, "canonical ABI")]
        require(len(records) == 1 and source_sha(records[0]["path"]) == digest_text(records[0].get("sha256"), "ABI hash"), "mandatory ABI header pin")
        if "known_required_owner_indices" in records[0]:
            indices = records[0]["known_required_owner_indices"]
            require(isinstance(indices, list) and all(type(index) is int and 1 <= index <= 917 for index in indices) and len(set(indices)) == len(indices), "known ABI consumer indices")
    jobs, owners, object_map, required, candidate_inputs = [], [], {}, [], []
    typed_count, legacy_count = 0, 0
    for index, row in enumerate(rows, 1):
        identity = primary_identity(row); locator, command = by_identity.get(identity, (None, {}))
        fields = [name for name in ("arguments", "argv", "args") if name in command]
        require(len(fields) <= 1, "typed array ambiguity")
        value = command[fields[0]] if fields else None
        typed = typed_arguments(value, "actual typed argv") if value is not None else None
        require(typed is not None or not command or isinstance(row.get("compiler_command_reference"), dict), "explicit legacy provenance")
        typed_count += typed is not None; legacy_count += typed is None
        source_field = scalar_string(policy.get("source_field"), "explicit source field")
        old_source = scalar_string(row.get(source_field), "actual source metadata")
        windows_path(old_source, "actual physical source")
        old_cwd = command.get("directory", command.get("cwd"))
        if typed is not None: windows_path(old_cwd, "actual command cwd")
        new_source = map_path(old_source, old_cwd, policy["source_mapping_rules"], source_root); scoped(new_source, source_root)
        key = windows_path(absolute(old_source, old_cwd), "source rule")
        rule_indices = [number for number, rule in enumerate(policy["source_mapping_rules"]) if key == windows_path(rule[0], "rule") or key.startswith(windows_path(rule[0], "rule").rstrip("/") + "/")]
        require(len(rule_indices) == 1, "unique source rule proof")
        selected = override_for(policy.get("owner_overrides", []), identity)
        job = make_job(build_root, "c" + format(index, "04d"), selected.get("bounds", config["compile_defaults"]) if selected else config["compile_defaults"], config["environment_settings"], "compile", index)
        replacements = {"source": new_source, "object": job["output"], "deps": job["dependencies_file"], "pdb": job["pdb_file"], "job_root": job["job_root"]}
        fresh = typed is None or selected is not None
        if fresh:
            argv = expand(selected["argv_template"] if selected else policy["target_templates"][row["target"]], replacements)
            cwd, carrier = job["cwd"], new_source
            local = dict(policy); local["include_mapping_rules"] = []; local["immutable_include_roots"] = policy["candidate_include_roots"]
        else: argv, cwd, carrier, local = list(typed), old_cwd, old_source, policy
        original = list(argv); role_proof = override_for(policy.get("typed_role_overrides", []), identity) if not fresh else None
        argv, roles, position, includes, mappings = rewrite_compile(argv, cwd, carrier, new_source, job, local, role_proof)
        kind = "derived203_new_policy" if typed is None else "fresh_environment_policy" if selected else "actual_full_argv"
        digest = source_sha(new_source)
        refs = {"lineage": row_proof(store, declarations, "lineage", index - 1), "commands": row_proof(store, declarations, "commands", locator) if locator is not None else None, "source11_legacy": store.references["source11_legacy"] if typed is None else None}
        owner = {key: row[key] for key in ("target", "cpp", "object_path", "physical_compiled_source", "compiled_source_head", "source_head", "parent_object_lineage", "actual_compiler_receipt", "compiler_dependencies_json", "compiler_command_reference") if key in row}
        rule_ref = {"path": config_path, "sha256": config_sha, "pointer": "/recipe_policy/source_mapping_rules/" + str(rule_indices[0])}
        source_ref = dict(refs["lineage"]); source_ref["pointer"] += "/" + pointer_token(source_field)
        candidate = {"index": index, "target": row["target"], "source": new_source, "source_sha256": digest, "source_mapping_rule_ref": rule_ref, "original_native88_source_ref": source_ref}
        candidate_inputs.append(candidate)
        consumer = identity in consumers
        if consumer: required.append(index)
        deps = {"policy": "fresh_capture", "allowed_roots": policy["dependency_allowed_roots"], "required": True, "accepted_versions": versions, "source_sha256": digest, "mailbox_header": header, "requires_mailbox_header": consumer, "required_includes": policy.get("required_includes", [])}
        job.update({"index": index, "target": row["target"], "owner_tuple": owner, "source_mapping_rule_ref": rule_ref, "original_native88_source_ref": source_ref, "source": new_source, "source_sha256": digest, "source_arg_index": position, "include_indices": includes, "argv": argv, "token_roles": roles, "tool_sha256": tool_digest(argv, policy["tools"]), "mappings": mappings, "inputs": [new_source], "recipe_kind": kind, "old_actual_recipe_claimed": kind == "actual_full_argv", "original_argv": original, "input_refs": refs, "original_source_field": source_field, "original_source": old_source, "dependencies": deps, "defaultlib_bindings": [], "responsefiles": []})
        token_sha(roles); jobs.append(job); owners.append({"index": index, "owner_tuple": owner, "input_refs": refs})
        object_map[identity[2]] = (index, job["output"])
    require(typed_count == 714 and legacy_count == 203, "actual 714/203 recipe partition")
    closure = config["closure_policy"]
    require(isinstance(closure.get("archives"), list) and closure["archives"] and isinstance(closure.get("link"), dict), "actual closure inputs required")
    archives, archive_map, inspections = [], {}, []
    for ordinal, spec in enumerate(closure["archives"], 1):
        archive, old_output = closure_job(spec, "archive", ordinal, store, object_map, {}, config)
        require(old_output not in archive_map, "archive output duplicate")
        archives.append(archive); archive_map[old_output] = archive["output"]
        review = closure["archive_inspection"]
        inspection = make_job(build_root, "i" + format(ordinal, "04d"), review.get("bounds", config["closure_defaults"]), config["environment_settings"], "archive_inspection")
        inspection["output"] = str(Path(inspection["job_root"]) / "stage.stdout")
        inspection["stdout_encoding"] = scalar_string(review.get("stdout_encoding"), "inspection encoding")
        inspection_argv = expand(review["argv_template"], {"archive": archive["output"], "job_root": inspection["job_root"]})
        require(any(token.upper() == "/LIST" for token in inspection_argv) and any(token.upper() == "/NOLOGO" for token in inspection_argv) and inspection_argv.count(archive["output"]) == 1, "explicit archive /LIST template")
        inspection.update({"argv": inspection_argv, "tool_sha256": tool_digest(inspection_argv, policy["tools"]), "token_roles": review["token_roles"], "mappings": [], "inputs": [archive["output"]], "immutable_inputs": [], "responsefiles": [], "defaultlib_bindings": [], "archive_job_id": archive["job_id"], "expected_member_indices": archive["member_indices"], "expected_member_basenames": [ntpath.basename(jobs[index - 1]["output"]) for index in archive["member_indices"]]})
        require(len(inspection["token_roles"]) == len(inspection_argv), "inspection roles")
        token_sha(inspection["token_roles"]); inspections.append(inspection); archive["inspection_job"] = inspection
    link, _old_link = closure_job(closure["link"], "link", 1, store, object_map, archive_map, config)
    members = [index for job in archives for index in job["member_indices"]]; direct = link["direct_object_indices"]
    require(len(set(members)) == len(members) and len(set(direct)) == len(direct) and not set(members) & set(direct) and set(members + direct) == set(range(1, 918)), "archive/direct owner exact closure")
    require(set(link["selected_original_archives"]) == set(archive_map), "selected archive closure")
    parallel = config["parallel_policy"]
    for key in ("max_parallel_stages", "logical_processors", "max_observation_age_seconds", "cpu_parallel_limit", "aggregate_memory_reserve_bytes", "aggregate_output_reserve_bytes", "cleanup_wait_seconds"): strict_integer(parallel.get(key), key, 1)
    require(1 <= parallel["max_parallel_stages"] <= 64 and type(parallel.get("allow_oversubscription")) is bool and isinstance(parallel.get("observed_at_utc"), str) and config["max_parallel_stages"] == parallel["max_parallel_stages"], "Root parallel policy")
    all_jobs = jobs + archives + inspections + [link]
    writes = [windows_path(job[field], field) for job in all_jobs for field in ("output", "pdb_file", "dependencies_file", "tmp", "temp")]
    require(len(set(writes)) == len(writes) and len({ntpath.basename(job["output"]) for job in jobs}) == 917, "private writes/unique object basename")
    approved = config["approved_receipt_paths"]
    for key in ("build", "environment", "archive_link", "selected_owner", "explicit_selection", "source_admission"): scoped(approved[key], render_root)
    defaults = approved.get("defaultlib_bindings", {})
    require(isinstance(defaults, dict), "defaultlib approval paths")
    for path in defaults.values(): scoped(path, render_root)
    approval_paths = [windows_path(path, "approval") for path in list(defaults.values()) + [value for value in approved.values() if isinstance(value, str)]]
    require(len(set(approval_paths)) == len(approval_paths), "approval path collision")
    selected_lineage = {"native_owner_label": "Native88", "result_path": declarations["result"]["path"], "result_sha256": declarations["result"]["sha256"]}
    selected_map = {"path": declarations["lineage"]["path"], "sha256": declarations["lineage"]["sha256"]}
    manifest = {"schema": "xar.native.parallel.production/v1", "source_head": head, "output_root": build_root, "render_output_root": render_root, "sdk_freeze_receipt": declarations["sdk_freeze"]["path"], "build_admission": approved["build"], "environment_policy": approved["environment"], "archive_link_policy": approved["archive_link"], "selected_owner_admission": approved["selected_owner"], "RootExplicitSelection": approved["explicit_selection"], "source_admission": approved["source_admission"], "selected_owner_lineage": selected_lineage, "selected_owner_map": selected_map, "mode": "rebuild917", "compile_jobs": jobs, "retained_objects": [], "archives": archives, "link": link, "abi_inputs": abi, "max_parallel_stages": parallel["max_parallel_stages"], "parallel_policy": parallel, "root_render_config_sha256": config_sha, "renderer_qualification": MANIFEST_QUALIFICATION, "source11_legacy_ref": store.references["source11_legacy"]}
    data = canonical(manifest) + b"\n"; manifest_sha = hashlib.sha256(data).hexdigest()
    common = {"status": "REVIEW_REQUIRED", "manifest_sha256": manifest_sha, "source_head": head, "sdk_freeze_sha256": declarations["sdk_freeze"]["sha256"], "root_render_config_sha256": config_sha, "approved_receipt_paths": approved, "actual_compile_or_native_qualification": False}
    def draft(fields):
        result = dict(fields); result.update(common); return result
    drafts = {
        "selected_owner_draft": draft({"selected_owner_lineage": selected_lineage, "selected_owner_map": selected_map, "native86_indices_substituted": False, "compile_indices": list(range(1, 918)), "retained_indices": [], "owners": owners, "candidate_compile_inputs": candidate_inputs, "known_mailbox_consumer_indices": required}),
        "environment_draft": draft({"old_environment_inferred": False, "msvc_x64_cxx20_verified": False, "effective_write_paths_verified": False, "token_roles_verified": False, "job_environment_sha256": {job["job_id"]: value_sha(job["environment"]) for job in all_jobs}, "job_token_roles_sha256": {job["job_id"]: token_sha(job["token_roles"]) for job in all_jobs}, "accepted_dependency_versions": versions, "policy_added_write_roles": {role: policy.get("add_missing_" + role) is True for role in ("pdb", "deps")}, "required_compile_flags_by_target": policy["required_compile_flags_by_target"], "compile_flag_rules_by_target": policy["compile_flag_rules_by_target"], "compile_configuration_refs": policy["compile_configuration_refs"], "native_compile_policy_refs": policy["compile_configuration_refs"], "known_mailbox_consumer_indices": required, "derived203_admitted_indices": [job["index"] for job in jobs if job["recipe_kind"] == "derived203_new_policy"], "fresh_admitted_indices": [job["index"] for job in jobs if job["recipe_kind"] == "fresh_environment_policy"], "fresh_dependency_admitted_indices": list(range(1, 918)), "recipe_counts": {"typed_present": typed_count, "legacy_command_only": legacy_count}}),
        "build_draft": draft(dict(config["build_review_fields"], scope="native-production", approved_output_root=build_root, max_parallel_stages=parallel["max_parallel_stages"], parallel_policy=parallel, exclusive_output_owner_verified=False)),
        "archive_link_draft": draft({"selected_inputs_complete": False, "rendered_owner_coverage": True, "archives": [{"job_id": job["job_id"], "member_indices": job["member_indices"], "recipe_ref": job["recipe_ref"], "independent_refs": job["independent_refs"]} for job in archives], "archive_inspections": [{"job_id": job["job_id"], "archive_job_id": job["archive_job_id"], "expected_member_basenames": job["expected_member_basenames"]} for job in inspections], "link": {"direct_object_indices": direct, "recipe_ref": link["recipe_ref"], "independent_refs": link["independent_refs"], "defaultlib_bindings": link["defaultlib_bindings"]}}),
        "explicit_selection_draft": draft({"scope": "source-input", "source_root": source_root, "sdk_name": "SDK91", "sdk_freeze_receipt": declarations["sdk_freeze"]["path"], "Root_selected_full_head": head}),
        "source_admission_draft": draft({"scope": "source-input", "source_root": source_root, "sdk_name": "SDK91", "sdk_freeze_receipt": declarations["sdk_freeze"]["path"], "actual_freeze_evidence": evidence, "source_files": [{"index": job["index"], "path": job["source"], "sha256": job["source_sha256"]} for job in jobs], "mailbox_header": header, "abi_inputs": abi}),
    }
    payloads = {"manifest": data}; payloads.update({name: canonical(value) + b"\n" for name, value in drafts.items()})
    return payloads, manifest_sha, store

def write_outputs(config, payloads, store):
    admission = store.resolve(config["root_render_admission_ref"])
    require(isinstance(admission, dict) and admission.get("status") == "ADMITTED" and admission.get("scope") == "native-production-render" and admission.get("source_head") == config["source_head"] and admission.get("approved_output_root") == config["render_output_root"], "independent render admission")
    paths = config["output_paths"]
    require(isinstance(paths, dict) and set(paths) == set(payloads) and admission.get("approved_output_paths") == paths, "exact render output paths")
    require(sum(map(len, payloads.values())) <= strict_integer(admission.get("max_total_output_bytes"), "render budget", 1), "production metadata budget")
    from datetime import datetime, timezone
    deadline = datetime.fromisoformat(scalar_string(admission.get("deadline_utc"), "render deadline").replace("Z", "+00:00"))
    require(deadline.tzinfo is not None and datetime.now(timezone.utc) < deadline, "render admission expired")
    normalized = []
    for path in paths.values():
        normalized.append(windows_path(scoped(path, config["render_output_root"]), "render path")); require(not Path(path).exists(), "existing output refused")
    require(len(set(normalized)) == len(normalized), "render path collision")
    require(not {windows_path(ref["path"], "input") for ref in store.references.values()}.intersection(normalized), "input/output collision")
    final_paths = {windows_path(path, "approval target") for path in list(config["approved_receipt_paths"].get("defaultlib_bindings", {}).values()) + [path for path in config["approved_receipt_paths"].values() if isinstance(path, str)]}
    require(not final_paths.intersection(normalized), "draft/approval collision")
    require(not Path(config["output_root"]).exists(), "build root remains fresh")
    for name, path in paths.items():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with Path(path).open("xb") as handle: require(handle.write(payloads[name]) == len(payloads[name]), "short artifact write")
        require(source_sha(path) == hashlib.sha256(payloads[name]).hexdigest(), "artifact readback hash")

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True); parser.add_argument("--config-sha256", required=True)
    args = parser.parse_args(); windows_path(args.config, "Root config path"); config = load_document(args.config, args.config_sha256)
    payloads, digest, store = render_manifest(config, args.config_sha256, args.config)
    write_outputs(config, payloads, store)
    sys.stdout.write(json.dumps({"status": "RENDERED_REVIEW_REQUIRED", "manifest_sha256": digest, "outputs": len(payloads), "compile_jobs": 917, "executed_compiler": False}) + "\n")
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, RecursionError) as error:
        sys.stderr.write("BLOCKED; Source13 renderer; " + type(error).__name__ + ": " + str(error)[:600] + "\n")
        raise SystemExit(3)
