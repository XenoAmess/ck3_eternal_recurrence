# 会合审查按需展开命令历史

`machine_id: xenoamess-full-tower-eb9d2c1186`，身份由 2026-10-18T10:56:09Z 的 `tools/ck3_live_run_id.py machine` 核对。本次仅仓库源码和既有小夹具，没有游戏、Native、媒体、索引、SAVE 或 Driver 操作。

[`review_safe_war_rendezvous_v1`](../../ck3_autonomous_player/src/xar_autoplayer/war_safe_rendezvous_v1.py) 先验证防御驻守、多军分驻、当前军力、合并能力与目标占领状态，然后才用历史。普通调用链现在传可选展开工厂，在原 `list(commands)` 位置调用；相关会合仍消费完整独立列表，直接列表 API 保留。不改变路线、全部友军 H1、接触、起点暴露及移动意图检查。

新 14 项实际 `BELOW_NORMAL` 测试为 `14 passed in 2.56s`：8 个不适用条件不展开，4 个完整查询阶段仍依次要求路线及两支友军 H1，陈旧预览／不安全等待方仍不选择移动。首轮同生产源的既有会合与预测 23 项、14 子用例已通过；一个新测试误从 strategy 导入合并常量，修正至 war_contract 后重新验证新模块，生产代码未因该错误变化。[证据](evidence/rendezvous-history-expansion-on-demand-2026-10-18.json)保留两次结果。

普通非移动调用边界现仅剩起点暴露审查的一次原有展开。减少的是未使用的 Python 物化；没有实机墙钟或 CPU 收益测量，冻结运行与编码源未改变。
