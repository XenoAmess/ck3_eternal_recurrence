# r11 自然声线重排

r11 解决 r10 的时间轴缺陷：IndexTTS 自然语速旁白被塞回旧 Edge TTS 画面槽，导致声音尚未结束，旧烧录字幕已经消失。r11 不修补 r9/r10 成片，也不在旧字幕上覆盖遮罩；它从 r6、r8、r9 的原始 manifest 与干净视觉源重新编码。

## 时间契约

- 最终顺序固定为 98 个旁白 cue。
- 旁白使用 r10 已生成的 `natural-reference-emotion` WAV，`tempo=1.0`，严禁 Rubber Band/atempo 压缩。
- 普通镜头下限为：`旁白延迟 + WAV 实测时长 + 1.25 秒尾留`。
- 双语字幕重新排成 `paired-balanced` 块；最后一块至少显示到旁白结束后 1 秒。当前真实素材规划结果为 107 块，而不是把整章双语文字挤进一个旧时间槽。
- 四张章节门保留 12 秒无旁白主题声明和原有 SFX。
- 罗贝尔展示不锁定巴勒莫。R30 正式源从可见的 1066 罗贝尔选人界面开始，经 MCP 状态绑定、动态选敌、宣战、作战、首胜和后续防御战；成片使用母带 `95s..480s` 的连续 `6:24.967` 区间。源时间不跳切、不倒序、不重排，播放速率为 `1.0x`。
- 动态选敌会通过 MCP 读取全部合法宣战项并逐个查询原生军力；目标保守兵力取基础、网络合计、修正后合计三者最大值，优先 3:2 优势，若无优势则选择当前最低风险目标并继续到首次战争级失败。每轮完整排名写入 `target-evaluations.jsonl`，不靠 OCR 或预设人名。
- 全片硬上限 60 分钟。当前 98 条真实 WAV + R30 连续实机得到约 40 分 04 秒。

## 先生成可审计计划

```powershell
& Z:/ck3_mod_rewrite/tools/.venv/Scripts/python.exe tools/build_project_causality_r11.py
```

这一步不启动 CK3、不运行 IndexTTS、不编码成片，只写：

- `artifacts/project-causality/2026-09-20-r11/project-causality-r11.build-plan.json`
- 同名 `.zh-CN.ass`

计划逐 cue 记录 WAV 哈希、自然时长、字幕块时间、干净视觉源、章节门延迟和 SFX。任一 WAV 的 cue id、文本哈希或文件哈希不匹配都会失败。

## 接入一镜到底罗贝尔母带

复制 `robert-continuous-edit.template.json` 到 artifact 目录并填写 10 个语义区间。区间名称对应“开局—治理—评估—战争—再次评估—能力边界”，不再对应固定目标。约束如下：

1. 所有区间引用同一条从选人界面开始的干净母带。
2. 后一区间的 `source_start_seconds` 必须等于前一区间的 `source_end_seconds`，容差一帧；不能跳切、倒退或漏掉母带时间。
3. `playback_rate` 可以在区间边界改变，用于蒙太奇加速；画面仍按母带时间连续前进。
4. 每个区间换算后的输出时长必须容纳对应自然旁白和尾留；最终展示长度由真实连胜次数决定，并服从全片 60 分钟硬上限。
5. 控制和判定必须是 MCP-only；不得使用 OCR、鼠标、键盘、固定坐标或旧 Palermo 专用步骤。权威录制契约见 `docs/project-causality-robert-mcp-streak-capture.md`。

正式渲染命令：

```powershell
& Z:/ck3_mod_rewrite/tools/.venv/Scripts/python.exe tools/build_project_causality_r11.py `
  --robert-edit promo/project_causality/r11/robert-continuous-edit.r30.json `
  --render
```

没有 `--robert-edit` 时，`--render` 必然失败。这个门禁是为了防止候选片悄悄复用 r9 的多段旧罗贝尔素材。

## 干净重渲染边界

视觉输入来自：

- r6 的 `project-causality-30m.manifest.json`：原始图片、实机片段、证据卡；
- r8 的价值说明和四章门 manifest；
- r9 agent manifest 仅提供 10 个 cue 的标题、文案和版式定义；正式画面由连续母带 edit 替换；
- 家徽编辑器的三段画面统一改读 r9 的 53.4 秒干净实录，并按自然旁白时长连续分段、统一变速；不会退回 r6 中重复读取同一段前 20 秒的错误；
- 98 个自然声线 WAV。

`project-causality-r9-nomusic-picture-lock.mp4` 与 r10 成片不在输入图中。字幕在各干净 segment 最后一次烧录，因此不存在遮罩旧字幕或双层字幕。

## R30 集成状态与边界

- 已填写并校验 10 个连续语义区间；母带为 `artifacts/project-causality/2026-09-20-robert-mcp-streak-r30/robert-mcp-showcase-continuous-6m25s.mp4`，SHA-256 `08C5A46300641CC0141AD1FDDD6BC22F93C61A8C92147E5036A8BDB65F469245`。
- R30 已证明动态选敌后的第一场进攻胜利。后续自动进入防御 WarID `23`，智能体接管新战争并继续观察、规划和游玩；成片在这里收束，不替尚未结束的战争预告胜负。底层报告继续保留操作员停止状态供工程审计。
- 将 r7 已审阅的 Mermaid 架构运镜以干净 plate override 接回对应 cue；不得从 r7 已烧录字幕的 segment 截取。
- 完整无音乐版已经渲染到 `artifacts/project-causality/2026-09-20-r11/project-causality-r11-owner-voice-nomusic.mp4`：`40:03.880`、2560×1440、H.264/AAC、SHA-256 `C776E5D21490A5D425B931DAB2DBB959B3DEB959CCAB54B6ED3C4DC2F28903B4`。
- 媒体参数、107 块字幕时长/宽度、十点画面抽检、选人/胜利/战役继续帧与响度均通过机器/人工抽检；所有字幕至少覆盖到对应旁白结束后 1 秒。完整 1× owner 审片和后续 owner-operated 音乐 pass 仍待进行，因此 publication 保持未授权。
