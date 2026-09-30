# Episode 02：a04 完整六章审片版

本次从固定 `ie` 基线 `d5f3c51215439b23f578c8973d5d74ac01f1493c` 独立制作。期间没有 fetch、merge、rebase，也没有接收 master 或后续 ie 的代码。未操作 Steam、CK3、桌面或录制；Steam 离线规则继续有效。

## 内容与实际时长

按原六章顺序恢复完整解释；最终中文配音为 Edge TTS `zh-CN-XiaoxiaoNeural`、`-5%`，含167句和对应英文字幕。每句有画面用途，章尾不加无声独读停留。

| 章节 | 句数 | 实际旁白秒数 |
| --- | ---: | ---: |
| opening：人物、目标、真实接战钩子 | 10 | 105.700 |
| pursuit：两份预算、逐团余数、三次跨日 | 30 | 365.200 |
| knights：致残、选择器、死亡与名单写回 | 38 | 415.567 |
| reinforcement：条目、缓存、定点数与历史战宽 | 42 | 462.067 |
| terminal：损失分子、996分母、系数与封顶 | 37 | 369.267 |
| closing：四类变化与界面观察顺序 | 10 | 100.833 |
| 合计 | 167 | **1818.633（30:18.633）** |

真实1288对330接战截图在开头展示，首句实际6.900秒，首两句18.133秒交代罗贝尔、阿里、争夺塞尔古塞与墨西拿战场。片头与结尾去掉重复预告，四个机制章保留全部核实的推导。

## 画面与来源

167幅逐句画板全部保留真实界面原像素的全图定位、框选和局部放大，并将原生字段与复算图分开标示。成片还包含13个带旁白的原速实录片段。没有循环或慢放原片，没有用静音填足时长。

原始接战、A05后段追击／终局、A01增援、当前a08名单及a02阵亡实录各自注明来源。历史039→040、020、070、036→038没有留存对应原UI；画面明确写“历史原生记录／原UI未留存”，当前UI仅作独立例。没有把这些回放剪成已经证明的单次因果链。

本次完整事实包绑定六章167句与新增机制解释，保留非零掩护、其他人物事件、未来增援、主动撤退与通用胜率的未证边界。UI人数与原生current、软硬伤、缓存、战宽及战争分数分母保持各自口径。终局536.62042人当量是计分分子；与可读参战者硬伤526.62042的差10来自非主战条目，硬伤未提供，不能称10人死亡。

## 固定输入与复用实现

- 最终故事：`project/review-story-a04-v2.json`，SHA-256 `697EDD37D55DFC6F11BD5B7FCF4DDFD8A28D4342A66010A772932C08B3F96378`。
- 原始六章盘点：外置 `episode02-a04-production/input-inventory-a02.json`，SHA-256 `773FD65D6D5A445C447CB594E70072F8B156A5E4720E61E7751CF6E98379BB13`。原稿Draft451、六条旧MP3的实测身份及旧时间轴均冻结保留。
- 当前ProjectConfig：`project/review-story-a04-project.json`，精确配置快照由原生 `start-run` 创建。
- 最终画板意图：`project/review-story-a04-board-specs-v2.json`；最终剪辑：`project/review-story-a04-edit-v2.json`。首版意图也保留。
- 项目composer：`review_story_a04.py`。严格要求六章原顺序与实际旁白1620–1920秒后才允许编码；TTS并发16，章节并发6，每次编码最多8句以控制解码输入数。
- 图板composer：`compose_review_boards_a04.py`，只使用原图、裁切、文字与矩形，不生成游戏UI。
- 已执行的外置操作脚本冻结投影到 `support-a04/`，其中路径是本次固定机器的复现坐标；开始新run必须重新选新外置目录，不得覆盖既有路径。

