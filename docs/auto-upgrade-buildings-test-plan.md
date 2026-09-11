# “自动升级建筑”1.19.0.6 维护验收计划

状态：维护中。本文定义本轮完成门，不把静态解析、命令 ACK 或文件出现冒充实机功能 GREEN。

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

同一进程串行覆盖：

- 产品实际挂载、进入目标界面、决议可见，产品相关解析错误为零；
- 禁用状态跨 16 日零变化；启用后跨首次检查与一个完整 15 日周期；
- 国库足额、国库不足/个人足额、两者不足三种资金分支；
- 可用革新、不可用革新、正在建设、普通建筑和各排除类别；
- 新征服直辖地；
- 保存/重载后的 flag 与单循环行为；
- 禁用后旧排队事件零副作用，重新启用恢复一次循环。

fixture 以升级前后 building ID、国库、个人金钱、日期与调度 marker 形成断言；UI 截图只证明玩家可见结果。报告必须绑定 source/runtime
tree hash、Git commit、CK3 build/EXE hash、日志增量、进程清理及失败 artifact。当前任务不执行 Workshop fresh-cache 发布层验证。
