# 任命候选人的原生等级只读诊断（1.20.0.4）

2026-10-10：共同 MCP `ck3_query_current_title_appointment_v1` 新增可选 `diagnostic_character_id`。它读取当前任命窗口对应规则下指定完整角色 ID 的原生等级；角色可以不在候选池内。原候选池、分页、`breakdown_character_id` 和评分行为不变，各产品复用同一入口。

只接受 EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。读取在已暂停的 application-owner mailbox 内进行，沿用真实窗口、完整角色/头衔 ID、会话和 revision 门禁，以及读取前后窗口/规则/候选池/法律一致性复核。新增叶节点也复核完整身份并采样两次；过期身份、读失败、数据变化或未支持来源返回 unavailable，派生字段为 null。

## 已证实的范围

当前规则 `+0x148` 的原生 ordinal 0 路径经 `0x320F46B..0x320F4D5` 调用 `0x28BE1D0..0x28BE226`。角色 `+0x1B0` 的扩展中，`+0x178` 是 signed64 累积值，`+0x180` 是 signed32 等级上限；全局阈值表 `module+0x5458818`、数量 `+0x5458824` 决定等级，负上限不封顶，空扩展按原生语义返回等级0且 raw 字段为 null。头衔 template `+0x64` 的 tier 索引 `module+0x5461660` 得到最低等级；原生分支以 `level < floor` 拒绝，因此相等通过这一分支。

返回的 `character_level_diagnostic` 包含 available/reason、完整角色和当前头衔 ID、来源 ordinal、扩展是否存在、raw 累积/上限、原生等级、tier、最低等级及比较结果。此比较不是完整入池资格。ordinal 0 与脚本字符串 `merit` 的命名映射尚未证明；其他 ordinal 明确 unavailable。canonical Native71 的 RESOURCE14 `+0x170` merit balance 不是本字段，不能混为一谈。任命冷却期实际值及语义仍未证明，接口不提供猜测的 cooldown 字段。

## 一次实际构建与离线验证

实际08:32:37.621225Z开始、08:39:24.428881Z结束，总406.81秒。完整573对象图中21个必要编译、552个编译器及依赖等价对象复用，归档和 DLL 链接 exit0。首次配置漏继承父 `/WX /utf-8` 时等价检查拒绝复用；该 attempt 的 exit15 和产物保留。recovery02 只纠正配置继承，在原15分钟窗口内完成。

新focused target `xar_ck3_12004_appointment_character_level_test` 编译/链接/唯一执行均0，10项 mock 用例通过，包括完整generation、精确EXE、unsupported ordinal、空扩展、阈值与floor相等、cap、第二采样变化、过期头衔、不可读字节及表上界。新测试EXE在执行前完成精确路径 Defender 管理员实际读回。统一stdlib入口 `ck3_autonomous_player/tests/test_appointment_window_contract.py` 保留原8项并新增12项，实际20项通过；已接入现有 static CI，无新增产品测试工具或MCP安装依赖。

- [实际构建回执](C:/workspace/ck3-upgrade-20261010/r58-appointment-level-shared-mcp-wiring-03/actual-native-build-01/recovery02/result.json)：18656 B / SHA-256 `84f607eed851d46a85fb085414c277a2bbbd22bb7d0d36a0c71614a45c9b9ef9`。
- [新冻结 DLL](C:/workspace/ck3-upgrade-20261010/r58-appointment-level-shared-mcp-wiring-03/frozen-native-level-01/xar_ck3_bridge.dll)：9078784 B / SHA-256 `27db8da0c740b3334ce661b73d4ef618de87fda24f3b91f705f3b31bef7bfe19`。
- [原生输入索引](C:/workspace/ck3-upgrade-20261010/r58-appointment-level-shared-mcp-wiring-03/NATIVE-BUILD-INPUT-INDEX-01.json)：4175556 B / SHA-256 `099cc2aed5bac9ff8564415193169ea7904e2e45fe49aa19e70039c1b978dfc8`，6917行/11delta；原生权威源码是其 `native-source-candidate-01/ck3_autonomous_player/native_bridge`。
- [最短消费卡](C:/workspace/ck3-upgrade-20261010/r58-appointment-level-shared-mcp-wiring-03/ROOT-NATIVE-LEVEL-BUILD-CONSUME-FINAL-05.md)。运行时应继承 Source14 并只投影四个共同 Python 文件，不能把原生构建输入树直接当当前 Python runtime。

这些结果为 BUILD_AND_FOCUSED_MOCK_PASS_NOT_LIVE。旧 Source14/qa12/fd1f 原件未改；实际角色31883的值、入池原因、后继Source15选择和新DLL实机资格仍待新场。原R58失败不追认，政府产品、完整QOL及正式release均未因此完成。
