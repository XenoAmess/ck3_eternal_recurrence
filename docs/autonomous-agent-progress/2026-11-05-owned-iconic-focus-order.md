# 自有最小化窗口先恢复，再执行原严格聚焦检查

实际恢复入口曾在任何聚焦前失败：Game117900的唯一可见自有 SDL 窗口已最小化，client为0×0；`focusOwnedWindowOnce`却先调用强制2560×1440的 `unique`，所以到不了后面的 `ShowWindow(9)`。这是一项独立的窗口恢复顺序缺陷。

修复只在既有自有聚焦操作前发现需要恢复的窗口：精确PID、可见顶层root、最小化及唯一性，两次有限枚举，加上实时HWND／PID／root、进程birth和原期限复核后，才恢复该窗口。随后仍以原HWND进入原严格尺寸、身份及前台检查；非最小化路径保留原逻辑。截图、输入、permit、`unique`及其它原检查全文保留，不添JNA接口、数据类型、循环抢前台或其它UI动作。

生产源0e64a13c→6f9d3497共2个owned span，outside全文逆还原一致，实际与正式同叶前后字节相同。模型5完整源50700B首派真实stop，10.5131025秒／TTFT1.8928083秒；仅两行入口flow／命名部分采用，缺第二枚举及prewrite复核、改变非最小化多窗语义的raw helper未采用，owner重写两个private helper。新Test模型length8000整份未读、0方法采用、没有R2，owner接管完整软件测试。

必要编测已实际闭环：生产1TU0／9类／4.8839697秒，新Test1TU0／4类／4.5112216秒，原3方法3P／3.9824168秒，XML43151B／cc18c33e…，0error／failure／skip／abort，全部close／fence／terminal与资源释放独核。3方法验证最小化0尺寸先恢复再原严格聚焦；歧义、他PID、二次枚举漂移、birth及期限错误零写；恢复后尺寸／HWND不符仍拒绝、只读截图不自动聚焦、非最小化原行为保留。Windows和像素端口使用已有软件IO seam，未构造私有Managed owner或permit，未访问真实桌面。

旧新9个类名相同、无字段变化，但两个private helper及synthetic形状变化，不授body redefine。源码／软件通过与实际采用分别记录；不会为该候选重载健康24，也不授本次Native完整读取恢复、自然M7或性能通过。

独立现场事实不能归因本源码：一次精确自有窗口restore及既有production focus成功后，Core仍不可用。之后Runtime对已视觉确认的唯一事件选项做一次独立owner-only UI输入，SendInput一call／请求3事件／插入3，前后图与原件保留；插入计数不当作NativeACK或语义成功。弹窗消失后唯一Full READ在22:37:16.728169Z→22:37:19.060010Z真实成功，date53159088／paused／mapReady／actor31254。此对照不授具体Native submit拒因或modal为唯一可能原因，更未用截图伪造Frame／event ID。

Root随后独核原140→143、child142及C5：原command／body／22:29:59.575528200Z deadline完全不变，以既有SameGameWatch只读角色结算，C5链接C4，pending=null、新世界38eligible／8saved，没有新增SAVE。Runtime24重新LOOP后正常游玩。首140失败时80次READ约60秒、独立Core拒读及预算65536／60秒原件均保留；下一窄P0只增加首份已归档负ACK通知，不改原重试、期限或Guard，也不泛化任意点击。
