# R0012：历史身份准备失败与正常退出

`machine_id: 4-8e1c2f1861`；源码上下文 `8d49d0e028ab79e53331e984555a266911426464`。本场为 1.20.0.4 跨宗教机制实验准备失败记录，**没有取得业务 PASS**。原 public／host 的失败与后继退出清理分别保存。本文依据[小型来源索引](evidence/faith-power-r0012-preparation-failure/closure-source-pins.json)整理，不新增游戏、MCP、屏幕、媒体或源码资格。

## 失败发生在准备状态

原夹具把旧场运行时角色号 `29829` 写进 `character:` 历史角色链接。08:09:04Z 的诊断记录保存八条 `Referencing non-existent character ... character:29829`；实际虔诚仍为 150，准备 marker 为 0。地图已出现、Start 返回或当前玩家 full ID `31254`，均不能证明这段历史引用已解析，更不能证明准备效果已应用。

书签与人物历史的既有来源确认罗贝尔历史 key 为 `1128`：`00_bookmarks.txt` SHA `fee9519196b964bb3eae364ef459f7bc92edff0a435be14b81a2377ab1db1472`，`history/characters/norman.txt` SHA `588a012e567f6acc9e032a162b9995bb7424b535ff50cfaea459cf10a1c0132b`。这些是历史定义身份；运行时 full ID 要由每次实际进程读回，不能写回历史 key，也不能跨进程复用。来源线程同类核查确认另一场 `character:34014` 是穆尔太兹的历史 key，未把此次修复泛化成所有数字都错误。

修订包只修历史身份守卫，保留正常 Can；08:09:50Z 的 HANDOVER 明确 `live_qualified=false`，不声称其余准备守卫都通过。原输入与失败日志保留，方案使用新独立 state 冷载，后继实测另记。当前活动日志曾因 sharing violation 无法重散列，本记录使用已封小诊断，不制造新的原日志 SHA。

## 真实闭场及资格边界

| 对象 | 实际结果与时间（UTC） |
|---|---|
| 原 public Popen | 退出码 2，08:23:31.186661 |
| 原 host Popen | 退出码 1，08:28:57.372764 |
| 新 cleanup CaseClient Popen | 退出码 0，08:28:57.444125 |
| 同一 retained HANDLE | PID14416、create_time1792310025.2548645；08:28:27.957766 实际 wait=0/OS exit=0；未重开句柄 |
| keeper | 退出码 0，08:29:03.813444 |
| 现场资源 | 任务总线序号11733、resources=[]，08:29:13.254495 |

原版 GUI Confirm 的返回当时没有证明终态；后继由同一 CaseClient 的 retained HANDLE 独立证明 OS0。操作人关于原生退出界面及取消自动保存的审阅，保留在原 `normal-quit-root-result.json`，本文未重新查看其 PNG。`normal-close-result.json` 实际为 `cleanup_ok=true`、`failure_lifecycle_completed=true`、`failure_preserved=true`，同时 `business_pass=false`、`normal_close_qualified=false`。原错误仍是 `TimeoutError: actual qualified fixture government/tier/player did not stabilize before deadline`。正常退出与资源释放完成，不把准备失败改写为业务成功，也不据这个历史释放记录推断当前现场空闲。

## 明确的后续改进

08:14:08Z 的独立源码审计未找到已部署的公共 prehold normalexit／受管交接入口：bootstrap 等待期间外部队列尚未被消费，MCP stdio 由原 host 唯一持有。本场等真实诊断 hold 后，才沿现有受管退出与 retained-HANDLE 清理续行，未伪造 ready、hold 或超时。

未来改进是在现有 owner 的启动等待边界消费**仅用于退出清理**的显式请求，沿现有 normalexit 工具、实际进程/来源/lease 与句柄守卫配对，保留原准备错误和一次提交／未知不重发规则。该入口**尚未实现或部署**，本记录不给它能力完成信用。制作方法见[系列方法](../../promo/ck3_faith_and_power/docs/production-lessons.md)，因果经验见[制作经验](../../promo/ck3_faith_and_power/docs/production-experience.md)。
