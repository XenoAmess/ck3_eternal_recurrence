# B3 exact trigger helper split fallback（2026-09-04）

状态：**`NOT_SELECTED_FALLBACK` / `GREEN_NO_LAUNCH` / 未实机。**

该分支没有修改 canonical 集成树，也不主张这是必要修复。显式 `AND` 最小候选已经由 CK3 串行协调器实机恢复
Frontend：303 callbacks 首次完成于 `123.801s`，Frontend 出现于 `125.965s`，材料错误为 0。因此“只有显式
AND 仍失败才运行本 fallback”的条件没有发生；本候选不再占用 CK3 槽，其命令保留但标记为不得执行。

选择依据绑定到：

- artifact：`Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\artifacts-live`；
- outer report SHA-256：`F0ABC5F24505019061B986DB8992CA0DDD95C0D584C6C9F24B5D4BF6BB9B9B70`；
- evidence index SHA-256：`A6049D099759571921A5E81A0634517E25C91E5A0452AABA0D583041F6BFCE5F`；
- cell report SHA-256：`9A9AE5C6F52AAB6FC99F6D44D918C9556A8C43BCEF25C430583097D8846B9E17`；
- `final_error.log` SHA-256：`5ACD90C8C74A82014ABE065B33CB51D6BDEF2DF6298C0E83D9E296333B818A9D`。

## 静态候选

独立分支：`codex/b3-exact-helper-split-20260904`。源码提交为 `325284f1e15a96159ab348ff99a5f89d05630def`
和 `6758e83314b2c56d956441da12b18421eb8a719a`。

候选从冻结 r5 A 的 565 文件树派生，只删除旧
`common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt`，并新增四个生成器拥有的用途文件：

| 文件 | 用途 | definitions | bytes | SHA-256 |
|---|---|---:|---:|---|
| `zg361_phase2_central_001_m360_candidate_triggers.txt` | candidate readiness | 1 | 15,909 | `c2fec5b0bd090bab4d5f6d14cd34e05cffa09148e92ec0aebc94e6a09574434f` |
| `zg361_phase2_central_002_m360_b1_identity_triggers.txt` | B1 source identity / quota | 1 | 555 | `f84a6023400c68b5c2053b2e591cb27129c291f719e74ff0bbfbf638f94d6989` |
| `zg361_phase2_central_003_m360_mg_identity_triggers.txt` | MG case / snapshot identity | 1 | 533 | `ae7e270b55821de693d4e5dfa1c5965656d49ea50b18a4d25f27d2c99faa1bca` |
| `zg361_phase2_central_004_m360_exact_triggers.txt` | exact composition | 1 | 1,070 | `c1dad1d3cf746ec7bd2b8ae7aaf2cafe720eea0af0bd33df8aba844ad09ed48b` |

结果为 568 files / 21,608,480 bytes，564 个共同文件逐字节不变，tree SHA-256
`2564a8a824068cf500e106af0026c4269c6e4844d17ed8dc841fb0abd95ea91f`。每文件恰好 1 个 trigger definition，
满足 1–10 目标；没有超过 20 的例外。

这不是“文件体量已被证明为根因”的证据。candidate readiness 正文本身仍为 15,909 bytes；此 fallback 只把 exact
的附加比较隔离成小 helper，目的是在显式 AND 失败时进一步区分 exact composition/边界，而不是把大文件假说写成结论。

## 语义与 ABI 证明

- `candidate_ready` block 相对 r5 A 逐字节不变；
- 原 exact 的 9 条附加等式逐式保留：5 条 B1 source identity/quota 比较进入 B1 helper，4 条 MG
  case/snapshot 比较进入 MG helper；
- 两个 helper 在未切换 scope 的相同 current scope 调用；exact 仍是 candidate + B1 helper + MG helper 的隐式合取；
- exact 正文仍消费全部 12 个 `$PARAM$`，参数逐名原值转发；candidate 为 3 参数、B1 helper 为 5 参数、MG helper 为
  4 参数；
