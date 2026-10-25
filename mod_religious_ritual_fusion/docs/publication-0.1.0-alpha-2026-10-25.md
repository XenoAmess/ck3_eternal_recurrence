# 0.1.0 Alpha 首发执行记录（未完成）

`machine_id: 4-8e1c2f1861`；更新至2026-10-25T07:48Z。用户已明确要求发布到 Steam 创意工坊。新增授权清理本机CK3 Workshop载荷后，容量已通过；正式a03包和六张实机图已保全，条目仍为3826756673。07:34Z本机登录失效，实际窗口提示另一台计算机已登录，更新在Submit前被拒绝；目前等待用户完成本机登录，尚未公开发布或验收缓存。下文保留首次失败及后继实际结果，不把条目创建、构建或调用ACK计为公开发布。

## 05:46Z 首次提交所用载荷和页面素材（历史）

- 产品版本 `0.1.0-alpha`，标签 `religious-ritual-fusion-v0.1.0-alpha`，内容提交 `7b0c9b6c80a058c20193913387ddfe8a732f8efe`。
- 默认命令行 Maven 3.10.0 的本轮完整 `verify`：20 tests，0 failure/error/skip，退出0；随后新 Jar `validate`、`build`、`verify` 均退出0。七种新增翻译由既有 MiniMax-M3 候选流程产生，九语各65键通过格式检查；没有逐语人工语义审校或外语实机验收。
- 首次提交所用 staging：`C:/workspace/rrf-development-20261024/release-staging-0.1.0-alpha-a02`，75文件、1,083,422B。清单同级 `.manifest.json`：14,130B，SHA-256 `0690cc5aa49a2bce98de364903acb844b6b192a750ced52584f7c518e69cfde2`。a01因 rebase 被替代，不能上传；两份75个文件内容相同。后继canonical清单已替换为a03，见本文末尾。
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

## 06:13Z 时的续行准备（历史）

空间条件满足后先做新的机器／容量／离线准入，不复用旧64MiB许可。重新核当前账号与同一item的实际媒体快照，针对 **3826756673** 更新正式75文件、封面、六图、完整Notes和public可见性；已知失败可新建update操作，未知结果不得重放。

来源绑定的inactive CMake候选只有语法检查，没有运行回归；已完整保存为外置 `inactive-cmake-source-binding.UNVALIDATED.patch`（41,916B，SHA `8ec64f149e92f88569c8bdc404eb0690806c97ff37c6cd8895b5929a52cac586`），并撤出生产工作树。它不属于已通过的发布包。若缓存菜单运行仍需该候选，先重新应用并完整执行既有10条回归／静态检查，再以clean源码生产真实来源证明；保留原DLL构建身份。

上传成功后匿名核对标题／说明、兼容版本、六图和Notes全文；经原生Steam下载确认75文件与正式清单一致，再运行无fixture、无战役的公共 `workshop_cache` 菜单加载。最后更新[永久changelog](../../docs/release-changelogs/religious-ritual-fusion/0.1.0.md)、恢复Steam离线并提交／推送实际记录。原R8/R10完整场次GAP不改变。

## 用户新增清理授权及正式清单接管

用户随后明确允许清理这台机器Steam订阅下载的全部CK3模组本地载荷。[本机实际清理](../../docs/maintenance/2026-10-25-ck3-workshop-cache-cleanup-4-8e1c2f1861.md)已完成：86,120文件／87批／0拒绝，Native释放38,318,603,536B，订阅及ACF保持。revision123的新128MiB发布准入通过，上一阶段的容量BLOCK保留为历史结果。

共享缓存消费者要求canonical正式manifest（`format_version/workshop_item_id/git_tag/git_sha/files`）；旧a02的Java manifest不具备该合同。后继仅迁移正式release record及其build/verify消费者，生成目录和fixture合同保持各自边界；完整Maven23tests零失败／零跳过，实际Java producer已进入现有共享 `validate_manifest` 和逐文件 `_verify_cache` 回归。75个载荷的路径／大小／SHA均与a02相同。

因此a02及旧标签 `religious-ritual-fusion-v0.1.0-alpha` 是历史失败候选。当前正式后继计划使用新匹配标签 `religious-ritual-fusion-v0.1.0-alpha-publish1` 和a03 staging；新完整SHA、canonical manifest及实际发布结果在封包后追加，不移动旧tag，不将更新后的构建器追认为旧源码。

此前外置的inactive CMake候选已重新应用并完成约定10条CI命令：199 tests、0 skip，4条静态检查退出0。此修复只证明两个明确OFF条件内的精确wire迁移不改变原production编译输入；旧DLL和原编译提交保留，未重编正式DLL。既有小型MSVC测试fixture编译属于本轮完整CI范围。第7条CI原wait0，但外置采样器遇到一次临时文件读取PermissionError而保守记录FAIL；其原件保留，后续8–10独立接续0，不宣称采样全程完整。完整回执 `public-chain-a01/inactive-prisoner-cmake-a01/VALIDATION.full-scope.actual.json`：7,189B，SHA `a65076ee580686fe0e72a216a611afa5c1ed13e8623e90a484cc6c4ce3e4dfb6`。最终clean源码还须实际执行producer→qualifier，再授予本次runtime来源资格。

## 07:34Z 后的实际状态：容量已解决，等待本机重新登录

