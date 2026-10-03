# R0006：技能事务实机 RED

本轮明确判定为 **产品 RED，不可发布**。真正存档中的基础属性显示：预检扣除了捐赠者属性，却没有给接收者属性，也没有恢复扣点。日志中的部分 PASS 不能推翻基础数组证据。

完整 run ID 为 `desktop-3fevhd2-1c74096080--superman-qiang--R0006`，execution ID 为 `ab4b312c-81c6-424b-99f4-2c337063f00a`。实际 CK3 PID 为 **17852**，玩家角色为 **31254**。永久证据根目录为 `D:/ck3-experience-drain-feasibility-20261004/desktop-3fevhd2-1c74096080--superman-qiang--R0006/`；profile、输入快照、MCP 请求及回复、日志、存档及解码文本继续保留。

## 输入与实机身份

运行 Steam CK3 **1.20.0.3**，build **25652598**，路径 `C:/SteamLibrary/steamapps/common/Crusader Kings III`。游戏 EXE SHA-256 为 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。产品输入是 `live-production-a01` 的 21 文件 staging，来源提交 `ebeb394634cc2a1e1ebd013b56c3e6952f4ce88e`；另加载外置 `fixture-a05`。本轮未包含后来加入的 `force_character_skill_recalculation` 生产修复。

