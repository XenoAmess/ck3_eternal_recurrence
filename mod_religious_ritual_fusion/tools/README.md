# 宗教礼仪融合工具

Java 21 + 默认命令行 Maven 3.10.0 以上；Quarkus 为 CLI 宿主，无 HTTP 服务。玩家只加载生成的 CK3 内容。

先在仓库根目录安装共享存档读取叶模块，再执行完整检查。重型输出须使用当前机器获准的构建根；共享模块只安装自己的 GAV，不另建整份依赖缓存：

```text
mvn -f java/ck3-save-core/pom.xml -Dsave.build.root=<approved-shared-build-root> install
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
java -jar mod_religious_ritual_fusion/tools/target/quarkus-app/quarkus-run.jar build --output <new-disjoint-staging-path> --revision <full-git-sha> --git-tag <matching-release-tag> --workshop-item-id 3826756673 --machine-id <current-machine-id>
java -jar mod_religious_ritual_fusion/tools/target/quarkus-app/quarkus-run.jar verify --output <staging-path> --manifest <staging-path>.manifest.json
```

`tools/product.json` 为手工生产文件的显式清单，`catalog/generated-files.json` 只由目录生产者生成并自动并入清单。快照含来源相对路径、SHA、观察时间和机器 ID；它证明该机器观察时的源内容，不代表当前其他机器安装状态。游戏内运行不读取快照或游戏安装目录。生成文件不得手改；规则不支持投影时只禁该项并将原因写入快照。

构建拒绝旧输出、源与 staging 包含关系、缺文件、额外 runtime 文件、BOM 错误、内部 Workshop ID、脚本引用缺失、已声明语言键或保护 token 不一致及生成内容漂移。版本字段使用单一 token，例如 `0.1.0-alpha`，同时用于 product、descriptor 和 manifest。`picture` 必须在显式清单中，缩略图须有 PNG 签名。不执行任意递归删除，不复制 docs/tools/catalog/fixture。静态检查与 staging 不能证明原生解析、按钮业务、创建后态或存档通过；实机按模组 docs 的公共验收入口执行。

正式 release manifest 使用共享 Workshop cache 格式 `format_version=2`：`workshop_item_id` 为规范十进制字符串，`git_tag` 与 `git_sha` 为显式发布来源，`files` 保留逐项 path/size/SHA。额外 `product_id`、`version` 与机器 provenance 保留本产品身份。真实构建要求 Git tag 解析到显式 revision，且 revision 等于源 HEAD；验证再次核 tag，并核完整清单和源/staging 字节。目录生成清单和独立验收 fixture 的合同不受此格式迁移影响。Maven 回归调用真实共享 cache validator 与逐文件 verifier，拒绝缺失 Python 环境而不跳过。

## 独立实机 fixture

fixture 使用同一 Quarkus CLI 生成，和正式 75 文件载荷分开：

```text
java -jar mod_religious_ritual_fusion/tools/target/quarkus-app/quarkus-run.jar fixture --repo-root . --output <new-fixture-path> --machine-id <current-machine-id> --inputs mod_religious_ritual_fusion/tools/src/main/resources/acceptance/requests/core-rite.json
```

输入为严格 `Request`：`schemaVersion=3`、`kind=core|ui_rejection|cold_reload`、`mode=rite|faith`、`actorHistoryId="1128"`。历史 ID 使用独立值对象和规范十进制字符串，仅支持原版 Robert the Fox 的历史定义 1128；所有脚本身份门由同一字段生成。旧 v1/v2／`actorId` 字段、数字／布尔／浮点和其他历史 key 均拒绝。原生 MCP 的运行时角色 ID 仍须逐场观察，不能沿用此前场次的 29829，也不能将历史 ID 当成运行时句柄。`setup` 为带 `type` 的封闭分支：新局 `{ "type": "fresh", "piety": 500 }`；冷读 `{ "type": "saved" }`，拒绝其混入 piety 或任何 seed 参数。`expectedSelection={"coreTenets":["tenet_esotericism","tenet_astrology","tenet_communal_identity"]}` 为必填共享类型，结构范围3–100、拒绝重复；实际目录类型必须是可见的 TENET，全部条目必须来自 A/B 并集，并保留双方独有核心贡献。当前来源并集只有4项，5–100一律拒绝。`requests/` 保留显式三项基线，`*-four.json` 提供两模式四项及相应冷读示例；不能称100项通过。

