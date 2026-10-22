# Prepared case 的真实公共消费者修复

机器 `pc-20260924rtuf-f11af23c08`，2026-10-22 UTC。原 c16 离线公共链实际得到：threshold 的 plan / prepare / preflight 均退出 0；timer 的 prepare 退出 0，但 preflight 退出 2，报 `Exact standalone registry stanza required`；curse 在 plan 退出 2，报只读 opt-in 工具声明不合法。原输出与退出回执均保留，未修改 c16，也不将它们追认为新源码通过。精确来源见 [本次回执](evidence/prepared-case-preflight-fix.json)。

共享 `Selection` 会把 prepare 产出的真实 `startup` 和 `initial_plan` 写入选中 case。timer、cold、curse 原先将这份合法绑定后的 case 与未绑定的整份登记模板比较，导致拒绝。现沿用 threshold 的稳定 case ID、必需工具和显式权限合同检查；canonical contract、整数类型及原源码、部署文件、fixture/正式产品完整闭包守卫继续执行。curse 保留已经默认注册的 CampaignRoot 查询为必需工具，移除不适用于该工具的可选 read-only opt-in，独立 stanza 与公共登记保持一致。

cold 公共 prepare 还暴露了 SDK 来源冲突：产品目录中的顶层 materializer 导入会选择产品源码树的 SDK，与公共入口选定的冻结 SDK 冲突。cold 现在从实际 `shared_source_root` 延后加载已有 v2 materializer；保留原 helper 的同树 SDK 硬校验，没有修改共享 host、v2 helper 或增加 fallback。

修改后的 timer 和 curse 均实际完成 plan0 → prepare0 → preflight0。cold 使用真实 R8 输入先 prepare0，再携带真正的 prepared-case 执行 plan0 → preflight0。未绑定的 cold plan2 只说明六个保存输入尚未绑定；其原输出保留。旧 SDK 逃逸的 prepare2 也单独保留。离线测试 mapping 只将产品 `repo_root` 指向待提交源码，其余 c16 backend Pin 未改，禁止用于 allocate/run；实际场次须由 Root 提交并冻结 c17 后重新准备。

原部署消费者又实际读通 timer 151、curse 162、cold 37 个源码与部署引用。完整独立 CI 四命令组通过：214 项产品测试（352.297 秒）、六个完整文件 strict、v2 profile 八项测试、独立 SDK profile 八项测试；现有全模组 strict 另通过 53 个完整文件。新增持久回归执行真实 `Selection` prepared 消费、错误/缺失字段、类型和 JSON 往返，以及独立 Python 进程内选定冻结 SDK → 既有 v2 producer → inventory consumer。

这些结果只授予源码与离线公共准备路径的验收范围。未 allocate、未启动或控制 CK3，timer、cold、curse 的新实机业务结果仍为 `NOT_RUN`；R8 原件不会因此获得新的冷载或六格业务通过。
