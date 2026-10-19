# AUTO194 的独立只读局部恢复与后继 bootstrap

machine_id: `xenoamess-full-tower-eb9d2c1186`。实际来源观察时间为2026-10-19 UTC04:35:29（M0）及04:40:58（runtime）；软件组合资格使用相同机器的精确原件。没有新增现场 RPC 或动作。

194 的新来源包 `p51-auto194-source-review01/META.json` 为10433B，SHA256 `6cf39a4277e95cf660840e2728c201fc779497cc0b16c237c03a99f06cc0d1aa`。它保存本次首 plan、TEXTACK、完整 MCP error、current request、scheme ledger 与 schedule。旧 Sway instance2/gen0 在 Native98/raw53145792 完成只读月检并持久化 next53146512；无新 Start。普通 fallback 的第二 before-submit 因固定194文件名碰撞抛出，未派发普通 Driver 动作，第二 plan 与外层完整 summary 未保存。

runtime 的 `closed-before194-recovery49/FROZEN.json` 为2213B、SHA256 `172fdb55db129166f44d1b95caaf6cedade57deb23bf0eb1d83541d8033c048f`，精确保全74完整周期、pending75、halt、governance 与 next195。真实已完成 MET193 为14110B、SHA256 `d40c98fd93f29609f80e4f8ae8990da8e54253dbcfc863a5709cd27c7485a383`，证明同 actor/episode、Native98、paused map、connection4、日期61日，等于当前 before。194 来源控制流证明其后只有只读观察，不能宣称完成75或整体 AUTO 成功。

[本次独立叶](../../tools/g2_saved_campaign/partial_sway_194_readonly_recovery_v1.py)绑定以上三份精确来源，核 Game kernel birth、当前 state/governance/classifier 与完整 instance/冷却身份。它不复用143的条件，不发 fresh SEM 或其他 RPC，只清 pending75，保74/count/date/before/旧实际 checkpoint 不变，保留194失败与发布去重账。新61日 checkpoint 必须由下一次真实 SEM/SAVE建立，不能把旧30日 checkpoint 改成61日。

由于 known-pause 与 saved-preflight 已在该 Queue 缓存，本次复用尚未调用的 `recover_known_owner_1024` method 内动态 import。[producer](../../tools/g2_saved_campaign/prepare_partial_sway_194_readonly_recovery_v1.py)仅前置 exact194 kind，原1024函数改名后 AST 全保留，绝不进入其 Native lifecycle。现成原 Queue 的 `frame`、`consume_sequence`、`persist_loop_state` 实际组合资格通过；5个必要负例均在写入/consume前拒绝。[资格记录](evidence/c3-partial194-readonly-recovery-qualification01.json)记录0新 MCP/Native 与原件 pins。

唯一控制为195、`command=recover_known_owner_1024`、`arguments={"recovery_kind":"partial_sway_readonly_194_zero_rpc"}`。候选原模块27908B、SHA256 `0c39687265aa73b165b173e49a02ff1c2f1f340af74f5dd136b184792a3edd5c`；邻接 `root_partial_sway194_readonly_recap.py` 为11422B、SHA256 `4be60650cdab92507bebc2c88027c0086c5b50630bad50fdd0d04463950e1731`。runtime 是唯一采用与实际运行操作者，逐步实际后验独立记录。

下一次维护的 Queue 源顺序明确如下：

1. 读取已含 encode-once 的 C3 原 Queue263414B，SHA256 `18bfcbe93b17c625b80fa2701a29e44229f2a554b5daee75c32544c677e9c2b6`；不能重复套用旧 P37B 的编码 transform。
2. 调用 [settled_readonly_dispatch_source_v1.transform](../../tools/g2_saved_campaign/settled_readonly_dispatch_source_v1.py)，得到264841B、SHA256 `633dee176ad0a182179793b09d1da0b137dca61dfeeacf36338bb90df9bc0b5e`。
3. runtime 再对该字节结果执行下一代 literal、entry、manifest 与新的有限 warm factory 变换，取最终真实 SHA 写 owner input pins；原 full_loop 结算算法不改。
4. 已耗 MET110 once 不能再用。新 App opening 要绑定新 fresh SEM；T0 map、评分和月样本锚继续保留原实际输入。

194 当前控制叶是维护边界的有限恢复，不是每月通用 workaround。公共多 callback producer 的永久修复、合批 SDK 与 Native 后继分别验收，不热换当前 App。小 review 输入在维护验收后7日按统一存储策略复核引用与替代证据；必要活跃输入与原失败保留理由应明确，过期派生副本不无限期续存。
