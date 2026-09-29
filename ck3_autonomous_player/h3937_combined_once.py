"""Direct entry for the exact H3937 read-only one-shot and screen challenge."""

import json
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from xar_autoplayer.h3937_combined_once_enable import (  # noqa: E402
    issue_screen_challenge, main, supervise_exact_once,
)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise SystemExit(supervise_exact_once(Path(__file__)))
    if len(sys.argv) == 2 and sys.argv[1] == "--issue-screen-challenge":
        print(json.dumps(issue_screen_challenge(Path(__file__)), ensure_ascii=False))
        raise SystemExit(0)
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        raise SystemExit(main(sys.argv[2]))
    raise SystemExit("H3937 one-shot accepts no operator arguments")
