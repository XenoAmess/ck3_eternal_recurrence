# 宗教礼仪融合工具

Java 21 + 默认命令行 Maven 3.10.0 以上；Quarkus 为 CLI 宿主，无 HTTP 服务。玩家只加载生成的 CK3 内容。

在仓库根目录执行完整检查：

```text
mvn -f mod_religious_ritual_fusion/tools/pom.xml verify
```

生成器读取真实原版脚本并绑定 SHA（本机观察须传稳定机器 ID）：

```text
java -jar mod_religious_ritual_fusion/tools/target/quarkus-app/quarkus-run.jar generate --machine-id <current-machine-id>
```

默认游戏路径为仓库 `Crusader Kings III/game`；也可显式传 `--game`。CI 和没有游戏的机器重放入库目录快照：

```text
java -jar mod_religious_ritual_fusion/tools/target/quarkus-app/quarkus-run.jar generate --catalog mod_religious_ritual_fusion/catalog/generated-catalog.json
java -jar mod_religious_ritual_fusion/tools/target/quarkus-app/quarkus-run.jar validate
java -jar mod_religious_ritual_fusion/tools/target/quarkus-app/quarkus-run.jar build --output <new-disjoint-staging-path> --revision <full-git-sha> --machine-id <current-machine-id>
java -jar mod_religious_ritual_fusion/tools/target/quarkus-app/quarkus-run.jar verify --output <staging-path> --manifest <staging-path>.manifest.json
```

`tools/product.json` 为手工生产文件的显式清单，`catalog/generated-files.json` 只由目录生产者生成并自动并入清单。快照含来源相对路径、SHA、观察时间和机器 ID；它证明该机器观察时的源内容，不代表当前其他机器安装状态。游戏内运行不读取快照或游戏安装目录。生成文件不得手改；规则不支持投影时只禁该项并将原因写入快照。

构建拒绝旧输出、源与 staging 包含关系、缺文件、额外 runtime 文件、BOM 错误、内部 Workshop ID、脚本引用缺失、双语键不一致及生成内容漂移。不执行任意递归删除，不复制 docs/tools/catalog/fixture。静态检查与 staging 不能证明原生解析、按钮业务、创建后态或存档通过；实机按模组 docs 的公共验收入口执行。

## 独立实机 fixture

fixture 使用同一 Quarkus CLI 生成，和正式 67 文件载荷分开：

```text
java -jar mod_religious_ritual_fusion/tools/target/quarkus-app/quarkus-run.jar fixture --repo-root . --output <new-fixture-path> --machine-id <current-machine-id> --inputs mod_religious_ritual_fusion/tools/src/main/resources/acceptance/requests/core-rite.json
```

输入为严格 `Request`：`schemaVersion=1`、`kind=core|ui_rejection|cold_reload`、`mode=rite|faith`、`actorId=29829`。`setup` 为带 `type` 的封闭分支：新局 `{ "type": "fresh", "piety": 500 }`；冷读 `{ "type": "saved" }`，拒绝其混入 piety 或任何 seed 参数。`requests/` 提供两模式正向、499 虔诚拒绝和两模式冷读示例。

输出 `<path>.fixture.json` 严格采用公共 `ck3-mod-acceptance-prebuilt-fixture-v1`；`<path>.request.json` 单独保存输入，不混入游戏 fixture。manifest 固定完整文件表、源 Java／模板／目录 SHA、机器 ID 和观察时间。生产 Java 源与模板同时嵌入工具包，和当前仓库不一致时拒绝生成，防止旧 JAR 冒充新 producer。

新局 fixture 在首次启动后一天准备三个独立来源：A={esotericism, legalism, astrology}、B={esotericism, legalism, communal_identity}，B 同 Faith 与不同 Faith 各一份。使用原版创建／分离、知识和虔诚效果，仅写输入；完成一次后停止 seed，不调用 RRF 创建路径。目标最终集合为 {esotericism, astrology, communal_identity}，教义从 divorce_disallowed 切至 divorce_allowed。

实际生产 GUI 后调用 `rrfa.20`（礼仪）／`rrfa.21`（宗教）只读核对；`rrfa.30` 核取消／拒绝后钱包、身份和来源未变。冷读包不携带 seed 文件，启动时立即执行 `rrfa.22`。所有观察只运行谓词和日志，不写预期 flag、钱包、对象或冷却。精准钱包差要求暂停且日期不变；全局新增对象计数、冷却到期日和自然收入归因仍须公共原生／存档独立读回。

启动标记为 `RRFAT: FIXTURE_ARMED <case>`，失败前缀 `RRFAT: TEST FAIL`。core receipt 要求 fixture_ready 及对应模式 success_readback；ui_rejection 要求 fixture_ready 与 no_product_change_readback；cold_reload 仅要求对应 persisted_readback。生成成功的业务状态始终是 NOT_RUN，不能替代公共 prepare、原生加载或业务验收。
