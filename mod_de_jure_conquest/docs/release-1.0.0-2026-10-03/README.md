# 公国／王国／帝国法理征服（XenoAmess维护版） 1.0.0 发布报告

2026-10-03 已创建并公开发布新的[维护版物品 3812510217](https://steamcommunity.com/sharedfiles/filedetails/?id=3812510217)。上游 `3600021457` 仅作来源，从未作为上传目标。此版本为 initial baseline，无上一维护版版本、tag 或 commit。

源码为 `dc53f4a183d4a753c0c5eeb3623f7f060b59f231`，正式 tag 为 `de-jure-conquest-v1.0.0`，两者已推送。实机游戏为 CK3 1.20.0.3／Steam build 25652598；`1.20.*` 只表示兼容声明，不能外推为整个系列均已实测。正式 16 文件 staging、ZIP 与最终中文实机运行字节一致，文档、工具和夹具均未上传，内层 descriptor 无 `remote_file_id`。带新物品ID的manifest SHA-256为 `13d586066e50edf97359db08b264fe72ee5afb0c099aa730d06ebe8c4677237a`，ZIP SHA-256为 `8ed44c081ff53f54e6d267c35425da9e7ec3cd976f7476b7faf7936d1d6b87f1`。完整构建绑定见 [id-bound-build.json](id-bound-build.json)。

中文普通公国宣战、实际费用与次级防守者、新战争保存重载通过；三档胜利／白和平／战败九格共72项综合语义断言通过。 完整实机边界见[中文验收报告](../cn-live-acceptance-2026-10-03.md)。**实机仅验简体中文；其他八语仅格式、编码、键和受保护占位符检查。** 精确源码的[官方CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37117295585)与[独立维护Mod CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37117295549)均为success。

原生CreateItem与首次SubmitItemUpdate、随后的一张中文玩法图上传均返回 `EResult=1`。图片已按原生index0/type0核对，CDN下载字节／像素与上传JPEG相同，并直接审阅下载图片；匿名物品HTML引用同一媒体。原生媒体提交虽然成功，公开Change Notes仍停留在A，故通过离线Steam客户端的登录态作者页编辑**原有条目** `1791025832`：精确字段 `change_description` 经ValuePattern设值，等待异步刷新并回读全文后调用保存，没有键盘或坐标输入。未创建第三个物品或新版本。

匿名[公开更新说明](https://steamcommunity.com/sharedfiles/filedetails/changelog/3812510217)回读证明同一条目由A替换为完整[冻结B文本](change-notes-B.txt)：HTML解码与换行归一化后 1393 字符／34 行，SHA-256 `A73B35C633D4AF7D6B9A84597D9CA28D17AC992BDD3128F671D6A178C7CF0057`。首次A的全文回读与后续HTTP429、未改变页面、UIA即时缓存未刷新等失败attempt全部保留。见[最终公开回读](anonymous-public-B-verification.json)、[原始匿名HTML](anonymous-public-B-changelog.html)、[作者保存回执](owner-notes-save-receipt.json)。B仅比A增加该版本一张中文实机图说明，运行文件不变。

真实SubscribeItem回调1313和DownloadItem回调3406均对应新ID、AppID1158310并返回1。首次自动下载缓存先安全保留到外置目录，证明canonical缓存路径不存在后再请求全新下载；最终state=5，subscribed/installed为真，needs_update/downloading/download_pending均为假。canonical缓存的 16 文件已与正式manifest逐文件比对通过，未从仓库复制制造缓存；**未另开缓存游戏会话**，中文验收关联通过精确运行字节一致性成立。详见[缓存复核](fresh-cache-verification.json)。

原生网络工作结束后已恢复Steam离线。作者编辑期间继续保持离线；结束后再次用窗口位移取得新桌面像素，直接审阅2026-10-03 19:49画面的“离线模式”，CK3／启动器进程均为零，屏幕任务经精确CAS释放。见[离线审阅](steam-offline-root-review.json)与[释放收据](screen-lease-release.json)。

已知限制：仅支持玩家进攻。与上游公开CB ID相同，原作和维护版只能启用其一。建议用于新战争；本轮保存重载限于新宣战公国战争。未独立验收旧版大圣战迁移、自动军队、并发战争、原生议和按钮或多人真人赔款。最终结算证据链仍有93条动态文本格式诊断、来源未定位，并保留原版加载／旅行诊断；不宣称日志零错误。

本报告及[全量证据索引](report.json)、[永久仓库changelog](../../../docs/release-changelogs/de-jure-conquest/1.0.0.md)随发布记录提交并推送master；不移动已发布源码tag。外置证据根为 `C:/workspace/two-mod-maintenance-20261003`，失败记录与过程素材永久保留。
