# 361 scripted effect 文件边界合同

状态：**强制执行 / canonical source 已迁移 / live validation pending**。

## 强制规则

- scripted effect 必须按用途分组拆分；不再把单文件体量作为待讨论或待触发的可选优化。
- 目标为每文件 `1–10` 个顶层 effect，原则硬上限为 `20`。
- 发现超过 `20` 的文件即判定 RED 并拆分。例外必须同时记录不可拆理由与该精确文件的 CK3 实机证据；当前例外数为 `0`。
- generator、静态测试、production projection 与 release 清单必须认识全部分片；旧聚合 owner 不得与新分片并存。
- 历史未拆分产品及 A/B artifact 只用于追溯旧运行，不得重新成为后续候选。

## 当前 canonical 布局

| 来源 | 文件数 | 每文件 effect 数 | 旧 owner |
|---|---:|---:|---|
| 361 mechanism | 186 | `1–8` | `zg361_generated_mechanism_effects.txt` 已退役 |
| B1 runtime | 12 | `3–10` | 两个 `zg361_b1_runtime_effects*.txt` 已退役 |
| Phase2 core | 4 | `3 / 6 / 8 / 9` | `zg361_effects.txt` 已退役 |
| 全部 ZhongGuo effect | 626 | 最大 `10` | `>20=0`、例外 `0` |

B1 十二个用途组的顶层 effect 数依次为：`8, 10, 9, 8, 7, 6, 8, 4, 6, 5, 3, 4`。
361 mechanism 按 ledger、相邻 policy 机制组和四个 dispatcher/helper 用途拆分；Phase2 core 按 review cycle、result delivery、appeal/scoreboard、elimination 拆分。

## 校验入口

```powershell
py mod_zhongguo_style/tools/gen_361_mechanisms.py --check
py mod_zhongguo_style/tools/gen_361_b1_runtime.py --check
py mod_zhongguo_style/tools/effect_file_boundaries.py
py mod_zhongguo_style/tools/validate_local.py
```

当前静态结果：`626 files / 3721 effects / target misses 0 / >20 violations 0 / maximum 10`。本布局仍需由下一次正式 CK3 product run 完成实机加载与业务回归；静态 GREEN 不冒充 live GREEN。
