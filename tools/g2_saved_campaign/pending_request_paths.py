"""List only unconsumed published request files; avoid historical per-file stats."""
from pathlib import Path
import os


def pending_request_paths(inbox, outbox, next_sequence, *, held_control=None):
    if type(next_sequence) is not int or next_sequence < 1:
        raise ValueError("positive next request sequence required")
    pending = []
    suffix = "-1-result.json"
    with os.scandir(inbox) as entries:
        for entry in entries:
            name = entry.name
            if not name.endswith(suffix) or name == held_control:
                continue
            prefix = name[:-len(suffix)]
            if not prefix.isascii() or not prefix.isdecimal():
                raise ValueError("actual inbox filename has malformed request sequence")
            if int(prefix) < next_sequence:
                continue
            # Only new candidate names can incur file or response lookups.
            if entry.is_file(follow_symlinks=False) and not (Path(outbox) / name).exists():
                pending.append(Path(entry.path))
    return sorted(pending)
