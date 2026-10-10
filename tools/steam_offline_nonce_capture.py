"""Capture two live nonce labels without deciding Steam's offline status."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import time


def capture(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    import tkinter as tk
    import pyautogui

    window = tk.Tk()
    window.title('Live desktop freshness challenge')
    window.attributes('-topmost', True)
    label = tk.Label(window, font=('Arial', 28), bg='#ffff00', fg='#000000',
                     padx=15, pady=15)
    label.pack()
    records = []
    previous_nonce = None
    try:
        for index in (1, 2):
            nonce = secrets.token_hex(6)
            if nonce == previous_nonce:
                raise RuntimeError('Independent nonce did not change; review not produced')
            previous_nonce = nonce
            requested = datetime.now(timezone.utc).isoformat()
            label.configure(text='LIVE ' + nonce)
            window.update_idletasks()
            width, height = pyautogui.size()
            left = max(0, width - window.winfo_reqwidth() - 16)
            top = max(0, height - window.winfo_reqheight() - 64)
            window.geometry(f'+{left}+{top}')
            window.update()
            time.sleep(.3)
            shot = pyautogui.screenshot()
            path = output / f'challenge-{index}.png'
            with path.open('xb') as stream:
                shot.save(stream, format='PNG')
            raw = path.read_bytes()
            records.append({'index': index, 'nonce': nonce, 'requested_utc': requested,
                'captured_utc': datetime.now(timezone.utc).isoformat(), 'path': str(path),
                'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                'image_size': list(shot.size), 'desktop_size': list(pyautogui.size())})
    finally:
        window.destroy()
    report = {'records': records, 'steam_offline_status_observed': None,
        'scope': 'Two transient labels and unmodified full desktop captures. The actual operator must personally review both nonce pixels and offline Steam mode; no game or input action.'}
    with (output / 'report.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='new output directory; existing paths are refused')
    args = parser.parse_args()
    print(json.dumps(capture(args.output)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
