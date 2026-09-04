# G2 `evaluated_days` capture-entry review (2026-09-03)

> 2026-09-04 companion pin update: canonical open_kaishek main is now
> `135113d3c1426a9d8f0c8c7d8368e3d525ab0d3b`. The advance adds only the
> static B3 manager-governance capability descriptor; the G2 truce capability,
> fields, invariants, and false native/runtime certification are unchanged.
> References below to `15ab978` remain the immutable identity of the already
> executed current-pin r1 candidate and its archived evidence.

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
8 个逻辑定向测试与 1 个 frozen-candidate evidence contract 已通过；本包没有启动 CK3、附加进程或修改游戏状态。

同一包随后从干净 `6145be50a1666c2392dd23edef7779507c3043d4` 构建了 current-pin Release
候选与 default-OFF control。`open_kaishek` 保持 clean 且
`HEAD == origin/main == 15ab978f879ed4562aacb74dacdaee702fbce54b`，兼容性 verifier 为
`GREEN_STATIC`；exact-build evaluator verifier 仍为
`PASS: exact_build=1 evaluator=1 call_sites=2 read_only=1`。private DLL 包含 v3 summary 与 durable
boundary 两个标记，default DLL 两者均不包含；private/default native fixture、private game-access fixture
全部 GREEN。冻结目录为
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-evaluated-days-current-pin-20260904T1200\frozen`，
private DLL / injector / source ZIP SHA-256 分别为
`98F9F82E…E754C / 42452C6C…5B627 / A436EF40…F715`。完整尺寸、哈希、测试与
readiness 边界见
[`evaluated-days-current-pin-static-ready.json`](../../artifacts/g2/2026-09-04/evaluated-days-current-pin-static-ready.json)。
该 candidate 目前仅为 `STATIC_READY_NO_LAUNCH`：没有 CK3、profile、attach 或 mutation；下一动作仍是独占
CK3 槽内的一次双 query capture，再用上述收口器判定，不能仅凭本静态构建提升 runtime certification。

## 2026-09-04：current-pin 单槽 preflight

[static-ready / no launch] 新增机器可读 manifest
`native_bridge/research/fixtures/g2_evaluated_days_current_pin_live_manifest.json` 与 no-launch preflight
`native_bridge/research/prepare_g2_evaluated_days_current_pin_capture.py`。manifest 冻结 candidate source、
checkpoint/driver、CK3 EXE、private/default build、Open Kaishek jar、两次只读 query、private capture
shape 及其 SHA-256；preflight 在创建 profile 或启动/附加进程前复核这些输入、exact-build evaluator bytes、
build option、private/default marker、driver identity、Open Kaishek current pin、fresh attempt 以及 CK3 独占槽。

第一次 preflight 只因当时已有一个 `ck3.exe` 占用独占槽而 RED；没有停止、附加或干预该进程。槽释放后使用
新报告名复跑得到 `ready-to-run`：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe -B ck3_autonomous_player/native_bridge/research/prepare_g2_evaluated_days_current_pin_capture.py --report Z:\ck3_mod_rewrite_process_assets\zg361\g2-evaluated-days-current-pin-20260904T1200\preflight-current-pin-r2.json
```

