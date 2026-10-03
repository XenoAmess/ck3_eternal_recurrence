# 2026-10-04 本机验收过程记录

当前状态为 **实机产品 RED，尚未发布**。R0006 的旧基础属性事务已确证漏点；R0007 改用 A3 净修正账本，独立存档未见基础点改动，但正常查看事件的动态数值表达式失败，仍不可发布。具体见 [R0006 报告](live-R0006.md)与 [R0007 报告](live-R0007.md)。前面的环境及夹具失败一并按其真实边界记录，不能替代 [测试方案](test-plan.md) 的全部门禁。

本机游戏为 Steam CK3 **1.20.0.3**、build **25652598**，实际安装目录为 `C:/SteamLibrary/steamapps/common/Crusader Kings III`。`ck3.exe` 的 SHA-256 为 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。执行解释器为 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，Python **3.14.7**、MCP **2.0.0**。桌面实读尺寸为 **1024 × 768**。

全部过程资产保存在 `D:/ck3-experience-drain-feasibility-20261004/`。每个游戏 attempt 均使用独立 profile、冻结产品 staging 和外置夹具。R0006 使用 21 文件旧候选；R0007 使用 A0003 的 22 文件 staging，产品来源提交 `599af8da0008fd77f30347f7d3a7b2faef33a852`，逐文件 manifest 与运行工具 SHA 绑定在各轮目录中，不用后来的来源重新解释旧输入。SDK 的 clean detached checkout 为 `D:/sxad-freeze-20261004`，提交 `f643b32e6146dce73f77fedfefd8471da59fb04f`；屏幕 lease 的 custody checkout 是独立 clean `D:/ar`，不作为产品构建来源。

| 完整 run ID | 实际结果 | 证据及限制 |
| --- | --- | --- |
| `desktop-3fevhd2-1c74096080--superman-qiang--R0001` | 未启动游戏 | prelaunch Python dataclass JSON 序列化失败；不能算游戏 RED。旧 profile、构建输入保留。 |
| `desktop-3fevhd2-1c74096080--superman-qiang--R0002` | CK3 PID 3180 已进入普通 Robert 地图；夹具 RED | MCP Python 返回字段由 camelCase 改为实际 snake_case；停止旧消费者并让同一游戏 PID、同一 DLL 重新连接成功。夹具 `female` 字段及缺失 employer 被引擎拒绝。结束时通过 PID、创建时间、EXE 和 profile 命令行核对后停止自有游戏。 |
| `desktop-3fevhd2-1c74096080--superman-qiang--R0003` | 未启动游戏 | 已分配身份，但准备时发现原 injector EXE 不在原路径；保留 partial profile。DLL 存在；R0002 启动前已验证旧 injector SHA，不把重新 link 的字节冒称旧输入。 |
| `desktop-3fevhd2-1c74096080--superman-qiang--R0004` | CK3 PID 18504 已执行加载校验；夹具 RED | 引擎明确拒绝同时设置 `location` 和 `employer`；死亡原因 `death_natural` 不存在。修复为项目既有的 employer 单独字段，以及原版证实的 `death_natural_causes`。产品机制尚未形成后态结论。 |
| `desktop-3fevhd2-1c74096080--superman-qiang--R0005` | 原生编排／夹具 RED | execution ID `25b9f2a0-2162-4436-bab0-2940f89028e5`。Robert 开局成功；`set-speed-1` 成功，随后的 `resume-map` 被拒绝。夹具 `on_game_start` 的 `every_player` 为空，未排程。下一轮换用原版确证的 `on_game_start_after_lobby`。 |
| `desktop-3fevhd2-1c74096080--superman-qiang--R0006` | 产品 RED | execution ID `ab4b312c-81c6-424b-99f4-2c337063f00a`，实际 PID 17852。真正存档显示六项确定性 helper 扣点未恢复；随机 helper 漏掉六次恢复。日志 17 PASS/8 FAIL/3 未执行不能作为最终通过数。详见 R0006 报告。 |
| `desktop-3fevhd2-1c74096080--superman-qiang--R0007` | 产品 UI RED；矩阵 39 PASS/2 FAIL/0 未执行 | execution ID `63c8382d-e86b-43cf-8a93-b882b2f64794`，实际 PID 10824；独立存档 base/ledger/modifier 40 项通过、死亡角色定位 1 项不足。两个面板 FAIL 由原版诺曼文化抵消勇武负修正解释，旧标记保持。正常查看事件数字缺失且日志确证 data chain 错误；trait hover 1001 与查看前后 81 角色只读比较成功。21:42:40.648553 UTC 受管停止，进程树清理证明完整。详见 R0007 报告。 |

Steam 始终保持离线。R0002 的首次离线证据经过较长准备后才启动，故其普通地图只作为探索证据。后续正式启动前重新取得画面并直接审阅。

R0002 停止后，Win32 foreground 指向已经退出的游戏窗口，`SetForegroundWindow` 被拒绝，旧桌面时钟为 15:18。真实 Steam 窗口位移已读回，窗口像素改变而时钟仍与旧参考图相同；显式尝试现有 ToDesk 服务恢复函数时 `sc stop` 返回 code 5，finally 确认服务仍在运行。随后使用 UI Automation `IUIAutomationElement.SetFocus` 成功，Steam 商店实际重绘，时钟和日期恢复当前值。此恢复没有键盘或鼠标输入。

R0005 的新鲜离线证据是 `offline-a09/probe-1/steam-moved.png`：当前时钟 4:01、日期 2026/10/4，底部明确“离线模式”；SHA-256 为 `126527B847D42F6ABCA2A0E160E6BCAD9526925A7D5C28E012C15A2DEC422562`。恢复报告完成于 `2026-10-03T20:01:04.650812+00:00`，审阅后立即受管启动。

日志 marker 只作为补充证据。夹具还会把每条检查的结果写入角色持久变量 `sxat_case_*`，并设置 `sxat_scheduled`、`sxat_finished`，后续以真实 checkpoint 和保存的六项基础属性逐项复核。测试末尾人为给玩家的经验 1001 仅供数值展示验收，不能用于首发宣传图。首发媒体必须来自只挂载正式产品的普通开局，通过真实查看入口展示“未记录 / 0”。

历史构建资产有一项明确保全缺口：R0002 后原 injector EXE 在原路径消失，R0003 因此没有启动 CK3。随后仅重新 link injector target，DLL 字节保持不变，但执行者复用了 `D:/sxad-native-20261004-a01` 构建目录，旧 build stdout/stderr/result 三份日志被新的 relink 输出覆盖，未提前另存。原 injector SHA 仍在 R0002 preparation 中；原 DLL 和编译来源 metadata，以及新 injector 的逐轮 SHA 保留。不能据此声称旧编译全过程所有 stdio 都完整保全。此缺口不被后续收据补写为历史事实，后续 attempt 使用新目录保留全部输入和输出。
