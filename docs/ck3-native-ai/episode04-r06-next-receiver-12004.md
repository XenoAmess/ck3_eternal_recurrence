# Episode 04 R06：a26 当前失败层与下一次 receiver 实验

R183 的 a26 **已经执行补员 receiver 候选读口**，两处控件都在第一个 capture pass 触及 **8-context 上限**。它不是“没有 candidate”，也没有证明 R182 的旧 `candidate_memory_unreadable` 已彻底消失。下一项应是新场暂停后沿现成原生入口打开军务窗口，取得可见后验，再读取一次完整树；当前不具备实际 receiver、补员 toggle 或实际 ADD 资格。

`machine_id: desktop-3fevhd2-1c74096080`；离线复核时间 `2026-10-16T09:03:08Z`，仓库源点 `20c7319b6964c80fa419540cf4e30852feff4810`。稳定机器 ID 已由 `tools/ck3_live_run_id.py machine` 当次读回。本文只解析既有小源文件和 R183 原响应，没有连接 SDK、运行游戏、操作桌面、构建或重新读取游戏 EXE。[机器可读摘要](evidence/episode04-r06-next-receiver-12004.json)保留精确来源路径、bytes/SHA、实际帧与候选状态；其他机器可复用代码与判据，须另验本机版本、权限、容量和实机状态。

## 当前已经定位到哪里

[R182 原失败](evidence/r182-refill-reader-failure-12004.json)只有粗粒度 reason：两个固定补员外层控件都返回 `candidate_memory_unreadable`，没有 partial 诊断。旧 reader 把 count、required-null、active、真实读失败等都折叠成这一原因。a26 的三处来源修正和诊断合同见 [type635 reader](military-refill-type635-candidate-reader-12004.md)：允许祖先空 definition，正确终止已不再 pending 的 receiver，不读无关后续父链。

R183 新响应实际时间为 **06:58:42.782312 UTC**，原件 936,825 bytes、SHA-256 `85d06c9afd8b8cbb181be551c4e8428b9142d799b735761d343597aaeb4fc773`。直接 `/body` 为完整506控件树，`root_available=true`、`truncated=false`，`military_view` 根仍 hidden。两处外层路径是 `0/0/0/2/3/0/0/0` 与 `0/0/0/3/5/0/0/0`；两者 enabled，effective_visible=false。SDK 的镜像不另计一次采样。

两处均保持已闭表达式 `3AA30E0 → 3A9F960`、chain0、finalkind3、target `1303D40`、receiver type635、flag0，且都实际包含 `receiver_entry_candidates_12004`。共同结果为：

| 字段 | 实际值 | 可用解释 |
| --- | --- | --- |
| reason / stage / kind | `candidate_parent_depth_exhausted` / `parent_walk` / `parent_depth_exhausted` | 本次采集按政策上限停止；不是 memory API 失败诊断 |
| capture pass / read ordinal / depth | `1 / 51 / 8` | 首次采集就未完成，不存在成功双捕获 |
| declaration count / index count / local active | `1 / 1 / 1` | 已经过 declaration/index 与本地 active 读入阶段；不代表运行期 receiver 已选中 |
| variable index / declared key / entries | `null / null / []` | 失败结果明确丢弃未完成候选，不能把 diagnostic 拼回 available 数据 |
| stable double read / selected / variable table observed | `false / false / false` | 当前真实 receiver 仍未确定 |

实际绑定为 PID7640、generation1、native_revision3、pump30923、ticket2、thread23912、played FullID31254、date53147928；public snapshot `native:3`、revision4、episode `native-31254-f71419cd501a`。这些是 **R183 的历史帧**，不能直接填进下一场请求。

这让当前缺口收敛到已访问 context 链在8层内未结束。它没有回溯证明 R182 究竟命中了哪个原始错误，也没有证明隐藏状态导致过深；“打开后可能改变绑定”只是下一项需要检验的假设。GUI child_path 深度与语义 context 链层数也不是同一个量，不能按控件深度推定应放宽多少层。

## 下一次只做一个有界现场实验

