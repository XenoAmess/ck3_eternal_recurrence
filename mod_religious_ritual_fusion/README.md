# 宗教礼仪融合 / Religious & Ritual Fusion

目录采用仓库独立模组的 `mod_<英文小写下划线>` 约定：`mod_religious_ritual_fusion`。

当前版本为 **0.1.0 开发候选**。用户已于 2026-10-24 授权编写编码／测试方案并开始实现。源代码包含同 Faith 礼仪融合、不同 Faith 宗教融合的目标选择、独立对照窗口、核心／教义选择、共享提交与来源记录；实际资格以当次验证记录为准，尚不能视为实机业务通过或已发布产品。

- [可行性分析报告](docs/feasibility-2026-10-24.md)
- [编码方案](docs/implementation-plan-2026-10-24.md)
- [测试验收方案](docs/test-acceptance-plan-2026-10-24.md)
- [实机验收执行方案](docs/live-acceptance-plan-2026-10-24.md)
- [首轮编码结果与未验范围](docs/implementation-status-2026-10-24.md)
- [二进制观察与证据边界](docs/binary-observations-2026-10-24.md)
- [本机来源、版本与存储记录](docs/evidence/source-observation.json)
- [原生接口登记、帮助文本和有限机器码切片](docs/evidence/binary-observations.json)

工具为 Java 21 + Maven + Quarkus 命令行应用；游戏内功能使用 CK3 原生脚本与 GUI，不需要在线后端。Maven 使用执行机器命令行默认 `mvn`，最低 3.10.0，不绑定安装目录。

```text
mvn --batch-mode --no-transfer-progress -f mod_religious_ritual_fusion/tools/pom.xml verify
java -jar mod_religious_ritual_fusion/tools/target/quarkus-app/quarkus-run.jar validate --source mod_religious_ritual_fusion
```

`tools/product.json` 与生成文件清单共同定义正式载荷；只用 Java 构建器产生的 staging 进行加载或后续发布。`catalog/generated-catalog.json` 保存本次原版目录的来源 SHA 与可投影规则；生成内容只改工具再生成。原版更新需要重新采集并审查差异，运行模组不读取本地原版路径。

默认礼仪融合 500 虔诚、宗教融合 1000 虔诚，成功后十年冷却。所选核心限三项且双方各有独有贡献；未选旧核心可仍作为 permitted 存在。宗教融合产生单一 Religion 归属的新 Faith；不提供引擎双父 Religion。当前语言为简中／英文，AI 与多人资格尚未验收，尚无 Workshop ID。
