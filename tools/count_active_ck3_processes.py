"""Root-only read-only CK3 count; never launch or control a process."""
from __future__ import annotations

import json
from pathlib import Path
import sys

_AGENT_SOURCE = Path(__file__).resolve().parents[1] / "ck3_autonomous_player" / "src"
if str(_AGENT_SOURCE) not in sys.path:
    sys.path.insert(0, str(_AGENT_SOURCE))
from xar_autoplayer.windows_process import active_process_pids


def main() -> int:
    excluded: set[int] = set()
    active = active_process_pids("ck3.exe", signaled_dead_pids=excluded)
    print(json.dumps({"image_name": "ck3.exe", "active_pids": active,
                      "excluded_signaled_pids": sorted(excluded)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
