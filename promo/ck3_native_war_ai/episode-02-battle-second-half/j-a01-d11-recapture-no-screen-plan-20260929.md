# E2-06/07 第 11 日增援：下一独立录制的无屏准入计划

2026-09-29 CST。当前 d06 受管 CK3 独占屏幕；本文件只安排下一次**新**第 11 日
attempt，不触屏、不启动游戏、不读 J-A01 原 raw/完整 ffprobe。旧 J-A01 仍为
`ENCODED_UNREVIEWED`；它的原生 battle-control 缺失，按 #451 `e4957f17e`
正式 E2-06/07 reel 输入合同为 RED。详情见
[J-A01 adapter 准入](j-a01-adapter-admission-20260929.md)。

## 可复用但须重新冻结的配对

- 源 save：`D:/workspace/ck3_native_war_ai_promo_work/episode01-full-edge-attempt-004/trace-d11-immutable.ck3`，
  52,408,560 B，SHA-256
  `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953`。
- 原生保存 sidecar：同一 `episode01-full-edge-attempt-004/ck3-output/interactive-requests-responses/trace-d11-save.json`，
  13,397 B，SHA-256
  `DD986180C7E9C4B42D43FC634884F5294387D18CF8F798012FAD621B37E9E4A5`。
- 本轮当前文件各重验一次 SHA，均与历史回执一致；旧 J-A01 隔离 profile 的副本
  `war_film_checkpoint.ck3` 经只列路径确认仍在，本轮未重新哈希其当前字节。
  新 attempt 必须从原件另作只增复制、记录源与副本 bytes/SHA，不能把旧
  `checkpoint-copy.json` 或旧 profile 路径当新 attempt 的复制证明。
- 源帧期望 actor 29829、date_raw `53146488`、WarID 4、ArmyID 18；后一日应是
  `53146512`。这些只是新冷载的拒绝门，不凭旧回执自动宣布新运行匹配。新 EXE、DLL、
  injector、pipe、profile、输出根、screen lease 和 fresh Steam 离线像素均在未来独立
  attempt 重新绑定。旧 2026-09-27 DLL SHA 不自动代表新二进制可用；当前 helper
  `bind_session` 仍固定 `JOIN_DLL`/`JOIN_INJECTOR` SHA，新二进制若不同须先显式改
  d11 track 合同、静态测试并独审，不能跳过这个绑定。

## GUI 100% 与完整下半面板门

旧 J-A01 在 1920×1080、`GUI.scale=1.3` 下把下半战斗面板裁出屏幕；逐团和战宽
若要作为可见 UI 事实，必须重新拍。E2-05 a02 证明过 **其自身** 2560×1440/原生
GUI 100% 的战斗窗上半和骑士行可见，不能外推到新 d11 画面的下半逐团字段。

1. 先做无启动 preflight：唯一新根、新 profile/pipe、原 d11 save/sidecar、所选
   EXE/DLL/injector 的实际 SHA、无现存 CK3 冲突和严格 `--gui-scale 1.0` 意图。必要的
   `capture_session.py` `--import-a04-ui-gui-100` 目前**只准既定 day-26 配对**，
   不能拿它为 d11 绕过源门。若复用原生 UI 保存的 54 B `value="1"` GUI block，
   先另立 d11 精确配对且固定来源 SHA 的显式 opt-in、静态负例和 no-launch 回执；
   否则由新运行的原生设置页 SaveAndClose 后，以新保存原件、解析器和画面门证明。
   单纯预置 `1.0` 曾被 warmup 改回 `1.3`，不能作为放行事实。
2. 未来屏幕持有者完成 fresh Steam 离线、独占 lease 后冷载，检查 warmup 后、final
   launch 前、postmap/posthold 的**磁盘** GUI block 与原生热点回读。若 native UI 将
   100% 写成 `value="1"`，须由本次明确授权的 parser gate 接受并绑定整块 SHA；
   不能把旧 parser 对 `"1"` 的 RED 当成画面 GREEN，也不能对当前 d11 用 day-26
   专用 opt-in。
3. 开 recorder 或推进日期前，以本次原始桌面截图核真实 GDI 与 pyautogui
   2560×1440（若实际另选几何则按实记录），战斗窗顶部、两军人数、日期、CombatID/
   WarID 对应身份，以及**所要主张的下半逐团列表、当前人数与战宽控件**完整、无裁切、
   无遮挡且文字可读。需要的控件若原版 UI 本身没有，明确改用标注原生 trace/计算卡，
   不伪称 UI 可见。任何 RED 只保存该 attempt，不开 600 秒正式 raw。

