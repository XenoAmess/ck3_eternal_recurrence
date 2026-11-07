# P108：cash规范化不再重复编解码完整历史

`OrdinaryFinanceCollector.cash()` 过去把完整snapshot编码后交RawCashCodec再parse，包括当前模型不消费的数MB历史。本单元只把normalize第二参改为已验P107融资snapshot角色，原Native查询、完整cash第一参、Packet、source/Guard、错误处理及codec预算均不改。依赖闭合为actor/native/date、rawContext的alive/paused/map_ready、hello四build键及presence优先级；原完整snapshot/request仍由Java持有。

该行依赖P107新增私有helper。相对冻结Runtime不是已资格的body-only热替，P107/P108均未授实际采用、装载或实机收益。

本地模型一次200/stop，UTC19:12:29.618→19:12:35.731，TTFT2851.24ms、total6113.28ms、prompt21394/output456、cached=null；单行hunk采用。其说明误列player_armies等未消费字段，owner按完整RawCash源码与独审核正，未扩helper。原件：`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/cash-snapshot-performance108/model01`。

## 新软件验收

必要Collector1TU exit0/12class/5.8104523秒，19:24:55.653643Z close。唯一新Test/main TU exit0/2class/4.77816秒，仅两个新方法2P/0F/0E/0skip，7.662193秒，19:29:57.119962Z实际close；P107已编fixture仅复用纯加载器和软件READ producer，不跑其旧@Test或重编旧codec。

新DATA逐字比较32项既有Loan normalize向量、7项rawContext向量及unpaused/dead_actor两个原拒绝；同时核frame、war/army IDs、metrics及loanObservation全部typed getter。public cash接线比较原packet、source/frame/deadline与完整snapshot不变，肯定结果对独立原小输入oracle一致。大history139行只作为未消费扩展，不冒充当前FinanceCurrent或实机许可。

## 实际同输入ABBA

旧P107已编Collector为A、新P108为B，只替换classpath该前缀。四个独立JVM固定A0/B0/B1/A1，统一CPU1/384MiB/45秒，每次2warm+4measure，全部8warm和16measure保留，无强制GC、删慢样本或速度assert。计时为完整public cash的软件READ解码、输入组装/encode及normalize，包含原完整现金来源检查。

| 本地public cash组件，每模式8测量 | A | B |
| --- | ---: | ---: |
| 中位耗时ms | 26.075399 | 9.7960495 |
| 均值ms | 27.430274625 | 10.24948725 |
| 全部测量范围ms | 21.055099–38.9299 | 3.1893–20.6737 |
| 主线程分配中位bytes | 53363560 | 572224 |
| 主线程分配均值bytes | 53364058 | 572362 |

组件中位耗时约减少62.43%，主线程实际分配约减少98.93%。snapshot3402368B，角色434B；全部四JVM规范化输出均4134B/SHA `a3adf5888633a292b85514cd23c6c486f0cbb3555c044ed056e9ddcd90330d11`，原packet SHA均 `757bc2af2b1e6951401193f8d051ef7f2cef98f278274fc932e98f853781c867`。实际原字节和typed值相同，未通过删现金、改原件或跳verify取得差异。

完整outer窗口两次合计A12.0043524秒、B11.0969114秒，setup/load/main/JVM和峰值各有原件，不把组件差异当整个进程、HTTP、当前CK3或游戏日吞吐。末资源于UTC19:30:40.975409Z实际关闭。模板历史LIFE106 schema标签保留并已明确绑定P108实际CONFIG/FQN/source，不为改label重跑。

最终原件：`D:/ck3-state/resume91-native-integration/p108-cash-test01/QUALIFIED-P108-PUBLIC-CASH-SOFTWARE-AND-ALL-ABBA.json`（25182B，SHA `702d0ee82242a76392e160e8f41b6c10606561cbaa470230b38587eb7a3dea01`）；全部样本 `ALL-ABBA-SAMPLES.json`（12093B，SHA `e1ba25a5c4ce560bbac3d00e8fdaa75ded2aaf8a358b0ec24653de389a0f6192`）。

P109独立预算snapshot角色已完成真实模型候选和源码/新DATA审阅，接续增编验证；P110 cashContext/Focus完整角色随后。原UNKNOWN/P100/Guard与冻结工作树保持，本轮新增确认保存日0，10秒/新增确认保存日目标仍未通过。
