# B3 trigger body 互斥二分候选（2026-09-04）

状态：**ABI 修正版 V1 / V2 均为 `GREEN_NO_LAUNCH`，仅供一次性诊断，不是 production candidate。**

## 诊断边界

r5 A 相对 r4 唯一新增的产品文件是
`common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt`。本组固定同一 r5 A 树，
每份候选只替换其中一个 trigger body：

- V1：`zg361_p2c_m360_candidate_ready_trigger` 保持 r5 A 真实正文；
  `zg361_p2c_m360_frozen_manager_exact_trigger` 使用 ABI-consuming false stub。
- V2：`candidate_ready` 使用 ABI-consuming false stub；`frozen_manager_exact` 保持 r5 A
  真实正文，且内部调用仍解析到同名 `candidate_ready` stub。

false stub 在 `always = no` 前显式消费原定义的全部 `$PARAM$`：candidate 定义 3 个参数，exact
定义 12 个参数。机器门禁要求每个定义及整个 provider 的 placeholder set 与 r5 A 精确相等，避免
CK3 将 stub 推断为零参数 provider。两棵树都只有上述 provider 的 SHA/bytes 变化，其余 564/565
文件逐字节不变；stub 不进入生成器、正式 projection 或 production。

## 当前权威冻结

- materializer commit：`8d2065c36a111dc87b1d66aa01954b4ae7ce6520`
- 根：
  `Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-abi-8d2065c-20260904T093334Z`
- attempt manifest SHA-256：
  `1f1ae161d4a0731cce937399e654b828ba61482e951a59b0207428249c13b119`
- frozen r5 A：565 files / 21,607,125 bytes / tree
  `50eca1ef14d30c613f6a6e59ccd244bc3b92ee5a4aedaf7bccd191af20b0475f`
- r5 A projection manifest SHA-256：
  `2052dada087a91273a3b15587a34b00c861cca543dbe14926026f3a2ba29b298`
- r5 A trigger provider：16,712 bytes / SHA-256
  `ee8d962f5a9aa95ae68098b96ffe26e1b2da2435821617bd51e75fe0fec377d7`
- A2 runner：
  `Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\run_zhongguo_acceptance.py` /
  SHA-256 `2dd1067f7a0de9076cacc552bd2f786c00f1b04af9ef969eaa258ea2e7a747c6`

### V1

- product：`...\20260904T093334Z\v1\product-source`
- 565 files / 21,607,113 bytes；564 unchanged；added=0；removed=0
- tree SHA-256：`8a43b13dd35e31a3a94b7c200bea72ba19aa0e52fac9c313ea471ebeaec5bf78`
- trigger provider：16,700 bytes / SHA-256
  `b3f6535184d61418354f614866ed2bcbd1f4c4412b17fdcb766929bc94752aff`
- projection manifest SHA-256：
  `6a0cb0d2e89b9a02d35a042ebe75b9e67a11c4cbc72499828da2a1c3881da7e6`
- real `candidate_ready` body SHA-256：
  `5bfe697f42cebda0e70f04e3df65c76f486e2320ebca878f0ae5116786c12c92`
- exact false-stub body SHA-256：
  `52b44d3787226d192f91a3e00d61d931eb2c69077eac68a99e8975e413ccae70`
- open_kaishek parser report SHA-256：
  `ad0cb362bed8cded9e0175f210b8305223417e18e0b5f23714c53933f5a2f318`
- formal no-launch preflight log SHA-256：
  `0a2733ea6e9c601d80f6eb6a3fcf08d058d20f3fb3f7e3bd32e6b87f9eb9ee26`

### V2

- product：`...\20260904T093334Z\v2\product-source`
- 565 files / 21,591,648 bytes；564 unchanged；added=0；removed=0
- tree SHA-256：`9a68993c832e09824a7f75b2bd9d339d99a2f3ac6515fe28913ea74c93860937`
- trigger provider：1,235 bytes / SHA-256
  `b99096ad694729f91599565643aaa68ce5ff29486181798251191494a24e3964`
- projection manifest SHA-256：
  `9967aed85411cf66d2056d53f99a52cbfc184c09c18a0404c90acb7d1c427762`
- real `frozen_manager_exact` body SHA-256：
  `34ef467740aeaa5ff734613d777ece39b1feca036aa011885a28bb635c81676b`
- candidate false-stub body SHA-256：
  `1bedfe51de66d36876ed79fd8d786c1febcde1c055447608c87afed55a683981`
- open_kaishek parser report SHA-256：
  `14d45d403f10836936e9af18d4d4cb46d641cbd1f32828ba0dec3395b98292fa`
- formal no-launch preflight log SHA-256：
  `5e43b6503f49b819aee894fb8be8533f47abd08c4ce6c1bf292263102cdb943d`

## 门禁结果

两份候选均保留 UTF-8 BOM 与 `GENERATED FILE` header；定义级 placeholder ABI 与 provider
placeholder union 均精确匹配 r5 A。open_kaishek parser/root-parser 为 0 diagnostics，central
closure GREEN（reachable effect/event/trigger = 1,868 / 560 / 16，三类 missing 均为 0），正式
`--preflight` 返回 0。两份 `artifacts-live` 均不存在，生成前后 CK3 process count 均为 0；本轮没有
启动 CK3，也没有产生 gameplay/footage。

## 作废的 08:35 候选

旧根
`Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-366f30f-20260904T0835Z`
已由 `SUPERSEDED-MATERIAL-ABI-INVALID.json` 明确作废，marker SHA-256 为
`7283ad86eab6fe491b4a473656b4ea171e5bdd13961ab55ad7b7dcd59960cb3b`。旧 V1/V2 stub 没有引用
`$PARAM$`，与双 stub live 的六条 `Scripted trigger should have no arguments` 属于同一 material ABI
错误；旧 product、manifest、pipe 与命令均不得启动，也不得用于正文归因。

## 唯一 live 命令与排他顺序

推荐顺序：**V1 → 完整回收并确认 CK3 count=0 → V2**。两条命令必须由 CK3 排他调度者分别执行；
不得并发，也不得复用 pipe、userdir 或 artifacts 根。

V1：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\run_zhongguo_acceptance.py --phase2-live-batch --bridge-dll Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge.dll --bridge-injector Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge_injector.exe --bridge-pipe \\.\pipe\xar_ck3_bridge_zg361_0f0d11aa4816a2c4259d7da9bc5e8240 --phase2-seed-contract Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\zg361_phase2_seed_contract.json --phase2-product-source Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-abi-8d2065c-20260904T093334Z\v1\product-source --phase2-product-projection b3-r5-trigger-body-bisect-v1 --phase2-product-projection-manifest Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-abi-8d2065c-20260904T093334Z\v1\projection.json --artifacts-dir Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-abi-8d2065c-20260904T093334Z\v1\artifacts-live --discard-userdir
```

V2：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\run_zhongguo_acceptance.py --phase2-live-batch --bridge-dll Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge.dll --bridge-injector Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge_injector.exe --bridge-pipe \\.\pipe\xar_ck3_bridge_zg361_1d543a39d36a0abb17020119ca579038 --phase2-seed-contract Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\zg361_phase2_seed_contract.json --phase2-product-source Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-abi-8d2065c-20260904T093334Z\v2\product-source --phase2-product-projection b3-r5-trigger-body-bisect-v2 --phase2-product-projection-manifest Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-abi-8d2065c-20260904T093334Z\v2\projection.json --artifacts-dir Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-trigger-body-bisect-abi-8d2065c-20260904T093334Z\v2\artifacts-live --discard-userdir
```