- 六个外部 callsites 保持 3 个 candidate + 3 个 exact，caller 参数集合不变；
- Central closure GREEN：reachable `1,868 effects / 560 events / 18 triggers`，三类 missing 均为 0；material
  projection 为 `3,698 effect / 985 event / 25 trigger` definitions，missing/duplicate 均为 0。

静态矩阵：generator `--check`、generator tests（普通/`-O`）、materializer tests（普通/`-O`）、release
reproducibility `--check`、release tests 9/9、projection tests 8/8、B3 freeze tests 14/14 均 GREEN。open_kaishek
parser/root-parser 均为 0 diagnostics；parser report SHA-256
`D9DBECB1EA658D87298F9C085CEB05D7505C333B6DA2A074C465CB4AD2339670`。这些只证明静态语法、投影和闭包，
不构成 CK3 parser、业务语义或 gameplay 证据。

## 冻结与并发门禁

最终 no-launch 冻结根：
`Z:\ck3_mod_rewrite_process_assets\zg361\b3-exact-helper-split-6758e83-20260904T100659Z`。

- attempt manifest SHA-256：`F8BDC1ADBCE25EB05A3645667303AB08B4E18AB696C14087E2B771114CE76D29`；
- projection manifest SHA-256：`ACB8C409CC6E4DE4E50A06450DE8B10562F77A6203687CAFE77A679470A5FDA2`；
- formal `--preflight` GREEN log SHA-256：`3FEB528733A1AAA0026AC7F44C57068F2B3AB1FDD82BBB4142779C53B7110723`；
- `artifacts-live/` 不存在，`ck3_launched=false`、`selected_for_live=false`。

此前在主线 CK3 正占用排他槽时，第一次 preflight 被 runner 明确拒绝：
`Z:\ck3_mod_rewrite_process_assets\zg361\b3-exact-helper-split-325284f-20260904T100320Z\formal-no-launch-preflight.txt`
为 79 bytes / SHA-256 `493C864365CBF98DFDA51DCA6698E2CB7E32631D0D46195AF94726011B928278`，唯一错误为
`ck3.exe is already running`。它是 `harness_concurrency_prelaunch_red`，不是候选或能力 RED；本工作包没有启动、关闭或干预该
CK3 进程。槽释放后只用全新目录完成 no-launch preflight，未复用失败目录。

机器记录：

- `docs/phase2-promo/b3-exact-helper-split-no-launch-2026-09-04.json`：紧凑仓库摘要；完整冻结 manifest 只保存在外置根并由 SHA-256 绑定；
- `docs/phase2-promo/b3-exact-helper-split-selection-2026-09-04.json`：未选用 receipt；
- 外置 `NOT-SELECTED-FALLBACK.json`：与选择结论同源的 sidecar。

## 冻结命令（不得执行）

下列命令由 GREEN no-launch preflight 精确签发，但因 activation condition 未发生而标记 `do_not_launch=true`：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\run_zhongguo_acceptance.py --phase2-live-batch --bridge-dll Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge.dll --bridge-injector Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z\native-build\xar_ck3_bridge_injector.exe --bridge-pipe \\.\pipe\xar_ck3_bridge_zg361_05d22eefe44245df7ed2845e2066f9ff --phase2-seed-contract Z:\ck3_mod_rewrite\_wt-b3-trigger-body-diagnostic\tools\zg361_phase2_seed_contract.json --phase2-product-source Z:\ck3_mod_rewrite_process_assets\zg361\b3-exact-helper-split-6758e83-20260904T100659Z\product-source --phase2-product-projection b3-r5-exact-helper-split-v1 --phase2-product-projection-manifest Z:\ck3_mod_rewrite_process_assets\zg361\b3-exact-helper-split-6758e83-20260904T100659Z\projection.json --artifacts-dir Z:\ck3_mod_rewrite_process_assets\zg361\b3-exact-helper-split-6758e83-20260904T100659Z\artifacts-live --discard-userdir
```
