# 天朝二期双片制作包（2026-09-03）

这份制作包把两条正式成片路线分别登记下来。两条片都要做、都要单独审片、都要单独导出；任何一条都不能替另一条签核。

## 人物版

- 导演稿：[phase2-character-director-treatment.md](phase2-character-director-treatment.md)
- 项目配置：`mod_zhongguo_style/promo/phase2-promo-character-project.json`
- 目标文件：`artifacts/demos/2026-09-03/zhongguo-361-phase2-character-led.mp4`
- 当前状态：`authoring-ready`；二期真实 CK3 素材 `0/8`；未生成 MP4
- 本次 runbook：`Z:\ck3_mod_rewrite\_runtime\phase2-dual-runbooks-20260903-0800\character-runbook.json`
- runbook 结果：`RED / footage_pending`（SHA-256 `55E2751FBC8408682B04251C3706928A2C78B9B70F61D11D3D6C829DC572E408`）

## 制度群像版

- 导演稿：[phase2-institution-director-treatment.md](phase2-institution-director-treatment.md)
- 项目配置：`mod_zhongguo_style/promo/phase2-promo-institution-project.json`
- 目标文件：`artifacts/demos/2026-09-03/zhongguo-361-phase2-institution-led.mp4`
- 当前状态：`authoring-ready`；二期真实 CK3 素材 `0/8`；未生成 MP4
- 本次 runbook：`Z:\ck3_mod_rewrite\_runtime\phase2-dual-runbooks-20260903-0800\institution-runbook.json`
- runbook 结果：`RED / footage_pending`（SHA-256 `6A3FD533B0656722CF8296224A286586F5AF8B568ECDA6C7B9B3A157007BF2BF`）

## 已满足的制作前置

- 宣传工具已在可写 fresh clone 更新并核对到 `origin/main`：`57c42fca13ea459432c1caf76e069a1fbccf602c`。
- 两份 authoring claims 均通过静态验证：每份 10 个章节、8/8 gameplay cues 绑定到未来真实 clean spans。
- 两份 runbook 已分开生成，使用独立 work/run 身份；没有共享审片结论或媒体哈希。

## 当前硬阻塞与解锁后顺序

当前尚未产生可入片素材：自动化运行有的到过 `Frontend`/`In Game` 后在 bridge/采集器收尾阶段 RED，另有无 mod、无 bridge 裸跑在 9 月 3 日约 05:46 于 pre-loader 崩溃。两类结果都不能满足八段 clean-span 合同，也不能概括为“CK3 一直打不开”。阻塞证据见
[live-startup-blocker-2026-09-03.md](live-startup-blocker-2026-09-03.md) 与
[manual-vs-automated-launch-diagnosis-2026-09-03.md](manual-vs-automated-launch-diagnosis-2026-09-03.md)。解锁后按以下顺序执行：

1. 取得同一 seed/save lineage 的 8 段真实 CK3 clean spans，并完成 footage intake。
2. 人物版与制度群像版分别做具名 source review、TTS、双语字幕、候选片和 claims audit。
3. 两版分别完成全长 `1×` 人工审片、sign-off、export，并把实际时长、编码、路径和 SHA-256 回填到本目录状态索引。

素材一旦齐备，预计采集与 intake 约 20–40 分钟；每版候选制作约 45–90 分钟，另加两轮人工审片。当前不把该时间写成固定交付承诺，因为 CK3 启动仍未恢复。
