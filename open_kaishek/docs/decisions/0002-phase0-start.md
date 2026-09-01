# ADR-0002：Phase 0（M0）开工与冻结门槛

**日期：** 2026-09-01
**状态：** 已批准开工；Phase 0 静态基线已形成，M0 待正式评审

## 决定

项目所有者已授权 `open_kaishek` 从前期预研进入 Phase 0 实施。当前已落地“合同冻结与工程决策”所需的文档、schema、构建工程和可复核的最小工具链；不把静态基线解释为 Runtime 或 CK3 实机已可用。

Phase 0 的完成门槛仍是 roadmap 中的 M0：

- 合同经过实例评审，能明确区分重复键、混合 block、scope、参数、事件、随机和 native port；
- 外部依赖均有许可证、固定版本、采用理由和 `THIRD_PARTY_LOCK` 记录；
- 核心模块无需 Quarkus 启动即可构建和测试；
- 第一批 corpus、CST/diagnostic/profile/IR/snapshot/trace/differential schema 可被审阅并可重复生成。

## 当前状态（2026-09-01）

| 项目 | 状态 | 说明 |
|---|---|---|
| Phase 0 / M0 | `static-ready` | 构建、许可证、manifest、profile/IR/runtime/diff 合同已落盘；正式维护者评审仍待完成。 |
| M1（lossless parser round-trip） | `static-ready` | 27 个目标 `.txt/.gui` 文件逐字节 round-trip 通过；property/fuzz 矩阵尚未完成。 |
| M2（schema validator） | `static-ready` | 小型 CK3 profile 与 361 schema validator fixture 通过；历史故障覆盖仍有限。 |
| M3（strict runtime synthetic 361） | `static-ready`（原语 + synthetic 014） | finite draw/stale/receipt/queue 合同与一个有限状态夹具通过；不代表 CK3 语义。 |
| M4/M5（exact-build / MCP differential） | `static-ready`（仅 synthetic 子集） / `not-available` | 014 夹具已走通生成脚本到 VM；完整 exact-build 范围和真实 paused artifact 仍缺失，认证集合为空。 |
| CK3 live / product-live | `not-available` | 没有 CK3 live artifact，不得写成 fixture-live 或 production-live。 |

## 冻结记录与剩余评审

以下是本次静态基线实际采用的版本；平台矩阵、CI 镜像和正式发布级 hash 复核仍在
M0 评审中，不以默认值冒充已决策：

1. **JDK**：当前验证基线为 Eclipse Temurin `21.0.10+7`，源码/目标级别为 21；平台矩阵和发行版 hash 仍待评审。
2. **构建工具**：当前采用 Apache Maven `3.6.3+`，插件版本固定于父 POM，离线验证命令见 [Phase 0 验证记录](../phase0-verification.md)；CI 镜像与 wrapper 仍待决定。
3. **许可证**：项目采用 Apache-2.0；核心无运行时第三方依赖，JUnit/构建插件的版本和 SPDX 信息已写入 [`THIRD_PARTY_LOCK`](../../THIRD_PARTY_LOCK)。Chronicle、CWT、PDXTools、Jomini 仍仅作研究输入，未复制源码。

上述剩余评审完成后，才能把静态基线升级为正式发布清单；当前构建文件只包含已记录的
测试/构建依赖。

## 本阶段允许与禁止

允许：编写并审阅 schema/接口草案、构建探针、最小 corpus 清单、许可证记录、静态
parser/validator 和 runtime 合同夹具。
禁止：声称完整 M1/M3/M4 端到端或 CK3 Runtime 已完成、执行或发布 CK3 Runtime、把
静态 fixture/ACK 当作 live、引入未经许可证审查的第三方代码，或为了“跑通”未知语义
而 silent no-op。synthetic 014 只作为离线夹具证据。

## 下一步与证据

下一项可交付是 M0 合同实例评审，以及扩展 B2/Workforce exact-build 范围的 361 纵向
切片。当前 synthetic 014 已形成“生成脚本 → parser → validator → IR → synthetic VM”
闭环，但每项结果仍必须记录命令、版本、hash、测试输出和未支持项；在真实 paused artifact
出现前，readiness 保持 `research`/`static-ready`，不升级为 `fixture-live`、
`differential-certified` 或 `production-live`。