报告 SHA-256 为
`E364750DF68022062238BD7BB3568645D223ADD3E2711997DC5E4E5E0A7751EC`；其中全部 input/source hash、
private/default build contract、driver anchor、exact evaluator、Open Kaishek 静态兼容、空独占槽与 fresh attempt
检查均为 true。报告给出唯一 PowerShell 命令：按 manifest 指向的同一 frozen checkpoint 启动 shared runner，
只发两次 `query-war-termination-terms-v1-50331699`，随后无论 public runner 是否 RED 都执行 private analyzer。
未来 attempt 固定为
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-evaluated-days-current-pin-20260904T1200\live-current-pin-dual-query-r1`。

该 GREEN 只证明下一次独占槽输入已经就绪；本次仍未启动 CK3、未创建 profile、未附加进程，也没有 live
evaluator result。`native_certified=false`、`runtime_certified=false`、public wire/readiness、expiry、决策、
自动投降与 `GEN-034=unresolved` 均保持不变。

## 2026-09-04：current-pin live r1 RED 取证

[production-live primitive / capability RED] 独占槽 r1 已经到达 exact-build paused readiness：
`native:3 / rev4 / native_rev3`、CharacterID `29829`、WarID `50331699`、
`date_raw=53223936` 均吻合，runner 也进入了第一条
`query-war-termination-terms-v1-50331699`。因此启动、冷 checkpoint 投影、身份绑定和进入查询的
harness 链已经工作；这次失败不是 harness RED。

private JSONL 确实产生，但只有一行 durable `pre_call`（SHA-256
`FC7BB45C…8FA9F`）：exact index-7 路径、Truce vtable `0x4461CA8`、duration
`truce+0x108`、evaluator `0x3373000` 与非空 context 均已写盘，
`completed_call_count=0`，没有任何 `post_call_1`。随后 CK3 以 code 1 退出；crash artifact 是
`C0000005`，地址 `0x7FF7EDBCC668`，由 minidump 的 CK3 module base
`0x7FF7EA880000` 归一化为 RVA `0x334C668`。该处指令为
`movzx eax, word ptr [r12]`，异常读取地址与异常上下文 `R12` 都是 `0x12`；同时
`RDX=RDI=0xAD2BBCC470`，等于 private row 的 effect-context，dump 中该 context 的首 qword 也为
`0x12`。这直接证明当前 direct evaluator context 仍不可用；先前把 R8 改成
`*(effect_context+0x28)` 的修复虽满足 callsite 表面 ABI，却没有补齐 evaluator 下游所需的正确 context root
或原生调用现场。现有证据尚不足以指定正确替代指针，不能靠猜 offset 修复，也不应原样重跑同一 candidate。

runner report 的顶层 `ExceptionGroup` 丢失了上述首错细节，但 session、durable boundary 和 crash dump 能形成
连续时间线。runner 最终 `shutdown_ok=true`、`tree_gone=true`、`cleanup_proven=true`、
`driver_closed=true`，原 checkpoint/driver 哈希不变；“session 没有正常 stop”与“进程树已可靠回收”是两件事。
analyzer 已据本次实证做最小修复：分别报告这两个事实，保留不完整组的 `pre_call` stage，并把该精确模式归类为
`capability_red_process_exit_during_first_evaluator_call`。修复后只读重分析为预期 RED：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe -B ck3_autonomous_player/native_bridge/research/analyze_g2_evaluated_days_private_capture.py --runner-report Z:\ck3_mod_rewrite_process_assets\zg361\g2-evaluated-days-current-pin-20260904T1200\live-current-pin-dual-query-r1\report.json --private-jsonl Z:\ck3_mod_rewrite_process_assets\zg361\g2-evaluated-days-current-pin-20260904T1200\live-current-pin-dual-query-r1\g2-evaluated-days-private-v3.jsonl --output Z:\ck3_mod_rewrite_process_assets\zg361\g2-evaluated-days-current-pin-20260904T1200\live-current-pin-dual-query-r1\evaluated-days-private-analysis-r3.json --expected-war-id 50331699 --expected-character-id 29829 --expected-date-raw 53223936
```

重分析 SHA-256 为 `666324E9…8A4D`。完整路径、哈希、寄存器、cleanup 和边界见
[`evaluated-days-current-pin-live-r1-red.json`](../../artifacts/g2/2026-09-04/evaluated-days-current-pin-live-r1-red.json)。
下一步不是再次启动 CK3，而是先沿两个原生 CAddTruce callsite 反向闭合 R15/R12 的 context 来源，并解释
RVA `0x334C668` 为什么从当前 RDX 读到 `0x12`；只有产生新的、静态证据支持的 private-only context candidate
后才可申请下一次独占槽。当前没有 `evaluated_days` 返回；public wire/readiness、expiry、决策、自动投降和
`GEN-034=unresolved` 全部保持不变。

## 2026-09-04：R15/R12 与 `0x334C668` 静态闭环

[static-ready / no launch] exact `1.19.0.6` EXE 的反向数据流已经闭合，且否定了把
`TraverseLoadedEffect` 根 wrapper 直接交给 evaluator 的方案。两个 CAddTruce execute 实现分别在
`0x2EDAD3C` 将入参 RDX 保存到 R15、在 `0x2EDB3BC` 保存到 R12；到 evaluator 调用点时，两者都使用
`RCX=this+0x108`、`RDX=该保存值`、`R8=[同一保存值+0x28]`。真正的 RDX 来自 generic execute dispatcher
`0x3380A00`：它在自己的栈上复制 parent context 的 `+0/+8/+0x10/+0x18/+0x20`，令 child
`+0x28` 指向同栈帧的 8-byte evaluation state，再于 `0x3380CFB` 把 child 地址传给 vtable
`+0xB0`。这个 0x30-byte leaf wrapper 只在同步虚调期间有效。

