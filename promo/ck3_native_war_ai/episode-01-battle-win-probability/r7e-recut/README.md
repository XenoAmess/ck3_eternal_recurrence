# 第 1 期 R7E：同场实机先行的开场重剪

R7E 是 R7D 后续的独立 attempt，不覆盖旧脚本、TTS、素材或 OneDrive 文件。`build_script.py` 从 `../r7-same-battle/script.json` 确定性生成本目录 `script.json`；改文案先改生成器，再重建并核对 diff。

开头用墨西拿原片 275 秒与 280 秒，直接并列罗贝尔守方 `1,222→1,156` 的相邻日游戏战斗窗。首 cue 在棕金画面中展示两帧真实实机；第二帧先隐后明，计算卡从第二 cue 才进入。开头只说战线上的 66 名现役士兵减少，不把这项 UI 整数差称作阵亡；底层对应 `122,225,074→115,629,874 raw`，精确差额 `65.952` 人当量。

本版还把“第 5 日主战阶段”和森林 `1,645×90,000÷100,000→1,480` 放在宽度计算之前；主战 `36%` 改称硬伤拆分比例；追击原片 420 秒的“顶部现役 0”与“下方红字 761 名败退”分开解释；智能体局部出伤输入补齐优势系数与固定缩放；区分玩家 UI 和逐团研究回执；结尾不再借罗贝尔守方劣势兵力的本场战斗讲“人多也输”。战前预测的概率提醒移到同场战斗结果之后。

视觉代码在 `../../integration/src/war_ai_promo/episode_one_r7e_same_battle.py`，构建入口在 `../../integration/src/war_ai_promo/produce_r7e_same_battle.py`。沿用第 0 期棕金色、同一首系列主题音乐、固定增益无旁白压低；中文 EdgeTTS 为 `zh-CN-XiaoxiaoNeural`、语速 `-12%`。本次正式工具链选择为 GitHub Release `v0.2.1` wheel，SHA-256 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`。生产 attempt 与全部过程资产保存在 `D:/workspace/ck3_native_war_ai_promo_work/episode01-r7e-recut-001/`。

成片 `CK3-War-AI-Episode-1-Messina-Original-EdgeTTS-Full-R7E-20260926.mp4` 时长 23:04.155，SHA-256 为 `f42e6b54ad33b812037c8af66916ccbf27b67e3cf7fd39f47a7eae6dbf47ff0f`。已只复制这一份 MP4 到固定 OneDrive 选择性同步文件夹 `C:/Users/1/OneDrive/CK3-War-AI-20260923/`，客户端回读为“已上传到 CK3-War-AI-20260923”，未读取或下载其他云文件内容。

客户端上传成功后，对同一路径的文件核对字节与哈希、完整解码、23 章抽帧及 1/8/18/30 秒开场画面；23/23 章配色抽查通过。中文 152 条、英文 65 条字幕和 23/23 章文案对齐通过，26 项数字检查通过。`xar-promo validate --profile authoring` 检查 122 份引用素材及 SHA，结果 GREEN。自动审查与人工抽帧不构成 1× 完整观看签核；精确证据见 `../../build-records/episode1-r7e-opening-recut-20260926.json`。
