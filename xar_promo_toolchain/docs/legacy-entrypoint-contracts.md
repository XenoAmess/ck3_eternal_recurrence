# 旧宣传视频入口兼容合同

本文冻结以下两个现行入口的可观察行为，供后续将实现迁入
`xar_promo_toolchain` 后编写兼容 wrapper：

- `tools/build_full_agent_showcase.py`
- `mod_zhongguo_style/tools/build_promo_video.py`

证据均来自上述两份脚本当前源码；行号以本文建立时的版本为准。这里的“必须”表示：如果旧入口改成调用新工具链，旧调用方在不改命令、manifest 和输出消费逻辑的前提下，仍应得到同类结果。新工具链自己的新入口可以提供不同或更宽的能力，但不得借此悄悄改变旧入口。

## 1. 通用能力展示入口

### 1.1 命令行参数

入口：`py tools/build_full_agent_showcase.py ...`

| 参数 | 必填 | 当前默认值 | 冻结行为 | 证据 |
|---|---:|---|---|---|
| `-h`, `--help` | 否 | argparse 内建 | 打印帮助并以 0 退出；不得要求其他必填参数 | `tools/build_full_agent_showcase.py:2031-2054` |
| `--manifest PATH` | 是 | 无 | UTF-8/UTF-8-BOM JSON manifest | `tools/build_full_agent_showcase.py:336-346`, `tools/build_full_agent_showcase.py:2033` |
| `--output PATH` | 是 | 无 | 目标必须以 `.mp4` 结尾（大小写不敏感） | `tools/build_full_agent_showcase.py:2034`, `tools/build_full_agent_showcase.py:2068-2072` |
| `--work-dir PATH` | 是 | 无 | 可复用的构建/缓存根目录 | `tools/build_full_agent_showcase.py:90-92`, `tools/build_full_agent_showcase.py:2035`, `tools/build_full_agent_showcase.py:2091-2097` |
| `--ffmpeg PATH` | 否 | PATH 中的 `ffmpeg` | 显式指定可执行文件；未指定时从 PATH 查找 | `tools/build_full_agent_showcase.py:559-573`, `tools/build_full_agent_showcase.py:2036`, `tools/build_full_agent_showcase.py:2076` |
| `--ffprobe PATH` | 否 | ffmpeg 同目录，继而 PATH | 显式指定可执行文件；未指定时先尝试 ffmpeg 同目录，再查 PATH | `tools/build_full_agent_showcase.py:559-573`, `tools/build_full_agent_showcase.py:2037`, `tools/build_full_agent_showcase.py:2076-2077` |
| `--voice NAME` | 否 | manifest 的 `voice`，再退回 `en-GB-SoniaNeural` | 非空 CLI 值优先；空值不覆盖 manifest；manifest 未给、为 `null` 或空串时使用默认声线 | `tools/build_full_agent_showcase.py:143-147`, `tools/build_full_agent_showcase.py:695-705`, `tools/build_full_agent_showcase.py:2038-2044` |
| `--fps N` | 否 | `30` | 必须为正整数 | `tools/build_full_agent_showcase.py:138`, `tools/build_full_agent_showcase.py:2014-2021`, `tools/build_full_agent_showcase.py:2045` |
| `--crf N` | 否 | `18` | 必须为 `1..51` 的整数 | `tools/build_full_agent_showcase.py:141`, `tools/build_full_agent_showcase.py:2024-2028`, `tools/build_full_agent_showcase.py:2046` |
| `--preset NAME` | 否 | `medium` | 原样传给 libx264 | `tools/build_full_agent_showcase.py:142`, `tools/build_full_agent_showcase.py:1649-1680`, `tools/build_full_agent_showcase.py:2047` |
| `--force` | 否 | false | 忽略旁白和分段的有效缓存并重新生成；不改变 manifest 或输出命名 | `tools/build_full_agent_showcase.py:798-805`, `tools/build_full_agent_showcase.py:829-843`, `tools/build_full_agent_showcase.py:1631-1647`, `tools/build_full_agent_showcase.py:2048`, `tools/build_full_agent_showcase.py:2098-2118` |
| `--validate-only` | 否 | false | 做依赖、manifest、素材哈希、视频裁切范围和文字布局预检，不合成 TTS、不编码且不写构建/输出目录 | `tools/build_full_agent_showcase.py:2049-2053`, `tools/build_full_agent_showcase.py:2074-2089` |

