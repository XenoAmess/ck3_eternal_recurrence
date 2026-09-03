# 天朝二期宣传工具复核（2026-09-03）

本次复核针对两条二期成片共用的宣传工具链，不启动 CK3、不生成或伪造 gameplay 素材。

## 结果

- 独立 fresh clone：`Z:\\ck3_mod_rewrite\\_runtime\\promo-tool-fresh-20260903`
- `HEAD`：`57c42fca13ea459432c1caf76e069a1fbccf602c`
- `origin/main`：`57c42fca13ea459432c1caf76e069a1fbccf602c`
- 工作树：clean
- 安装包版本：`xar-promo-toolchain 0.2.1`
- 全量单元测试：`263 passed, 2 skipped`（2026-09-03）
- 仓库侧接入测试：`test_promo_toolchain_loader.py`、`test_zhongguo_phase2_promo_runner_plumbing.py`、`test_plan_zhongguo_phase2_final_promo.py` 均通过

## 当前可交付物

两条导演线的 project config、authoring claims、字幕文本、旁白 cue、剪辑顺序和 runbook 均已落盘；工具链版本门槛已闭合。两条 runbook 当前都诚实标记为 `RED / footage_pending`，因为八段真实 CK3 clean span 还没有完成 intake。

工具链通过并不等于成片已经生成。TTS、字幕媒体渲染、FFmpeg 和 MP4 导出必须在真实素材与对应的 lineage receipt 到齐后执行；不得用静态截图、旧版 smoke 视频或 fixture 冒充二期 gameplay。

## 解锁后的并行顺序

1. CK3 正式实机取得同一 seed 的八段 clean span，并写入 footage intake。
2. 人物线、制度群像线分别绑定各自 project config，生成 TTS、双语字幕和静态卡。
3. 两条线分别构建候选 MP4、跑 ffprobe/claims audit，并进行独立人工审片。
4. 各自导出、保存 SHA-256；任一条线不得替另一条线签核。
