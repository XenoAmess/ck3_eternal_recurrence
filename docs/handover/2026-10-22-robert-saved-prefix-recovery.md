# 2026-10-22 罗贝尔续跑：结果缓存与未决批次恢复

machine_id: xenoamess-full-tower-eb9d2c1186。记录时间以本文件所链接回执的 UTC 为准；本次在 Z:\ck3_mod_rewrite 开发，运行材料位于该机器的 D: 外置目录。

N34（R0021）在 1082-02-09 停止。累计 5622/10950 游戏日；原始墙钟起点仍为 2026-10-19T03:26:49.420926Z。G2 仍为 6/8，30 年及 1 秒/日均未完成。本轮两个已验证的只读周期将累计周期从 5143 增至 5145，没有增加游戏日。

实际故障是完整 MCP 结果已经返回后，启动重试缓存将普通 AUTO 结果交给控制数据的安全整数校验，抛出 “JSON integer loses precision”。11386 的完整原始结果未保存，不能追认具体超限字段、业务成功或失败。婚姻 sidecar 的更新不能替代原回执。11386 及其 pending5146、HALT 和失败 FULL 原件保留，禁止重发旧请求。

4df238693715d519e0ce7e12e30cc52e21b54901 将缓存限制在原 semantic 加载重试实际需要的对象；普通业务结果继续交由原队列编码，保留 Python 整数原值。控制数据的安全整数校验继续有效。19 项回归和修改范围严格类型检查通过，包含原 Queue.call 到后验与持久化链；测试中的 int64 输入是合成合同样本，不是丢失的 11386 原始结果。

本文件同提交的续跑分支已通过 20 项定向回归和 11 文件严格类型检查；Root 用真实闭场资料验证四个 owner 消费入口通过。该分支验证实际两条 AUTO/METRICS、原 classifier、after、credit 和只读保存跳过记录，再生成独立的已结算 seed。它保留 10565、11386 的未知历史，不改原 pending 文件，不把失败 FULL 算成成功。当前四份 sidecar 原字节另存快照，唯一变化的婚姻快照只作来源证据，不投影为业务信用。非空继承预期继续验证，原检查点及 SAVE 身份不变。

整改要点是验收生产者到消费者的完整路径：实际队列编码、原后验、治理状态持久化及 BOUND，不能用单独 parser 或 ACK 代替。启动使用新目录和新冻结源码，完整离线预验通过后才允许实机；结果未知时保全原件，用独立冷载资格恢复，不清空原故障记录。

证据根为 D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100/：

- current-saved-a34-runtime-prep01/ROOT-A34-ACTUAL-CLOSED-PREFIX-UNKNOWN-INDEX01.json：真实闭场及未决请求。
- current-saved-a34-runtime-prep01/ROOT-A34-AUTO-OPAQUE-RESULT-SOFTWARE-QUALIFICATION01.json：结果缓存回归。
- current-saved-a35-runtime-prep01/ROOT-A35-ACTUAL-READONLY-PREFIX-EVIDENCE01.json：两周期的实际来源。
- current-saved-a35-runtime-prep01/ROOT-A35-CLOSED-SIDECAR-OBSERVATIONS01.json 及 ROOT-A35-SIDECAR-OBSERVATION-METHOD-CORRECTION01.json：快照及取证方法勘误；实际为路径 stat 前后夹读，不声称持有同一文件句柄。
- current-saved-a35-runtime-prep01/：本轮 epoch、basis、qualification 和启动前检查回执；其软件资格不等于 Native 或完整 FULL 实机通过。

