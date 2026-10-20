# E04 军队人数变化：130 秒组合审阅章

`machine_id: desktop-3fevhd2-1c74096080`；实际产出与自动 QA 于 2026-10-20 UTC。本包把 R194/R196 55 秒章、R211 27 秒、R215 21 秒和 R217 27 秒既有候选顺接为一个可直接审阅文件。四段来自独立回放；新组合增加可审章节，不增加原始取材时长、研究通过数、正式动态或 A/B/C 信用。

本机视频为 `C:/ck3-e04-resume-20261020-a01/media/work-a01/E04-ARMY-OBSERVATIONS-130s-REVIEW-DRAFT-a01.mp4`，12,222,689 B，SHA-256 `74480cf62a07bcf18fc86c16a0ccc6a7554b4a835c179c4b4d68c405143b0d00`。容器 130.052083 秒，3899 帧，1920×1080，名义 30fps，AAC 48kHz 双声道，带四段章节导航。AAC 尾部时长使接缝有不足一帧的时间偏移，不声称新文件处处落在恒定帧网格。

新文件一次严格全 AV 解码通过；视频/音频包 DTS 严格递增，全部视频帧保留。三处拼接最大视频 PTS 间隔 0.054688 秒，最大音频包间隔 0.021334 秒。八张新文件章节首尾帧经 AI 直接审阅，研究边界卡可读。连续 clean、完整人工 1× 和 human signoff 均未完成；正式动态仍 0/11，A/B/C 仍 0/3，未上传。

新 run 查询官方最新正式 Release 为 xar-promo-toolchain v0.3.0；wheel SHA-256 `f59c4b62b89297e2ff7bb7df4354fc88c6447fa6b1b7eade28de2bc1e6dc974c`。实际使用主工作树 `tools/.venv/Scripts/python.exe`，依赖与 CLI help 均见 `INTAKE.actual.json`。独立 skill 实际路径为 `D:/workspace/xar_promo_toolchain/codex-skill/promo-video-pipeline/SKILL.md`。通过公开 `plan_concat`/`execute_render_plan` 拼接，再按 skill 的外部产物路径用原生 CLI start-run/preserve/validate 登记；没有声称执行 native build 或 generic audit。

未生成 TTS、未重编码视频、未修改旧字幕音轨、未复制或解码旧原片，也未重做旧四件候选的已过 QA。只对四件小成品执行一次 SHA/流元数据输入检查。机器路径是本次出处；其他机器须重新绑定实际素材、解释器、Release 与容量。

`DELIVERY.actual.json` 给出最终路径、精确输入、QA、原生 manifest 和保留期限；`qa-a01/pending-review/review-template.json` 保持 pending。自动 QA 与 AI 稀疏帧观察不能替代完整人工观看或签核。