## 同帧 control、trace 与 marks 顺序

**启动前工具门。** 原 J-A01 所用 `remaining_live_step.py` 的 `e2-06-d11`
`spec.control=false`，`advance` 不查询 d12 的 post control；原样复跑必然再次留下
`control=null`。本计划须使用已改且经独立静态复核的 helper：d11 `observe` 查询
battle-control 并分别验证 wrapper/native revision、`snapshot_id`、日期、ArmyID/
CombatID（真实 086 源帧 wrapper `5`、native `4`，两域不可互换）；`advance` 在任何游戏动作前
核其原始 response SHA 已进入 `d11-before` mark，再于存档后重查原生 control，
只在同帧验证通过时启动 trace 和单日动作；d12 暂停后再次查 control 并把 response
SHA 交给 `d12-after` mark。`record_bounded_gameplay.py mark --control` 已支持此绑定，
但该参数本身不会发起原生查询。缺回执、错 revision、异 CombatID/ArmyID、缺 mark
或重复推进均必须在静态负例中拒绝；`finish` 还须只读核 d12 mark 的
`control`/`report` 与 advance 响应 SHA 完全相同、截图仍同字节、marks 与 recorder
封口哈希一致；并核 advance intent 中冻结的 recorder intent/start 身份仍是同一
recorder，封口 marks 逐字节保留 d11-before 追加前缀和唯一原 mark。这个后验失败要保留
RED，同时仍请求 CK3 清场；同屏新 attempt 前须有
独立审阅 GREEN。
若**已经执行**单日动作而 d12 查询失败，保存该动作和失败请求为 RED，不能声称
动作被撤销，也不能落正式 `d12-after` mark、继续推进或借其他 run 的 control 补证。

1. 第 11 日暂停源 snapshot 后，在无日期/游戏状态变更间隙调用原生
   battle-control 查询，针对 **ArmyID 18** 保存原始 request/response，读回
   actor 29829、date_raw `53146488`、WarID 4、CombatID 16777218、ArmyID 18
   的真实战斗成员集合，并核 wrapper/native revision 与 snapshot 同帧；仅能力字符串
   `query_supported=true` 或 private begin 的 CombatID 不够。先判断正式
   `subject_combat_membership_verified=true`，否则该运行停止正式取材。
2. 新 recorder 自然开始并证明 gameplay HUD 后，在仍暂停的同帧落 `d11-before`
   mark；把上述 battle-control 原件填入 mark 的 **`control`** `{path,bytes,sha256}`，
   同时保存当次 snapshot `report` 和原始 `screenshot`。mark 的单调时钟/UTC 只作墙钟
   导航，不转成媒体 PTS。
3. 开 private join/width trace，提交**恰好一次**受管 d11→d12 日期动作；helper 内部
   先完成 private trace finish，随后在暂停的 d12 帧保存新 snapshot 与新原生
   battle-control（同样核 actor/WarID/CombatID/ArmyID、date `53146512`、
   wrapper/native revision 与成员集合），再由操作者落 `d12-after` mark 的 control、
   report 与 screenshot；不得额外调用第二次 trace finish。核同 run ArmyID 22、13 个团、2570/2560、
   缓存重算、战宽 `1480→2220` 与第一次伤害实际参数；若与旧 A01 不同，卡与口播
   必须使用新 run 数据重算。
4. 录制自然封口并清场、显示恢复、释放 screen lease 后，独立做完整原片 PTS 审计。
   此时才按最新正式 `xar-promo` Release 和显式解释器开新 append-only adapter
   `prepare`，核 source manifest 实际含**两份** mark control 的 SHA。然后按 1×
   看完整 raw，选真正可见的段和 exact frame PTS，逐端点抽帧，再由真人签入
   `human-review.json`、`package` 和独立 clean-span audit。正式 reel 仍要求同 attempt
   卡重算、来源标签实片可见、六章 reel 审片和最终成片签核。

新 run 若只有 trace、没有 battle-control，或控制回执只属于旧 085/旧 J-A01，
正式 reel 准入仍是 RED。任何复查不能改写旧 J-A01 的原件或把机器 PTS 搜索窗称作 clean span。
