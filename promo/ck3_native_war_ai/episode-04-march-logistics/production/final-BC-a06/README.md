# 第4期最终 B/C 旁白生产知识与代码

这是文本、方法与历史生产证据包。最终中文69段、完整来源账、Root实际中文源审、六章音频索引、新7段词边界和原生118项run manifest均精确保留。实际旁白为41658624个24k单声道16位样本，即28:55.776；新增7段配音，62段中文及67旧音频片段复用，未插入静音。新7段774个WordBoundary来自实际provider原生ticks；最早6旧片段仍没有词边界，沿用完整PCM，不重配或拟合。

本包不携带MP3、PCM/WAV、视频、截图或native content-addressed树。索引与manifest中的外置路径是历史来源信息，不能默认在另一台机器可用。OMITTED-ASSETS.json明确列出历史media pins及118个CAS记录；包内consumer不会打开这些路径或读取媒体。历史native validate=0是当次实际机器回执；不能把本包的metadata检查称作现在完整native run或媒体验收。

## 只读、跨机器检查

用已验证Python运行 `python -I -S -B verify_pack.py plan`（默认也是plan），或显式 `verify`。只读取本目录FILE-CATALOG列明的文本文件，核对bytes/SHA、69段与源审绑定、实际生产代码的AST方法和记录下来的整数时钟。它不import/执行production code，不调用provider、媒体工具、游戏、桌面、Git、下载或安装。输出PASS只覆盖包内文本与记录方法/时钟，媒体可用性仍NOT_CARRIED_NOT_GRANTED。

## 实际生产顺序

Root对准确正文和ledger的NO_BLOCK之后，实际oral producer执行validate-freeze/freeze。final_BC_audio.py支持真正plan、prepare-final-request、generate、bind-english；TTS由EdgeTtsProvider/TtsRequest和edge_tts.Communicate.save_sync WordBoundary API完成，没有虚构通用TTS CLI。generate从旧音频索引中文字计算最少voice diff，以4–8并发只生成这些段；每个请求、返回、失败、退避、decode/probe和stdio永久保全。AUDIO-READY先交字幕/画面；公共preserve_artifact API单进程串行登记，避免逐文件解释器冷启。随后bind-english只写新的六章索引，0provider、0新PCM/WAV。

code目录保留实际执行源码和历史输入路径。复用前显式提供新机器的输入、解释器及媒体工具，取得新版本/人物/军队实证；不要直接执行历史launcher，也不要把包内metadata视为已有音频。每个新的正式production run重新查询最新正式GitHub Release。本次2026-10-06 00:38:37 UTC实际fresh query匹配v0.2.1，wheel SHA f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621，0install。通用工具链源码留在独立仓库，此处只归档项目代码及实际API/sourcepin metadata。

## 叙事边界

A首次到达观测区间(49,51]；B在+38因冻结编制/统帅门槛未通过而停止，剩52日，伦敦结果NULL；C首次到达观测(75,77]，15个两日采样偏差原样保留，仅描述性NOT_GRANTED，winner NULL。C终态global scope available/unknown[]，途中59..75未知单位健康NULL保留历史；主力原始27团/37DATA的6689不是玩家全军总数。当前1%损耗getter不是死亡账；所有人数与现金变化是净端点，不是补员、付款或损失执行ledger。

PUBLISHED-RESEARCH-REFERENCES引用既入库A/B/C具体commit与repo路径，不重复研究原包。Root中文源审不等于人工听审、完整影片1×或签核。成片和字幕生产另有自己的attempt；本包不授clean span、影片验收或外部发布。
