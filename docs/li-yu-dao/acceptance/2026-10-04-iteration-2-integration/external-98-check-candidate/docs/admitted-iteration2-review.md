# I2 外置准入投影与专项复核

本目录候选基于冻结 checkout `588492d3dbf473226664220b722a04b66ae54bae`，未合回 tracked、未启动游戏、未操作屏幕。原 `iteration2-candidate` 及其53项历史离线结果完整保留。

## 证据准入的范围

`evidence/native-admission-binding.json` 绑定实际 R0002 原始 v2、`ed90…82ca` 不可变存档、完整对象投影与 summary、实际加载的探针源码，以及当前原版头衔 factory 来源。验证器重新计算这些文件及 v2 冻结日志的哈希，核对三轮 join/detach、D+1/D+30 计数和 faith108 存档关系。

生成投影的原生准入为 `always = yes`；生成器不带凭证时仍默认关闭。准入状态是 `R0002_PRIMITIVES_ATTESTED_AND_SAVED_GRAPH_BOUND`，只允许使用已观察的原生效果。正式议定事件、权限、界面、共享窄 factory、自然冷却与重载仍为 `NOT_RUN`，没有声称整包 live GREEN，也没有掩盖 R0002 未闭合的错误日志。

R0002 探针先清旧头衔再合流，其 trigger 并未调用本候选的 `has_same_core_doctrines` / same-head 组合。因此原生 setter 已观察成功，不等于本候选所有兼容性条件、动态作用域已经实机通过。

## 必须修正项与本候选处理

1. **旧 faith 备用主礼仪**：ed90 的 faith34/106/107 仍在，并生成 main160/161/162。旧候选用迁入后“没有 rite”才清头衔会失效。新候选用迁入前 `source_singleton` 与原 main=moving 快照判定退休范围。
2. **宗主指针与退休**：普通迁出仍保留 same-core / same-head；只有单礼仪来源、捕获的原 HoF title 精确绑定当前来源faith/holder、且有本mod owned 标记与 ownerfaith 的议案才允许退休该一职位，再调用 setter。接收方 head 不被替换。多派来源、共有同一 title、外来或未标所有权的 title 不进入退休路径。
3. **旧领袖额外否决**：`.223` 的拒绝只记录不认可；不再关闭议案，也不把 `source_head_yes` 作为额外实施门槛。其正常学者票及本人若为受影响玩家的明确同意仍按共同规则计入。每个活跃接收rite仍须单独授权，双方代表分开签署，接收领袖仍须明确同意。
4. **动态faith重复流程**：actor gate 不再依赖第一包“必须属于 lyd_common_faith”的入口条件，而核对玩家、enabled、儒家大类及8个正式rite身份。原生返回的新faith可以参与下一轮。
5. **主流／最后礼仪**：仍不直接拆当前main/sole rite；多个rite来源不能迁走其main而留下未议定继任。单礼仪来源的整派来归是独立的合流路径。
6. **费用与失败**：只有真实 faith/rite/main/head 及退休后置条件通过，才收费用、写五年调整期。保留旧领袖本人；捕获的其他原有头衔在实施前后都核对仍归其持有。原生部分成功不能假回滚；失败保留实际状态与日志。
7. **scope检查**：没有在 trigger 内塞 `save_scope_as`，也没有把随机选择器当作返回scope API。detach 保持 Character调用+返回Faith保存；退休从 Character调用 `destroy_title`，目标仅捕获的HoF title。离线 AST 不是引擎类型检查，原生scope仍列入R4验证。

## 共享领袖接口

导入 I3 的两个独立源快照：`lyd_c3_head_factory.txt` 与 `lyd_c3_migration_hooks.txt`，哈希见 `evidence/shared-*-dependency.json`。集成时只保留一份共享定义。

既有世俗宗主章程的正式 detach，取得本轮授权后可暂置 `lyd_c3_head_creation_authorized`，调用共享 factory，随后无论成功失败均清该临时变量。仅在真实返回的本派新faith无headtitle时创建一个专属HoF title；本轮获授权发起代表担任。no-head章程不暗改为temporal；spiritual路线仍暂不开放。本轮没有实现争统挑战者。

共享factory省略原版无关 realm-law/fervor/broadcast效果，但省略后的继承行为、头衔事务对既有政治关系的实际影响尚未live验证，不能据静态“没有显式夺地产effect”外推所有间接结果。

I2拒绝已有C3 proposal owner的rite，不越权清理C3锁。已议定迁移前撤销该rite的C3政治声明，迁移/退休后按实际head关系复核认可角色。setter失败时，已撤销的声明和已退休职位不假回滚。`lyd_c2_retired_teacher` / `previous_rite_head` 是历史角色记录，不伪称设置了未证实的原生 `head_of_rite` setter。

## 当前离线证据与文件差异

最新 `evidence/offline-20261004T052856381424Z/offline-report.json`：65项模型/AST检查通过，15个BOM生成文件可重复，checkout前后相同且干净。首次修订64项结果另保留；增加共享迁移hook后才补跑第65项及完整适用检查。

`evidence/actual-delta-files.json` 是相对旧候选的完整源与生成差异清单：18个 authored 文件变化，10个生成文件变化。运行时改动为 c2 triggers、setup/vote/commit effects、events、双语loc；新增 c2 head effect 与两份共享 C3 helper。其余原议定目录、逐rite授权、休眠排除、低资格玩家同意、serial/terms和过期规则保留。

## 未来R4可走的原生界面路径

这些是候选已有入口，不是本次执行事实。原生右键互动：对真实、合格且处于接收faith当前main rite的代表使用 `lyd_c2_propose_join_interaction`（议定学统来归）。自动投递只送议案，不算同意。需要至少一名实际接收代表；完全无人faith不能由来源本人代签。

正式决议分别为 `lyd_c2_propose_detach_decision`、`lyd_c2_review_proposal_decision`、`lyd_c2_cancel_proposal_decision`。事件路径：提出`.200` → 来源票`.210`／每派接收票`.211`／全部受影响玩家`.212`（零学者活跃接收rite另有真实holder`.213`）→ 复核`.220`来源签署 → 接收代表`.221` → 接收head`.222`；旧head`.223`/请立`.224`只处理离开认可 → `.220`最终实施 → `.228`结果。`.229`是过期处理。

最小R4应从新普通玩家冷启动、正式进入与择师开始，另用明确标识的外置fixture提供真实接收main代表；不得拿NPC初始化夹具或旧NP宗主角色冒充正式权限体验。首先核查按钮tooltip/执行scope，再分别走拒绝、未达逐派授权、玩家不同意、成功签署、专属head退休与无head重复流程。已有退休位置要独立验证捕获title、旧人及其他头衔；新factory要检验唯一owned title/ownerfaith/holder。D+1、D+30、存档对象、重载与自然冷却各留自己的证据。外置验收若加速或清冷却，不能计作自然届满证明。

原生会议GUI／原版历史合并决议不是这个议定权限层的替代入口；本候选没有接管其全局一次性锁。
