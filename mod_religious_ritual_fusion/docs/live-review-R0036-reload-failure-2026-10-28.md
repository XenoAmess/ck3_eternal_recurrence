# R0036 重载实测与失败资源闭场

machine_id: `4-8e1c2f1861`。实测开始于 2026-10-28T06:14:56Z；CK3 于 06:32:26Z 正常退出，外置 Root 调度原句柄于 12:37:59Z 收齐，屏幕于 12:45:06Z 通过 CAS14439 释放。本文只记录实际范围，不授予整场、五日邀请、完整家属或发布通过。

外置根 `R=C:/workspace/rrf-development-20261024`，`C6=R/review-fixes-a01/cold-R0033-five-day-a01`，`V21=R/recovery-v21`。机器、路径和时间仅证明本机本次事实。

实际新进程 PID15488、出生 FILETIME `134376417061741544`，CK3 1.20.0.4，EXE SHA256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。原生恢复绑定为 `ACTUAL_SAVED_CAMPAIGN_CURRENT_CONTEXT_BOUND`，日期53144376、暂停、玩家31254、地图就绪。输入为真实 R0033 Save3，68446460 B / `45f225aa8f60542c63696cb42fe259dd8ad4a04b75fbf328866fadaea02a9f5d`；启用正式模组及8文件被动观察夹具，没有 MTS/DES 或开局初始化。

原生读回礼仪153、信仰13、宗教8、创建者31254，三核心为 communal_identity/esotericism/astrology，30项教义，虔诚5400。通过实际 `decisiondetail_view` 控件一次确认只读观察决议；debug.log 实际出现 `RRFAT: TEST PASS rite_persisted_readback`。该隐藏事件只写观察标记，不是完整保存图验收，也不打开事件窗。美德/罪恶目录因当前信仰窗口未绑定礼仪153仍不可用，不能把 null 当空列表或复用其他礼仪的数量。

06:31:21Z 的原生保存成功，当前 checkpoint 为68445278 B / `14fa05fed7a257003282e08a3b97e8730c5b6d570cada493534927db2ca7a1f1`。随后 Root 的控件查询错误地保留保存前 public revision3；保存后已为4，接口拒绝，host实际退出1。CaseClient 保留失败并通过原 typed 正常退出通道确认桌面退出；原生与保留 OS 句柄均读回 CK3 exit0，job/tree 清理完成，业务仍 false。没有重放失败动作、重复邀请或推进五个自然日。本轮没有产生合格的新宣传截图。

原外置 serial 只接受 normal_close_qualified=true，无法消费这条真实失败资源终态。使用本机 Python3.14 的 remote_exec 将不可变的一次性收尾送入该外置调度自身的原主线程，核验其原文件、PID/出生身份及真实 typed/OS/host 终态；仅消费已保留的原 Popen，未修改冻结 SDK、游戏或 normal_facts。实际 public2、两 guard0、keeper0、allocator0，原 Root 外层 wait2。所有原始收据形状保留在 `C6/metadata/public-operations-a01/root-execution-a43`，包括 `REMOTE-FAILURE-ORIGINAL-TERMINALS.actual.json`；屏幕已释放，桌面恢复1024×768。

共享 allocator 新增窄类型 `root-serial-original-popen-v1` 格式，分别读取 intent、started、original-wait、retained-handle terminal 原件，验证精确 Pins、PID、十进制 FILETIME、时间顺序及真实原等待结果，接入既有 played failure reducer 和原 writer 锁。它不把 played 场次伪装为未启动分配，也不授正常退出或业务通过。原 CI 失败闭场完整3命令59测试，加完整公共导入10命令和RRF五模块消费者254测试，全部原 wait0、0 skip；补充 preserved-failure 17测试通过。新函数/producer的严格静态检查为明确提取范围，不代表旧 allocator 全模块严格检查通过。

R36 实际 bundle `V21/Root-metadata/R36-admission/a02/R36-FAILED-LIVE.bundle.actual.json` 为12124 B / `53804cde25034b29066b73845ea205eb624a41a65f3533329d90cf9705edd0a3`；真实 reducer 只读预演原 wait0，结果 `previous-shared-failed-live-resource-closed`，全部资格仍 false。后继实际 allocate 仍须在原 writer 锁内重验，预演不能替代它。

零日 checkpoint 的两次独立 Java V4 解析实际退出0，记录在 `V21/R36-oracles/zero-day-a01`。同一 Win32 拒写/拒删句柄覆盖两次原 Java wait 和前后身份/哈希校验，最后才关闭。组合图与八家属分开读取；完整比较范围和真实差异以该目录的 COMPARISON 原件为准，不能宣称所有演员记录逐字不变。

旧 C6 keeper 在外置调度悬空期间继续写快照，闭场实测 keeper charged204722176 B 超过旧104857600 B，metadata224649672 B 超过旧150994944 B；旧10Z期限和这两项 RED 均保留。CAS291→292 是前瞻的新有限审查：新 owned7GiB/gross9GiB、项目配额84000000000 B、V21验证96MiB及唯一后继场1040MiB，18:57:49.569946Z到期，不自动续期。完整原生库存、物理容量、quota/owned/gross均实际通过；不重置历史 gross/addback、其他任务预留或系统增长。它只授验证与准备，尚未授 Game 启动。

后继仍须完成真正的五日邀请回复、家属资格与状态、当前礼仪美德/罪恶完整目录和实机图片，并另验 MTS/可选 DES 等未完成需求，再更新同一 Workshop 条目3826756673。现有商店两张新增 UI 图是此前已验证的0.2开发预览，不代表 R0036 或新版二进制已发布。
