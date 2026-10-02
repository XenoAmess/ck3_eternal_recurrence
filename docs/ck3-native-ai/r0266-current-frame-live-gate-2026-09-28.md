# R0266 当前帧现金读数的最短受管窗口

状态：**排程与安全门，未运行新的 CK3，也没有战争现金实值。**H3603 七件已完成 7/7 哈希传输验收，但 R0299 已使其成为历史帧；H3670 是 R0299 官方来源冻结配对，来源明确没有停帧窗口，七件虽精确接受但并未传输。R0300 又给出更晚 H3674/raw53219496，仅有原始 pair 身份、无官方 rebound/no-launch 或停帧。三帧均不能给当前 M5 填金额。五项 Q100000 战争现金仍为 null。

## 屏幕外先完成

1. 当战争现金生产者具备静态可审核读口后，取得**当时最新**官方持久 checkpoint 的 history index、date raw、actor、episode、WarID 重查来源、save/driver/sidecar/账本逐件 bytes 与 SHA-256；来源自己的 rebind/no-launch 不代替接收端检查。H3674 之后若继续推进，旧帧只用于隔离研究。
2. 确认当前本地代码、CK3 EXE、DLL 与 injector 的 SHA-256。H3670/H3603 来源历史 M6 DLL/injector 身份不能当新战争现金 producer。只有安全原生读口和 selected action 身份绑定可审核后才值得占屏正式采现金；仅有 MilitaryView 或顶栏 GUI 月费率无法补全五字段。
3. 先做精确资产接收、版本化风险政策与原生费用来源的静态验证。待消费方对 typed selected step、军队、完整路线、preview 序号、报价 ID 以及独立建设/战争 reserve 相加语义核准，才允许完整现金收据进入正式 M5。既有结构候选始终返回 formal_action_ready=false。

## 屏幕释放后的最短门

视频 E2-09 持有 ck3-screen 时不执行官方 no-launch、CK3 启动或进程附着。待其显式释放、CK3 与 recorder PID 均为空，先领取 ck3-screen，取得**当次新鲜** Steam 离线画面并按桌面恢复合同保存窗口位移与回执；不能从空 task-bus owner 推断已释放。

接收端新建外置 attempt，逐字节复制已核来源 save/driver/family/账本，不改旧 attempt；运行 exact-code official prepare/rebind、native consumer、cold validator 和 no-launch preflight，并冻结派生文件哈希。失败即停，不启动 CK3。正式受管冷启动应给 readiness 1800 秒和 session 总上限 3900 秒，本机已有首 turn 约 23.5 分钟的实证；旧 300/900 秒导致环境误判。暂停帧前后双读 snapshot/public/native revision、date、actor、episode、WarID、国库和暂停状态，失败即不出现金收据。

若仅诊断 GUI 缓存，先 VirtualQueryEx 只调查 private readable committed 区域总量、区域数与最大区域，再按独立上限作被动扫描；H2825 曾在旧 8192 MiB 界提前 RED，不能把前 8 GiB 未命中认成对象不存在。候选必须绑定唯一 player MilitaryView 或 topbar 实例、vtable、Q100000 比例和渲染帧新鲜度。顶栏 GetGoldExpensesBreakdown getter 会刷新/写缓存，不可主动调用；FleetPredictionMapIcon 总价可能覆盖多支预测军队，不能自动当 selected MoveArmy 的报价。任何一项未证只保留诊断原件，现金字段继续 null。

按本机已有冷启动，单次 no-launch/离线门约 7–15 分钟、受管启动与被动采样/后检查/清理预计还需 30–50 分钟；会话硬上限 65 分钟。**这个窗口最多获取月费或缓存诊断，不能在现有 producer 下交付五项现金。**若先完成真正同帧 producer 的静态门，才对当时最新且来源同意短暂停帧的 pair 预约正式占屏，避免历史帧重跑。来源若拒绝 hold，就记录原因并等待下一次自然冻结边界，不中断其正式续跑。