r1 的 direct bridge 调用绕开了这段构造。`0x334C665` 执行 `mov r12,[rdi]`，紧接着
`0x334C668` 执行 `movzx eax,word ptr [r12]`；r1 中 RDI 等于顶层 `WarEffectContext`，其首 qword
恰为 `0x12`，所以第二条指令读取地址 `0x12` 并崩溃。这说明问题不只是 R8 的“字段地址/字段值”区别：
RDX 本身也必须是原生 leaf effect-call context。根 preview dispatcher `0x3380170` 产生的只是 root
wrapper；CAddTruce 下层实际接收的 preview leaf wrapper 由 `0x3380840` 重新复制，并令
`[child+0x28]=&stack[RSP+0x70]`，随后在 `0x3380947` 调用 vtable `+0xB8`。因此 root slot+0x58
proxy 在 forward 前尚无 leaf context，forward 返回后 leaf context 已失效，不能拿它替代。

可复现的函数 PDATA、字节段与 SHA-256 冻结在
[`g2_truce_context_lifetime_v2.json`](../../ck3_autonomous_player/native_bridge/research/g2_truce_context_lifetime_v2.json)，
由只读 extractor
[`extract_g2_truce_context_lifetime_v2.py`](../../ck3_autonomous_player/native_bridge/research/extract_g2_truce_context_lifetime_v2.py)
对 exact EXE 和已提交的 r1 RED 摘要逐项重建。关键函数哈希包括
`0x3380A00..0x3380EB1 = DE65DB5D…AA22`、
`0x3380840..0x338097B = A2BE88DE…F8DFE`，故障双指令
`4C8B27410FB70424 = 04E56C6B…88DD`。

据此新增的 V2 只在显式
`XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2=ON` 候选构建中存在，默认仍为 OFF。它让原生
preview traversal 自己走到目标 CAddTruce，并只在 `0x2E87155` leaf preview entry 的同步 hook
窗口内使用真实 RDX 及同一 wrapper 的 `[RDX+0x28]`。callback 会再次核对 exact index-7 目标对象后才做
两次 evaluator 读取，并在前后读取 paused frame；wrapper 地址不缓存、不克隆、不带出该虚调。
默认构建、public wire、readiness 与 action 路径不变。MSVC Release 全构建完成，相关 native fixture 的
Debug 断言版与 Release 版均通过；这仍只是 `static-ready` 候选，尚未取得新的 CK3 返回值。

下一次独占槽只能使用新 V2 构建和新的 manifest/preflight，仍只发送同一 paused frame 上两条
`query-war-termination-terms-v1-50331699`。旧 V1 direct DLL 与 r1 命令不得复跑。只有两组 durable
`pre_call -> post_call_1 -> post_call_2` 都出现、结果非负且相等、frame/identity/cleanup 全 GREEN，
才可把 artifact 交给 readiness 审查；在此之前 `native_certified=false`、`runtime_certified=false`、
`decision_ready=false`、`automatic_surrender_ready=false`，`GEN-034` 继续 unresolved。

## 2026-09-04：leaf-context V2 单槽前置已成立

[static-ready / no launch] 新增
[`g2_evaluated_days_leaf_context_v2_live_manifest.json`](../../ck3_autonomous_player/native_bridge/research/fixtures/g2_evaluated_days_leaf_context_v2_live_manifest.json)，
并扩充 no-launch preflight，使它能显式区分已失败的 `direct_v1` 与新的
`leaf_context_v2`。V2 合同要求 direct capture 为 OFF、leaf-context capture 为 ON，默认构建两者均为
OFF；preflight 还会从 exact EXE 与已提交的 r1 RED 摘要重新生成 context-lifetime 证据，并逐字比较冻结
JSON。因此这不是把旧 raw context 换名重跑，而是只允许由静态数据流证明的同步 leaf wrapper candidate。

