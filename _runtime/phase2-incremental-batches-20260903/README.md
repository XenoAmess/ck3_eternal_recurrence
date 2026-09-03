# 天朝二期增量启动验证计划（2026-09-03）

这是给 CK3 独占启动代理使用的离线批次清单。它不修改 canonical source，也不把任何一次启动超时误报成“功能完成”。完整数据见同目录 `manifest.json`。

## 基准关系

`none` 是 8 月 30 日已经 GREEN 的实际 51-file mounted product projection（7,137,587 bytes，tree SHA `ddac4703...aa14a693`）。它对应天朝一期/二期早期可启动 core，不是当前 279-file 全量树的简化猜测。

当前全量 product projection 是 279 files / 29,351,046 bytes（tree SHA `eafb3261...28015574`）。新增部分来自 2bfd10b 集成后的 workforce、Phase3、career、feedback、credit 等功能簇；因此必须按簇追加，不能一次把所有 runtime 混入启动实验。

## 批次顺序

| 顺序 | 批次 | 新增或替换 | 累计文件/字节 | 主要依赖 |
| ---: | --- | ---: | ---: | --- |
| 0 | `none` | old core 51 files | 51 / 7.14 MB | 无 |
| 1 | `core-current` | 18 个非 scoreboard 基线文件替换 | 51 / 7.16 MB | none |
| 2 | `scoreboard-current` | scoreboard 三文件替换，+6.57 MB | 51 / 13.74 MB | core |
| 3 | `central-case-kernel` | 14 files / +338 KB | 65 / 14.08 MB | core |
| 4 | `b1-b2` | 22 files / +909 KB | 87 / 14.99 MB | central/case |
| 5 | `incident` | 12 files / +784 KB | 99 / 15.77 MB | central/case、B1/B2 |
| 6 | `manager` | 13 files / +468 KB | 112 / 16.24 MB | central/case、B1/B2 |
| 7 | `workforce` | 101 files / +5.77 MB | 213 / 22.01 MB | central/case、B1/B2、manager |
| 8 | `phase3` | 11 files / +2.06 MB | 224 / 24.07 MB | workforce |
| 9 | `career` | 22 files / +1.62 MB | 246 / 25.69 MB | workforce、Phase3 |
| 10 | `feedback` | 11 files / +1.51 MB | 257 / 27.20 MB | workforce、career |
| 11 | `credit` | 11 files / +1.48 MB | 268 / 28.68 MB | workforce、feedback |
| 12 | `compensation` | 11 files / +673 KB | 279 / 29.35 MB | credit、feedback |

这里的“依赖”是静态文件命名和现有 runtime 关系推断，不能替代实机证明。每个批次应以同一 Steam EXE、同一完整 settings/warm shadercache、同一桥接来源和新 userdir 启动；只有 CK3 独占代理执行启动。

## 首失败后的二分

1. 先跑 `none`，确认旧 core 仍然是 `Frontend + clean exit`；这一步已经有约 52 秒 GREEN 证据。
2. 按表格逐项追加。某累计批次 RED 时，保留 RED 报告，再在 old 51-file base 上只加入该批次，区分“本批次自身”与前序交互。
3. 若单簇仍 RED，把该簇按文件体积从大到小二分，优先 workforce（最大单体为 `zg361_workforce_endgame_runtime_effects.txt`，约 4.64 MB/74k 行）。
4. 只要窗口到了 Frontend 但 `error.log` 有 parser/runtime 错误，标记为“startup GREEN / parser closure RED”，不能当作正式功能交付。

已准备的 disposable 参考目录：

- `Z:\ck3_mod_rewrite\_runtime\phase2-group-bisect-20260903\`
- `Z:\ck3_mod_rewrite\_runtime\phase2-scoreboard-bisect-20260903\`

这些目录仅用于实验，禁止直接上传 Workshop 或覆盖仓库源树。
