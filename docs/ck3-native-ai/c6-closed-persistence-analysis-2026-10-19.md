# C6 第一个完整批次的自然性能

机器 `xenoamess-full-tower-eb9d2c1186`，核算到 `2026-10-19T06:38:52.493930Z` 的 MET353。实际分析 UTC、输入 SHA、生产器在 [回执](evidence/c6-closed-persistence-analysis01.json)。只读已封的小 compact/trace、原289/291两个约1.2KB控制回执及旧C5报告；0新RPC、0活Driver/SAVE正文读取，现场继续跑。

原291明确成功完成30个cycle，112→142、110→189日；289只消费原MET286结算112，没有新RPC或进日。**首AUTO292→末MET353为43.664544秒/79日**。291包装没有外层开始/完成时间，因此完整FULL墙钟及完成尾部是unknown，不能拿文件mtime补成“完整43.665秒”。此窗口不是长期资格。

原AUTO9锚累计到MET353为11,523.073004秒/189日，SDK115为9,873.425863秒/171日，既往维护全部保留。C6从warm287起算306.795643秒/79日，其中SAVE290为2.5216115秒；不把起点重置到首AUTO。批内SAVE325另有2.4991226秒，也完整保留。

24次全量持久化共0.1969554秒：12次succession、11次life、1次SAVE。JSON为0.0077239秒，UTF8为0.0199403秒，stream write为0.0181875秒；这些均嵌在父阶段内。逻辑交给writer的全量JSON共48,439,484字节。历史部分从1,578,335字节/183行增至2,312,343字节/240行，即+734,008字节/+57行；不是设备写入、分配量或未来模型。

11个候选run全长1，并全被full barrier关闭；真实WAL append为0。现有实验首次激活仍要重写sealed base，且多日资格缺口未解决。这段不支持开WAL或新增持久化框架。

更大开销是11次life driver共14.2149374秒、30次normal plan共8.2042361秒。最大的plan为2.2469239秒，次大0.7042917秒，均位于296/328两个未观测大响应窗口。choose、capabilities、history、copy子阶段都小，应向规划准备/provider链继续定位，保持同帧候选与策略。

296/328没有tool timing，Native primitive数量与Native-only时间均unknown，不把余量当队列或Native CB。public wait按life时间包含关系核算，不能照名称相加；所有阶段是墙钟而非CPU。完整输入与可复算分组均在回执。没有旧矩阵重跑、源码策略改变或长期达标声明。

命令：`python -B tools/g2_saved_campaign/analyze_c6_closed_persistence_v1.py --output <新回执路径>`。输出create-only；显式拒绝输入SHA、机器或cycle不符。
