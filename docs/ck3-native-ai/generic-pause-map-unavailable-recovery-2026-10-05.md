# Generic pause-map 的一次独立恢复

2026-10-05。R0162 在已运行的地图上调用 `pause-map` 得到原生 `CK3 map state is unavailable`，随后独立 snapshot 显示 `paused=false`。最终 Root 独立暂停成功，但原始日期累计增加88日，最后有效的逐团暂停样本仅到+22日；这段长空窗不能用于第4期的结算因果或A/B/C起点。[现场边界与原始文件](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0162-index.json)保持原样。

该错误合并了原生缓存/owner snapshot和core stamp的多个拒绝条件。现有证据不能唯一确定失败分支，也不能把它改称为已经证明的revision竞争。原生handler与validator未修改。

新增恢复只适用于generic `pause-map` 的这个明确原生拒绝。首次提交继续执行原有capability、expected revision及已暂停后置条件。拒绝后必须取得新的semantic frame，核对exact build、连接、PID、episode、存活玩家、速度、event及pending交互绑定；仅当同一身份实际仍在运行时，最多提交一次具有新request ID的独立暂停。重试前再次核对身份，最后必须实读同身份 `paused=true`，总等待沿用首次deadline。

超时、其他原生错误、重连、人物/事件/速度变化、地图不可用或没有新frame均不会触发这个重试。原始拒绝及两次request保留在 `map_control_recovery`，失败也保留后置条件报告。此改动不重试移动、resume或其他游戏动作；sampler仍须在暂停失败后优先恢复，恢复未确认时不得再次resume。

候选与检查位于 `C:/ck3-war-episode04-research-20261004-a01/pause-running-revision-race-a01/`，最终patch SHA-256为 `789a36e6fa5c58cba0e6da5cad3672a8e34da674be398e520c9898bed90148e8`。Root在合入tooltip后的主树运行16项focused测试通过，覆盖真实registered MCP/service/driver链，Endpoint使用本地fake；原生handler未调用。Root记录为 `root-code-checks-a01/result.json`。当前是static-ready，实机恢复与有界采样尚待下一次独立会话验证。
