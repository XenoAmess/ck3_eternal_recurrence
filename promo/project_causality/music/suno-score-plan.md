# Suno 配乐生成方案：因果律组曲

## 目标

- 模型：Suno V5 或 V5.5
- Instrumental：On
- 成片长度：`8:20`
- 结构：先生成一条统一主题的长组曲，再按粗剪切分；必要时只对“道”与终幕生成替换段。
- 核心母题：五音动机，前四音逐步上行，第五音回落并悬停；低钟负责“死亡/裁决”，青色脉冲负责“观测/验证”。
- 禁止直接写真实艺术家或乐队名称。

## A 路：主组曲，优先生成

### Style Box

```text
Cinematic dark-fantasy orchestral score with restrained electronic pulse. Low strings, frame drums, glass harmonics, ancient bell and precise mechanical percussion. Medieval archive atmosphere, disciplined dynamic range, one recurring five-note motif, solemn to quietly triumphant, spacious modern mix.
```

### Lyrics Box

```text
[Intro - ominous restrained]

[Main Theme - ember solemn]

[Development - precise mechanical]

[Interlude - sparse uncompromising]

[Finale - luminous ascending]

[Outro - resolved quiet]

[End]
```

### Exclude Styles

```text
no pop vocals
no EDM drop
no trailer braams
```

### 推荐设置

- Instrumental：On
- Weirdness：35–45
- Style Influence：70–80
- 目标：生成 `7:20–8:00`；保留自然尾音，不要求一次精确命中 `8:20`
- 每轮生成 2 个候选，最多 3 轮；先选母题和动态最稳定者，再决定是否 Continue
- 若不足 `8:20`，从 Finale 前约 20–40 秒处 Continue，生成新的 Finale / Outro；后期交叉淡化到精确长度

## B 路：必要的替换段

只有 A 路无法提供足够动态差异时才生成，不默认全部使用。

### “道”稀疏段，约 65 秒

Style Box：

```text
Sparse dark chamber score, low cello, distant ancient bell and paper-like percussion. Minimal harmony, severe pauses, controlled tension, the same five-note motif reduced to single notes, dry intimate mix.
```

Lyrics Box：

```text
[Intro - austere still]

[Main Theme - sparse judged]

[Outro - unresolved breath]

[End]
```

Exclude Styles：`no choir, no drum kit, no cinematic boom`

### “辉煌愿景”终幕，约 120 秒

Style Box：

```text
Visionary orchestral-electronic finale, rising strings, glass harmonics, deep frame drums and wordless low choir. The recurring five-note motif becomes complete and luminous, broad dynamic arc, hopeful disciplined climax, spacious cinematic mix.
```

Lyrics Box：

```text
[Intro - gathering light]

[Main Theme - expansive interlocking]

[Finale - quietly triumphant]

[Outro - luminous release]

[End]
```

Exclude Styles：`no pop vocals, no EDM drop, no heroic fanfare`

## 时间适配

| 成片区间 | 音乐作用 |
|---|---|
| 00:00–00:36 | 低钟、低弦和未完成母题；片名出现时第一次给出五音轮廓 |
| 00:36–03:14 | 增加框鼓与旧金色弦乐；产品群像加速但不盖旁白 |
| 03:14–05:28 | 引入规则脉冲和机械打击；typed state 验证时短促确认 |
| 05:28–06:28 | 主动抽空；RED 处允许 0.5–1.0 秒近静音 |
| 06:28–08:05 | 四 Loop 逐层叠加；每闭合一个 Loop 增加一层织体 |
| 08:05–08:20 | 撤掉鼓点，保留完整母题与明亮低钟，最后 2 秒自然衰减 |

## 选择标准

- 母题在至少三个章节中可辨认，但不能像歌曲副歌一样压过旁白；
- “道”必须真的变稀疏，不能从头到尾保持宣传片高潮；
- Finale 有增长感，但不得成为通用企业胜利配乐；
- 不出现可辨识歌词、突兀人声主唱、EDM drop 或夸张 trailer braam；
- 下载原始无损或最高质量文件，并记录模型、生成时间、Suno track URL/ID、账户权利状态和 SHA-256。
