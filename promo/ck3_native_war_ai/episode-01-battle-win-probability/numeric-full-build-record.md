# 第 1 集原版数字版 EdgeTTS 整片构建记录

- 成片：`CK3-War-AI-Episode-1-Native-Battle-Math-EdgeTTS-Full-R3-20260925.mp4`；23 分 04.488 秒、30 章节、180,923,123 字节、SHA-256 `9701488f5a434078d7b85bb77854a04ce69481de3ac197acbcb27ce959ef5bf6`。
- 配音：EdgeTTS `zh-CN-XiaoxiaoNeural`，速率 `-12%`；数字版 25 cue 的所有请求、音频、边界和时间探测保存在外置 `D:\workspace\ck3_native_war_ai_promo_work\episode01-native-numeric-edge-full-003\speech`。整片采用其中 23 cue，并穿插已核对的 M02–M08 算式卡。未把未使用的 F11/F12 放入成片。
- 剪辑与音频：墨西拿同存档独立实机段落、R0217 单日出伤算式卡，以及墨西拿原始第 5→6 日守方入伤与伤亡卡。全片只使用系列单一主题音乐 SHA-256 `fda2464fb4b06cd9a2f0196e5c40ca311eb693ec263c996e4ccc24a6ada8803f`；固定 `-17 dB` 增益，不做旁白压低。
- 构建：`xar-promo` 正式版 `0.2.1`，wheel SHA-256 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`。原版研究回执、文案、分镜、实机和音频经 `xar-promo` 原生 run 保存；25 段观察片构建 GREEN。最终 30 段合成在外置 `episode01-native-numeric-edge-full-004`，保存 edit list、每段哈希、章节、完整解码和成片哈希。失败的 `episode01-native-numeric-edge-full-003` 合成尝试保留原样，没有覆盖。
- 数值核对：见 [证据账](numeric-script-evidence.md)。R0217、墨西拿第 5→6 日和 R0220 分属不同原版回执；实机镜头是独立重放，第 6 日后不能按原始研究回执逐帧解释。没有报未经校准的整场胜率或深层击杀概率。
- OneDrive：仅复制这一份 MP4 到既有 `C:\Users\1\OneDrive\CK3-War-AI-20260923`。`2026-09-25T07:58:24Z` 客户端活动行明确显示该精确文件名“已上传到 CK3-War-AI-20260923”；回执为外置 `episode01-native-numeric-edge-full-004/onedrive-readback-002.json`，本地同步副本与源文件 SHA-256 一致。
- 上传后机器检查：对成片 30 章节各取两帧，共 60 帧、8 张接触表，检查字幕、数字卡与实机战场布局；未见裁切或标题/字幕重叠。全文件解码通过。检查回执为外置 `episode01-native-numeric-edge-full-004/machine-review-001/machine-review-report.json`。机器检查不等于人工 1× 完整签核，当前没有人工签核。

## R4：原始整数与实际人数逐项配对

- 成片：`CK3-War-AI-Episode-1-Native-Battle-Math-EdgeTTS-Full-R4-20260925.mp4`；25 分 46.921 秒、30 章节、159,269,048 字节、SHA-256 `966ced74773f7b791655f7fb8145caee9bc3d7db31af7a697d0ae16751b495ae`。R3 文件与证据保留原样。
- 修订原因：R3 把人数与伤亡的十万倍原始整数先口播成“上亿／几十万”，而实机界面只有几百／几千人。R4 在首次解释及 F05、F13–F15 逐项把原始人数／伤亡 `÷ 100,000` 后的按人折算值紧邻说出，并在画面卡上成对显示。战宽、已按人回读的整数、伤害值、属性值、ID、计数器分别说明单位；F05、F14 换成回执数字卡，避免独立重放画面承担另一份战局的精确人数证明。详见 [单位对照](unit-consistency-r4.md)。
- 素材与工具链：R4 观察配音与 25 段工具链构建在外置 `D:\workspace\ck3_native_war_ai_promo_work\episode01-unit-observation-005`；R0217 算式段在 `episode01-edge-math-unit-007`；整片 30 段合成在 `episode01-native-unit-edge-full-005`。EdgeTTS `zh-CN-XiaoxiaoNeural`、速率 `-12%`；系列单一主题音乐 SHA-256 `fda2464fb4b06cd9a2f0196e5c40ca311eb693ec263c996e4ccc24a6ada8803f`、固定 `-17 dB`、无旁白压低。开始 run 前重新查询最新正式 `xar-promo 0.2.1`，wheel SHA-256 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`。
- OneDrive：只把这一个 R4 MP4 复制进既有选择性同步文件夹 `C:\Users\1\OneDrive\CK3-War-AI-20260923`。本地副本与源文件字节数、SHA-256 一致；客户端在 `2026-09-25T08:52:42Z` 回读该精确文件名“已上传到 CK3-War-AI-20260923”，外置回执为 `episode01-native-unit-edge-full-005/onedrive-readback-003.json`。
- 上传后检查：完整解码通过；按 30 章节各抽两帧，共 60 帧、8 张接触表。已目视复核全部 8 张表，兵力／伤亡换算卡完整可读，字幕与数字卡抽样未见裁切或重叠，实机战场未漂离。外置回执为 `episode01-native-unit-edge-full-005/machine-review-001/machine-review-report.json`。这不是人工 1× 完整观看，人工签核仍未提供。

