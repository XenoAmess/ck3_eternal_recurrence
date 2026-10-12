# 2026-10-12 完整自动游玩入口与罗贝尔重开

用户要求永久删除“只处理非战争事务”的配置，并使用全部能力，重新以1066年的罗贝尔从头开局。

公共 MCP 的 `ck3_plan_turn`、`ck3_auto_turn` 现在分别直接调用 `GameplayBridgeService.plan_turn`、`auto_turn`。MCP 与 native-auto-run 的 `--nonwar-only` 参数、CLI 转发、Driver 属性设置、运行函数参数及报告字段已删除。旧开关不再是有效公共入口。内部领域研究函数及其历史证据不据此改写，现有资格守卫、异常处理和提交前 revision 检查保持。

本次同时同步三份原测试来源中的失效开关调用及路由断言，保留政府权限、Council 材料与 Army 完整结构覆盖。执行者与两路独立审阅者只进行了源码审阅，未运行测试、fixture、重放、AST 或项目导入检查；本条不授予业务运行通过。

## 作废的受限演示与实际问题

外置根目录为 `D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-resume-20261012/fresh-robert-demo-20261012`。

`attempt03` 实际从新空白用户目录启动罗贝尔，Game PID164268，1066.9.15/raw53144328，actor31254，episode `native-31254-d7a2c4ea147a`。它推进到1069.6.2/raw53168088，共990个游戏日；完成过事件处理、请求回复和猎场施工回读，但没有打赢战争，实际使用的 `--nonwar-only` 与用户要求的完整游玩范围不符。因此本场不作为重新开局的成绩。

保存原件 `attempt03/responses/314-ck3_save_checkpoint.json` 实际 checkpoint 为83,271,906字节、SHA-256 `9449482c3ca9c4ab69093f83bb26f81491fa449971990693d8544dd3ee33b53b`。声明窗口未及时关闭，后期已经发生真实敌方进攻。此次记录不授予应战或胜利能力。

录制脚本还存在一个实际错误：录像从启动前开始计45分钟，游戏循环却从 launch 后才计45分钟，录像先结束时触发异常并终止了受管游戏。`attempt03/ROOT-SUPERVISOR-CLOSED.json` 记载2026-10-12T10:27:37Z Game exit1，清理树归零；不是正常退出。一次关闭通知的坐标兜底因截图时效守卫被拒绝，未产生点击，也未证明关闭成功。

## 重新开局的范围

`attempt04-full-capability` 重新准备独立空白用户目录，没有复制上一场存档或 Driver。当前实机仍固定完整SDK91源 `50a1a5451227d1b30f42394dd02ddfbaea26a1ff`；新公共入口源码删除尚未部署到这个不可变研究副本。本场实际 argv 不传旧开关，使用该冻结 SDK 已有的完整普通规划器，不能把本条源码提交外推为实机加载了新 master。

实机版本为CK3 1.20.0.4，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。桥接DLL SHA-256 `a6657351be2bb1110fd112b8ffb6c752da7131dcb6cdb21ce800575514e54d7d`，为同源Native89的罗贝尔配置修正：只有c0325重新编译并追加 `XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1=1`，其余916 owner及 Runtime archive原样保留，340个 link token同序仅替换该对象和三项输出。源码原已存在默认OFF的CMake选项；这是实际编译配方纠正，没有新增原生功能。

新录制器按15分钟分段，正常分段结束不终止游戏；所有片段与旧素材共同计入原6GiB录制子预算，达到预算只停止新录制。当前的实际启动、选择、自动回合、战争和最终保存，以本场外置原始回执逐项更新，未发生的胜利和完整能力验收保持未完成。

先前“G2 6/8=75%”记录是历史专题状态，不能代表从新开局连续自动游玩的通过率。本次显示了入口、配置和运行验收未闭合的问题；不把源码研究或旧存档成绩作为新局整体验收。

## 存储与下一项实现

沿原通用存储策略1.0.0及Root手动12GiB准入，其他并发未支出额度保守计512GiB；复核及保护截止固定2026-10-12T16:47:28.264315Z，不因重开续期。未部署自动预留或自动回收器。原失败原件保留实际可读性及复核理由，媒体不入Git。

原版通知窗口源码 `game/gui/window_war_declared_overview.gui` 的 `war_declared_overview`，X及底部dismiss均调用 `WarDeclaredOverviewWindow.Close`。现SDK专门窗口类型和关闭操作尚未接入；普通导航会拒绝可见modal。后继需独立查询当前窗口身份、绑定主线程专用Close、读取实际隐藏或移除，再接入普通游玩通知处理。此次源码定位不是自动关闭能力验收。
