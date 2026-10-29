# 宗教礼仪融合 / Religious & Ritual Fusion

目录采用仓库独立模组的 `mod_<英文小写下划线>` 约定：`mod_religious_ritual_fusion`。

已公开版本为 **0.2.0 Alpha**，Workshop ID **3826756673**，2026-10-29T19:42:56Z实际更新同一条目。完整文案和四张补验图已公开回读；真实Steam下载90文件与正式manifest逐项一致，主菜单加载仍在验收。正在落实[人工审核八项整改与验收方案](docs/manual-review-followup-2026-10-25.md)，完整业务仍有GAP。历史实测继续按各自范围引用，不能以发布或下载成功替代。

2026-10-29，`machine_id: 4-8e1c2f1861`的R0057五项UI补验与R0058三项冷载补验分别通过并正常关闭，见[续工记录](docs/live-review-resume-2026-10-29.md)。这些局部补验不改写原12项／20项完整矩阵的incomplete；SDK续行及county宗教地图颜色样本仍有缺口。正式tag固定于Source A，后继入口修复不重建已发布内容。见[0.2实际发布记录](docs/publication-0.2.0-alpha-2026-10-29.md)和[永久changelog](../docs/release-changelogs/religious-ritual-fusion/0.2.0.md)。

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
mvn --batch-mode --no-transfer-progress -f pom.xml -pl :religious-ritual-fusion-tools -am -Dsave.build.root=<approved-shared-build-root> -Drrf.build.root=<approved-rrf-build-root> -Ddes.build.root=<approved-des-build-root> verify
java -jar mod_religious_ritual_fusion/tools/target/quarkus-app/quarkus-run.jar validate --source mod_religious_ritual_fusion
```

`tools/product.json` 与生成文件清单共同定义正式载荷；只用 Java 构建器产生的 staging 进行加载或后续发布。`catalog/generated-catalog.json` 保存本次原版目录的来源 SHA 与可投影规则；生成内容只改工具再生成。原版更新需要重新采集并审查差异，运行模组不读取本地原版路径。

默认同宗教礼仪融合500虔诚、其他礼仪融合1000虔诚，成功后十年冷却。普通环境所选核心恰好三项；加载More Tenets Slots（3182367229）时允许3–100项实际信条，双方各有独有贡献，不显示容量空槽。新结果随后进入同一对象的原生定制：四项名称、图标、地图颜色、标准教义扩展和美德罪恶。宗族化密教默认提供非宗族化选项，宗族化由玩家选择。联合加载时，本模组放在MTS与宗族化密教下面。

本轮为取得真实原生编辑上下文，仅覆盖 `gui/window_rite_creation.gui`：保留 MTS v11 的通用信条滚动区及原生输入、图标、颜色、教义和美德罪恶，只在融合设置会话增加同对象编辑按钮并锁定已选核心。宗族化密教的标准教义组由原生类别自动提供。此路径不自动合并任意第三方自定义 GUI；来源与 R0012 失败后修正见[原生接口研究](docs/research/native-creation-options-2026-10-25.md)。该修正尚须新场次验证，不能沿用旧独立编辑窗的结果。

新增未知核心的规则仍需要目录投影资格，不能靠放行未知`can_pick`实现兼容。封臣邀请使用原生互动及其费用，未确认结果不自动重发。至亲沿原版规则自动转换并提供预览、实际礼仪记录。新Faith仍属于单一Religion。附带九语言文件，日常新增文案仅制作简中、英文，其他七语新增键为英文占位。当前只向玩家开放，AI与多人资格尚未验收。正式载荷仅使用Java构建器的显式清单staging，文件数以当次构建manifest为准；Workshop发布事实另记永久changelog。

## Tooltip 预演的 L1 实机回归

2026-10-24 UTC 的 R0004（`machine_id: 4-8e1c2f1861`）已通过原生目标选择与生产决策打开真实草稿，但 effect 描述预演展开 catalog，产生 `while building tooltip/description` 下的 `rrf_source_a` 未设错误并使日志超预算。该场未提交融合，不计 core 成功。入口现采用静态说明与 `hidden_effect`；此修改的引擎效果仍须按下列真实路径验证，Maven 或脚本形状检查不替代它。

1. 在打开生产决策前，记录实际场次、机器、当前状态以及 `error.log`、`debug.log`、`game.log` 的文件身份、字节数和读取偏移。提前固定日志增量及场次总预算，三份日志分别计量，不因内容重复而抵扣占用。
2. 使用现有原生控件通道完整执行“来源 B selector → 生产决策 toggle → RRF 草稿”。保留实际 query／action 回执、当前 actor／来源与截图；不从 fixture 直接调用产品开草稿 effect 来替代路径。
3. 读取三份日志的实际增量和时间范围，确认该预演没有 RRF 脚本错误，尤其没有 catalog 初始化链中的未设来源变量；日志增长须在事先预算内。轮转、身份变化或读取不完整时保留真实缺口，不能据尾部片段或截断后的文件大小判通过。
4. 在实际草稿核对来源名称、核心候选、教义类别图标、文字边界和滚动。第四个核心候选允许通过原有滚动区域查看。取消／拒绝用例还须独立读回钱包、对象、来源与冷却未变；正向用例在本项通过后继续既定提交和存档验收。

core 与 UI rejection case 的既有 `gui_phases[].requirements` 均包含这项断言，公共适配器沿原合同转成 `required_assertions`。断言通过必须绑定上述真实引擎与文件证据；不以 mock、静态单测或原生调用 ACK 伪造预演成功。每次结果和退出状态由对应场次报告记录。
