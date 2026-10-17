# 已过时雇佣市场历史的有界保存

公共实现保留最新完整市场上下文，在下一次完整的新查询通过既有类型与同帧校验后，把旧市场历史正文转成明确摘要。直接 API 仍返回完整公司、报价、组成与可用性字段。策略选择、原生请求、雇佣提交及后验规则没有变化。

`bridge/mercenary_history_projection_v1.py` 只处理历史正文，不写文件。NativeDriver 沿原请求和记录流程执行，随后在既有历史锁内调用它；有实际变化时，失效增量历史 JSON 缓存并标记状态待持久化。Native 市场分支、primitive 和 Service 类型查询沿已有 `include_native_command_history=False` 机制读取快照，避免为市场查询复制整个命令历史。其他操作和普通完整快照继续原行为。

摘要保留原查询序号、来源帧、行数、构建与 capture 信息及规范 JSON 的 SHA/字节数，明确说明没有保留完整正文、不能从摘要完整重建，也没有制造归档文件或已知原件路径。历史行、索引、其他结果字段、错误、其他 command、selected decision/plan/pending ledger 字段及最新市场全文保留；selected 曾引用的旧市场全文也可能变成摘要。此前原 MCP 回执不作修改。

只有新查询 accepted、completed、read-only、完整集合 available 且通过原 normalizer，前后 public/native revision、日期、玩家、episode 与窗口绑定不变，并沿原 normalizer 核对构建来源，才允许压缩旧正文。新结果无效、不可用或跨帧时保留旧全文。构造全部摘要完成前不改历史；编码失败不会把成功业务查询改成失败。恢复仍走原 loader/schema，启动时先保留输入全文，首次合法新查询后才压缩。维护容量须覆盖这之前的完整输入与原子临时文件峰值。

普通 consumer 只消费当前同帧完整市场。pending hire 需要 capture epoch 晚于提交前观察的新上下文，并从中检查 employer；它保有自己的选中 decision、frame、epoch 和军队事实。未知 ACK 保留 pending，禁止重复雇佣，并允许独立的新查询。后验不要求重新读取旧的被选市场全文；只有摘要或旧帧时，现有类型校验拒绝它并允许正常重查。

离线验证使用真实公共 NativeDriver、Service、normalizer、consumer、增量编码器、原子持久化与恢复函数，端点和状态仅为内存/临时夹具。新增 7 类回归覆盖完整返回、第三次查询幂等、无效/不可用/跨帧保持全文、已缓存编码的内行失效、实际持久化恢复、摘要安全重查、其他行及 pending 不变，以及市场查询不导出历史。另运行既有战争选择、pending/未知 ACK 与注册雇佣测试，共 28 passed、3 subtests passed；证据见 [资格记录](evidence/p61-market-history-public-port-2026-10-18.json)。没有运行全部矩阵。

本机资格记录使用 `machine_id: xenoamess-full-tower-eb9d2c1186`，时间及精确源码 SHA 见上述证据。此为公共源码离线资格，不表示当前 R5/P62 或 Native 实机已加载，也不外推跨机器安装或性能收益。已封存的外置 6374 候选不作修改。
