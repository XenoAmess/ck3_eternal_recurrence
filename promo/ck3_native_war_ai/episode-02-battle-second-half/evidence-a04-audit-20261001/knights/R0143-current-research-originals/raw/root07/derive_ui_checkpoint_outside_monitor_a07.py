from pathlib import Path
import hashlib
import json
ROOT = Path(__file__).resolve().parent
old = ROOT / 'preserve_paused_ui_checkpoint_a06.py'
new = ROOT / 'preserve_paused_ui_checkpoint_a07.py'
text = old.read_text(encoding='utf-8')
anchor = "    controller.require((evidence / 'variable-monitor-begin.json').is_file() and not (evidence / 'variable-monitor-finish-intent.json').exists(), 'Independent writer monitor must be armed')"
replacement = """    if args.phase == 'before':
        controller.require(not (evidence / 'variable-monitor-begin-intent.json').exists(), 'Before UI checkpoint must precede day monitor')
    else:
        finished = controller.read(evidence / 'variable-monitor-finish.json')
        controller.require(finished['scoped_variable_monitor']['detours_uninstalled'] is True, 'After UI checkpoint requires drained monitor')"""
if text.count(anchor) != 1:
    raise RuntimeError('Unexpected checkpoint source')
text = text.replace(anchor, replacement)
with new.open('x', encoding='utf-8', newline='\n') as f: f.write(text)
# This stage is a new run's preparation and has not been executed or bound yet.
stage = ROOT / 'run_required_core_ui_a11.py'
stage_a12 = ROOT / 'run_required_core_ui_a12.py'
with stage_a12.open('x', encoding='utf-8', newline='\n') as f:
    f.write(stage.read_text(encoding='utf-8').replace('preserve_paused_ui_checkpoint_a06.py', 'preserve_paused_ui_checkpoint_a07.py'))
binding = ROOT / 'prepare_runtime_binding_and_plan_a08.py'
binding_a09 = ROOT / 'prepare_runtime_binding_and_plan_a09.py'
text = binding.read_text(encoding='utf-8')
text = text.replace("ROOT / 'scoped_ui_research_a08.py',", "ROOT / 'scoped_ui_research_a08.py', ROOT / 'advance_and_drain_immediately_a12.py', ROOT / 'run_required_core_ui_a12.py', ROOT / 'preserve_paused_ui_checkpoint_a07.py',")
with binding_a09.open('x', encoding='utf-8', newline='\n') as f: f.write(text)
def ident(p):
    return {'path': str(p.resolve()), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest().upper()}
with (ROOT / 'UI-monitor-window-derivation-a07.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump({'original_checkpoint': ident(old), 'derived_checkpoint': ident(new), 'original_stage': ident(stage), 'derived_stage': ident(stage_a12), 'original_binding': ident(binding), 'derived_binding': ident(binding_a09),
               'scope': 'Keep all native source/session/date/hash checks. Place UI/save windows outside the monitor one-day observation. No previous run modified.'}, f, indent=2)
