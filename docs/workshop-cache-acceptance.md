# Steam 创意工坊缓存验收

2026-10-07，项目所有者明确要求：

> 我要求你简化“缓存实机验收”步骤。 让 CK3 加载 Steam 实际下载到本机的已发布模组，确认玩家下载到的文件与正式构建一致就行了，不要再次检查在游戏中运行。后续对于这些mod的发布全部改成这个规定，你更新到对应的docs里。

本规则适用于本仓库全部现有及后续 mod 产品、首次发布和更新发布，自上述指令起执行。它覆盖旧文档、交接、操作卡和 runner 计划中的缓存代表业务或缓存完整矩阵要求。

## 仅有两项缓存验收

1. 确认目标 Workshop item 的已发布内容由 Steam 实际下载到本机。用该次正式 tag 构建的 manifest 及产品现有 `--workshop-cache` 校验方式，核对实际下载文件的清单、大小和 SHA-256；保留下载与核对回执。不得用仓库、staging 或旧本地副本覆盖 Steam 缓存后再授予通过。
2. 让 CK3 加载这份实际下载缓存。记录实际游戏版本、进程和缓存路径，并保留 CK3 对目标 mod 实际挂载/加载的证据。成功启动的实际加载日志能证明目标 mod 及来源路径时即满足要求；启动器勾选、准备 profile 或进程启动 ACK 本身不证明加载。无需新开战役、选择角色、进入地图或查询完整 native 业务状态。

两项成立，缓存验收即通过。随后正常关闭 CK3，保持 Steam 离线并释放进程和屏幕资源；这些是既有现场收尾操作，不新增缓存业务门槛。

## 共用菜单加载入口（2026-10-09）

全部产品复用[公共六模式入口](../tools/ck3_mod_acceptance.py)的`--case workshop_cache`，共同case与[adapter](../tools/ck3_mod_acceptance_cases/workshop_cache_adapter.py)只定义一次。产品身份取[canonical清单](../workshop/products.json)；没有公开item ID的开发版不能推测下载目标。产品不复制host、DLL、启动器、正常退出或SDK下载实现。

`prepare`只消费本次实际SDK下载回执、正式tag的manifest、下载cache路径与四份普通配置。沿用现有严格cache verifier，仅容许正式descriptor中已有的启动器ID注入归一化；缺失、额外、改字节或错误ID均拒绝。新profile只有六份普通输入，外层descriptor直接指向实际Steam下载目录，不复制cache、不挂fixture。SDK下载仍由原发布入口执行，prepare不会下载、启动CK3或授予加载通过。

加载采用既有现场已接受的组合证据：同一实际受管CK3进程的PID、创建时间、真实启动命令和userdir绑定上述单产品profile；native实际读回两次连续、完整且可见的主菜单route/tree，核当前游戏build、pipe和generation，并绑定该profile的只读引擎诊断。它证明这次实际启动已完成目标cache配置的菜单加载；不把单独的配置、ACK或截图当加载通过，也不声称取得独立引擎VFS路径读回。独立VFS字段未知不新增门槛。无需New Game、Start、人物、地图或游戏内业务。

公共客户端沿用原正常GUI Quit、独立retained OS0/native0及清理/keeper/CAS。菜单模式拒绝日推进、载入存档及业务动作；源码功能验收继续使用各原case。新增菜单6项、cache9项离线回归已实际通过并接入原CI；首次公共菜单模式的实际qualification仍待真实发布后run，不将代码采用写成实机PASS。

## 发布流程中的使用

发布前仍完成对应产品源码/正式 staging 的功能验收。发布后不再重复检查事件、决议按钮、特质、数值、冷却期、任命、存载业务、自然时间链或其他游戏内功能；不挂载业务测试 fixture，不重跑代表业务 cell 或完整业务矩阵。已取得的真实缓存文件核对及实际加载证据直接复用，不为新规则再次启动或下载同一版本。

正式 tag/staging、实际上传、公开完整 Change Notes、兼容标签、无 ID staging 恢复及永久 changelog/master 提交推送继续使用各自既有发布规则。本文件只调整缓存验收范围。

永久发布记录应注明本规则日期、实际下载及文件核对证据、实际 CK3 加载证据与现场收尾。不把“缓存加载通过”写成新的功能实测通过，也不改写发布前源码验收的版本或范围。

旧失败、raw、冻结输入和当时的验收结论保留。对于按旧规则已加载缓存、随后因可选业务复验失败而 pending 的发布，直接按本规则评估已有文件核对和加载事实，追加说明旧业务复验已不再是缓存门槛；不得将旧失败改为业务 PASS。

相关入口：[发布流程](workshop-publishing.md)、[MCP 发布](workshop-publishing-mcp.md)、[原生下载](workshop-native-download.md)、[测试流程](testing-workflow.md)、[产品清单](../workshop/products.json)。


## 2026-10-09 首次公共菜单模式实机资格

TED 1.0.1 的 R0023 已实际消费同一 Source09/FINAL10/bound11 公共
`workshop_cache` 入口。原 SDK 下载完成，公共 prepare 对正式 tag manifest
核对 strict16 一致；单产品普通 profile 直接指向该下载缓存。实际 CK3
1.20.0.4/PID 28112/generation 1 取得同一受管启动、profile 与稳定主菜单
native 读回的组合加载证据，随后真实 GUI Quit、独立 retained OS0/native0、
job0→0、线程清理、原 keeper0 与 CAS 7530 done/resources[] 完成。Root
亲审闭场后的新鲜 Steam 离线原图。原 common run/verify 均0，
case_acceptance_pass 与 qualified_boundary_pass 为 true；business_pass 和
product_release_pass 保持 false。

这是上方“首次 qualification 待 run”截止之后取得的实际资格，不重写旧记录。
独立引擎 VFS 路径读回仍 UNKNOWN，未新增此门槛；没有 New Game、Start、
地图或缓存业务复验。原始下载、strict16、加载、正常退出和离线 pins 见
[TED 1.0.1 发布证据](release-evidence/tributary-expansion-directives/1.0.1.json)。
其他产品后续发布仍各自取得其真实下载文件与实际加载证据，不由本次外推。
