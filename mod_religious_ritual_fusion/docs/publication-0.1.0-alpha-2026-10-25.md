# 0.1.0 Alpha 首发执行记录（未完成）

`machine_id: 4-8e1c2f1861`；记录时间 2026-10-25T06:13Z。用户已明确要求发布到 Steam 创意工坊。本记录不把已创建条目、构建通过或调用 ACK 计为已公开发布。

## 正式载荷和页面素材

- 产品版本 `0.1.0-alpha`，标签 `religious-ritual-fusion-v0.1.0-alpha`，内容提交 `7b0c9b6c80a058c20193913387ddfe8a732f8efe`。
- 默认命令行 Maven 3.10.0 的本轮完整 `verify`：20 tests，0 failure/error/skip，退出0；随后新 Jar `validate`、`build`、`verify` 均退出0。七种新增翻译由既有 MiniMax-M3 候选流程产生，九语各65键通过格式检查；没有逐语人工语义审校或外语实机验收。
- 唯一可上传 staging：`C:/workspace/rrf-development-20261024/release-staging-0.1.0-alpha-a02`，75文件、1,083,422B。清单同级 `.manifest.json`：14,130B，SHA-256 `0690cc5aa49a2bce98de364903acb844b6b192a750ced52584f7c518e69cfde2`。a01因 rebase 被替代，不能上传；两份75个文件内容相同。
- Root 上传前再次比较全部相对路径、大小及 SHA：75/75，extra/missing/mismatch均0。源码及 staging 内层 descriptor 无 `remote_file_id`，仅用户目录外层 `.mod` 保存实际 ID。
- [封面来源与完整生成提示](media/cover-0.1.0-alpha.json)：内置 imagegen 新生成独立宣传插画，Java ImageIO 编码为512×512 PNG，696,215B，SHA `1f6b9353d4df99eb5e34a2482aef561731d2df75976a36ffa2a01f7f95f5d5ba`；不作为实机证据。
- [六张实机图](../../workshop/religious_ritual_fusion_screenshots.md)：保留2560×1440，Java ImageIO JPEG quality0.90纯格式转换，合计4,367,884B，每张小于1MiB。原PNG、捕获身份及R8/R10验收边界保留。
- [商店说明](../../workshop/religious_ritual_fusion_description.bbcode)冻结为3,093 UTF-8 B／1,588字符／40行，SHA `1a166060108f7256c8c8126ad59482abdac0ff9d49134a7ed90faa4f76c16498`。
- [完整 Change Notes](../../workshop/religious_ritual_fusion_0.1.0-alpha_change_notes.txt)冻结为1,719 UTF-8 B／863字符／14行，SHA `17176db70b020e922ad8164df5457bfc185d6825f18a85085a33a22da0990176`。公开全文回读尚未完成。

Java原始回执在 `C:/workspace/rrf-development-20261024/publication-java-a01/`；交接 `HANDOFF.actual.json`：3,791B，SHA `0915a56c90637b37bee8311538df6631b8e2caed6ad12e892635fb36e8164a8d`。其余本轮原件以 `C:/workspace/rrf-development-20261024/publication-a01/` 为根。

## 实际 Steam 结果

后台离线探针于05:32:21Z确认离线。随后只为本次发布经实际 Steam 菜单控件 Invoke 临时上线；没有使用坐标点击。05:38Z原生 probe 实际返回 AppID1158310、`logged_on=true`、账号 `76561198273714027`。DLL来自当前安装目录，298,384B，SHA `1db3fd414039d3e5815a5721925dd2e0a3a9f2549603c6cab7c49b84966a1af3`。

经现有 `ck3_workshop_mcp` 的 `workshop_native_publish` 提交正式包。为先配齐媒体，首次创建计划设置 private；此时没有宣称公开发布。

