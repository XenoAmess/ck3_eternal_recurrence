# 0.2.0 Alpha：离线正式封包完成，网络发布仍受阻

> **后继事实，2026-10-29 19:42Z起**：用户明确继续本机、取消额外预算缺口门槛并授权清理无关Mod后，0.2内容与四图已实际公开提交；真实Steam下载及90文件精确校验已通过，菜单加载仍在修复入口后验收。见[实际发布记录](publication-0.2.0-alpha-2026-10-29.md)。以下保留离线准备时的观察和判断，不再作为当前发布状态或额外容量门槛。

`machine_id: 4-8e1c2f1861`；2026-10-29 UTC。目标只更新[既有Workshop3826756673](https://steamcommunity.com/sharedfiles/filedetails/?id=3826756673)。最后匿名核实的公开版本为0.1.0-alpha（10月29日约01:50Z）；本轮未提交更新。0.2正式canonical stage已于18:32:09Z完成并独立verify，annotated tag固定于封包来源`b31664ba659f5a20a188527719367c831734b8c1`；四张新补验JPEG已本地生成并由Root逐张查看。新内容与四新图均未上传／公开，缓存验收NOTRUN，Steam仍离线。

## 文案及业务依据

完整玩家说明见[canonical BBCode](../../workshop/religious_ritual_fusion_description.bbcode)，完整Notes见[0.2 Notes](../../workshop/religious_ritual_fusion_notes_0.2.0.bbcode)，技术边界及后续发布身份见[永久changelog](../../docs/release-changelogs/religious-ritual-fusion/0.2.0.md)。现有封面和15图没有重新生成；[截图说明](../../workshop/religious_ritual_fusion_screenshots.md)新增四张本地合格PNG及Root实际导出的四张JPEG身份，均未称已公开。

[R0057五项UI补验、R0058三项冷载补验](live-review-resume-2026-10-29.md)已各自正常通过。历史12项／20项完整矩阵incomplete不变，SDK continuation、county宗教地图实际颜色和真实Steam缓存闭环仍有缺口。玩家文案使用补验范围和已知限制，不暴露运行器退出码或内部错误码。

R0058实际来源`7bcbc067656d0a090bbb8fe6559f805e482e2a84`；不是正式发布内容commit。18:10:33.426334Z新鲜后台Steam探针`status=offline, offline_mode=true`，Steam PID7032／出生FILETIME`134376848388036198`，11.15.70.27；回执为C19 `metadata/R58-postclose-Steam-offline.actual.json`。这个历史离线观察不授未来online或Game资格。

## Steam与容量的具体阻断

只读审计原件根：`C:/workspace/rrf-development-20261024/review-fixes-a01/shared-unrun-recovery-b01/metadata/publication-preflight-candidate-a01`。`CANDIDATE.actual.json`9550B，SHA`e1044a681d2282fd0a9e71f7bd979749882f081e6cedab5d433642198144d80e`；闭证3033B，SHA`629ae7f50e1899e4466843b2aa1d9f5f16c360d458a3f8a341a6d28cbcb2c56d`。审计没有改变Steam状态。

当前本机注册表与libraryfolders定位库为`C:/Program Files (x86)/Steam`。本机`C:/ProgramData/CK3WorkshopLocalPolicy/blocked-items.json`仅含2291024373、2993056101、2962333032三项，持续至明确撤销；不能套用另一机器五项偏好。三个item在content、downloads及两种temp路径共12处的当前DACL仍有拒写／删除ACE，立即子项只有策略marker，未改权限。

当前`steamapps/workshop/appworkshop_1158310.acf`仍有91条Installed、85条Details，size求和79,314,180,936B，NeedsUpdate／NeedsDownload均1；目标3826756673没有Installed，content不存在而downloads有旧暂存。appmanifest另列BytesToStage79,315,194,954、BytesToDownload31,369,396,944，进度0。它们是当前读取的本地持久计划，不是远端最新订阅证明或未来分配硬上界，不能当成现有实际占用，也不能直接取消该风险。

采集时卷free120,125,161,472B；保持该metadata G的90,916,396,646B预留作比较，增列79,315,194,954B暂存风险后示意缺口50,106,430,128B，尚未计新包与其他临时输出。这不是新网络admission。未来网络阶段必须重新检查实际卷、并发和系统预留、owned／gross／quota及期限，不能沿用旧41GB缺口或仅按小模组包放行。

现共享下载器的高优先级DownloadItem只为指定请求和目标回调／安装路径提供守卫，没有总写入cap。旧临时SuspendDownloads仅有void ACK和pause／resume序列，未证明“暂停全部后只放行目标”或上线前时间窗隔离。10月25日两次真实指定下载仍因2993056101预分配拒写连带失败；当前根因没有消失证据。官方文档及当前源码pins在上述审计中，不在本任务重复联网研究。

## 已完成的离线正式封包与后续边界

新的64MiB独立离线准备G已于2026-10-29T18:24:13Z由CAS373→374实际采用：`C:/workspace/rrf-development-20261024/publication-0.2.0-alpha-publish1-a01/metadata/admission-a01/G.json`9020B，SHA`3f7b1d5c4b617ce07cb996d0cf115556ab7f3ffb9ffe747f2c7d9b5fdd505cf6`，截止20:00Z。只准现有合格Java JAR离线正式封包、四图有限编解码、metadata和限定docs／workshop／README git；不准Steam online／下载／发布、Game、SCREEN、Maven或新生产编译。G的source_commit是admission base，不能据它冒称正式发布输入。

18:32:09Z的后继实际封包已取代此前文档采用时的canonical／tag／manifest PENDING状态。Root先将八份文档普通提交／push为clean源码`b31664ba659f5a20a188527719367c831734b8c1`（Source A），再由既有合格JAR完成validate／build／verify；正式tag固定绑定同一Source A。本次及以后追加的文档提交仅记录后继事实，不移动tag、不把后继master提交追认为该包来源，也不触发canonical重建。

当前没有已合格的低峰值选择性在线命令。保持三项策略和订阅不变时，可继续离线准备，另机路线须逐机新鲜身份与容量核验；若选择在本机恢复整个旧队列，需用户逐项明确改变三项永久禁回装偏好并给出获准容量／回收范围。单纯“重试”不授权改DACL、ACF、退订或disabled setter，额外许可也不能替代缺少的隔离证据。

实际网络操作与cache闭环仍待独立解决，不以补验、正式包生成或上传成功相互替代。原0.1公开／失败缓存及各旧场次保持原文；后续事实发生后再追加，不覆盖旧原件。


### 准备期原失败与采用（非生产／业务失败）

首次close/prep b02脚本原exit1：CAS prepare要求10个exact guards，超过max8；已生成闭场扫描及同一G，但当时H仍373，未prepare／publish CAS。Root随后通过C19 `metadata/adopt-prepared-publication-G.once.py`复核原H、同一扫描／G及闭写来源，以8个exact guards仅commit恢复，原wait0，实际373→374；没有重扫、Game、新save或网络重放。原失败与采用分别保留，不能概称所有准备命令都原0，也不记为生产／业务失败。采用回执为C19 `metadata/close-R58-and-admit-publication-prep-a01/CAS.actual.json`，SHA`e46e080d4a81636e6524fc77e256f31cbfc1c5ab5ac140c91c3e73b85109e692`。


### 四图实际离线编码

Root于18:25:50Z完成两Java进程序列，原Popen4248／9340均wait0；原PNG前后SHA校验一致。四JPEG均2560×1440、每份<1MiB，仅ImageIO0.90格式编码，无裁切／缩放／像素修改，仍未公开。回执`C:/workspace/rrf-development-20261024/publication-0.2.0-alpha-publish1-a01/metadata/media-export-a01/MEDIA-EXPORT.actual.json`4923B，SHA`90e3e51c819d1b1ea58f31014c3d243828c881a0a49b0616e6565a5420067a59`；各文件名／字节／SHA见[截图索引](../../workshop/religious_ritual_fusion_screenshots.md)。没有复制JPEG进仓库。正式canonical stage／tag／manifest已由下述18:32后继事实完成；图片编码和正式封包均不授公开或缓存加载资格。


### 正式包、tag及原始CLI终态

NEWPUB=`C:/workspace/rrf-development-20261024/publication-0.2.0-alpha-publish1-a01`。`canonical-staging`为90文件，**manifest逐项size实际求和1,289,918B**；`canonical-staging.manifest.json`17020B，SHA`3ce7412e8bbaefca8efdd9ed465b398496955ccb603afdd1e75840715280b808`。manifest的git_sha及build实际revision均为Source A，不是后续事实记录提交。

annotated tag `religious-ritual-fusion-v0.2.0-alpha-publish1`已创建并普通push；Root实际远端读回tag object`de305138b17238ef3804cd98894c4b832688dff1`、peeled`b31664ba659f5a20a188527719367c831734b8c1`，旧tags未移动。本次文档步骤仅只读核对本地同值，不重新联网查询远端。

| 既有JAR原始命令 | 原PID／原wait／耗时 |
| --- | --- |
| validate | 16288／0／1.566s |
| build | 3544／0／2.080s |
| verify | 4152／0／1.476s |

外层Root工具0；没有Maven或Native编译，55项Java图及module JAR前后完全相同。原件`metadata/formal-build-a01/FORMAL-STAGE.actual.json`5614B，SHA`c88efa8e574a1e38fd03461a6fc4ecc4c3ff143b6fd750519fcd9079f9ca5af7`。既有236项产品回归和131项共享恢复修复回归继续引用原执行及原来源身份；本阶段只有文档及既有CLI，没有重跑测试或新增测试通过数。

内层descriptor已读回不含remote_file_id。用户目录外层.mod本阶段没有修改，仍使用既有公开版本；本地正式staging不等于已注册0.2、真实Steam缓存或菜单加载。

### 完整payload仅离线解析，尚无网络准入

Root已冻结完整标题／说明／Notes，并实际调用现生产`steam_native._load_plan`：没有初始化DLL／Steam API、没有联网。`metadata/PUBLISH-PAYLOAD-OFFLINE-VALIDATION.actual.json`5092B，SHA`b0bdbeeeadba742246dbef1b155f14a480640557290bc0659e32c9bbc5cec973`。完整冻结字段分别63／5209／3367B、均<8000B；字段来源与frozen-copy原字节相等，精确SHA在该原件中。

`content-update.NOT-ADMITTED.plan.json`4166B，SHA`8e72dba737db38917d2d7a64efc069860145a93c3f3cbc2615ffe2616a2c74e2`；生产解析payload SHA`0c435a7983edd5ac82d4899bdc1e33a19b46ceb448c54ea648777a60b440cd8a`，operation=update、唯一目标3826756673、App1158310、public visibility0，解析后完整tags为Religion／Gameplay／1.20 'Crozier'。该plan仅content与完整metadata，没有append预览动作，未调用publish。

`media-append.inputs.NOT-ADMITTED.json`只有四图输入，不是append计划；必须未来获准联网后取得`workshop_native_previews`新鲜完整当前顺序snapshot，才能生成真实append操作。历史15图不能构造当前snapshot。Root已查看全部四个最终JPEG，均全幅2560×1440、文字可读；它们仍未公开。

离线parser通过、tag push及正式CLI通过均不解除前述Steam容量／DACL阻断。新内容未上传，四新图未公开，下载／逐文件缓存／菜单加载均NOTRUN；历史业务incomplete、SDK续行与county地图颜色缺口不变。后续只追加实际发生的网络回执，不把本次文档提交当作另一份包来源。
