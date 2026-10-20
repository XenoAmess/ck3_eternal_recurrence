# E04 R08 / B：下一处实际入口

机器 `desktop-3fevhd2-1c74096080`；本次离线核对时间和 20 份源码/小原件精确 pins 见 [离线来源检查](evidence/episode04-r08-b-next-20261020/retained-inspection.actual.json)。稳定 ID 已重新读回。来源事实按原时间保留；本包没有 SDK、CK3、屏幕、构建、EXE 读取，也没有新业务通过数。该离线包输出限256KiB，未申请/消费重型写入额度。来源检查发生在整合前的只读阶段；本页和单站CLI随后按Root指令整合，整合回执另存。

## 优先级与可立即采用的窄结论

先完成 Root 的 R04 独占现场与正常收束。本卡不加进 R04 的动作或录制前置。其后如当前同进程仍有合法暂停窗口，B 与 c/d pilot 可以分别重新准入，不要求为它们重启游戏；不可沿用 R04 的许可、一次动作、时间或 debugger 配置。两种 pilot 分时执行。

本次新增可复核的来源边：a38 exact source `3e7d337dc4edadde26642ad23fee85df5e41ecf9` 的 supply journal 与当次被读文件具有相同 Git blob `46e5bd8fd016589d1285a12ac1256e07d25985df`，该文件已包含事件前后 Province 捕获。a38 的历史生产资格原件为实物，`production_bytes_qualified=true`。所以 B 不需要新增 native 代码；已有 a38 已编译包含这段来源，不应继续把“native 编译”笼统写成尚未做。新的 source/DLL/runtime 仍须各自绑定；这不证明 a38 有真实 Province 样本或两站增长。精确生产资格 pin 在 inspection 中。

## R08：先采 c/d，不再沿已持 worker 栈盲扩

**目前真正可执行且无需新 native 的入口是固定四槽 write observer。** 其 DR0=2C0、DR1=2C8、DR2=28、DR3=30；c/d 已在槽2/3。先得到一个实际 c/d `RIP_after`，才有新的 producer source 起点。重复 current-cash query 本身不会给出 writer PC、调度对象或 cadence。

仓库入口：

```text
ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/build_card.py
ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/ROOT-CONFIG.template.json
ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/select_cd_writers.py
```

Root 用新 source、独立 expected identity、fresh snapshot/cash 和不存在的 watch 目录填模板。先运行：

```text
<verified-python> -B -O -X utf8 build_card.py --config ROOT-CONFIG.actual.json --output ROOT-ARGV.actual.json
```

依卡 `prepare_argv` 运行既有 `prepare_writer_admission.py --prepare-only`，成功后以 `Popen(ADMISSION['argv'])` 原数组启动。不能拼 shell 字符串，不增添未知 flag，不加后来源码才有的 copy-caller 开关。模板历史 build-a07 路径在本次仍存在，但本次没有读取/执行 EXE，也不授新现场 SYSTEM/observer 资格。实际 native argv 固定为：

```text
maintenance_writer_cold_observer.exe
  --enable-ck3-12004-data-watch
  --fixture-meta NEW/CURRENT-RAW-ADMISSION.meta.txt
  --timeout-ms 30000
  --raw NEW/writer.raw.ndjson
  --ready NEW/writer.ready.json
  --expected-hits 128
  --machine-id <actual-machine-id>
```

公共输入方法是 `ck3_take_snapshot` 与
`ck3_query_war_cash_current_resources_private_v1(expected_revision=F.revision, payment_sampling='query')`。
需要独立匹配 PID/create/gen/actor/revision/native/date/episode/window/epoch；raw context ready/stable；journal ON/idle/active0、read_complete、failure0、same-owned-no-load。若当前 OFF，采样启用按原合同由 Root 另做一次并独立读回；不能靠本卡 enable。必须明确 external-debugger 专场，不能与 R06 DR 或其他 debugger 同时附加。

先 ready 真且当前 Popen 活着，才按已有 exact-clock 进行一个**预先指定**自然机会。30秒/全槽累计128 hit，先到即结束；a/b 先占满或零 c/d 是本次未取得输入，不是无 writer/零军费。保留实际 cleanup/restored/detached、pending-event、线程 generation/DR readback。结果未知不再 attach。结束后 fresh payment/cash 原件独立归档。

随后执行卡中的现有 consumer 和 c/d selector。新的最小 source 输入是 clean same-image c/d `RIP_after-1` 所属唯一函数的 `.pdata/root`；metadata≤512B、code≤8192B、≤48reads，从入口解码到恰好结束于 post-PC 的 store，并核有效地址。只得 copy 就只闭直接输入，不给业务标签。军事类别→同次 NET→payer→cadence 分开结算。