| 阶段 | 真实结果 |
| --- | --- |
| CreateItem | 2026-10-25T05:46:20Z，EResult1，ID **3826756673**，不要求接受新的 Workshop 法律协议 |
| 首次 SubmitItemUpdate | 2026-10-25T05:50:19Z，明确 **EResult2**；原件 `create.receipt.json` 的 `stage=submit_failed` |
| Steam自身日志 | `workshop_log.txt`：`Failed to initialize build on server (No Connection)`，本次未完成内容上传 |
| 公开页面、六图、版本标签、Notes | 未验证；尚未完成公开发布 |
| 真实 Steam 下载及 CK3 加载缓存 | 未执行；未启动 CK3，不重跑功能验收 |

本次计划预演出的完整标签为 `Religion`、`Gameplay`、`1.20 'Crozier'`。首个结果是已知失败，不是结果未知；下一次使用同一 ID 的 update，**不得再次 CreateItem**。canonical产品登记及用户目录外层 `.mod` 已保存该 ID，不能因此称发布成功。

## 容量、清理与离线恢复

临时上线后，Steam对既有订阅发起自动更新。Root确认下载队列0、网络/磁盘0bps，CK3项目显示磁盘写入错误而未安排。05:54:03Z及06:11:58Z后台原生探针均重新确认 `status=offline, offline_mode=true`。

只回收本次05:38Z之后新建、现已明确废弃用途的3654个未完成下载文件；4批原生独占句柄、SHA和文件身份复核后全部成功，0拒绝，Native实际释放 **1,766,805,376B**。没有删除既有控制标记、depot manifest、顶层patch、安装内容或订阅。精确实际回执：`publication-steam-recent-staging-a01/reclamation/ACTUAL.actual.json`，5,984B，SHA `f6d250522f73005599ef44fdf3ca72dabc63bbd6c70ce5e6d3b8009b52b3f7be`。

回收后统一账本revision121。实际free `88,701,362,176B`；维持既定其他任务上界、15GiB系统增长和20GiB安全余量时，8MiB来源验证仍缺65,662,566B，64MiB发布预算缺124,382,822B，224MiB菜单缓存场次缺292,154,982B。不是游戏实际文件需要88GB，而是整个卷的固定预留仍不足。没有降低预留，也没有拿其他机器的安装或空间事实代替本机。

后续窄查确认R7/R8缓存已空，旧runtime/source/prepared副本与R4残余不足，当前Q引用的对象和R8/R10存档、读回及照片继续保留；不重复计算已回收空间。最终不足及边界原件在 `publication-steam-recent-staging-a01/`。已请求用户释放至少500MiB或指定其他可清理目录。

为后续联网控制后台下载，临时调用了当前DLL正式导出的 `SuspendDownloads(true)`，仅记录void ACK；没有在线效果验收。06:11:58Z确认Steam离线后调用false并正常结束该操作进程，未留下后台暂停器或永久客户端设置。正式接口依据：[Valve文档](https://partner.steamgames.com/doc/api/ISteamUGC#SuspendDownloads)。屏幕租约已CAS释放，未启动游戏。

## 继续执行

空间条件满足后先做新的机器／容量／离线准入，不复用旧64MiB许可。重新核当前账号与同一item的实际媒体快照，针对 **3826756673** 更新正式75文件、封面、六图、完整Notes和public可见性；已知失败可新建update操作，未知结果不得重放。

来源绑定的inactive CMake候选只有语法检查，没有运行回归；已完整保存为外置 `inactive-cmake-source-binding.UNVALIDATED.patch`（41,916B，SHA `8ec64f149e92f88569c8bdc404eb0690806c97ff37c6cd8895b5929a52cac586`），并撤出生产工作树。它不属于已通过的发布包。若缓存菜单运行仍需该候选，先重新应用并完整执行既有10条回归／静态检查，再以clean源码生产真实来源证明；保留原DLL构建身份。

上传成功后匿名核对标题／说明、兼容版本、六图和Notes全文；经原生Steam下载确认75文件与正式清单一致，再运行无fixture、无战役的公共 `workshop_cache` 菜单加载。最后更新[永久changelog](../../docs/release-changelogs/religious-ritual-fusion/0.1.0.md)、恢复Steam离线并提交／推送实际记录。原R8/R10完整场次GAP不改变。