输出 `<path>.fixture.json` 严格采用公共 `ck3-mod-acceptance-prebuilt-fixture-v1`；同一份规范 JSON 同时写入 `<path>.request.json` 留作输入记录和 fixture 内 `_rrfa_request.json`。后者进入 manifest 完整文件表，公共 prepare 原样复制并冻结到 profile；保存比较只消费该受绑定成员，不读取 detached sibling。manifest 固定完整文件表、源 Java／模板／目录 SHA、机器 ID 和观察时间。生产 Java 源与模板同时嵌入工具包，和当前仓库不一致时拒绝生成，防止旧 JAR 冒充新 producer。

新局 fixture 在首次启动后一天准备三个独立来源：A={esotericism, legalism, astrology}、B={esotericism, legalism, communal_identity}，B 同 Faith 与不同 Faith 各一份。使用原版创建／分离、知识和虔诚效果，仅写输入；完成一次后停止 seed，不调用 RRF 创建路径。目标最终集合由同一 ExpectedSelection 生成结果核心及 origin-list 的成员和基数谓词，三项基线为 {esotericism, astrology, communal_identity}；四项代表场另加 legalism。教义从 divorce_disallowed 切至 divorce_allowed。

实际生产 GUI 后调用 `rrfa.20`（礼仪）／`rrfa.21`（宗教）只读核对；`rrfa.30` 核取消／拒绝后钱包、身份和来源未变。冷读包固定8文件（含规范输入JSON；新局为11文件），不携带 seed 或 on-action 注册文件；真实存档加载后，由 Root 显式点击 `rrfa_observe_cold_decision`，只触发 `rrfa.22`。该决议要求玩家为历史角色 1128 且保存的 `rrfa_mode` 存在，不初始化或修复状态。所有观察只运行谓词和日志，不写预期 flag、钱包、对象或冷却。精准钱包差要求暂停且日期不变；全局新增对象计数、冷却到期日和自然收入归因仍须公共原生／存档独立读回。

新局启动标记为 `RRFAT: FIXTURE_ARMED <case>`，失败前缀 `RRFAT: TEST FAIL`。core receipt 要求 fixture_ready 及对应模式 success_readback；ui_rejection 要求 fixture_ready 与 no_product_change_readback；cold_reload 没有自动启动标记，仅要求实际点击观察决议后产生对应 persisted_readback。生成成功的业务状态始终是 NOT_RUN，不能替代公共 prepare、原生加载或业务验收。

## 独立存档 oracle

```text
java -jar mod_religious_ritual_fusion/tools/target/quarkus-app/quarkus-run.jar inspect-save --inputs <request.json> --output <new-report.json>
```

严格输入为 `schemaVersion=2`、`machineId`、绝对 `repository`、`save`／`decoder` 的 `{path, bytes, sha256}`、显式 `layout`、`selection` 和下述封闭 `expectation`。`layout` 含 `actorTable`／`riteTable`／`faithTable`／`religionTable` 路径数组；`selection` 含运行时 `actorId` 及 `riteIds`／`faithIds`／`religionIds` 数组，所有身份均为规范无符号十进制字符串。此处是原生运行时 ID，不能使用 fixture 的历史 ID 1128。未知字段、缺失、null、数字／布尔 ID、重复／不安全身份、错误 SHA 或布局均拒绝。

