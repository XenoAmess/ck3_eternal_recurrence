# 天朝二期静态交付检查点（2026-09-03 09:23）

本检查点记录一次不启动 CK3 的 T0 继续施工。它验证制作链和发布树是否可继续使用，**不把静态 GREEN 写成实机 live，也不生成 TTS、FFmpeg 或占位 MP4**。

## 已确认

### 宣传工具 freshness

在可写 fresh checkout `Z:\ck3_mod_rewrite\_runtime\promo-tool-fresh-20260903` 执行：

```powershell
git -c safe.directory="Z:\ck3_mod_rewrite\_runtime\promo-tool-fresh-20260903" `
  -C "Z:\ck3_mod_rewrite\_runtime\promo-tool-fresh-20260903" fetch origin main --prune
```

结果：

- `HEAD = 57c42fca13ea459432c1caf76e069a1fbccf602c`
- `origin/main = 57c42fca13ea459432c1caf76e069a1fbccf602c`
- checkout 状态：`CLEAN`

因此，在真实素材到齐后开始 TTS/渲染前，宣传工具更新门已经满足；正式制作仍需再次绑定当时的 tool-head receipt。

### 二期与发布树校验

使用项目共享 Python 环境执行：

```text
tools/test_plan_zhongguo_phase2_final_promo.py
tools/test_zhongguo_phase2_promo_producer.py
tools/test_zhongguo_phase2_footage_intake.py
tools/test_zhongguo_phase2_final_promo_completion.py
tools/test_zhongguo_phase2_dual_cut_completion.py
tools/test_zhongguo_phase2_capture_choreography.py
tools/test_zhongguo_phase2_promo_runner_plumbing.py
```

结果：`78 passed, 36 subtests passed`。唯一警告是工作区 `.pytest_cache` ACL，未影响断言。

随后补跑 `tools/test_zhongguo_phase2_*.py` 的完整二期静态测试集合（15 个模块，覆盖业务后置条件、事件编排、provider packet、发布目标、source checkpoint、视觉处理和 workforce action）：`130 passed, 67 subtests passed`；同一 `.pytest_cache` ACL 警告仍不影响断言。

随后执行 `tools/validate_static.py`、`tools/build_release.py --check` 和
`tools/build_vivhite_release.py --check`，结果分别为：

- `STATIC VALIDATION OK`（40 option keys、5 custom loc、88 modifiers、9 languages）；
- 原版 release check GREEN，`86 files`，deterministic manifest/ZIP；
- 白绮独立版 release check GREEN，`27 files`。

## 尚未修好的部分

两条正式片（人物版、制度群像版）仍各为 `footage 0/8`，目标 MP4 不存在。CK3 启动/采集边界仍需在稳定桌面会话取得八段真实 clean spans；本检查点没有尝试再次启动 CK3，也没有把旧 fixture 升格为二期素材。

## 结论

可以继续推进：T0 的导演稿、双 cut 配置、authoring ledger、runbook、工具 freshness 和静态发布链均已可用。当前未完成的是实机素材及其后续两条独立 TTS、候选、审片、导出和哈希回执，而不是静态制作脚本故障。
