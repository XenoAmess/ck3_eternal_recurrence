# v20261019：存储全局锁导致受管游戏退出

`machine_id: xenoamess-full-tower-eb9d2c1186`。事实时间为 2026-10-19 UTC；以下属于这台机器的记录。当前恢复结果另记，不能把源码资格当成已恢复游玩。

13:48:40.300880–13:49:05.385858 的存储维护回执区间内，旧私有删除生产器在全局任务总线锁内执行全进程扫描及逐进程命令行读取。该区间约25.1秒，不是独立测得的精确持锁时长。旧租约 CLI 的 `LK_LOCK` 重试耗尽并报 `Errno 36`；监护器随后停止录制、提交一次 `WM_CLOSE`，最终关闭自有 Job。Game 15512 / FILETIME 134368811928524228 于13:49:39.090123实际退出1，属于强制清理，不能记正常退出。

这是维护流程错误。publisher 后来的 `QueryFullProcessImageNameW` WinError 5 发生在关闭过程中，现有证据不支持另认它为最初根因。publisher owner 退出1；子 publisher 的数值退出码未知。独立录制156d的OBS正常退出0，与整个受管场次异常退出分别记录。原异常和旧记录保持原样。

最后成功保存为 SAVE6322：第3023个已结周期、第2419实际游戏日、raw53202384，当前角色40526。关闭前到达的3037周期/2432日只作历史事实，未保存的14周期/13日不计入恢复后的当前进度。该尾段由12次只读查询和两次时间推进组成，没有新的赠礼、移动、事件选择或生命周期写操作。保留原始1066开局、10950日目标、raw53407128终点及03:26:49.420926Z起算墙钟。

两层修复分别解决不同问题：

- 存储采集、哈希、遍历、序列化移至锁外；锁内只做有限精确元数据校验、代次CAS和至多两次原子发布。详见[锁边界](../maintenance/storage-lock-boundaries.md)及[隔离资格](../maintenance/evidence/2026-10-19-storage-short-commit-qualification.json)。旧177项源审清单只标识历史用途与禁止复跑，不声称自动阻止所有旧文件执行。
- 总线使用有界非阻塞等待，繁忙返回独立 `BUS_BUSY`，不冒充所有权已改变；当前租约检查显式最多等待45秒，成功取得锁后继续原有所有者、时效及CAS检查。等待期间不声称游戏已暂停或租约已续期。详见[资格记录](evidence/screen-bus-bounded-lock-wait-2026-10-19.json)。

冷恢复使用原生存档边界与原历史前缀，不伪造当时未独立保留的完整loop/governance快照。C15实际冷加载必须读回 `cold_checkpoint`、上述日期和角色；准备脚本或本文件不能授予恢复通过。新显示链必须使用新Game身份、新publisher owner及新OBS UUID，先通过相同子进程环境的依赖预检，再开始录制。Steam仍须新鲜离线图像直接审阅。

14:48:41.095050 后续：C15已实际读回 `cold_checkpoint` / `driver_state_restored=true` / `active_resumed`，SEM6358、CAP6359和上述保存日期、角色通过，新增周期/日信用均为0。新录制 `c7f52534-431f-48f2-bef6-283aa5536933` 首帧由Root直接查看，通过[呈现审阅](evidence/c15-primary-recording-cold-review-2026-10-19.json)，未授予全境或持续跟踪。实际冷恢复闭件为相邻准备目录 `c15-checkpoint6322-cold-source88/ACTUAL-COLD-READY.json`，4912字节，SHA-256 `6830da757f5150f3f02d31b9cd572ec47d83160904cc4704c1577804b17cc654`；Root已直接读取核摘要。随后发布FULL6360继续完整规划。未保存的13日仍只保留历史，原墙钟不重置。

原始小型闭件位于 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c13-auto6356-failure88/display-closed/`：`GAME-SUPERVISOR-EXIT-FROZEN.json`（9921字节，SHA-256 `93c28466d55036b2e8d3abfe7774dcda52ee5dc2e78d53217e33846a6f005376`）及 `CHECKPOINT6322-FRONTIER.json`（50167字节，`0052ae0b2dfc7858b53271022adde77ebb156c3bb34fd6b5fbec7ddc039470fd`）。Root于14:35:53前直接读取并核摘要；未读取存档或活动Driver正文。跨机器不可据此追认现场状态。
