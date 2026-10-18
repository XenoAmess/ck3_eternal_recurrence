# 围城完整ID零值的只读解析

`machine_id: 4-8e1c2f1861`；整理时间 `2026-10-18T16:58:46.921141+00:00`；来源CK3 1.20.0.4、源码提交 `c1f73ad6a5f215e45d9284afdd5e27928048cd8f`。R20的原生占领查询306行中，第161行是已由对象池、完整ID、类型标记和省份反向关联验证的 `siege_id=0`。旧Python解析器要求正数，导致整包拒绝。R22保留了当时同类解析RED；本修复不能追认其host成功。

`war_contract._normalize_active_siege` 现在仅对观察到的SiegeID接受严格整数 `0..2**31-1`。空值、布尔、负一、FFFFFFFF和越界仍被拒绝；缺失围城仍由原生absence语义表达。其它ID命名空间、攻击命令和原有正数门槛未扩大，因此不能据此声称围城ID零的突击动作已支持。

原始包：`C:/workspace/ck3-faith-and-power-20261017/episode01/live/4-8e1c2f1861--faith-and-power--R0020/d2-war8-original-native-occupation-wire-record-a01.jsonl`，160633B，SHA-256 `626c2df96fa4fcf1a174bf65d3ad24389a057e8aa10d6d82489de1e63f17a196`；原字段 `/message/result/war_occupation_targets_v1/rows/161/active_siege`。冻结候选的单项真实行回归与全306行包回放均通过，未调用游戏。资格原件 `revision-v5-20261018/mcp/zero-siege-id-a01/qualification.json`，3449B，SHA-256 `56f6a91e1ce4cefd74b4b774d53327594d3b185c7ea8cb99b7f2b6223b59314c`；源码链和此前runner失败亦保留。

规划者应按对象命名空间、完整ID及缺失哨兵分别定义有效性，不能用一个全局“ID必须正数”规则替代原版语义。本次只授予离线解析资格；新的SDK/MCP实机全量查询须在后续实际运行中独立验证。

主树已集成此修复及[真实行回归](../../ck3_autonomous_player/tests/unit/test_zero_siege_id.py)。`2026-10-18T16:57:39.613570Z`使用正常主模块导入实际运行一项检查，失败0／错误0；回执为本工作包 `revision-v5-20261018/root/ZERO-SIEGE-MAIN-INTEGRATION-a01.json`。它确认实际主树的解析行为，不是新的游戏调用、全包回放或对R22原失败的追认。
