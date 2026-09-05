# T2：T0 / G2 当前增量同步（2026-09-05）

## 已交付

open_kaishek 已提交并推送到 `main == origin/main ==
84a2b18fedad74de37bf5cd0472519ee321f367d`，工作树 clean。主仓同步其
compatibility fixture、Java metadata 提取器及现行 profile commit pin；没有改动
CK3 native provider、公共 wire、产品 effect 或 G2 比较策略。

本包的实际差异是：

- T0 promotion transport ABI pin 从旧 `d53befa` 推进到 `d077bcf`，反映已取证的
  fixed-name descendant fallback。ABI SHA 为
  `EB22C5339A483614E75CD5135B896742AC9E0040166AC9689FB8AF3070C94068`。
  source contract、Python contract、能力 ID、字段与 readiness 不变量均不变。
- G2 metadata 补齐既有 R3 的 same-lifecycle 私有 cleanup / persisted-expiry 实机事实，
  不再写 `LIVE_NOT_RUN`。新增独立 live source / manifest / report / DLL pins；原
  static / synthetic pins 保留，`synthetic_fixture=true`、`fixture_is_live=false`
  保持不变，不能把旧 synthetic 记录改称实机。
- B1 `is_alive` / list 重建与 B2 first-use lazy trigger 使用现有 parser 结构，
  四个发生变化的产品脚本均 parser GREEN。弱引用生命周期、列表重建、写入求值顺序
  和 lazy evaluation 仍非 open_kaishek 已认证 finite-runtime 语义；本包不对 B1
  实机修复效果作结论。
- native event-window 的 stale named Character typed-unavailable 输出，以及 promotion
  Python 事件角色/时间窗/失败时间轴，均没有 open_kaishek decoder/runtime consumer；
  对应执行语义同步为 `not-applicable`，不新增 opcode 或猜测事件动作。

## 精确身份与验证

CK3 `1.19.0.6` / EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
离线 parser profile `ck3-1.19.0.6-zg361`；metadata profiles
`ck3-1.19.0.6-zg361-promotion-source-transport-v1`、
`ck3-1.19.0.6-g2-postwar-cleanup-expiry-adapter-v1` 未改名。

外部仓命令：

```powershell
mvn -o -ntp -pl kaishek-cli -am '-Dtest=ZhongguoPromotionSourceTransportCapabilityProfileTest,G2PostwarCleanupExpiryAdapterMetadataTest' '-Dsurefire.failIfNoSpecifiedTests=false' package
java -jar kaishek-cli/target/kaishek-cli-0.1.0-SNAPSHOT.jar parse <changed-product-file>
```

