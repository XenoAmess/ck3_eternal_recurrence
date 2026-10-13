# REA 对 G2 的帮助评估（2026-10-13）

REA 适合辅助原生来源追踪、减少重复分析和整理证据；建议先作为隔离的静态逆向 sidecar，保留现有 Strategy、Service、NativeDriver。它不提供 CK3 选敌、调兵或跨代规划，也不能证明宣战成功或战争获胜。本次只浏览官方文档、源码和测试，并核对文件身份：**未安装、未运行 REA 或其测试，未占用游戏、屏幕，未取得 REA 的 CK3 实测结果**。

## 固定版本与实际差异

本次检视固定 main **`bb154d1067b0fc250452b7d468d0b0523031a16f`**（2026-10-13 03:24:05 UTC）；当时最新正式发布为 [rea-agents-6.4.0](https://github.com/morluto/rea/releases/tag/rea-agents-6.4.0)，commit **`a56f7bb668ab23fec8d33f7af353ac7ed2fe1895`**（2026-10-11 03:58:03 UTC）。main 仍自报 6.4.0，但已领先 **376 个提交**。逐文件核对的 `EvidenceLedger.ts`、`AnalysisSnapshotCache.ts`、`AnalysisViewService.ts`、Windows guide、CLI guide 和 `package.json` 六项均与正式发布字节不同。以下机制对应固定 main，不能仅凭版本号外推到已发布包。

## 可采用的机制及边界

原生分析可组合函数 dossier、精确 call target 和 p-code def-use，按恢复的参数 ordinal 连接 CALL 与 RETURN。它保留间接调用、缺失参数及截断的未知项；LOAD/STORE 不自动说明对象字段、TLS、持久状态或 RNG，静态路径也不证明运行时到达。[追踪源码](https://github.com/morluto/rea/blob/bb154d1067b0fc250452b7d468d0b0523031a16f/src/application/native/NativeValueTrace.ts#L327-L400)

证据层值得借鉴：不可变 `evidence_id`、冲突拒绝、原子导入和带 revision 的残余未知；闭合清单要求实现 owner、必要 case 和具有可比 authority 的独立 verifier。这能帮助八组研究分别记账源码、测试、实机与业务结果。证据保存幂等不能保证游戏命令零重送。[EvidenceLedger](https://github.com/morluto/rea/blob/bb154d1067b0fc250452b7d468d0b0523031a16f/src/application/investigation/EvidenceLedger.ts#L43-L172)、[闭合合同](https://github.com/morluto/rea/blob/bb154d1067b0fc250452b7d468d0b0523031a16f/docs/reconstruction-obligation-ledgers.md#L1-L16)

完整原件先保留，再返回带 parent ID 的小视图，可减少重复大响应。静态快照绑定 target、provider profile 和查询参数，排除 live、cursor、mutation；它是已有观察，不是游戏 SAVE 或长局记忆。新连接不继承旧 ledger，必须显式导出、导入，并继续执行本仓库存储期限。[视图实现](https://github.com/morluto/rea/blob/bb154d1067b0fc250452b7d468d0b0523031a16f/src/application/analysisView/AnalysisViewService.ts#L88-L143)、[快照合同](https://github.com/morluto/rea/blob/bb154d1067b0fc250452b7d468d0b0523031a16f/docs/cli.md#L154-L189)

G2 的[宣战资格](../../ck3_autonomous_player/src/xar_autoplayer/ordinary_prewar_force_admission_v2.py)仍要求当前暂停帧、角色、日期、连接代次、独立 receipt、完整力量覆盖与原生合法性。REA 分析不能替代这些材料。其 Ghidra 超时 close/reopen 只用于静态 provider；**不得接入 live SDK 重启或重送**。在途 CK3 查询继续由同一 Driver 收集原 request ID，保留零重送守卫。[REA 恢复合同](https://github.com/morluto/rea/blob/bb154d1067b0fc250452b7d468d0b0523031a16f/docs/mcp-contracts.md#L382-L452)

## 最小试验（尚未执行）

1. 闭场后另建独立 attempt，核实际 Node、provider、包字节和 schema，不更改全局 agent 注册，不与游戏现场竞争。
2. M0 只查已有定位 **`0x2BAA6F0`、`0x880430` 两个函数**，先确认 RVA/VA 和实际映射；限深度、函数数和输出，对照保留的原始 bytes、反汇编，核 callee、callsite、参数 ordinal 与 context 来源。缺失 TLS/alias 材料保持 unknown。
3. 保留 dossier 后读取小视图，量测额外 provider 调用、bytes 和冷暖耗时；对固定静态查询验证快照复用及错 target/profile 拒绝。`trace_native_values` 分页会重新分析，不能混同于原件视图读取。
4. 仅补出一个可独立核实的新来源叶或证明重复成本下降后，才扩到 M5；M5 必须先取得实际 declaration tuple 和 Node，再核具体 operator/callee。宣战资格、真实业务结果与胜负另行验收。

## 依赖、许可与交付证据

Windows Ghidra P0 仍为实验性只读边界，要求支持的 Node、本地固定 NTFS、匹配 native addon、Ghidra 12.1.x 和其声明范围的完整 x64 JDK；已验证组合为 12.1.4/JDK21。本机安装成本和 CK3 大二进制冷启动未测，不给数字承诺。上游含 PowerShell 范例，本项目后续包装须用 Python argv/env。[Windows 条件](https://github.com/morluto/rea/blob/bb154d1067b0fc250452b7d468d0b0523031a16f/docs/windows-ghidra-p0.md#L9-L40)

REA 自有代码为 [MIT](https://github.com/morluto/rea/blob/bb154d1067b0fc250452b7d468d0b0523031a16f/LICENSE)，复制实质代码须保留版权和许可；[第三方 notices](https://github.com/morluto/rea/blob/bb154d1067b0fc250452b7d468d0b0523031a16f/THIRD_PARTY_NOTICES.md)独立适用，REA 不提供 IDA、Hex-Rays 或 Hopper 的商业工具许可。源码存在及注入 provider 的测试不能替代真实 engine 验证。

小型报告、版本比较及逐文件 SHA 回执位于外置 `g2-remediation-20261013/resume02/rea/`：`REA-ASSESSMENT.json`、`SOURCE-RECEIPT.json`、`UPSTREAM-VERSION-RECEIPT.json`、`RELEASE-FILE-COMPARISON.json`、`CLOSE-RECEIPT.json`。闭场前逻辑量 334,173 bytes；共用原 8 GiB，复核期限仍为 2026-10-13 16:58:39 UTC，未续期。可重取源码适用派生期限，小型结论适用记录复核规则。
