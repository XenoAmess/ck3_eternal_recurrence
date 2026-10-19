"""Pure reversible future-C19 Driver overlay; never writes an SDK or file.

Apply only during an explicitly admitted future source composition. Exact
method fingerprints prevent silently porting this across business changes.
"""
import ast
import difflib
import hashlib

METHODS = {
    "_route_horizon_wal_eligible_v1": "cb937d06c693c2bfb1dda91ecf9a135f3e0c3a0ae82495d674368981219702af",
    "_execute_life_advance": "81037745838e1486194a50fa73bcd1086f55489b027bad23f77a1695dd62f1e4",
}
GATE = '''        # Reuse the exact-day native clock proof. Generic life-advance,'''
GATE_NEW = '''        if step == "life-advance":
            from .bounded_multiday_wal_v1 import eligible_bounded_multiday_delta_v1
            return eligible_bounded_multiday_delta_v1(step, result, expected_owner=(
                self._session_bridge_pid, self._episode_character_id, self._episode_run_id))
''' + GATE
RESULT = '''        if campaign_clock_receipt is not None:
            result["campaign_deadline_native_clock_v1"] = campaign_clock_receipt'''
RESULT_NEW = RESULT + '''
            if getattr(self, "allow_driver_state_wal_v1", False):
                from .bounded_multiday_wal_v1 import OWNER_KEY, owner_proof_v1
                owner_proof = owner_proof_v1(starting, current)
                if owner_proof is not None:
                    result[OWNER_KEY] = owner_proof'''


def method_fingerprints(source):
    tree = ast.parse(source)
    result = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in METHODS:
            if node.name in result:
                raise ValueError("duplicate guarded method")
            result[node.name] = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
    if set(result) != set(METHODS):
        raise ValueError("missing guarded method")
    return result


def transform_driver_bytes_v1(data):
    """Return candidate bytes; no I/O, compilation side effects or live apply."""
    if type(data) is not bytes or method_fingerprints(data) != METHODS:
        raise ValueError("bounded-multiday Driver method baseline changed")
    text = data.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    for before, after in ((GATE, GATE_NEW), (RESULT, RESULT_NEW)):
        before, after = before.replace("\n", newline), after.replace("\n", newline)
        if text.count(before) != 1:
            raise ValueError("bounded-multiday Driver source anchor changed")
        text = text.replace(before, after, 1)
    candidate = text.encode("utf-8")
    if reverse_driver_bytes_v1(candidate) != data:
        raise ValueError("bounded-multiday inverse changed original source")
    compile(candidate, "<future-c19-bounded-multiday-driver>", "exec")
    return candidate


def reverse_driver_bytes_v1(data):
    text = data.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    for before, after in ((GATE_NEW, GATE), (RESULT_NEW, RESULT)):
        before, after = before.replace("\n", newline), after.replace("\n", newline)
        if text.count(before) != 1:
            raise ValueError("bounded-multiday reverse anchor changed")
        text = text.replace(before, after, 1)
    return text.encode("utf-8")


def patch_text_v1(data):
    candidate = transform_driver_bytes_v1(data)
    path = "xar_autoplayer/bridge/native_driver.py"
    return "".join(difflib.unified_diff(data.decode().splitlines(True),
        candidate.decode().splitlines(True), fromfile="a/" + path, tofile="b/" + path))
