"""ROOT entry for exact R24 file-only v3 boundary check/create."""
import sys
sys.dont_write_bytecode = True
from verify_previous_boundary import main
if __name__ == '__main__':
    raise SystemExit(main())
