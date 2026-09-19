# 《project因果律》30 分钟 Suno 配乐接力单

本文件只规定项目所有者明天手动输入 Suno 的内容。制作脚本不会打开、登录或自动操作 Suno；当前 picture lock 也不包含音乐。

## 总体音乐合同

- 模型：Suno V5 或 V5.5；Custom Mode；`Instrumental: On`。
- 母题：五音动机，前四音逐步上行，第五音回落并悬停；不同章节改变配器，不改变身份。
- 叙事底色：黑暗奇幻档案感 + 克制的电子机械脉冲；从“余烬”逐步走向“可验证的光”。
- 四个章门 `03:10–03:30`、`13:40–14:00`、`21:10–21:30`、`25:10–25:30` 保持无配乐，仅保留已经合成的专属声效与主题宣言。
- 不追求一次生成精确长度。每条生成略长，后期只做裁切、短交叉淡化与旁白 ducking。
- 不使用任何真实艺术家或乐队名称。

整片分成六条独立配乐，而不是把一首长曲机械循环三十分钟。每条先生成两个候选；只有母题或结构明显不稳时再开第三轮。

## Track 00 — 冷开场与体系命题

- 成片位置：`00:00–03:10`
- 建议生成长度：`03:20–03:50`
- 作用：先以死亡结算与余烬提出问题；55 秒片名出现时第一次给出可辨认但不完整的五音母题。

### Style Box

```text
Cinematic dark-fantasy chamber score, restrained electronic pulse, low strings, ancient bell and glass harmonics. Slow 68 BPM, unresolved five-note motif, spacious modern mix, documentary tension, wide dynamic range.
```

### Lyrics Box

```text
[Intro - ember still]

[Main Theme - questioning restrained]

[Development - hidden mechanism]

[Outro - suspended breath]

[End]
```

### Exclude Styles

```text
no vocals
no EDM drop
no trailer braams
```

## Track 01A — 咒：可见产品与轮回

- 成片位置：`03:30–08:35`
- 建议生成长度：`05:20–05:50`
- 作用：展示主 Mod、白绮、牛来、天朝 361 已公开能力与周边工具；节奏应有前进感，但不能压成产品罗列广告。

### Style Box

```text
Dark-fantasy orchestral documentary score, low strings, frame drums, hammered dulcimer and subtle analog pulse. 82 BPM, recurring five-note motif, measured forward motion, detailed spacious mix.
```

### Lyrics Box

```text
[Intro - covenant opens]

[Main Theme - artifacts revealed]

[Development - many forms one system]

[Bridge - inheritance deepens]

[Outro - controlled momentum]

[End]
```

### Exclude Styles

```text
no vocals
no heroic fanfare
no pop drums
```

## Track 01B — 咒：自动玩家与诚实边界

- 成片位置：`08:35–13:40`
- 建议生成长度：`05:20–05:50`
- 作用：从可见产物转向自动玩家的观察、决策、操作、验证；在 capability boundary 与 blocker 处主动抽空。

### Style Box

```text
Cinematic systems score, muted low strings, precise mechanical percussion, glass pulses and distant bell. 78 BPM, the same five-note motif fragmented into verified signals, restrained tension, transparent documentary mix.
```

### Lyrics Box

```text
[Intro - telemetry awakens]

[Main Theme - observe decide act]

[Break - evidence only]

[Development - bounded autonomy]

[Outro - unresolved blocker]

[End]
```

### Exclude Styles

```text
no vocals
no EDM drop
no triumphant climax
```

## Track 02 — 术：制造方法

- 成片位置：`14:00–21:10`
- 建议生成长度：`07:20–07:55`
- 作用：文档组织、生成器、MCP、智能体、OCR 与反例边界。节拍像精密工坊，不像高速编程混剪。

### Style Box

```text
Orchestral-electronic process score, pizzicato low strings, paper percussion, modular synth pulse and dry metallic clicks. 88 BPM, recurring five-note motif arranged as a precise workflow, clean separation, disciplined dynamics.
```

### Lyrics Box

```text
[Intro - blueprint measured]

[Main Theme - documents become contracts]

[Development - generators synchronize]

[Interlude - bridge state exposed]

[Break - OCR only when visible]

[Development - agents verify outcomes]

[Outro - methods return evidence]

[End]
```

### Exclude Styles

```text
no vocals
no cyberpunk aggression
no festival drums
```

若生成结果短于 7:10，不要循环整段。优先从第二个 `[Development]` 前使用 Suno Continue，并以 `[Outro - methods return evidence]`、`[End]`
结束；下载合并后的完整版本。

## Track 03 — 道：证据尺度

- 成片位置：`21:30–25:10`
- 建议生成长度：`04:00–04:30`
- 作用：把音乐密度降到全片最低；为“文档高于测试、测试高于代码”和 readiness 边界留出呼吸。

### Style Box

```text
Sparse dark chamber score, low cello, distant ancient bell and dry paper percussion. Slow 60 BPM, five-note motif reduced to isolated tones, severe pauses, intimate uncompressed mix.
```

### Lyrics Box

```text
[Intro - austere still]

[Main Theme - claims weighed]

[Interlude - red remains red]

[Bridge - hierarchy of evidence]

[Outro - verdict suspended]

[End]
```

### Exclude Styles

```text
no vocals
no drum kit
no cinematic boom
```

## Track 04 — 辉煌愿景：四环咬合

- 成片位置：`25:30–30:00`
- 建议生成长度：`04:45–05:20`
- 作用：四个无限演进 Loop 逐层加入织体，最后完整陈述五音母题；明亮但不变成通用企业胜利配乐。

### Style Box

```text
Visionary orchestral-electronic finale, rising strings, glass harmonics, deep frame drums and luminous analog pulse. 84 BPM, recurring five-note motif gradually completed, broad controlled arc, hopeful documentary climax, spacious mix.
```

### Lyrics Box

```text
[Intro - first loop ignites]

[Main Theme - four loops interlock]

[Development - evidence feeds creation]

[Finale - luminous disciplined]

[Outro - recurrence continues]

[End]
```

### Exclude Styles

```text
no vocals
no EDM drop
no heroic fanfare
```

## 交回文件

每条至少保留 A/B 两个原始候选，优先下载 WAV；没有 WAV 时保留 Suno 原始下载格式，不要预先转码。放入：

```text
artifacts/project-causality/2026-09-19-r6/music/inbox/
├─ 00-prologue-a.*
├─ 00-prologue-b.*
├─ 01a-spell-products-a.*
├─ 01a-spell-products-b.*
├─ 01b-spell-agent-a.*
├─ 01b-spell-agent-b.*
├─ 02-method-a.*
├─ 02-method-b.*
├─ 03-principle-a.*
├─ 03-principle-b.*
├─ 04-vision-a.*
└─ 04-vision-b.*
```

同时记录每条的 Suno track ID 或分享 URL、模型版本、生成时间、使用账户/方案对应的商业使用权状态。不要把登录凭据写入仓库。

## 选择标准

- 六条在配器与五音母题上必须像同一部片，不像六个随机歌单条目；
- 旁白区域不能持续满编制，必须允许后期压到旁白下方；
- Track 01B 的边界段、Track 03 全段必须真的稀疏；
- Track 04 有增长感，但不得出现英雄凯旋、合唱主唱、EDM drop 或夸张 trailer braam；
- 开头和结尾必须可裁切，不得在目标时长附近突然断奏；
- 任何音乐接入都会改变当前候选哈希，接入后必须重新做媒体探针与 1× 连续审片。