`--manifest`、`--output` 和 `--work-dir` 只在 argparse 后分别执行 `expanduser().resolve()`；manifest 内素材路径则额外支持环境变量和 `~`，相对路径以 manifest 所在目录为基准。wrapper 不得把素材相对路径改成以当前工作目录为基准。`tools/build_full_agent_showcase.py:319-324`, `tools/build_full_agent_showcase.py:387`, `tools/build_full_agent_showcase.py:2068-2070`

### 1.2 manifest 与预检语义

- 根对象要求 `format_version == 1`，并要求非空 `chapters`；章节 ID 不得重复。`tools/build_full_agent_showcase.py:374-415`
- 支持的章节类型固定为 `title_card`、`still`、`video_clip`、`evidence_card`。每章要求中英标题、英文旁白、中文字幕，以及包含中英标签和 `classification` 的 `status`。`tools/build_full_agent_showcase.py:148`, `tools/build_full_agent_showcase.py:415-432`
- `still`/`video_clip` 要求一个 `source`；`evidence_card` 要求非空 `sources`。所有引用必须是存在的普通文件，加载时记录字节数和 SHA-256。`tools/build_full_agent_showcase.py:437-466`, `tools/build_full_agent_showcase.py:526-555`
- `classification` 是调用方给出的展示声明；脚本不从证据内容推导能力等级，而是把声明原样画入画面和 sidecar。`tools/build_full_agent_showcase.py:4-6`, `tools/build_full_agent_showcase.py:1913-1927`
- 全局章节最短时长默认 3.0 秒、旁白尾垫默认 0.75 秒，章节可分别覆盖；镜头时长取“最短时长”和“实测旁白时长加尾垫”中的较大值。`tools/build_full_agent_showcase.py:139-140`, `tools/build_full_agent_showcase.py:392-405`, `tools/build_full_agent_showcase.py:507-520`, `tools/build_full_agent_showcase.py:905-907`
- 视频片段在编码前必须有视频流，且 `start_seconds`/`end_seconds` 必须落在实测素材时长内。`tools/build_full_agent_showcase.py:666-692`

`--validate-only` 仍要求 Pillow、`edge-tts` 包、ffmpeg、ffprobe 和 Windows 字体均可用；它不会访问 Edge TTS 网络服务，也不会创建工作目录或输出文件。换言之，“无网络验证”不等于“可以不安装 TTS 包或媒体依赖”。`tools/build_full_agent_showcase.py:2057-2089`

### 1.3 正常构建输出与 sidecar

正常构建的可观察产物如下：

1. 工作根为 `<work-dir>/showcase-<manifest-SHA256前16位小写>/`，每章目录为 `<三位序号>-<安全化章节ID>/`。`tools/build_full_agent_showcase.py:2091-2097`
2. 每章保留 `narration.en.txt`、`narration.en.mp3`、`narration.edge-tts.json`；TTS 缓存指纹包含 provider/version、旁白文本、声线和 rate/volume/pitch。媒体与元数据通过带回滚文件的事务式替换提交，失败时不把不完整媒体当成有效缓存。`tools/build_full_agent_showcase.py:708-730`, `tools/build_full_agent_showcase.py:749-795`, `tools/build_full_agent_showcase.py:798-885`
3. 每章还保留 `frame.png` 或 `overlay.png`、`chapter.zh-CN.ass`、`segment.mp4` 和 `segment.build.json`；分段缓存指纹绑定章节、分类、素材、旁白、字幕、画面尺寸及编码参数。`tools/build_full_agent_showcase.py:1289-1303`, `tools/build_full_agent_showcase.py:1594-1631`
4. 工作根保留 `concat.txt` 和 `showcase.zh-CN.ass`；脚本成功后不清理这棵可复用工作树。`tools/build_full_agent_showcase.py:1818-1827`, `tools/build_full_agent_showcase.py:2091-2142`
5. 最终成片写到 `--output`，固定验证为 2560×1440、H.264、yuv420p、AAC、48 kHz 双声道；同目录 sidecar 名为 `output.with_suffix(".video.json")`。`tools/build_full_agent_showcase.py:136-142`, `tools/build_full_agent_showcase.py:1772-1807`, `tools/build_full_agent_showcase.py:2009-2011`
6. sidecar 的既有顶层结构为 `format_version`、`kind`、`generated_utc`、`manifest`、`language`、`video`、`subtitles`、`tools`、`chapters`；其中记录 manifest/成片/字幕/素材/旁白/分段哈希、章节时间线、声线与分类。新增字段可以是向后兼容的，但 wrapper 不得删除这些字段或改变其含义。`tools/build_full_agent_showcase.py:1885-2008`

