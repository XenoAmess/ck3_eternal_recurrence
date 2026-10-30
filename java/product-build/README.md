# 共享存档核心与产品构建

该 POM 只聚合 `ck3-save-core`、宗族化密教和宗教礼仪融合三个模块，不作为它们的 parent，不改变各模块的版本、编译选项、依赖或测试合同。

在仓库根目录用命令行默认的 Maven（至少 3.10.0）构建指定产品及其 reactor 依赖：

```text
mvn --batch-mode --no-transfer-progress -f java/product-build/pom.xml -pl :dynastic-esotericism-tools -am -Dsave.build.root=<获准构建根>/save -Ddes.build.root=<获准构建根>/des verify
mvn --batch-mode --no-transfer-progress -f java/product-build/pom.xml -pl :religious-ritual-fusion-tools -am -Dsave.build.root=<获准构建根>/save -Drrf.build.root=<获准构建根>/rrf verify
```

构建根必须显式指向执行机器获准的输出目录。离线执行时加 `--offline` 并复用已核验的本机依赖缓存；缺失依赖应失败，不能跳过测试。

两个静态工作流和密教发布格式工作流均保留独立的共享核心 `install`，再运行上述完整 `verify`。reactor 按产品对共享核心的真实 GAV 依赖排序，Quarkus 测试引导可取得同一 Maven session 的模块模型。打包仍使用各模块现有生产源码和嵌入的 `producer-source` 资源，不从历史安装包复制业务实现。

此入口针对独立 `install` 与产品 Quarkus 测试引导之间的跨 session 解析问题。原失败中的 Central prefix 拒绝并未证明本地仓库追踪为何不可用；不能将其记为已确认的根因。产品 `verify` 通过只证明该次构建与测试，不代表游戏实机验收完成。

实现依据：[Maven reactor 的排序与 `--also-make`](https://maven.apache.org/guides/mini/guide-multiple-modules.html)；[Quarkus 3.33.3.2 将 Maven session 项目模型交给测试引导](https://github.com/quarkusio/quarkus/blob/3.33.3.2/devtools/maven/src/main/java/io/quarkus/maven/QuarkusBootstrapProvider.java#L206)；[同版 workspace loader 将全部提供的 POM 入队](https://github.com/quarkusio/quarkus/blob/3.33.3.2/independent-projects/bootstrap/maven-resolver/src/main/java/io/quarkus/bootstrap/resolver/maven/workspace/WorkspaceLoader.java#L79)。
