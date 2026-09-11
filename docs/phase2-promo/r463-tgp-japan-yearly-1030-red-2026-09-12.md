# R463 `tgp_japan_yearly_events.1030` RED 与最小合同

日期：2026-09-12（Asia/Shanghai）

## 状态

当前轮次 R463 / PID `113420` 在固定 120 游戏日 Stage 10 source 窗口的 `date_raw=53219640` 暂停于原版事件 `tgp_japan_yearly_events.1030`，instance `343`。Operator 保留 `STAGES_RED_PARKED`，没有尝试选择，CK3 没有重启。冻结 RED 为：

- `_runtime/p1-stage10-source-r349-r462-r463-20260912/r463-tgp-japan-yearly-1030-red-freeze.json`
- 392,668 bytes
- SHA-256 `07BC6B2AA7A4AD2AC5AE4422CE9B129118C1940123DD187E2A3BC8AE2AE5A4C6`

该 RED 是合同注册表尚未认识真实原版事件，不是 mod 脚本、DLL 或游戏文件故障。P1 保持 `6/9 = 66.7%`；Stage 10、Stage 11、代表性终态 cold restore 仍为 PENDING；P2 最终宣传视频继续硬锁定。

## exact-build 定义与调用链

- CK3 `1.19.0.6`，`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- 定义：`game/events/dlc/tgp/tgp_japan_yearly_events_ariana.txt:926-1089`，SHA-256 `B9F5799465E9B83B16C97086BC74F43ECD3949680AE1A78C081ED44ECD9B5FD6`。
- 专用年度池：`game/common/on_action/dlc/tgp/tgp_japan_yearly_on_actions.txt:1-50`，`.1030` 位于第 24 行、权重 100，文件 SHA-256 `40D68D6306D3E180E40EFBC80D5879DA825AB111F7EC0870682AB414F2AD5FE4`。
- 上层年度入口：`game/common/on_action/yearly_on_actions.txt:2552-2563` 在第 2558 行以权重 6 选择 TGP 日本年度池；该文件 SHA-256 `0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA`。同一文件的通用年度池也在第 3780 行词法引用 `.1030`，源码索引如实保留两条候选，不把词法命中冒充唯一运行时 caller。
- 年度池要求 TGP DLC，并要求日本文化传承、日本地区首都或日本政府之一；事件自身要求可用成年角色，且有 15 年 cooldown。

## R463 精确窗口

- root 为当前玩家 character `32904`，saved scopes 为空。
- current-event 投影严格显示且启用 native indices `(0, 1, 2, 3)`。
- native snapshot 保存五个源码 authored options；第 5 个 authored option 受 `has_trait = cynical` 约束，R463 当前窗口未渲染，因此合同使用 `option_count=4`、`snapshot_option_count=5`。
- query snapshot 为 `native:44`，revision `45`，connection generation `1`。

## 选择与范围

合同选择 authored option 1 / native index 0。该路线无后续事件、无资源支出，添加五年 `tgp_shrine_health_modifier`，固定减少少量压力；若角色已受伤，还有 25% 的伤势改善机会。其余可见路线分别偏向继承人、财富和虔诚。

本次只比较该事件源码明确写出的终端效果。虽然事件 `theme=faith` 且有虔诚选项，合同不读取或推导 faith、doctrine、tenet、fervor、改宗或宗教改革状态，因此没有越过项目所有者暂缓的通用宗教域边界。

## 通用资产与验证

- 新增 `records_tgp_japan_yearly.py`，把 campaign identity 替换为 `$player`，只绑定空 scope、四项渲染投影及 authored1/native0。
- exact-build source index 从 183 个事件增加到 184 个事件：184 个唯一定义、522 条词法调用候选、71 个定义文件、79 个 caller 文件。
- portable evidence bundle 已收入三个源码文件与 R463 不可变 RED；离线自校验为 280 个 evidence / 1,086 个 references，状态 GREEN。
- manager recovery 定点测试在普通 Python 与 `python -O` 下各执行一次，均为 `1/1` GREEN；没有运行全量或长跑测试。
- 变化仅涉及 Python 数据合同、只读 MCP 资产、测试与文档；DLL、游戏文件、启动配置、加载顺序均未变化。按 SOP 在提交推送后对当前轮次 R463 原位热重跑，不新建 CK3 轮次，也不延长既定 120 游戏日窗口。

## 待关闭项

- 根仓提交推送后，同步 open_kaishek 的内容兼容记录；公共 MCP schema、工具名和参数不变。
- R463 热恢复后补写 event instance advance、选择后证据、最终 commit hash 与 RED 关闭状态。
- 若固定窗口耗尽仍未到 Stage 10 `.390`，按既定上限收口并判定此 source 不合格，不扩大观察窗口。

## R463 进程退出与封存补记

合同工作包提交并推送后，准备执行同轮次热恢复时，Operator 只读状态显示当前轮次 R463 的 CK3 PID `113420` 已不再存在。没有向 CK3 发送 cleanup、终止、重启或游戏输入；Windows Application 事件与运行目录也没有留下 CK3 崩溃事件、dump 或 exception 文件。因此只能确认“进程在 RED checkpoint 保存后消失”，不能证明具体终止来源，也不能把后续验证记为同进程热恢复。

随后通过同一 Operator MCP 对旧作业发送 `cleanup`。最终状态为 `CLEANED`，产品结果仍为 RED，`cleanup_result=GREEN`，CK3 清单为空。证据为：

- canonical cleanup：`live-artifacts/09_phase2_native_session_cleanup.json`，31,826 bytes，SHA-256 `843A695FFAD821B09C4289254A20C143CC292B7614DD14329D7C13618B212733`；
- managed cleanup：`live-artifacts/terminal-stages-managed-cleanup.json`，33,405 bytes，SHA-256 `AD209C55EFCEFD3FC5BA1764CD9C4CB18172987C0C1B0F2B9F6AA4AD79954B8F`；
- 可恢复的最后 checkpoint：`live-artifacts/terminal-partial-attempt-02.ck3`，87,799,060 bytes，SHA-256 `3F8629957AA0DC9002AB97417E450167B23708BB2B7492CBE00189C913CE09C4`。

旧 Operator 服务与作业进程已经终止，端口 `12431` 不再监听，CK3/旧 Operator 进程清单均为空。当前轮次 R463 已终止；旧轮次 R462 早已终止。

由于 R463 已死亡，原计划的同轮次热恢复取消。下一次实际启动必须使用新轮次。为避免重放 110 天已验证前缀，后继激活从上述 partial checkpoint 开始，并把 `max_advance_days` 缩为 10；这对应原始绝对截止 `date_raw=53219880`，不延长既定 120 游戏日边界。Operator 生命周期固定要求一次前台 warmup 后紧接 gameplay，因此下一组为 R464 warmup / R465 gameplay。R465 只允许关闭 `.1030` 并跑完剩余窗口；遇到新 RED 立即停，不做永久长跑。
