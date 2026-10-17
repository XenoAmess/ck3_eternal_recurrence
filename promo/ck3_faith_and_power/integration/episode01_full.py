"""Explicit, bounded full-episode review entry point; no game or TTS access."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from faith_power_promo.full_episode import main
if __name__=='__main__':raise SystemExit(main())
