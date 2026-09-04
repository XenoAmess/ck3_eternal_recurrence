# G2 `evaluated_days` capture-entry review (2026-09-03)

## 结论

本次只做了 exact-build、root/open_kaishek pin 和现有 paused artifact 的只读复核，
没有启动 CK3、附加进程、执行游戏效果或修改 public bridge/readiness。结论是：
当前没有一个同时满足“当前 pin + paused + 能返回 evaluator 结果”的可用入口。
下一次施工应是一次独立的、单槽的 private evaluator capture；在启动环境恢复前不执行该槽。

机器可读的缺口与操作清单在
[`evaluated-days-capture-entry-gap-20260903T1325.json`](../../artifacts/g2-open-kaishek-compatibility/2026-09-03/evaluated-days-capture-entry-gap-20260903T1325.json)。

## 这次复核确认了什么

当前 root fixture 固定 capability
`game.command.query-g2-truce-evaluated-days-v1`、profile
`ck3-1.19.0.6-g2-truce-evaluator-v1` 和 `open_kaishek`
`15ab978f879ed4562aacb74dacdaee702fbce54b`。外部 checkout 的
`HEAD == origin/main` 且工作树干净；JAR SHA-256 为
`FC85947E9976B80345C10A9789A6520C8ABCEF557365284570C18C4677D891CC`。
这只是静态兼容性身份，`native_certified=false`、`runtime_certified=false`。

