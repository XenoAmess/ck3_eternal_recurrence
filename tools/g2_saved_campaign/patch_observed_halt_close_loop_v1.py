"""Pure projection of the admitted supervisor loop; no runtime I/O."""
from __future__ import annotations
import ast
import hashlib

_EARLY = "340b8cb5adcc78fccc4ffe2de5fd677dea13dcb21ba483358914041ef7f43afa"
_CLEANUP = "df003823429c35b0c6c9d7413f73b901e26087c5e0eeab3ef65f5fe7efe54cd6"
_BEFORE = b'        while not (N / "STOP-OWNED-GAME-C23").exists():\n'
_AFTER = b'        while True:\n            stop_requested: bool = (N / "STOP-OWNED-GAME-C23").exists()\n'
_KEEPER = b'            keeper.require_live()\n'

def _dump(node: ast.AST) -> str:
    return ast.dump(node, include_attributes=False)

def _digest(node: ast.AST) -> str:
    return hashlib.sha256(_dump(node).encode("utf-8")).hexdigest()

def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)

def _loop(tree: ast.Module) -> tuple[ast.FunctionDef, ast.While]:
    mains = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"]
    _require(len(mains) == 1, "one supervisor main required")
    main = mains[0]
    loops = [n for n in ast.walk(main) if isinstance(n, ast.While)
        and any(isinstance(x, ast.ImportFrom) and x.module == "root_a10_early_owned_close_v1" for x in n.body)]
    _require(len(loops) == 1, "one retained early-close loop required")
    return main, loops[0]

def patch_observed_halt_close_loop_v1(raw: bytes) -> bytes:
    """Snapshot STOP before admission loading; retain all once-only cleanup."""
    if type(raw) is not bytes:
        raise TypeError("supervisor source must be bytes")
    _require(0 < len(raw) <= 524288 and b"\r" not in raw, "bounded LF source required")
    _require(raw.count(_BEFORE) == raw.count(_KEEPER) == 1, "exact unpatched loop seams required")
    before = ast.parse(raw.decode("utf-8"))
    main, first = _loop(before)
    expected = ast.parse('not (N / "STOP-OWNED-GAME-C23").exists()', mode="eval").body
    _require(_dump(first.test) == _dump(expected) and len(first.body) >= 4, "original STOP condition required")
    _require(_digest(ast.Module(body=first.body[:3], type_ignores=[])) == _EARLY,
        "original admission/execute-once block required")
    _require(_dump(first.body[3]) == _dump(ast.parse("keeper.require_live()").body[0]), "keeper seam order differs")
    cleanups = [n for n in ast.walk(main) if isinstance(n, ast.If) and _digest(n) == _CLEANUP]
    _require(len(cleanups) == 1, "original guarded finally cleanup required")
    _require(not any(isinstance(n, ast.Name) and n.id == "stop_requested" for n in ast.walk(main)),
        "STOP snapshot variable already used")
    changed = raw.replace(_BEFORE, _AFTER).replace(
        _KEEPER, b"            if stop_requested:\n                break\n" + _KEEPER)
    _, second = _loop(ast.parse(changed))
    _require(isinstance(second.test, ast.Constant) and second.test.value is True, "unconditional loop required")
    _require(_dump(ast.Module(body=second.body[1:4], type_ignores=[]))
        == _dump(ast.Module(body=first.body[:3], type_ignores=[]))
        and _dump(ast.Module(body=second.body[5:], type_ignores=[]))
        == _dump(ast.Module(body=first.body[3:], type_ignores=[])), "loop body changed")
    compile(changed, "future-supervisor-stop-snapshot", "exec")
    return changed