覆盖与保留规则是这个入口特有的：它会先编码到同目录隐藏 `.partial.mp4`，验证后用 `os.replace` 直接替换同名成片；不会为旧成片或旧 sidecar 建归档。旧的同名 partial 会被删除。sidecar 自身也用临时 JSON 原子替换。兼容 wrapper 不得擅自改成 361 入口的“默认拒绝覆盖”语义。`tools/build_full_agent_showcase.py:261-266`, `tools/build_full_agent_showcase.py:1829-1867`, `tools/build_full_agent_showcase.py:2009-2011`

成功构建最后向 stdout 输出 `VIDEO:` 和 `SIDECAR:` 路径标记；验证成功输出以 `VALID:` 开头。兼容 wrapper 至少要保留这些可供脚本识别的前缀。`tools/build_full_agent_showcase.py:2082-2089`, `tools/build_full_agent_showcase.py:2140-2142`

### 1.4 退出码与错误边界

| 情况 | 退出码 | 输出约定 | 证据 |
|---|---:|---|---|
| `--help` | 0 | argparse 帮助到 stdout | `tools/build_full_agent_showcase.py:2031-2054` |
| 正常构建或 `--validate-only` 成功 | 0 | 构建路径标记或 `VALID:` | `tools/build_full_agent_showcase.py:2082-2089`, `tools/build_full_agent_showcase.py:2140-2155` |
| argparse 缺参、类型或范围错误 | 2 | argparse usage/error | `tools/build_full_agent_showcase.py:2014-2028`, `tools/build_full_agent_showcase.py:2031-2054`, `tools/build_full_agent_showcase.py:2145-2146` |
| manifest、依赖、素材或编码产生 `ShowcaseError` | 2 | stderr 以 `ERROR:` 开头 | `tools/build_full_agent_showcase.py:163-164`, `tools/build_full_agent_showcase.py:2147-2151` |
| 构建期间 `KeyboardInterrupt` | 130 | stderr 为 `ERROR: interrupted` | `tools/build_full_agent_showcase.py:2147-2154` |
| 其他未捕获异常 | 非零，当前由 Python 解释器处理 | 当前会逸出并显示 traceback；不属于稳定的业务错误分类 | `tools/build_full_agent_showcase.py:2145-2159` |

wrapper 必须保留 0/2/130 三个明确边界；不得用“进程已启动”或“文件路径已计算”冒充成功。普通进度日志的措辞不是合同，但上述最终标记、错误前缀和退出码是合同。

### 1.5 外部依赖与可迁移边界

当前入口依赖：Pillow；`edge-tts`（未锁死具体版本）；在线 Microsoft Edge TTS（仅缓存未命中时）；ffmpeg/ffprobe；Windows 字体目录中的 Segoe UI/Arial 与 Microsoft YaHei；以及 manifest 引用的本地素材。`tools/build_full_agent_showcase.py:80-92`, `tools/build_full_agent_showcase.py:112-131`, `tools/build_full_agent_showcase.py:559-594`, `tools/build_full_agent_showcase.py:798-895`

适合迁入通用工具链的部分，是 manifest 驱动的章节管线、素材寻址与哈希、TTS 缓存、媒体探测、字幕布局、分段编码、拼接和 sidecar 生成。仍属这个旧入口的项目/表现层合同，包括：CK3 自动玩家语义、英语主叙事加简中字幕、四种旧章节类型、调用方提供的 capability classification、2560×1440 版式和旧 sidecar `kind`。这些可以在新 API 中参数化，但旧 wrapper 必须继续提供原值。`tools/build_full_agent_showcase.py:2-6`, `tools/build_full_agent_showcase.py:80-92`, `tools/build_full_agent_showcase.py:134-159`, `tools/build_full_agent_showcase.py:1963-2008`

## 2. 天朝 361 宣传片入口

### 2.1 命令行参数

入口：`py mod_zhongguo_style/tools/build_promo_video.py ...`

