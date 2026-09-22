# 连续实机片段接入 produce / composer

新 attempt 可追加 `--capture-spec`，其合同见 [实机导入接口](README.capture-media-draft.md)：

```text
tools\.venv\Scripts\python.exe -m war_ai_promo.produce --project promo/ck3_native_war_ai --inputs D:/film/NEW-SPEECH/production-inputs.json --capture-spec D:/film/NEW-SELECTION/capture-clips.json --run-root D:/film/NEW-MIXED-RUN --run-id NEW-MIXED-RUN
```

这些路径必须换成实际输入和全新输出。本入口不启动 CK3，不录制，不上传；它只复用已经通过 adapter 验证的 capture bundle。`evidence_role` 与 `claim_ids` 为编辑归属，不能自动证明原生 AI 因果。

`produce` 先保全原音频和文档，在新 run 内准备片段；通过真实 `xar-promo preserve` 保全原始 raw 一次、控制证据、导出片段、receipt 与全部过程审计。随后将每条选择写到对应 cue 的 `capture_clip`，冻结新的 `selected-production-inputs.json`，`media_scope` 标为 `mixed-footage`。失败的准备过程和时长冲突同样保留并封存，不能改成成功。

`composer` 对映射 cue 只读取 run 中已保全的媒体与 receipt，不再次依赖原 bundle 路径。其他 cue 继续图解。没有 `--capture-spec` 的新 run 保持旧 `teaching-graphics-radio-cut` 模式；已有历史 run、旧输入和旧导演稿不改写。新 attempt 文档来源固定为 `longform/director-plan-v3.md`，同时保全新主张台账。

片段与 cue 计划段长只允许最多一帧的整帧对齐差；采用真实片段的帧数时长，而且必须覆盖完整实测 speech。较大差异或音频越出都直接失败，应重选片段或调整旁白。不会循环录像、定格最后一帧、插帧、裁去口播或变速填满。字幕按最终段长生成。

正式工具链 0.2.1 的默认 renderer 含 `fps` 和 `tpad`。项目通过受支持的 `render_planner` 接缝，仅对实机来源移除这两段，保留官方字幕、音频、编码及审计流程，并明确使用 `fps_mode=passthrough`。上游图结构改变时拒绝猜测处理；旧图解仍使用默认 planner。

原始 CFR/VFR 已由导入器按真实 PTS、1×时间轴准备成30fps交付片；composer不再次补尾或改速。
v2 receipt 的 `source_sampling_quality` 随 visual metadata 保留，输出30fps不提升原片运动观测分辨率。
该兼容不改变暂停地图producer的同日期范围，也不取消案例因果、端点视觉审阅或人工签核边界。

20–40 分钟继续是编辑工作范围，不构成新硬时长门；`--full-film` 仍要求配置中的章节完整。真实实机覆盖、案例因果和人工审片由独立交付记录说明，`mixed-footage` 本身不是整片完成或内容批准。

聚焦测试只渲染0.8秒合成片段及字幕/合成音频，另测混合/旧模式、时长冲突保全、cue/claim 映射拒绝。capture adapter 的成功投影与 preserve 回调是明确的合成夹具，不冒充 GREEN CK3 或正式 lifecycle 成片：

```text
tools\.venv\Scripts\python.exe -B promo/ck3_native_war_ai/integration/test_capture_integration.py --artifact-root D:/workspace/ck3_native_war_ai_promo_work/capture-integration-SYNTHETIC-NEW
```

首次证据目录为 `D:/workspace/ck3_native_war_ai_promo_work/capture-integration-synthetic-20260923-r1`；实际结果以该目录 `result.json` 为准，失败过程不清理。
