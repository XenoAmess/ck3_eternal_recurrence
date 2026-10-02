"""Use this checkout's Episode 2 reel editor with an explicit interpreter."""

from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "integration" / "src"
sys.path.insert(0, str(SRC))

from war_ai_promo.episode_two_reel_edit import main  # noqa: E402


if __name__ == "__main__":
    main()
