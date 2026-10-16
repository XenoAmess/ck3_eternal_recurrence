# 专属磁盘回收与每日巡检（2026-10-16）

`machine_id: desktop-3fevhd2-1c74096080`。本轮按用户明确要求启动独立回收 worker，执行[通用存储策略 v1.0.0](../storage-retention-policy.md)。实际观察窗口为 `2026-10-16T09:18:36Z` 至 `2026-10-16T09:43:05Z`，全部为 UTC。旧文档中的“永久保留全部过程资产”未作为本轮阻止过期回收的依据。

已实际删除 **156 件，失败 0，单链接分配量 28,545,642,496 B（约 26.59 GiB）**；逻辑量 28,545,541,211 B。所有目标原路径均再次读回确认不存在，不再可读。没有删除目录，没有改动当前 E04 原片、seed、游戏、Steam、SDK、桌面、安装依赖或容量准入。

| 批次 | 实际范围 | 件数 | 逻辑量 B | 单链接分配量 B |
| --- | --- | ---: | ---: | ---: |
| 01 | 已闭场 Superman 旧 `melted.ck3`，保留当前 SHA 相符的 binary checkpoint、精确 decoder 与报告 | 21 | 2,351,187,686 | 2,351,239,168 |
| 02 | 旧 v3/v4 视频重复原片与过程 ZIP、Superman 已完成 render 的重复 ZIP；每组保留一份实测同字节副本 | 23 | 15,740,227,276 | 15,740,268,544 |
| 03 | 9 月 22 日已成功消费的 Torch wheel、分段下载及被完整已验证模型替代的两份网络失败 partial | 111 | 10,351,684,310 | 10,351,689,728 |
| 04 | Superman R0006 冷归档的可重建完整文本导出 | 1 | 102,441,939 | 102,445,056 |

C 卷回收 25 件、分配量 4,040,736,768 B；D 卷回收 131 件、分配量 24,504,905,728 B。闭场 `09:43:05Z` 新鲜容量读回：C 自由空间 **32,068,505,600 B**，D **47,153,627,136 B**。卷自由空间还受并发 Root/系统写入影响，不能把净差全部归因于回收，也不能由此延长旧配额或认定下一次重型写入已获准。

每批先冻结精确候选及 SHA，执行前校验 realpath/重解析点、文件身份、大小、时间、硬链接数和实际内容；目标用 Win32 独占 `GENERIC_READ + DELETE + READ_ATTRIBUTES` 句柄校验并在同一柄上删除，关闭后读回不存在。保留输入在删除期间持有禁止写入/删除的句柄，前后身份与 metadata 均不变。批 02 还核对了当前 E04/Review02、Review01 基线及外置 `review02-*` 的 1,112 份代码、配置和 manifest/source 索引，没有命中候选旧路径；删除前再次确认其 SHA 未变。旧 manifest 保持历史原样，不把已删除路径自动改指其他副本。

[小型回执包](storage-retention-2026-10-16-dedicated-worker/manifest.json)共 482,406 B，包含[汇总](storage-retention-2026-10-16-dedicated-worker/summary.actual.json)、[逐件当前可用性](storage-retention-2026-10-16-dedicated-worker/availability.actual.json)及四批 plan/result。保留来源仍是机器本地文件；本包不声称其他机器拥有这些大文件。重建文本导出须使用各 plan 绑定的保留 binary、decoder 和 recipe，并写入新的派生路径。已删除 wheel/分段缓存若日后重装需要，须按保留的官方精确 URL/SHA 重新下载；本轮没有重新验收 IndexTTS 运行能力。

## 定时缺口与实际整改

任务开始时，统一策略明确 `automatic_gc_implemented=false`，当前 Task Scheduler 清单也没有项目存储巡检任务；此前不能声称已经定时回收。本轮已新增 [Python 只读巡检器](../../tools/storage_retention_inspect.py)与[聚焦测试](../../tools/test_storage_retention_inspect.py)，3 项测试通过，覆盖实际最后使用时间、当前引用/未知闭场/超期保护、跨机器和路径越界拒绝。

**本机每日任务已真实安装，并由 Task Scheduler 实际运行成功。**

