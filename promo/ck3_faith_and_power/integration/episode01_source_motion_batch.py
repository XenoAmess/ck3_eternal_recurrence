"""Explicit source-bound episode production entry; no game access."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/"src"))
from faith_power_promo.mechanism_motion_batch import main
if __name__=="__main__":raise SystemExit(main())
