# 2026-11-18：本机 CK3 更新、经济研究与金融模组设计

执行机器 `machine_id: 4-8e1c2f1861`，工作目录 `C:/workspace/ck3_eternal_recurrence`。本次范围为更新本机 Steam 安装、同步项目、分析正式版经济系统，以及设计独立的「期货市场与虚拟货币市场」模组。没有启动 CK3、注入 DLL、接续旧自动游玩、实现或发布新模组。

## 安装结果

`2026-11-18T07:00:11.716858Z` 由 `steam-ck3-versions` 的实际安装回读确认：

| 项目 | 结果 |
| --- | --- |
| 更新前 | `1.20.0.4`，build `25734779`，分支 `1.20.0` |
| 更新后 | `1.21.0 (Florin)`，public 分支，build `26622941` |
| Steam 状态 | `StateFlags=4`、`UpdateResult=0`、当前与目标 build 相等 |
| 下载/部署 | `1,358,446,000 / 1,358,446,000` 字节；部署 `3,749,093,613 / 3,749,093,613` 字节 |
| EXE 大小 | `114,756,216` 字节 |
| EXE SHA-256 | `2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc` |
| launcher-settings SHA-256 | `9494b94341519fb94dd7d56f48a3aae50ee8a0b418a40de1b4b3a5695f3e83b8` |

安装路径为 `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III`。原始回执在外置目录 `C:/workspace/ck3-market-task-20261118/steam-wait-public-04/result.json`，其 SHA-256 为 `d9c29160c89276917688f97352e4d26476a3706403c569d60193fbe7ec29b096`。

最初 Steam 缓存把 public 指向旧 `1.20.1.2 / 26046173`；切换和等待回执中的超时保留。通过官方客户端正常重启及其 console `app_info_update 1` 刷新元数据后，才读到并完成正确目标。登录界面随后自动恢复既有账号会话，无需用户提供密码或验证码。没有编辑 appmanifest/VDF 来伪造分支或下载结果。

## Steam 收尾与运行边界

下载完成后于 `07:03:33Z` 调用官方「进入离线模式...」菜单；紧接着的后台 UIA 读回包含「Steam 当前处于离线模式」和底栏「离线模式」。回读保存在 `offline-confirm-dialog03.json`，SHA-256 为 `6b02f7901c62631f911f2babd8fb876f63ba438c4f67b94cde30bdce5ec4a3a8`；未为状态确认另行截图。SCREEN 已于 `07:04:40Z` 释放。

同机 `tools/steam_offline_state_probe.py` 在 `07:03:44Z` 返回 **unavailable**：当前客户端原生 provider 不可用，且未启用 CDP；诊断为 `native_provider_unavailable=invalid_input`、`cdp_not_enabled`。这是保留的真实限制：客户端 UIA 已显示离线，受管游戏的原生离线准入尚未取得 `status=offline`。本任务不启动游戏，也不将 UIA 回读冒充该原生资格。诊断原件为 `steam-state-final.json`。

旧 exact-build 原生 DLL、地址、结构与资格没有自动转用于新版；本次安装成功和静态脚本研究均不表示它们已通过迁移或实机验证。

## 文档与核对

- [经济系统分析](../ck3-1.21-economy-analysis-2026-11-18.md)：官方来源与本机正式脚本交叉核对，区分实际定义、开发期数值和未核实的引擎行为。
- [模组综合设计](../design/futures-and-virtual-currency-markets.md)：产品范围、资金来源、指数、期约、两类账币、数值账例、GUI、生命周期、性能和分期验收。
- [可携带来源索引](../ck3-1.21-economy-sources-2026-11-18.json)：官方固定链接、安装身份及定向读取的原版文件指纹。没有提交原版完整脚本、公告全文或截图。

初始项目从 `322e3ca70` 快进至 `94ee9256ce2d2dac76fa51fc2bc0c022038ac3a1`；审稿期间再次 fetch 并 rebase 至 `21dc308df85bce2a5a4dbaa37845bc805e8068c0`。最终文档提交以正常 Git 历史为准，不创建 merge commit，不覆盖其他任务改动。

本轮通过三份 Markdown 的 16 个本地链接、来源 JSON 解析、13 行金币账例守恒，以及逐月差额、AMM 往返、非整除舍入、乘积不减与储备互斥分类检查；113 个静态文件指纹和八组计数经独立 cmd/Python 复核。原件为外置 `document-review.json`。未改运行代码，不以文档检查宣称脚本、界面或资金效果已通过实机。

过程偏差：研究分岗曾误用 PowerShell 做只读静态读取、计数及外置 JSON 写出，违反项目的命令外壳约束；发现后已停止，后续命令统一 `cmd.exe / login:false`。该偏差未操作游戏、Steam 或进程，也未更改仓库源码；不将其计为实机验证。

## 存储与证据期限

更新前有完整的项目根元数据清点，共 `1,457,019` 项、逻辑占用 `154,676,131,196` 字节；可用空间 `76,331,905,024` 字节，覆盖 35 GiB 下载峰值、8 GiB 系统增长与 20 GiB 安全预留。沿通用策略登记了至 `2026-11-19T06:34:46Z` 复核的临时配额覆盖，既有树均保留，本轮删除为零。

闭场增量检查及任务外置文件清单保存为 `storage-task-close.json`，不重复扫描或散列全部旧项目。原始回执按通用策略 720 小时后进入复核，派生检查材料按 48 小时复核；到期仅作为可回收候选，不自动删除活跃输入。小型正式文档留在 Git，外置资料不作永久保留承诺。