`machine_id: 4-8e1c2f1861`；记录日期2026-10-25。a03 的正式源码为 `f48c3f2ed531ca60a802c11a74b93e5c394fe8b5`，匹配标签 `religious-ritual-fusion-v0.1.0-alpha-publish1` 已推送；没有移动旧标签。canonical manifest 为14,228B，SHA `84aab0f47399c62f0442f4dc4bc4a185333f0ce5cfdd124c7314692643b9b44c`。75文件／1,083,422B 与旧a02的实际载荷完全相同；完整Maven23tests以及实际共享manifest与逐文件消费者均通过。

07:27Z，对同一条目3826756673准备public更新，包含封面、六张真实JPEG、完整说明、Notes及三个完整标签。计划 `public-update.plan.json` 的payload SHA为 `5d4a5e43f7d9322c77188925c394e44173593d8dfe5ad6f0312e4e4aa189d344`。07:34:05Z实际调用现有MCP；子进程PID23732，07:34:07Z退出1。原生错误为 `Steam user interface reports BLoggedOn=false`，原业务回执停在 `item_id_recorded`；本次没有调用StartItemUpdate或SubmitItemUpdate，也没有再次CreateItem。

随后只读UIA检查实际“登录刷新”窗口，显示“此帐户已在另一台计算机上登录”。已停止发布并请求用户结束其他机器使用、在本机完成登录；没有读取、填写或保存密码，没有强行接管账号。原生暂停下载操作进程正常退出0；在实际登录窗口Invoke“退出Steam”后，07:36:27Z后台进程读回Steam和CK3均0。最后一次离线探针是 `unavailable`，**不声称已确认offline**；联网阶段以客户端实际退出终止。屏幕声明按CAS释放；另一次过期声明的释放保留 `unresolved_red`，不改写成业务通过。

关键原件均在 `C:/workspace/rrf-development-20261024/publication-a01/`：`PUBLIC-UPDATE.login-expired-stop.actual.json`（SHA `d2136d7208167009bd0fa4ca1c5ebff768311baf022b07d58140ef10a87c5fa5`）、`public-update.receipt.json`、MCP stdout/stderr、实际登录窗UIA、退出Invoke及进程读回。用户目录外层.mod已指向a03，并保留唯一canonical remote_file_id；其换行纠正后的实际回执为 `OUTER-MOD.a03-path.line-endings.actual.json`。源码和staging内层均无该ID。

匿名公开核对另遭HTTP429，原stdout/stderr保留；未把此结果解释成可见性、内容或Notes通过，也未换代理或凭据绕过限流。公开标题／全文说明／兼容版本／六图及Notes全文、真实Steam下载和实际CK3缓存加载仍未完成。

07:42Z统一账本head124关闭publication/Java/menu预留，仅留下32MiB来源资格和Root小型收尾，共用原08:30Z截止；旧128MiB不再授予Steam写入。闭场回执 `PUBLICATION-CLOSED-ACCOUNT-BLOCKED.actual.json` 为6,007B，SHA `996f564ba229ff5459715c66b84788b4775768c2a155968e56b7ce9d32014161`。freshfree126,848,888,832B，容量不再是当前阻断；菜单224MiB仍只是候选。

恢复时使用同一ID和已保全的a03包、六图及冻结文案；先重新核机器、容量与账号，发新发布准入，查询实际媒体快照，再按现有持久回执安全续行。成功后才做匿名精确公开回读、真实原生下载及无fixture／无战役的公共workshop_cache菜单加载和正常退出。既有R8/R10完整场次GAP及其他业务NOT_RUN不变。

## 07:46Z 实际来源资格闭环

对clean f48c实际执行原CLI来源绑定producer，原等待退出0；随后现有公共`qualify_native`实际PASS／退出0。保留原编译提交 `d13c6721b281235dad3628674b85b1b321118b33`，原15,711,744B DLL的SHA为 `ff6916d2ff3cff737803c910ac28452ad1d141fe540b7a0994e05197f91a74af`；835个production源通过严格校验，完整native树仍不相等，没有声称重新编译了当前源码。

此前旧host pin实际被拒绝，原a01小回执保留；当前host新增三行接口声明，经现有九条完整CI命令（77项测试、零跳过、四项静态检查）及实际有限consumer正／拒绝路径后，生成真实当前review、三refs及shared_host资格。有限consumer使用软件及owned DTO，并未启动CK3或授予真实囚犯业务资格。此链没有修改tracked源码。

外置原件根为 `publication-a01/inactive-cmake-final-f48-a02/`。`HANDOFF.actual.json`：7,322B，SHA `4aec2dd9a8f1dceaff36edf9efff63633f2e8c125195dec9f34ea7e380b27477`；`QUALIFY-NATIVE.actual.json`：4,489B，SHA `c5f3cb62b5b84818e1b03d474b9ac915451a7b674a87e150333241d57068e0f6`；binding：2,714B，SHA `00b40e7814318a7f0366c9aa923540e40ce0c6d55eebfb87ea9d60c7563c6568`。完整原argv、PID、原wait、stdout/stderr及16项pin都在交接中。

该资格只绑定f48c，不等于runtime已构建、Steam缓存已下载、CK3已加载缓存或任何实际业务通过。后续master为接收其他产品和下载器更新而线性rebase；不能将f48c资格外推为新HEAD已验收。当前真实来源须在后继runtime中重新绑定，原DLL、回归和业务历史身份保持。产品登记中的正式命令参数同步补入现在必填的`--git-tag`和`--workshop-item-id`；不会据此重写已经保全的a03包。
