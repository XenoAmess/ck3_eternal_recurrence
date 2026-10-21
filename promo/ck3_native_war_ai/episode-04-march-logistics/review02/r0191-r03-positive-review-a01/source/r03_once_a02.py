"""Create-only R191 once entry; no work happens on import."""
from pathlib import Path
import sys
from r03_pipeline_a02 import ROOT, run

def main(argv: list[str]) -> int:
    if argv != ["--execute-once", str(ROOT / "R03-RECIPE.prepared-a02.json")]:
        raise SystemExit("Requires Root-adopted exact source, source-bound cap and explicit once grant")
    return run(Path(argv[1]))

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
