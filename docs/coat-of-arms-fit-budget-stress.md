# CK3 家徽编辑器真实 10,000 拟合预算压力证据

状态：`WP4 in_progress / real-fit-budget、tab-session checkpoint pause-resume、cancel-restart sub-gates passed`

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

环境：本机 Microsoft Edge headless、Vite 开发服务器、正式独立页面配置、合成静态 asset pack。随机种子为 `null`，输入由固定公式
`palette[(x + 3y) mod 4]` 生成；scoring contract 为 `alpha-weighted-srgb8-mse62-luma-gradient-l1-38-v1`，renderer contract 为
`cpu-rgba8-bilinear-clamp-pixel-center-v1`。

| 用户预算 | 实际实例 / 块 | 候选评估 | 四叉树深度 | 停止原因 | 耗时 |
| ---: | ---: | ---: | ---: | --- | ---: |
| 128 | 8 / 8 | 412 | 4 | `no_improvement` | 3,464 ms |
| 1,024 | 250 / 250 | 3,260 | 6 | `no_improvement` | 5,307 ms |
| 10,000 | 1,824 / 1,824 | 14,908 | 7 | `no_improvement` | 13,223 ms |

10,000 结果总损失 `0.19578464753140656`、边缘损失 `0.26330842040763747`；这是压力图的绝对数，不与 hunter 指标横向比较。
该结果完整复制后为 711,661 UTF-8 bytes / 25,543 行，重新解析得到 1,824 `colored_emblem` 块和 1,824 `instance`，与结果元数据一致。

`ck3-coa-fit-checkpoint-v1` 在最多约 100 个安全边界保存输入 SHA-256、asset-pack manifest SHA-256、算法/分辨率/预算、`randomSeed=null`、
完整当前模型、原生块列表和下一块游标。暂停终止当前 Worker，恢复使用同一逻辑 run 的新 revision；旧 revision 的消息会被拒绝。
实测暂停延迟 80 ms，恢复完成耗时 3,164 ms；恢复后的指标、实际实例、块数和停止原因与不中断的 128 预算运行一致。单元门禁进一步
逐字段比较完整 `coatOfArms`、metrics、layer losses 与 seam receipt，并证明输入 SHA 不匹配时 fail closed。

该 checkpoint 当前只保存在打开的浏览器标签页；刷新、浏览器崩溃或关闭标签页后的 IndexedDB 持久恢复尚未实现，因此这里只把
“同标签页精确暂停/恢复”标为通过，不把 WP4 checkpoint 总项标为完成。

绘制阶段取消延迟 60 ms；旧 Worker 被 run ID/revision 作废后，新的 1 预算 run 在 173 ms 内产生进度，没有旧结果污染。压力序列的
JavaScript heap 增量为 37,436,014 bytes；非 GET 请求为 0。高分辨率接缝 receipt 在三个预算下均为 96/230/512 px 零泄漏。

DOM-less reference 同一 10,000 预算运行得到相同 1,824 实例、15,274 个候选、`no_improvement`、总/边缘损失完全一致，耗时
7,966.64 ms。候选数与浏览器不同是该快速 reference 使用 8 个 refinement shortlist 名额，而生产页面使用 48；最终模型和损失一致。

## 复现命令

在 `coat_of_arms_editer_of_ck3/` 中执行：

```text
pnpm exec vitest run src/domain/fitBudgetContract.test.ts --reporter=verbose
pnpm exec playwright test e2e/fit-budget-stress.spec.ts --reporter=line
pnpm exec playwright test e2e/reference-hunter-fit.spec.ts --reporter=line
pnpm test
pnpm build
```

本子门禁仍不等于 WP4 完成：checkpoint 的 IndexedDB 持久恢复、WebGL2 上下文丢失恢复、GPU 真正承担批量候选搜索、更多取消阶段及
参考设备总进程/GPU 内存证据仍未完成。