结果：focused Java `7/7`，package GREEN；四个真实变更产品文件各解析一次，
`4/4 PARSED`、roundTrip=true、0 diagnostics。解释器为 JDK21
`C:\jdk-21\bin\java.exe`，Maven 为 `C:\apache-maven\bin\mvn.cmd`。
完整命令语境、四文件路径/bytes/SHA 与不支持项已提交外部仓
[`docs/companion-delta-sync-2026-09-05.md`](https://github.com/XenoAmess/open_kaishek/blob/84a2b18fedad74de37bf5cd0472519ee321f367d/docs/companion-delta-sync-2026-09-05.md)。
不重复 unchanged 全量 reactor / corpus。

当前 CLI JAR 为 358,078 bytes，SHA-256
`BB94CD9142112A62DF57B901CA5E008B3A8EC0C05FEEC6EC3D3A7551DF5512C9`。
主仓 fixture
`ck3_autonomous_player/native_bridge/research/fixtures/g2_open_kaishek_compatibility_v1.json`
SHA-256 为 `14FD1469EE1D590F714F6B5C11A14C5EBDAAB2186B81FFFD4BCEE3C00AD987E2`。

主仓命令（显式使用已验证主 worktree venv）：

```powershell
$env:PYTHONPATH='ck3_autonomous_player/src'
& Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe -m pytest -q --disable-warnings ck3_autonomous_player/tests/unit/test_g2_open_kaishek_compatibility.py ck3_autonomous_player/tests/unit/test_raiktor_surrender_truce_contract.py
```

`13 passed, 16 subtests passed in 0.33s`。现有 available-checkout 测试确认
真实外部 HEAD / origin / clean 与 Java profile / fixture 一致；新增断言区分 R3
live receipt、synthetic fixture 和未完成的自动策略。`git diff --check` GREEN。

## 实机证据边界

本包没有启动/附加 CK3，没有写存档，没有发送游戏动作。复用的 R3 native source 为
`e72f9fa302811a823479635648eb008a6f5d8418`，report SHA
`44E1F7C0B470B2CF7B6549192865402F21F88C7CF073E896DE1B93632311D5D0`；
冻结 manifest SHA
`2113032784CC3ACC5DA14557C14315B0AEC9AF03CDC15654739A3C54704F96DA`。
两份保留 artifact 的 bytes/SHA 读取一致。来源见
[R3 原生专题](g2-postwar-cleanup-expiry-current-pin-no-launch-2026-09-04.md)。

现行 metadata 允许表述 private cleanup dispatch 已 live-tested、companion
runtime-cleanup primitive ready；不等于 open_kaishek runtime evaluator 或新认证。
public/action/source-specific-attribution/decision/automatic-surrender/GEN-034
仍 false。T0 `.146 -> D+1 .147` 完整源链不因本包升级。

旧 R3 manifest、source ZIP、driver-state 和历史报告继续绑定当时的 `37cab82`，
不会被改写为今日 accelerator 版本，也不因文档/metadata 同步重复运行 CK3。
下一实际 G2 comparison intake 若产生新的共享合同，由其工作包单独同步。

## 10:59 增量：`ae60624` G2 comparison intake

复核提交 `ae60624fd9b0de8775f6713ea089a94be18926d4` 后，结论为
`not-applicable / NO_EXTERNAL_CODE_CHANGE`：open_kaishek `84a2b18` 没有消费
本次新增的 Python policy 参数、intake manifest/schema 或 source-specific provider seam。

新 `raiktor-observed-surrender-outcome-v1` 是主仓内部比较层输入，接到
`assess_raiktor_three_way_exit` 的第六个可选参数
`observed_surrender_outcome_value=None`；旧五参数调用保持兼容。该提交没有变更
native bridge、MCP/public wire、Paradox 脚本或 open_kaishek 现有 profile/metadata
声明的 cleanup/expiry receipt。新 source-specific provider ID 是下一施工入口，
不是已实现或被外部 runtime 执行的能力。

本次一次只读检查使用 `git show --stat/--name-only ae60624`、实际 policy/intake
调用点，以及外部 repo 全树 `rg` 查询以下精确名称：
`raiktor-observed-surrender-outcome-v1`、`observed_surrender_outcome_value`、
`assess_raiktor_three_way_exit`、`g2_postwar_comparison_intake`、
`raiktor-source-specific-war-loss-attribution-provider-v1`。外部无匹配；实际主仓
调用是 intake → Python policy，没有调用 open_kaishek。外部 HEAD/origin 仍为
`84a2b18fedad74de37bf5cd0472519ee321f367d` 且 clean。

| 本次主仓输入 | SHA-256 |
| --- | --- |
| `g2_postwar_comparison_intake_r3_manifest.json` | `3360F729AAA7F8CEFDA27D918928CCCFAFDE343BF63DBE840BD7E5C41EF53D63` |
| `prepare_g2_postwar_comparison_intake.py` | `34B995DD604706EA1D218968C90850E826B3CA190E36B83A57E31BE682E0B99B` |
| `raiktor_three_way_exit_policy.py` | `3FCFC01532D1AE184D07D885391367DB784E66DFC45D36862F3753BA9036FC61` |

复用 [G2 intake 专题](g2-postwar-outcome-comparison-intake-2026-09-05.md) 已完成的
真实输入验证：normalized observation SHA
`08132B217DDF647DF9602F00CF4F927096ED0146E53FF9AB56A87ACD92C81F97`，
status 为 `observed_generic_boundary_source_attribution_required`；
`comparison_input_ready=false`、`source_specific_loss_comparison_ready=false`。
既有 R3 cleanup/expiry live metadata 仍准确，不新增 profile/opcode/runtime evaluator，
不重跑无变化的 Maven、parser 或历史 R3。public/action/decision/automatic/GEN-034
全部保持 false；没有启动/附加 CK3。B1 D0 witness 本轮也未出现超出前次 parser
覆盖的语法变化，不能据此宣称有限 runtime 已支持其游戏执行语义。

## 增量：`523432a` source-specific capture/provider

提交 `523432aec7846d0da833c5a351faad743fa23d2d` 的伴随检查结论仍为
`not-applicable / NO_EXTERNAL_CODE_CHANGE`。本提交新增主仓 Python typed capture
normalizer、离线 preflight、合同与测试/专题；没有修改共享 native DLL、MCP/public
wire、既有 cleanup/expiry receipt 或 Paradox 脚本。新 preflight 直接调用
`normalize_raiktor_source_specific_capture`，不调用 open_kaishek。

本次以 `git show --stat/--name-only 523432a` 确认七文件改动范围，并读取新合同、
normalizer/preflight 调用点及
[source-specific 原生专题](g2-source-specific-war-loss-provider-2026-09-05.md)。
外部仓全树 `rg` 对
`raiktor-source-specific-war-loss-attribution-provider-v1`、
`raiktor-war-bound-private-capture-v1`、`normalize_raiktor_source_specific_capture`、
`raiktor_source_specific_war_loss`、`source_set_sha256` 的精确检索结果为 0 匹配；
现有 `G2PostwarCleanupExpiryAdapterMetadata` 与 `G2WarBoundLossCandidateMetadata`
中的 `SOURCE_SPECIFIC_ATTRIBUTION_READY=false` 与新合同完全一致。

| 本次读取的源输入 | SHA-256 |
| --- | --- |
| `raiktor_source_specific_war_loss_attribution_v1_contract.json` | `1633808E42C324EF6C282481040B905DAF7FE9B0147F7072382919CA5064F9CE` |
| `prepare_raiktor_source_specific_war_loss_capture.py` | `6286921CF0782FE47EFFEC911BCD93697FF6F77BA99CD815784E957DD0A80D9E` |
| `raiktor_source_specific_war_loss_contract.py` | `F3204BA33885F12443493B4E0B8FE779C233E4B45047FA46C66079A65D75942A` |

新输出仅证明六次源执行捕获的结构和创建时实测士兵总数。当前尚无 classified live
capture，也没有贯穿同生命周期 current/action/postwar 的 source-specific join；
`source_specific_loss_ready`、`comparison_input_ready`、public/action/decision/
automatic-surrender/GEN-034 均未升级。不能把既有 R3 的 generic `598 -> 0`
事后归因给这六次源执行。

因此外部 HEAD/origin 保持 `84a2b18fedad74de37bf5cd0472519ee321f367d`、工作树 clean；
不新增 Java descriptor、opcode、IR/runtime handler、fixture 或 metadata pin。
复用专题已记录的 GREEN 静态 preflight
`FE3CDDF93E07B0028ED40BF472F55C89589CF497B2395DC587806ED4C913EB4B`，
本次不重复 Maven、parser、capture self-test 或 ABI verifier。仅作上述一次必要的
源码/合同消费关系检查和文档 `git diff --check`；没有启动/附加 CK3，没有写存档，
没有 effect-file 体量或加载性能的新实证。

## 12:27 增量：`a05b94e` 旧存档 B1 active witness provenance

主仓 `a05b94e545fc6074fa2ffae2ffa76e34d9990d62` 只改变现有固定 widget
`zg361_promotion_source_b1_active` 的生产端真值条件：直接加载的旧存档尚无新
manager cycle serial 时，可用 manager-only `policy_next_review_serial > 1` 作为
只读 active witness。固定 widget 身份及传输字段 `widgets.effective_visible` 不变，
因此 public ABI、request/output schema、能力 ID、allowlist、native decoder 均无
delta；但该文件是 promotion source contract 列明的产品源，故外部 profile 的精确
source provenance pin 需要推进。

独立 `open_kaishek` 已在 clean `main == origin/main == 84a2b18` 上直接完成四文件
最小同步并推送 `4c1f6867ff168f476a30a7b13220a8c2e0aa3294`。其中
`ROOT_INTEGRATION_COMMIT` 推进到 `a05b94e`；profile ID、source-contract / ABI /
Python-contract hashes、字段、invariants 与所有 readiness/certification flags 均不变。
新增 GUI 分支只使用既有 `OR` / `AND` / `NOT` block、`has_variable` 与 `var:*`
比较形状，不新增 parser vocabulary、opcode、IR 或 runtime handler。

外部 focused Maven profile test 为 3/3 GREEN；新 CLI 对目标 GUI 返回
`PARSED`、2,566 bytes、641 tokens、20 blocks、`roundTrip=true`、0 diagnostics，
CLI / GUI SHA-256 分别为 `B1DB12AF…9801A` / `31AD1EE1…3A5568`。这些是
静态 profile/parser 证据，不能冒充 CK3 runtime。R68 已独立实机证明旧种子 active
widget 可见，但完整 promotion loop 仍在 `.200` saved-scope 合同处 RED，所以外部
profile 继续 `PRODUCTION_LIVE_READY=false`，不因本次 T2 同步升级。

主仓 fixture 同步 `root_binding.open_kaishek_commit=4c1f686` 与
`promotion_source_transport.root_integration_commit=a05b94e`；公开桥常量及其
单测期望同步到同一 external commit。focused compatibility tests 在 normal / `-O`
下各为 13 passed + 16 subtests passed；verifier 两种模式均退出 0、
`GREEN_STATIC`，并确认 external HEAD=origin/main=`4c1f686`、clean、promotion
pin=`a05b94e`。`git diff --check` GREEN。没有生成新的 live artifact，也没有启动
CK3；完整 promotion loop 的 RED 边界保持不变。
