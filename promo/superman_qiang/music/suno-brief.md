# 《超人强》宣传片单曲配乐输入

2026-10-04。按用户指定的 suno-engineer skill 编制；用户在 Suno 生成并提供一首纯配乐。配音另用 Edge TTS 的 zh-CN-XiaoxiaoNeural，不把旁白放进 Suno。

## 创作目的

服务已批准的 02m 玩家宣传稿：宫廷的体面、赴约的诱惑，以及“你也可能是猎物”的反转。影片允许 90–300 秒；本曲目标约 3 分钟，实际长度允许浮动，后期依据原曲和配音剪辑。只使用一个配乐来源，不要求多首音乐或多份分轨。

## Suno 输入

模式：Custom；Instrumental：On。若当前界面提供创意滑杆，建议 Weirdness 25%、Style Influence 80%；这是本次创作偏好，不是生成结果保证。

### Style of Music

```text
Instrumental cinematic dark comedy, baroque chamber orchestra. 96 BPM, D minor. Harpsichord, pizzicato low strings, restrained hand percussion. Sparse arrangement, short memorable motifs, ample space for spoken narration. Brief intro, concise three-minute cue, clean resolved ending.
```

### Lyrics

纯音乐只填以下结构标签，不填台词、括号说明或时间轴。

```text
[Intro - sly regal]

[Main Theme - playful temptation]

[Bridge - sudden suspense]

[Main Theme - confident return]

[Outro - elegant resolve]

[End]
```

### Exclude Styles

```text
no vocals, no choir, no EDM drops, no dense lead melody
```

## 接入与审听

接收用户提供的一个原始音频文件，永久保存原始字节、来源、SHA-256 和实际媒体探测结果。当前尚未收到音乐，不能标为已生成或已接入。

审听关注：无歌词或吟唱；主旋律克制、给旁白留空间；主题有记忆点；中段有一次悬念变化；结尾可自然收束。情绪顺序优先于精确秒数，结构标签不能保证生成时长或反转位置。按原曲变化点配合剪辑，必要时对同一首音频裁切、淡入淡出，并在旁白期间降低音乐音量。

参考：[suno-engineer SKILL.md](C:/Users/1/.codex/skills/suno-engineer/SKILL.md)、[Suno Custom 与 Instrumental](https://help.suno.com/en/articles/3726721)、[Suno Exclude 输入](https://help.suno.com/en/articles/3161921)。
