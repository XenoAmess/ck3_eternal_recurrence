"""Create new helpers for the explicitly changed observation lifetime."""
from pathlib import Path
import hashlib
import json
ROOT = Path(__file__).resolve().parent
def ident(p):
    return {'path': str(p.resolve()), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest().upper()}
def create(n, text):
    with (ROOT / n).open('x', encoding='utf-8', newline='\n') as f: f.write(text)
    return ROOT / n
old = ROOT / 'scoped_ui_research_a08.py'
text = old.read_text(encoding='utf-8')
anchor = "        require((evidence / 'variable-monitor-begin.json').is_file() and not (evidence / 'variable-monitor-finish-intent.json').exists(), 'Observe variable writers before UI/save getters')"
replacement = """        if args.phase == 'before':
            require(not (evidence / 'variable-monitor-begin-intent.json').exists() and not (evidence / 'one-day-intent.json').exists(), 'Before presentation must precede the one-day monitor')
        else:
            require((evidence / 'one-day-finished.json').is_file(), 'After presentation requires actual original day')
            finished = read(evidence / 'variable-monitor-finish.json')
            require(finished['scoped_variable_monitor']['detours_uninstalled'] is True, 'After presentation requires stopped observer')
    require(args.mode not in {'advance', 'monitor-begin', 'monitor-finish'}, 'Use the separately bound immediate one-day observer consumer')"""
if text.count(anchor) != 1: raise RuntimeError('Controller derivation anchor differs')
controller = create('scoped_ui_research_a09.py', text.replace(anchor, replacement))
sha = ident(controller)['sha256']
old_sha = '169EE7EA1DBF979B3EBE0C6221A4287B908E4F0F7BFA01A14DB86AC5D671F640'
derived = []
for a, b in [('advance_and_drain_immediately_a12.py', 'advance_and_drain_immediately_a13.py'), ('run_required_core_ui_a12.py', 'run_required_core_ui_a13.py'), ('preserve_paused_ui_checkpoint_a07.py', 'preserve_paused_ui_checkpoint_a08.py'), ('capture_desktop_hover_source_a01.py', 'capture_desktop_hover_source_a02.py'), ('run_logged_mode_a01.py', 'run_logged_mode_a02.py')]:
    p = ROOT / a
    text = p.read_text(encoding='utf-8').replace('scoped_ui_research_a08.py', 'scoped_ui_research_a09.py').replace(old_sha, sha).replace('preserve_paused_ui_checkpoint_a07.py', 'preserve_paused_ui_checkpoint_a08.py')
    if a == 'run_logged_mode_a01.py':
        text = text.replace("choices=['save','advance','monitor-finish','finish']", "choices=['save','finish']")
        text = text.replace("    assert ident(helper)['sha256']=='" + sha + "'", "    if ident(helper)['sha256']!='" + sha + "':raise RuntimeError('Current controller bytes changed')")
    if a == 'capture_desktop_hover_source_a01.py':
        text = text.replace("    assert args.label and all(c.isalnum() or c in '-_' for c in args.label)", "    if not (args.label and all(c.isalnum() or c in '-_' for c in args.label)):raise RuntimeError('Invalid exclusive label')")
        text = text.replace("    assert pid==cfg['native_session_binding']['bridge_pid']", "    m.require(pid==cfg['native_session_binding']['bridge_pid'],'Foreground is not current admitted game')")
        text = text.replace(";assert list(image.size)==size", ";m.require(list(image.size)==size,'Desktop dimensions changed')")
        text = text.replace(";assert not dst.exists()", ";m.require(not dst.exists(),'Original image exists')")
        text = text.replace(";assert not view.exists()", ";m.require(not view.exists(),'Preview exists')")
        text = text.replace(";assert values==pv", ";m.require(values==pv,'Paused native source changed around pixels')")
    target = create(b, text)
    derived.append({'original': ident(p), 'derived': ident(target)})
p = ROOT / 'prepare_runtime_binding_and_plan_a09.py'
text = p.read_text(encoding='utf-8').replace('scoped_ui_research_a08.py', 'scoped_ui_research_a09.py').replace('advance_and_drain_immediately_a12.py', 'advance_and_drain_immediately_a13.py').replace('run_required_core_ui_a12.py', 'run_required_core_ui_a13.py').replace('preserve_paused_ui_checkpoint_a07.py', 'preserve_paused_ui_checkpoint_a08.py')
text = text.replace("ROOT / 'preserve_paused_ui_checkpoint_a08.py',", "ROOT / 'preserve_paused_ui_checkpoint_a08.py', ROOT / 'capture_desktop_hover_source_a02.py', ROOT / 'run_logged_mode_a02.py',")
target = create('prepare_runtime_binding_and_plan_a10.py', text)
derived.append({'original': ident(p), 'derived': ident(target)})
with (ROOT / 'daily-window-controller-derivation-a09.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump({'original_controller': ident(old), 'controller': ident(controller), 'derived_helpers': derived,
               'change': 'Move only presentation/save lifecycle guard outside the actual daily observer. All original native identity, owner, revision, date, pixel capture and geometry checks remain unchanged. Unused old advance/monitor CLI modes are refused. No R0142 artifact changed.',
               'current_runtime_binding_not_yet_created': True}, f, indent=2)
print(json.dumps(ident(controller)))
