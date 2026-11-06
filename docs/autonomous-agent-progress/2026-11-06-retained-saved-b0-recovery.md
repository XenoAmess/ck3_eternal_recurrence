# 已保存世界的只读 B0 后缀恢复

本记录切点为 2026-11-06 20:36:53 UTC。运行岗观察到同一 Game 102152、keeper 35300 的 Main250 24536 恢复普通 LOOP，下一批编号为 1。START 20:32:18.119762 至 LOOP 20:36:53.1774429 共 **275.0576809 秒**，完整计入恢复成本。

## 实际故障与修复

前一 Main250 96392 已通过源资格，随后在 attach 前被 `domain imports must precede the retained read-only batch` 拒绝。原件显示：21 为 BATCH_STARTED，22 为 Driver READ，23 为 OPENING_GATE 域导入；25 还有一次同域导入，36 以相同 batch 的 BATCH_FINISHED 正常结束，状态为 running。整段只有 12 次 READ、两次域导入和批边界，没有动作提交。

旧恢复状态机只允许批前导入，以及以 BATCH_INTERRUPTED／repair_required 结束的只读批。正常关闭还有两个消费缺口：已用 B0 编号只在 repair 状态下返回；Core 又把任何非空已用编号都送入仅接受 repair 的恢复器。

P099 保留逐事件连续前态、完整 reducer、原始与 durable body 的 Pin／字节比对，以及 READ 的 source、Driver 引用、版本、epoch 和 head 链验证。合法域导入可以出现在唯一打开的只读批内；新增同 owner、同 batch、原 source、空 pair／cycle proof 的 FINISHED 正常关闭。验证得到的 B0 编号仍交给原 Controller 消费，原严格编号解析得出下一批 1。

只有已经验证为 INTERRUPTED 的关闭角色进入原 repair 恢复器。正常 FINISHED 保持原 READ 重放、域初始化和已用编号绑定路径。未清账本、伪造 repair、重建 Entry 或重放 B0。

## 软件与实际运行分账

最终实际变体包含 Bootstrap 与 Core 两个编译单元、39 个 class，首编 exit 0，用时 9.4494245 秒。唯一新 DATA 测试使用真实 state20、21–36 全部事件与两次导入的七份原件；验证 12 次 READ、两种关闭角色、next1，以及动作、版本、source、batch、head、body 冲突和原 IOException 身份。该方法真实 1P，用时 5.4884524 秒，资源全部释放。DATA Session 明确不签发私有 Entry、custody 或 writer 资格；中断变体只验证纯后缀层。

实际 24536 随后通过旧拒口，20:33:00 获得 attachment、20:33:01 获得 Loaded custody，20:36:53 恢复 head36 和 next1。日志中的 SAVED_ENTRY_ADOPTED 指对原 Entry 的保留恢复，本次新增 Entry 信用为零。此切点尚未取得后续新模型消费、新游戏日或 SAVE 的回执。

P098 的 Sway 任务投影和 P097 的同调用 Driver 解码复用已随必要前缀交付；软件通过与前缀采用分别记录，端到端收益仍需实际业务窗口。原 10 秒／新增确认保存日目标未达，本次零新增保存日，不能计算有限秒／日。

## 可复核索引

- 实运行：`D:/ck3-state/resume91-runtime/resume-after-user-play-20261105/m7-retained-repair99/frozen-loop99/ACTUAL-RETAINED-LOOP99.json`，6393 B，SHA-256 `2aee96951776da559fa9aa23b6ec05ef48a7e64ae9d75ee12d8403d5bb8ecfce`。
- Owner：`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261105/saved-retained-readonly-suffix99/OWNER-SOFTWARE-DELIVERY-FINAL03.json`，4461 B，SHA-256 `99ecace03d1093706b3d3717278ca8a22fbd3129cb5d605bcb43185f4a4f5887`。
- 软件：同目录 `QUALIFIED-FINAL03-COHERENT39-AND-REAL-B0-DATA02.json`，33039 B，SHA-256 `c8f38f164b1a453d18861aefd5d3d252395c46711ee7b87fb7987eb8b6c4ef93`。
- 独立源审：`D:/ck3-state/resume91-root/retained-saved-readonly-suffix-independent99/FINAL03-ACTUAL-B0-CLOSURE-PRIVATE-ROLE-AND-TEST02-SOURCE01.json`，23731 B，SHA-256 `3f47eb055dd6606174452868e6d61f657b2d9fffe64b52cebbb9bf00a1e8eb21`。
- 固定原件：`D:/ck3-state/resume91-runtime/resume-after-user-play-20261105/m7-retained-resume98/retained-suffix-failure99/COMPLETE-B0-READONLY-SUFFIX99.json`，12088 B，SHA-256 `f4573dd6c4ba4b9e0d1d36da1be728d475fe20edf57f9c2f5b1599382fbdf89e`。

正式源码仍按 owned spans 保留既有正式外体，完整正式变体的类型与组合资格另记，不借实际变体字节码覆盖。文档发表不触发 worker 或 Game 重启。
