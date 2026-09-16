# CK3 家徽编辑器真实 10,000 拟合预算压力证据

状态：`WP4 passed / real-fit-budget、reload-persistent checkpoint pause-resume、multi-stage cancel-restart passed`

日期：2026-09-16（Asia/Shanghai）

合同：`ck3-coa-real-fit-budget-stress-v1`

## 这项证据证明什么

测试把同一张确定性 96×96 四色高频图真正交给浏览器 Worker，分别以 128、1,024、10,000 为最大改善实例预算执行拟合。
这不是只测试输入框，也没有把小预算结果改名为 10,000 结果。另一个
[完整文档压力合同](coat-of-arms-large-document-stress.md)独立构造恰有 10,000 个实际实例，负责验证大模型的复制、保存和编辑。

预算不等于必须凑满的图层数：只有实际降低损失的实例才会被保留。当前原生 tile 搜索平面为 96×96，按预算和像素粒度共同决定
四叉树深度；10,000 预算原值进入算法，深度为 7、像素叶容量为 9,216。它没有被改写为 1,024 或其他产品上限，但仍可因无改善、
精确匹配或当前搜索分辨率而自然提前停止。上述信息现在进入每次结果的 `nativeTileSearch` receipt 并显示在页面中。

为避免大预算中的二次数组与 tie-key 增长，tile trial 现在只增量渲染候选；比较两个覆盖安全的 scale 后才把胜者追加到结果模型。
每个接受层仍按完整 scoring contract 重新评分，hunter 1024 回归保持通过。

## 预先冻结的门禁

门禁位于 [`fitBudgetContract.ts`](../coat_of_arms_editer_of_ck3/src/domain/fitBudgetContract.ts)，在浏览器压力执行前定义：

- 128 / 1,024 / 10,000 分别小于 15 / 45 / 180 秒。
- 绘制阶段取消响应小于 1,000 ms，取消后必须能立即启动并完成新 run。
- 安全 checkpoint 暂停响应小于 1,000 ms；恢复 128 预算结果小于 45 秒，且模型和指标须与不中断运行一致。
- 若 Chromium 暴露 `performance.memory`，JS heap 增量小于 384 MiB；此值不覆盖 GPU 和浏览器进程总内存。
- 每次结果必须保留用户预算原值、实际实例、候选数、停止原因和搜索空间 receipt。
- 最终复制须重新解析，并与结果的块数和实例数一致；不得读取可见 DOM 窗口。
- 全程不得产生非 GET 请求，用户像素不得外传。

## 浏览器实测

### 初始基线

环境：本机 Microsoft Edge headless、Vite 开发服务器、正式独立页面配置、合成静态 asset pack。随机种子为 `null`，输入由固定公式
`palette[(x + 3y) mod 4]` 生成；scoring contract 为 `alpha-weighted-srgb8-mse62-luma-gradient-l1-38-v1`，renderer contract 为
`cpu-rgba8-bilinear-clamp-pixel-center-v1`。

| 用户预算 | 实际实例 / 块 | 候选评估 | 四叉树深度 | 停止原因 | 耗时 |
| ---: | ---: | ---: | ---: | --- | ---: |
| 128 | 8 / 8 | 412 | 4 | `no_improvement` | 3,636 ms |
| 1,024 | 250 / 250 | 3,260 | 6 | `no_improvement` | 5,405 ms |
| 10,000 | 1,824 / 1,824 | 14,908 | 7 | `no_improvement` | 13,409 ms |

10,000 结果总损失 `0.19578464753140656`、边缘损失 `0.26330842040763747`；这是压力图的绝对数，不与 hunter 指标横向比较。
该结果完整复制后为 711,661 UTF-8 bytes / 25,543 行，重新解析得到 1,824 `colored_emblem` 块和 1,824 `instance`，与结果元数据一致。

`ck3-coa-fit-checkpoint-v1` 在最多约 100 个安全边界保存输入 SHA-256、asset-pack manifest SHA-256、算法/分辨率/预算、`randomSeed=null`、
完整当前模型、原生块列表和下一块游标。`ck3-coa-persisted-fit-checkpoint-v1` 再把这一搜索状态、已解码的浏览器内输入金字塔和所需
asset-pack 身份写入独立 IndexedDB 单槽；它不进入 Service Worker/静态资产缓存，也不产生网络请求。暂停终止当前 Worker，恢复使用
同一逻辑 run 的新 revision；旧 revision 的消息会被拒绝。未知版本、输入/素材哈希、预算或游标不一致均 fail closed。

实测暂停并完成持久写入延迟 82 ms；刷新页面、重新载入静态素材包并恢复 checkpoint 共 3,318 ms；随后恢复搜索至完成耗时
3,239 ms。恢复后的完整 `coatOfArms`、metrics、layer losses、seam receipt、实际实例、块数和停止原因，逐字段与不中断的 128 预算
运行一致。该结果证明同一浏览器 origin 的正常刷新恢复；浏览器清站点数据、无痕会话退出、磁盘配额拒绝或设备丢失不在其保证范围内。

