# R06：真实 core 调用与指令 ADD 的只读关联载体

本实现候选的来源机器是 `desktop-3fevhd2-1c74096080`，准备于 2026-10-18 UTC。
基底为 `19024b4d79d818a88709c9932ca4eb364d81ef33`，实际原生来源仍限定
CK3 1.20.0.4、EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
生产 DLL/独立探针的重新构建、SYSTEM 读回、部署及 CK3 采样尚未执行。
合成 DLL 的离线执行与实际游戏资格分开记录；旧 binary 不会因源码改好而获得新能力。

原版链继续由[自然 regular core](army-natural-regular-core-entry-observation-12004.md)
与[物理 ADD](episode04-refill-instruction-add-provider-12004.md)约束：实际 post-date
`2A9A570` 经 `2A9A8DD` 调用 `2A98AC0`；请求向量生成后才在 `2A98B88` 加到物理
current，`2A98B8B` 为即时后态。后面的 pair clear 和 ArRg 缓存刷新不是该 ADD 的操作数。

旧探针只能给物理 ADD，两端的 native core token 为 null；按同一天、相同 TID 或相邻
journal 序号拼接自然父链都不充分。本增量复用既有共用 invocation allocator/TLS 栈，
在实际 core 线程、真正 original-once 调用周围取得真实 token，不新增计数器代替它。
自然父身份仍是原生事件的 `(clock_identity, sequence, thread_id)`，它与 invocation token
是两个域；`natural_parent_token` 保持 null，已有真实 TLS parent token 另行原样保存。

固定 DATA export `XarRefillCoreCarrier12004` 发布 64B 头及 16 个 168B owner-TID 槽。
每槽用奇/偶 sequence 包围原子标量写入，返回时失效；同线程递归保存、恢复外层载体，
无效的内层调用也会暂时发布 inactive，避免借用外层 token。不同线程使用不同固定槽；
槽满、token/sequence 耗尽或读取失败均为 unavailable，不改变游戏 original 的调用次数。
载体只包含 token、自然父/子事件、日期、线程及原生 manager/GameState 身份，不写游戏数据。

生产探针 v4 保留原九组 CLI、固定 B88/B8B、DR0/1 和既有恢复/detach 流程。
它只在唯一 `xar_ck3_bridge.dll` 中定量解析上述具名非执行 DATA export，没有任意地址参数。
只有选定 FullRegi、物理槽和 TID 匹配后才读载体；两个 trap 各保存独立两次 168B 原文、
实际 64B 头和读取诊断，要求稳定 active、同序列、同线程、同 token 和完全相同帧。
源码 epoch 是 ABI 标记，不能替代 Root 的 DLL/source/build/SYSTEM/runtime 资格。

v4 消费必须另外提供真实、完整的原始 CoreEvent。五个新增字段在原生产 normalizer
中是全部出现或全部缺省的严格扩展；旧 wire 不填假默认值。消费者核实际 entry/return
provenance、完整七槽/DATA、完整 generation、同调用 token、父/子事件、日期和上下文。
成功只授 `same_core_invocation_join_ready` 与该条自然归因；整个 NET 的唯一原因、整窗总量、
开关效果和完整 R06 业务资格继续为 false。v2/v3 的原物理消费判据保持。

下一场先在正常局面取得完整新帧。`prepare_live_refill_add.py` 复用分类器及完整顺序模型，
拒绝 partial、最终共享 q≤0、物理位置判据非 true 和身份不一致的目标。物理槽与 q-index
分别保留，重复 manager occurrence 不去重；`fixed_chunk0_prepare` 的正 q 明确是条件投影，
不冒充已写 prepared148 或真实 ADD。不能在 R204 末尾仍撤退的军队上原地盲等正例。

Root 在新的独立场次实际核 source/生产输出/SYSTEM/容量和同 PID 代际后，使用现有
prepare → launcher。prepared v2/ready v3 显式绑定载体模块路径和 epoch；独立读回已 armed
后才推进一次获准自然机会。结束先保存原始 CoreEvent，再给原 consume argv 追加
`--core-observation <实际已保存的单条原始CoreEvent.json>`；不预造未来文件或 token。
最后核实际 DR restore/detach，并分别 disable/readback DLL 的 regular_core 与 natural_phase。
DLL inline 不占 DR；另一个 external 四槽调试器与本探针不能共用同一 PID。

零样本、q0、超时或不完整 parent 只能说明该有限窗未取得目标正例；不能说没有 ADD、
补员开关关闭或永不补员。当前新增证据为 source/离线合成验证，实际 CK3 正 ADD 仍待采样。
