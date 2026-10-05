# R0168：暂停实机完整月净额 — 2026-10-05

本记录闭合 exact CK3 1.20.0.3 当前角色个人金币的**完整月净率 primitive**，更新[当前费用专题](war-cash-current-resources-12003.md)此前“新 DLL 实读待验”的切点。原始无标记 NET 字段的历史误标及其追加勘误继续保留，不能追认旧帧为已验净额。

Root 在 R0168 原始 Jan11 冷载执行既有 `ck3_query_war_cash_current_resources_private_v1(expected_revision=3)`。前后独立状态均 William33388、alive/map_ready/paused=true、`native:2`、public3/native2、date_raw53147160，新增游戏日0。实际 cash response 的 body 与 Root 导出的 cash-body JSON 完全相等。正文是只读文件对账，未执行 SDK、桌面、游戏、安全设置或测试 EXE。

| 同帧实际量 | signed raw /100000 | 金币口径 |
| --- | ---: | --- |
| 个人金币库存 | 65418341 | 654.18341，存量 |
| 月总收入 | 469417 | +4.69417/月 |
| 完整月支出 | 439469 | 4.39469/月，包含军事 |
| 月净额 | 29948 | +0.29948/月，收入−完整支出 |
| 当前军事维护 | 388749 | 3.88749/月，角色跨全部战争各计一次 |
| 全部集结的替代军事维护 | 487050 | 4.87050/月，另一个当前原生反事实总量 |

实际语义标记为 `ck3-1.20.0.3-native-income-minus-total-expenses-v2`，time_basis=`month`、source_scope=`played_character_personal_gold`、military_expenses_included=true，gross/total/NET及同帧、两种军费所有7项 readiness=true。`469417−439469=29948` 是原生收入和完整支出的可审合同；不按 HUD `+0.2`/`+0.3` 数学拟合，不除30。军事已含于 NET，不能再扣3.88749。current/all-raised 两值不相加、不按战争数重复计入；两种十槽 vector 均只有 slot0 非零、slot6 treasury=0，资源槽不能混为个人金币。

`advertised=false`、`formal_action_ready=false`、两项 future_war_cost_upper_ready=false 仍为实际状态。此同日暂停样本不是累计收付流水：无法由余额差认定纯行军费，未闭合登船实际付款、逐军分摊、未来战争费用上界/风险预算/最低保留金币或完整预算控制 loop；不增加 TERM、A/B/C 或成片信用。

## 原始包与来源

源为冻结 `C:/w/e4a02` 提交 `ffc29e7c6f616592c0186f18570759eb36f30206`、a07 native build；exact stock EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。源码字节 pin 如下，冻结运行树未修改。

| 源文件（native_bridge 相对路径） | 字节 | SHA-256 |
| --- | ---: | --- |
| `src\ck3_12003_war_cash_current_reader.cpp` | 8704 | `47d9802384694277dd2169ac3a76e80644047b1e42355dc14d792f5b87b85040` |
| `src\ck3_12003_war_cash_current_serializer.cpp` | 7092 | `f6da1c9345235454f98eb72b48cb5f876ecab3d5ae83327c23117f4c2c15cd9e` |
| `include\xar_bridge\ck3_12003_war_cash_current_reader.hpp` | 3956 | `36ae77f56c3425bf0925d9f088c6b223aa025e3d99509f00979e948df95e0d5f` |
| `src\ck3_12003_war_cash_net_income_test.cpp` | 10749 | `95e096311f67b2601709615e0742c88a3202c5533c14dd5a386227aeaeda6666` |

原始响应均在 `C:/ck3-war-episode04-research-20261004-a01/native-live-merge-r0168-originaljan11-a01/responses/`：

| 原始来源 | 字节 | SHA-256 |
| --- | ---: | --- |
| `r0168-paused-initial-a02.json` | 168966 | `b7057838d34d8c31d79d165d207ecf010e5c4bd23300ab8f4a03861b4f7a28cf` |
| `r0168-net-cash-a01.json` | 15915 | `f9916759317e8f1285b3f6f9dcfac5bff129bffa0ad40f042852e5e88981d584` |
| `r0168-net-loss-after-a01.json` | 1054054 | `7a5a8ff069310a90ef997ce290fc956e8a6720c615e9c8029c22946e92c9a71b` |
| `root-r0168-net-loss-probe-a01/cash-body.json`（CROOT相对） | 3488 | `c2a153c2b8081cbb6908f87c9ddf81ac7415b7baa17688372e54d606b6fc7d21` |

外置 `cash-net-live-r0168-closure-a01/VERIFIED-CLOSURE-a01.json` 为3173B / SHA `fb75658ded5832739002bd7620268a75b1c286dd8f4292b6a8f4fc43e1c00793`；该有限对账保留实际 query、前后身份和原 packet，不覆盖任何失败 attempt。

## 已有登记门禁后的实际 focused 验证

Root 实际执行 a07 两项 focused CTest，生产 C++ reader/serializer 与已注册的 in-memory MCP 共6cases/52checks通过。`native-net-ctest-a07-a01/RESULT.json` 为4665B / SHA `f170ac3e9a53de77d455a37148bcb577cc03e1b0f36566f26463af77c5eb53bb`，ctest_returncode=0；其 admin gate 绑定已验证登记收据 `998ea9c2d65fc449fecdf0ffa473cefc027ffe654848ee45aa59585fb90e3618` 及 a07 test EXE SHA `689a6f33ba746fc67481799a8937de70c0ca782c3988ab372bdf090e8f37536f`。不是将提醒前旧未登记执行重写为符合门禁。

六份实际 wire 位于该 attempt 的 `native-wire/`：

| wire | 字节 | SHA-256 |
| --- | ---: | --- |
| `negative-net.json` | 2659 | `37b15fb6ad3c26503bc3d3298e32ce8af141057e01e63a49863cd117125ab67a` |
| `zero-net.json` | 2643 | `ba401b164895b7c61091d3998ffcaed4caa11e22ebd07df9de4c656f70b06389` |
| `context-unavailable.json` | 2727 | `1c4ed64359382136427577d5b1519841ace46dd7cdb991b2ef26699e28a18b66` |
| `income-unavailable.json` | 2727 | `1c4ed64359382136427577d5b1519841ace46dd7cdb991b2ef26699e28a18b66` |
| `expenses-unavailable.json` | 2718 | `532c59bcbfd91b1ff7e01c32420826211f45d212949d61ae6699597aade45a17` |
| `overflow-net.json` | 2707 | `78247f01ac92a87715e41b91e7495b062090be0dd9b16970ecf4d4498ee1a23a` |

注册 MCP `registered-mcp/RESULT.json` 为14087B / SHA `f3e0f5f89f99cf909302a9a941667d2189d4793069a6210d01760854459a36f7`。这些实际离线 tests 支持失败/null、合法零、负净额、overflow与producer→serializer→normalizer合同；单独的 R0168实机回包才闭合新 DLL 当前月净率，二者范围保持分开。
