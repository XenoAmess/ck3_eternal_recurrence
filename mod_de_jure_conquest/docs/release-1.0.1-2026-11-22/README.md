# 1.0.1 Florin 发布记录与验收范围

本轮目标为 CK3 1.21.0.3 Florin／26785313，仅简体中文真实游戏验收，其他八语保留格式、键与占位符检查。当前正式发布、真实下载和完整公开回读均已完成并恢复离线；独立无fixture缓存游戏加载及正常退出也已完成。原作者白绮、原作来源3600021457与维护canonical3812510217不变；旧1.0.0标签及历史报告不改。

## 当前通过范围

- 当前16文件路径、大小、SHA与已接受a96清单一致；本次五份玩法脚本、九语和缩略图没有新改，descriptor版本与兼容元数据相对1.0.0更新。
- 普通公国真实宣战、战争目标与双防守者、S0/S1物理保存资源和独立第三次冷载匹配。实际保存差额0金币／50威望／300虔诚。
- 三档官方借口费用为威望／虔诚50／200、250／1000、1250／5000；帝国纯只读重复同值。另一次同S0来源进程的公国取价50／200加S0实际原版附加100与保存差额相符，不冒同一宣战事务内预览，也不把它称本地化文本渲染。
- 九个独立场覆盖公国／王国／帝国与胜利／白和平／战败，每场原8项各一次，严格聚合72/72、无缺格／重复格／重复物理log或contract。九场同生产16文件及同夹具producer；不拼接旧partial。
- 最后帝国胜利场6次各+24到.21，独立最终Core核后正常退出0／Job0／cleanup，0SAVE。受限事件处理的资格单独记录，不扩展为任意事件控制或其他业务通过。

## 保留的范围与失败

矩阵通过测试场景触发生产战争借口及原生结算；普通GUI宣战、实际扣款、保存重载是另外的有限实证。九格不代替原生议和按钮、死亡、旧大圣战存档迁移、自动军队、独立并发战争或多人真人赔款未完成的验收；不额外加全13或17模组新门，也不将历史规划全部写成完成。

原串行10/24失败、三个partial、旧未知操作与原期限、普通宣战工具等待警告失败、保存ACK与独立物理证据的有限边界均保原。原stock／地图／旅行／portrait等诊断和未定位动态文本格式信息不删除、不声称全error.log干净，不把新成功回写旧失败。详细机器原件留D并在紧凑维护索引中引用，不把大raw日志上传到发布包。

正式16文件tag构建／verify、唯一canonical更新、完整标题／说明／Change Notes回读、真实16文件下载、独立无fixture缓存场和最终Steam离线分别取证。上传回执本身不等于完整交付。预览图和原图库保持，语言与以上限制继续公开。


## 实际发布与原件索引

SourceA为`4dcd897f9793d15119b662f6970d51253e75b1e6`，正式标签`de-jure-conquest-v1.0.1`不移动；构建／verify均0，16文件path／size／SHA与已验收a96清单完全一致。正式manifest SHA为`05158c288007c829c2efcd1e818a69e11bafcca3d1115937b5468dcdf508dc22`，ZIP为`748ff56dd6bd46bc0af27c644449e58ad7c4f2635611ab6e1218a34200c7f6f5`。

维护canonical3812510217于2026-11-21T22:03:04.717634Z一次更新成功EResult1，operation `djc-101-canonical3812510217-a373`；SDK实际下载16文件全精确、原图库保持。完整公开标题／说明／Notes与粗体格式回读通过，entry1795298605。真实在线窗口59.5971196秒，22:03:41.497170Z新鲜离线证明独立保留；没有把脚本整体耗时写成在线时长。

原件位于`D:/ck3-state/upgrade-20261118/`：`djc-final-release-a373/formal-delivery-final.json`（7140B，SHA0d7c9403f53759d98f6fb21dd6b903e39d6bae1b3b3685829c55dd24356ed698）；同目录原发布回执629B／c42a8a3c395e8108c3be2763aee423878890f4cbe77c953af1cceb5f2c89e9d8；`djc-publication-a373/operator-a312/djc-download-exact.json`715B／4b66239644138aeb6dfc1ead475544909d190f655648613eacdc96570f14691e；`djc-public-readback-a375/actual-readback-a376/verification.json`4696B／1be4c1afc81155aa19c37771e202fcd98d5d22be279c61f193ddd4b8b080ea4a。原网页、大日志和存档不复制入库；紧凑机器索引见`docs/maintenance/evidence/.../djc-101-publication-actual-a373.json`。

独立无fixture缓存场a374已完成真实游戏加载与正常退出：只挂载实际C cache3812510217的16文件，paused／map／alive Robert36423／.15；原creator5600、Game23568于22:18:04.570560Z独立Natural0／Job0／CLEANUP_PROVEN，0Date／0SAVE及源输入保持。早a378 Core未就绪拒绝保留，a379是真实Core，a380一次退出；raw normal_exit_confirmed=false与独立Natural0证据分列。此有限缓存场不授whole-product／全SDK资格。旧公开读取路径比较preflight拒绝及全部历史失败保持，不补造重试成功。


## 最终缓存签收与存储纠正

最终机器交付索引见`D:/ck3-state/upgrade-20261118/djc-final-delivery-a381/djc-final-delivery-envelope.json`（1689B，SHA814dfe97187656d07af0e06b0457dedbcd28efde045fda74ba33133cbc3f3294）；原finalindex8763B／f9efc4c0dcf95fc220de12ffbab53a574cda613a4f5f2a1cc2124ecfe600fcee和缓存closure29490B／cfd1b9a2956dbd0187f7ff9cbc18e9f135539e1bfca647383694e819e18b7467均不回写。

必须保留真实预算偏差：原发布32MiB阶段端点实际分配下界60,517,696B，比33,554,432B超26,963,264B；约23MB逻辑大小不能代替allocation。两张tmp分配59,650,048B，后经Root精确RestartManager和birth／TEMP证据确认属于本次Steam WebHelper20972／21984，非CK3或新XQOL。Root正常离线关闭旧Steam后两临时文件自行消失，现不可读；没有手工删除／移动，不把全卷free变化全归此动作。

Root随后仅以子进程环境将离线Steam的TEMP／TMP改到独立D目录`steam-offline-client-temp-a383`，恢复新鲜offline；新128MiB是按已观察60.5MB约两倍估计的独立后台临时阶段，非硬文件系统cap、非事后补造原32许可，不改全局环境或C批量输出。原formal operator及cache1GiB future0，Steam后台128与Root36／新XQOL仍各自开放，旧held／超限观察不退不抹。后续发布wrapper的finally offline restart须显式沿独立已准入child TEMP／TMP，不再继承publication32/tmp；原helper不热改。紧凑纠正索引见维护目录`djc-101-final-cache-storage-correction-a381.json`。
