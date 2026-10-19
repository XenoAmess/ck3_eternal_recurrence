"""Pure Source20-only Driver splice; no complete Driver output or Git writes."""
import ast
import difflib
import hashlib
from pathlib import Path
import subprocess

BASE = "f19864de1cc073eed62617faad2307c57ad45a97"
PATH = "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"
PIN = (1637048, "cc60c9af670c37ef2085f66d07db17a2bd309660fcb60c05a5340df7720874ab")
REPO = Path(__file__).resolve().parents[2]

EDITS = (
    ('''        self._driver_state_wal_barrier_generation = 0
''', '''        self._driver_state_wal_barrier_generation = 0
        self._succession_binding_wal_anchor_v1 = None
'''),
    ('''        with self._driver_state_lock:
            if (
                self._episode_character_id != episode_character_id
                or self._episode_run_id != episode_run_id
            ):
                raise PreSubmissionRevisionMismatchError(
                    "succession expectation crossed the active episode"
                )
            self._succession_expectation = copy.deepcopy(expectation)
            self._succession_reconciliation = None
            self._driver_state_dirty = True
        self._persist_driver_state(persistence_reason='succession_expectation')
        return copy.deepcopy(expectation)
''', '''        refresh_enabled = getattr(self, "allow_driver_state_wal_v1", False)
        refresh_proof = None
        if refresh_enabled:
            from .succession_binding_refresh_wal_v1 import begin_refresh, finish_refresh
        with self._driver_state_lock:
            if (
                self._episode_character_id != episode_character_id
                or self._episode_run_id != episode_run_id
            ):
                raise PreSubmissionRevisionMismatchError(
                    "succession expectation crossed the active episode"
                )
            if refresh_enabled:
                refresh_before = self._driver_state_wal_scalar_fields_locked_v1()
                refresh_generation = self._driver_state_wal_barrier_generation
                refresh_reconciliation = self._succession_reconciliation
            self._succession_expectation = copy.deepcopy(expectation)
            self._succession_reconciliation = None
            self._driver_state_dirty = True
            if refresh_enabled:
                refresh_fields = self._driver_state_wal_scalar_fields_locked_v1()
                if refresh_reconciliation is None:
                    refresh_proof = begin_refresh(self, snapshot, refresh_before, refresh_fields)
        if refresh_enabled:
            self._persist_driver_state(
                persistence_reason='succession_expectation', journal_append=refresh_proof is not None,
                succession_binding_refresh=refresh_proof)
            with self._driver_state_lock:
                finish_refresh(self, snapshot, refresh_fields, refresh_generation)
        else:
            self._persist_driver_state(persistence_reason='succession_expectation')
        return copy.deepcopy(expectation)
'''),
    ('''    def _try_persist_driver_state_wal_append_v1(self) -> bool:
''', '''    def _try_persist_driver_state_wal_append_v1(self, *, succession_binding_refresh=None) -> bool:
'''),
    ('''                if fields != prior_fields:
                    # Scope, checkpoint and lifecycle mutations are barriers;
                    # they never hitchhike on a subsequent daily result.
                    return False
''', '''                if fields != prior_fields:
                    # Scope, checkpoint and lifecycle mutations are barriers;
                    # they never hitchhike on a subsequent daily result.
                    if succession_binding_refresh is None:
                        return False
                    from .succession_binding_refresh_wal_v1 import consume_refresh
                    with self._driver_state_lock:
                        if not consume_refresh(self, succession_binding_refresh, prior_fields,
                                               fields, rows, _is_deferred_read_only_history_step):
                            return False
                elif succession_binding_refresh is not None:
                    return False
'''),
    ('''        journal_append: bool = False,
    ) -> dict[str, object] | None:
''', '''        journal_append: bool = False,
        succession_binding_refresh=None,
    ) -> dict[str, object] | None:
'''),
    ('''                    self._driver_state_wal_barrier_required = True
                    self._driver_state_dirty = True
                    self._driver_state_error = f"{type(error).__name__}: {error}"
''', '''                    self._succession_binding_wal_anchor_v1 = None
                    self._driver_state_wal_barrier_required = True
                    self._driver_state_dirty = True
                    self._driver_state_error = f"{type(error).__name__}: {error}"
'''),
    ('''                and self._try_persist_driver_state_wal_append_v1()):
''', '''                and (self._try_persist_driver_state_wal_append_v1()
                     if succession_binding_refresh is None else
                     self._try_persist_driver_state_wal_append_v1(
                         succession_binding_refresh=succession_binding_refresh))):
'''),
    ('''        with self._driver_state_lock:
            self._driver_state_wal_barrier_required = True
            self._driver_state_wal_barrier_generation = getattr(
''', '''        with self._driver_state_lock:
            self._succession_binding_wal_anchor_v1 = None
            self._driver_state_wal_barrier_required = True
            self._driver_state_wal_barrier_generation = getattr(
'''),
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load_base():
    raw = subprocess.check_output(["git", "-C", str(REPO), "show", BASE + ":" + PATH])
    require((len(raw), hashlib.sha256(raw).hexdigest()) == PIN, "exact Source20 Driver unavailable")
    return raw


def transform(raw, *, reverse=False):
    if not reverse:
        require((len(raw), hashlib.sha256(raw).hexdigest()) == PIN, "foreign Driver baseline")
    result = raw
    for before, after in (reversed(EDITS) if reverse else EDITS):
        old, new = (after, before) if reverse else (before, after)
        require(result.count(old.encode()) == 1, "Driver hunk absent or not unique")
        result = result.replace(old.encode(), new.encode(), 1)
    compile(result, PATH, "exec", dont_inherit=True)
    if reverse:
        require((len(result), hashlib.sha256(result).hexdigest()) == PIN, "inverse Driver differs")
    return result


def patch_bytes(before, after):
    return "".join(difflib.unified_diff(before.decode().splitlines(True), after.decode().splitlines(True),
                    fromfile="a/" + PATH, tofile="b/" + PATH)).encode()


def methods(raw):
    tree = ast.parse(raw)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "NativeHeadlessGameplayDriver")
    return {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}


if __name__ == "__main__":
    raw = load_base()
    candidate = transform(raw)
    require(transform(candidate, reverse=True) == raw, "whole Driver inverse mismatch")
    print("Source20 in-memory Driver candidate", len(candidate), hashlib.sha256(candidate).hexdigest())
