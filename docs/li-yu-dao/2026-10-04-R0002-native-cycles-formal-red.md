# R0002：原生三轮分合通过，正式入口与礼仪选择 RED

本轮 **原生 faith／rite 分合原型通过三轮验收；正式产品入口和朱熹礼仪选择 RED**。欢迎和选择事件能够显示并消费选项，但玩家实际礼仪没有改变，选择冷却却已写入；因此本轮不能宣布正式修习可玩、产品整体 GREEN 或发布通过。

永久证据位于 [R0002 验收目录](acceptance/2026-10-04-R0002-native-cycles-formal-red/FINAL-REPORT.md)，现行 [索引 v3](acceptance/2026-10-04-R0002-native-cycles-formal-red/index-v3.json) SHA-256 为 `aca33571847b96307aeb230bef32b4f061e9ba36b0281af6382cd65209481dda`。旧索引、初期待验状态及后续失败增补均保留，没有覆盖旧 attempt。181 个文件共 4,480,348 字节，以原字节保存小型回执、两次加载源码、对象摘录及必要截图；完整 native 时间线、debug.log 和大存档继续留在原外置永久树，以索引绑定路径、大小和哈希。

## 当轮身份、输入与来源

当轮来源是 `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game`，CK3 **1.20.0.3**，Steam build **25652598**；EXE SHA-256 为 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。实际开局为普通 **1066 罗贝尔·吉斯卡尔**，runtime 玩家 id **31254**、历史键 **1128**。基线保存态同时核对姓名、生日、狐狸绰号、奥特维尔家族和历史映射，见 [身份报告](acceptance/2026-10-04-R0002-native-cycles-formal-red/baseline/identity.verified.json)。旧准备回执的“867／29829”是保留的历史错误，未作为本轮控制台目标。

当轮新鲜 Steam 离线画面由根代理直接审阅，先取得窗口变化与新桌面像素，再确认“离线模式”，见 [新鲜度回执](acceptance/2026-10-04-R0002-native-cycles-formal-red/offline/steam-frame-freshness.json)、[审阅回执](acceptance/2026-10-04-R0002-native-cycles-formal-red/offline/offline-reviewed.json) 和 [原图](acceptance/2026-10-04-R0002-native-cycles-formal-red/screenshots/steam-moved.png)。没有把截图文件时间当作画面新鲜度。

R0001 为提交 `01a52e6842b0513c78053751304cfe60a963df92`；它的真实装载 RED 和当时源码保留。R0002 的实际冷加载 manifest 绑定提交 `7fd082eab7626239ecb88702d0ebae71f938b259`，装载修正来自父提交 `be321ac403741aed6036c46d6f1e426e10f26b4d`；两提交的产品 tree 都是 `5107ad4fa03bb66a663be1acc24f7a74c0ade4a4`。正式样板 18 个文件、原型 9 个文件在三轮期间均与首次停止审计一致，见 [manifest](acceptance/2026-10-04-R0002-native-cycles-formal-red/source-r0002/production.manifest.json) 与 [精确原型断言报告](acceptance/2026-10-04-R0002-native-cycles-formal-red/primitive/native-primitive-attestation-candidate-v2.json)。

CI 的实际引用为：7fd082e 的 [Official Runner CI 37163561735](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37163561735) success；礼与道专项实际 success 是 be321ac 的 [37163517527](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37163517527)。没有 7fd 专项独立 run；[只读回执](acceptance/2026-10-04-R0002-native-cycles-formal-red/ci/official-ci-readonly.json) 证明两提交的产品、专项 workflow 和相关 extractor 对象相同。静态 CI 与实机结论分开记录。

当前 1.20 native SDK／profile 已实际接入，见 [attach](acceptance/2026-10-04-R0002-native-cycles-formal-red/native/0002-attach.json)。日历推进、暂停、快照、事件选项和保存使用 MCP。该精确 provider 的工具目录没有任意脚本、控制台或 LYD 决议入口；缺少的入口由根代理执行桌面回退，并保全能力目录、代码哈希、窗口／角色／布局／租约门禁和全文读回。这是当前 provider 的能力边界，不是引擎永远不能增加这些能力的结论。

输入历史也保留：虚拟 backtick 未打开控制台；物理扫描码 `0x29` 成功打开；虚拟 Ctrl+A/V/C 读回仍为哨兵，故未按 Enter。最终复用已有物理扫描码 executor，在英文布局 `0409`、窗口焦点和新鲜 native 本地玩家 31254 确认后，完整复制读回 **`event lyd_np.9000`** 相同才提交 Enter，见 [v3 输入回执](acceptance/2026-10-04-R0002-native-cycles-formal-red/input/console-v3-execute.receipt.json)。输入 ACK 自身不算脚本业务通过。

## 分项结果