对 CK3 `1.19.0.6`（EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`）运行现有
call-site verifier，结果为：

```text
PASS: exact_build=1 evaluator=1 call_sites=2 read_only=1
```

静态 ABI 没有发现可替换的“另一个 offset”：evaluator 是
`0x3373000`，签名是三个 MSVC x64 参数，两个直接 CAddTruce callsite 都是
`RCX=[RSI+0x108]`、`RDX=effect_context`、`R8=*(effect_context+0x28)`，返回值是
`EAX` 中的有符号 `int32`。这确认了调用约定，但不等于运行时已经读到天数。

## 为什么现有入口都不够

1. 最新暂停 terms 报告
   `g2-fresh-semantic-ready-20260902T100431236/report.json`（SHA-256
   `4A7C66D34C851698572F4BBA2970ECAA00C005C2DC338ABCD75A7FD304F0B991`）确实在
   `native:3 / rev4 / native_rev3`、CharacterID `29829`、WarID `50331699`、
   `date_raw=53223936` 上完成了两次相同的只读查询；但
   `evaluated_days_observable=false`、`evaluated_days=null`，expiry 也仍是
   `false/null`。所以这是 paused 证据，不是 evaluator 成功证据。
2. 被冻结的 passive callsite observer
   `g2-native-callsite-observer-ready-20260903T003347` 能安全观察 native 调用，
   但它是 heartbeat-only，关闭 direct evaluator、MCP 和 mutation。它的唯一 live
   结果（报告 SHA-256
   `1F319AE1F9D947D1BC766E304E8329CEE80E845B35833E45A2BB6F6E1DEB0AC9`）是
   `NO-GO/no_native_callsite_hit`：两个 callsite 的 pre/post 计数都为零。暂停且不提交
   终止效果时，slot-22 本来就不会被调度；零计数不能冒充天数。
3. 旧的 index-7 shape capture 确认了输入形状，但没有确认结果。它在两条相同的
   私有行中看到 Truce vtable `0x4461CA8` 和 `truce_effect+0x108`，同时明确记录
   `duration_evaluator_called=false`、`evaluated_days_observed=false`。这证明下一次
   观察可以沿已证实的对象路径走，不需要猜 offset；该 artifact 仍绑定旧的
   `open_kaishek=0390b9a...`，不能当作当前 pin 的认证。
4. 旧的 direct evaluator candidate
   `g2-index7-eval-context-fix-ready-20260902T2219` 绑定的是
   `open_kaishek=0390b9a...`，而当前 pin 已是 `15ab978...`，因此不能复用。它的历史
   单次运行虽然写下了精确 index-7 Truce 和 `+0x108` 输入，但在第一次 evaluator 调用
   前进程退出（`RED_NATIVE_PROCESS_EXIT_DURING_FIRST_EVALUATOR_CALL`，报告 SHA-256
   `1A238BFE5194CE94E9C3CB784360E98E9A99EF758D0802D33478F52DC91C45AC`），完成调用数为
   `0`，没有 `evaluated_days`。

因此目前的判定是 `NO_CURRENT_USABLE_PAUSED_EVALUATOR_ENTRY`，不是“找到了新的
offset”，也不是可以把 readiness 打开的理由。

## 下一次单槽怎么做

启动环境恢复后，按 JSON 清单逐项执行：

1. 先对当前 root/open_kaishek 做静态兼容性核对和 OfflinePreflight，并把 JSON/SHA
   一起冻结；任何 pin、EXE、checkpoint、driver-state 或 source hash 不一致都在启动前
   结束。
2. 从当前 source 重新构建一个 private direct-capture DLL。默认构建仍必须
   `XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1=OFF`；只在候选构建打开它，且不能和
   passive observer 组合。已经由 exact-build 证据确认的 `0x108`/`0x28` 只能原样使用，
   不得擅自替换。
3. 只保留一个新 attempt 目录和一个 bridge DLL 槽。通过现有 terms runner 做两次只读
   查询，sidecar 记录 `pre_call`、两次 `post_call` 和 cleanup；不发送 Context、投降、
   白和、强索、推进时间或商店动作。
4. 只有在同一 paused frame 上拿到两个相等、非负的 evaluator 返回值，并同时满足
   index-7 Truce vtable `0x4461CA8`、`+0x108`、RVA `0x3373000` 和 session/frame 身份
   一致时，才可把 artifact 交给后续 readiness 审查。
5. 若再次在首次调用前退出、没有返回、或 hash/身份不符，保留完整 RED，不重复同一
   checkpoint，不改 public wire/readiness，也不从天数推 expiry。

完整逐步条件、命令模板和失败处理见 JSON artifact；本次 review 本身的
`run_authorized=false`，因此没有消耗 CK3 启动槽。

## 测试与 readiness 边界

- `verify_raiktor_truce_evaluator_callsite_v1.py`：PASS（exact build、evaluator、两个
  callsite、read-only）。
- `verify_g2_open_kaishek_compatibility.py --checkout Z:\\workspace\\open_kaishek
  --require-checkout --require-clean`：`GREEN_STATIC`，`ok=true`。
- 本次没有修改 capability、profile、wire 字段、offset、allow-list 或 readiness；
  `native_certified=false`、`runtime_certified=false`、`truce_ready=false`、
  `decision_ready=false`、`GEN-034=unresolved` 保持不变。
- 运行结果和逐步清单的固定副本：
  [`evaluated-days-capture-entry-gap-20260903T1325.json`](../../artifacts/g2-open-kaishek-compatibility/2026-09-03/evaluated-days-capture-entry-gap-20260903T1325.json)。

## 2026-09-04：private result 的确定性收口器

[static-ready / no launch] 新增
`native_bridge/research/analyze_g2_evaluated_days_private_capture.py`，用于在下一次独占实机槽结束后，
把 shared terms runner 的报告与 private JSONL 合并判定。这样不会再要求人工从 runner 的公开 RED 中猜测 private
evaluator 是否已经返回：private reader 会在公开结果序列化前有意 reset，因此“公开 runner RED、private evaluator
GREEN”是合法且必须被显式识别的组合。

收口器只接受两次同一 paused frame 的公开查询，以及每次严格连续的四行 private 证据：
`pre_call → post_call_1 → post_call_2 → capture.v3 summary`。每组都必须保持 exact index-7 路径、
Truce vtable `0x4461CA8`、对象 `+0x108` duration、evaluator `0x3373000`、非空 context、
`0→1→2` completed-call progression、两次相等非负返回及完成态 summary；两组的最终天数还必须相等。
runner 侧仍要求 exact-build、两条只读 query、身份/同帧/normalized payload equality、零 mutation、零 time advance、
cleanup 与 source invariant 全部成立。

输出只把 `private_evaluated_days_evidence` 标为 true；`public_wire_promoted`、
`actual_expiry_observable`、`decision_ready`、`automatic_surrender_ready` 与 `gen034_closed` 固定保持 false。
因此它是下一次 current-pin candidate 的验收消费者，不是 public readiness 提升。合成 GREEN、首次调用前退出、
返回不等、跨 query 漂移、指针偏移错误、mutation/frame drift、malformed JSONL 与 no-launch source boundary 共
8 个定向测试已通过；本包没有启动 CK3、附加进程或修改游戏状态。
