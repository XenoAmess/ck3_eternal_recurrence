# Java 构建与校验

构建工具使用 Java 21 和 Quarkus command 宿主；默认命令行 `mvn` 必须不低于 3.10.0。Java 只在开发／验收时使用，正式 CK3 包没有 Java 运行依赖。

先在仓库根目录安装共享存档读取叶模块，再编译、运行全部工具测试并打包。共享构建根须按当前机器存储策略获准：

```text
mvn -f java/ck3-save-core/pom.xml -Dsave.build.root=<approved-shared-build-root> install
mvn -f mod_dynastic_esotericism/tools/pom.xml verify
```

实际输出位于 `mod_dynastic_esotericism/tools/target/dynastic-esotericism-tools/`。需要外置构建时传 `-Ddes.build.root=<获准外置构建根目录>`；工具会在其下使用 `dynastic-esotericism-tools/`，包括编译、Quarkus 包、测试报告和测试临时文件。重型写入前按全仓存储策略检查容量；Maven 本身的临时目录和下载依赖由执行机器配置，不把其他机器路径写入生产配置。

以下 `<runner>` 是该构建目录下的 `quarkus-app/quarkus-run.jar`，所有正式产物和重建检查均指定新的外置目录。命令从仓库根目录执行；也可显式提供 `--source <产品源目录>` 与 `--repo-root <仓库根目录>`。

```text
java -jar <runner> validate
java -jar <runner> check --output <新的外置双构建目录>
java -jar <runner> build --output <新的外置staging> --git-tag dynastic-esotericism-v0.1.0
java -jar <runner> verify --output <staging> --manifest <staging>.manifest.json
```

首次真实创建 Workshop item 后，构建可增加 `--workshop-item-id <规范十进制字符串>`。未分配时不传；manifest 明确保留 `null`，不猜 ID。内部 descriptor 永远不写 `remote_file_id`。

`ReleaseProduct` 是正式文件清单的唯一入口；`docs/`、`tools/` 和产品 README 均不发布。构建同时生成 staging、相邻 `.manifest.json` 和 `.zip`，已有目标拒绝覆盖。`check` 比较两次真实构建的 manifest／ZIP 字节，并保留两份结果供审阅。`verify` 使用严格字段合同解析 manifest 并逐文件核对真实 staging；不需要把源目录复制到发布缓存。

Manifest 沿用 `independent_mod_release` 的 v1 JSON 字段：`format_version`、`product_id`、`mod_version`、`git_tag`、`git_sha`、`workshop_item_id` 和 `files`。每个文件包含 `path`、整数 `size`、小写十六进制 `sha256`。必填可空字段也必须出现；未知字段、错误类型、布尔／浮点整数、重复或错序文件均拒绝。兼容标签只读取仓库 `ck3_workshop_mcp/.../compatibility_tags.py` 的单一 registry，保留其他分类字符串与顺序；未知 minor 拒绝构建。

静态检查确认正式清单、UTF-8/BOM、括号／引号、本地化合同、版本、实际 DDS 头及像素载荷，并验证两项预置信仰／礼仪／教义／纹章资源闭合。它不替代 CK3 解析器和实际业务验收；实机与发布按产品 [测试方案](../docs/test-plan.md) 执行。`fixture` 子命令仅用于公共验收入口所需的外置准备夹具，不进入正式 allowlist。

`verify` 的 `DefaultMavenTest` 会实际调用 PATH 选择的 `mvn --version`，记录 Maven home 并拒绝低于 3.10.0 的默认工具；它同样适用于 CI。`runtime` 子命令只为公共验收生成有限共同 runtime 后继，不授予业务资格；其参数为 `--repo-root`、`--base-runtime`、`--native-index`、`--host-projection`、`--output`、`--machine-id`，必须各提供一次。运行输入须使用已经冻结的公共 runtime 和实际构建的 native index。

`validate`、`check`、`build`、`verify` 都接受独立开关 `--release-localization`。0.2.0 候选普通模式投影中英 31 文件，忽略源码中七语各三份已知外语文件；未知文件仍拒绝进入正式树。发布模式使用明确九语 52 文件清单，验证各文件 UTF-8 BOM、语言 header、`:0`、引号／转义和保护 token（含 `−100`），并在 staging 回读时重新验证格式。原产品 15 key、教派 20 key、动态名称 1 key 保持三份独立精确合同；Rite 本地化引用对应 Faith，两预置纹章纹理与其图标逐字节一致；宗族化专用组图／教义图同字节并验证实际120×120 BGRA8单层格式。None详情隐藏／编辑保留及AI选择合法性同时校验，但静态通过不表示实际GUI或AI行为已验收。非中文只认证格式，不以游戏内语义或显示已验收作为结论。

```text
java -jar <runner> validate --release-localization
java -jar <runner> check --release-localization --output <新的外置双构建目录>
java -jar <runner> build --release-localization --output <新的外置staging> --git-tag dynastic-esotericism-v0.1.0
java -jar <runner> verify --release-localization --output <staging> --manifest <staging>.manifest.json
```

发布格式检查仅由 `dynastic-esotericism-v*` tag 或人工发布 workflow dispatch 触发。普通 push/PR 运行开发检查和九语合同测试。九语候选已落盘；格式检查不证明翻译语义或游戏显示通过。本构建器不生成或改写译文。JUnit 通过现有独立 parser、token 校验与 manifest 消费者验证真实 52 文件构建，不新增 Python 生产入口或 Java 运行时依赖到游戏中。

用户图标由同一 Java 模块导入：`java -jar <runner> artwork <uploaded-zip> <mod-source>`。繁育 DDS 原样保留，白绮 PNG 以保留透明度的双三次缩放转换为 256×256 RGBA DDS；两份纹章纹理与对应信仰图标相同。原 PNG 位于 `tools/artwork/source/`，不进入正式包。来源与实际导入回执见[素材记录](../docs/artwork.md)。
