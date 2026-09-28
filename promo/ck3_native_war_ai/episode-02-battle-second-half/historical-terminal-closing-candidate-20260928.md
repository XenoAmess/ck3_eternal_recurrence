# 第 2 期终局与收束候选旁白（2026-09-28）

这一轮为 `terminal` 与 `closing` 两章生成完整的 EdgeTTS **历史研究板候选**音频。源稿明确把 `004` 终局和 `024` 原生 writer 称为不同的历史独立回放；`024` 的 `-50` 只属于它自己的原始回执。新 E2-09 配对尚未取得同 run 实机 writer、战争面板和录像，候选音频不得配成新回放的确定结果。若新 run 的数字或身份不同，修稿后另起 run 重录。

## 身份与范围

- 本轮源稿是 #451 修正后的 `narration-script-draft.md` 精确 26,675 B，SHA-256 `6F970C3C144646F6ACC74B113E1886AA537563045A48D2F041F1F74B6581EB6E`；快照在 `D:/workspace/ck3_native_war_ai_promo_work/episode02-full-narration-20260928-a03/frozen-narration-script-draft.md`。终局六段、收束两段；每段 `request.json` 含 `historical-independent-replays-candidate-only`，manifest 与时长报告同样标记 `new_e2_09_live_verified=false`。
- 新 run 前再次查看 [xar-promo 最新正式 GitHub Release](https://github.com/XenoAmess/xar_promo_toolchain/releases/latest)，当时仍为 `v0.2.1`；重新下载的 wheel 为 190,405 B，SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`，与发布 digest 和 requirements 精确 pin 一致。API 发布原件取自当天已保全的 a02 回执，SHA-256 `453F60B2D8AA3511D5027B6340CEDF75B5E117C574AEE0D18681CFAFE9CD6058`；本轮另作最新网页核对。
- 解释器：`D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`；实际 `xar-promo-toolchain 0.2.1`、`edge-tts 7.2.8`，声线 `zh-CN-XiaoxiaoNeural`、速率 `-12%`，与前四章剪辑代理音频一致。此次没有 CK3 进程、人工 1× 听审、签核或成片。
- [生成器](render_selected_narration.py) 对终局/收束要求显式 `--history-only`，且检查当前稿件中 `024` 与 `004` 的历史身份语句；[审计器](verify_selected_narration_run.py) 复核请求、报告与 manifest 中的同一使用边界。

## 实测与回执

| 章节 | 段数 | 原时间轴预算 | MP3 实测纯旁白 | 预算减纯旁白 | MP3 SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| 终局与战争账本 | 6 | 5:50 | 4:08.256 | 1:41.744 | `AE452762359CAA768DA8B65DB76D8EB65249B5F408E83F7839ADE1F174B2FAB0` |
| 收束 | 2 | 1:35 | 1:21.960 | 0:13.040 | `B148405805DF1AF3ADE70B9EC36D15EC0135249FF0093A603D768E5F060EB027` |

两章合计 **5:30.216** 纯旁白。音频、每段请求/返回/事件/探测、章节 concat 与 probe 均位于新建外置 `D:/workspace/ck3_native_war_ai_promo_work/episode02-full-narration-20260928-a03/render/`；未覆盖前四章 a02 或更早样片。与 a02 前四章的 **16:17.256** 相加是六章跨两个独立 TTS run 的 **21:47.472** 纯旁白素材总长；它不含画面停留、来源卡、音乐、字幕和剪辑，也不是一条同 run 成片。

- 最终生成 manifest：同上 `render/manifest-final.json`，18,226 B，SHA-256 `9EB1A6642E2F06666CF9BBA8A55EA1F51FF20262ADC5F8CB339342CCE007C352`。
- 时长报告：同上 `render/duration-report.json`，SHA-256 `C1271AFA38684FF67136B43155C6E306E9E47A1431A8B7900EA1FB57301FE4EA`。
- 最终机器身份审计：同上 `render/machine-audit-v2.json`，SHA-256 `15FFD499A76B8777AEF9D622B207D861EEC4B79E801F3002000D2C158B37A585`；`GREEN`，8 段、48 个文件身份核对、8 段源稿逐字对拍，逐段与逐章重新 probe，不代表人工完整听审。先前 `render/machine-audit.json` 原件及其内容寻址记录保留，不覆盖。
- 原生 run：`D:/workspace/ck3_native_war_ai_promo_work/episode02-tts-native-run-20260928-a05/run-manifest.json`；最终 `xar-promo validate --json` 为 `GREEN`、`artifacts=16`、`chapters=6`（ProjectConfig 计划章数）、`files_checked=true`。两章 MP3、源稿、生成器、核验器、wheel、回执等关键资产已进内容寻址库，其余全部段级原件在外置 attempt 并由 manifest 哈希绑定。

历史 `024` 精确 DLL 已由 WAR 来源机答复不可得；这段音频只可跟明确写着“历史独立回放 024／原始回执”的研究计算板，以及单独标记的历史 `004` 终局材料配合。新拍 E2-09 需要自己的 source save、DLL/injector、capture report、raw 媒体、clean spans、同 run writer 与战争面板读数，再决定是否重录。