由 Root 沿既有唯一 live endpoint 执行；先完成当次容量、Steam 离线、实际 EXE/build 与 runtime actor 资格。R183 原容量截止已过，本文不续期，也不把旧准入授权下一场重型写入。新 snapshot 必须 `paused=true`、`map_ready=true`，记录其当前 public/native revision、date、episode、PID/create-time、generation 和角色完整 ID。

1. 使用已实现 `ck3_execute_step`，参数 `{"step":"activate-ingame-military-v1","expected_revision":<新snapshot的revision>}`，**最多提交一次**。实现入口是 [ingame_military_open_12004.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_military_open_12004.py)，走固定原版 topbar 语义、owner/modal/frame 和 once claim，不靠坐标或按键。
2. 读取该调用的实际后验。现有 opener 自带最长5秒的只读 later-tree 观察，必须看到完整 `military_view` 根 effective_visible=true，且暂停帧/episode 未变，才返回 `status=verified_visible`。原生刚派发后的 `native_after_visible=false` 可以随后变为可见：R182 就保留了这种 native ACK 与 later-tree 差异。只读观察成功以前不能把 ACK 写成“窗口已打开”；调用报错或结果未知不重复提交。
3. 在同一暂停身份下，用既有 `ck3_inspect_gui_window_tree_v1({"window_kind":"military"})` **再显式读取一次**。此方法 [native_driver.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py)已自动保存前后 snapshot 并绑定候选帧；不要另开 capture 脚本的新 endpoint。比较两处 source-qualified 外层的实际新表达式、candidate 与诊断，保存直接 body 的小投影与原件 SHA。
4. 到此结束本实验，不顺手 toggle、执行 provider、猜 Character 或等待一个月。已有窗口可见事实与 receiver 资格分别报告。

成功判据分两级：**诊断实验成功**是打开后的完整新树和同帧诊断可读；**候选采集成功**另需 leaf available、稳定双捕获、declaration/key635、合法有序 entry、全部 frame/public binding 验证通过。即便两级都通过，`current_variable_table_observed` 与 `native_receiver_selected` 仍为false，不能宣布 getter/toggle/实际 ADD 完成。

停止判据是身份/版本/source pin或预算变化、窗口5秒内未获可见后验、树截断、源控件表达式失配、leaf unavailable，或同样8层上限再次出现。遇到最后一种结果，保留原 reason；不要扩大任意内存扫描、无限增加深度或连续重开游戏。后续 source 改动应先独立定义有限新上限、最坏读数和20ms预算，并加精确父链/缺失definition反例；没有这些输入前不能热改 cap。

## 两个仍可改进的 reader 实现点

这两项来自已保存源码的离线比较，没有修改 reader，也没有声称它们已造成 R182/R183 实际失败。

**首个 key 命中后仍扫描尾项。** 当前 [reader header](../../ck3_autonomous_player/native_bridge/include/xar_bridge/gui_refill_receiver_candidates_12004.hpp) 的 `for(n<entries)` 找到首个匹配 key 后，只设置 `matched`，仍逐项读取剩余 key。已持879B原始 `3AC3EF0` 在 `3AC3FE0/3AC3FE3 → 3AC3FF0`，以及父层 `3AC4164/3AC4167 → 3AC4174` 都在首个匹配时直接结束查找。当前 reader 因而可能在 native 不需要的尾项读失败或耗尽预算后，把本来可用的首个候选拒绝。后续最小修正可以停止尾项读取；相应双读身份仍比较查找实际经过的 prefix 和完整匹配 entry。需要的新反例应包含“首项命中、尾项不可读”，而非放宽所有 read 失败。这个问题会额外增加 unavailable，当前没有证明它造成业务误选。

**depth-limit 诊断带上一层字段。** `ancestor_depth=depth` 在上限检查前赋值，而 `raw_definition_entry_count/definition_present` 在其后才 reset。故 R183 `ancestor_depth=8` 时的 `definition_present=false` 来自最后已访问层的进度，不是读取过第8层 definition 的证据；`context_present=true` 也只记录最初 callback context。它不能被报告成“第8层 definition 为空”。将来诊断可以在 limit guard 前清空按层字段，或明确给字段附来源层；现阶段消费者须按失败进度读取这些值，不能拿它们构造 receiver。

