# H2743 部分休战输入：精确 DLL 只读准入

状态：**静态准入 GREEN，未启动 CK3，未取得新 DLL 的 H2743 实机读数。** 本页只为 [部分休战输入候选](h2743-dejure-partial-truce-input-native-candidate-2026-09-28.md)接上受管只读运行单；旧 [attempt-11](h2743-defender-dejure-readonly-attempt-11-2026-09-28.md)仍是旧 title-prestate DLL 的历史回执，不能追认三个新布尔。

`run_h2743_dejure_readonly_v3.py` 新增显式 `--candidate partial-truce-inputs-v4`。它精确绑定外置 `build-truce-inputs-002/xar_ck3_bridge.dll` SHA-256 `1361FC0991D1FA09CB7272112D73F7F50736B7BBAD6A3656C33F9FB200CA1BAA`，源 save、driver、family sidecar、源 DLL、injector 与 CK3 EXE 的原有 SHA 门不变。省略 `--candidate` 时仍绑定旧 `build-title-prestate-001` DLL SHA `6689ED3B3EB40F33157B028BD7067FF859F1C6ACDCFC02EDEB92A7D0F271B17E`。两者均只允许两种只读查询：`query-defender-de-jure-exit-terms-v1-16777231`、`query-war-termination-options-16777231`；没有终战或日期推进指令。

新 `ready-summary.json` 和 `source-pair.json` 写入 `candidate_kind` 及 DLL SHA。运行阶段必须同时匹配二者；没有 `candidate_kind` 的旧 READY 只可按旧候选解释，无法供 v4 复用。v4 live 输出使用新目录名 `live-dejure-partial-truce-v4/`，保留所有失败 attempt；两次同帧 baseline 必须都有完整 typed `truce_inputs_v1`，其三项可观察布尔、`nomad_both` 关系及三个固定未知条件由既有 wire 规范校验。任何休战天数、到期日、`directed_truce` 或 action 字面量出现，都拒绝本次只读结果。查询前后仍要求同一 paused frame、同一完整战争签名、加载模块路径与磁盘 SHA、清洁退出和原件后哈希。

占屏执行者须先按 [v3 受管运行单](h2743-dejure-readonly-live-v3-runbook-2026-09-28.md)取得当次独占 `ck3-screen`、真实新鲜 Steam 离线画面和人工审阅回执；当前 H3911→E2 屏幕队列优先，须等任务总线实际释放。只读静态准入命令：

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\run_h2743_dejure_readonly_v3.py --candidate partial-truce-inputs-v4 --check-static
```

取得屏幕后只能用**新的** `attempt-N-dejure-baseline-no-launch` 先执行 `--candidate partial-truce-inputs-v4 --prepare-no-launch --attempt-name <new-name> --task-id <exclusive-owner>`，审阅新 Steam gate 后再用同一个 `--candidate partial-truce-inputs-v4 --run --prepared-attempt <new-attempt> --steam-gate <new-gate> --task-id <exclusive-owner>`。准备、实机或清理失败时保留该 attempt，换新编号；不得覆盖旧记录。

本次无屏幕验证：候选 DLL 与旧 DLL 的磁盘 SHA 独立复核；`--candidate partial-truce-inputs-v4 --check-static` 完整校验源四件、候选 DLL、injector、EXE、解释器依赖和 CLI help，结果为 `static_bytes_verified_no_launch`；runner 单测普通与 `-O` 各 11/11 GREEN。测试覆盖新旧候选选择、旧 READY 拒绝、缺失/污染部分 wire、错误推高条款及原有进程清理门。以上不构成 live 布尔、投降后 title／封臣／资源 delta、休战期限、续战风险或退出动作闭环。
