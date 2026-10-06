# 战争第4期最终 BC 双语字幕与实际音频时钟

最终 Chinese a06 实际69段保持稳定编号；相对 A-only 修改7段：C05-04/05/08/10/14/16、C06-10。其他62段中文、英文、显示与音频来源复用。本次字幕已按真实24kHz单声道PCM生成全片ASS、C05全部16段与C06全部10段相对ASS；字体保持中文35、英文25，每种语言最多两行、实测宽度上限1700像素。完整音频41658624样本，即1735.776秒（28:55.776）；字幕326组，其中新增86个语义组。

实际新增7段配音包含774条原生WordBoundary；67个既有音频fragment复用，旧6段没有WordBoundary，保留既有实际PCM段边界及诚实的计时标签。没有为英文再请求TTS，没有插入静音，也没有用预测时长作为最终时钟。索引中的音频路径与SHA只是已完成run的历史来源；本text-only包不包含WAV、MP3、视频、截图或原片。

最终来源边界保留：C在第77天首次观察到London，第75天仍在路上，所以实际到达区间为(75,77]，精确tick未知。主力原27团/37DATA为6689/6747、补给101.90260、容量300；这些是该主力的读数，不是玩家全部单位总人数。终点当前1%损耗不是旅途实际死亡数。B在第38天因冻结条件变化停止，尚有52日预算，并非耗时截止；新增1/1团与统帅变化的原因未知。C有15次真实采样偏差，严格比较资格NOT_GRANTED，未产生三方案赢家。净金币变化不能改写为行军、登船或逐笔付款账；真实饥饿及applied loss/refill/payment ledger仍未由此闭合。

第一轮实际字幕build因为4组英文显示超过4.5词/秒而RED，已保留原FAILURE、stderr、command receipt、原alignment与失败章节timeline。仅这4处显示英文作等义缩短，完整English源、中文、声音和实际时码都没有变化。最终新86组无机器读速flag，最大英文4.44445词/秒、中文5.42169字/秒。Root实际逐段读完原86组中英并窄读4处显示改动，精确source receipts已保全。文本语义审核和自动读速检查不等于人类完整听审、1×影片观看或signoff。

便携证据：[index.json](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/final-bc-subtitles/index.json)。其中原JSON/ASS/源码/WordBoundary/失败attempt文本均逐字节复制，来源绝对路径仅是历史注记。跨机器检查只需stdlib；默认PLAN不读文件、不写资产，显式`--verify`才核catalog字节、69段中英重建、实际PCM连续性、62段原显示复用、C05/C06相对范围和新774条WordBoundary。

```text
python -I -S promo/ck3_native_war_ai/episode-04-march-logistics/evidence/final-bc-subtitles/verify.py
python -I -S promo/ck3_native_war_ai/episode-04-march-logistics/evidence/final-bc-subtitles/verify.py --verify
```

本专题只授予实际字幕/音频时钟与精确文本来源的交付信用。最终主片、媒体审核、OneDrive上传、远端传输和人类signoff由各自实际产物与回执另行记录。
