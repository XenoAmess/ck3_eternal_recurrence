# 0.1.0 Alpha 首发执行记录（已公开，缓存验收未完成）

`machine_id: 4-8e1c2f1861`；2026-10-25。用户再次要求重试后，本机登录恢复，同一条目 **3826756673** 于08:02:19Z公开提交成功。匿名标题／完整说明／完整更新日志核对通过；六张公开实机图和封面均与提交素材逐字节相同。当前缓存下载因旧订阅目录拒写而失败，未启动缓存加载场次，完整release闭环仍未完成。Steam于08:25:11Z由后台原生探针确认恢复离线。下文保留最初网络失败、容量阻断、登录失效和后继实际结果。

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

## 云端检出故障修复

收尾master `2f7b10ea5cfa890dce8c316148fa9c18f3213c07` 的 [RRF静态CI 40174479553](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40174479553) 于07:54Z在actions/checkout失败，原日志为`Filename too long`／Git exit128，尚未执行Maven或产品测试。日志原件在 `publication-a01/CI.failed-40174479553.log`。RRF工作流补入既有Official Runner CI使用的job级`GIT_CONFIG_COUNT/KEY_0/VALUE_0`，使长路径配置在checkout之前生效；未改载荷或重跑本机已通过的23项测试。后继云端实际结果另以run原件记录，不能把该检出失败称为测试已通过。

## 08:02Z 公开成功及匿名回读

用户回复“你再试试看”后正常重启客户端；08:01Z原生probe确认App1158310、账号76561198273714027、logged_on=true。使用原同一update计划和持久回执续行，没有Create新条目。08:02:19.714556Z实际`SubmitItemUpdate`返回EResult1，`stage=complete`；原生MCP子进程原wait0。Steam日志独立记录上传内容manifest **4029636242467382206**、封面、六图及`Upload finished ... : OK`。正式载荷仍为a03的75文件／1,083,422B，原publish1/f48c身份未改变。