| 参数 | 必填 | 当前默认值 | 冻结行为 | 证据 |
|---|---:|---|---|---|
| `-h`, `--help` | 否 | argparse 内建 | 打印帮助并以 0 退出 | `mod_zhongguo_style/tools/build_promo_video.py:1796-1826` |
| `--manifest PATH` | 是 | 无 | 天朝 361 专用 JSON manifest | `mod_zhongguo_style/tools/build_promo_video.py:172-178`, `mod_zhongguo_style/tools/build_promo_video.py:1798` |
| `--output PATH` | 是 | 无 | 目标必须以 `.mp4` 结尾（大小写不敏感） | `mod_zhongguo_style/tools/build_promo_video.py:1799`, `mod_zhongguo_style/tools/build_promo_video.py:1842-1846` |
| `--work-dir PATH` | 是 | 无 | 保留内容寻址的过程素材 | `mod_zhongguo_style/tools/build_promo_video.py:4-14`, `mod_zhongguo_style/tools/build_promo_video.py:1800`, `mod_zhongguo_style/tools/build_promo_video.py:1887-1903` |
| `--take-id TEXT` | 否 | `take-01` | 必须是非空文本；参与构建根和逐 cue TTS 指纹，用不同 take ID 保留不同录音批次 | `mod_zhongguo_style/tools/build_promo_video.py:751-764`, `mod_zhongguo_style/tools/build_promo_video.py:1801`, `mod_zhongguo_style/tools/build_promo_video.py:1847-1849`, `mod_zhongguo_style/tools/build_promo_video.py:1887-1899` |
| `--ffmpeg PATH` | 否 | PATH 中的 `ffmpeg` | 使用共享入口的发现规则 | `mod_zhongguo_style/tools/build_promo_video.py:1802`, `mod_zhongguo_style/tools/build_promo_video.py:1863-1867` |
| `--ffprobe PATH` | 否 | ffmpeg 同目录，继而 PATH | 使用共享入口的发现规则 | `mod_zhongguo_style/tools/build_promo_video.py:1803`, `mod_zhongguo_style/tools/build_promo_video.py:1863-1867` |
| `--visual-audit-report PATH` | 条件必填 | 无 | 与下一参数成对提供；`captured_release_candidate` 必须提供一个可重验、GREEN 且绑定当前 manifest 的报告 | `mod_zhongguo_style/tools/build_promo_video.py:636-703`, `mod_zhongguo_style/tools/build_promo_video.py:1804-1808`, `mod_zhongguo_style/tools/build_promo_video.py:1851-1858` |
| `--expected-audit-sha256 HEX` | 条件必填 | 无 | 与报告成对提供，必须为 64 位十六进制，并匹配报告 | `mod_zhongguo_style/tools/build_promo_video.py:651-668`, `mod_zhongguo_style/tools/build_promo_video.py:1809-1812` |
| `--fps N` | 否 | `30` | 必须为正整数 | `mod_zhongguo_style/tools/build_promo_video.py:54`, `mod_zhongguo_style/tools/build_promo_video.py:1779-1786`, `mod_zhongguo_style/tools/build_promo_video.py:1813` |
| `--crf N` | 否 | `18` | 必须为 `1..51` 的整数 | `mod_zhongguo_style/tools/build_promo_video.py:55`, `mod_zhongguo_style/tools/build_promo_video.py:1789-1793`, `mod_zhongguo_style/tools/build_promo_video.py:1814` |
| `--preset NAME` | 否 | `medium` | 原样传给 libx264 | `mod_zhongguo_style/tools/build_promo_video.py:56`, `mod_zhongguo_style/tools/build_promo_video.py:1500-1506`, `mod_zhongguo_style/tools/build_promo_video.py:1815` |
| `--archive-existing` | 否 | false | 成片或 sibling sidecar 已存在时，先分别移动到 `superseded/<本地时间戳>/` 再构建；未指定则拒绝覆盖 | `mod_zhongguo_style/tools/build_promo_video.py:1570-1575`, `mod_zhongguo_style/tools/build_promo_video.py:1602-1614`, `mod_zhongguo_style/tools/build_promo_video.py:1816-1820` |
| `--validate-only` | 否 | false | 离线预检；不做 TTS、不创建目录、不写媒体 | `mod_zhongguo_style/tools/build_promo_video.py:1821-1825`, `mod_zhongguo_style/tools/build_promo_video.py:1863-1882` |

