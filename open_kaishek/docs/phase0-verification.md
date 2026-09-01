# Phase 0 验证记录

记录日期：2026-09-01（Asia/Shanghai）

本记录描述当前 `open_kaishek` 静态基线的可复核结果。它只证明源码、合同和离线夹具
的一致性，不证明 CK3 会加载这些脚本，也不构成 MCP 差分认证或 `product-live` 证据。

## 冻结/观测环境

- JDK：Eclipse Temurin `21.0.10+7`（`--release 21`）。
- Maven：Apache Maven `3.6.3`；离线验证使用本机缓存并显式设置
  `-Dmaven.repo.local`，项目本身不依赖开发者目录。
- 项目许可证：Apache-2.0，见根目录 `LICENSE`。
- 运行时依赖：核心模块没有第三方运行时依赖；JUnit 只在测试 classpath，构建插件及
  许可证见 [`THIRD_PARTY_LOCK`](../THIRD_PARTY_LOCK)。
- CK3 profile：`ck3-1.19.0.6`，EXE SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。

## 可重复命令与结果

在仓库根目录执行（Windows）：

```powershell
cmd /c "set MAVEN_OPTS=-Duser.home=C:\Users\xenoa&& mvn -o -Dmaven.repo.local=C:\Users\xenoa\.m2\repository clean test -f open_kaishek\pom.xml"
java -ea -cp 'open_kaishek/kaishek-syntax/target/classes;open_kaishek/kaishek-syntax/target/test-classes' com.xenoamess.kaishek.syntax.ParserSelfTest
java -ea -cp 'open_kaishek/kaishek-syntax/target/classes;open_kaishek/kaishek-syntax/target/test-classes' com.xenoamess.kaishek.syntax.DuplicateKeyRoundTripSelfTest
java -ea -cp 'open_kaishek/kaishek-syntax/target/classes;open_kaishek/kaishek-syntax/target/test-classes' com.xenoamess.kaishek.syntax.ParserCorpusRoundTripSelfTest --root mod_zhongguo_style --require-corpus
java -ea -cp 'open_kaishek/kaishek-cli/target/classes;open_kaishek/kaishek-cli/target/test-classes;open_kaishek/kaishek-validator/target/classes;open_kaishek/kaishek-ck3-11906-profile/target/classes;open_kaishek/kaishek-profile-api/target/classes;open_kaishek/kaishek-syntax/target/classes' com.xenoamess.kaishek.cli.KaishekCliSmokeTest
cmd /c "set MAVEN_OPTS=-Duser.home=C:\Users\xenoa&& mvn -o -Dmaven.repo.local=C:\Users\xenoa\.m2\repository -DskipTests package -f open_kaishek\pom.xml"
java -jar open_kaishek/kaishek-cli/target/kaishek-cli-0.1.0-SNAPSHOT.jar corpus mod_zhongguo_style
& tools/.venv/Scripts/python.exe -m unittest discover -s open_kaishek/kaishek-zg361-profile/tests -v
& tools/.venv/Scripts/python.exe open_kaishek/kaishek-zg361-profile/tools/validate_domains.py
```

当前观测：

- Maven reactor：`BUILD SUCCESS`；profile-api 4、CK3 profile 4、validator 7、IR 6、
  runtime 19、diff 2、zg361 synthetic 4 个 JUnit 测试全部通过。Syntax/CLI 的无框架
  smoke 主类也由上面的显式命令运行（CLI smoke 无输出即表示通过），Maven 报告其
  JUnit 测试数为 0，这是有意的 dependency-free 设计。
- Parser corpus：27 个 `.txt/.gui` 文件、2,677,440 bytes、0 个错误诊断、字节级
  round-trip 一致。
- CLI corpus：27/27 parsed、0 errors；确定性 corpus SHA-256 为
  `30d63aad6adbe60a5df610dca4dcb2592f4e8d6dc5edb9a1d411744571cd687c`。
- Manifest：[`corpus-manifest.json`](corpus-manifest.json) 由生成器重建后无 diff；
  manifest 以显式 LF 写出，SHA-256 为
  `b219a2ee0ef3c9b77fbc0d28a7c99714e6e8b000b84bf4403d352999e3896ac3`。
- 361 schema：Python structural validator 与 8 个单元测试通过，覆盖 38 个 domain
  和机制 ID 1–361；Java validator 仅提供同一结构合同的无框架投影。
- Synthetic 014：BOM `.txt` 经 Parser → Validator → Strict IR → RuntimeKernel/IrExecutor
  走通 `delivered → appeal_open → closed`；未知 opcode、解析错误和 CK3 未认证语义均
  fail-closed。该结果属于离线 synthetic fixture，不是 CK3 live 或差分认证。

## Readiness 与未完成项

| 能力 | 当前状态 | 证据边界 |
|---|---|---|
| M0 工程/合同基线 | `static-ready` | 构建、许可证、manifest 和合同已落盘；正式维护者评审仍待完成 |
| M1 lossless parser | `static-ready` | corpus round-trip 与 malformed/GUI smoke；尚未完成全部 property/fuzz 矩阵 |
| M2 静态 validator | `static-ready` | 小型 profile/schema fixture；尚未覆盖全部历史故障 |
| M3 Runtime | `static-ready`（原语 + synthetic 014 fixture） | finite draw tape、stale/receipt/queue 合同与一个有限状态切片；不代表 CK3 语义 |
| M4 361 离线闭环 | `static-ready`（仅 synthetic 014 子集） | 已有一条生成 `.txt` → parser → validator → IR → VM 证据；完整 B2/Workforce exact-build 范围尚未开始 |
| M5 CK3 MCP 差分 | `not-available` | 没有 paused pre/post artifact，认证集合为空 |
| Quarkus 服务 | `scaffold-only` | 只保留外壳，按路线图延后依赖与适配器 |

下一步应先完成 M0 合同实例评审，再扩展 B2/Workforce exact-build 范围的 361 纵向切片；
在真实 paused artifact 出现前，不得把任何 ACK、fixture 或单元测试升级为 `fixture-live`、
`differential-certified` 或 `product-live`。
