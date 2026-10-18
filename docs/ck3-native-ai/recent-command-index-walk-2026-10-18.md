# 最近命令查找避免预先物化整段历史

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-18T10:56:09Z 以 `tools/ck3_live_run_id.py machine` 核对机器；本次仅工作仓源码和小合成测试，不读取或统计 Driver、存档、媒体和索引。

[`strategy._latest_index` 与 `_latest_life_advance_index`](../../ck3_autonomous_player/src/xar_autoplayer/strategy.py) 的输入是调用者持有的命令列表。原先每次先执行 `tuple(enumerate(commands, start=1))`，再倒序查找；即使末行命中，也为全部 N 行创建枚举元组。现在从 `len(commands)` 倒数到 1，读取对应行，匹配成功即返回。查找顺序、成功状态过滤、包裹 AUTO 的有效动作以及显式／回退索引均保持原样。

这个改动不缓存历史、不截取窗口，也不更改策略或查询频率。稳定列表的额外空间从 O(N) 降至 O(1)；若最近匹配距末尾为 k 行，只读取这 k 行。调用者仍需在同一次规划内持有稳定输入；普通 Driver 的内部规划视图保留原历史锁。

23 项 focused 测试实际使用 `BELOW_NORMAL(0x4000)`，结果为 `23 passed in 6.68s`。测试覆盖空／无匹配、尾部／中部命中、失败动作过滤、显式与回退索引及既有类型行为、AUTO 包裹和不同时间推进步骤。带读取计数的列表在尾命中时只读取末行，并禁止预先正向遍历；输入内容保持原样。精确 UTC、来源 SHA 和命令见[证据](evidence/recent-command-index-walk-2026-10-18.json)。

这证明减少了 Python 历史物化和多余访问。实际战役墙钟、CPU 或视频编码性能没有在本轮测量；冻结运行树、原生守卫和当前编码源未修改。
