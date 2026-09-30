"""Read-only frozen-source process inventory under the Chinese Windows locale.

No SDK, bridge connection, desktop capture, process start or game input.
"""
import argparse
import json
import locale
import os
from pathlib import Path
import sys


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    if sys.flags.utf8_mode != 0 or os.environ.get('PYTHONUTF8') != '0' or os.environ.get('PYTHONIOENCODING') != 'utf-8':
        raise RuntimeError('native inventory probe needs -X utf8=0 and explicit PYTHONUTF8=0/PYTHONIOENCODING=utf-8')
    source = Path('C:/w/jdcap0930/ck3_autonomous_player/src')
    sys.path.insert(0, str(source))
    from xar_autoplayer.environment import ck3_process_inventory
    print(json.dumps({'inventory': ck3_process_inventory(), 'source': str(source),
                      'utf8_mode': sys.flags.utf8_mode, 'locale_encoding': locale.getencoding(),
                      'preferred_encoding': locale.getpreferredencoding(False),
                      'stdout_encoding': sys.stdout.encoding,
                      'environment_overrides': {'PYTHONUTF8': os.environ.get('PYTHONUTF8'),
                                                'PYTHONIOENCODING': os.environ.get('PYTHONIOENCODING')},
                      'started_game': False, 'screen_accessed': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
