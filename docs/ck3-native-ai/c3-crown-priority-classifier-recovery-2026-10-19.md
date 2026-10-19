# C3 Crown priority：补齐来源明确的旧格式字段

`machine_id: xenoamess-full-tower-eb9d2c1186`。实际源、观察 UTC 与软件检查见 [资格回执](evidence/c3-crown-priority-classifier-qualification01.json)，实际本地安装/原件核验见 [读回](evidence/c3-local-classifier-recovery-readback01.json)。

AUTO130 实际完成 `verify-realm-law-crown-v1-private`，原件46,540字节、SHA `ce6cc323f7be1c6c2aac637a0c53ca173d0fa2146f6acdff56fd16dc1d3c1ea5`。旧 harness 拒绝的是 `plan.crown_cold_recovery is False`：Src03 的 `pending-material-publication-v1` 优先返回路径没有携带该字段，普通 Crown consumer 路径才携带。它与 C3 LIFE opening 日期问题无关，不能通过重置 T0 或放宽日期来解决。

独立源审和原件逐项确认：提交、pending、原 Native ACK 与 receipt 都指向 `crown-formal-2215f5b0b90d415cb7d19ab7b2592f3d`、`crown_authority_1`、角色31254及原 episode。完整 source_context 恰好只有 Game PID214568 与该 episode；publication ready/same_process为真，pre Native54、observed/post Native55，原日期均53145048。原 prestige220250260减去精确报价22000000，实际 receipt为198250260；三项效果验证均为真。原消费者对资源、法律、继承与修订的其余检查完整通过，没有用 App public19替代 Native54/55。

[有限生产器](../../tools/g2_saved_campaign/prepare_c3_crown_pending_classifier_v1.py) 只对来源证明的 priority Crown hot tuple 投影缺失的 `crown_cold_recovery=False`。不能仅凭 ready推断：完整 pending必须相同，source_context必须严格等于当前 Game/episode二字段，same_process与无业务信用字段必须明确，observed Native必须等于当前规划帧且大于原pre Native。原 Native receipt不修改，原所有函数AST不变，仅最后dispatcher改名并追加wrapper。

候选261,745字节、SHA `9da4445b22bf49c616ad190023655911a102c76d225c3052c662e58292c23a11`，保留之前的 LIFE修复。真实130经原完整业务classifier通过；错Game、cold source、额外source字段、错ID、错目标、陈旧后验修订、错误扣费、未验证效果、错episode九个变体全部拒绝。117的LIFE结果保持相同。runtime实际以131安装相同字节至原runtime目录，再以132核验原130，均零新增MCP/Native调用、原动作未重放。该事实只关闭130，不代表后继整场运行完成。

资格时读取的原治理sidecar为6099字节、SHA `9ab39b112dc0630ba4068c896c518712a73ef0858e1399d8a3a2dc0e93aad18c`。后续正常核验已覆盖该mutable路径，runtime及离线资格执行者未保全其原始小文件副本。旧路径现不能读取该版原字节；仍可读取原130.plan.pending、原128提交和当时的资格结果。不得重构文件冒充保留原件。两份新producer现已补后续保全：生成review时create-only保存已经读入的governance原字节，并记录pin；已丢原件不补造，已通过资格不重复运行。紧凑记录于2027-04-17复核保留用途。
