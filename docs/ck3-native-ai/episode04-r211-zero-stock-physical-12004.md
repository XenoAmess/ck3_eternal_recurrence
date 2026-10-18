# R211 零库存目标窗口：本场首帧来源

本页记录 R211 自己的暂停查询，不以 R209 的预测代替本场读回。执行机器 `machine_id: desktop-3fevhd2-1c74096080`；session 为 `desktop-3fevhd2-1c74096080--r05-mechanism-research--R0005`。本研究线程只消费既有原件，没有 SDK、游戏操作或新构建。

## 首帧实测

来源为 `case-output-observe-only-a01/r211-observe-only-a01-r05obs-0009-day-01-before-full-history-derived-normalized-full.json`，15,112,791 B；其 SHA、实际观察 UTC、独立目标字段和 query frame 已封于[首帧 extract](evidence/episode04-r211-zero-stock-physical-12004/R211-FIRST-TARGET-EXTRACT.actual-a01.json)。

- snapshot `native:2`，public revision3、native revision2、connection generation1；date raw53147376。
- Army0 / native CArmy0，stored D389474、当前 phase14。
- 全30桶均 ready；只有 phase0 的真实 pointer `matching_positions=[0]` 包含该军，计一次 occurrence。
- stock raw0，capacity raw30000000，rate raw−877192；当前6746名合格供给人数、当前条件供给预算337，独立围城预算67、raid0。预算不是物理扣兵。
- Unit170=0、combat=false、gathering=false、Army gathering count0。loaded levels `[60,10,0]`、fractions `[0,0,5000]`，fleet suppression=false、commander modifier0。
- grace anchor raw53144256、loaded grace30；初始年龄130天，已越过严格大于30的门。两个 journal 均 installed，初始 oldest/latest/failures/overwritten/event_count均0。

以本场 source pair 和实际桶 positions 独立计算，冻结 membership/准入等输入时，下一候选为 **第16个实际自然日**，date raw53147760、D389490、phase0；该时年龄146天。它是观察窗口，不是实际 future callback、337人实扣或完整30日结果。

## 第16日实际结果

目标 after-full 已落地并由本线程完整读取一次；初始 full 也只读一次，中间大 full 未读。目标帧为 snapshot `native:53`、public revision54、native revision53、date raw53147760、connection generation1，同一 Run5、Army0/CArmy0；stored D389490、实际 phase0。原件和 scoped physical 字段见[实际生产消费](evidence/episode04-r211-zero-stock-physical-12004/R211-DAY16-PRODUCTION-CONSUMPTION.actual-a01.json)。

前一日的[独立小回执](evidence/episode04-r211-zero-stock-physical-12004/R211-DAY15-JOURNAL-PROJECTION.original-a11.json)实际为 day15、date raw53147736、native49/public50/gen1/Run5。其 callback fence92、writer fence2615；目标日 writer oldest2328/latest2839，所以单日 fence 仍在完整保留范围内。writer 已全局覆盖2327件旧事件，初始 fence0 会真实产生 gap；本次没有用这个 gap 去否定仍完整的目标单日，也没有声称完整16日总量。

生产 `join_actual_supply_parent_writer_observations_v1`、`select_actual_zero_stock_supply_preferred_12004` 和 `classify_actual_loss_component_12004` 已实际消费该目标原件：46条目标 writer 全部 keyed join、unknown reasons为空；共同自然 callback sequence/token93、thread2464、depth1，caller return为 `2A9AB4B`，前后均同实例和 Province1506，库存0→0。

| 实际来源分量 | writer数 | 正物理debit writer数 | complete unique physical debit |
|---|---:|---:|---:|
| supply preferred /return24E35FF | 23 | 17 | **337** |
| siege_or_raid preferred /return24E377C | 23 | 15 | **67** |

23条供给 writer sequence为2756..2778；后续23条围城/劫掠 writer为2779..2801。它们都复制同一parent token，但调用点分量不同，67不计入供给337。46条物理debit均可读，计数中包含合法的零变化 writer。当前Army人数6746→6342，净减404与337+67算术吻合；来源归因来自每条物理写入，不从净差倒推。

