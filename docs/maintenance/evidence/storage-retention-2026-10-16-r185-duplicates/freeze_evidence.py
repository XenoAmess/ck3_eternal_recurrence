"""Freeze small exact7 evidence. --verify checks packaged bytes without asset access."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, subprocess, sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
DOC=HERE.parents[1]/'storage-retention-2026-10-16-r185-duplicates.md'
BASE=Path('C:/ck3-e04-resume-20261015-a01')
OLD=BASE/'storage-followup-r185-a01'
M='desktop-3fevhd2-1c74096080'
NAMES=('E01-SEVEN.plan.actual-a01.json','E01-SEVEN.result.actual-a01.json','E01-SEVEN.independent-readback.actual-a01.json','E01-CURRENT-CONSUMERS.actual-a01.json','E01-CURRENT-CONSUMERS.actual-a02.json','E01-SEVEN.intent.actual-a01.json','E01-SEVEN.files.actual-a01.jsonl')
SOURCES={
 'source/plan_e01_exact_duplicates.py':OLD/'plan_e01_exact_duplicates.py',
 'source/execute_e01_seven.py':OLD/'execute_e01_seven.py',
 'source/readback_e01_seven.py':OLD/'readback_e01_seven.py',
 'source/reclaim_superman_melts.py':BASE/'disk-reclamation-worker-a01/reclaim_superman_melts.py',
 'source/win32_exact_retire_lib.py':BASE/'capacity-lane/win32_exact_retire_lib.py',
}
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(j):return (json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def verify():
    j=json.loads((HERE/'INDEX.json').read_text(encoding='utf-8'))
    assert j['machine_id']==M
    for r in j['files']:
        b=(HERE/r['name']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256'],r['name']
    b=DOC.read_bytes();assert len(b)==j['maintenance_doc']['bytes'] and sha(b)==j['maintenance_doc']['sha256']
    p=json.loads((HERE/'E01-SEVEN.plan.actual-a01.json').read_text(encoding='utf-8'))
    r=json.loads((HERE/'E01-SEVEN.result.actual-a01.json').read_text(encoding='utf-8'))
    readback=json.loads((HERE/'E01-SEVEN.independent-readback.actual-a01.json').read_text(encoding='utf-8'))
    ledger=[json.loads(x) for x in (HERE/'E01-SEVEN.files.actual-a01.jsonl').read_text(encoding='utf-8').splitlines()]
    assert p['machine_id']==r['machine_id']==readback['machine_id']==M
    assert len(ledger)==r['deleted']==7 and r['failed']==0
    assert r['actual_D_single_link_allocation_bytes']==5629001728 and r['actual_D_logical_bytes']==5628978551 and r['actual_C_credit_bytes']==0
    assert len({x['path'] for x in ledger})==len({tuple(x['file_id']) for x in ledger})==7
    assert all(x['status']=='deleted_unavailable' for x in ledger)
    assert sha((HERE/'E01-SEVEN.plan.actual-a01.json').read_bytes())==r['plan']['sha256']
    assert sha((HERE/'E01-SEVEN.files.actual-a01.jsonl').read_bytes())==r['files_ledger']['sha256']
    assert sha((HERE/'E01-SEVEN.result.actual-a01.json').read_bytes())==readback['actual_result_sha256']
    assert readback['seven_paths_absent_now'] and readback['keeper_current_identity_metadata_unchanged']
    size=DOC.stat().st_size+sum(x.stat().st_size for x in HERE.rglob('*') if x.is_file())
    assert size<=98304,size
    print(json.dumps({'machine_id':M,'verification':'PASS','new_package_total_bytes':size,'index_sha256':sha((HERE/'INDEX.json').read_bytes()),'D_actual_allocation_bytes':5629001728,'C_credit_bytes':0}))
def freeze():
    if DOC.exists() or (HERE/'INDEX.json').exists():raise RuntimeError('Already frozen; use --verify')
    argv=[sys.executable,'-B',str(REPO/'tools/ck3_live_run_id.py'),'machine']
    started=datetime.now(timezone.utc).isoformat()
    run=subprocess.run(argv,cwd=REPO,text=True,encoding='utf-8',capture_output=True,check=True)
    assert run.stdout.strip()==M
    observed=datetime.now(timezone.utc).isoformat()
    blobs={n:(OLD/n).read_bytes() for n in NAMES}
    assert sha(blobs['E01-SEVEN.plan.actual-a01.json'])=='c488f1749b26232a863d8263df15ac6116046c15cfffc65f79443deb924911a2'
    assert sha(blobs['E01-SEVEN.result.actual-a01.json'])=='a5efe843b63d02438f594e2ec616e3865e515f068207d28fbd73aed6a8bd4e4c'
    assert sha(blobs['E01-SEVEN.independent-readback.actual-a01.json'])=='8e952df073231e03f1fd0a02773795a1ba15a0125f243e04cb674993a7081583'
    source_refs=[]
    for name,path in SOURCES.items():
        blobs[name]=path.read_bytes()
        source_refs.append({'name':name,'source_path':str(path),'bytes':len(blobs[name]),'sha256':sha(blobs[name]),'mtime_ns_at_freeze':path.stat().st_mtime_ns})
    r=json.loads(blobs['E01-SEVEN.result.actual-a01.json'])
    p=json.loads(blobs['E01-SEVEN.plan.actual-a01.json'])
    for name,pin in (('E01-CURRENT-CONSUMERS.actual-a01.json',p['consumer_query']),('E01-CURRENT-CONSUMERS.actual-a02.json',r['current_consumer_query'])):
        assert sha(blobs[name])==pin['sha256']
        check=json.loads(blobs[name]);assert not check['matches'] and not check['skipped'] and check['complete_scoped_query']
    fresh={'schema':'xar.r185-exact7-packaging-machine-readback.v1','machine_id':M,'started_at_utc':started,'observed_at_utc':observed,'argv':argv,'returncode':run.returncode,'stdout':run.stdout,'scope':'Fresh canonical machine identity only. No new capacity/asset content/TaskScheduler/Steam/runtime qualification was performed by packaging. Historical actual deletion and keeper facts retain their original observation times.','policy_version':'1.0.0','automatic_gc_implemented':False}
    blobs['MACHINE.fresh-a01.json']=enc(fresh)
    doc='''# R185 期间 E01 七份重复原片回收（2026-10-16）

`machine_id: desktop-3fevhd2-1c74096080`；[通用存储策略](../storage-retention-policy.md) **1.0.0**。本记录只证明来源机器在原回执 UTC 时点的实际操作。入库时另调用 `tools/ck3_live_run_id.py machine` 新鲜读回机器 ID，见[机器身份回执](evidence/storage-retention-2026-10-16-r185-duplicates/MACHINE.fresh-a01.json)；该检查不追认当前容量、Steam、运行时或定时任务状态。

经 Root 审阅精确 plan SHA `c488f1749b26232a863d8263df15ac6116046c15cfffc65f79443deb924911a2` 后，只删除 E01 的 **7 份**独立物理副本，0 失败：D logical **5,628,978,551 B**，D single-link allocation **5,629,001,728 B**，**C credit = 0**。这是本轮新增 actual，不能与先前 156 叶或 R184 cache/native 回收重复计数。全卷并发 free 变化不全归本批；使用已包含本次删除的 fresh used/free 时，不能再扣一次这笔 credit。

## 被删路径与唯一 keeper

以下路径均相对来源机器的 `D:/workspace/ck3_native_war_ai_promo_work/`；全路径、原 FileID、SHA 和实际 `deleted_unavailable` 映射见[逐叶原回执](evidence/storage-retention-2026-10-16-r185-duplicates/E01-SEVEN.files.actual-a01.jsonl)与[实际结果](evidence/storage-retention-2026-10-16-r185-duplicates/E01-SEVEN.result.actual-a01.json)。原历史 manifest 保留原样；这些旧路径已经不可读，没有创建同名替代文件。

| 旧 run | 删除的叶文件 |
| --- | --- |
| `episode01-r7f-index-formal-001` | content-addressed raw |
| `episode01-r7e-recut-001` | content-addressed raw |
| `episode01-r7c-muted-palette-001` | content-addressed raw |
| `episode01-r7-same-battle-002` | `messina-original-900s.mkv` |
| `episode01-r7-same-battle-002` | content-addressed raw |
| `episode01-r7-same-battle-001` | `messina-original-900s.mkv` |
| `episode01-full-edge-attempt-002` | `gameplay-precontact-r2.mkv` |

content-addressed raw 的固定后缀为 `run/artifacts/raw/sha256/0E/0E7699911B05EC54ACC852C6FCB31CB77E32D1DE5BCA8BA2A6FD054C3903589F.mkv`。唯一 keeper 位于 `episode01-r7f-index-formal-002/` 下的同一后缀，804,139,793 B，allocation 804,143,104 B，FileID **[882653518, 281474978651758]**；完整 SHA-256 为 `0e7699911b05ec54acc852c6fcb31cb77e32d1de5bca8ba2a6fd054c3903589f`。

keeper owner 为 **Root**，用途是保留 formal002 的同源原片及这 7 个历史路径的精确字节恢复来源；保护/复核截止 **2026-10-23T14:31:40.196824Z**，不自动续期。本次入库不重置该期限。formal002 `build-receipt.json` 的 source_video_sha256 对应同一内容，出处 SHA 已冻结在原 plan；该旧 build receipt 缺机器 ID，仍标历史 `machine_id: unknown`，不追认其执行机器，keeper 当前文件身份则由本轮实测绑定。

## 资格、执行与验证范围

采用已实际验证的同 SHA 副本提前回收例外，**没有声称原片自然满 30 天**。计划前和执行前分别有界读取当前 E04 Review02/Review01 的 1,113 个文件 / 5,849,220 B；exact path、旧 run 名及内容 hash 命中均为 0，skip 为 0，两次有序路径/大小/SHA manifest digest 一致。该结论限于已列当前消费 scope，不把旧 E01 历史 manifest 中的路径当作未来消费者。Root 另核对并批准 exact7，未扩到其他 E01、E02 素材。

执行前重新打开 keeper，持只读 shareREAD handle 禁止写/删；7 target 以独占 READ+DELETE handle 逐一核 SHA 和冻结 Win32 身份。所有 7 个 full SHA 均与 keeper 一致，FileID 不同，硬链接数均为 1；全部重新核验通过后才在同 handle 上设置删除并逐叶确认不存在。没有删目录，没有使用哈希充当丢失原件。

[独立闭场读回](evidence/storage-retention-2026-10-16-r185-duplicates/E01-SEVEN.independent-readback.actual-a01.json)确认 7 个旧路径仍不存在、FileID 唯一、keeper metadata 身份未变，D free **53,925,978,112 B**。独立读回只核 keeper ID/size/ftime/links/allocation，**没有再次全文哈希**；full SHA 证据来自此前同 handle 的计划和执行校验。入库步骤也没有重跑 payload hash、容量准入或当前资产可用性检查。各观测准确 UTC 保留在原件中，不把包装时间改成执行时间。

R185 live 场景、a28、R184 normal/raw/source、游戏与依赖均排除；主仓、TaskBus、SDK 和屏幕零操作。回收时使用独立 R185 a02 容量来源 SHA `7abe40950df2f25228dd646b0ac9aa9f10a68f6c9288af8a22cc551f643d5593` 与保护表 SHA `471540064b6a8261c3794a30e1166796457ea247615b6caaf80b1dc012367ec0`。**已过期的 2026-10-16T07:45:01.597Z 额度没有复用或延长**。本记录不是新的录制/写入准入，后续必须重新核共享预留、free 与有效期限。

## 可复用证据与自动化边界

[INDEX](evidence/storage-retention-2026-10-16-r185-duplicates/INDEX.json)固定精确原件的 bytes/SHA、source 路径和包装时点。[原计划](evidence/storage-retention-2026-10-16-r185-duplicates/E01-SEVEN.plan.actual-a01.json)、actual、independent readback、两次 current-consumer 查询、intent 和逐叶 ledger 均保持原字节。`source/` 冻结计划器、执行器、读回代码及其 Win32 辅助代码，供审阅与移植方法；source SHA 是入库时冻结的身份，不补造过去未记录的 source hash。代码包含来源机器路径，不能当跨机即用的删除任务；迁移必须重新绑定根目录、机器与身份/用途资格。

全部新文件合计不超过 **96 KiB**，无视频、原始 payload 或巨型库存入库；其他机器可复用结论与代码方法，不能外推来源机磁盘事实。执行 `freeze_evidence.py --verify` 只核包内字节和计数，不访问旧原片或系统任务。普通每日 04:00 只读巡检的历史安装记录不构成自动删除：本次没有检查/安装/修改 Scheduler，**`automatic_gc_implemented: false`**，没有宣称定时 autoGC 已部署。小型 record 按通用策略 180 天复核，精确 ledger 归纳期按原始 30 天约定；包装不刷新 payload 寿命或 keeper 保护。
'''
    db=doc.encode('utf-8')
    files=[{'name':n,'bytes':len(b),'sha256':sha(b)} for n,b in blobs.items()]
    helper=HERE/'freeze_evidence.py';files.append({'name':helper.name,'bytes':helper.stat().st_size,'sha256':sha(helper.read_bytes())})
    index={'schema':'xar.r185-seven-duplicates-small-evidence-index.v1','machine_id':M,'packaged_at_utc':observed,'policy_version':'1.0.0','original_receipt_root':str(OLD),'files':files,'source_freeze_refs':source_refs,'maintenance_doc':{'name':DOC.name,'bytes':len(db),'sha256':sha(db)},'automatic_gc_implemented':False,'new_asset_deletion_or_capacity_qualification':False,'record_review_policy_days':180,'keeper_original_deadline_unchanged':p['retained_replica_protected_until_utc']}
    ib=enc(index);total=sum(len(b) for b in blobs.values())+len(db)+len(ib)+helper.stat().st_size
    assert total<=98304,total
    for name,b in blobs.items():
        q=HERE/name;q.parent.mkdir(parents=True,exist_ok=True)
        with q.open('xb') as f:f.write(b)
    with DOC.open('xb') as f:f.write(db)
    with (HERE/'INDEX.json').open('xb') as f:f.write(ib)
    verify()
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--freeze',action='store_true');group.add_argument('--verify',action='store_true')
    args=parser.parse_args();freeze() if args.freeze else verify()
