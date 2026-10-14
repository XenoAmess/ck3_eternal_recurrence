# R89：道学代表原生互动桥接错误，制度验收 RED

2026-10-14（北京时间）。R89 在独立 A62 容量预约、本场新鲜 Steam 离线画面及屏幕独占下，从 R79 不可变原版儒家存档启动 CK3 1.20.0.4。实际加载 0.1.2 正式候选的83个文件；原版 `confucian_faith` Faith31、宗教9、主礼仪道学33、玩家白沙礼仪174及尚无宗主头衔均重新读回。基线和准备两个 cell 均 `complete/qualified=true`，道学推荐 AI 候选仍为31763，学识28。旧 R88 的代表动作没有从未保存的状态中继承。

ROOT 通过正式“议建共同体宗主制度”决议发起本轮。`lyd.430` 的实际选项显示实施条件未齐，ROOT 选原生 index2“待诸方答复”。当前“封定制度条款、征询诸儒”在 UI 中灰显并提示未满足要求。ROOT 再通过正式“明确提名自己参与本派代表推举”决议进入 `lyd.410`，选实际原生 index0“我明确赞成所示条款”，白沙玩家本轮接受后事件消失。

随后公共 case 对完整原儒家名册重新查询，确认31763是另一活跃礼仪的合格推荐 AI 候选；原生普通互动查询返回 `available`，且 `shown/can_send/auto_accept/ready_to_initiate=true`。一次性提名意图在调用前已持久化，**真正的互动提交未成功**：原生桥接录制包装器 `RecordingEndpoint.send()` 未接受 `packet_evidence_path` 关键字参数，MCP 调用报错。行动目录只留下 claim 与 unknown 回执，没有 `.packet.bin` 或原生结果；不能推断 NPC 已收到或接受，更不能重试本场意图。case 保存 `business_pass=false` 的 RED，制度 cell 没有结果；封定、两派三分之二投票、玩家同意、签署、实施、宗主头衔及36项实机效果均未验收。0.1.2 仍不得发布。

已修复包装器转发该参数及请求包证据路径，补了包装器行为回归测试，并同步旧内存互动测试夹具。新增测试1项及普通互动测试24项通过；修复以线性提交 `8ee983df04bc51fabeab534d2059be8deaca678a` 推送 `master`，未改变 R89 已启动的运行时。下一场须重新申请容量、屏幕与离线证据，从 R79 源存档重做发起及白沙自提名，再经修复后的桥接层验证一次道学提名和**后验接受状态**；本场的 `available` 查询不算业务通过。

R89 实际运行时仍指向旧冻结源码 `C:/csr19`，其 `run_ck3_12002_mcp_live.py` SHA-256 为 `206f41a189cad449059fb2802c039d2239e0e567a4ede805ce6c4a4c14befd97`，保留了缺参的 `send(frame)`。当前 `master` 修复文件 SHA-256 为 `e9bfb8123ba6d1b1779dc8f79969de21b4ed1928f3f2a963db43b67f07f46d95`。**R90 不得复用 A62 的 runtime/manifest 或直接改写 `C:/csr19`**；必须先建立新的不可变共享源码后继与精确 source index/manifest，实际预检并读回已绑定修复文件，才能申请下一次实机。单纯更新主仓或复用旧配置会重现同一错误。

错误后 CK3 实际退出码1，原运行器退出码1，公共入口退出码2；没有游戏内“退出到桌面”操作或 OS0 证据。原生报告为 RED，虽 `cleanup_ok=true`，`normal_close_qualified=false`，不能写成正常退出。进程已不存在后，keeper 停止，显示器恢复1024×768，屏幕任务序号5849→5850精确释放，Steam 仍离线。按[通用存储策略](../../../storage-retention-policy.md)，闭场后仅删除与保留来源逐件大小及 SHA-256 相同的三个存档副本；三份原生日志分别压为单成员 ZIP，核验解压 SHA 后删原流。六原件共452,138,886 B，新增压缩包4,280,292 B；保留唯一议案前存档、R79 来源、错误与原生报告。四根逻辑量477,287,711 B，加32 MiB余量后的保守 carry 为140,844,370,155 B，低于141,863,902,123 B上限。A62 原1.25 GiB预约在09:38:49Z前闭账、余额归零；容量协调任务序号5851完成。

外置证据根：`A62=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-r89-admission-20261014-062`，`R89=C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0089`，`CASE040=C:/workspace/ck3-common-runtime/cases/lyd-release012-headship-resume-20261014-040`。R89 的 `xar_checkpoint.ck3` 是议案前 SAVE（91,608,339 B，SHA-256 `6e2f880926070ad05a4ddc655d9d00c16d4594a6e8cb93f8bfbddf1d108df1c3`），不能替代白沙与道学的后验存档。

| 关键回执 | SHA-256 |
| --- | --- |
| `R89/case-output/baseline-cell-result.json` | `16bfbbb3824d7d86dee45f3c8dd982436faf4f8e3041e65b5256cb0648956169` |
| `R89/case-output/preparation-cell-result.json` | `6a927c521d73beee8111bb1307544964b87b611585e2440acff2a500f490e937` |
| `R89/case-output/release012-institution-0006-nomination-intent.json` | `07026367efe51e1bdb555b8c2eebe265f69e2e2d76b8f04866a8d716a2458043` |
| `R89/case-output/case-error-preserved.json` | `c8f08081fb6bbb340bf72df525f1af30715a96d7158fb975b136f95a58db8248` |
| `R89/case-output/normal-close-result.json` | `cfc9d4949d6e71f1e24fa96f226a170af23ee751a43f61c2a27fc75765a0ce95` |
| `R89/native-report.json` | `93bfe2f6ca41807bd31e6f649f48b3bda7f5a3c4a90a713d282f56487287df13` |
| `A62/R89-SCREEN-RELEASE.actual.json` | `5b91c8ce3538ce6eacc01b4d10cc7360f5f17629cfe7b4e338485fd0c4be53f1` |
| `A62/R89-EXACT-RECLAIM.actual.json` | `965f808d0113b92b8141464b703dbefc6b979a7d2bad5f70e5b4260a8a2d504c` |
| `A62/CLOSED-RESERVATION.actual.json` | `e03c4266cd6a130cbfba7de6583fe25873a4535b6136c8bb88a60ca1f4eeabd6` |