manifest、输出和工作目录执行 `expanduser().resolve()`；manifest 内素材路径支持环境变量、`~` 和以 manifest 目录为基准的相对路径。`mod_zhongguo_style/tools/build_promo_video.py:165-169`, `mod_zhongguo_style/tools/build_promo_video.py:278-280`, `mod_zhongguo_style/tools/build_promo_video.py:1842-1844`

### 2.2 361 专用 manifest 与发布门槛

这些是项目专属合同，不应硬编码进通用内核，但旧 wrapper 必须继续执行：

- `format_version == 1`、`kind == "zg361_chinese_first_promo"`、声线必须精确为 `zh-CN-XiaoxiaoNeural`、主语言必须为 `zh-CN`、字幕语言顺序必须为 `["zh-CN", "en"]`，并要求 `skip_ck3_loading_opening == true`。`mod_zhongguo_style/tools/build_promo_video.py:42-60`, `mod_zhongguo_style/tools/build_promo_video.py:278-308`
- manifest 时长上限不得超过 1200 秒；离线估时必须不超过 manifest 上限与 1080 秒保护线中的较小值。TTS 实测和最终编码成片还都必须严格短于 1200 秒。`mod_zhongguo_style/tools/build_promo_video.py:52-58`, `mod_zhongguo_style/tools/build_promo_video.py:300-308`, `mod_zhongguo_style/tools/build_promo_video.py:624-628`, `mod_zhongguo_style/tools/build_promo_video.py:1912-1917`, `mod_zhongguo_style/tools/build_promo_video.py:1639-1642`
- 支持 `title_card`、`placeholder_card`、`still`、`video_clip`；其 `material_status` 必须分别为 `generated`、`placeholder`、`captured`、`captured`。placeholder 要求 capture 描述；实拍 still/video 要求素材和 capture，且 capture 明示 `exclude_ck3_loading == true`。`mod_zhongguo_style/tools/build_promo_video.py:59-60`, `mod_zhongguo_style/tools/build_promo_video.py:379-420`, `mod_zhongguo_style/tools/build_promo_video.py:456-481`
- 每章要求中英标题、双语状态和至少一个 cue；每个 cue 要求中英字幕，`spoken_zh` 未给时回退到 cue 的 `zh`。`mod_zhongguo_style/tools/build_promo_video.py:422-446`
- 14 个 361 主题标签必须全部出现，且中英文脚本文本必须分别命中每个主题的指定关键词；这不是可泛化的视频规则。`mod_zhongguo_style/tools/build_promo_video.py:61-90`, `mod_zhongguo_style/tools/build_promo_video.py:611-623`
- 可选的 release provenance 一旦出现，就要求 GREEN capture、存在的绝对 artifact root、五项带哈希素材，以及固定 policy card ID `[1, 7, 20, 22, 26, 361]`。`mod_zhongguo_style/tools/build_promo_video.py:328-369`
- 当 `project_status == "captured_release_candidate"` 时，所有将渲染的字段都经过测试/夹具禁词扫描，并强制要求视觉审计报告；报告会被重新验证为 GREEN，并绑定当前 manifest 的路径、字节数和 SHA-256。`mod_zhongguo_style/tools/build_promo_video.py:574-609`, `mod_zhongguo_style/tools/build_promo_video.py:636-703`, `mod_zhongguo_style/tools/build_promo_video.py:1851-1858`

脚本确实支持带显眼水印的 placeholder，用于 animatic；sidecar 会把仍含 placeholder 的结果标为 `draft_animatic`，不会把它描述为最终宣传片。本文不把“支持草稿 placeholder”误写成“已通过发布画面审计”。`mod_zhongguo_style/tools/build_promo_video.py:4-7`, `mod_zhongguo_style/tools/build_promo_video.py:1258-1323`, `mod_zhongguo_style/tools/build_promo_video.py:1711-1729`

`--validate-only` 仍要求 Pillow、已安装且版本精确为 7.2.8 的 `edge-tts` 和 Windows 字体；它不会调用 TTS 网络。无视频素材时不要求发现 ffmpeg/ffprobe，有 `video_clip` 时仍要求两者并用 ffprobe 检查素材。release candidate 在 validate-only 下也必须通过同一视觉审计绑定。`mod_zhongguo_style/tools/build_promo_video.py:1829-1841`, `mod_zhongguo_style/tools/build_promo_video.py:1851-1882`