每次新run实际查询独立工具仓库最新正式Release；本次为 `xar-promo-toolchain 0.2.1`，wheel SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`。显式解释器为 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，Python3.14.7／edge-tts7.2.8／Pillow12.3.0／FFmpeg9.0.1。C工作树没有相对venv，主venv已验证，未回退裸Python。

## 实物、审计与签核范围

最终实物 `C:/Users/1/AppData/Local/ck3-review-render/episode02-review-20260930-a04-a04/CK3-War-AI-Episode02-Review-20260930-a04.mp4` 为240710781字节，SHA-256 `CB141C63966D86BDC8E267B4D958A79C1BB06A8EF69814DC0D6788F0345B8C7E`。

独立实际ffprobe给出1920×1080、30fps、H.264／AAC48kHz双声道、六个章节、视频1818.633333秒、音频1818.654667秒。最终字节执行一次新全片AV解码54,559帧，RC0；一次新全片音轨检测在-40dB、连续至少2秒条件下无静音区间。最终机器报告保留在 `C:/Users/1/ck3-a04-machine-audit-20260930/attempt-02/report.json`，147029字节，SHA-256 `FE2A6F77FE6883FF0820BAB360C22CE80A7920E264A13944DC1D3060F663BD0D`。

首次完整编码1D787版本经root实际帧检查发现P1：讲结算后−50%时，大幅裁切使用结算前0%。该版本保全且没有交付。新attempt将t031和同类c004的主放大换成同次a2-480真实结算后−50%，只重编码两段，22段逐字节核对后复制复用，完成六章新拼接；167句配音、时码及24个ASS字节全部一致。新attempt的实际执行入口与源冻结为 `support-a04/partial_render_a04.py`。

最终产品局部报告为 `C:/Users/1/ck3-a04-independent-review-20260930/attempt-03/actual-product-review.json`，7411字节，SHA-256 `148446BD77C3ED45F1A25AB137E8800993871237FA20247F204EA38DC61D14B5`，结论 `PASS_PENDING_HUMAN_REVIEW`。首次14帧检查只保留其原字节范围；修正版另提取t031和c004两张实际成片帧，主−50%/剑形分项与正文一致。新两帧manifest SHA-256 `3506986951D7262CE3D8F8209F0D2ADFE32631D10719516609B80DDD736C437C`，仅绑定最终CB141字节，没有将旧帧冒作新成片证据。

原始TTS请求、成功／失败响应、中英文字幕、所有图、24个chunk、六章编码、concat、命令argv/stdout/stderr、probe及报告永久保留。失败输入attempt与首轮放大不足的图板attempt也保留。原生公共API用于不可变保全与记录实际外置composition；不声称运行了未执行的CLI build或CLI audit。

原生保全完成回执位于最终run的 `native-preservation-complete.json`，71023字节，SHA-256 `5B9861947E1139E92B965B8DE554FC78C12BDFCBCF78A61A32639F325D1B6201`；其绑定 `native-run/run-manifest.json`，43847字节，SHA-256 `1C0A8303422444EA42B84D104403C5342D10E2E58F768A8082ACDBD89483D20B`。配置、最终媒体、机器与产品回执、实际帧及过程索引通过公共API不可变保全，signoffs数组为空。

独立机器核验与必要的局部视觉修正复核已经通过。按持续授权仅将同名a04单MP4复制到 `C:/Users/1/OneDrive/CK3-War-AI-20260923/CK3-War-AI-Episode02-Review-20260930-a04.mp4`。2026-09-30北京时间21:30:33实际Cloud Files客户端状态为InSync，9/9检查通过，源文件、复制流与目标全量SHA-256均为上述CB141字节。最终交付回执为 `C:/Users/1/AppData/Local/ck3-review-render/episode02-delivery-20260930-a04/delivery-final-20260930T133049317282Z.json`，3612字节，SHA-256 `A3795B800618B1DBC99646016606F61CAE5A84DC12E10ECA05FE6844FC363F0A`。旧1D787版本没有复制，a02、a03及全部素材保留；客户端同步元数据不是独立远端回读。

完整人工1×审片、听感、原片clean span与signoff仍待真人执行；任何自动PASS或客户端InSync均不替代这些事项。
