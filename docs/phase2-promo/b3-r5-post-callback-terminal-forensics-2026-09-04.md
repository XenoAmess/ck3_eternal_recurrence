# B3 r5：303 callbacks 后的 Frontend terminal 取证（2026-09-04）

状态：**READ-ONLY FORENSICS / 唯一下一实验已确定。** 本轮没有启动 CK3、没有修改产品/runner/native probe，
也不把静态检查或 bridge ACK 当作实机成功。本文承接
[`docs/zg361-b3-effect-boundary-ab-fallback.md`](../zg361-b3-effect-boundary-ab-fallback.md) 已冻结的 r5
`A1 → B1 → B2 → A2` 矩阵，专门回答共同的 post-callback/Frontend terminal 缺失发生在哪里。

## 冻结边界

- 四轮产品 source commit：`cb02d4c16f7ff86243e063fa97d519ec87553266`。
- CK3：`1.19.0.6`；EXE SHA-256：
  `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
- A：565 files / 21,607,125 bytes；tree SHA-256
  `50eca1ef14d30c613f6a6e59ccd244bc3b92ee5a4aedaf7bccd191af20b0475f`；projection manifest SHA-256
  `2052dada087a91273a3b15587a34b00c861cca543dbe14926026f3a2ba29b298`。
- B：760 files / 21,617,213 bytes；tree SHA-256
  `c071005918b151a41ef1b65cba538d93b2e23da9a7ba5783724d7f39cd485c32`；projection manifest SHA-256
  `7c492bcec9013ab8070935a8f5fe0fc4e0bd4e679f2b22c3cdde873358cdcab4`。
- B 只把三个 effect owner 等价拆成 198 个 1–10-effect shards；定义 block 与调用图不变。完整边界证明见上游
  ABBA 文档，本轮不重复检验。

决定性的最近对照不是更早的 B2，而是 r4
`Z:\ck3_mod_rewrite_process_assets\zg361\b3f-1341251-20260904-070920Z\artifacts-live`。它的整体结果仍为 RED
（六处 unknown trigger，且 Frontend 后没有进入 `Load Save`），但 loader 已在 first-303 `117.800s` 后、总 elapsed
`119.830s` 明确发布 `Frontend`。outer/cell report SHA-256 分别为
`55df5de1c6988c94e41358946f4dabadda68a06b137a969668ada30834098071` /
`6c3a1eadaaa29dca174e4b30b1da911ac7dc34adb6d189877f3a8b8993e8df6`；debug/error SHA-256 分别为
`6d2caf2f5b04becec7aa9b420fd01a59e016be433f5fa4c53ec8af75b2ebac0d` /
`0b084d2b92b9673ebeeef2ad1db2cc3477e7ab8c0f083bf98b78011069d54b49`。

r4 `product-source` 有 564 files；r5 有 565 files。逐文件 SHA `Compare-Object` 的精确结果为：r4-only=0、
r5-only=`common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt`、同路径 hash 变化=0。新增文件为
16,712 bytes，SHA-256
`ee8d962f5a9aa95ae68098b96ffe26e1b2da2435821617bd51e75fe0fec377d7`，只定义
`zg361_p2c_m360_candidate_ready_trigger` 与 `zg361_p2c_m360_frozen_manager_exact_trigger`。因此 r4→r5 的
Frontend terminal 分歧有一个比 localization 或总量猜测更强的单变量入口。

更早且能完整进入 native-ready 的较小 GREEN 是 B2 r22：
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-r22-20260904-123400\focused-live`。它的产品投影为
252 files / 12,106,862 bytes，tree SHA-256
`fc4218469ce72ea1bca4e5bc0e5fa668e644ec05dea537e38ebda607ae72dc8f`；outer/cell report SHA-256 分别为
`6fc744ba4c5d6ba905a41a0e91ef870452a378da3431dcbfb537c31aa3533f47` / 
`78bd148ed20ba1bf0d3af9866bb9d02e7ba4f6060b4d764c658c298d55ee641e`。B2 r20
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-r20-20260904-121400\artifacts-live` 也独立到达
`Load Save`/`In Game`/native readiness；其 runner report SHA-256 为
`eb09db6bac4962fbf05b3a1998016a14fe2d5fb0aa61526a389119a4cec6dce4`。

## 首个可观察分歧

四轮 r5 都完成相同的 **303** 个 database callbacks，最后节点都是
`CJominiInGameMusicDatabase`；之后也都写出了 `Start loading of history` 和 `End loading of history`。
分歧不是“有没有进入 history”，而是 history 两个标记之间缺少 GREEN 必有的 application idler publish：

| 运行 | 最后 callback | history start | 应有但缺失的首行 | history end | end 后有效静默 |
|---|---|---|---|---|---:|
| A1 | 15:40:40 | 15:41:00 | `Setting idler 'Frontend' with NO init options` | 15:41:04 | 仅 2.675s，受总门限截断 |
| B1 | 15:47:56 | 15:48:19 | 同上 | 15:48:20 | 165.348s（callback quiet 166.813s） |
| B2 | 15:56:00 | 15:56:18 | 同上 | 15:56:20 | 171.685s（callback quiet 173.854s） |
| A2 | 16:06:13 | 16:06:31 | 同上 | 16:06:32 | 160.726s（callback quiet 162.083s） |
| r4 loader-positive control | 15:20:53 / 117.800s | 15:21:12 | **15:21:14 出现** / 119.830s | 15:21:14 | Frontend 后因 save-resume + unknown-trigger 另行 RED |
| B2 r22 GREEN | 12:44:42 | 12:44:43 | **12:44:44 出现** | 12:44:44 | 同秒进入 `Load Save`，12:44:47 进入 `In Game` |

因此严格的首个 post-callback 分歧是：**r5 在 history start/end 之间没有发布
`gameapplication.cpp:558` 的 `Frontend` idler；随后也没有 `Load Save`、`In Game` 或 native snapshot。**
这比笼统的 “303 callbacks 后卡住” 更精确；而 r4 证明同量级产品与同量级日志可以越过这个点。

关键原始证据：

| 运行 | artifact | debug SHA-256 | loader progress SHA-256 | loader gate SHA-256 |
|---|---|---|---|---|
| A1 | `Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\artifacts-live` | `4b933de97243298817c67f246cf558fa58162781e42d14f11d2e36b39dd526f2` | `3b651fa40b1697a3f5b045c0b5181cdd3974843d3dc13ad904f205c975333a4f` | `7d6661769142d7ccff8dbc7da876810cf9db7bbf7de34d7313a3b9856e7d58fc` |
| B1 | `Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z-boundary-B\artifacts-live-b1` | `dfc8b0e79829f93c215b55ddac42229a2fbd44af93705e044725b787fa02f7e6` | `be1ccf95450acd701e0fcd87590495522b9f28437f76088545e8391649cade13` | `a9e19ca954e1415e3a05d424a49d3501a122d97c39365cf0383d5eeedbda5c06` |
| B2 | `Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z-boundary-B\artifacts-live-b2` | `d8cf80d2fb1558bbbce96f0ee96e87d83f876159792cccaf8953c37e6dfb3479` | `a7249b5a13d95d4b7f552599bf7f49b838c5b85d6542a324e3be09a009565c6d` | `abe497b094914a4c0fc5a46164d833a2ad61a8470cf490bcf3fc83bd84d97b51` |
| A2 | `Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\artifacts-live-a2` | `62c4a8035baff12ed61f6d625efa3d33d961cbc58393b8d7fe52a4dc4aeedda2` | `ee647bffa89f2e00f481b49dcefba1f008d723b143c51b1e4dcde3fcf346ac9c` | `66a89c73f1cf88f8ce578300b54268265c665379d71e59e69f8b91e40d48ed71` |
| r4 loader-positive control | `Z:\ck3_mod_rewrite_process_assets\zg361\b3f-1341251-20260904-070920Z\artifacts-live` | `6d2caf2f5b04becec7aa9b420fd01a59e016be433f5fa4c53ec8af75b2ebac0d` | `9e339209bfc34a1a8e88d805d2c90d6f83bc316565d81cb6df973fc3623f7e95` | `7c4d34ed3efbfde22b14da5380be31413852bad6dff6b38a5235d5ded0b8aefc` |
| B2 r22 GREEN | `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-r22-20260904-123400\focused-live` | `adb61ba8cc3896521e863cb91394d4054a7b5a4a3cae94f1e51e95a423667377` | `4cea020d205c5eb5f4bf81dad2af0272f7b112a93d09e00f3567d0eceafb3896` | `2ee1e5a84dff3f4cd7d73ada18f0dfdfa922ecec34e169644ef33adf087146c0` |

## 五类解释的证据权重

### 冷缓存：解释 A1 callback 慢，不解释共同 terminal RED

A1 到 303 callbacks 为 297.264s；相同原边界的 A2 为 137.788s，B1/B2 为 133.034s/125.891s。
因此首轮 cache/运行次序效应真实存在。但 B1、B2、A2 都早于门限约 162–174 秒完成 callbacks，仍在同一
Frontend publish 点失败。冷缓存只能解释 A1 的慢速离群值，不能解释 terminal 缺失。

### 日志写爆：r4 是决定性反例，不是 r4→r5 terminal 分歧的必要条件

r5 每轮 `final_error.log` 都是 3,650,011 bytes / 15,032 lines：952 条 unrecognized localization、
13,990 条 set-never-used、90 条 used-never-set；unknown effect/trigger/event 与 fatal 均为 0。四轮去掉时间戳并排序后的
同一诊断 multiset SHA-256 都是
`4a8dcbcf91c5081180048e0030b8157d04d61dd9743d40cb679309914042e0ac`。

r4 的 `final_error.log` 反而更大：3,652,831 bytes / 15,044 lines，SHA-256
`0b084d2b92b9673ebeeef2ad1db2cc3477e7ab8c0f083bf98b78011069d54b49`。其计数为 952 条 unrecognized localization、
13,996 条 set-never-used、90 条 used-never-set、6 条 unknown trigger；去时间戳并排序后的诊断 multiset SHA-256 为
`2bb45ab81150e1762fcea16f6e94ba80648528ff3267cbf1782d45f4b0aa5111`。它仍在 first-303 `117.800s` 后、总 elapsed
`119.830s` 发布 Frontend。因此“日志约 3.65 MB / 1.5 万行”及同样的 952 条 loc 错误都不是 r4→r5 terminal
分歧的必要条件。

B2 r22 GREEN 的 `final_error.log` 为 1,376,819 bytes / 5,607 lines，SHA-256
`eef5d65350d20f8b36d358d0dc12212e41d14fa2f367adb4d8ec6828f13e0796`，其中 unrecognized localization 为 0。
这只说明较小 GREEN 的日志负载更低，不能推翻更接近且同量级的 r4 loader-positive control。另且 B1/B2/A2 的最后诊断均在
history end 时已经写完，之后各自静默 160 秒以上；没有持续增长、fatal、进程退出或 I/O 错误。结论是：日志去噪有产品价值，
但不能抢在 r4→r5 的单文件单变量实验之前。

### 资源 / GUI / event / localization 后阶段：唯一精确产品差异是双 trigger provider

- 四轮 GUI asset 日志都明确完成 `frontend_main.gui` 等 frontend GUI 的加载；没有 GUI load error。
- 三态 closure 已消除 unknown effect、unknown trigger、event-not-found；四轮实体错误计数均为 0。
- r4→r5 的逐文件 SHA 对比只多出
  `common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt`；其余 564 个同路径文件全部同 hash。
- 该文件只提供两个 trigger，r5 的 event/effect/trigger closure 因它归零实体错误，但 r5 同时丢失 r4 已有的 Frontend publish。
  这不是已经证明 trigger body 有错，而是当前唯一能做严格单变量反证的产品边界。

r4 与 r5 均有相同的 952 条 localization 错误，所以 localization 缺口不是 r4→r5 terminal 分歧的必要条件。resource exhaustion
也没有 crash/fatal/telemetry 证据。两者都不得越过唯一的 source delta 被优先升格为因果结论。

### native probe 契约：不是首因证据

r5 的 append-only probe 报 `post_init=0`、completion publish absent；但 B2 r22 GREEN 的 loader-progress 最终记录同样是
`post_init=0`、completion publish absent，仍可通过 debug idler 与真实 native snapshot 判定 GREEN。因此这两个计数本身不是
RED/GREEN discriminant。

更重要的是，独立的 CK3 `debug.log` 也没有 `Setting idler 'Frontend'` / `Load Save` / `In Game`，而 B2 r20/r22 都有；
这排除了“游戏已经到达、只是 probe 没看见”的现有证据链。probe 仍缺少更细的 post-history 内部节点，但在已有严格单文件
source delta 与可物化单变量候选时，先扩 probe 不是最小下一步。

## 唯一首选下一实验：同名同参数双 trigger false-stub

准备态根目录：
`Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z`。其中：

- `diagnostic-manifest.json`：SHA-256
  `8f7e06a131919a11f9aa5332932bcfaf994802a26f04802eb8b373fdfb0278f8`。
- `projection.json`：SHA-256
  `d7535663a648537b3026504a2f5b09a2017bffac546fe39227178275ec2b4953`。
- `open-kaishek-preflight.json`：结果 GREEN，SHA-256
  `f8a1781a2ab1224461fd0b7267bbf3683a7061466c9d4e47c888e44d7402ff4b`。
- candidate：565 files / 21,591,388 bytes；tree SHA-256
  `4b6d6bca975a12708d64b68c83f08ce2a1028a9ecf8ab2cde2e474d01c54eafd`；file-list SHA-256
  `b91532aaa73b3ded3b1302d9dd343581c7ee2723f0befe003b5d709f3adbf04e`；564 个文件逐字节不变。
- 唯一变更文件仍叫 `common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt`，从 16,712 bytes /
  `ee8d962f5a9aa95ae68098b96ffe26e1b2da2435821617bd51e75fe0fec377d7` 变为 975 bytes /
  `caa8267e979898d951f7f390046d86372ddc7b0db9459fab79a73ea1d2072485`。
- 两个 trigger 的名字、数量、调用方和参数 ABI 均保持不变；仅各自 body 替换为 diagnostic-only `always = no`。
  manifest 已证明 closure GREEN、missing 为空、调用 surface 逐字节不变、source tree 不变，且 `artifacts-live` 不存在。

这正好只测试 r4→r5 的唯一新增 source owner，同时保留 r5 文件集合和 caller ABI。它不能验证 Phase2 业务语义，也不能在
Frontend 恢复时直接指认两个原 body 中的哪一条表达式；但这是当前信息增益最高的单变量实验。执行必须进入 CK3 串行门，且不得
再混入 localization、effect 分片、probe 或 profile 变更。准备态 manifest 冻结的唯一命令为：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe Z:\ck3_mod_rewrite\tools\run_zhongguo_acceptance.py --phase2-live-batch --bridge-dll Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge.dll --bridge-injector Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge_injector.exe --bridge-pipe \\.\pipe\xar_ck3_bridge_zg361_b3h_trigger_false_081911 --phase2-seed-contract Z:\ck3_mod_rewrite\_worktrees\b3-trigger-closure-r5\tools\zg361_phase2_seed_contract.json --phase2-product-source Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z\product --phase2-product-projection b3-trigger-body-always-false-diagnostic-fecd2f2 --phase2-product-projection-manifest Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z\projection.json --artifacts-dir Z:\ck3_mod_rewrite_process_assets\zg361\b3h-fecd2f2-trigger-false-20260904-081911Z\artifacts-live --discard-userdir
```

