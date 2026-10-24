# 宗族化密教 / Dynastic Esotericism

独立模组预研目录：`mod_dynastic_esotericism/`；产品 key：`dynastic-esotericism`；拟用脚本前缀：`des_`。

当前为开发候选：游戏脚本、原创图标与工坊预览、Java 正式构建器及测试夹具已实现，离线构建检查已执行；实际游戏业务验收进行中，尚未公开发布或分配 Workshop ID。具体结果以[交付状态](docs/delivery-status.md)与实际回执为准。

需求包括：礼仪创建／改革时选择“宗族化”或“无”；宗族化礼仪创建对应宗族，创建者与全部信徒加入；宗族成员背离对应礼仪时，受到该礼仪信徒的一项 `-100` 好感修正，并被视为具有监禁、处决等惩罚理由。

[需求文档](docs/requirements.md)、[测试方案](docs/test-plan.md)、[可行性研究](docs/feasibility-2026-10-24.md)、[发布准备](docs/release-plan.md)分别记录产品合同、验证和实际边界。

正式构建使用 Java 21 与默认 Maven（版本按根规范）：

```text
mvn -f mod_dynastic_esotericism/tools/pom.xml verify
java -jar mod_dynastic_esotericism/tools/target/dynastic-esotericism-tools/quarkus-app/quarkus-run.jar build --source mod_dynastic_esotericism --repo-root . --output <new-output>
```

容量受限机器通过 `-Ddes.build.root=<admitted-external-root>` 将 Maven 产物放入已准入的外置根，再使用该根下的 runner。游戏运行本身只加载正式 staging 的原生 CK3 文件，不依赖 Java 服务。`tools/` 的测试夹具、文档和图标生成源码均不进入正式包。
