# 超人强宣传片修订版交付

[修订版视频](C:/Users/1/OneDrive/CK3-War-AI-20260923/超人强_越超人越强_宣传片_修订版_20261004_2d880ce2.mp4) 已通过 OneDrive 桌面客户端同步。影片 **2分18.688秒、1920×1080/30fps、31,431,220字节**，SHA-256 `2d880ce2df313d2c9cdc343208e5d21aea16963654696718c8ca4e9055eeaf82`。

用户提出的三项修订已经落到实际影片：前五场使用皇家书房、多人舞会、室外练武、王冠邀请静物、独立女王五张新图；全部删除源类别浅白角标；字幕由31条短句改为10场各一段完整旁白，均为两行，持续显示至场尾。晓晓声线和用户提供的唯一Suno音乐保留。

2026-10-04 18:08:43北京时间，OneDrive客户端报告InSync=1、validated=全部31,431,220字节、modified=0。只上传这一份修订MP4。随后对该副本执行18项检查，完整音视频解码无错误，实际响度-16.48 LUFS、峰值-2.81 dBTP；再直接查看28张实际成片帧，十段字幕在口播早段与尾段均持续存在，预览占位黑条和场景编号未进入电影。片尾实际视频帧的QR解码到Workshop3812991990。

[制作报告](production-report.json)、[客户端同步回执](delivery-confirmed.json)、[媒体与字幕检查](encoded-media-check.json)、[实际画面观察](actual-frame-quality.json)、[实际片尾QR检查](actual-encoded-qr-check.json)、[过程保全](retention-receipt.json)均绑定精确成片字节。原生review另生成40张帧及pending-human-review包；原生audit的范围为字节绑定与证据完整性，不代替内容判断。

原生run永久保留于 `C:\ck3-superman-qiang-promo-20261004\render-A0004\native-run\run-manifest.json`；914份过程文件的199,466,886字节ZIP已经保全进该run，原始目录仍在。原生验证PASS，146个artifact、零signoff。独立服务器字节回读与人工1×全片观看/听审签核未执行；本次是私有文件交付，没有发布到视频平台。

首版与全部旧原图、31条字幕、旧run、失败plan、原ZIP/WAV、TTS请求和时间标记继续保留。A0003只读plan发现新原图路径漏入绑定清单，原run未改写、没有建build；修正准备脚本后新建A0004，正式原生plan/build成功。当前影片来自A0004，source commit为 `c9e8331d7f20fb9c87e9b5908b0a24079b93c8ba`，正式工具链版本0.2.1及wheel SHA见框架记录。


2026-10-04 补充：用户指出转场音乐卡顿后，新增 packet/sample 检查发现本版实际音轨缺少8.833秒声音。上述18项通过不覆盖声音连续性；原始报告继续保留。修复与新增验收见[音频修复版](../audio-delivery-20261004/README.md)。
