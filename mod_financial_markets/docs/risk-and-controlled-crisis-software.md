# 开仓风险与受控债务剧情：本轮软件证据

2026-11-23，机器 `4-8e1c2f1861`。Root已采用risk修订、crisis03／04／05／06及两处局部type-only收窄；本记录不把软件VM或受控fixture当作新Game证据。

原真实生产脚本VM反例返回 **1／29.0099667秒**：原submit／fill、双方free撤回、次日mark、真实6分基金与追索断言已完成，随后安全断言失败。原WITNESS及失败保留；没有据此声称实机已经发生亏损。修订在普通新仓成交提交前，以当前mark核双方新仓权益满足既有60%维持保证金，原保证金／费用算法、减仓与强退路径不改。

| 本轮独立软件窗口 | 原结果 | 原耗时 |
| --- | --- | ---: |
| 修后定向风险 | 8P／0FES，exit0 | 8.0297201秒 |
| 受影响盘口 | 48P／0FES，exit0 | 49.7582812秒 |
| 共享首轮 | 75P／4ERROR／0F，exit1，原红保留 | 原wait为准 |
| crisis06两类 | 21P／0FES，exit0 | 17.4909063秒 |
| NoGame受影响组 | 195P，exit0 | 139.0043396秒 |
| Python optimized | 13P，exit0 | 11.6729822秒 |
| 最终NoGame受影响组 | 41P，exit0 | 19.307295秒 |

共享首轮的三项解析错误来自受控contextChecks生成器缺一个闭括号；第四项来自已切换known-heir的测试fixture缺真实收入字段。06只修生成器括号，并为该测试heir明确给0收入，不把VM缺字段统一当0，也不放宽生产终局保护。两次原typing失败保持，局部收窄后第三次实际exit0／3源无错误。

完整金融verify实际 **701个distinct方法全部PASS／0FES**，来源before／after保持一致；外层原wait **0／256.3898331秒**，内层原Maven wait **0／255.1551153秒**，两层耗时分开记录。默认完整verify无测试过滤或skip，保留56份原Surefire XML；不将本篇增量组另加为distinct总数。

以上窗口互有重叠，不能相加冒称本轮distinct测试总数。[原反例、原红及各实际窗口索引](../../docs/maintenance/evidence/2026-11-23-financial-markets-risk-and-controlled-crisis-software.json)分别保留来源、原wait与日志pin。Core53尚未build，新实机场尚未run，Q55旧Native资格仅保持原域。新的20剧情实机场、受控2048→4096场未由软件测试授予；受控fixture的声明性合成输入不算自然AI发行、自然收入或市场规模。原[R78／E8](r0078-e8-continuous35.md)35日信用保持其原来源窗口，完整产品／Workshop首发继续待验。
