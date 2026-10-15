# Review02 story-a05：原69段最后16段草稿

本目录新增C01-03/04/05/06/08、C02-01/02/04/11/12、C03-01、C04-09、C05-11/12、C06-03/04。与story-a02/a03/a04的53段不重叠，文字草稿覆盖69/69。**此分母只数有正文的原段号**，不代表全文已审冻结、研究/镜头/配音/新版成片完成。原六章和30–35分钟编辑目标不变，实际时长仍须由将来的音轨与动态镜头确认。

[完整口播与镜头](narration.zh-CN.md)、[逐段director/claim/shot/API映射](claim-shot-agent-map.json)、[来源字节索引](source-index.json)共同使用。director映射保留当时行号与行文本，章节预算及旧pending状态不被改写为新完成事实。R03/R07/ABC等仍按各自实证边界；本次写作新增研究信用为0。

[TTS JSON](tts-inputs.zh-CN.json)保存16段精确输入及逐段UTF-8 SHA；[纯文本](tts-inputs.zh-CN.txt)只有正文，以两个换行分段，无标题、编号或MISSING。它们只是待源审的配音输入，未发送provider、未选新声线、未产生音轨或请求回执。不可因这里准备完文本就宣布声音完成。

D13数量与单位、D14费用口径、D15合军输入位于[cards-svg](cards-svg)。[纯SVG生成器](render_cards.py)只写新的显式输出目录，无PNG、TTS、SDK、游戏、媒体调用；其颜色与2560×1440字号沿用系列，1120以下留字幕。SVG的XML与文本墨迹边界检查不等于视觉审阅或成片签核。

```text
python -B promo/ck3_native_war_ai/episode-04-march-logistics/review02/story-a05/render_cards.py --output-dir <new-explicit-directory>
```

旧53段、旧失败attempt及Review01交付不改。新.4合军source依赖若存在，由source-index精确列出其封包；实际stock/cap/weights pair仍单独待取，不把source公式变成实机结果。媒体候选和精确支付数据只复用已有账，本目录未打开或重哈希原片。
