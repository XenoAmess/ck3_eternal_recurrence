# 玩家宣传片 composer 准备

项目代码为 [player_trailer_composer.py](../../tools/player_trailer_composer.py)，原生配置为 [render-project.json](../../render-project.json)。它实现正式 xar-promo 0.2.1 的 `PipelineComposer` ABI，交由原生 `plan` / `build` 执行。正式成片的 run 和 attempt 由主执行者建立，本文不声称已经产出成片。

公共包负责 native run、phase history、CAS、process audit 和 render-plan 执行；项目 composer 负责批准的十场文案、实音时长、画面取景、中文字幕、安全区和唯一 Suno 音乐的剪辑与混音。没有改动或复制公共工具链源码。

验证已经完成：

- 原生 `validate render-project.json`：authoring GREEN，十章。
- Python 编译：GREEN。
- 真实 Edge TTS `zh-CN-XiaoxiaoNeural` / 十场语音共 99.576 秒；根据这些实际时长与镜头头尾，渲染时间线为 138.666667 秒、30 fps。
- 真实 SentenceBoundary + 已安装 Microsoft YaHei 46 px：31 个字幕 cue，最长行 1104 px，小于 1460 px 安全宽；每句外区间来自 provider，长句内部按文字权重细分，未声称逐词强制对齐。
- 四种画面各两秒的 FFmpeg 技术 smoke：艺术镜头、示意图、完整实机静帧、七属性词层均 GREEN。它们只检查真实滤镜与编码，不能作为最终视频验收。
- 第一 smoke 的短裁片可选层时序触发负 fade；原 RED attempt 保留。实现现在跳过已超出裁片区间的图层，第二 attempt 验证通过。旧 attempt 未覆盖。

完整外置过程在 `C:/ck3-superman-qiang-promo-20261004/composer-prep-A0001/`：API 实读、字幕报告、两个 smoke attempt 的输出、partial、ASS、filtergraphs、argv、stdout/stderr 与命令收据永久保留。字幕原始请求与音频由独立 narration run 保全；音乐由独立 music-input attempt 保全。

接口：主执行者在新 native run 保全 `render.inputs`、`music.source`、`narration.input.SQP-01` 至 `SQP-10`、`visual.overlay.SQP-01` 至 `SQP-10`。项目输入 JSON 必须有原始配乐与旁白 summary、视觉 plan、font、frame、duration policy，以及全部背景和 optional PNG 的 SHA 绑定；overlay 直接从 run 的不可变 CAS 读取。只读 plan 不创建 workdir、不调用 TTS、不运行 FFmpeg。

首次真实 native CLI plan 为 RED：原 authoring 占位 `generic` / `default` 没有 Python entry-point 注册。该失败尚未调用 composer；manifest 前后 SHA 完全不变，提议的 build workdir 没有创建。原始源码、配置和失败计划收据已保存在 `C:/ck3-superman-qiang-promo-20261004/render-A0001/failed-plan-source/`，A0001 不改为 GREEN。

必要修正是项目自有的小登记包 [plugin/pyproject.toml](../../plugin/pyproject.toml)，声明真实 `xar_promo.adapters` 与 `xar_promo.presets` entry points；正式配置使用 `superman-qiang-prepared-stills` / `superman-qiang-player-trailer`。两 factory 返回真实 prepared-media 及玩家宣传 preset 政策，composer 实际消费源类型、SHA 必需性、截图比例、语音、画幅、时长范围和镜头呼吸配置。公共官方 wheel 始终保持 0.2.1，没有改源码或注册空占位。

登记包的首轮构建因同一已验证 venv 缺少构建 backend 而标 environment RED，完整过程留在 `registration-A0002`。随后将 setuptools 84.0.0 的确切 wheel 下载、保全并安装，另开 `registration-A0003`，真实构建、安装、import/entry-point 来源验证全部 GREEN。小登记 wheel 为 `superman_qiang_promo_project-0.1.0-py3-none-any.whl`，2704 bytes，SHA-256 `07f81cdedb0ad6f2df9a411842f5a412be565868f21778f2fe72df3b57596e98`；pip 源码副本、生成 metadata、wheel、依赖 wheel、argv 与完整 stdout/stderr/receipt 全部留在外置 attempt，未在仓库写入 build 目录。新配置与源码须由主执行者绑定一个新 run，再执行原生只读 plan。

真实命令形式：

```text
tools/.venv/Scripts/python.exe -m xar_promo plan <native-run-manifest> --workdir <fresh-render-attempt> --composer promo.superman_qiang.tools.player_trailer_composer:compose
tools/.venv/Scripts/python.exe -m xar_promo build <native-run-manifest> --workdir <same-fresh-render-attempt> --composer promo.superman_qiang.tools.player_trailer_composer:compose --offline-tts
```

产物 ID 为 `deliverable.player-trailer`；相对路径为 `deliverables/superman-qiang-player-trailer.mp4`。额外保留 `timeline.json`、完整 ASS/SRT、字体测量报告、逐场 filtergraph、concat 输入和单音乐混音 filtergraph。`storyboard-timing.json` 保留公共 storyboard 原输出；`storyboard.json` 使用实际 review API 的 `id` 章节字段，供主执行者结合公共 `probe_and_write_bound_media` 实测封套调用 `review`。

目标为 H.264 / yuv420p / 1920×1080 / 30 fps / AAC 48 kHz 双声道。音乐是用户提供的一份 WAV，剪辑保留原曲开头及最后 12 秒，以 2 秒 crossfade 接续；旁白归一化并驱动音乐 duck，最终响度目标 -16 LUFS / TP -2 dBFS，实际编码后的响度和 true peak 必须另行实测。本模块不记录人工 approval。

2026-10-04 09:12:08 UTC，A0002 的实际 native CLI plan 已 GREEN：10 segments draft validated，生产 phases 依照只读合同 skipped；未创建 `render-A0002/build`，manifest SHA-256 前后均为 `25e4b0a7879bd9c963d093234e5a449330da36fe1ec27e86dfddc2bf7b7f439c`，`signoff_recorded=false`。完整计划 stdout/stderr/receipt 在外置 `composer-prep-A0001/native-plan-A0002/`。计划通过只证明 composition 可执行；最终 build、编码后媒体核验、review 和交付由主执行者继续。
