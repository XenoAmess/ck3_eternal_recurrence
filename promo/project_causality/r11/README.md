# r11 自然声线重排

r11 解决 r10 的硬性 RED：IndexTTS 自然语速旁白被塞回旧 Edge TTS 画面槽，导致声音尚未结束，旧烧录字幕已经消失。r11 不修补 r9/r10 成片，也不在旧字幕上覆盖遮罩；它从 r6、r8、r9 的原始 manifest 与干净视觉源重新编码。

## 时间契约

- 最终顺序固定为 98 个旁白 cue。
- 旁白使用 r10 已生成的 `natural-reference-emotion` WAV，`tempo=1.0`，严禁 Rubber Band/atempo 压缩。
- 普通镜头下限为：`旁白延迟 + WAV 实测时长 + 1.25 秒尾留`。
- 双语字幕重新排成 `paired-balanced` 块；最后一块至少显示到旁白结束后 1 秒。当前真实素材规划结果为 107 块，而不是把整章双语文字挤进一个旧时间槽。
- 四张章节门保留 12 秒无旁白主题声明和原有 SFX。
- 罗贝尔展示接受 6–12 分钟；无母带 edit 时规划器用 8 分钟占位，但拒绝渲染。
- 全片硬上限 60 分钟。当前 98 条真实 WAV + 8 分钟罗贝尔占位得到约 41 分 39 秒。

## 先生成可审计计划

```powershell
& Z:/ck3_mod_rewrite/tools/.venv/Scripts/python.exe tools/build_project_causality_r11.py
```

这一步不启动 CK3、不运行 IndexTTS、不编码成片，只写：

- `artifacts/project-causality/2026-09-20-r11/project-causality-r11.build-plan.json`
- 同名 `.zh-CN.ass`

计划逐 cue 记录 WAV 哈希、自然时长、字幕块时间、干净视觉源、章节门延迟和 SFX。任一 WAV 的 cue id、文本哈希或文件哈希不匹配都会失败。

## 接入一镜到底罗贝尔母带

复制 `robert-continuous-edit.template.json` 到 artifact 目录并填写 10 个连续区间。约束如下：

1. 所有区间引用同一条从选人界面开始的干净母带。
2. 后一区间的 `source_start_seconds` 必须等于前一区间的 `source_end_seconds`，容差一帧；不能跳切、倒退或漏掉母带时间。
3. `playback_rate` 可以在区间边界改变，用于蒙太奇加速；画面仍按母带时间连续前进。
4. 每个区间换算后的输出时长必须容纳对应自然旁白和尾留，十段合计必须在 360–720 秒内。

正式渲染命令：

```powershell
& Z:/ck3_mod_rewrite/tools/.venv/Scripts/python.exe tools/build_project_causality_r11.py `
  --robert-edit artifacts/project-causality/2026-09-20-r11-robert/robert-continuous-edit.json `
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

## 尚待母带完成后的集成

- 填写连续母带的 10 个语义锚点与速度区间。
- 将 r7 已审阅的 Mermaid 架构运镜以干净 plate override 接回对应 cue；不得从 r7 已烧录字幕的 segment 截取。
- 完整渲染后做 1× 连续审片、字幕安全区抽检、响度和媒体参数验收。
