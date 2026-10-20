"""Private receipt wake; never game progress, a frame, or a public revision.

Uses only the transport's existing Condition and accepted heartbeat cache.
The caller re-reads its original cache and rechecks its original game predicate.
"""
from __future__ import annotations


def _positive_int(value):
    return type(value) is int and value > 0


def _heartbeat_sequence(value, pid):
    if (not isinstance(value, dict) or type(value.get("pid")) is not int
            or value["pid"] != pid):
        return None
    value = value.get("sequence")
    return value if type(value) is int and value >= 0 else None


def wait_for_exact_day_receipt_v1(state, after_revision, timeout_seconds,
                                  before_snapshot, progress):
    """Return True if this private wait was used, else preserve the old wait.

    This does not assert that its predicate became true: Condition timeout has
    the same next step as a wake, namely the caller's original snapshot read.
    A different/closed connection wakes for normal error/identity handling.
    No outside-Condition snapshot of the receiver's mutable cache is taken.
    """
    if not isinstance(before_snapshot, dict) or progress is None:
        return False
    diagnostics = before_snapshot.get("diagnostics")
    if not isinstance(diagnostics, dict):
        return False
    identity = (diagnostics.get("bridge_pid"),
                diagnostics.get("connection_generation"),
                before_snapshot.get("episode_character_id"),
                before_snapshot.get("episode_run_id"))
    if (not all(_positive_int(v) for v in identity[:3])
            or type(identity[3]) is not str or not 0 < len(identity[3]) <= 128
            or getattr(progress, "identity", None) != identity
            or not _positive_int(getattr(progress, "generation", None))
            or getattr(progress, "closed", True) is not False):
        return False
    previous = _heartbeat_sequence(diagnostics.get("last_heartbeat"), identity[0])
    if previous is None:
        return False
    # The public method and its predicates are intentionally untouched.
    with state._condition:
        def changed():
            hello = state._hello
            pid = hello.get("pid") if isinstance(hello, dict) else None
            same = (state._connected is True
                    and state._connection_generation == identity[1]
                    and pid == identity[0])
            if not same:
                return True
            return (state._public_revision > after_revision
                    or (_heartbeat_sequence(state._last_heartbeat, identity[0]) is not None
                        and _heartbeat_sequence(state._last_heartbeat, identity[0]) != previous))
        state._condition.wait_for(changed, timeout=timeout_seconds)
    return True