相关 source pins 在机器可读摘要：receiver header SHA `227ccc94…9466e3`；原始879B `3AC3EF0` SHA `476ac967…5b5a2a7`；449B `3AC1C00` SHA `8efccb73…6e43cfc`。这是现持原件的有限复核，不是新增 EXE 读取计划。

## receiver、toggle 与真实补员还差什么

| 输出 | 达标所需 | 当前边界 |
| --- | --- | --- |
| 真实 GUI receiver | 运行期 variable/index/type635 的实际选中值，或独立闭合且有当前资格的等价解析 | 当前候选读口只列 definition entry，故永远不自授 native selection；dynamic provider 的 slot2 只是一条后续源码入口 |
| 当前来源 owner 与开关 | 从合格 receiver+218 得完整 Character，拒绝 fallback；同代际独立读 Character+1C0 military 的 raw4A9/enabled | 不能用 callback+F0、当前玩家31254或 Army 的政治归属替代 GUI receiver；mode1 direct owner 也仍只是候选来源 |
| 正常 toggle | 固定补员 profile 的原生 once dispatch；独立读回同一来源 owner 的预期 raw4A9 | 当前 `click_action_available=false`；现成 Military opener只开窗口，不是补员按钮 action |
| 单条实际 ADD | `.4 2A98B88` 真正指令前后、Regi FullID/physical slot/q/当前值与完整 runtime 身份、清理 | [冷夹具](episode04-refill-hardware-add-cold-qualification-12004.md)只验 synthetic，不等于 CK3 attach、自然父调用或业务通过 |
| 开关影响本轮补员 | 同一新 T0 的独立正常 ON/OFF 回放，准备路径缓存与真实 ADD 分别观察，覆盖其他变化 | 当前无两臂新样本；切换开关不直接令 q 乘0，旧 prepared148 可能继续影响 core |

后续 getter/source 边沿 [slot8-copy](military-refill-wrapper-slot8-copy-12004.md) 与 [toggle命令载荷](military-refill-toggle-command-12ff8d0-12004.md)继续追；正ADD目标复用 [现成采样选择](episode04-refill-sampling-target-selection-12004.md)，新场重新查询有实际物理缺额的普通 Army18，不能借R183单帧兵数或旧来源开关凑新帧。R06 合格业务和动态镜头数量本次均不增加。

本次只新增本页与小型JSON，未复制原响应/原片/存档，也未续期旧外置包。记录按 [统一存储策略](../storage-retention-policy.md) 的 record 类在 `2027-04-14T09:03:08Z` 复核；原件可读性与保留期限仍由其原有资产记录决定。

## 09:12 UTC 后续：两处最小来源修正候选

Root随后要求落实上述两个实现点，已对现有 reader 做定点修正：首个key匹配立即停止查找；进入每层时先更新当前context presence，并将该层尚未读到的definition/count置null，再执行depth/cycle guard。8context、每definition256entry、4096读、64KiB、20ms、每tree4capture及全部source/frame/双捕获守卫没有扩大；`native_receiver_selected=false`与变量表未知的合同保持。前文“未修改reader”与原始source pins记录09:03离线复核时点，不能被当作此后代码仍未变化。

[native冷fixture](../../ck3_autonomous_player/native_bridge/fixtures/gui_refill_receiver_candidates_12004_fixture.cpp)补上：首项匹配而尾key不可读、非匹配prefix后第二项命中、prefix不可读仍拒绝，以及depth7已读取definition/count后depth8守卫不能遗留上一层字段。编译若定义NDEBUG会显式拒绝，保证断言存在。Python现有候选/失败合同两文件验证为 **10 passed、29 subtests passed**；新增消费反例确认depth8的null仍是unavailable，不授receiver或ADD。三处修改的diff whitespace检查通过。此时未构建或运行新版native fixture/生产Bridge，Root需在下一合格build中运行该冷target；不以Python结果代替原生断言或实机验证。
