# “自动升级建筑”1.19.0.6 维护验收计划

状态：L0 已完成；当前 source-live 核心实机矩阵已由
`desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0013` 验收为 GREEN。扩展边界矩阵仍保留为后续计划，不把静态解析、
命令 ACK 或未执行的场景冒充实机功能 GREEN。

## 冻结环境

- CK3：`1.19.0.6 (Scribe)`
- Steam build：`23530548`
- CK3 EXE SHA-256：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- 上游来源与字节：[auto-upgrade-buildings-upstream.md](auto-upgrade-buildings-upstream.md)
- Steam：后续静态检查与 CK3 验收期间保持离线

## 玩家可证伪合同

1. 只有真人玩家可见并执行启用/禁用决议；AI 没有入口。
2. 启用后恰好建立一条自续循环；首次检查在 1–2 日内，后续每 15 日一次；重复启用、读档或旧排队事件不会并行倍增循环。
3. 每轮只遍历玩家直接持有的 province，不扫描全地图，不处理附庸直辖地。
4. 只升级已经存在的普通建筑；主建筑、公国、特殊、部落、游牧、曼荼罗、great project 和其他非普通体系保持不变。
5. 下一等级必须满足本 mod 承诺的革新与地产等级条件；有正在进行的建设时不强制替换建筑。
6. 同一建筑链每轮最多升级一级；升级与一次扣款属于同一成功路径。
7. 国库足额时只扣国库；国库不足且个人金钱足额时只扣个人金钱；两者不足时建筑和两种资源都不变化。
8. 禁用后已排队检查可以到达，但必须零副作用且不得续排；重新启用能建立一条新循环。
9. 保存/重载后 `enable_auto_build` 保持，且循环不丢失、不重复。

## L0：离线静态门

- descriptor、UTF-8/BOM、本地化头和括号结构正确；canonical tree 不含 `remote_file_id`。
- 先用当前 `open_kaishek` 对其覆盖的 Clausewitz 语法子集做离线 parse/round-trip；记录 commit、profile、游戏 build 和不支持项。
- 校验公开 namespace/flag 未更名，decision 有显式 `is_ai = no`，循环的 seed/dispatch/续排均受 flag 闸门保护。
- 校验 runtime 明确使用玩家直接持有 province，拒绝 `every_province` 全地图扫描。
- 校验建筑白名单与 CK3 1.19.0.6 原版定义一致，下一等级 ID、费用档、革新和 holding 条件存在。
- 校验 release allowlist、无额外文件、确定性 manifest/ZIP 与上游 ID 禁止规则。

## L1–L3：单进程隔离实机矩阵

使用 production projection、外置 fixture 与一次性 `-userdir`，直接启动本地 `ck3.exe`；不启动 PDX Launcher，Steam 保持离线。
启动前后均以 `Get-Process` 和 WMI 双源清点 CK3。

R0013 当前在同一进程中串行覆盖：

- 产品 7 文件 production projection 实际挂载、进入地图、产品相关解析/运行诊断为零；
- 首次检查、禁用状态跨 16 日不再升级、重新启用后新循环建立并可干净停止；
- 国库足额、无国库且个人足额、两者都不可用三种实机资金分支；
- `outposts_01 → outposts_02` 成功路径每轮只升一级；
- 结果事件可见并由 OCR 确认，运行树、受保护真实资料与进程清理合同保持不变。

以下扩展场景尚未由 R0013 独立覆盖，继续作为后续矩阵，而不是本轮已验证事实：decision 可见性、不可用革新、正在建设、全部
排除类别、新征服直辖地，以及保存/重载后的 flag 与单循环行为。

fixture 以升级前后 building ID、国库、个人金钱、日期与调度 marker 形成断言；UI 截图只证明玩家可见结果。报告必须绑定 source/runtime
tree hash、Git commit、CK3 build/EXE hash、日志增量、进程清理及失败 artifact。当前任务不执行 Workshop fresh-cache 发布层验证。

当前实机证据：`desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0013` 在 C 盘 CK3 1.19.0.6 上于 402.065 秒完成并 GREEN。
报告绑定 EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`、产品 tree SHA-256
`E0B95B5228670633EB7DBFAFA13F2B4555C6B72BCDD12242CA208B1F7DB2224F`、五项 PASS marker、零项目诊断、运行树不变、临时
userdir 删除、受保护资料不变与退出后双源零进程。artifact 位于
`C:\Users\1\AppData\Local\Temp\desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0013`。

R0006（legacy `R410`）仍作为原始 environment RED 历史证据保存在
`D:\workspace\ck3_auto_upgrade_runtime\R410-maintained-live\artifacts`，不为迁移编号而改名；后续已确认其根因为同任务遗留的全盘
`rg.exe` 扫描造成 D 盘 I/O 竞争。Steam 在全部实机轮次中保持离线，本任务没有执行 Workshop fresh-cache 或上传验证。
