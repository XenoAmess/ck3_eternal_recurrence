# 宗教礼仪融合 / Religious & Ritual Fusion

目录采用仓库独立模组的 `mod_<英文小写下划线>` 约定：`mod_religious_ritual_fusion`。

当前版本为 **0.1.0 Alpha**，用户已于 2026-10-25 授权发布测试版。源代码包含同 Faith 礼仪融合、不同 Faith 宗教融合的目标选择、独立对照窗口、核心／教义选择、共享提交与来源记录。R0008 已观察到礼仪实际创建、扣费及保存，R0010 已冷加载并对比持久化对象；两场的完整公共验收仍为 GAP，宗教融合及完整矩阵尚未实机通过。完整边界见 [实机结果](docs/acceptance/live-results-2026-10-25.md) 和 [发布准备](docs/release-preparation-0.1.0-alpha-2026-10-25.md)。

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

默认礼仪融合 500 虔诚、宗教融合 1000 虔诚，成功后十年冷却。所选核心限三项且双方各有独有贡献；未选旧核心可仍作为 permitted 存在。宗教融合产生单一 Religion 归属的新 Faith；不提供引擎双父 Religion。附带游戏九种语言的本地化文件，七种新增翻译已做格式和键检查，尚未逐语人工审校或实机验收。当前只向玩家开放，AI 与多人资格尚未验收。正式上传仅使用 Java 构建器生成的 75 文件 staging，Workshop 发布事实另记永久 changelog。

## Tooltip 预演的 L1 实机回归

2026-10-24 UTC 的 R0004（`machine_id: 4-8e1c2f1861`）已通过原生目标选择与生产决策打开真实草稿，但 effect 描述预演展开 catalog，产生 `while building tooltip/description` 下的 `rrf_source_a` 未设错误并使日志超预算。该场未提交融合，不计 core 成功。入口现采用静态说明与 `hidden_effect`；此修改的引擎效果仍须按下列真实路径验证，Maven 或脚本形状检查不替代它。

1. 在打开生产决策前，记录实际场次、机器、当前状态以及 `error.log`、`debug.log`、`game.log` 的文件身份、字节数和读取偏移。提前固定日志增量及场次总预算，三份日志分别计量，不因内容重复而抵扣占用。
2. 使用现有原生控件通道完整执行“来源 B selector → 生产决策 toggle → RRF 草稿”。保留实际 query／action 回执、当前 actor／来源与截图；不从 fixture 直接调用产品开草稿 effect 来替代路径。
3. 读取三份日志的实际增量和时间范围，确认该预演没有 RRF 脚本错误，尤其没有 catalog 初始化链中的未设来源变量；日志增长须在事先预算内。轮转、身份变化或读取不完整时保留真实缺口，不能据尾部片段或截断后的文件大小判通过。
4. 在实际草稿核对来源名称、核心候选、教义类别图标、文字边界和滚动。第四个核心候选允许通过原有滚动区域查看。取消／拒绝用例还须独立读回钱包、对象、来源与冷却未变；正向用例在本项通过后继续既定提交和存档验收。

core 与 UI rejection case 的既有 `gui_phases[].requirements` 均包含这项断言，公共适配器沿原合同转成 `required_assertions`。断言通过必须绑定上述真实引擎与文件证据；不以 mock、静态单测或原生调用 ACK 伪造预演成功。每次结果和退出状态由对应场次报告记录。