每条正供给 writer 在实际写入入口观察到的stock均为0；库存0→0不等于没有更新。回调后 `+188` 已写成当日日期，后验当前getter重新计算的供给预算是317、围城预算63，不能用这些后验预算改写刚才实际扣兵337/67。

这证明**受控初始化低库存后的自然供给 callback，在零库存时实际扣减337名物理兵员**。它不证明库存是自然耗尽，不把全部404统称饥饿或死亡，也不授予固定每月5%、完整周期总量或一般未初始化战役的结果。初始化 fixture、自然结算和物理写入分层保留。

本线程没有操作游戏或正常闭场；Save/OFF读回与OS正常退出由Root现场 owner另行验收，不能由本物理正例替代。视频是否覆盖该callback时刻、人工1×审片和签核仍须单独确认。

## 供其他机器和智能体离线使用

[重放入口](evidence/episode04-r211-zero-stock-physical-12004/replay.py)只读取保留的目标证据和[生产消费者 pins](evidence/episode04-r211-zero-stock-physical-12004/REPLAY-CONSUMER-PINS.actual-a01.json)，调用同一生产 join/selector/classifier。一次实际[离线重放](evidence/episode04-r211-zero-stock-physical-12004/REPLAY.actual-a01.json)已通过，复得供给337、围城/劫掠67、46条join且unknown为空；没有新游戏、SDK或当前机器部署信用。

在包含受审消费者源码的仓库中运行 `python -B replay.py --repo <repo> --evidence <target-json> --consumer-pins <pins-json> --machine-id <本次稳定机器ID> --output <新的回执路径>`。当前源码 SHA 不符会拒绝，原来源提交保存在 pins 中。目标机器 ID 使用 `tools/ck3_live_run_id.py machine` 实读；源机器的实机结果只归源机器，其他机器可复用数据、知识和代码，不外推其安装或运行资格。

## 正常闭场与本次采纳补注（2026-10-18）

`machine_id: desktop-3fevhd2-1c74096080`；本次整合依据 Root 的 R211 闭场采纳指令。
上文研究线程封包时的 Save/OS/录像 pending 是当时事实；随后现场
[monitor 原件](acceptance/2026-10-18-r211-r05-normal-close/monitor-result.actual.json)
实际证实16天、Save verified、采样 OFF/clear、retained OS exit0、normal-close-qualified 与原 host Popen exit0。
该原件早于资源释放，内部 not-assessed 不改；后续
[Root 释放原件](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r211-window-take02/resource-release.json)
另证 keeper STOP、原 allocator exit0 和 CAS6624 resources[]。

Root 已采纳这条受控初始化后自然 callback 的供给扣兵核心：研究10/14（71.43%）、
基本业务7/11（63.64%）。只新增 R05 一项；不把自然耗尽、死亡、整周期或合计404全部供给化。
[媒体小原件](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r211-window-take02/media-review.json)
记录971.2267秒、29037帧、1280×720客户区、唯一 Finish/Job0、全解码和5/480/960秒三个 AI 样本。
画面6746→6342仅支持净变化；337与67来自上文 native strict proof。
连续 clean、人工整片1×、正式镜头签核仍未完成，合格动态0/11、ABC0/3。
589,432,005 B raw 与三 PNG 仅保留来源 pins，没有复制入 Git。

本次还保留[launcher 原始读回](acceptance/2026-10-18-r211-r05-normal-close/launcher-race-readback.actual.json)：
exists 后解析 host-started 的 JSONDecodeError 不抹去真实 host 已启动事实；未保留瞬时0字节正文，不倒造该原件。
后继源码只在原45秒 deadline 内重读该 ACK，接受完整原件后才返回 started；不重复 Popen 或 launch。

供后续 agent 读取的[采纳记录](evidence/episode04-r211-zero-stock-physical-12004/integration-adoption.actual.json)明确仅闭合这条 R05 primitive；[媒体来源索引](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r211-window-take02/source-index.original.json)保留机器路径映射与不复制 raw/PNG 的边界。