V2 frozen candidate 来自 commit `39697ff157f3c3b1f8790f4395dc0bb62f908bfc`：private DLL、injector、
source ZIP 的 SHA-256 分别为 `E905197B…F5ED`、`9D3E1FEB…09B2`、`B5990115…300C`；default-OFF
DLL 为 `AB08A3AF…4EA`。open_kaishek 兼容 pin 已同步到干净主线
`135113d3c1426a9d8f0c8c7d8368e3d525ab0d3b`，其静态审计为 `GREEN_STATIC`，但 capability 中的
`native_certified=false` 与 `runtime_certified=false` 未改变。

在没有 CK3/injector 进程的前提下，V2 preflight 首次运行得到 `ready-to-run`；全部 input/source hash、
private/default build option、driver identity、exact evaluator bytes、exact leaf-context chain、open_kaishek pin、
fresh attempt 与独占槽检查均为 true。外部报告路径为
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-leaf-context-v2-20260904\preflight-leaf-context-v2-r1.json`，
SHA-256 为 `BBF2673B3258D1A0CA95943BF58C360161EBF68098FEED7FD7DB20046F82BCEF`。相关 Python 契约、
preflight、analyzer 与 preview integration 测试在 normal/`-O` 下各 48 项通过；本步未创建 profile、未启动或
附加 CK3，也未发送游戏命令。

合入 canonical root 后，下一次独占槽应先重新运行以下 no-launch preflight（报告名必须保持新鲜），再只执行
其 `unique_powershell_command`：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe -B ck3_autonomous_player/native_bridge/research/prepare_g2_evaluated_days_current_pin_capture.py --manifest ck3_autonomous_player/native_bridge/research/fixtures/g2_evaluated_days_leaf_context_v2_live_manifest.json --report Z:\ck3_mod_rewrite_process_assets\zg361\g2-leaf-context-v2-20260904\preflight-leaf-context-v2-canonical-r1.json
```

该命令只允许新的 attempt
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-leaf-context-v2-20260904\live-leaf-context-dual-query-r1`，
仍只做两次同帧只读 terms query。preflight GREEN 证明的是“新的实机候选及前置成立”，不是 evaluator 已 live
成功；在新的 durable post-call 证据出现前，public wire/readiness、expiry、决策、自动投降与 `GEN-034` 均不提升。

## 2026-09-04：集成态 V2 重冻

[static-ready / no launch] 上述首版 frozen candidate 合入集成线后，canonical preflight 正确地因
`CMakeLists.txt` source hash 漂移而 RED；集成线已经加入 B3 manager 的生产源和测试目标，不能以旧 source
archive 冒充当前构建。本次没有放宽 preflight，而是从最新集成 pin
`249e6fb1be4e434a3c8fd30f41d9ec4afd929427` 重新构建并冻结。与首版 candidate 比较，五个 G2 实现/头文件
逐字不变，唯一相关源码差异仍是 `CMakeLists.txt` 中 26 行 B3 manager 并集，因此 leaf-context seam 与
private-only 边界没有改写。

新 private DLL / injector / source ZIP 的 SHA-256 分别为
`69CA9175577C42C0644630D0D4B8838A4E0DBEA14EE37819996483031513765F`、
`55A9612C6F5D254B6801604D9E2D1004C51F98B92A939BA039639B726749B21D`、
`34BC988B43503A6F766A17958CDA61AE0F34729E7CCBD958A8EC133B9EAF549E`；default-OFF DLL 为
`824646F19152F9CFCC14FFF550EEE74EF7E93369D80451673BE5837B74AC69D3`。private/default Release
构建成功，Debug 断言版两个 G2 native fixture 通过；相关 Python 测试 normal/`-O` 各 53 项通过。

新的 no-launch preflight 对全部输入与 source hash、候选/default build option、driver identity、exact evaluator
bytes、exact leaf-context chain、open_kaishek pin、空独占槽和全新 attempt 均返回 true，状态为
`ready-to-run`。报告位于
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-leaf-context-v2-integration-249e6fb-20260904\preflight-leaf-context-v2-r1.json`，
SHA-256 为 `1C2FC5AB1D41885051AEE34311C62F445A7C7B57CDBBF85315E33E23C96A0DEE`。合入 canonical root
后仍须用新的报告名再做一次 no-launch 路径绑定：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe -B ck3_autonomous_player/native_bridge/research/prepare_g2_evaluated_days_current_pin_capture.py --manifest ck3_autonomous_player/native_bridge/research/fixtures/g2_evaluated_days_leaf_context_v2_live_manifest.json --report Z:\ck3_mod_rewrite_process_assets\zg361\g2-leaf-context-v2-integration-249e6fb-20260904\preflight-leaf-context-v2-canonical-r1.json
```

只有该报告为 GREEN 时才可执行其 `unique_powershell_command`；对应 fresh attempt 是
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-leaf-context-v2-integration-249e6fb-20260904\live-leaf-context-dual-query-r1`。
本次没有启动/附加 CK3，没有发送游戏命令；public/readiness 与 `GEN-034=unresolved` 继续不变。

