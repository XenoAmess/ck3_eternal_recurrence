# Episode 03：原版 CUnit 0 与实机恢复补丁

本包修复战争第三期取材时真实出现的阻点。游戏为 CK3 1.20.0.3 / Steam build 25652598，EXE SHA-256 为 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`，与[实际 William 验收与证据索引](episode03-william-lewes-live-2026-10-03.md)相同。

## 实际故障与修复范围

原版威廉主军的 public CUnit ID 为 **0**。旧的正整数检查把合法主军拒绝掉，阻断军队查询、导航、合军和规划。新增共享 public-unit 合同严格接受非 bool 的 `0..INT32_MAX`；C++ provider、Python DTO、MCP 参数及已有策略消费者使用同一边界。其他角色、战争、地区及 private 身份没有因此一并放宽。

独立 CArmy 身份也实际出现 0。只调整 ArmyStrength 的 nullable `native_carmy_id` 字段，保留其他 CArmy 身份约束。实机读回了合军后的 6,746 人、强攻次日的 6,578 人以及城破后的 6,384 人。第一份读数早于强攻，不能冒充同日独立基线。

原生 army route provider 补齐 `route_status` 与 `source_count`，保留严格 DTO 检查。环境层以严格 OEM CSV 解码读取 tasklist，并与 Toolhelp inventory 互证；战争 assessment 的超时参数保持正数、有限值检查。桌面恢复工具以 binary stdio 保存 Windows SC 的实际 OEM 输出，在主线程解码，避免中文错误文本触发 reader-thread UnicodeDecodeError。真实 SC access denied 仍是失败，不能因解码成功写成恢复成功。

这些补丁不启用额外 private 功能，不修改游戏玩法参数。真实取材的 production DLL 全部 117 个 private 选项 OFF；完成过程、原始失败和源码输入均永久保存在 `D:/ck3-war-episode03-20261002-a01/`。

## 已完成的验证

| 验证组 | 实际结果 | 永久保留的外置证据 |
| --- | --- | --- |
| Native public CUnit | 12/12 CTest；最新 army fixture 另有 isolated MSVC 验证 | `native-unit-zero-test-a03-20261002T134857793910.json`、`native-army-route-ci-report.md` |
| Core / CArmy 单字段 | normal 和 `-O` 各 91 tests；19 个 producer→serializer→DTO rows | `carmy-zero-strength-source-pins-a04.json` |
| Battle / simulation | normal 和 `-O` 各 227 tests | `unit-zero-battle-contracts-a01/verification.json` |
| MCP / UI | normal 和 `-O` 各 28 tests，含真实 MCP 参数分派 | `unit-zero-route-strength-a01/test-attempt-03/tests.json` |
| 最终 planner 边界 | normal 和 `-O` 各 16 tests +35 subtests | `strategy-public-cunit-a01/final-a03/test-results.json` |
| 正式 CI 新增命令的本机执行 | normal 和 `-O` 各 30 tests +351 subtests | `ci-public-cunit-a01/verification.json` |
| SC OEM 错误输出 | normal 和 `-O` 各 7 tests | `sc-oem-decoding-fix-a01/report.md` |

以上路径均相对外置永久目录，报告绑定执行时的精确源码。后续 rebase 改变文件字节时，以新增受影响测试回执限定最终结论，不能移植旧 source pins。

CI 保留 Windows x64 MSVC C++20 的真实 army fixture 编译、执行，以及 normal/`-O` 的三项 route DTO 检查，新增四个 public CUnit pytest 模块。官方 runner 不运行 CK3；最终主线 commit 的官方结果由第三期交付收据另行记录。

较广 gameplay suite 的三项失败已在 before-source 重现：callback 不接受 `prewar_arbitration`、旧 MCP expected tool-set 少 8 个 UI tools、R0118 旧标签与当前 scope 不符。本包不把它们改写为全套 GREEN，也没有删除这些测试。

## 2026-10-03 02:30 最终主线组合源码验证

源包在 `238bbc13d9b6fca9bdc2718e093d52eeafcf5432` 合入当时最新master后，9个受影响的pytest module/class targets在normal与`-O`下各 **87 passed、384 subtests passed、1 skipped**，退出码0；1216个source/test/fixture pins前后完全一致。唯一skip是未显式开启的桌面集成 `test_watchdog_ready_authenticates_the_parent_object`，不冒充PASS；新增CP936完整CSV回放另实际1 PASS。仅适配主线上已有的两项tasklist测试方法，保留损坏PID fixture的 `injector_attestation=None`。证据为 `post-rebase-scoped-tests-a02/verification.json`，SHA `dba983973a72a601258626a1244137534d61bbcbdb51fb8d7c89b5eebcda1e5a`；隔离MSVC army compile/fixture另见 `post-rebase-army-msvc-a01/`。

最终fresh Release/Ninja原生构建完成4个production targets与11个fixture EXE，**12/12 CTest**；实际cache中117个XAR BOOL全OFF，源码/header/CMake前后未变。外置wrapper起初只计main文件115项而拒绝收口，纳入included module的另2项后继续同一已通过configure，原guard失败保留。`native-final-master-a05-result.json` SHA `51a0c7c76eb74609d3f42eb02f91dffd1d04dcff12941f32f93ce80d70abab0d`、报告 `native-final-master-a05-report.md` SHA `f06339842c156443ea25e40cb51d4fd28c15285cf1fab490779eeca520db1c05`。新DLL4522496字节/SHA `ff78e2249d4a44fcf712dfca30655b914bcdec012cc9afdc749e3d18d1dde7e3` 未部署或加载，本段只证明组合源码的离线构建与fixtures；R0156继续绑定原实机DLL及输入。

## 实机资格与边界

实际 R0156 为 `desktop-3fevhd2-1c74096080--vanilla--R0156`，execution ID `76f24633-87c9-4c12-907f-001cf0b6a9f1`。威廉独立原版案例完成正常围城、增援、合军、强攻启动与停止、城破后的独立读回和正常保存。SDK 源码输入 387 项在 capture 后、stop 后均无变化；211 个模块 origin 已核对；进程树与屏幕排他槽已释放。

它是本次围城教学案例的有界实机闭环，不增加罗贝尔长期日数、G2 固定验收项、百年或整局自治资格。详细日期、UI 精度、伤亡归因及战分的限制见[实机专题](episode03-william-lewes-live-2026-10-03.md)与[证据索引](episode03-william-lewes-evidence-index.json)。
