# P20 可选读取恢复与家庭查询节奏

本包将已审阅的 P20 Python 修复按局部差异合回公共源码。机器标识为 `xenoamess-full-tower-eb9d2c1186`。原 P19 construction 526/588、council 600/605 的错误与停机修复事实保留；源码修复、离线测试和 P20 实机验收分开记录。G2 M0–M7 仍为 **6/8**，M6/M7 未完成，连续三十年与平均 0.5 秒/游戏日均未由本包达成。

## 行为

- **建设已完成材料不可完整投影：** 在原意图、owner、暂停帧与只读租约均匹配时，返回具名的不可观测结果，保留原 applied 材料和 completion；不制造完工收益、不重发建造。月度观察和 worker epoch 变化可继续；未知 pending 或租约不匹配仍拒绝。
- **议会可选规划读取暂不可用：** 保存完整请求、原 ID、原始结果或结果缺失的诊断。仅当前无 pending、同帧的 planning 查询失败进入 30 游戏日技术延迟。失败不计真实操作，也不增加无操作计数。动作、LIFE、未知错误与变帧不走此分支。
- **六项独立冷却：** 赎俘、议会、生活方式、建设机会、王权、宴会各自记录三个无操作帧后延迟 30 天；同帧去重。公共 Service 已接入持久化 consumer，技术延迟期间实际跳过议会查询；已有 pending 的回执处理继续。
- **家庭查询：** 两次明确无机会后形成的 30 天冷却，到期复查仍无机会时可连续下一周期。和平普通规划也复用该机制，保留当前继承人、玩家配偶、episode、待处理婚姻/教育及未知回执守卫。两项婚姻 transport 的五次快照读取改用已有不导出原生命令历史的入口，输出与日期漂移拒绝保持。

公共合回保留现有 Sway 完整普通规划接线、Clan 建设场景、负金材料资格、movement prefix 和 Army 查询范围守卫。Service 的六域 consumer 是此次必要依赖，没有复制旧 SDK 的 profiling 包装或整叶覆盖公共源码。没有新增 Native API、部署 DLL、操作游戏/录制/桌面或读取活 Driver。

## 来源与验证边界

外置来源根为本机 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/`：

| 来源 | 固定身份或范围 |
| --- | --- |
| `ROOT-FINAL-SDK-FREEZE-P20.json` | SHA-256 `f9a7869bea5dda55600320ecc55f600ee279e9961c04453ab6165eebced0205d`；1310 叶，9 叶变更 |
| `p20-sdk-only-incremental-plan01/P20-SDK-DELTA-PINS.json` | SHA-256 `30c1902b7337b12538530751b249f92f87d16e8707f2c2cc9d91bc94b399de23`；逐叶前后 pin |
| `p20-construction-material-nonfatal-candidate01/FINAL-MANIFEST.json` | 两个 Python 叶；实际 533/534 字段投影及合成 transport/worker 包络 |
| `p20-council-planning-defer-candidate01/MANIFEST.json` | transport、consumer 与独立冷却模块；12 项定向离线结果 |
| `p19-war-termination-cd01/PEACE-FAMILY-P20-DELIVERY.json` | 最终 SHA-256 `3eb73e2715f385d18d46de95dd87d22067bd7ee09673f1babf24765e23715632`；实际 570/576 回执投影与五项定向用例 |
| 私有 P20 classifier | SHA-256 `955d786ee21b14a222a749ead23d7a181cadc9ce117bdb1825cc123187764ae3`；实际 6820 基线加 typed construction 分支，独立于公共九叶 |

便携测试只使用仓库内小型字段投影和临时状态目录；原件 SHA/来源与合成部分在 fixture 内明列。Service 测试验证技术延迟不加无操作/动作计数、到期才复查、独立计数/同帧去重和 pending 回执绕过冷却。既有公共 Sway 与 Clan 定向回归保留，原件回放不冒充新 Native Start、业务收益或实机吞吐。

合回后的 **33 项定向测试在 6.97 秒内通过**：建设6、议会12、Service冷却3、家庭11，以及一个更新的旧建设断言；另有公共 Sway/Clan 四项回归通过。议会12项的 frame、request ID 和 Native包络是明确的合成夹具；原 AUTO600/605 plain error 不含完整 Native请求/结果 ID，不能以这些合成数据补作原件。两份事件来源 SHA 分别为 `dd1c593a9dc633f27943e7d3c35158e13214593cf876288125709d5ff78d928e` 与 `acd8eeda7caff507ccaad7416d42a48bcc2288722aee4ea56fb2667e9aa4d860`。

相邻历史 family/council/construction 检查首次为 70 PASS/12 FAIL。仅对失败 12 项用内存中的公共 `20c7319b6964c80fa419540cf4e30852feff4810` 源码复验，11 项在基线也失败，属于旧 fixture/资格不一致，未在本包改动或记为通过。唯一新增差异是已验证 applied 材料的不可观测读取由异常变为具名结果；对应旧用例已更新，继续断言零提交、禁止重放、原材料各字段原样保留，并单独通过。没有把全部历史单测记为 GREEN。

本包为 Python/JSON 逻辑，无新增 Paradox 文本，open_kaishek 不适用。统一存储策略 1.0.0 下外置源码/helpers 峰值额度为 8 MiB，复核时间 `2026-10-18T12:00:00Z`；保护理由为当前冻结 P20 与待交付来源，不无限续存。未复用录像预留、复制游戏或清理其他工作包。公共 commit/push、官方 CI 结果及未来实机消费由精确 SHA 的交付回执另记。
