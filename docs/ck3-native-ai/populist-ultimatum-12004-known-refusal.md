# 1.20.0.4 民众派最后通牒：来源已知时拒绝

P19 的实际事件 `faction_demand.1001`（calculated ID `3551001`、instance `72`）只显示可选的 native 2、3，顺序分别为 rendered 0、1。原版 `events/factions/faction_demands.txt` SHA-256 `eb17720ca9d48acfb8cc24e5f61edc62fd2d4d2d599561c92854fc762104eccd` 中，native 2 通过 `successful_popular_revolt_outcome_effect` 同意独立；native 3 拒绝并调用 `faction_start_war`。实际 AUTO518 选了 native 2；事件实例消失得到确认，领土持有者变化未独立核验。原回执仍保留当时的 unknown 分类。

普通策略只在离线 registry 对精确 .4 来源指纹 `f41794487b9ed31454e9687052b9b84b761104f61db412ae76c5c0518ecdf96c` 标为 exact known、七个保存作用域与当前角色一致、同帧同进程、只有 native 2/3 按上述顺序显示且均 enabled、native 3 的 typed step 已发布时，选择 `select-event-option-4`。这是保留领土的偏好，接受派系战争风险；不预判战争启动、胜负或头衔最终归属。其他事件、来源变化、布局变化或证据不足继续既有首个可选项规则。

计划中的 `active_event`、`event_decision` 和 fallback capture 同时改为 native 3/rendered 1。Service 在提交后核原实例消失和回执选项一致；不一致时保留原回执、拒绝重复提交及业务计分。便携夹具取自 P19 AUTO518 的窗口/绑定字段，模拟的 native 3 ACK 明确不是实机结果；`test_populist1001_known_refusal.py` 覆盖正常链和错索引、过期帧等拒绝。Root 外置队列分类器未来也应先消费同一 `verify_source_reviewed_populist_refusal_result_v1`，再回退普通 primitive 分类。

## 2026-10-18 当前exact绑定勘误

上文固定 `3551001 / f4179448…` 是初版范围；现公共实现已由P43改为在相同 `.4` 来源与完整选项目录下，使用当前 native calculated ID重算应有exact指纹，并继续要求生产loader已验证当前exact entry。通用letter-event重绑定没有开放。`3571001 / 14b787d2…` 的实际历史投影现可进入拒绝偏好；本轮在SDK48冻结源与公共叶核到同一SHA `6e8a5777…`，29项离线检查通过，没有新实机拒绝或保地信用。续行须保留当前entry／facts／可读原版源的知识闭包，详见[P50失地复核](p50-populist-loss-prevention-2026-10-18.md)。

本次核对 `machine_id: xenoamess-full-tower-eb9d2c1186`，观察2026-10-17 18:18:36–18:21:15 UTC；源自机器ID命令、源码SHA及生产loader离线读回。上文P19历史记录未附机器ID，仍为`machine_id: unknown`，所属机器未核实；不由本次读回追认其安装或实机效力。
