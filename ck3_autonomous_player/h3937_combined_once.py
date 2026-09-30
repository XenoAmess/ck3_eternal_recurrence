"""Direct entry for the exact H3937 read-only one-shot and screen challenge."""

from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from xar_autoplayer import h3937_combined_once_enable as runner  # noqa: E402
from xar_autoplayer.h3937_run_config import main_for_runner  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main_for_runner(runner, Path(__file__), sys.argv[1:]))
