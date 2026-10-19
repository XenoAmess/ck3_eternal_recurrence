# C4 首个自然窗口的持久化结论

机器 `xenoamess-full-tower-eb9d2c1186`；闭窗截至 `2026-10-19T05:41:09.681232Z`，实际分析 UTC 与全部输入 SHA 见 [回执](evidence/c4-closed-persistence-analysis01.json)。仅解析 runtime 封存的 compact、stage trace、211 小 header 及旧 ledger03；0 新 RPC、0 Driver/SAVE 正文读取，旧 ledger02/03 未改。

这段的全量持久化还不是主要耗时。14 次实际成功写入合计 **0.2630371 秒**：7 次 succession expectation、6 次推进、1 次拒绝角色交互；实际交给 writer 的完整 JSON 合计 16,307,100 字节。这是逻辑写入量，不是设备写入或分配量。

| 已有阶段 | 次数 | 合计秒 |
| --- | ---: | ---: |
| full persistence | 14 | 0.2630371 |
| atomic write（包含其子阶段） | 14 | 0.2362204 |
| JSON serialization | 14 | 0.0051605 |
| UTF8 materialization | 14 | 0.0059385 |
| temp stream write | 14 | 0.0073028 |
| temp open | 14 | 0.0995937 |
| replace | 14 | 0.1127245 |

阶段嵌套，不能相加成总耗时。两次约 100ms 尾部各定位到 open 和 replace；没有来源证明其原因是 Defender。P49 的 stream-write 占比不能搬到这段。

六个候选 run 全是长度 1，随后被 succession 或交互 barrier 关闭；真实 WAL append 为 0。既有实验首次激活要读取、校验并重写完整 sealed base，后继 full barrier 又重置激活状态。此分布没有连续 append 的省写依据，单纯开启现有 WAL 会增加激活和 journal 工作。六次推进为 8/8/8/6/8/8 日，也不属于旧 exact-one-day 资格。维持 default-off，无已验证可立即省写的改动；不为它建立新存储层。

历史 JSON 从 902,912 字节/124 行增到 1,306,030 字节/163 行，即 +403,118 字节/+39 行。最大两次 barrier 间增长为 184,731 字节/12 行，与 211 宣战查询及后续评估窗口重合；延后记录混合在一起，不能归因到其中单个查询。当前小 trace 无法解释此前报告的 3.4GB Driver，不能拿本段安静局面增长外推长期或战场；既有大响应/历史增长证据仍有效，但本次没有读取其正文或重做模型。

主要开销转向执行链：六次 life AUTO 共 13.7253172 秒，其中 driver life 总计 9.6538988 秒，后者包含 public wait；25 次 normal plan 合计 4.9833882 秒。211 的现成小 header 补齐其 4.2982032 秒宣战查询；不是队列间隙，也没有 Native-only 分段。251 发布器失败耗时 5.108243 秒，缺 paired MET，不算完整 cycle。应先完成既有发布器修复，并继续按自然 declarable profile 定位查询成本；不削减宣战或决策。

46 日局部窗口包含失败/outer 结尾是 32.746611 秒；24 个已配对 cycle 到 MET250 为 27.560162 秒。全局仍是 AUTO9 起 8,060.260306 秒/107 日，SDK115 起 6,410.613165 秒/89 日，全部保留既往维护间隔；都没有长期达标。封存观察还记录闭窗后 182.138598 秒开放维护，留待后继累计，不能剪掉再起算。六次 clock 均只遇 `date_deadline`，不授普通事件等待修复的实局 PASS。

生产命令：`python -B tools/g2_saved_campaign/analyze_c4_closed_persistence_v1.py --output <新回执路径>`。输入大小、SHA、机器、计时关联与端点均显式拒绝不符；输出 create-only。此工具不是性能 benchmark 或 WAL 资格验证器。
