from pathlib import Path
ROOT = Path(__file__).resolve().parent
src = (ROOT / 'restore_and_release_screen.py').read_text(encoding='utf-8')
old = "subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout="
assert src.count(old) == 2
src = src.replace(old, 'subprocess.run(command, capture_output=True, timeout=')
src = src.replace("write(args.output_dir / 'display-restore-process.json',", "(args.output_dir / 'display-restore-stdout.bin').write_bytes(result.stdout)\n    (args.output_dir / 'display-restore-stderr.bin').write_bytes(result.stderr)\n    write(args.output_dir / 'display-restore-process.json',")
src = src.replace("write(args.output_dir / 'screen-release-CAS.json',", "(args.output_dir / 'screen-release-CAS-stdout.bin').write_bytes(result.stdout)\n    (args.output_dir / 'screen-release-CAS-stderr.bin').write_bytes(result.stderr)\n    write(args.output_dir / 'screen-release-CAS.json',")
src = src.replace("'stdout': result.stdout, 'stderr': result.stderr", "'stdout': result.stdout.decode('utf-8', errors='replace'), 'stderr': result.stderr.decode('utf-8', errors='replace')")
compile(src, 'restore_and_release_screen_a02.py', 'exec')
with (ROOT / 'restore_and_release_screen_a02.py').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(src)
print('raw restore controller derived; no desktop action')
