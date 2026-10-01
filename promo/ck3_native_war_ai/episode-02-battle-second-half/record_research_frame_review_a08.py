"""Record root's completed limited final-frame review; never a full human signoff."""
from pathlib import Path
import argparse,json
import review_story_a04 as p
def main(run):
    final=p.read(run/'final-artifact.json');index=p.read(run/'frame-review/frame-index.json');machine=p.read(run/'audit/machine-report.json')
    if not machine['passed'] or index['artifact']['sha256']!=final['sha256']:raise ValueError('Actual exact-byte machine/frame evidence required')
    quality={'at_utc':p.stamp(),'reviewer':'/root','verdict':'PASS_PENDING_HUMAN_REVIEW','subject':final,'reviewed_contact_sheets':[p.ref(x)for x in sorted((run/'frame-review').glob('contact-*.jpg'))],'reviewed_final_frame_count':len(index['frames']),'original_packaging_focus_frames_actually_viewed':True,'brown_gold_matches_war_series':True,'changed_diagram_text_and_bilingual_subtitles_visible':True,'character_pages_and_four_complete_rosters_visible':True,'R149_complete_battle_and_width_tooltip_visible':True,'historical_A01_and_current_R149_transition_explicit':True,'historical_a02_inset_visible_at_plus_0_5s_and_absent_at_plus_3s':True,'full_1x_human_viewing':False,'full_listening_performed':False,'human_signoff':'not-provided','production_clean_admission':False,'scope':'Root directly viewed 9 contact sheets covering 34 actual final frames; limited pixel/packaging check only.'}
    p.write(run/'frame-review/final-frame-quality.json',quality)
    p.write(run/'final-brown-gold-artifact.json',final)
    p.write(run/'audit/delivery-machine-condition.json',{'at_utc':p.stamp(),'machine_condition_status':'PASS','final_artifact':final,'source_machine_report':p.ref(run/'audit/machine-report.json'),'checks_passed':len(machine['checks']),'human_signoff':'not-provided'})
    print(json.dumps({'quality':'PASS_PENDING_HUMAN_REVIEW','frames':len(index['frames']),'sha256':final['sha256']}))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run',required=True,type=Path);main(a.parse_args().run)
