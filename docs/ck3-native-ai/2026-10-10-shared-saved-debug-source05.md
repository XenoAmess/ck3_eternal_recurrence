# Source05：共享存档 debug 开关与固定原生二进制复用

Source05 已实际冻结、绑定并完成源代码检查。新增 `saved_campaign_debug_mode` 为默认 OFF 的机器级共享开关：仅 saved-campaign 启动可映射到 host 的 `--saved-campaign-debug-mode`，最终同一次受管启动 argv 必须含恰好一个 `-debug_mode`；仍保留唯一 `-loadsave`、原 PID/Job、绝对 deadline、延后单次注入和严格两个原生 owner 帧门禁。产品或 case 不能选择该开关。本机 Source05 manifest 明确把 debug 与 `saved_campaign_inject_after_load` 同时设为 true。这是待实机验证的诊断输入，不能证明 R41 加载问题的根因或修复效果。

实际作者提交为 `3704561725e583d9c9fc10f4c47c1523bb1d9643`，单父 `0c0e36e21164d55cd9f47d2d8ab9ae7a5cbf3f63`。冻结提交为 **`27644fdc18e693990e43794af62ebf13db523aef`**，单父固定 Source04 `919bae0f42def04e6398eb2de4b4afe20dcfc106`，标签 `archive/common-runtime-source05-20261010`。冻结在独立 Git index 中只应用作者父提交→作者提交的五路径增量；未 merge、未把当前 master 全树复制为共享源。

独立复核实际遍历 `C:/csr5` **7,904** 件文件，全部 SHA-256 与文件集合匹配 Source05 index；与 Source04 index 恰好只有以下五项差异，其余 indexed bytes 全部相同：

- `ck3_autonomous_player/src/xar_autoplayer/runtime.py`
- `ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py`
- `tools/ck3_mod_acceptance.py`
- `tools/test_ck3_mod_acceptance.py`
- `ck3_autonomous_player/tests/unit/test_saved_campaign_delayed_injection.py`

native 目录索引含 **4,260** 件，变化仅限 host Python；编译输入没有变化。继续使用 `C:/cbr2/xar_ck3_bridge.dll`（9,459,712 字节，SHA `390506e486f5b19e298070523360d420de255a7811b5e79a5b279d5f9331dbbe`）与 `C:/cbr2/xar_ck3_bridge_injector.exe`（39,936 字节，SHA `2e22a985ba3166ce50ca1732901f0bac0629e8ff0f068de73330fdd5d09c86a8`）；现文件、manifest pin 均实际复验相同。构建回执继承 Source04 所指的原 Source02 `20261010-002/BUILD-RESULT.actual.json` 与 `BUILD-INPUTS.actual.json`，没有新 native build，也没有假定 Source04/05 存在新构建回执。运行路径、host、launcher、queue、keeper、MCP source 已实际绑定到 `C:/csr5`；运行时 metadata 为 `C:/workspace/ck3-common-runtime/20261010-004`。

原件与验证边界：

| 阶段 | 已发生的结果 |
| --- | --- |
| 外置 source-only 002 | 11 项 focused PASS、host help 与 apply-check 返回 0；历史 001 错误假定依赖存在而失败，未改源码，其失败原件保留。 |
| 主仓相关测试首轮 | 共 93 项：native lifecycle 48、saved admission 11、entry 20 均 PASS；delayed 14 中一项旧 lease-mtime fixture 失败，原 RED 保留。 |
| 夹具窄修后 | 只把测试 marker mtime 明确设为 epoch+1 秒；delayed 14 实际 PASS，未重复前述 79 项。最终适用覆盖为 79+14=93；mtime 是原失败的源码分支推断，当时未记录实际 mtime。 |
| 固定 Source05 | saved lifecycle **14 PASS**、四个新 global routing 边界 **4 PASS**、host help **exit 0**；精确源码、argv、stdout/stderr pin 已复验。 |
| 本次独立复核与归档 | 静态派生三项、单父链、五路径增量、全索引字节、原生与 manifest 绑定实际 PASS；没有重跑测试、构建或启动 CK3。 |

此时 Source05 manifest 中所有 `actual_live_qualified` 仍为 false，资格仍为 `PYTHON_FIX_NATIVE_INPUTS_EQUAL_NOT_LIVE_NOT_PRODUCT_PASS`。本包不纳入未来 R42 的启动、连接、事件、业务、关闭或正常退出结论。R41 原启动失败和退出证据缺口见[原场报告](2026-10-10-r41-shared-runtime-startup-red.md)；前驱 Source04 完整证据见[独立报告](2026-10-10-shared-delayed-injection-source04.md)。exact `0c0e36e21` 官方 CI 原失败与 cache reviewer 夹具 9 PASS 另见[独立 CI 报告](2026-10-10-common-cache-reviewer-ci-fixture.md)，本地修复 PASS 不追认该次官方成功。

永久证据为 [INDEX.json](acceptance/2026-10-10-shared-saved-debug-source05/INDEX.json)、[FACTS.actual.json](acceptance/2026-10-10-shared-saved-debug-source05/FACTS.actual.json)、[VALIDATION.actual.json](acceptance/2026-10-10-shared-saved-debug-source05/VALIDATION.actual.json)、[RAW-EVIDENCE.zip](acceptance/2026-10-10-shared-saved-debug-source05/RAW-EVIDENCE.zip) 与[只读封存生产器](acceptance/2026-10-10-shared-saved-debug-source05/package_evidence.py)。ZIP **175** 件、**1,433,978** 字节，SHA `0fcb65487693b446ba9f7258a88c0639203cda251e7360333fc6debd1d6019cd`；收作者候选与集成原件、两次独立审核、root 派生/冻结/绑定/固定源检查回执、新五项源码及原构建链小件，27 个原声明 pin、全成员/原件 SHA 和 CRC 实际复验通过。候选中复制的 1,176 项未变依赖留在外置目录，以原 manifest pin 保全，不在紧凑包重复；首份过宽外置归档及生产器派生记录保留。Source04、CI 原 ZIP 不重复。

完整 `shared-source05.zip` 只 pin：**53,556,929** 字节，SHA `87af317bf149c7acea82ebc07b9a476709bfca3174687e281812a09d603fb3fd`；临时 whole-repository Git index 亦只 pin。未打包存档正文。