**dispatch 路线确需另一份新观测，不伪装成现有 query。** a03已纠正：290DC00 的 task+0 为 atomic cursor；3F90A6F 的 dispatch object 是 `*(job+38)`，两者不能混用。下一最小 typed record 应停在已持 worker virtual call 3F90A6F，保存原 job(RBX)、RCX dispatch、RAX actual vptr、`[RAX+10]`真实 target、原始 RDX/R8/R9/RSP 与 same-image/thread/session/clock。之后只读真实 target 的唯一有限 body，查实际参数调整；不预填 thunk，不用相邻 stack/date join。现有四槽 writer observer没有执行断点/dispatch模式；若走此路线，需要专用有限 observer/ABI实现和独立冷资格，不能改 argv 假装已经支持。constructor/enqueue/calendar PC还须真正同实例的 producer record；selection后的writewatch无法恢复过去构造。

建议 R08 最小现场 case：单 payer、单30秒机会、原 observer，不改 native。预算提案为新增 driver/SDK 与小原件 **128 MiB**、raw/stdout/observer端点 **8 MiB**、source后续≤16KiB；profile/存档/共享host仍计 Root同一账，不另复制。8MiB 是估计上限提案，不是 native 的新 raw-limit flag；达到 Root meter 前停止后续 SDK/推进并按合法清理收束，不能强杀已 attach observer。当前没有重型准入。

## B：先找当前库存余量；合法抬容量可省掉耗库存准备

最短同进程路线先从当前 paused snapshot 的真实可控军队选择。优先已有 `0<=stock<capacity`、当前正率、真实 resupply eligibility、静止无战斗/撤退的军队/省份。当前就符合时无需换帅、拆军或先走别省。

若现军 stock==cap，不要在原地等“+20”当增长。**可以先查询一个合法提高容量的候选，正常任命并独立读回，从而建立真实 headroom。** 这是本次补出的具体准备路线：不必先等负率消耗若干轮。只从该军 fresh candidates 中取 `available/final_eligibility_observable/can_assign=true`，用既有 strict conditional-capacity normalizer核精确来源及整数公式，并要求条件容量>当前 stock；然后仅提交一次正常任命。任命后重新核真实 commander、stock/cap/rate/eligibility，出现实际 `stock<cap` 才进入 pilot。条件容量不等于实际容量，也不保证 rate 保持正值。

R0177 coastal S0 的 Army93@2624、stock/cap100/100、+20和返程候选2619只是历史 fallback。保护存档本次 stat 仍存在且大小71,631,396B相符，**未重hash/未freshload**。R196在Army18的31254/34973高容量观测不能直接授Army93可任命资格。Root正在R04时不加载该旧S0；若现军没有合适余量/候选，才另提正常输入，不干扰R04。

第一轮最小 4 个实际只读请求（统一绑定 fresh F）：

```text
ck3_take_snapshot(include_native_command_history=false)
ck3_query_army_strengths(army_ids=[<actual public FullID>], expected_revision=F.revision,
  ordered_refill_entry_mode='observed_prepared',
  ordered_besieging_entry_mode='observed_prepared', profile='observed_history_full_v1')
ck3_query_army_commander_candidates_v1(army_id=<same>, expected_revision=F.revision)
ck3_take_snapshot(include_native_command_history=false)
```

full原件必须取成功响应的精确 `army_history_evidence.raw_result_reference`；compact summary不足。ordinary_core_v1省略retained journals，不能用它取本站增长证据。需要当前 full DATA、ArRg/max/backlink、双Army/full native身份、commander、stock/cap、当时Province、真实 CDate64 与实际 callback fence。

callback 是独立常驻 journal，512个全局事件，不属于九族 sampling family；**没有 supply enable flag**。源码正常调用原callback一次。query只读 owned journal，不触发 updater。跨前fence有丢失、Province null/跨省、捕获失败、身份/统帅/DATA/max变化时不授本站资格。

如决定换帅，用现有
`ck3_assign_army_commander_v1(army_id, commander_character_id, expected_revision)` 一次，随后独立重新取 typed commander、full strength 和 snapshot；不把动作内 readback独占当唯一后验。新原生结果未知只读恢复，不重投。

进入驻定pilot时把此刻冻结为**该站采样 T0**，与正式ABC T0分开。既有Root exact-clock `terminal-a-0`、speed5、Arm start→start+24、Resume一次、独立暂停snapshot和clock status；未知modal按当前AGENTS续行。至少保存这一个精确自然日两侧完整 endpoint。不需要先split。一次机会没增长时按事前有限天数继续或到界闭场，不用月getter保证结算日。建议最先只准入一个 exact-day case；根据它的实际体积与native bucket/admission再决定后续≤32日窗口，不能现场无限延长。

第二省只从实际preview候选筛选，第一候选可沿当前真实war/campaign collection。旧2624↔2619只作候选，仍fresh `ck3_execute_step(step='preview-move-army-<actual>-to-<P>', expected_revision=F.revision)`，核完整路线/战争风险，正常Move一次且独立到站，再冻结该站独立采样T0。**同一army可以先后取两处Province**；现consumer只要求两省distinct、同actor、事件key不复用，并未要求pilot先split或必须同进程。真实第二省需要仍有headroom；第一站涨满则重新按实际条件决定，不能改库存或伪造差分。

## B 原件形状与第一站可立即封存

