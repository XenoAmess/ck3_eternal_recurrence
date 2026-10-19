# 《CK3：信仰与权力》第一期 V6 本地审阅交付

`machine_id: 4-8e1c2f1861`；2026-10-19T10:42:39Z现有正式生产入口原Popen实际wait0，本地审阅版已生成。状态为 **ENCODED_REVIEW_PENDING**：技术检查通过，完整人工1倍速听看片及人工签收未完成。下列绝对路径只表示本机文件，不授其他机器安装或运行资格。

## 可直接打开的文件

| 文件 | 本机交付 |
| --- | --- |
| 视频 | [episode01-review.mp4](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v6-production-a01/full-final-a01/native-run/derived/direct/episode01-review.mp4) |
| 中文字幕 | [episode01.zh.srt](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v6-production-a01/full-final-a01/native-run/derived/direct/text/episode01.zh.srt) |
| 英文字幕 | [episode01.en.srt](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v6-production-a01/full-final-a01/native-run/derived/direct/text/episode01.en.srt) |
| 双语字幕 | [episode01.bilingual.srt](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v6-production-a01/full-final-a01/native-run/derived/direct/text/episode01.bilingual.srt) |
| 中英讲稿 | [episode01-script.md](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v6-production-a01/full-final-a01/native-run/derived/direct/text/episode01-script.md) |
| 17章时间点 | [episode01.chapters.txt](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v6-production-a01/full-final-a01/native-run/derived/direct/text/episode01.chapters.txt) |
| 机器可读交付索引 | [LOCAL-DELIVERY-a01.json](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v6-20261019/resume-20261019/LOCAL-DELIVERY-a01.json) |

视频145,383,839B，生产者SHA-256 `c1329d56c4ddf4e6017bce33e22fcffc93b90c0a12b2d3cdb4c810d20dc0a819`。2560×1440/H264/30fps、48kHz双声道AAC；135段旁白、460组字幕、17章、76,832个实际视频帧。帧跨度声钟42:41.067，容器实际probe为2561.088021秒；实际首视频PTS为0.021秒。外置字幕及章节均使用最终实际PTS，保留封装起始偏移，未按旧V5或墙钟估算。交付索引中的duration_seconds指76,832帧的跨度。

## 本次实际验证

源码及文档工作包在`ad245ac53de41a2f2e835c6069b803c978873a6c`推送后，现有`formal_episode.py → FormalInputs.inspect → admit_v3 → full_episode.build`沿唯一新输出运行，2workers，2026-10-19T09:58:39Z开始、10:42:39Z原wait0。作者最终a37只合a17＋a29＋a36，正常metadata plan实际0、remaining={}、content_ready=true；135/460/76832声钟未变。沿冻结1440p配置，不把历史4K样板目录名当本次输出规格。

正式链一次完成整片严格AV解码、实际格式/时长、全部视频帧PTS和CFR帧数、135段与图层实际帧映射、字幕/讲稿、音频信号及音乐存在性检查。音量实测mean −22.5dB、max −2.9dB。音乐仍为`quiet-courtly-tension.wav`，旁白0dB/音乐−17dB、loop、淡入2秒/淡出8秒，未另normalize或duck。技术检查不替代完整人工听看片。

输出根为`EP/production-candidate/value-v6-production-a01/full-final-a01`，EP沿[恢复记录](faith-power-v6-resume-20261019.md)的本机映射。关键小回执：

| 回执 | 大小／SHA-256 |
| --- | --- |
| 输出根`completed-review.json` | 4,662B；`cb1d55542afab47bd682820cd2391e778a8b597ccba2d57b881cd0de9e3c8cc9` |
| 输出根`raw-to-final-map.json` | 5,036,303B；`9a2b824afc591cccf5014e45169fe1fc6a515481833e2de15d6968d13df23474` |
| `text/episode01.chapters.json` | 6,412B；`7411bafbab4254ec0f543a4acc31fe246234b0d0eda66d7d2962ee573d6095df` |
| `RES/LOCAL-DELIVERY-a01.json` | 13,568B；`168c962a646b10f4141cc96001283c57763d4c2285f5636a71205e7775008c50` |
| `RES/FULL-RENDER-CAPACITY-CLOSED-a01.json` | 2,514B；`a5e8dc3901411f1a2e03d2c6e7b6bb546b14d700a0106825b75272c942bf4bc6` |

RES为`EP/revision-v6-20261019/resume-20261019`。本地索引只核成片实际存在及大小，复用原生产者SHA，没有再次哈希大媒体或复制媒体。a36的场景说明及SC27“纳杰夫真实地点示例＋按朝圣者本教判断的结算规则图”作为索引勘误保留；不重写冻结输入或已编码像素。

## 素材与能力边界

R32原图最终index-a02、Root直接像素审阅a01–a08及具体研究见[恢复记录](faith-power-v6-resume-20261019.md)。自己的司祭默认确认页和四个建筑目标本体真实取得；其余五个目标使用真实当前对象配原版来源规则图解，未改名伪造。完整Construct、外部默认神职预览、typed tooltip join/全局清栈仍缺业务资格；Python新修复只保留实际native不可用原因。准备场景、预览与真实已完成后态依各来源标签区分，不能把影片时间当自然战役推进。

`ad245ac`官方CI39233520388于10:38:02Z实际completed/success，Linear39233520196也成功；CI worker machine_id unknown，本机只是只读观察者。小回执`RES/tooltip-readback-research/ciad245ac-a01/terminal-a02.actual.json`为2,032B，SHA `964779b1a7cee0956ddcb6c3a14327131a7241eb90afcad3b419f932d9f8b5dd`。这些CI结果不补授上述原生业务缺口或人工审片。

10:43:14Z对唯一新增输出根做一次既有FileStandardInfo元数据闭账：实际AllocationSize合368,175,552B，含收尾guard保守保留369,224,128B，future0；项目保守上界47,339,029,581B<配额51,177,672,294B，卷free112,869,249,024B。作者/研究/Root累计小型额度仍保守保留，不把未用渲染预留取消算物理回收；本次编码未删除文件。旧原件已回收的事实仍以原精确清单为准。

本审阅交付和必要来源仍在使用，保护用途不迟2026-10-26复核；可重建中间段按通用策略于10月21日起复核当前引用和替代证据。复核不等于到时整树删除，也不因这次交付重置历史资产期限。下一项为完整人工1倍速听看片、记录修改点并签收；预计45–60分钟，尚未执行。

## 2026-10-19后继V7

本页保留V6实际历史。后继[V7交付](faith-and-power-episode01-value-v7-delivery.md)新增开场免责声明／研究版本并完成全文与领袖作用域审校，最终本地审阅版43:54.133；`machine_id: 4-8e1c2f1861`，原wait0于`2026-10-19T13:44:11.792039+00:00`。两版输入、媒体及回执保持各自身份。