### 2.3 正常构建输出与素材保留

1. 工作根为 `<work-dir>/zg361-promo-<构建键前16位小写>/`；构建键包含 manifest SHA-256、`take_id`、build format 和可选视觉审计报告 SHA-256。每章目录仍是三位序号加安全化章节 ID。`mod_zhongguo_style/tools/build_promo_video.py:1887-1903`
2. 每个 cue 用内容指纹命名并保留 `.zh-CN.txt`、`.zh-CN.mp3`、`.edge-tts.json`。指纹包含 build format、provider/version、voice、rate/volume/pitch、文本和 `take_id`；有效缓存还要通过元数据指纹、媒体 SHA-256 和 ffprobe MP3 检查。`mod_zhongguo_style/tools/build_promo_video.py:751-805`
3. cue TTS 最多尝试 3 次，重试前分别等待 1 秒、2 秒；每次使用独立 partial，失败后删除 partial，只有经过探测和哈希的媒体才提交为缓存。`mod_zhongguo_style/tools/build_promo_video.py:46-51`, `mod_zhongguo_style/tools/build_promo_video.py:810-879`
4. 每章还保留按 cue 哈希聚合的旁白 concat、中文 MP3 和 build JSON；保留内容寻址的 frame/overlay、双语 ASS、segment MP4 和 segment build JSON。相同指纹复用，改变内容或 take 不覆盖旧命名素材。`mod_zhongguo_style/tools/build_promo_video.py:882-1006`, `mod_zhongguo_style/tools/build_promo_video.py:1325-1361`, `mod_zhongguo_style/tools/build_promo_video.py:1439-1498`
5. 工作根保留内容寻址的 concat 清单和 `promo.<构建键>.zh-CN+en.ass`。最终成片仍验证为 2560×1440、H.264/yuv420p、AAC/48 kHz/双声道，并把音轨语言标为 `zho`。`mod_zhongguo_style/tools/build_promo_video.py:92-100`, `mod_zhongguo_style/tools/build_promo_video.py:1500-1506`, `mod_zhongguo_style/tools/build_promo_video.py:1578-1644`, `mod_zhongguo_style/tools/build_promo_video.py:1930-1940`
6. 最终 sidecar 仍为 `output.with_suffix(".video.json")`。既有顶层字段包括 `format_version`、`kind`、`generated_utc`、`readiness`、`honest_boundary`、`take_id`、`manifest`、`language`、`video`、`subtitles`、`placeholder_count`、`tools`、`chapters`，以及有报告时的 `visual_audit`；章节中保留素材、cue、布局、旁白和分段哈希。`mod_zhongguo_style/tools/build_promo_video.py:1647-1776`

同名输出的规则必须保留原样：默认只要成片或 sidecar 任一存在就以退出码 2 拒绝；`--archive-existing` 才将已存在的两者分别移动到输出目录下的 `superseded/YYYYMMDD-HHMMSS/`，随后写入新成片。新成片先写隐藏 partial，经过媒体和 20 分钟上限验证后原子替换；sidecar 也经临时 JSON 原子替换。`mod_zhongguo_style/tools/build_promo_video.py:181-188`, `mod_zhongguo_style/tools/build_promo_video.py:1570-1644`

成功构建最后向 stdout 输出 `VIDEO:`、`SIDECAR:`、`WORK:` 三个路径标记；验证成功输出以 `VALID:` 开头，并报告章节数、placeholder 数、估算时长、声线、双语字幕、loading 排除和审计状态。兼容 wrapper 至少要保留这些前缀和信息含义。`mod_zhongguo_style/tools/build_promo_video.py:1874-1882`, `mod_zhongguo_style/tools/build_promo_video.py:1953-1956`

### 2.4 退出码与错误边界

