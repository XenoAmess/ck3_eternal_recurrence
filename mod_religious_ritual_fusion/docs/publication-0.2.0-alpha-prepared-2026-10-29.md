# 0.2.0 Alpha发布准备：补验通过，正式包与网络阶段未执行

`machine_id: 4-8e1c2f1861`；2026-10-29 UTC。目标只更新[既有Workshop3826756673](https://steamcommunity.com/sharedfiles/filedetails/?id=3826756673)。已公开历史版本仍为0.1.0-alpha；正式0.2 canonical stage／tag／manifest仍PENDING；四张新补验JPEG已经本地生成，尚未上传、下载或执行缓存加载。

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

## 后续执行范围

新的64MiB独立离线准备G已于2026-10-29T18:24:13Z由CAS373→374实际采用：`C:/workspace/rrf-development-20261024/publication-0.2.0-alpha-publish1-a01/metadata/admission-a01/G.json`9020B，SHA`3f7b1d5c4b617ce07cb996d0cf115556ab7f3ffb9ffe747f2c7d9b5fdd505cf6`，截止20:00Z。只准现有合格Java JAR离线正式封包、四图有限编解码、metadata和限定docs／workshop／README git；不准Steam online／下载／发布、Game、SCREEN、Maven或新生产编译。G的source_commit是admission base，不能据它冒称正式发布输入。

本轮文档已在该G下采用；canonical stage／tag／manifest仍PENDING。Root须先完成clean文档提交，再基于真实最终源码执行既有正式builder并记录manifest；正式tag创建只在Root clean commit之后执行。本岗没有commit、push、构建、网络或CAS。

当前没有已合格的低峰值选择性在线命令。保持三项策略和订阅不变时，可继续离线准备，另机路线须逐机新鲜身份与容量核验；若选择在本机恢复整个旧队列，需用户逐项明确改变三项永久禁回装偏好并给出获准容量／回收范围。单纯“重试”不授权改DACL、ACF、退订或disabled setter，额外许可也不能替代缺少的隔离证据。

实际网络操作与cache闭环仍待独立解决，不以补验、正式包生成或上传成功相互替代。原0.1公开／失败缓存及各旧场次保持原文；后续事实发生后再追加，不覆盖旧原件。


### 准备期原失败与采用（非生产／业务失败）

首次close/prep b02脚本原exit1：CAS prepare要求10个exact guards，超过max8；已生成闭场扫描及同一G，但当时H仍373，未prepare／publish CAS。Root随后通过C19 `metadata/adopt-prepared-publication-G.once.py`复核原H、同一扫描／G及闭写来源，以8个exact guards仅commit恢复，原wait0，实际373→374；没有重扫、Game、新save或网络重放。原失败与采用分别保留，不能概称所有准备命令都原0，也不记为生产／业务失败。采用回执为C19 `metadata/close-R58-and-admit-publication-prep-a01/CAS.actual.json`，SHA`e46e080d4a81636e6524fc77e256f31cbfc1c5ab5ac140c91c3e73b85109e692`。


### 四图实际离线编码

Root于18:25:50Z完成两Java进程序列，原Popen4248／9340均wait0；原PNG前后SHA校验一致。四JPEG均2560×1440、每份<1MiB，仅ImageIO0.90格式编码，无裁切／缩放／像素修改，仍未公开。回执`C:/workspace/rrf-development-20261024/publication-0.2.0-alpha-publish1-a01/metadata/media-export-a01/MEDIA-EXPORT.actual.json`4923B，SHA`90e3e51c819d1b1ea58f31014c3d243828c881a0a49b0616e6565a5420067a59`；各文件名／字节／SHA见[截图索引](../../workshop/religious_ritual_fusion_screenshots.md)。没有复制JPEG进仓库。正式canonical stage／tag／manifest仍PENDING，编码成功不授公开或缓存加载资格。
