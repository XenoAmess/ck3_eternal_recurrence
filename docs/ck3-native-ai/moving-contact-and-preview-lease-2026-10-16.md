# 单军移动接敌观察与路线预览同帧绑定

2026-10-16，当前罗贝尔战役的公共源码收口。此包只改普通战争策略和定向测试，不修改 Native、游戏、录制或战斗力量门槛。公共源码和正在运行的 SDK 是不同版本；实机后续效果须以继续运行的新回执判断。

P07 AUTO20 在防御围城解围时得到完整的路线接触查询，但战力名单包含另一个友军，无法证明单场战斗的完整参战分组。策略现在拒绝直接进战；仅在已有完整敌军路线和第一跳接触证明可用时，复用原先的一跳只读预览／有限侦察分支，随后逐日重读。原始回执为 [P07 AUTO20](D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p07-responses/0020-1-result.json)，SHA-256 `92d83919f0ba8afe4c23bc4f7e2cdef1cbb8d23a5a378b46a00efab6659b5d99`。这不是战斗授权或胜利证明。

P08 AUTO18 在同一游戏日跨 SDK 续接时，历史预览仍带旧 `native_revision=143`／连接代际 7；新帧已是 144／代际 8。旧策略按日期复用预览，继而找不到新帧资格的第一跳动作。现全部九个 `_fresh_move_route_preview` 调用点均传当前 snapshot；读取结果必须同时匹配 snapshot ID、public/native revision、连接代际和 episode，旧帧只会重新走可用的只读路线预览。原始回执为 [P08 AUTO18](D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p08-responses/0018-1-result.json)，SHA-256 `26f1fd2c25f6c3e514f61740048677a20cb4e52d60e50f9f6bd7c121b1803896`。没有重放 AUTO18。

同一防御分支的两处“本日已查询”去重也核当前成功结果的完整帧租约，否则它会在旧成功结果失效后错误抑制新只读查询。失败行继续沿用原先的本日防循环守卫；没有失败回执的精确帧身份时不推测可以重试。

仅对单支已承诺移动的己军、完整敌军 ID 集合、暂停地图、无当前战斗、无主要防御围城和无突击的严格子集，策略先用现有全敌军一日接触时间线查询。只有同帧证明 `one_day_contact_free=true` 才选择受限单日推进；预测接敌、查询失败或证明缺失仍回到完整军力查询，不据此批准攻击。性能收益尚未由自然移动回合量化。

外置运行候选 [P09 一叶](D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/siege-preview-lease-candidate02/strategy.py) SHA-256 `fe09d85c047529b7b6d5f6ed19f9d37cd36607750173c8acc416c0450fbe186c`，基于 P08 当前 SDK；公共树按各处函数逐段移植，没有覆盖整叶或带入其他运行时差异。聚焦验证命令：

```text
PYTHONPATH="src;.." py -3 -m pytest -q tests/unit/test_wartime_moving_contact_preview_lease.py tests/unit/test_general_battle_strategy.py tests/unit/test_combat_provisional_defense_canary.py
```

包含两处去重补丁的最终结果为 35 passed。旧 canary 的合成路线预览补上其已有帧的完整租约；真实 R0284 旧帧预期改为重新查询路线，而非沿用旧预览查询接触。另有旧 `test_route_contact_horizon_contract.py` 中 ID 0 parser 失败，所涉 `war_contract.py` 未由本包修改，未计入本包 GREEN。公共源码通过不代表 P09 实际第一跳或三十年任务完成。

外置候选属可重建派生物，按通用策略 48 小时复核；两个原始回执由当前战役 owner 在其活动工作包保护期限内保留。公共小型文档和测试由 Git 正常维护，本包没有制造大文件或回收现场资产。