[公开条目](https://steamcommunity.com/sharedfiles/filedetails/?id=3826756673)的匿名API实际返回visibility0、正确owner和双AppID、完整标签`Religion`、`Gameplay`、`1.20 'Crozier'`。标题和说明全文exact。原`change_note`已经进入[公开更新日志](https://steamcommunity.com/sharedfiles/filedetails/changelog/3826756673)，entry **1792915338**，无需owner页面补写；HTML解码、换行及末尾文件换行归一化后全文862字符／14行，SHA `edecb0989f7d7da1bd7447d09c666b780ffa5b9254606ee86089660b55c457d7`，与同法处理的冻结全文exact。冻结文件原始863字符及SHA17176…保持，字符差为末尾文件换行，不是删减正文。

SDK再次无缓存查询返回恰好六项，index0–5／文件名01.jpg–06.jpg。六个公开CDN原图HTTP200、2560×1440，逐字节等于已冻结JPEG，顺序与[截图说明](../../workshop/religious_ritual_fusion_screenshots.md)相同。公开封面HTTP200、512×512 PNG、696,215B，SHA与源封面相同。未重复存储与保留原件相同的公开图片正文。前端详情HTML另遇HTTP429，兼容版本右栏HTML仍待回读；没有用代理或更换凭据绕过限流。

小型机器可读[公开证据](evidence/publication-public-readback-2026-10-25.json)包含实际API、Notes结果、六图、封面、离线及原件pins。本机外置原件根仍为`publication-a01/`，其中`public-update.completed.frozen.json`保全完成态，原登录失效回执的历史状态保留在当时操作记录。`public-readback-after-submit-a02/`保存匿名API、完整changelog原HTML及exact结果；`PUBLIC-SIX-IMAGES.actual.json`和`PUBLIC-COVER.actual.json`保存逐图验证。

## 实际下载失败与离线恢复

两次实际SDK下载均从目标缓存不存在开始。第一worker16444、第二worker17260，匹配App/item的callback3406均为EResult37，installed=false、install_info=null，原worker退出2。外层MCP传输成功／外层命令退出0不等于下载完成。第二次改为先resume再显式高优先级下载，仍然相同失败，未盲目重复第三次。

Steam日志把失败绑定到旧订阅2993056101的`downloads/1158310/.../common/buildings/00_standard_economy_buildings.txt`预分配。该旧item目录实际保留Everyone拒写／删除ACL，父目录正常；全app校验被它中断，随后本目标返回I/O失败。当前ACF尚留91条Installed和85条Details，目标只在Details中。未解除这些控制、伪造安装索引、退订旧模组或复制staging到缓存；不将旧历史下载或源码加载代替本次Steam真实缓存。

联网任务停止后正常shutdown Steam、退出临时SDK暂停器，原keeper正常退出并CAS释放13843，08:22:01Z实际Steam／CK3进程均0。客户端启动时已自行更新至11.15.70.27，不能沿用原11.12.30.7身份。因新客户端菜单未提供可用UIA树，在客户端完全停止时只对当前账号请求WantsOfflineMode=1并静默启动；该配置操作本身不算离线证明。08:25:11Z新的后台探针实际返回`status=offline, offline_mode=true`，PID26192／出生FILETIME134373902961232097，当前SteamUI SHA `cd9226db4e6c28942df70c22c0475d91fdd62cba5f100baae2d65af57cabb610`，前后身份及两次原生样本一致。未通过截图确认状态，未启动CK3。

联网期间本机又产生8,388份CK3旧订阅临时下载载荷。沿用户已授予的全部本机CK3载荷删除范围，在确认离线、原生独占重验并排除控制／0B／ACL备份和新目标后，9批实际释放21,472,069,880B、0拒绝，订阅及ACF保持。`workshop-recreated-payload-cleanup-a01/ACTUAL.actual.json`为4,068B，SHA `7fc24a7084bb328bc9ad8a7f78a92144d6336eea989b4618d3a935f1f6ec6396`。这不重复计算首次38.3GB，也不按卷free差额给项目quota退款。

后继仅继续必要CI修复、公共缓存runtime准备及下载阻断分析；a07源／元数据预算已独立登记，Java已闭场。菜单224MiB尚未准入，只有真正下载完成、逐文件匹配和fresh离线准入后才执行公共菜单加载；不重跑业务矩阵。

## 云端测试进程故障的本地修复

长路径修复后的云run40174667186已经检出并执行23tests，其中22通过、1失败：CanonicalReleaseTest的临时Git命令30秒超时，旧helper先等待退出再读输出，可能产生管道互等，且超时未回收子进程。未保留到导致填管道的具体Git警告，因此根因机制仍作推断。最小修复只改测试helper：并发有界读取、原30秒期限、64KiB上限和finally中的杀进程／等待／join；新增32KiB成功与65,537字节拒绝回归。

同机默认mvn3.10.0、原Maven home实读为`C:/apache-maven-3.9.16`（事实记录，不作为执行命令）。一次完整`mvn --batch-mode --no-transfer-progress -f mod_religious_ritual_fusion/tools/pom.xml verify`原wait0，24tests全部通过／0skip，26.544秒。`publication-ci-fix-verification-a01/HANDOFF.actual.json`为3,961B，SHA `3c56be3b5626614a4ac47ad372544f7c7bc0bf2d1ab473dc56b3733c73faa8cd`。14份production源、187,192B appJar及75个发布文件均与publish1/a03相同；未重建正式包或移动tag。后继云结果仍以实际run为准。

09:01:18Z同机对规范公开URL正常GET获得HTTP200，右侧Compatible Version实际为完整 `1.20 'Crozier'`；原HTML69,680B，SHA `b74274836f9bb6b97e945548260466dbd28c5b3daf783a7de5fb2f50c93996f2`。此前429保留为历史，不再阻断公开页面核对。

## 公共缓存runtime生产路径修复

实际公共Selection支持全局workshop_cache，而旧builder只检索产品局部case；后继在同一生产路径消费Selection全局case。原只读能力严格绑定source-index、原TU、snapshot SHA和实际host注册；两个前端能力还必须有原两项ON标志，未借此授予实际游戏资格。

同机完整七条既有CI命令169tests零失败、零跳过及完整相关静态检查退出0。原件 publication-a01/workshop-cache-runtime-fix-a01/successor-a06/HANDOFF.actual.json：3866B，SHA `2d25478bb0100f642f67e99d903c6d5c5c14cc0bc384dcca0ad7fb8f8f096864`。只改现有builder和对应回归；未启动游戏、未编DLL或复制SDK，未声称实际缓存加载通过。

## 当前公开状态与缓存缺口（09:06Z）

机器 `4-8e1c2f1861`：09:06:18Z再次后台探针确认Steam offline，PID26192及源码身份不变；CK3进程0，目标Steam cache目录仍不存在。正式条目已公开，完整说明和Notes、封面、六张实机图及兼容右栏已逐项回读，不重复上传。

[官方RRF静态CI40179069224](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40179069224)绑定master `de1747bef1cc4a7222f4f7aa5898a71fa97a0537`，09:05:01Z实际SUCCESS，24tests／0failure／0error／0skip，Maven31.395s。云runner稳定machine_id未观察，记unknown；其独立mvn3.10.0和JDK21读回只证明该job。原件根 `C:/workspace/rrf-development-20261024/publication-ci-de1747-a01/`，HANDOFF2764B、SHA `329767440e1fd6d0375ec59a6c877c4a8ccfe89a9c75bd394a03c58c67741b85`。未以云端编译或软件测试代替缓存或业务通过。

缓存恢复仅做只读分析：公共UGC021接口实际读取84订阅、84启用、0本地禁用，没有调用setter。Valve仅承诺[SetItemsDisabledLocally](https://partner.steamgames.com/doc/api/ISteamUGC#SetItemsDisabledLocally)会从默认枚举排除item，不能据此证明全app校验不会写入。95个旧ID的临时guard方案没有已资格的完整恢复流程，也不能限制Steam其他路径写入；本轮未实施guard、rename、ACL或ACF改动，未退订。

按旧ACF79,314,180,936B的保守可能峰值、新鲜free126,795,399,168B及统一固定预留，缺口至少41,345,575,342B；不能拿历史Native量代替该峰值，也不降低系统或其他任务预留。原只读容量回执 `publication-a01/OLD-DOWNLOAD-79GB-CAPACITY.READONLY.actual.json` 保留。因此本轮结束网络实验，真实下载、逐文件缓存一致及CK3菜单加载均保持待完成。后续须取得可靠选择性下载隔离或满足真实峰值预算，沿同一已发布条目继续；不用staging覆盖cache，不重测功能矩阵。

09:08Z，对de1747实际执行来源producer PID11584、原wait0，随后公共qualify_native退出0。835份production源、d13原编译身份及原DLL均保留；host77和cache-runtime169回归只继承精确同源字节，保留原执行身份，未重跑或外推实机。交接 `publication-a01/inactive-cmake-final-de1747b-a01/HANDOFF.actual.json` 为4,872B，SHA `6610d1bdb2b7741a133f9d28b11ca7b2a4599cfa4dcc3dcb60da98ae626b2210`。未构建runtime或启动游戏；后继doc提交不被追认为该次资格的源码身份。

09:09:50Z再次按原formal manifest逐一核对a03：75文件、1,083,422B，精确清单、大小、SHA全同；源码和staging内层descriptor仍无remote ID，用户外层保留唯一ID并指向a03。`publication-a01/FORMAL-STAGE.final-unchanged.actual.json` 保存该读回；这次核对对象是正式staging，未冒充Steam实际下载缓存。
