此包记录 a39 的生产构建、精确 EXE 登记和有限冷验收。`machine_id: desktop-3fevhd2-1c74096080`；整理观察时间：`2026-10-20T03:11:27.838379+00:00`。原始 Q、读回、失败回执、计划和容量回执均逐字节复制，既有 pins 保持原值。

构建来源为 `43fd32670897f657da681cf0a94d162e3135a89c`；冻结 runtime 为 `76dcbf7fe4526117fc25f0c892593b570f0a8b68`。两者 native tree 均为 `28dda02c23eda2efdc0a09c8a9cba122dd06cca9`，来源绑定见 [机器与树身份读回](SOURCE-EQUIVALENCE.actual.json)。整理时未修改冻结主树；机器身份通过公共 machine 工具只读核对。未执行构建、冷例、SYSTEM 设置或 CK3 操作。

| 层级 | 已实际确认的范围 |
| --- | --- |
| 生产 3 项 | DLL、host、injector 的构建与精确产物 hash；host/injector 未执行。生产与已链接的六个冷例产物在最后补建中保持原 SHA。 |
| SYSTEM 9 项 | 九个最终 EXE 的精确路径和 SHA 由实际 SYSTEM 回执验证：`verified`、`admin_token=true`、`S-1-5-18`。 |
| cold 7 项 | 七个 CTest 首次执行全部通过，共 0.62 秒；实际 cache 为 183 BOOL、33 ON、150 OFF。steward finite 项只确认实际共享注册和邮箱的 owned-memory 生命周期，不授予 steward 业务或 production WarOverview 验收。 |

首场真实 C1083 来自现有 war-cash 净收入 target 缺失研究头/链接闭包。提交 `43fd326` 只给该 target 增加 `target_link_libraries(... PRIVATE xar_ck3_12002_runtime)`；生产 TU 字节未变。第二场在同根仅增量 28 步，生产 3 项和原六个冷例全部链接成功，war-cash 修复获实际验证。

第二场的 B11 `gates_off` 仍以 17 个未定义符号结束：该消费者要求 allON provider 库，而本场保留新增 provider OFF。此项属于冷例选择 RED，完整保留，未声称通过。最终换用已逐 TU 审核依赖的现有独立 steward mailbox finite target，同根只补 12 TU 后完成 SYSTEM 和七个冷例；未开启新 provider，未复制整树重编。

[最终 Q](ROOT-A39-PRODUCTION-QUALIFICATION.actual-a03.json) 与 [独立读回](A39-FINAL-INDEPENDENT-READBACK.actual-a03.json) 仍明确 `live_CK3_qualified=false`、`R04_closed=false`。a39 实占及观测峰值均为 435,781,465 B，存活 EXE 为零，剩余 heavy 写入需求为零；同一 1 GiB native future 已结算为零，未当作物理释放量。

此小包不携带二进制、完整日志、compile database 或大构建对象。JSON 内的原路径/pins 按历史原值保留；未打包的原始资产不因此成为永久保护项。其可读性和到期处置按通用存储策略及实际清单另行核实。当前 R0216 的实机结果由其独立场次证据记录，本包未新增该资格。