## 2026-09-04：leaf-context V2 live r1 heartbeat harness RED

[harness RED / capability not exercised] 集成态 V2 独占槽保留在
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-leaf-context-v2-integration-249e6fb-20260904\live-leaf-context-dual-query-r1`。
runner 在同一个 pipe connection 上收到了 `native:3 / revision=4 / native_revision=3`；地图已就绪且暂停，
CharacterID `29829`、WarID `50331699`、`date_raw=53223936` 均正确，但 300 秒内
`heartbeat_sequence` 始终为 `null`，mailbox 字段因此均不可用。runner 没有提交 MCP query、没有执行动作或推进时间，
private JSONL 也没有产生。这不是 leaf evaluator 的 capability 结果，因为该能力根本没有进入执行边界。

进程回收是 GREEN：session PID `22512` 以受管 `stop` 收口，`shutdown_ok=true`、`tree_gone=true`、
`cleanup_proven=true`、`driver_closed=true`；事后进程清单没有 `ck3.exe` 或 injector。原 checkpoint 与 driver
hash 保持不变。runner report SHA-256 为
`50E36D75CA765D5FA2FD90055F23350298A130646392DD048CC3288EF42FB542`；完整摘要见
[`evaluated-days-leaf-context-v2-live-r1-harness-red.json`](../../artifacts/g2/2026-09-04/evaluated-days-leaf-context-v2-live-r1-harness-red.json)。

与最后一次成功进入 mailbox readiness 的 direct V1 r1 对比，EXE、checkpoint、driver、production mod tree
及游戏身份相同；旧桥收到 heartbeat `789`，mailbox `installed/ready/executor_submission_enabled=true` 且
`failure=0`。两次 CK3 日志都只有正常 mod/GUI 加载标记，没有 injector/bridge/pipe/fatal/crash 差异。有效差异
位于私有构建组合：旧构建只启用 direct capture；V2 启用 leaf-context capture。后者即使把独立 preview
observer option 留为 OFF，CMake 依赖仍会定义
`XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1`。

该编译分支的 `HeartbeatFrame` 在写完 `g2_truce_preview_entry_observer_v1` 后曾先追加一个 `}`，随后函数公共
terminator 又固定追加 `}}`，使 leaf-context-only heartbeat 多出一个结束括号。Python pipe reader 对每帧
`JSONDecodeError` 采取跳过并继续读取的策略，所以非法 heartbeat 全部被丢弃，而紧随其后的合法 snapshot
仍能到达；这与实机的选择性缺帧逐项吻合。最小修复是删去该分支的提前闭合，让公共 terminator 统一关闭
observer 子对象和根对象，并增加 leaf 依赖组合的源码回归断言。此修复只恢复既有私有诊断传输，不改变
leaf-context evaluator、public wire/readiness 或 action。

旧 r1 保持 RED 且不得原样重跑。修复候选完成 default-OFF/private 构建、测试、冻结及 fresh preflight 前，
不得申请下一次独占槽；即使这些 no-launch 前置全部 GREEN，也仍只代表 harness 候选可运行。
`native_certified=false`、`runtime_certified=false`、`decision_ready=false`、
`automatic_surrender_ready=false`，`GEN-034` 继续 unresolved。

## 2026-09-04：heartbeat 修复候选重冻

[static-ready / no launch] heartbeat framing 修复已作为 canonical `81cf89b` 合入，随后 current integration
在 `48da012` 同步 open_kaishek pin 至 `f4ce25a1e0ea259b1fc58ca33a4caf2180e7d234`。private leaf-context 与
default-OFF 两套 MSVC Release 构建都完成全部 463 个 target；两边的
`raiktor_surrender_truce_v1`、native-callsite observer、preview-entry observer 三项 native test 各 3/3
GREEN，相关 Python 合同、preflight、analyzer、context-lifetime 与跨仓审计在 normal/`-O` 下各 42 项 GREEN。

构建后 canonical 只以前进 `b71b73c9a01604a5d1025d87e6f458f23103c707` 更新日报/周报；从 `48da012`
到 `b71b73c` 的 native bridge、G2 合同和 G2 测试 diff 为空，因此最终 source ZIP 与 manifest pin
`b71b73c`，并复用逐字节相同编译输入所得的 paired binaries。冻结目录为
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-hbfix-b71b73c\frozen`；private DLL、injector、default DLL、
source ZIP 的 SHA-256 分别为 `22BD3A5A…17DE`、`BF8917AE…D368`、`5F7C2F65…F5D2`、
`E09E3C62…2821`。首次较长 build path 因新增长名称测试目标触发 MSVC object-path limit，未作为候选；
缩短外部 build path 后同一构建完整通过。