## R5：兵团伤亡、骑士人物和追击链

- 成片：`CK3-War-AI-Episode-1-Native-Casualty-Chain-EdgeTTS-Full-R5-20260925.mp4`；38 分 37.355 秒、42 章节、195,570,365 字节、SHA-256 `2a3df7c67e7832cd4ffeae1df9db9ae83fb0d6259f94de53656855ff1d19ca5a`。R4 成片及所有旧 attempt 保留原样。
- 新增 12 段解释：墨西拿原版第 5→6 日 #50 征召兵、#51 职业兵士与 #65 一人规模 MAA entry 的各自逐级截断；36% 硬伤转换、软伤和底层组件存储顺序；坚韧敏感度；骑士人物的五日排程、有效事件加权抽取、受伤/致残/死亡及第 26 日实机退场；原版追击公式 golden vector 的坚韧加权、追击、掩护、基础/下限、双预算、逐团分摊与尾数。受控公式反事实与静态追击向量均在字幕和画面标明，不冒充墨西拿同场实机。
- 可审计口径：[伤亡链说明](../../../docs/ck3-native-ai/combat-casualty-chain-explainer.md)；文案与分镜分别在 `casualty-addendum/script.json`、`casualty-addendum/timeline.json`，追击逐步补格在 `pursuit-detail/script.json`、`pursuit-detail/timeline.json`。独立 11 段 run 为外置 `episode01-casualty-addendum-r5-001`，单段追击 run 为 `episode01-pursuit-detail-r5-001`，42 段整片合成为 `episode01-native-casualty-edge-full-006`；完整音频、请求、卡片源图、分段、失败/成功记录与 SHA 均保留。
- 工具链：新 run 前从 GitHub 最新正式 Release 核实 `xar-promo 0.2.1`，wheel SHA-256 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`；所选解释器为仓库 `tools/.venv/Scripts/python.exe`。继续使用 EdgeTTS `zh-CN-XiaoxiaoNeural`、`-12%`，系列唯一主题音乐 SHA-256 `fda2464fb4b06cd9a2f0196e5c40ca311eb693ec263c996e4ccc24a6ada8803f`，固定 `-17 dB`、不做旁白压低。
- 机器门禁：42 章节及 38 分 37.355 秒已由最终媒体 probe 核对，全文件 `ffmpeg -xerror` 解码通过；全片 run 已把精确 MP4、edit list、segment manifest 与 build receipt 作为 content-addressed artifact 保全，`xar-promo validate --profile authoring` GREEN。人工 1× 完整审阅仍未提供，不能代签。
- OneDrive：先通过桌面客户端只将这一份 R5 MP4 复制到既有选择性同步文件夹 `C:\Users\1\OneDrive\CK3-War-AI-20260923`；本地同步副本与源文件大小和 SHA-256 一致。客户端在 `2026-09-25T09:44:35Z` 回读精确文件名“已上传到 CK3-War-AI-20260923”，外置回执为 `episode01-native-casualty-edge-full-006/onedrive-readback-004.json`。
- 上传后检查：对 42 章节各取两帧，共 84 帧、11 张接触表；已目视复核全部 11 张表，新增数字卡可读，抽样未见字幕、标题裁切或重叠，实机战场热点仍在画面内。外置回执为 `episode01-native-casualty-edge-full-006/machine-review-001/machine-review-report.json`。这是上传后的机器抽样检查，不是人工 1× 完整签核。