Python 为 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` **3.14.7**，MCP **2.0.0**。本机 stdio MCP/native SDK 来源为 clean detached `D:/sxad-freeze-20261004`，提交 `f643b32e6146dce73f77fedfefd8471da59fb04f`。1027 个 SDK Python 文件 SHA 清单在 `sdk-python-input-hashes.json`。DLL SHA-256 为 `ad3bbb4e7bc19f2737bba10c468d26cabcae4058c6c2ae4f3b8675e95c5b8518`；编译来源仍按原编译记录标注，不用产品后续提交冒充 DLL 编译来源。`preparation.json` SHA-256 为 `0b872061dec749d41f0951795a20fd6d658a43dbb11e7f92e476da2c2d6fa319`，包含实际 runner、DLL、injector、产品与夹具输入。

Steam 全程离线。启动前直接审阅 `offline-a10/probe-1/steam-moved.png`，桌面为 **1024×768**，显示时间 4:20、日期 2026/10/4 与“离线模式”；SHA-256 为 `92ea8fb0787412034a9e9f7427a8b67c1b15a46431ed5399cc5ea215da725f13`。恢复回执完成于 `2026-10-03T20:21:00.694877+00:00`，随后立即启动。screen lease 使用独立 custody checkout `D:/ar`，它不是产品输入来源。

## 实际执行与独立存档读回

原生 MCP 完成普通 Robert 开局，夹具通过原版 `on_game_start_after_lobby` 找到玩家并排程。04:22:27 出现 `ON_START` 和 `SCHEDULED`；04:22:44 执行首批事件。28 项中，日志 **17 PASS、8 FAIL、3 未执行**。这只是日志汇总，不是最终通过数。

原生 `ck3_save_checkpoint` 保存了真实运行后态，存档日期为 **53145504**。`save-readback-a01/checkpoint.ck3` 为 **69,952,343** 字节，SHA-256 为 `444b8fb753694981619daaa9a2368da6eabba6f767e523c74a09d41bea141cd3`。Rakaly **0.8.19** 的 EXE SHA-256 为 `e154af990aaed2c2f44284946772188c9749ad3f6b641b41f6c23456a6f1633d`。真实 melt 结果 `save-readback-a01/melted.ck3` SHA-256 为 `8558f1aff1aa2f85b3130b21064c940284a6aaa325ba7ef6bfd4c7561f290ae5`；独立提取结果 `fixture-readback.json` SHA-256 为 `32ac37f0f8f3f99e42362cf23fdd2aa227a69124bf57de85e7dcd1e90d6d496f`。

以下数组直接读取存档 `skill` 字段，顺序固定为外交、军事、管理、谋略、学识、勇武。各角色由夹具 flag 定位，没有用日志总和替代数组。

| 生产 helper | 接收者 ID 与最终基础数组 | 捐赠者 ID 与最终基础数组 | 结论 |
| --- | --- | --- | --- |
| 外交 | 65850：`[10,10,10,10,10,10]` | 65851：`[9,10,10,10,10,10]` | 扣 1 未回滚 |
| 军事 | 65853：`[10,10,10,10,10,10]` | 65854：`[10,9,10,10,10,10]` | 扣 1 未回滚 |
| 管理 | 65856：`[10,10,10,10,10,10]` | 65857：`[10,10,9,10,10,10]` | 扣 1 未回滚 |
| 谋略 | 65859：`[10,10,10,10,10,10]` | 65860：`[10,10,10,9,10,10]` | 扣 1 未回滚 |
| 学识 | 65862：`[10,10,10,10,10,10]` | 65863：`[10,10,10,10,9,10]` | 扣 1 未回滚 |
| 勇武 | 65865：`[10,10,10,10,10,10]` | 65866：`[10,10,10,10,10,9]` | 扣 1 未回滚 |
| 随机吸取，原经验 1000/3 | 65871：`[10,10,10,10,10,10]`，经验 1001 | 65872：`[9,9,9,9,9,9]`，经验 4 | 六项预检各丢 1 |
| 反向赢家，原经验 2/20 | 65874：`[9,9,9,9,9,9]`，经验 3 | 65875：`[10,10,10,10,10,10]`，经验 21 | 六项预检各丢 1 |

六项初始基础属性均为 10。持久化 `sxat_before_*` 总属性为 `[10,10,11,10,10,12]`，包含文化等修正，读回并非空值。原生 `add_*_skill` 修改基础值后，总属性 trigger 缓存没有即时更新。旧生产分支把“总属性未变化”当成 native no-op，因而漏掉恢复。

负修正接收者 case 同样出现接收者基础 10、捐赠者外交基础 9 的漏点。上限探针接收者基础外交为 **100**，捐赠者基础外交却为 **9**；此项日志 PASS 不作为成功转移或安全 no-op 证据。

## 计数局部结果

原版已知双方 hook、匿名 hook、AI/AI、同人拒绝、17 岁拒绝、零经验与非零经验平局、99/100/101、百万及安全极限各项的持久变量均与相应已执行断言一致。这些局部结果不豁免技能事务 RED。

百万角色 **65904** 的经验为 **1,000,001**。99、100、101 初始值分别读回 100、101、102。极限减一角色 **65916** 与极限角色 **65919** 均准确读回 **92,233,720,368,547**，存档 fixed5 `identity` 为 **9,223,372,036,854,700,000**；通过整数解析验证，没有用浮点数证明极限。匿名 case 只递增调用者。

## 夹具缺陷与后续门禁

四层 prepare/capture/action/verify 连续触发达到引擎递归上限，在 `sxat.200` 被跳过。因此 `same-day-two-pairs`、`no-sex-memory-still-counts`、`dead-partner-rejected` 是 **未执行**。下一版每 8 项完整 case 在边界排程 `days=1`，同日两次行为仍在同一个动作事件内。

夹具在创建角色、添加 trait/modifier 或改基础属性后，没有刷新总属性缓存再捕获 baseline。因此基础 0 加正修正、负修正、上限 case 的总值基线可能陈旧；独立基础数组仍证明上述漏点，三个条件性 PASS 不证明边界正确。下一版在 setup 后、baseline 读取前刷新角色；生产修复必须另外在每次 probe、restore、commit 改点后刷新，不能由夹具刷新替代。

实际 UI 查看、trait hover、存档重载与无夹具正式玩法截图尚未完成。测试玩家人工经验不能用于 Workshop 首发 media。重测必须使用新 run ID、新 profile、新输入冻结，保留本报告与原始证据。