manifest 还新增了 `bridge.cpp` 与 heartbeat 回归测试本身的 source hash，避免只冻结 leaf evaluator 而遗漏
本次真实故障点。open_kaishek audit 为 `GREEN_STATIC`，但其 `native_certified=false`、
`runtime_certified=false` 不变。no-launch preflight 的全部 input/source hash、private/default option 与 marker、
driver identity、exact evaluator bytes、exact leaf-context chain、open_kaishek pin、空 CK3/injector 进程槽和
fresh attempt 均为 true；报告为
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-hbfix-b71b73c\preflight-leaf-context-v2-heartbeat-fix-r1.json`，
SHA-256 `DB970CBC7B4A54E9AF1FB11AEC10FC8225C68C09C6648FCFDC4792C74308A1FE`。冻结摘要见
[`evaluated-days-leaf-context-v2-heartbeat-fix-static-ready.json`](../../artifacts/g2/2026-09-04/evaluated-days-leaf-context-v2-heartbeat-fix-static-ready.json)。

preflight 给出的唯一 live 命令只允许 fresh attempt
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-hbfix-b71b73c\live-leaf-context-dual-query-r2`，仍只做同一 paused
frame 的两次只读 terms query。该 GREEN 是修复后 harness 的静态前置，不是 live evaluator 结果；本步没有创建
profile、启动或附加 CK3，也没有发送游戏命令。旧 r1 heartbeat artifact 保持 harness RED；public
wire/readiness、expiry、决策、自动投降和 `GEN-034=unresolved` 均未提升。

## 2026-09-04：leaf-context V2 live r2 private evaluator GREEN