- 名称：`\XAR-CK3-Storage-Daily-ReadOnly-Inspection`。
- 每日北京时间 `04:00`，XML 首次边界 `2026-10-17T04:00:00+08:00`，`StartWhenAvailable=true`。
- 当前普通用户 `InteractiveToken`；typed COM 读回 `RunLevel=0`、`LogonType=3`、启用，执行上限 `PT2M`。使用现有 `pythonw.exe`，不弹出控制台、不保存密码、没有 UAC 或管理员任务。
- 实际 `/Run` 后产生新的 machine-bound daily JSON，`LastTaskResult=0`；同一 UTC 日再次常规调用实际返回 `daily_inspection_already_recorded`，没有生成第二份常规盘点。低空间、任务开始、重型写入前和闭场是独立显式触发原因。
- [冻结 argv/脚本、解释器、profile、ledger、XML 的精确 SHA](storage-retention-2026-10-16-dedicated-worker/scheduler-intent.json)、[实际 XML 与 typed COM / 运行报告](storage-retention-2026-10-16-dedicated-worker/scheduler-readback.json)均保留。初次字符串检查因 Windows 导出 XML 省略默认 `RunLevel` 而失败，随后直接读取 COM 数值 0 验证最低权限，没有重新注册或提权。[Microsoft 的权限语义](https://learn.microsoft.com/en-us/windows/win32/taskschd/security-contexts-for-running-tasks)与 [LUA=0 定义](https://learn.microsoft.com/en-us/windows/win32/api/taskschd/ne-taskschd-task_runlevel_type)支持此判断。原始 COM 时间字符串按原样保全；调度时区以带 `+08:00` 的 XML 为准，不把 COM 包装器附加的时区当作 UTC 实证。

任务只读显式资产台账并输出复核候选，**没有自动删除新对象的能力**。普通用户任务需要该用户处于登录状态；已设置错过后可运行，但没有模拟注销/错过时段验证补跑。每份报告上限 1 MiB，台账/输入也限 1 MiB；未入账对象保持 unknown，未知容量参数保留 null，巡检器永不授予重型写入、容量预留或配额延期。不能将这个任务称为全机自动 GC 或已经部署至其他机器。

本机稳定入口位于 `C:/ck3-e04-resume-20261015-a01/disk-reclamation-worker-a01/scheduled-inspection-a01/`：`machine-profile.json`、`asset-ledger.json`、`reports/`。初始冻结台账已另存，四批实际回收随后通过同一 inspection lock 更新为 156 个 `deleted_unavailable` 和 1 个待复核对象；[台账更新](storage-retention-2026-10-16-dedicated-worker/ledger-update.json)与[闭场实际检查](storage-retention-2026-10-16-dedicated-worker/ledger-close-check.json)分别记录，不让新台账重新解释首份调度报告。

后续工作包在创建/闭场时应向这份本机台账登记资产组、实际用途和期限，使用同一 `reports/inspection.lock` 串行更新；每日任务据此产出候选。回收 worker 再独立冻结精确文件清单、核当前消费者及替代证据、检查 OS 句柄后执行。调度器只会查看已登记组，未实现新目录自动分类；新增工作包不能仅依赖这个任务而省略任务开始、重型写入前和闭场检查。

## 剩余对象的实际边界

R0014 `melted.ck3` 103,418,000 B 仍在。初始 scanner 只读取 `melt_command` / `retained_checkpoint_sha256`，误把采用 `melt_argv` / `checkpoint.sha256` 的另一 schema 解释为完全没有 recipe；本轮已纠正。其报告确有 recipe 与 checkpoint SHA，但缺该场 decoder SHA 绑定，当前源与重建结果尚未独立复核，因此没有删除。台账下一次人工复核期限为 `2026-10-18`，不是自动续期或自动删除许可。

唯一的 Episode02 原片、5.245 GB 历史 SDK 日志和其余未分类大文件没有因名称旧或目录含 cache 而删除：仍分别需要当前用途、期限或精确响应重放证明。7 个增量盘点 pass 每批少于 100,000 metadata、120 秒，记录了游标；扫描窗口与回收并行，其累计逻辑量不是原子当前占用，不直接用于新的配额准入。安装中的解释器、uv Python、uv-cache 运行库、venv、完整模型全部保留。

精简回执于 `2027-04-14` 复核；详细逐文件台账于 `2026-11-15` 归纳复核。保留来源按各批已记录的期限重新评估，不自动永久保留。