本机 Rakaly 0.8.22 的实际观察使用 `living`、`rites/database`、`faiths/database`、`religion/religions`；调用者必须按自己的 decoder／存档确认并显式填写，不自动将旧 `jens_*` 归一化。工具只运行已 pin 的 `melt -c --format ck3 --unknown-key error`，完整消费 stdout，验证词法与括号、退出码和 stderr；不落地完整 melt 或复制原始存档。对原档持共享只读锁，并在前后核大小、SHA、FileKey 与修改时间。

输出保留三类完整对象 ID 集合，选中 actor／Rite／Faith／Religion 的完整有类型 AST，以及资源原 decimal、变量、列表、期限与未知原字段；属性重复和列表顺序不归一化。元数据仅输出直接 scalar，`coverage=DIRECT_SCALARS` 明确区别于选中业务对象的 `FULL_RECORD`，其 token SHA 仍绑定完整原块。根 scalar 保留实际日期。原子 `raw` 含引号和原 lexeme，未出现字段不补零。`canonicalTokenSha256` 绑定仅用空格分隔 token 的规范形式；完整 stdout 另有字节 SHA。上限为 512 MiB 解码流、128 层、单 token 2 MiB、单选中块 512 KiB、合计选中 4 MiB、报告 1 MiB、stderr 64 KiB 和 120 秒。截断、重复身份或任何预算超限失败，不生成通过报告。报告只证明所 pin 存档的离线状态；前后差分、原生 GUI 业务、冷重载和实机验收由公共流程独立判定。


存档请求现为严格 `schemaVersion=2`，必填封闭 `expectation` 分支。仅保留原始 AST 使用 `{"type":"inspect_only"}`；结果核心业务比较使用 `{"type":"fusion_selection","fixtureManifest":{"path":"<absolute>","bytes":1,"sha256":"<actual>"},"preparedProfileInventory":{"path":"<public profile-preparation.json>","bytes":1,"sha256":"<actual>"},"resultRiteId":"<actual decimal ID>"}`，所有 pin 必须换实际值。旧 v1 请求不静默迁移。原生 ID 和 Selection 的 scope 数组仍为规范十进制字符串，不是信条选择数组。

`fusion_selection` 在解码前后完整校验原 fixture manifest/source/payload、规范 `_rrfa_request.json`、公共 prepared inventory 内复制件及 `_case_contract.json` 的同一 emitter manifest。随后要求完整 actor/A/B/result AST：actor adoption/last result 同ID、A/B真实核心与固定来源相等、结果 direct/core-status 两种表示一致，结果和 immutable origin 列表均为冻结期望的完整唯一集合，双方独有贡献存在。报告升级为 `rrf-save-inspection-v2`，输出分支 `fixture_bound_selection_verified` 只证明该保存的核心/来源选择；不授予费用、四名称、原生编辑完成、GUI或冷载通过。原 AST 和列表顺序保留。未知 origin-item 编码明确拒绝，不能以手写结果字段替代真实保存。

完整 Maven verify 后，RRF专用 `test_religious_ritual_fusion_prebuilt` 生产者到公共消费者测试需 `RRF_FIXTURE_CLI_JAR=<该次构建根>/quarkus-app/quarkus-run.jar`；未设置时只查默认 target 输出，缺少实际 JAR/Java 明确失败，不跳过计通过。该回归执行真实 Java fixture CLI →公共 generic prepare →实际 profile-preparation.json →v2 inspect-save CLI →完整 AST/比较器，覆盖3和4，并拒绝准备元数据篡改、三/四 profile替换及保存来源替换。游戏数据、engine身份和 decoder输出明确标记为 authored；实际子进程及生产消费者运行不等于实机通过。Maven 回归另保留 R0015 四个原始完整 scope及 report/save/decoder pins：`type=tenet key="tenet_*"` 是原始保存编码，原生编辑当时仍未完成；不因此授予编辑、费用、冷载或四核心实机资格。
