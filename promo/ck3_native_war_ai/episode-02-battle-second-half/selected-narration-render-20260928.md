# 第 2 期四章完整旁白素材（2026-09-28）

本轮只生成 `opening`、`pursuit`、`knights`、`reinforcement` 四章的**全章** EdgeTTS 剪辑代理音频。`terminal` 与 `closing` 留待新 E2-09 终局配对实机复核；旧 `024` 的 `-50` 是历史独立 writer 回执，不能配成新 attempt 的确定结果。本轮没有启动 CK3、没有人工 1× 审片或签核，也没有成片。

## 冻结身份与工具

- 本轮精确旁白稿快照：`D:/workspace/ck3_native_war_ai_promo_work/episode02-full-narration-20260928-a02/frozen-narration-script-draft.md`，26,675 B，SHA-256 `6F970C3C144646F6ACC74B113E1886AA537563045A48D2F041F1F74B6581EB6E`。它包含已合入的终局勘误，但后两章没有录音。
- 旧 26,022 B 稿件 SHA-256 `7F0972E042016D7D7B6B558CF54B866E139512FCE481DB6696F895D1BCAEBCA3` 与新稿的前四章：全部 22 段的口播文本 SHA 逐段相同；四章对拍回执 `D:/workspace/ck3_native_war_ai_promo_work/episode02-full-narration-20260928-a02/four-chapter-parity.json` SHA-256 `80CA776C2FE4A4D1B490F7EC37737649FA9C71112B0644161A7BF91C5C68B802`。
- 本次新 run 前查看 [xar-promo 最新正式 GitHub Release](https://github.com/XenoAmess/xar_promo_toolchain/releases/latest)，当时指向 `v0.2.1`。下载的正式 wheel 为 190,405 B，SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`，与发布资产 digest 和 `tools/requirements-promo-toolchain.txt` 一致。API 原件沿用当天较早 a02 的只读发布回执，SHA-256 `453F60B2D8AA3511D5027B6340CEDF75B5E117C574AEE0D18681CFAFE9CD6058`；本轮另作最新发布网页核对。
- 解释器：`D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`；实际 `xar-promo-toolchain 0.2.1`、`edge-tts 7.2.8`、`zh-CN-XiaoxiaoNeural`、`-12%`。这是剪辑代理声线，不代替计划中的最终 IndexTTS 人工审阅声线。`ffprobe`/`ffmpeg` 为本机 FFmpeg 9.0.1 WinGet 路径；路径和各次命令在 manifest 中。
- 生成器：[render_selected_narration.py](render_selected_narration.py)；机器身份核验：[verify_selected_narration_run.py](verify_selected_narration_run.py)。两者只处理既有文本与音频，不调用 CK3，也不制造人工签核。

## 实测音频

| 章节 | 段数 | 原时间轴预算 | MP3 实测纯旁白 | 预算减纯旁白 | MP3 SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| 开场 | 2 | 1:30 | 1:16.056 | 0:13.944 | `B57C8E7F7B4881D6EE8AB553682B3757EF6A6109B0BBDB11EC994BD07F9A8103` |
| 追击三日 | 6 | 5:40 | 4:05.784 | 1:34.216 | `2C2CFE26710A71974553608BF5A5588F2197D7B8AECC036F065AE029D0DDF52A` |
| 骑士事件 | 7 | 6:40 | 5:28.752 | 1:11.248 | `8EE7C6E70F1C7022DCA30C81DA83DCAAF69D7C414A4881AA1F282252A65E7DB4` |
| 增援入账 | 7 | 8:35 | 5:26.664 | 3:08.336 | `A8BA26C4E4815762EC436376D0968063B9DC5E6E750D0EC997907259D074AC3D` |

四章合计 **16:17.256** 纯旁白。章节 MP3 位于外置 `D:/workspace/ck3_native_war_ai_promo_work/episode02-full-narration-20260928-a02/render/<chapter-id>/chapter-speech.mp3`；每段各有 `request.json`、`response.mp3`、`response-events.jsonl`、`ffprobe-receipt.json`，章节另有 concat 输入/命令回执与 probe。每个文件留在新建的 append-only attempt 中，旧 attempt 原样保留。纯旁白时长不含来源卡、画面停留、转场、音乐、字幕或人工调整；不能由本表直接声称成片长度。

## 回执与边界

- 最终生成 manifest：`D:/workspace/ck3_native_war_ai_promo_work/episode02-full-narration-20260928-a02/render/manifest-final.json`，41,780 B，SHA-256 `396660C8843A90976C732BAE323A7FA1AF42545216C634EE7084974BCAA30AF8`；绑定源稿、22 个请求/返回、事件、探测、四章拼接与音频。
- 时长报告：同上 `render/duration-report.json`，SHA-256 `EB16F7CD9975500B17BB2374105EA5AF98123C0466CF1903DB0C54A9FF264EFF`。
- 机器身份审计：同上初次 `render/machine-audit.json` 为 `GREEN`。2026-09-28 追加 `render/machine-audit-v2.json`，SHA-256 `18B63EB2A6080EEDC4F705DCABC8B8B74D47898168486502C8C1D4765055AA30`，再次核对 112 个文件身份、22 段冻结源稿逐字对拍，并逐段与逐章重新 probe；两次原件均保留，均不代表人工完整听审。
- 原生 run：`D:/workspace/ck3_native_war_ai_promo_work/episode02-tts-native-run-20260928-a04/run-manifest.json`；初次校验 `artifacts=16`，追加 v2 审计和审计器后最终 `xar-promo validate --json` 为 `GREEN`、`artifacts=18`、`chapters=6`（项目配置计划章数）、`files_checked=true`。四个章节 MP3、源稿、工具、wheel、报告等关键资产已进内容寻址库；其余全部段级过程原件留在外置 attempt 并由 manifest 哈希绑定。
- 前一轮 `a01` 在源稿从 `7F0972...` 变为 `6F970C...` 后，于发起 provider 请求前拒绝继续，`provider_calls=0`。错误保存在 `D:/workspace/ck3_native_war_ai_promo_work/episode02-full-narration-20260928-a01/source-drift-red.json`，并进入独立原生 run `episode02-tts-native-run-20260928-a03`；未重写为 GREEN。

**后续**：E2-09 新配对只有静态材料核验，旧 `024` 精确 DLL 已被来源机答复不可得。等新 attempt 的同轨原生 writer、战争面板与录像核对后，若数字或身份改变，先修订 `terminal`/`closing` 文本和计算卡，再用新 run 录后两章。若新拍追击或增援轨迹变化，前四章也只能作为其明确标出的旧研究叙述，不能给新画面配成同一次回放。
