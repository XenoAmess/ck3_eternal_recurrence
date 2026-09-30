# 第 2 期 a05：统一战争系列棕金包装

2026-10-01，用户指出完整六章 a04 使用蓝色宣传包装，要求沿用第 0、1 期战争系列的棕黄色。

本次独立分支为 `codex/war-series-brown-gold-20261001`，工作树 `C:/w/e2gold1001`，底座为同事 a04 固定源 `d81b91be1ae6bf818f38c3c5af0d595dd4ea4752`。分支 owner 为本次 `/root`，隔离原因是用户要求未获合入指令前保持独立；验收目标为包装配色一致、游戏像素及音轨不变、完整媒体检查与单文件交付。目标日期为 2026-10-01；分支保留至用户明确要求合入。本次没有 fetch、pull、merge、rebase master，也没有操作 Steam、CK3 或桌面。

## 系列基准与修正

参考本地第 0 期 V5 和第 1 期 R7F Corrected 实际视频各三张原尺寸帧，以及 [R7D 视觉规则](../episode-01-battle-win-probability/r7d-brown-gold/visual-style.md)。参考文件均完全本地化，未触发云端下载。六张参考帧、RGB 采样及只读核对记录永久保留于 `C:/Users/1/ck3-war-palette-reference-20261001/attempt-01/`。

| 包装用途 | 统一色值 |
| --- | --- |
| 页面背景、字幕带、实录补边 | `#211813` |
| 计算面板、实录来源标签 | `#35291F` |
| 标题、正文米白 | `#F0E5CF` |
| 金色强调、定位框、字幕带分隔线 | `#CBA56A` |
| 弱边线 | `#61503C` |
| 次要文字 | `#BBA98D` |

色值集中到 `integration/src/war_ai_promo/series_palette.py`；原第 0 期 `visuals.py` 保留同名导出且色值不变。第 2 期当前画板和实录包装直接引用这一源。中文白字、英文浅灰的字幕字形沿用前两期，不把游戏原始 UI、地图或肖像统一染色。

新 run 为 `C:/Users/1/AppData/Local/ck3-review-render/episode02-brown-gold-20261001-a01/`。重新生成 154 张画板并重编码六章，保留 13 个原速片段的原始路径、起点、长度和出处。完整 167 句脚本与时间轴沿用 a04，最终 AAC 流直接复制 a04；没有重新生成 TTS、混音或改变片长。此前已修正的 `terminal-t031`、`closing-c004` 结算后 −50% 主放大保持同一来源与裁切。

本次再次实际查询宣传工具链最新正式 Release，为 `xar-promo-toolchain 0.2.1`，wheel SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`。显式解释器为 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，Python 3.14.7；没有相对 venv 时未回落系统 Python。Release 查询、依赖版本、真实 CLI help、配置快照、原生 run manifest、源码、命令、TTS 引用、画板、编码块、章节与中间拼接都保留。

## 新实物与检查范围

最终文件 `CK3-War-AI-Episode02-BrownGold-20261001-a05.mp4` 为 239565059 字节，SHA-256 `DE3471E6B14246A9D606C35DB72750D5910074CA9B53C1943CF44AF29D7222E4`，目标视频时长 1818.633333 秒（30:18.633）。24 块编码、六章拼接和原音轨封装全部返回 0。旧 a04 的 `CB141C…` 文件及全部历史版本、失败 attempt、原片与证据保持原样。

实际最终媒体审计与有限成片帧复核已通过；a05 作为配色中间版保全，尚未复制到 OneDrive。随后逐句机制审计发现图注、缺字和局部放大映射问题，最终交付转到独立 a06 新 run；旧 a05 不改字节。任何机器检查、抽帧或客户端 InSync 均不替代完整人工 1× 观看、听审、原片 clean span 与 signoff；这些状态继续待真人执行。

独立审计位于 `C:/Users/1/ck3-a05-palette-media-audit-20261001/attempt-02/`：全部 154 张包装采用棕金，所有原 UI 粘贴区域逐像素保留；24 块 347 条 ASS Dialogue 全文、位置与时码不变；全片 AV 解码 54559 帧返回 0；85284 个 AAC packet 的 payload、PTS/DTS/duration/flags/side data 与 a04 精确一致。六章及 13 个原速片段的来源与时间保持。`report.json` 为 `PASS`，`quality-report.json` 为有限帧 `PASS_PENDING_HUMAN_REVIEW`，均绑定上述 DE3471… 实物。

完整 run 的过程索引、机器/有限帧报告和视频已经公开工具链 API 加入原生不可变存储；`native-preservation-complete.json` SHA-256 为 `9B681B916047762EC428EB35B71CD4B8B41D99006B296A7BC3021A2F497DDCA1`，人工 signoff 数为 0。原始索引记录“因后续机制审计制作 a06，a05 未交付”，不能将其写成客户已收到的版本。配色工作包未操作游戏；另行补证工作包的当次桌面恢复 RED 见机制审计专题。
