"""Private AST adapter for one exact immutable exporter, never a disk copy.

Original validate_inputs/helpers retain their source/code. Only the validated
context handoff and three metadata records are transformed in memory. An exact
inverse comparison rejects every other change. No installed module is patched.
"""
import ast
import copy
import hashlib
from pathlib import Path
import threading

from g2_saved_campaign.native29_to30_export_contract_v1 import NativeTransitionV1, require

OLD_BYTES = 22964
OLD_SHA256 = "8b6972ac2a82b30c92b531c640df0eb9aa6e43cc205ab9d7d23796d5739da432"
_SEAL = object()


def _dump(node):
    return ast.dump(node, include_attributes=False)


def _code_source():
    path = Path(__file__).with_name("export_immutable_sdk_views_v1.py")
    with path.open("rb") as stream:
        raw = stream.read(OLD_BYTES + 1)
    _require_frozen_bytes_v1(raw)
    return path, raw


def _require_frozen_bytes_v1(raw):
    require(type(raw) is bytes and len(raw) == OLD_BYTES and hashlib.sha256(raw).hexdigest() == OLD_SHA256,
            "frozen original exporter bytes changed")


class _ReadyContextV1:
    def __init__(self, adapter, args, context, transition):
        require(type(transition) is NativeTransitionV1, "typed transition required")
        self.adapter, self.args, self.context, self.transition = adapter, args, context, transition
        self.seal, self.used = _SEAL, False


def _transform_export(original):
    transformed = copy.deepcopy(original)
    require(original.name == "export_views" and len(original.args.args) == 1
            and original.args.args[0].arg == "args" and not original.args.kwonlyargs,
            "original export signature changed")
    require(_dump(original.body[0]) == _dump(ast.parse("context = validate_inputs(args)").body[0]),
            "original pre-output validation changed")
    transformed.args.kwonlyargs.append(ast.arg(arg="_ready"))
    transformed.args.kw_defaults.append(None)
    transformed.body[0] = ast.copy_location(ast.parse("context = _accept_ready_v1(args, _ready)").body[0], original.body[0])
    counts = {"native": 0, "attempt": 0, "manifest": 0, "complete": 0}
    metadata_calls = []
    for node in ast.walk(transformed):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "dict":
            continue
        keywords = {kw.arg: kw for kw in node.keywords}
        if "native_build_label" in keywords and "native_dll_sha256" in keywords:
            for name in ("native_build_label", "native_dll_sha256"):
                expected = ast.parse("context['native'][" + repr(name) + "]", mode="eval").body
                require(_dump(keywords[name].value) == _dump(expected), "original Native metadata changed")
                keywords[name].value = ast.parse("_ready.transition.target_native[" + repr(name) + "]", mode="eval").body
                counts["native"] += 1
            counts["manifest"] += 1
            metadata_calls.append(node)
        elif "status" in keywords and isinstance(keywords["status"].value, ast.Constant):
            status = keywords["status"].value.value
            if status == "STARTED_NOT_ADOPTED":
                counts["attempt"] += 1
                metadata_calls.append(node)
            elif status == "SOURCE_READY_NOT_LOADED":
                counts["complete"] += 1
                metadata_calls.append(node)
    require(counts == {"native": 2, "attempt": 1, "manifest": 1, "complete": 1}, "metadata seam count changed")
    for call in metadata_calls:
        require(all(kw.arg != "native_transition" for kw in call.keywords), "metadata field collision")
        call.keywords.append(ast.keyword(arg="native_transition",
            value=ast.parse("_ready.transition.manifest_metadata", mode="eval").body))
    # Inverse every permitted edit, then compare the entire export function.
    inverse = copy.deepcopy(transformed)
    inverse.args.kwonlyargs.pop(); inverse.args.kw_defaults.pop()
    inverse.body[0] = copy.deepcopy(original.body[0])
    for node in ast.walk(inverse):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
            node.keywords = [kw for kw in node.keywords if kw.arg != "native_transition"]
            for kw in node.keywords:
                if kw.arg in ("native_build_label", "native_dll_sha256"):
                    kw.value = ast.parse("context['native'][" + repr(kw.arg) + "]", mode="eval").body
    require(_dump(inverse) == _dump(original), "export AST inverse is not exact")
    ast.fix_missing_locations(transformed)
    return transformed, counts


class FrozenExporterAdapterV1:
    def __init__(self):
        path, raw = _code_source()
        tree = ast.parse(raw, filename=str(path))
        original = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "export_views")
        transformed, self.seam_counts = _transform_export(original)
        # Execute original imports/constants/functions in a private namespace.
        # Skip only its sys.path bootstrap and __main__ dispatch, never helpers.
        selected = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.FunctionDef)):
                selected.append(copy.deepcopy(node))
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                continue
            elif isinstance(node, ast.Expr) and _dump(node) == _dump(ast.parse(
                    "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))").body[0]):
                continue
            elif isinstance(node, ast.If) and _dump(node.test) == _dump(ast.parse("__name__ == '__main__'", mode="eval").body):
                continue
            else:
                require(False, "unexpected original module initialization")
        namespace = {"__name__": "_xar_private_native_transition_exporter", "__file__": str(path)}
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)
        self.namespace, self.original_validate = namespace, namespace["validate_inputs"]
        self.original_export_code = namespace["export_views"].__code__
        self.original_ast_sha256 = hashlib.sha256(_dump(original).encode()).hexdigest()
        self.transformed_ast_sha256 = hashlib.sha256(_dump(transformed).encode()).hexdigest()
        self.lock = threading.RLock()
        self._validated = None
        namespace["_accept_ready_v1"] = self._accept_ready
        exec(compile(ast.Module(body=[transformed], type_ignores=[]),
                     str(Path(__file__).resolve()) + "<private-metadata-adapter>", "exec"), namespace)
        self.transformed_export = namespace["export_views"]
        require(namespace["validate_inputs"] is self.original_validate, "original validator replaced")

    def validate_base(self, args):
        """Original unchanged validation, including Native29/card/NTFS guards."""
        context = self.original_validate(args)
        with self.lock:
            require(self._validated is None, "base validation is once-only")
            self._validated = (args, context, repr(vars(args)), repr(context))
        return context

    def prepare(self, args, context, transition):
        require(type(transition) is NativeTransitionV1 and not transition.source_fixture,
                "synthetic transition cannot deploy")
        self._require_validated(args, context)
        require(isinstance(context, dict) and context.get("base_pin") == transition.manifest_metadata["base_freeze"]
                and context.get("native_pin") == transition.manifest_metadata["base_native_pin"],
                "validated base/native context differs")
        return _ReadyContextV1(self, args, context, transition)

    def _require_validated(self, args, context):
        require(self._validated is not None and self._validated[0] is args
                and self._validated[1] is context and self._validated[2] == repr(vars(args))
                and self._validated[3] == repr(context), "original validated arguments/context changed or missing")

    def _accept_ready(self, args, ready):
        with self.lock:
            require(type(ready) is _ReadyContextV1 and ready.seal is _SEAL
                    and ready.adapter is self and ready.args is args and not ready.used,
                    "same once-only validated export context required")
            require(not ready.transition.source_fixture, "synthetic transition cannot deploy")
            self._require_validated(args, ready.context)
            ready.used = True
            return ready.context

    def export(self, args, ready):
        return self.transformed_export(args, _ready=ready)
