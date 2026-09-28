# 第 2 期旁白时长复测（2026-09-28，a02）

## 身份与方法

- 审计对象是当前 `narration-script-draft.md` 的精确 26,022 字节，SHA-256 `7F0972E042016D7D7B6B558CF54B866E139512FCE481DB6696F895D1BCAEBCA3`。旧 a01 样片及 a04 审计绑定另一版 25,652 字节稿件，不能替代本次测量。
- 开始本次 run 前，以 GitHub Releases API 查询独立仓库最新**正式**发布为 [`v0.2.1`](https://github.com/XenoAmess/xar_promo_toolchain/releases/tag/v0.2.1)，发布时间 2026-09-02，wheel SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`；与 `tools/requirements-promo-toolchain.txt` 一致。使用 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`（Python 3.14.7），执行 `pip install --require-hashes -r tools/requirements-promo-toolchain.txt` 并确认 `xar-promo 0.2.1`、`edge-tts 7.2.8`、`ffprobe`，以及顶层和相关子命令帮助。
- 每章各选一整段旁白，按现有 `zh-CN-XiaoxiaoNeural`、`-12%` 语速生成独立 EdgeTTS MP3，`ffprobe` 实测文件时长。23 条第 1 期既有语音 cue 只作历史语速基线。样段不等于整章配音，也不代表拟用的最终 IndexTTS 声线或人工完整审片。
- 原生 `xar-promo start-run` 创建 run，`preserve` 将精确稿件、脚本、选择计划、样片 manifest、事件记录、六个 MP3、release API 回执及审计结果写入内容寻址库。`xar-promo validate <run-manifest> --json` 为 `GREEN`，`artifacts=14`、`chapters=6`、`files_checked=true`。本次没有启动 CK3 或占用桌面。旧 attempt 原样保留；a05、a06、a07 是顺序独立审计，其中 a07 修正了通用 limits 文案，为下文引用的最终审计。
- 审计器还以旧 a01 manifest 做负向验证：对当前稿件抛出 `sample run belongs to different draft bytes`，且不生成目标审计文件；两个 Python 脚本通过 `py_compile`。

## 实测与时长判断

| 章节 | 当前时间轴预算 | 本次样段实测 | 按本章样段外推整章纯旁白 | 原预算剩余 |
| --- | ---: | ---: | ---: | ---: |
| 开场 | 1:30 | 44.352 秒 | 1:17.9 | 12.1 秒 |
| 追击三日 | 5:40 | 37.584 秒 | 4:00.1 | 1:39.9 |
| 骑士事件 | 6:40 | 33.456 秒 | 5:18.9 | 1:21.1 |
| 增援入账 | 8:35 | 58.560 秒 | 6:09.0 | 2:26.0 |
| 终局与战争账本 | 5:50 | 45.504 秒 | 4:31.2 | 1:18.8 |
| 收束 | 1:35 | 38.976 秒 | 1:16.1 | 18.9 秒 |

六段实际音频合计 **4:18.432**；全稿为 4,343 个汉字、70 个阿拉伯数字 token。23 条历史 cue 的 `3.8072` 汉字/秒若生搬至全稿，得纯旁白 **19:00.7**，明显低估数字密集的增援与终局样段。六段合并速率外推为 **22:05.1**；按各章自身样段外推并加总为 **22:33.2**。后者仍是估计，不是全稿音频实测：数字读法、英文标识、段间停顿和句长会改变速度。

**22–24 分钟可以继续作为剪辑目标，现稿的 29:50 章节时间轴应重排。**以 22:33 的章节估计计，24:00 只余约 **1:27** 给所有来源卡、证据停留、转场和片尾；22:00 则需要先缩短旁白。若画面证明需要更长停留，优先压缩下面的口播数字，保留完整数字在可读计算卡；正式声线全稿渲染和画面粗剪后再定最终片长。不要把“29:50 预算”或任何单项自动审计写作成片时长。

## 六章逐段剪辑建议

1. **开场（稿件第 20、22 行）**：1:17.9 估计已接近原 1:30。保持来源身份解释，开头只需短标题停留；不为时长另加前情。
2. **追击三日（第 34、36、38 行）**：三段连续读长小数与零差分，建议口播聚焦“追击如何把软伤变硬”和 `72/72`、`69/69` 的闭合，`62.94269` 等逐帧原始值留在 E2-02/03 证据卡。原预算多出约 1:40，不必以静态表格填满；可给观众约 20–30 秒看证据后收紧节奏。
3. **骑士事件（第 54、58、62 行）**：第 54 行有效勇武和伤害链的多个小数可用 E2-04 卡展示，口播读方向和关键差值；第 58 行 `020` 是第 26 日选择器；第 62 行 `070` 是另一回放的成长权重，`036→038` 又是另一条后档名册，三者来源标签、数字与逻辑边界必须保留。这里更需要分轨的视觉停顿，不能为了压缩把三条回放说成一条。
4. **增援入账（第 76、80、82、86 行）**：最优先口语化第 76、80、82 行的缓存、残差、Q100000 和宽度计算。E2-06/07 卡完整保留 `085` 同钩子原数、`2570` 对 `2560`、旧残差、`R8D=2220` 及单位；口播让观众先猜旧缓存加新兵，再说“差额来自旧缓存与 entry 不齐”，最后落到首次出伤确实消费 `2220`。第 86 行必须说清“实际入场已发生”与“未来入场可预测”之间的边界，但可少读内部接口英文。增援样段含五个数字 token 和 23 个拉丁字符，58.56 秒比历史汉字速率预测的 40.97 秒长，整章外推不确定性最高。
5. **终局与战争账本（第 96、100、102、104 行）**：保留战斗攻方与战争攻方身份转换；第 100 行的中间软输入和第 102 行八桶全数、第 104 行长除法由 E2-09 卡逐行呈现。口播讲清 `024` 自己同一次 writer 的分子、整数比例、CB 倍率和战争攻方 `-50`，不能接在 `004` 后装成同一轨迹。终局样段含五个数字 token，45.50 秒比历史预测的 32.83 秒长。精确算式的实机镜头仍需新 run 与当次原件复核，不能把本次 TTS 审计当成录像准入。
6. **收束（第 116、118 行）**：估计 1:16.1，留约 19 秒给四格来源回闪和片尾；保持现有短句，不扩写新的结论。

## 复核入口

| 对象 | 位置 | SHA-256 |
| --- | --- | --- |
| 六样段最终 manifest | `D:/workspace/ck3_native_war_ai_promo_work/episode02-narration-samples-20260928-a02/manifest-final.json` | `E451A9B42AC03B06FC24AFF2024469577D2BAB4BAEB932CAE44BA6898D2CFB9A` |
| 当前完整时长审计 | `D:/workspace/ck3_native_war_ai_promo_work/episode02-narration-budget-audit-20260928-a07/audit.json` | `44C32B91A83AD3682627C21A053E4D83739F07F54126062A80F1EF04DC548579` |
| 原生 run manifest | `D:/workspace/ck3_native_war_ai_promo_work/episode02-tts-native-run-20260928-a02/run-manifest.json` | `64A2F5CAD33B32F17743CD99FF24570A528BF2A5BAC3B5B55362EF0E92AE2EE7` |
| 最新正式发布 API 回执 | 同上目录 `latest-release-api.json` | `453F60B2D8AA3511D5027B6340CEDF75B5E117C574AEE0D18681CFAFE9CD6058` |

复现命令模板（使用已核实的解释器，命令中路径从本 worktree 根目录执行；先用 `xar_promo start-run` 建立新的原生 run，以实际路径替换尖括号占位符。未来新 run 应重新查询届时最新正式 wheel 并更新版本和哈希参数）：

```cmd
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\sample_narration_tts_v2.py --draft promo\ck3_native_war_ai\episode-02-battle-second-half\narration-script-draft.md --project-config promo\ck3_native_war_ai\episode-02-battle-second-half\project\promo-project.json --run-manifest <new-native-run-manifest> --output <new-unique-attempt-dir> --expected-draft-sha256 7F0972E042016D7D7B6B558CF54B866E139512FCE481DB6696F895D1BCAEBCA3 --toolchain-version 0.2.1 --wheel-sha256 F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621 --ffprobe C:\Users\1\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffprobe.exe
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\episode-02-battle-second-half\audit_narration_budget.py --draft promo\ck3_native_war_ai\episode-02-battle-second-half\narration-script-draft.md --expected-draft-sha256 7F0972E042016D7D7B6B558CF54B866E139512FCE481DB6696F895D1BCAEBCA3 --reference-speech D:\workspace\ck3_native_war_ai_promo_work\episode01-r7-same-battle-001\speech --sample-manifest <new-unique-attempt-dir>\manifest-final.json --ffprobe C:\Users\1\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffprobe.exe --output <new-unique-audit-dir>\audit.json
```

这里的 a02 是时长样片及机器审计，不是完整旁白、人工签核、实机录像或成片。