[private-live evidence / public production unchanged] heartbeat 修复后的唯一 r2 独占槽已经完成，完整外部目录为
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-hbfix-b71b73c\live-leaf-context-dual-query-r2`。exact
`1.19.0.6` EXE、CharacterID `29829`、WarID `50331699`、`date_raw=53223936` 在同一 paused
`native:3 / revision=4 / native_revision=3 / connection_generation=1` 上执行了两次且仅两次
`query-war-termination-terms-v1-50331699`。query sequence 为 `1 -> 2`，before/between/after 的日期、暂停态、
snapshot 和 revision 均不变；`mutation_commands=[]`、`time_advanced=false`。

private JSONL 共 8 行，严格形成两个 4 行组：每组均为
`pre_call -> post_call_1 -> post_call_2 -> summary`，完成计数为 `0 -> 1 -> 2`。两组都命中
`root[7].default.children[1].children[0].children[0]`，Truce vtable RVA 为 `0x4461CA8`，duration 为
`truce+0x108`，evaluator RVA 为 `0x3373000`；每组的两次同步返回均为 `1825`。两组都满足
`pointer_shape_verified=true`、`evaluator_double_read_stable=true`、`same_frame_stable=true`、
`context_destroyed=true`。这关闭的是 leaf-context 下 `evaluated_days` 的私有实机取值缺口，而不是 expiry 或完整退出决策。

runner、analysis、private JSONL 的 SHA-256 分别为
`00343F7E1186DF65A13A7F85806BB048A8D28C67DF8F451BF559D21B800427D9`、
`D2A6DC1260FD32ECEE2B48B224F5461BA8EC4A52E9C5C81BF533913C51068A2D`、
`9F0EF7D9E045AE071B05C6F7DDE4166AE21BA12D98B3CA7DA19A8FE16A35B677`；紧凑、可提交的摘要见
[`evaluated-days-leaf-context-v2-live-r2-private-green.json`](../../artifacts/g2/2026-09-04/evaluated-days-leaf-context-v2-live-r2-private-green.json)。
session PID `55012` 由受管 `stop` 收口，`shutdown_ok/tree_gone/cleanup_proven/driver_closed` 均为 true。
原 checkpoint 与 driver-state 的前后 SHA-256 分别恒为 `60108A5D…F164` 与 `4FB901C7…F57E`，因此 source
immutable；没有 surrender、white-peace、enforce 或其它 mutation，也没有时间推进。

r2 使用显式 private leaf-context 构建；虽然该候选的两次 terms payload 已能带回
`evaluated_days_observable=true / evaluated_days=1825`，默认 OFF 的 production binary 尚未取得等价 live 证据，
因此 `public_wire_promoted=false`、`public_readiness_promoted=false`。`actual_expiry_observable=false`，不得以
`current_date + 1825` 推导 persisted expiry；`decision_ready=false`、`automatic_surrender_ready=false`，
`GEN-034` 继续 unresolved。open_kaishek capability/certification 也不在本次文档包内变更。

下一项不再重复 r2 private capture：先把这条已实证的同步 leaf-context 读取最小化接入默认 production reader，
保持 exact-build fail-closed 和纯只读边界，冻结 default binary 后再申请一次 fresh paused 同帧双查询，验证不启用
private capture 时 public terms 仍稳定返回 1825。expiry、generic war-bound、campaign/budget、white-peace、action 与
postcondition 继续作为后续独立门，不因本次 private GREEN 合并提升。

## 2026-09-04 default-production leaf reader candidate

[static-ready / production-live pending] Candidate source commit
`1941c56aba1e0eae31b5319575425d21123b2b86`, replayed on canonical
`27b66b3ea34c3ad03bdc72a4fb14345628a7a606`, moves only the r2-proven
synchronous leaf-context read into the default production path. The installed
exact-build preview-entry hook supplies the transient leaf wrapper; the reader
requires its `+0x28` evaluation-context pointer, binds the callback's
`effect_this` to the unique resolved
`root[7].default.children[1].children[0].children[0]` CAddTruce node, and
performs the same two equal nonnegative evaluator calls before the wrapper
returns. It does not execute the effect and does not derive persisted expiry.

The fresh Release build at
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-production-leaf-1941c56-20260904\frozen`
has all four G2 private/diagnostic options OFF. Frozen SHA-256 identities are:

- default `xar_ck3_bridge.dll`:
  `1ACC24DB476A7B1ECB4F0A98EF2E9A74D0E932CB74F5884622530D77246E3244`;
- injector:
  `03ED1EE07AC58E1E6F7ADDE31518C732C1D60CDBFFC3B50938D7E1CF84C877C5`;
- `CMakeCache.txt`:
  `D031DCBD98E05CBABE675B04FA9DD408BB067F65438EEB5AEAC387CF6F0EF9A6`;
- source ZIP:
  `84951CE78C3E075B609A1534005E82F246AACE102AD7BFE80106C1364C78DBC2`.

The clean native build completed all 483 steps. CTest reached an equivalent
`92/92` GREEN: 85 tests passed initially, while seven source-contract tests
reported only the isolated worktree's missing ignored game-EXE path; after a
read-only junction restored that exact input, those seven passed without
rerunning the other 85. G2/Raiktor Python regression is `212 passed` plus 85
subtests; the production preflight's normal and optimized tests are both
`12 passed`.

The immutable manifest is
`g2_evaluated_days_production_live_manifest.json`, SHA-256
`6B5783BCA00A1B082AA5FEC834EE73A95860535549B7525A616C82F178265C58`.
No-launch preflight
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-production-leaf-1941c56-20260904\preflight-production-leaf-r1.json`
is `ready-to-run`, SHA-256
`1FAF531BFD7B185550E82388275A470994694852BD9FC42F93A14F6789714421`;
the fresh attempt directory remains absent. Its sole emitted command runs the
existing public termination-terms runner twice and contains no private JSONL
environment, analyzer, mutation command, or time advance.

This is not production-live evidence yet. Public readiness is unchanged,
`expiry_observable=false`, decision and automatic surrender remain false, and
`GEN-034` remains unresolved. The next legal gate is exactly the manifest's
fresh default-binary dual-query attempt; do not repeat the r2 private build.
