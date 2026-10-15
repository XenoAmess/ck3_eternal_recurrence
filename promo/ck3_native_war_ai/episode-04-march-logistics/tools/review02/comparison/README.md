# Review02 R10：只读比较工具

合同、到达表与同日表、费用/unknown模型见[比较合同](../../../../../../docs/ck3-native-ai/episode04-comparison-contract-12004.md)。视频侧映射见[24段文案槽](../../../review02/r10-claim-result-shot-map.json)。

复用项目明确验证的Python环境；依赖`jsonschema`，不需要CK3、SDK或媒体工具。从仓库根运行：

```text
<verified-python> -B -m unittest discover -s promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison -p test_r10_compare.py
<verified-python> -B promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/r10_compare.py check-plan PLAN.frozen.json --evidence-root SMALL_EVIDENCE_ROOT --output CHECK.new.json
<verified-python> -B promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/r10_compare.py compare RESULTS.json --plan PLAN.frozen.json --evidence-root SMALL_EVIDENCE_ROOT --output COMPARE.new.json
```

四个`UNBOUND`模板是未绑定意图，按设计拒绝准入；目标、普通存档T0、军队和阈值不可拿合成测试值填上。schema由`schema_source.py`生成，不手改JSON；改生成源后运行该生成器并审阅差异。所有输出exclusive-create，重跑换新attempt。

测试用`TemporaryDirectory`内显式合成的native形状数据，不是存档或实机；旧B/C拒收例直接读取仓库跟踪的原始小记录，不读取其历史绝对媒体路径。测试与工具均从`Path(__file__).resolve()`定位本目录，不动态导入外置研究目录。实际相对路径检查记录见[回归回执](validation/relative-regression.actual.json)。

工具只检查供应的文件字节、整数、配对帧、时钟与声明的ledger范围。`controlled_comparison_records_eligible`不授source真实性、实际因果资格或每个策略动作验收；输出固定`research_card_closed=false`，不生成winner、clean片段、TTS、成片或人工签核。
