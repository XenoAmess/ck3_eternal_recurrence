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
