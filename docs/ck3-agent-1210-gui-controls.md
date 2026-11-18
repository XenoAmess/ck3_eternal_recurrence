# CK3 1.21.0 后台 GUI 控件通道

本次精确来源为机器 `4-8e1c2f1861` 已安装的 Florin `1.21.0`、Steam build `26622941`，EXE SHA-256 `2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc`。本页记录离线源码与软件验证范围，实际 Game 结果由场次验收另记；没有使用屏幕、恢复窗口、抢焦点或 console effect。

来源窗口与布局索引见 [GUI bindings](../ck3_autonomous_player/native_bridge/research/ck3_1_21_0_gui_controls.json)。新版本的 native shortcut Activate 是 `0x4088FD0`，ButtonBase slot 13 是 `0x406D780`，直接查找根是 `0x4077F00`。Modal vector 已变为 context `+0x298/+0x2A4`，shortcut manager 变为 `+0x3E8`，不能把 1.20 地址和布局只换 EXE 哈希继续使用。

生产路由复用原 bridge、唯一 pipe 与已验证暂停主线程 mailbox。每次请求同时绑定完整 Full snapshot、native revision、连接代次、不可变绝对期限、当前逻辑 owner、应用及 GUI context。原生 owner stamp、TLS、pump epoch、proof-reset 和 mailbox executor 必须相符；最小化状态不构成拒绝条件。

`query-scripted-widget-controls-v1` 按带名根查询有界原生树；无重复根、环、截断或预算耗尽后才发布 provider generation。`activate-scripted-widget-control-v1` 只接受该连接已发布的 generation 与 row ID，没有 caller 指针、root scope、actor scope 或任意表达式入口。动作前重新读取两遍实际 tree、父子关系、modal 路由及 callback 源，与 query 原件比较。每个动作句柄只消费一次。

根定位现只读当前`CJominiScriptedGuiManager`已发布的完整登记表（静态对象`0x5D6A9F0`，最多4096项），不调用懒初始化或扫描整个GUI树。逐项核实际类型、GUI context及已物化widget，拒绝重复身份和同名根，再沿目标的双向父子边追到已验证global owner，继承祖先的hidden/disabled状态。登记表及祖先身份均进入私有capture相等比较，激活前重新捕获；目标子树仍最多2048项、深度64。无关窗口的庞大子树不会因此被遍历。来源为同一精确EXE的manager创建、刷新、窗口创建及销毁路径；其他版本保持无资格。

R0012实际GUI查询返回旧`gui_global_tree_budget_exhausted`，该旧错误同时合并了节点／深度预算、指针读取及重复／环，不能单凭错误名确定实际是哪种结构失败。新实现为目标子节点和global父边保留分别可识别的拒绝原因。本次源码修复及软件检查不替代后继实机的窗口定位、按钮效果和金融账目验收；R0012已独立确认正常退出0，而金融业务仍未通过。

1.21 普通表达式 callback 的构造函数 `0x406F680` 分配 `0xF8` 字节，vtable `0x50BF430`，invoke `0x406FC40`；表达式位于 `+0x10`，实际 receiver 位于 `+0xF0`。私有 witness 保存完整 callback、五个 operand vector 和 parameter scope chain，不把 `enabled=true` 单独当作执行许可。尚未识别的 callback class 可以被观察，但保持不可点击；原版特殊决议回调不因此获得新版本资格。

`submitted` 仅表示实际调用了引擎普通 shortcut handler，`native_handled` 只是原生诊断。它不证明业务 effect 已完成，必须用之后的独立 query 和资产／订单／角色观察验收。进入原生调用后异常或结果不明记 `indeterminate`，不重试原句柄。

金融产品正常入口为已注册的 `xfm_market_entry` 根及 `xfm_market_open` 按钮；它调用实际 ScriptedGui，打开 `xfm_market_window`。交易、发行、期货等主要控件有稳定 name；列表中同名按钮由本次观察的 child path、row ID 及完整私有 binding 区分。

软件验证使用 `ck3_1210_gui_control_v1_test.cpp` 的真实 request parser、provider reducer 和 serializer，覆盖字段类型、版本身份、scope 源变更、连接变化、disabled、双读竞态、未知派发、溢出及禁止重放。它不调用 Game，不授予原生装载或业务通过。
