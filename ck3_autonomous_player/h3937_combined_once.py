"""Direct, no-argument entry for the exact H3937 read-only one-shot."""

from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from xar_autoplayer.h3937_combined_once_enable import (  # noqa: E402
    main, supervise_exact_once,
)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise SystemExit(supervise_exact_once(Path(__file__)))
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        raise SystemExit(main(sys.argv[2]))
    raise SystemExit("H3937 one-shot accepts no operator arguments")
