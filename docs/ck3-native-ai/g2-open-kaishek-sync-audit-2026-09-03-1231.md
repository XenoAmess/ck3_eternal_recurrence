# G2/open_kaishek 伴随同步审计（2026-09-03 12:32，Asia/Shanghai）

## 2026-09-04 伴随更新

本记录后续已推进到 `open_kaishek`
`135113d3c1426a9d8f0c8c7d8368e3d525ab0d3b`。这次存在一个真实但有限的
T0 同步缺口：B3 manager-governance 的 native mailbox、driver、service 和
MCP capability 已形成固定公开合同，而 open_kaishek 尚无相应 capability
描述。远端 main 已补入只读、hash-bound、未认证的
`ZhongguoManagerGovernanceCapabilityProfile`；parser、opcode profile、IR、
runtime 和 CLI 均未扩张。

root 的 G2 capability/profile/字段/不变量没有变化，仅将 exact repository pin
更新为上述提交。focused verifier 在 external
`HEAD == origin/main == 135113d3...` 且 clean 时为 `GREEN_STATIC`；
`native_certified=false`、`runtime_certified=false`、public readiness=false
保持不变。以下 2026-09-03 段落保留当时 `15ab978` 审计的历史上下文。

## 结论

本次只读审计判定 T0（天朝二期）和 T1（G2）近期没有改变
`open_kaishek` 所依赖的公开接口，因此没有新增代码修补。root 的 G2
canonical pin、外部 checkout 和 `open_kaishek` 远端主线均指向
`15ab978f879ed4562aacb74dacdaee702fbce54b`；跨仓合同审计为
`GREEN_STATIC`。

这里的 GREEN 只表示静态身份/合同一致，不表示 CK3 原生或 runtime
能力已经认证。

## 变更范围核对

root 的上一版 pin 为 `e4e8b6f`。从该提交到本次审计观察到的 root
`HEAD=5285d3297c5bd3c004a79802bb4c997255bc7eb8`，近期 Phase2 提交
（`5f47215`、`2d0dbad`、`29c759e`、`9064f48`、`5285d32`）只涉及
产品 projection、bootstrap/依赖扫描和证据文档；没有修改下列 G2/
open_kaishek 合同或桥接源：

- `ck3_autonomous_player/src/xar_autoplayer/bridge/`
- `ck3_autonomous_player/native_bridge/`
- `tools/kaishek_preflight.py`

Phase2 runner 的 projection 参数调整没有改变 open_kaishek CLI 的
schema、profile ID、capability ID 或 G2 wire 字段，因此判定为
`NO-CHANGE`，不重复制造 adapter 提交。

外部 `open_kaishek` 从 `981c793` 到 `15ab978` 的增量仅加入 activity-type
schema 的显式负夹具、测试、CLI 注册和边界文档；既有
`G2TruceEvaluatorCapabilityProfile`、`Ck3Profile11906` 和 truce capability
合同保持不变。该增量补充了真实的 activity `UNKNOWN_OPCODE` 覆盖缺口，
但没有把它误报为 runtime capability。

## 可复现审计

执行环境：

- root：`Z:\ck3_mod_rewrite\_root-promo-split-20260902`
- open_kaishek：`Z:\workspace\open_kaishek`（clean）
- open_kaishek `HEAD == origin/main`：
  `15ab978f879ed4562aacb74dacdaee702fbce54b`
- CK3 profile：`1.19.0.6`
- CK3 EXE SHA-256：
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- shaded CLI JAR SHA-256：
  `FC85947E9976B80345C10A9789A6520C8ABCEF557365284570C18C4677D891CC`

```powershell
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' `
  'ck3_autonomous_player/native_bridge/research/verify_g2_open_kaishek_compatibility.py' `
  --checkout 'Z:\workspace\open_kaishek' --require-checkout --require-clean
```

结果：`status=GREEN_STATIC`、`ok=true`；root capability/profile/commit、
open_kaishek source、`HEAD`、`origin/main`、CK3 build identity 全部匹配。
root targeted contract tests 为 `11 passed, 12 subtests passed`。

activity 负夹具仍按设计返回 parser `GREEN`、validator `RED`（五个
`UNKNOWN_OPCODE`），IR/runtime `SKIPPED`；这是 schema coverage 的已知
边界，不是 truce 合同回归。

## 边界与后续触发条件

本次仅读取源码、Git refs 和静态测试结果：`ck3_started=false`、
`process_attached=false`、`save_mutated=false`、`mutation_sent=false`，
没有购买/付款/商店动作。`native_certified=false`、
`runtime_certified=false` 保持不变。

只有当 T0/T1 后续实际改变 capability ID、profile/version、公开字段、
CLI 参数或调用时序时，才需要再次修改 adapter/profile/fixture；届时先
重跑同一只读审计，再做最小兼容性补丁。
