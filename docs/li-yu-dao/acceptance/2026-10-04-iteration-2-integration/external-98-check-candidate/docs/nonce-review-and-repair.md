# I2 旧事件窗口的轮次修复候选

本目录从 `iteration2-admitted-candidate-001` 复制；原目录和既有 65 项测试、原生接口证明及失败 attempt 均未修改。复制前逐文件输入哈希见 `evidence/nonce-parent-input-manifest.json`。本次只修复事件回调授权，不改变原生迁移接口、表决比例、费用、礼仪冷却、领袖退休规则或 I3 共享接口。

## 已修复的 P0

旧 `.200/.220` 对话的取消、签署和确认原先只读取发起者的**当前**提案；旧 `.213/.221/.222` 拒绝回调也可拒绝后来新轮。仅在事件出现时检查 trigger，不能证明点击选项时仍属于该轮。

所有事件突变现在在 effect 内检查保存的发起者、来源礼仪、礼仪序号、条款版本和玩家持久递增的 `lyd_c2_callback_nonce`。发起者对话另外核对当前响应者就是原发起者；零学者礼仪持有者、接收代表和接收领袖的拒绝各自检查实际响应角色。已有票决和同意 effect 原有的角色检查也经共享 context 获得 nonce 检查。

nonce 是玩家 Character 上跨轮保存的计数，不能加入 reset-round 清理表；它与 Rite 上已有的提案序号分开。这样同一玩家换到另一礼仪、遇到相同礼仪局部序号时，旧事件仍不能操作新轮。票据另外保存 `vote_nonce/player_nonce`；重复投票和代表签署匹配完整本轮记录，旧票据不能阻挡新票或充作新轮赞成票。开复核窗口保存当前值，绝不递增或重新绑定旧回调。过期回调检查同一保存 context；不要求已到期的 Rite 锁仍存在，避免阻断清理。

直接当前玩家取消决议仍使用 `lyd_c2_cancel_round_effect`，可以清理失效快照；它不依赖事件中保存的旧 context。事件专用 wrapper 不向直接决议添加隐藏条件。

## 接口与集成

事件 ID、入口决议和交互 ID 保持原样。新增角色回调 wrappers 在现有 effects 文件中，没有新增加载文件。新增 trigger 为 `lyd_c2_initiator_event_context_trigger`；复核和初始事件均从已保存 context 调用。

共享 I3 factory/migration hooks 原样保留，根集成时只加载一份定义。R4 夹具只引用既有 actor/elector trigger 与 Rite ID，无需更改夹具接口。集成本目录生成的 15 文件时，仍必须遵守生成器来源并保留 BOM；不要手改生成文件。

旧存档中的未结束 I2 对话缺少新 nonce/school context，事件突变会拒绝；通过当前玩家取消决议关闭旧轮，再重新提案。不会为旧窗口自动补 nonce，也不会伪造过去同意。

## 复核边界

迁移 scope/比例未发现另一个已经证实的 P0：接收方逐 Rite 对全 Faith 的实际角色收集独立表决，并非按某王国；接收领袖需同意，离任领袖不增加 veto。最终 commit 在任何头衔退休或原生 setter 之前重新核对快照；原生 detach 返回 Faith 后再核对人物、来源主礼仪和新主礼仪。

另有已报告、尚未在本 nonce 修复中改动的合同缺口：同意名单仅包含活着且有地的人类玩家。`source/common/scripted_effects/lyd_c2_setup_effects.txt:103,154`、`source/common/scripted_triggers/lyd_c2_consent_triggers.txt` 的 player consent trigger、生成器玩家计数/刷新与模型 affected-player snapshot 均排除无地玩家。若合同为**全部受影响玩家**，全球 Rite 迁移会影响的无地玩家也应纳入；需要移除同意集合的 landed 过滤并补来源/接收玩家回归。发起者可以继续限有地。此点与 nonce 修复分开，不能因离线测试通过而标为满足完整合同。

仍需 R4 冷载验证：`has_same_core_doctrines` 的类型和运行行为；`every_character_doctrine` 在非 HoR 的 actor/representative 上枚举的具体集合（原版注释为 HoR-known doctrines）；跨 Faith 的 divergence 查询；保存事件数值/scope 的生命周期；非发起者持有的已捕获领袖头衔退休；新动态 Faith 的窄 factory。脚本里存在门禁不等于这些门禁已原生执行成功。本候选不引入假定的 same-core-tenet 接口，也不改变全局 divergence 阈值。

## 离线证明与实机边界

新增 popup 生命周期 oracle 特意通过保存 actor 查找**当前**提案，再传入旧 context；它不是把旧 Proposal 对象交给旧模型后获得自然拒绝。回归覆盖旧确认/取消/签署/代表拒绝/领袖拒绝/持有者拒绝、全部票决及同意、旧条款、跨礼仪序号冲突、非本人的发起者窗口和过期清理；同时检查合法本轮签署和实际模型迁移及取消，防止修复把所有回调关闭。

结构检查绑定每个可变事件选项的 effect 内 gate，并核对发起者选项和 effect 双检查、直接取消决议分离、nonce 不被 reset、首次出票前已保存 context。原有 65 项测试继续保留。新测试只证明模型与生成脚本结构，不是游戏解释器，也不是 L1–L3；原生三轮 R0002 admission 原件仍只授权已观察的两个 primitive，新增同意与领袖流程均 `NOT_RUN`，不宣称零 error.log GREEN。

新离线 runner 允许显式 `--checkout-head` 核对当次只读 HEAD；这仅调整新静态运行的 checkout 身份，R0002 admission baseline、哈希绑定和历史证明不变。最终受影响核验为 85 项 PASS，15 个生成文件精确重现，fresh clean checkout `9015d45e5f1bc06ca756d442c2c530e52e81749f` 未变，见 `evidence/offline-20261004T075815354477Z/offline-report.json`。此前 83 项也通过，但当时根代理已存在的 tracked diff 使 clean 门禁返回 `FAIL_OFFLINE`；原 `evidence/offline-20261004T075141184664Z` 保留，未覆写。新 raw 输出、报告和精确最终文件哈希在本目录新的 evidence attempt 与 candidate-index 中。
