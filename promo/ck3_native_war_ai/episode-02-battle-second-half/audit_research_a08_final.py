"""Audit the actual separate render attempt and its explicit source snapshot."""
from pathlib import Path
import argparse
import review_story_a04 as p
import run_research_a08_phase as phase
def main(run):
    p.write(run/'audit/audit-inputs-a02.json',{'audit_entrypoint':p.ref(__file__),'audit_implementation':p.ref(phase.__file__),'frozen_render_composer':p.ref(run/'sources/composer.py'),'timeline':p.ref(run/'timeline.json'),'edit':p.ref(run/'edit.json'),'previous_route_failure_preserved':True})
    phase.audit(run)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run',required=True,type=Path);main(a.parse_args().run)
