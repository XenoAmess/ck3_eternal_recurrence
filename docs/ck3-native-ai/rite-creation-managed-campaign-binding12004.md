# 普通受管场次的礼仪操作绑定

R0016 在能力声明已修复后，首次高阶 `open_create_draft` 于发送前拒绝：普通 `native_campaign` 故意不生成 one-life 的 `episode_run_id`，但原礼仪传输误把该字段当成所有场次的必备身份。不能给普通场次编造 episode 或修改实际 snapshot。

适配复用 `managed_campaign_title_map_navigation_v1_binding` 的现有验证：分配器 run/state/pipe/host/frozen-argv、当前 exact .4 hello、存活玩家、暂停日期和主线程 owner 必须相容。结果保留原 `episode_run_id=null`，另附实际 managed binding。

最终确认继续使用原排他文件创建、flush/fsync、完整原生 preview/Can 和未知结果不重发合同。普通场次的语义意图键使用实际持久 state_dir、玩家和源礼仪；不把新 run ID、连接、日期或 preview 当成新的一次机会。不得通过换目录或复制不含旧 claim 的 profile 重试未知动作。one-life 的既有键保持原样。

R0016通过既有 `ck3_migration_raw_step` 只发送了一次可逆的打开草稿请求，原生总入口返回 `unsupported native gameplay step`，没有到达礼仪控制器，也没有打开草稿。原始请求保留为定位依据，不能称为成功的GUI兜底。正式后继继续使用上述高阶绑定与语义once；control队列按名字、内容、step ID排他消费，仍不能替代动作语义上的防重发。

机器证据：`machine_id: 4-8e1c2f1861`，原 snapshot 观察于 `2026-10-18T10:36:13.000669Z`，PID 19468，来源 `episode01/live/4-8e1c2f1861--faith-and-power--R0016/root-native-receipts/d1-frame-preopen-a01.json`。原件 SHA 记录在测试夹具 `tests/fixtures/rite_creation_actions12004/r0016-managed-frame.json`。本适配的源代码与离线测试不证明已热载、已打开窗口或创建成功。原高阶模块在首次失败后已缓存，磁盘修改不会自动改变持有中的 MCP child。
