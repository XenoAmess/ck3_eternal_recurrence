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

## R6：全量文案整改与 32 段重剪

- 成片：`CK3-War-AI-Episode-1-Native-Combat-Calculation-EdgeTTS-Full-R6-20260925.mp4`；27 分 58.821 秒、32 段、101,750,523 字节、SHA-256 `0176d5d83977d34ad983c07d843275268766b04dbcdfc10e323f97438b20f23e`。R5 成片和各次 attempt 永久保留。
- 整改：重新区分原始整数、人数当量、伤害与宽度单位；补齐 #51、#65 职业兵士的逐级定点截断、普通受伤事件对三级伤势的触发条件、静态追击预算与实机回执的边界；合并 R5 重复段落。文案及冻结分镜位于 `r6-recut/script.json`、`r6-recut/timeline.json`。
- 运行：`xar-promo 0.2.1`，wheel SHA-256 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`；成功 attempt 为外置 `episode01-r6-recut-003`，失败的 `-001/-002` 保留。EdgeTTS `zh-CN-XiaoxiaoNeural`、`-12%`，主题音乐 SHA-256 `fda2464fb4b06cd9a2f0196e5c40ca311eb693ec263c996e4ccc24a6ada8803f`，固定 `-17 dB`、不做旁白压低。
- OneDrive：只复制这一份 MP4 至既有同步文件夹；客户端 `2026-09-25T11:20:15Z` 对精确文件名回读“已上传到 CK3-War-AI-20260923”，外置回执 `episode01-r6-recut-003/onedrive-readback-004.json`。上传后按 32 段抽取 64 帧、8 张接触表，已目视检查全部 8 张表。R6 是修订历史版本，后续 R6.1 继续处理字幕过碎与追击逐团算术。

## R6.1：整句字幕、追击分配与 33 章节

- 成片：`CK3-War-AI-Episode-1-Native-Combat-Calculation-EdgeTTS-Full-R61-20260925.mp4`；29 分 16.421 秒、33 章节、107,679,112 字节、SHA-256 `a38a458f2c945c452b38c991ec30b6bf09c61d1fcbdfbbf101597a64d4d1f36b`。精确成片位于外置 `D:\workspace\ck3_native_war_ai_promo_work\episode01-r61-recut-001`；R6 和以前的版本保留。
- 本轮修订：把原先约 5.5 秒切分的半句字幕改为按句或段显示、最多两行，保护中文数字不断行；#65 画面卡明确列出三次不同方向的定点除法；追击先给出 A/B 定点比例和两类兵团每日预算，再新增一段逐团分配及一个原始单位余数的写回。文案、分镜和生成器在 `r61-recut/`；逐段复审见 [R6.1 全量文案审计](r61-recut/copy-audit.md)。
- 工具链：开工前核实最新正式 `xar-promo 0.2.1`，wheel SHA-256 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`；`tools/.venv/Scripts/python.exe` 执行原生 run，最终 MP4 和上传／审计回执均用 content-addressed `preserve` 保全，`validate` 对 196 件 artifact 精确字节检查 GREEN。EdgeTTS `zh-CN-XiaoxiaoNeural`、`-12%`；唯一主题音乐同上，固定 `-17 dB`，不做旁白压低。全片 `ffmpeg -xerror` 解码通过。
- OneDrive：只复制这一份新 MP4 到 `C:\Users\1\OneDrive\CK3-War-AI-20260923`，本地同步副本与源文件字节数、SHA-256 一致；客户端 `2026-09-25T11:55:42Z` 对精确文件名回读“已上传到 CK3-War-AI-20260923”，外置回执 `episode01-r61-recut-001/onedrive-readback-003.json`。没有读取或下载其他云端文件内容。
- **先上传，后机器检查**：按 33 章节各抽两帧，共 66 帧、9 张接触表；已目视复核全部 9 张表，数字卡与字幕未见裁切／重叠，实机战斗热点仍在镜头内。外置回执 `episode01-r61-recut-001/machine-review-001/machine-review-report.json`。真实 ASS 轨检查 197 条中文、83 条英文字幕，最多两行，没有中文数字跨行拆断；33 章节、媒体流与时长均 GREEN，见外置 `full-copy-audit-001.json`。本检查是机器抽样与逐段文案复核，不是人工 1× 完整观看；当前没有人工 signoff。

## R6.2：研究编号对上游戏人物、兵种与界面字段

- 成片：`CK3-War-AI-Episode-1-Native-Combat-Calculation-EdgeTTS-Full-R62-20260925.mp4`；33 分 23.188 秒、33 章节、121,021,039 字节、SHA-256 `f29c00bb010a16e042677bfca6b97a6673efec21c8aaabed07643a9c5f29bc43`。R6.1 及以前成片和失败 attempt 均保留原样。
- 整改：R0217 的 side 0/1 分别说成尼基弗鲁斯率领的敌军／玩家罗贝尔军；墨西拿 #50 是罗贝尔征召兵，#51 是原版“长枪兵”，#65 是骑士图尔吉塞的一人战斗记录，而不是普通兵士兵种；第 26 日击杀者 34120 是敌方塔米姆军骑士阿姆鲁，另一份伤情回执的 54144 是拉马丹军骑士阿什拉夫。原版 UI 的“勇武／调动／主要阶段／战线宽度／溃逃士兵／战死士兵”等名称进入口播和卡片；各内部量明确说明没有独立面板。R0220 与静态追击向量仍不编造人物。证据、全量文案复审和限制见 [R6.2 对照账](r62-contextual/identity-ui-ledger.md)与[成片审计](r62-contextual/copy-audit.md)。
- 素材与工具链：成功 run `r62-contextual/project/runs/run-20260925-r62f`、外置 attempt `D:\workspace\ck3_native_war_ai_promo_work\episode01-r62-contextual-006`；开工及出片时核实最新正式 `xar-promo 0.2.1`，wheel SHA-256 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`。EdgeTTS `zh-CN-XiaoxiaoNeural`、`-12%`；系列唯一主题音乐 SHA-256 `fda2464fb4b06cd9a2f0196e5c40ca311eb693ec263c996e4ccc24a6ada8803f`，固定 `-17 dB`、无旁白压低。33 段 UI/来源审计、28 项整数算式及完整解码 GREEN。
- OneDrive：只复制这一份 MP4 至既有选择性同步文件夹；本地副本与源文件字节数及 SHA-256 一致。客户端 `2026-09-25T13:36:35Z` 对精确文件名回读“已上传到 CK3-War-AI-20260923”，外置回执 `episode01-r62-contextual-006/onedrive-readback-003.json`；没有读取或下载其他云端文件内容。
- **先上传，后机器检查**：实际 ASS 轨共 224 条中文、81 条英文，最多两行、无中文数字跨行拆断；33 章节与时长 GREEN。每章节两帧，共 66 帧、9 张接触表，已逐张目视复核，抽样未见数字行／标题／字幕裁切或重叠，墨西拿游戏镜头仍覆盖战斗热点。回执为 `episode01-r62-contextual-006/full-copy-audit-001.json` 和 `machine-review-001/machine-review-report.json`。人工 1× 完整审阅与 signoff 未发生。
