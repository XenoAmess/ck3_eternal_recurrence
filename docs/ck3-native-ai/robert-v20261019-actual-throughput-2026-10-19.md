# v20261019 实际运行 wall 账本

`machine_id: xenoamess-full-tower-eb9d2c1186`。最新分析观测于 `2026-10-19T04:20:57.934821Z`，实际已封闭终点为 `04:18:04.628533Z`；这之后仍开放的修复时间要进入下一账本。来源、SHA、owner 代次、旧 header 更正及逐类 RPC 耗时见 [ledger03](evidence/robert-v20261019-closed-wall-ledger03.json)；此前截至30日的 [ledger02](evidence/robert-v20261019-closed-wall-ledger02.json) 保留原样。只读六个显式小 compact，未增加 RPC、未读 Driver/SAVE。

| 实际窗口 | wall | 实际游戏日 | 秒/日 |
| --- | ---: | ---: | ---: |
| 首 AUTO `03:26:49.420926Z` 起，保留全部维护/失败间隔 | 3075.207607s | 38 | 80.9265160 |
| 新 SDK 首 AUTO115 `03:54:19.068067Z` 起，保留分类器修复及后继错误 | 1425.560466s | 20 | 71.2780233 |
| FULL120 连续子窗口：首 MET121 至外层120错误闭合 | 5.978826s | 12 | 0.4982355 |
| FULL133 连续子窗口：首 MET134 至外层133错误闭合 | 8.644744s | 0 | null |
| FULL146 连续子窗口：SEM145 至外层146错误闭合 | 9.511150s | 8 | 1.18889375 |

两个累计窗口均未达到 1s/day。FULL120 包含普通 AUTO、paired MET、Crown动作/查询、间隙和外层合同拒绝，属于一个短连续片段，不能代替累计吞吐，也不足以宣称长期稳态。没有只取 clock 调用来计算目标成绩。

最大的实际耗时是运行链路故障和维护间隔：旧 MET110 至新 SEM111 为 1456.205360s；外层114错误闭合至 MET121 为 414.740821s；外层120错误闭合至 MET134 为 274.569277s；外层133错误闭合至 SEM145 为 710.878215s。这些是原始时间端点间的确切跨度；context 来自 runtime owner，不代表有互斥 CPU 分段。新 SDK 窗口的全部已知 RPC 合计 14.649575s，其余 1410.910891s 保留为间隙/维护成本，不从总 wall 中删除。

新 SDK AUTO122 实际推进 8 日用 3.195157s，AUTO126 推进 4 日用 0.504759s，后者精确停在月界；AUTO147 又实际推进 8 日用 1.007692s。三者 native clock 均为 `date_deadline`、overshoot 0，`speed_configuration.submitted=false`。三个新推进都未进入普通事件早停分支，**普通事件 30 秒等待修复尚无对应实机 PASS**。147的额外 pause-map false ACK 使旧外层合同拒绝；账本依原生日期链记录实际8日，不将其授予完整 ordinary/cycle。FULL146 保留 SEM 到 AUTO 之间约8.42s的等待，不能只用147调用计算全窗口吞吐。早先旧 AUTO74 的普通事件等待仍保留为历史反例，不因新源或正常 deadline 通过就改写。

FULL133 没有推进日期；两个 SAVE 合计 4.910178s，是该片段最大已知 RPC 组。SDK duplicate-publication 错误143为 1.963711s；其553B原件明确无 action replay，不能授进日或业务成功。Crown 外层分类合同及 duplicate publication 已由对应 owner 修复/诊断；当前证据优先支持消除这些实际控制链路中断。SAVE 内部没有 native/Driver/文件系统分段，不能把全部 4.91s 归为 Python persistence，也不能为提速跳过现有保存屏障或业务。

旧 SDK 77–110 使用更正后的 `COMPACT41`：原40错误绑定失败初始化的 owner，原文件保留，RPC 行和时间未改。当前编译负载报告为 Native26 离线构建约 `04:08Z` 起、至多两个 BELOW_NORMAL compiler，Game 继续 Native25；它晚于 ledger02 终点，但已与 ledger03 窗口重叠。本窗口必须标注并发且继续保留完整 wall，不能称无并发 A/B 或扣掉编译间隔。

新增离线工具 [summarize_closed_runtime_fragments_v1.py](../../tools/g2_saved_campaign/summarize_closed_runtime_fragments_v1.py) 区分真实 RPC、零 RPC 的本地 reconsume/install 和外层闭合端点，保留未知大响应18的 stat，不读取其正文。工具编译、AST Assert=0 及 `python -O` bad-SHA 写前拒绝通过。小产物计入原 `REPO-ONLY-MICROPOOL01`，外置写 0；没有重开 WAL 或引入持久化框架。
