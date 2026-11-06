# 性能瓶颈与功能缺口：2026-11-06 13:42 UTC 切点

用户要求性能和功能同时推进。原自动游玩局仍由唯一 Runtime owner 操作；本记录只整理已取得的证据，不触发游戏、保存、恢复或热更新。

完整 SAVE59→SAVE1323 窗口为 135371.5710557 秒、365 个新增确认保存日，即 **370.8810166 秒/日**，未达到 10 秒目标。该窗口包含等待、失败、准备及恢复。C33→1323 仅新增推进 135 日，另有此前未保存的 230 日，不能用这段较短墙钟除以 365。原件见下表。

| 优先级与瓶颈 | 已观察的证据 | 处理与验证边界 |
| --- | --- | --- |
| P0：历史恢复失败造成停顿 | r54 于 13:23:06.8392813 FAILED_DELEGATE，历史 capture 与重建的 Driver/action/source 联合校验拒绝；尚未进入 LOOP | 对固定 1412 capture 原件和前序发布边逐项比较。Driver、stamp、historyBasis、source 已相符；已发现 actionRows 保序算法不同，且同 SAVE 的重建使用原 UNKNOWN1321，而 capture 记录 settled1322。仍需核对原生产契约和首个失败边，不能仅排序、忽略序号或删除联合校验 |
| P0：重复历史重建与 JSON 投影 | 正常业务 45 秒 JFR：业务线程 467 个执行样本中，replay 223、rebuild 161、replayCapturedOriginals 158；这些栈互相包含，不能相加成耗时 | 后续只研究具有真实重复输入证据的纯数据投影，保留每次原件、哈希、owner 和当前帧校验；尚无新投影缓存采用或提速结论 |
| 已撤回：完整结果缓存无收益 | r53 连续四窗各 282 次调用、0 hit、282 次严格重建；OBS 分别约 107.117、104.554、109.976、107.021 秒 | 已撤回无效的 Complete 保留、额外 key 复制和 lookup，保留原有 Driver decoder。源码及必要测试通过，r54 已采用，但被恢复故障挡住，尚无新业务性能窗口 |
| 模型输入处理与首内容等待 | 实际 Life 请求约 2.08 MB，总耗时 43.328 秒，首有效内容 42.635 秒；另一次约 2.03 MB 请求首内容 46.273 秒 | 已有字典编码实际接线；继续按真实 REQUEST 量和语义完整性判断。尚无同输入对照，不能把离线压缩率视为实机提速 |
| 强制落盘与 GC | 同次 JFR 中 FileForce 事件累计约 2.122 秒，GC pause 累计约 1.970 秒 | 保留必要保存与完整校验；这些事件窗口不能直接外推整局耗时，不用减少保存或校验来达标 |

OBS、PLAN、策略方法和模型调用存在包含关系，不能把它们相加为独立 CPU 时间。短窗、累计旧日数和 observed 推进均不替代新增 SAVE_CONFIRMED 的完整墙钟口径。

功能线保持独立推进，整体 G2 最后完整验收仍为 **6/8**：

| 功能缺口 | 当前事实 | 剩余验收 |
| --- | --- | --- |
| 原局恢复 | 同一 Game/keeper/Quarkus 宿主保留；C55 日期 53167848，比 SAVE1323 日期 53167128 多 30 日 | 修复实际历史重建差异并恢复 LOOP；不能用旧保存回滚这 30 日 |
| Life 纯规划观察路由 | prepare/rewrite 与执行时 reserved-child scope 分开；执行 current/next、校验和提交门保持原样。必要 3TU 已通过，14 个 class 输出，尚未装载 | 合法 DATA 路由回归及当前局新的实际完整规划；不能重放旧 1376 |
| Sway 读取与完整收益链 | 已修复已知构建标签/EXE SHA 联合识别，生产增编及分开的正负例通过，r54 已采用但尚未到业务路径 | 新鲜读取成功后，完成真实 Start→同实例自然终态→收益因果链。调度检查完成或未到期不算该验收 |
| 公共保存与 M7 恢复 | 五叶同 Host 桥接源码与必要编译通过；当前真实状态接口返回 503、Root 尚未安装完整图，未发 SAVE/RESTORE | 先恢复合格当前 Root，再一次合法公共保存保护最新全部进度；随后由唯一 owner 走官方关闭、材料化和 RESTORE，并验证同目标的新计划。Java 热重载不算 RESTORE |

证据导航：

- 完整保存窗口：`D:/ck3-state/resume91-runtime/resume-after-user-play-20261105/natural-year-save1323/small-proof01/ACTUAL-CONSECUTIVE-SAVE-WINDOW81.json`，1549 B，SHA-256 `4e8de856675b07fe7a5ed27d145fd9b3c28e22d874c5c32434f7a571080332c1`。
- 唯一业务 JFR：`D:/ck3-state/resume91-runtime/resume-after-user-play-20261105/encode-sway-peacetime-cohort7880/normal-business-jfr81/normal-business81.jfr`，10400049 B，SHA-256 `0bb07bc589a6336aed6337762b2b092a9625834a4d2d12b61da3d98b48a8f37d`。
- [零命中诊断](2026-11-06-replay-cache-scope-diagnostics.md)及[严格重建保留撤回](2026-11-06-strict-replay-retention-withdrawal.md)分别记录源码、软件验证和实际采用边界。
- r54 失败：`D:/ck3-state/resume91-runtime/resume-after-user-play-20261105/public-save-strict-replay-cohort84/r54-failure85/FAILURE85.json`，3913 B，SHA-256 `280ff618d9b0513a1843a3c5ab6430511080a275d63b9ad7f17a1831d62eca0b`。
- 固定历史原件索引：同一 `r54-failure85/capture1412/CAPTURE-1412-REFS.json`，5424 B，SHA-256 `cc20889333a655c7c88ad9c0091d43392f161f8a7d86d97d6621979d5a3fe84b`。

本切点之后的装载、LOOP、游戏动作、公共保存与性能变化必须另以真实回执更新，以上软件通过均不提前授予实际游玩成功。
