"""Record completed limited frame inspection and checked-in delivery facts."""
from pathlib import Path
import argparse,json,shutil
import review_story_a04 as p
from compose_copy_bgm_a09 import P,exact,require

def quality(run):
    final=p.read(run/'final-artifact.json');index=p.read(run/'frame-review/frame-index.json');machine=p.read(run/'audit/machine-report.json');music=p.read(run/'audit/music-presence.json')
    require(machine['passed'] and music['passed'] and index['artifact']['sha256']==final['sha256'],'Exact final audit/frame binding required')
    report={'at_utc':p.stamp(),'reviewer':'/root','verdict':'PASS_PENDING_HUMAN_REVIEW','subject':final,'reviewed_contact_sheets':[p.ref(x) for x in sorted((run/'frame-review').glob('contact-*.jpg'))],'reviewed_final_frame_count':len(index['frames']),'brown_gold_series_palette_visible':True,'formula_names_growth_and_original_UI_visible':True,'original_notice_visible_then_absent':True,'175_percent_example_explicitly_static':True,'BGM_actual_decoded_audio_verified':True,'full_1x_human_viewing':False,'full_listening_performed':False,'human_signoff':'not-provided','production_clean_admission':False,'scope':'Root directly inspected nine sheets containing33 actual final frames. Music evidence is a signal comparison, not a claimed human audition.'}
    p.write(run/'frame-review/final-frame-quality.json',report);p.write(run/'final-brown-gold-artifact.json',final)
    p.write(run/'audit/delivery-machine-condition.json',{'at_utc':p.stamp(),'machine_condition_status':'PASS','final_artifact':final,'source_machine_report':p.ref(run/'audit/machine-report.json'),'checks_passed':len(machine['checks']),'human_signoff':'not-provided'})
    print(json.dumps({'quality':report['verdict'],'frames':len(index['frames'])}))

def report(run):
    final=p.read(run/'final-artifact.json');delivery=p.read(run/'delivery/final-delivery.json');machine=p.read(run/'audit/machine-report.json');audio=p.read(run/'audit/music-presence.json');levels=p.read(run/'audit/audio-levels.json');archive=p.read(run/'native-preservation-complete.json')
    require(delivery['status']=='CLIENT_METADATA_IN_SYNC_REMOTE_UNVERIFIED','Client must report completion before delivery report')
    closed=p.read(run/'closed-retention-result.json')
    require(closed['all_bindings_valid'] and closed['human_signoffs']==0,'Completed process archive required')
    # Verify every retained original source binding from the preceding full copy audit.
    seen={}
    def visit(x):
        if isinstance(x,dict):
            if {'path','bytes','sha256'}.issubset(x) and Path(x['path']).is_file():seen[x['path']]={k:x[k] for k in ('path','bytes','sha256')}
            for value in x.values():visit(value)
        elif isinstance(x,list):
            for value in x:visit(value)
    visit(p.read(P/'evidence-a09-copy-audit-20261002/full-copy-audit.json'))
    for ref in seen.values():exact(ref)
    out=P/'evidence-a09-video-bgm-20261002';out.mkdir(exist_ok=False)
    names=['final-artifact.json','music-policy.json','audit/machine-report.json','audit/music-presence.json','audit/audio-levels.json','frame-review/final-frame-quality.json','delivery/final-delivery.json','native-preservation-complete.json','retention-verification.json','board-label-revision.json','closed-retention-result.json','native-run/a09-frame-integrity-audit.json','pending-human-review/review-package.json']
    for name in names:shutil.copyfile(run/name,out/Path(name).name)
    p.write(out/'production-report.json',{'at_utc':p.stamp(),'source_branch':'codex/war-series-brown-gold-20261001','no_master_intake_or_integration':True,'final':final,'run':str(run),'narrated_duration':final['duration_expected'],'cue_count':177,'initial_fresh_narrations':100,'verified_existing_narrations':77,'initial_updated_boards':98,'final_label_fix_boards':1,'machine_check_count':len(machine['checks']),'decoded_music_test_windows':len(audio['windows']),'mean_dbfs':levels['mean_dbfs'],'peak_dbfs':levels['peak_dbfs'],'rechecked_copy_audit_bindings':len(seen),'archive':archive,'delivery':delivery,'human_signoff':'not-provided','full_human_review':'pending','process_attempts_retained':'C:/Users/1/ck3-e2-copy-bgm-20261002-a01','earlier_candidate_retained':'C:/Users/1/AppData/Local/ck3-review-render/episode02-brown-gold-copy-bgm-20261002-a01'})
    p.text_once(out/'delivery-summary.txt',f'战争系列第二期 a09：文案审计与系列 BGM\n\n交付：{delivery["target"]}\n时长：31分51秒；177句；六章；1920×1080/30fps\n主题曲：Quiet Courtly Tension，原战争系列 WAV；音乐-17dB，旁白0dB；片头2秒/片尾8秒淡化\n改动：100句新配音、77句原配音核验复用、98张图卡更新；另修正175%教学示例标签\n核验：193项机器检查通过；完整音视频解码；33张实际最终帧抽查；最终音轨音乐相关性检验通过\n边界：非零败方掩护仍缺实机验证；成长非空分支按原版静态规则讲解\n同步：OneDrive客户端InSync；独立远端字节回读未执行\n状态：供审阅成片；没有人工1×完整观看或听审签核\n分支：codex/war-series-brown-gold-20261001；未合入或拉取master\n')
    print(json.dumps({'report':str(out),'video_sha256':final['sha256'],'original_bindings_rechecked':len(seen)}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('phase',choices=['quality','report']);a.add_argument('--run',type=Path,required=True);args=a.parse_args();globals()[args.phase](args.run)