绘制阶段取消延迟 57 ms；旧 Worker 被 run ID/revision 作废后，新的 1 预算 run 在 146 ms 内产生进度，没有旧结果污染。压力序列的
JavaScript heap 增量为 49,825,310 bytes；非 GET 请求为 0。高分辨率接缝 receipt 在三个预算下均为 96/230/512 px 零泄漏。

三个预算均由 `webgl2-texture-array-reduction-float-v1` 在 Worker 内批量排序 6 个背景候选，再由 CPU reference 全量复核；最大指标差
`2.5092759509126594e-8` 且完整排序一致。GPU 覆盖范围、GPU reduction 与 context-loss 降级证据见
[WebGL2 批量搜索证据](coat-of-arms-webgl-batch-search.md)。

DOM-less reference 同一 10,000 预算运行得到相同 1,824 实例、15,274 个候选、`no_improvement`、总/边缘损失完全一致，耗时
7,966.64 ms。候选数与浏览器不同是该快速 reference 使用 8 个 refinement shortlist 名额，而生产页面使用 48；最终模型和损失一致。

### 当前 renderer / Pareto 回归

2026-09-16 在 `cpu-rgba8-trilinear-dds-mip-pixel-center-native-clockwise-depth-descending-v4`、生产 build 和同一确定性输入下复跑：

| 用户预算 | 实际实例 / 块 | 候选评估 | 四叉树深度 | 停止原因 | 本机耗时 |
| ---: | ---: | ---: | ---: | --- | ---: |
| 128 | 128 / 128 | 1,798 | 4 | `layer_budget` | 4,929 ms |
| 1,024 | 250 / 250 | 3,206 | 6 | `no_improvement` | 5,661 ms |
| 10,000 | 2,320 / 2,320 | 205,654 | 7 | `no_improvement` | 101,289 ms |

10,000 结果为 905,361 UTF-8 bytes / 32,487 行，完整复制、重新解析均为 2,320 块 / 2,320 实例；暂停 34 ms、刷新恢复
3,231 ms、继续至完成 4,727 ms、取消 67 ms、新 run 首次进度 155 ms，JS heap 观测增量 8,037,940 bytes，非 GET 请求为 0。
当前本机三个预算仍分别低于 15 / 45 / 180 秒的冻结门禁。

GitHub Pages 的共享 Linux runner 属于 `report-only` 性能环境，同一轮观测约为 41.9 / 52.2 / 150.2 秒；前三次真实拟合已经消耗
约 244 秒，原 300 秒整份 Playwright 用例上限会在随后的 pause/resume 阶段关闭浏览器。`report-only` 整份用例上限因此调整为
600 秒。后续 hosted run 又证明其单次 128 预算约需 46 秒，恢复阶段会超过只适用于维护者工作站的 45 秒门禁；因此 hosted 环境
最多等待冻结的 180 秒观测上限以完成功能闭环，但不据此判定性能 GREEN。工作站的 300 秒总上限、三个单预算阈值和
45 秒恢复门禁全部保持不变；暂停、取消和新任务响应仍执行原有有界断言。这是把功能验收与参考设备性能验收分开，不是放宽产品门禁。

修改后本机生产 build 的 report-only 全流程在 2.2 分钟内通过：128 / 1,024 / 10,000 分别为
4,958 / 5,583 / 101,914 ms，刷新恢复 3,341 ms、继续至完成 4,805 ms、取消 71 ms、重启进度 184 ms，非 GET 请求为 0。

独立的 `ck3-coa-fit-multi-stage-cancel-v1` 又在背景匹配、全库轮廓粗筛、0.1° 级精筛和原生矩形块残差细化四个不同阶段
主动终止 Worker，本机延迟分别为 17.9 / 17.4 / 20.8 / 14.5 ms，均低于预先冻结的 1,000 ms 门禁。每次取消后
`data-fit-evidence` 为空；最后的新 run 能在 1,000 ms 内恢复进度并再次安全取消，证明 run ID/revision 隔离未留下旧结果。

## 复现命令

在 `coat_of_arms_editer_of_ck3/` 中执行：

```text
pnpm exec vitest run src/domain/fitBudgetContract.test.ts --reporter=verbose
pnpm exec vitest run src/domain/fitCheckpointStore.test.ts --reporter=verbose
pnpm exec playwright test e2e/fit-budget-stress.spec.ts --reporter=line
pnpm exec playwright test e2e/fit-cancel-stages.spec.ts --reporter=line
pnpm exec playwright test e2e/webgl-batch-scorer.spec.ts --reporter=line
pnpm exec playwright test e2e/reference-hunter-fit.spec.ts --reporter=line
pnpm test
pnpm build
```

本子门禁仍不等于 WP4 完成：GPU 搜索尚未覆盖语义/local 与逐块残差候选，同 run GPU context 重建、更多取消阶段及参考设备总进程/GPU
内存证据仍未完成。