| 项目 | 实际结果 | 证据 |
| --- | --- | --- |
| 原型初始化 | 玩家 UI 决议执行；实际封臣阿贝拉尔 36445／history1134 为受测者；未走创建 NPC 备用路径 | 原型断言报告与冻结源码 |
| 同一玩家三轮合流／分立 | JOIN、DETACH 各 3 次；两种状态 D1、D30 断言各 3 次；终点 1 次；无 FAIL／REJECTED | [原始 marker 摘录](acceptance/2026-10-04-R0002-native-cycles-formal-red/primitive/debug-marker-lines.raw.log) |
| 冷却门禁 | 5 次阻塞断言；测试专用清除也恰好 5 次 | 原型断言报告；未验证自然五年过期 |
| 接收方分歧查询 | 明确比较接收方 main rite；三次合流前后均观察为 -15.00 → 0.00 | 原型断言报告的 transition scopes |
| 保存态对象图 | anchor faith33／rite150／领袖31254；branch faith108／rite151／领袖36445／title18417；c_camarda（title2250）保存 rite151 | [独立保存态 summary](acceptance/2026-10-04-R0002-native-cycles-formal-red/saved-objects/three-rounds.summary.json) |
| 欢迎事件 | native 选项后置条件通过，revision308 | [native 回执](acceptance/2026-10-04-R0002-native-cycles-formal-red/formal-ui-v1/native/0096-0022-welcome-select.native-01.json) |
| 礼仪选择取消 | 九个中文选项正确；取消第九项通过，revision311；金币、虔诚、威望、压力不变，仍可再选 | [取消回执](acceptance/2026-10-04-R0002-native-cycles-formal-red/formal-ui-v1/native/0099-0026-choose-cancel.native-01.json) |
| 正式入口 | RED：仅增加 lyd_enabled，玩家仍 rite150／faith33，未进入正式 main rite152／faith32 | [保存态投影](acceptance/2026-10-04-R0002-native-cycles-formal-red/formal-ui-v1/saved/formal-entry.objects.json) |
| 朱熹礼仪选择 | RED：目标 rite158／faith32；实际仍 rite150／faith33；新增选择冷却 tick365；没有修习冷却 | [前后存档比较](acceptance/2026-10-04-R0002-native-cycles-formal-red/formal-ui-v2/saved/zhuxi-choice.comparison.json) |
| 修习 | 本轮没有成功修习；“八种正式礼仪之一”的 OR 门禁正确拒绝当前原型礼仪，不能归咎冷却 | [真实 tooltip 截图](acceptance/2026-10-04-R0002-native-cycles-formal-red/screenshots/formal-study-requirements.png) |

三次分立实际产生动态 faith106、107、108。旧 faith34、106、107对象仍存在且有别的 main rite、没有原领袖绑定；旧头衔18372、18402、18410保存为已摧毁、无当前持有者。原支礼仪151的身份和信条数据保留。保存态读回证明这些具体关系，不能推断旧 faith 没有追随者或已经垃圾回收；本轮没有保存后重新加载验收。

朱熹目标的实际保存对象 `convert=no`。这是后续调查候选，尚没有调用链／反事实实机证明它就是失败原因；本报告不把字段观察或 native 选项消费成功升格成转换成功。

## 真实错误与收尾

退出后的 error.log 与三轮冻结副本**逐字节相同**，SHA-256 为 `9a94887d7d2f6e825cf806089445aa15ec06e3416d34613037214c4f911e53c5`。真实分类为 3 条 trigger localization perspective、165 条 unknown formatter、1 条 AI coronation、27 条 bp3_roaming invalid activity，见 [原始 error.log](acceptance/2026-10-04-R0002-native-cycles-formal-red/lifecycle/error.log) 和 [精确分类](acceptance/2026-10-04-R0002-native-cycles-formal-red/primitive/error-classification-addendum.json)。

原型 is_ai、正式 lyd_player_triggers:3 的 is_ai 及未知调用方的 is_alive perspective 错误都保留，正式界面粉色文字可见。formatter 原始 tag 字节为 `weak\x08\x15positive_value`，尚未定位；AI coronation 没记录宿主。bp3_roaming 日志明确指向 Irengba／26904／manipur019／c_manipur，异于受测两人，但没有无 mod 对照，不能排除间接影响。这些不是原型不变量 FAIL，却足以阻止整体零错误 GREEN。

最后一次有界 native 推进因真实终点 marker 停止并暂停读回；终点日志前1,585,492字节哈希与 [advance-cycles-004](acceptance/2026-10-04-R0002-native-cycles-formal-red/primitive/advance-cycles-004-report.json) 一致。后续 UI 错误没有冒充该终点内的断言证据，先前部分推进 attempt 也没有改写成三轮通过。

根代理已正常保存并退出，CK3 PID7564在 [退出回执](acceptance/2026-10-04-R0002-native-cycles-formal-red/lifecycle/normal-exit-desktop-confirmed.json) 中不再存在。[keeper FINAL](acceptance/2026-10-04-R0002-native-cycles-formal-red/lifecycle/keeper-FINAL.json) 记录线程退出、无 failure、最后 seq2626；[CAS release](acceptance/2026-10-04-R0002-native-cycles-formal-red/lifecycle/screen-release-completed.json) 匹配2626并实际释放至2627，resources为空。MCP close回执为 CLIENT_CLOSE_REQUESTED；其服务进程15206及keeper68845已停止由根代理报告，未把 close ACK 单独当作独立进程终止证明。

尚待验证的内容包括正式入口／选择的真实转换与成功修习、自然五年冷却／普通支付、main／last rite直接分立、达到100的自动分立、旧faith追随者和生命周期、保存后重载、native AI传播与正式学统权限。三轮原型 PASS 保留为可复用机制证据；正式产品需要另一个冷加载 attempt 修复并验收。

本报告保全者只读取现成回执及冻结文件，获授权后只导入上述新文档树，逐文件核对 SHA-256 与大小；没有编辑产品源码、发游戏／桌面／MCP输入、改变 Steam 或租约，也没有提交或推送。所有复制保留 BOM、CRLF、控制字节与原始换行；`.gitattributes` 的 acceptance `-text` 合同继续适用。