| 情况 | 退出码 | 输出约定 | 证据 |
|---|---:|---|---|
| `--help` | 0 | argparse 帮助到 stdout | `mod_zhongguo_style/tools/build_promo_video.py:1796-1826` |
| 正常构建或 `--validate-only` 成功 | 0 | 三个构建路径标记或 `VALID:` | `mod_zhongguo_style/tools/build_promo_video.py:1874-1882`, `mod_zhongguo_style/tools/build_promo_video.py:1953-1969` |
| argparse 缺参、类型或范围错误 | 2 | argparse usage/error | `mod_zhongguo_style/tools/build_promo_video.py:1779-1826`, `mod_zhongguo_style/tools/build_promo_video.py:1959-1960` |
| `PromoError`（含被包装的审计、依赖、素材、TTS、媒体错误） | 2 | stderr 以 `ERROR:` 开头 | `mod_zhongguo_style/tools/build_promo_video.py:113-114`, `mod_zhongguo_style/tools/build_promo_video.py:636-672`, `mod_zhongguo_style/tools/build_promo_video.py:1961-1965` |
| 构建期间 `KeyboardInterrupt` | 130 | stderr 为 `ERROR: interrupted` | `mod_zhongguo_style/tools/build_promo_video.py:1961-1968` |
| 其他未捕获异常 | 非零，当前由 Python 解释器处理 | 当前会逸出并显示 traceback；不属于稳定的业务错误分类 | `mod_zhongguo_style/tools/build_promo_video.py:1959-1973` |

### 2.5 外部依赖与项目边界

该入口直接复用 `tools/build_full_agent_showcase.py` 的 Pillow、Edge TTS、字体、ffmpeg/ffprobe、媒体校验与卡片能力，并依赖同目录可导入的 `audit_promo_visuals.py`。它把 `edge-tts == 7.2.8`、晓晓声线、中文主叙事、中英双语字幕、361 主题覆盖、20 分钟上限、实拍/placeholder 状态、release provenance 和视觉审计绑定全部叠加为项目策略。`mod_zhongguo_style/tools/build_promo_video.py:33-60`, `mod_zhongguo_style/tools/build_promo_video.py:278-369`, `mod_zhongguo_style/tools/build_promo_video.py:574-703`, `mod_zhongguo_style/tools/build_promo_video.py:1829-1841`

可迁入通用内核的是逐 cue 双语时间线、内容寻址 take、有限重试、双语 ASS、分段缓存、归档策略和 sidecar 机制；上述晓晓/中文/361/release 审计规则必须留在 profile 或 wrapper，不能成为所有项目的默认硬编码。旧 361 wrapper 则必须继续精确应用这些 profile 值。

## 3. 未来 wrapper 的不可破坏清单

将旧脚本瘦身为 wrapper 时，至少逐项回归以下合同：

1. **CLI 不变**：参数名、必填性、默认值、数值范围和 voice/take/audit 优先级不变；原命令无需新增参数即可运行。
2. **验证不写盘**：两个入口的 `--validate-only` 都不得合成 TTS、编码或创建输出/工作目录；同时保留各自现有依赖检查差异。
3. **路径不漂移**：manifest 内相对素材继续以 manifest 目录解析；最终 sidecar 继续是 sibling `*.video.json`。
4. **退出边界不变**：成功 0、可操作错误 2、构建中断 130；stderr 业务错误继续有 `ERROR:` 前缀。
5. **机器可读标记不变**：保留 `VALID:`、`VIDEO:`、`SIDECAR:`，361 入口另保留 `WORK:`。
6. **媒体最低合同不变**：2560×1440、H.264/yuv420p、AAC/48 kHz/双声道；通用入口保持英文主叙事/简中烧录字幕，361 入口保持简中主叙事和中英双语烧录字幕、且严格短于 1200 秒。
7. **sidecar 向后兼容**：不得移除或改义现有字段；可以添加有明确版本/含义的新字段。分类、素材哈希、时间线、TTS 信息和 honest boundary 不能在迁移中丢失。
8. **保留策略不混用**：通用入口继续直接替换同名成片；361 入口继续默认拒绝覆盖，并仅在显式 `--archive-existing` 下归档旧成片和 sidecar。
9. **过程素材不丢**：工作根、逐章 TTS 文本/音频/元数据、字幕、帧、分段及其 build metadata 继续可定位和复用；361 的 `take-id` 继续形成独立内容身份。迁移器不得在成功后自动清理旧工作树。
10. **项目策略不泄漏**：新内核不得硬编码晓晓、中文、361、固定主题或 CK3 capability classification；这些由旧 wrapper/profile 注入。反过来，旧 wrapper 也不得因内核泛化而放松现有 manifest 和发布门槛。

这份合同不要求新旧编码结果逐字节相同，也不冻结普通进度日志、内部函数名或 Python 模块布局；它冻结的是调用方能观察和依赖的 CLI、校验、退出、媒体、sidecar 与素材保留语义。
