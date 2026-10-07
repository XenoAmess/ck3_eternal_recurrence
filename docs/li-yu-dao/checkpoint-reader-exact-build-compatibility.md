# Checkpoint reader 的精确 .3/.4 build 兼容

R0020 切换到本机实际 CK3 1.20.0.4 时，既有 checkpoint 资格链把 HELLO/adapter 和 G2/G3 envelope/payload 固定在 .3，会在同帧 saved join 前拒绝新的实际观测。本次只扩展精确 build 对应项；原 checkpoint/DTO/schema、7 字段 frame binding、saved 完整 AST/ownerFaith/title join、完整集合、保护/readiness、PID/generation 与未知信用条件保留。

| version | exact EXE SHA-256 | HELLO adapter |
| --- | --- | --- |
| 1.20.0.3 | `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6` | `ck3-1.20.0.3-msvc-x64` |
| 1.20.0.4 | `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518` | `ck3-1.20.0.4-msvc-x64` |

版本、SHA 和 adapter 必须属于同一项；未知或混用项拒绝。checkpoint 前后项必须相同，G2/G3 envelope、操作专属 backend 和嵌套 payload 也必须与 checkpoint 同项。backend 分别为该 version 的 `native-confucian-assembly-predicates-v1` / `native-confucian-religious-title-v1`。既有 `ck3_12003_confucian_*_v1` 是软件 wire/schema namespace，.4 实际 producer 保持这个名称；reader 保留原 schema，不把 .4 原件改写成 .3。

.3 的三个 G3 static index 原值保留；.4 的 title properties/laws/head getters 三项都严格对应实际 finite map SHA `5f5a1005711ef523bcd228c1b2ff2822a9767e13c1b9a934f9a3a87f37287e3d`。9 个 qualification 字段、reference identity offset8/title full ID offset16/fallback `0x5D1E2E0`/runtime_acceptance null 保持实际新 producer 声明；没有用旧 .3 index 冒充 .4 资格。[实际 .4 map 原件](acceptance/2026-10-07-r0020-exact-build-reader/ACTUAL4-TITLE-MAP.original.json)。

必要的当前 DTO 版本分支改变了三个纯函数 AST，故同步更新当前 trusted primitives exact SHA 为 `4202e23626327c33908389e1e8f5b8ad8c6cf1f890a32141d5de69fd9a724aee`，并从当前 pure source 精确生成 inert codec fixture。lineage 继续验证实际 codec 的 bounded bytes/SHA 和全部 12 个纯函数 AST，没有跳过 hash/AST 或读取并执行 codec。旧 .3 历史包、SDK/reference、原 reader source pack 与失败原件保持历史原样；不拿新源去重验旧运行。

源码入口：[strict qualification](../../tools/lyd_i3b_checkpoint_readback/reader/sdk_checkpoint_qualification.py)、[transition qualification](../../tools/lyd_i3b_checkpoint_readback/reader/sdk_checkpoint_transition_qualification_v2.py)、[pure DTO](../../tools/lyd_i3b_checkpoint_readback/reader/dependencies/confucian_dto_primitives.py)、[codec lineage](../../tools/lyd_i3b_checkpoint_readback/reader/sdk_artifact_lineage.py)。CLI/request/output schema 沿原实现；新冷包必须从最终 actual export 一次复制完整 reader 目录及当前 codec，再生成实际 descriptor、source/inventory/hash，不沿用旧 R19 helper SHA。

本次在独立 `C:/lci20reader1`、base `2f5bb0759dbf792865f30c1ec9fba7eee1bce4dc` 验证四个新增 focused 方法及原两个相关测试模块，共 **54 tests exit0**。完整 old/new inert qualification 路径通过；mixed HELLO/version/image/adapter/backend/nested/checkpoint pair、wrong .4 static index、codec AST 改动均拒绝，原 frame/protection/AST 漂移负例继续通过。fixture 不访问 CK3、SDK、进程或 checkpoint body。初次 source AST 缩进错误在测试运行前被检查发现并纠正，原工具失败保留；没有实际业务动作或历史 artifact 重验。

[小型 source/test 索引](acceptance/2026-10-07-r0020-exact-build-reader/INDEX.json)。这只授予源码和 inert 测试信用；R0020 最终 qualified native build/官方 metadata/.4 live G2/G3/saved checkpoint/formal 信用均待 ROOT 后续实际回执。整个 mod **NOT_GREEN**。
