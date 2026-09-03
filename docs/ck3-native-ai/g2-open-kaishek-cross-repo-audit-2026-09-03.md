# G2/open_kaishek 跨仓静态兼容审计（2026-09-03）

## 结论

新增了一个可重复的只读审计器，检查 root 的 G2 truce 描述性常量、
open_kaishek 的 Java capability/profile 源码，以及外部仓库的
`HEAD` / `origin/main`。本次检查结果为 **GREEN_STATIC**：

- capability：`game.command.query-g2-truce-evaluated-days-v1`
- profile：`ck3-1.19.0.6-g2-truce-evaluator-v1`
- open_kaishek：`HEAD == origin/main == 981c79388a07e447b18f8e4472a16fd65e28c083`
- CK3：`1.19.0.6`，EXE SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- capability 仍为只读、确定性描述，`nativeCertified=false`、
  `runtimeCertified=false`。

这只是静态兼容性闭环，不是 CK3 实机结果，也没有把 `evaluated_days`
提升为 production-live。

## 可复现命令与证据

```powershell
& "tools\.venv\Scripts\python.exe" `
  "ck3_autonomous_player/native_bridge/research/verify_g2_open_kaishek_compatibility.py" `
  --checkout "Z:\workspace\open_kaishek" `
  --require-checkout --require-clean `
  --output "artifacts/g2-open-kaishek-compatibility/2026-09-03/audit.json"
```

审计回执：
[`artifacts/g2-open-kaishek-compatibility/2026-09-03/audit.json`](../../artifacts/g2-open-kaishek-compatibility/2026-09-03/audit.json)

本次回执 SHA-256 为
`947EF90CCD968C646CAE881D75986829549D647514C543347A1404C9ED1EA81C`。
root 单元测试为 `4 passed`；`-O` 优化模式同样为 `4 passed`（仅有 pytest
缓存目录权限 warning）。

## 边界与后续

审计器只读源文件和 Git ref，不启动或附加 CK3，不加载存档，不提交输入/命令，
不修改 Paradox opcode 或 allow-list。若外部 checkout 不存在，默认结果会明确标为
`GREEN_STATIC_NO_CHECKOUT`；传入 `--require-checkout` 时则 fail-closed。

只有取得同一 exact-build、paused 的 evaluator 双读 artifact 后，才可评估
`native/runtime` 认证或新增 production projector；在此之前继续保持现有
fail-closed 边界。
