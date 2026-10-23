# 通用产品验收的自然日与事件交接

以下实证来自 `machine_id: desktop-3fevhd2-1c74096080`；R26、R27 均保持 RED，离线回归不计为实机通过。

R26（2026-10-23 18:24:30 UTC，18:46 UTC 复核）直接投递旧 `advance_day`，没有 `allow_event_boundary`。一天目标处出现事件，冻结 host 没有设置 `allowed_event_instance`。32 项完整帧诊断只有第 9 项失败；没有证据归因为暂停预算或 owner 缺失。[原始诊断、wire 与来源 SHA](../tools/testdata/generic_product_day_boundary/r26-pause-admission.actual.json)保留实际失败帧。

普通推进现接公共 `CaseClient.advance_day(days=1, allow_event_boundary=True, allow_actor_change=配置值)`，按能力选择原生单日或既有事件边界通路。完整暂停、同一进程/连接/角色与精确 build 守卫保留；未知结果不重投。`actor_transition_days` 继续保留旧 `wait_for_played_character_change` 参数，冻结 host 的旧 `advance` 读取它，事件边界分支不读取；仅验参数保存，未验角色切换。

事件和交互通知分别交给 Root，ACK 后读回旧原生实例是否消失。同日不同实例继续交接；每次使用独立递增边界序号，避免检查点重用。缺少合法动作或后验时保留诊断，不把 ACK 当作已关闭。

正整数实例要求来自 `native_driver.py:21822` 的 1..2³¹−1、原生 event context 的非正数拒绝与通知解析 minimum=1；没有从观察层可读零推导动作资格。[测试](../tools/test_generic_product_day_boundary.py)覆盖实际公共客户端到适配器及同日连续窗口；成功 native envelope 为测试构造。

R26 历史冻结来源 SHA-256（不代表 R27 或当前候选）：

- adapter：`8327f1e295a050b62d542f37d27c0ff34c8376598bbb6c8ce95bc2a8b402e5d2`
- public client：`dfc100e133aa686ad64c906959de6e65052a8eb82e86889f48483a736af17b6d`
- host：`776fc23d6a0d7913df96e1799ae25b5021db99b76fb943802171bac6f85c808f`
- native-day projection：`c6b5e4fec8bdb9895a9e73506d56d748417af7c6403c07ed2863ab1d55d2ee54`

R27（2026-10-23 19:16:56 UTC，20:02 UTC 离线复核）上述事件接线已生效。随后运行帧 `native:6` 日期先变为 `53144352`，heartbeat mailbox 尚为 `53144328`，paused 均为 false；完整帧只有第 31 项日期一致性失败。原生 snapshot 于 `19:16:56.534117Z` 发布，同日期 heartbeat 于 `19:16:56.556580Z` 发布，相差 **22.463ms**。旧 classifier 只识别 mailbox 超前，遇 snapshot 超前立即抛错。[实际失败与相邻消息](../tools/fixtures/host-running-date-support/r27-failure.actual.json)保留两份完整公共帧、原生消息和来源 pin；没有保留下游 coherent 公共帧，不能追认为已恢复。

公共构建入口 `ck3_mod_acceptance_build_runtime.py host-running-date-support` 生成新全局 manifest/pathmap。它仅替换旧 host 的 `_campaign_pending_running_date`，以绝对路径加载逐字固定的 canonical `campaign_running_date_publication_v1.py`；旧 SDK、DLL、游戏与原 host 不变。限定原 host SHA `776fc23d6a0d7913df96e1799ae25b5021db99b76fb943802171bac6f85c808f`，精确反向恢复原字节；Selection 和 frozen launcher 均检查机器、时间、生成器、helper 和投影产物的完整闭包。各产品共用同一 host。

新 classifier 只允许原 deadline 内纯读等待下一完整 coherent 帧，支持相差一天的两种独立发布顺序；不会准入失败帧、放宽 owner/date 守卫或重发未知 advance。[投影回归](../tools/test_ck3_mod_acceptance_host_running_date_support.py)以真实 R27 帧验证唯一失败项和实际 import route；后续完整帧明确为作者构造，另验永不收敛超时且不重投。新公共投影仍待另场实机验证。