判定只看这一个变量：

- 恢复 `Frontend`：支持一个或两个真实 trigger body 是 terminal 缺失的充分候选；下一轮再逐 body 二分，不能直接宣称已定位到
  某个表达式，也不能把 diagnostic false-stub 当产品修复。
- 仍在 history end 后 terminal RED：排除两个真实 body 是该缺失的充分解释；保留该次新 artifact 的首个可观察分歧，再决定
  后续单变量，不顺手改 localization 或扩 probe。
- manifest/source/hash 漂移，或出现 target owner 外的文件差异：实验构造 RED，不解释产品 terminal。

## 独立产品缺口与后续去噪：localization closure

r5 的 952 条 localization 错误覆盖 **816 个唯一 key**。这些 key 全部可由同一 frozen `canonical-release` 中的
**63 个真实 provider 文件 / 685,315 bytes** 闭合，未解析 key 为 0。provider 恰为 7 个用途族乘 9 种语言：
`zg361_career_hc`、`zg361_career_learning`、`zg361_compensation_runtime`、`zg361_credit_project`、
`zg361_feedback_promotion_pip`、`zg361_phase2_central`、`zg361_phase3_metrics_delivery`。按
`relative-path<TAB>bytes<TAB>sha256` 排序后的清单摘要为
`541a3e0e2f580f1811b81fb186d11ece335a1c76daaa0328733b0af8351b6226`。

r5 产品实际只有 39 个 localization 文件；event/effect/trigger fixed point 引入了上述七族事件，但没有同步其 localization
providers。当前 `tools/expand_zg361_phase2_b3_projection_closure.py` 只对 `zg361pp.9004` 的三个 terminal key 做窄同步，不能闭合
这 816-key 集合。这是必须修复的独立产品缺口，也是后续获得低噪声 loader evidence 与发布就绪的门槛；但 r4 在相同 952 条错误下
已经越过 Frontend，故 loc closure 不得抢在 false-stub 单变量实验之前，也不得与该实验混跑。