新的 [qualify_one_b_site.py](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/qualify_one_b_site.py) 是单站只读CLI，直接调用已有 `strategy_b_site_growth.qualify_site`，不复制增长语义。第一站成立即可运行，不必等第二站或正式B计划。输出保留 `two_sites_qualified=false / formal_ABC_completed_arms=0 / B_live_readiness_granted=false`。

新wrapper已在项目 `tools/.venv/Scripts/python.exe -B -X utf8` 通过两个实际 focused compound：现有synthetic正链→真实CLI→现有consumer→输出单站；移除事件Province→拒绝且不留成功文件。只为新wrapper验接线，不重复旧矩阵，不是真实增长。普通系统Python因无`jsonschema`在import阶段拒绝，未安装依赖；使用项目已有venv即可。回执见 [原始focused回执](evidence/episode04-r08-b-next-20261020/single-site-wrapper-check.original.json)。

```text
<verified-python> -B -X utf8 promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/qualify_one_b_site.py --evidence-root SMALL_ROOT --site-input SITE.json --site-input-sha256 SHA --output SITE-QUALIFICATION.actual.json
```

CLI按自身位置导入同目录公共consumer，自动定位仓库，不含机器路径。可选`--repo`只兼容显式调用，并须等于当前checkout。整合后只验证这处相对路径调整，不重跑原两项focused；详见[整合回执](evidence/episode04-r08-b-next-20261020/integration.actual.json)。

最小SITE（所有pin均为SMALL_ROOT内path/bytes/sha256）：

```json
{
  "schema": "xar.e04.B-rest-site-input.v1",
  "province_id": 123,
  "army_id": 0,
  "runtime": {"path": "runtime.json", "bytes": 0, "sha256": "ACTUAL"},
  "normal_day": {"path": "normal-day.complete.actual.json", "bytes": 0, "sha256": "ACTUAL"}
}
```

上述数字是schema占位，不是现场默认。runtime用现有ARM runtime schema：machine/source/DLL、PID/create、gen/actor/episode、started_at_utc/source_proof。normal_day complete含：

- `machine_id/source_head/binding/plan/helper`；绑定实际runtime与pin；
- `claim`原件pin，原claim保留相同header、`before/previous_complete/start/target`及原Arm/Resume一次记录；
- `before/after` endpoint（day、snapshot、完整army_result、strategy_army_ids、commander source/pointer、loaded_features source/pointer）；
- `day={day,clock_source,paused_snapshot,strategy_army_ids}`，`previous_complete`与`qualified=true`必须由真实Root一日检查产生，不能由本wrapper合成。

每站pilot计划用自身真实 T0、实际build/source/DLL、原始完整团ID等现有consumer字段。多日链从该站day0连续，末日两侧同省/静止且库存正差；所有新callback要同完整CDate64、前后Province=该站、stock链连到端点。正式B `strategy_b_normal_stages.py`假设已经split/rest等状态，因此不直接拿来启动site pilot。Root现有clock/endpoint采集足够，若其输出尚非normal_day形状，仅需一个**Python原件adapter**将实际pins和原一次claim组装成上述形状并调用consumer；不需要 native hook、新SDK或绕过B阶段。

两站齐备后再调用既有 `strategy_b_site_growth.py --repo ... --evidence-root ... --plan ... --plan-sha256 ... --output ...`，不把单站结果当正式B或ABC完成。

## B 分阶段预算提案

以下均为待Root同一卷账采纳的上限，不是已授权额度，也不按lane各领host/profile。实际per-file16/32MiB与全量logical总额分别守卫。

| case | 本次可执行范围 | 新增logical提案 | 硬停止 |
| --- | --- | ---: | --- |
| B0只读筛选 | 2 snapshot + 1 full strength + 1 commander | 96 MiB | 无合法headroom/正率/省份身份则不推进 |
| B1单站单exact day | 真实before/after full端点、typed commander、Arm/Resume/status、claim/小记录 | 192 MiB | 首个合格增长即停止本站；身份变、失journal/unknown动作、预算/时限先到即收束 |
| B后继日 | 若事前采用≤32日窗口，按B1实际新增量估算并原子追加预算 | 不预发 | 不在192MiB里假装包含32日；样本约10–11MiB也不保证未来相同 |
| 录像 | pilot默认不新录像；已有现场若采镜头须Root单独绑定 | 0 B本卡新媒体 | 现成R04 recorder的范围不能挪给本pilot |

这套预算包括SDK response与完整sidecar两份可能同时存在，不只计compact JSON；profile/userdirs/存档另计共享现场总量。当前inspection中的free只是只读快照，系统增长预留、其他未消费预留、项目占用/配额均未由本lane核全，因此本卡不授重型写入。

本包目前实际交付为：精确来源检查、一处新的单站消费入口、可落地的公共查询/正常准备顺序与分阶段预算；R08新c/d PC、paid/payer/cadence仍unknown，B增长0/2、ABC0/3。review180日，外置派生helper48小时复核；未续期旧save/raw保护，不产生永久pending台账。
