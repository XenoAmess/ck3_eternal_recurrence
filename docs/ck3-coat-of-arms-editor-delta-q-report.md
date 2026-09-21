# CK3 家徽编辑器 Delta-Q 拟合质量 2.0 实施报告

> 报告日期：2026-09-21
>
> 状态：`passed`
>
> 计划：[Delta-Q / 拟合质量 2.0](ck3-coat-of-arms-editor-delta-q-plan.md)

## 1. 冻结决策

项目后续优化按以下不可颠倒的顺序选优：

1. 质量、效果和与输入图的相似度；
2. 只有视觉质量相同时，才偏好更少的 CK3 绘制实例、更小的源码和更低的游戏内渲染压力；
3. 网页拟合耗时只作诊断，分钟级可接受，不能用旧性能目标否决更好的图像。

实例预算仍是硬上限。质量优先不等于可以越过用户选择的 128 / 1,024 层上限，也不等于可以省略完整 DDS 与 CK3 原生验证。

## 2. 已实施的质量路径

- 新增冻结的感知 v2：线性光颜色、多尺度颜色布局、梯度、双向边缘距离和结构诊断；最终选择在完整 DDS 重绘上使用 v2，而不是用低分辨率代理分数冒充最终效果。
- 原生素材检索升级为旋转/镜像稀疏网格粗筛与 18×18 网格、有符号距离场精排；64 例 holdout 的 Top-8 / Top-32 recall 为 93.75% / 96.875%。
- 搜索从单一路径扩成原生素材、组件感知、legacy 安全通道、hybrid native-paint 与残差修复的有界候选前沿。
- 最终器对全部合格的 hybrid/high-resolution 候选执行精确 DDS 残差修复，同时尝试 sRGB 与线性光颜色；代理分数只负责 shortlist，接受与排序使用完整感知 v2。
- 首选顺序改为“感知 v2 绝对优先 → v2 精确相等时实例数 → 源码大小与 legacy 指标”；不再给较快或较小但更差的结果留隐式容差。
- 结构压缩只合并完全相邻且样式一致的 block，并记录 `exactStructureOnly=true` 收据；没有执行会改变像素或实例序列的质量换体积删除。
- checkpoint 升级到 v4，继续保证取消、暂停、恢复、重启和 revision 隔离；生产流程保留纯前端、无 CK3/后端依赖边界。

## 3. 正式质量结果

1,024 实例预算、七张真实用户图片、96 px 冻结感知 v2 口径：

| 图片 | v14 loss | Delta-Q loss | 相对改善 | 实例数 |
| --- | ---: | ---: | ---: | ---: |
| 01 | 0.027693 | 0.026567 | +4.067% | 739 |
| 02 | 0.042068 | 0.029923 | +28.869% | 729 |
| 03 | 0.020472 | 0.020466 | +0.032% | 1,024 |
| 04 | 0.041029 | 0.032058 | +21.865% | 971 |
| 05 | 0.033298 | 0.025490 | +23.449% | 922 |
| 06 | 0.006761 | 0.006410 | +5.193% | 1,024 |
| 07 | 0.040000 | 0.033069 | +17.327% | 1,024 |

- 中位改善 +17.327%，超过 +15% 门限。
- 最差改善 +0.032%，7 / 7 均为正提升，也高于 -2% 单图门限。
- 1,024 实例硬上限 7 / 7 满足；128 实例回归 7 / 7 完成，最大实例数 128。
- 96 / 230 / 512 px 完整 DDS 最差相对变化分别为 +0.032% / -0.222% / -0.182%，均在 -2% 门限内。
- 七图 1,024 预算总耗时约 36.94 分钟，128 预算约 11.88 分钟；按冻结优先级均为诊断数据，不构成质量失败。

权威机器证据：

- [1,024 预算质量汇总](coat-of-arms-fit-artifacts/delta-q-residual-repair-v1/real-budget-1024-v9-final-quality-first/quality-summary.json)
- [128 预算回归汇总](coat-of-arms-fit-artifacts/delta-q-residual-repair-v1/real-budget-128-v9-final-quality-first/regression-summary.json)
- [96/230/512 完整 DDS 复评](coat-of-arms-fit-artifacts/delta-q-final-multires-v1/README.md)
- [匿名 A/B contact sheet](coat-of-arms-fit-artifacts/delta-q-ab-contact-sheet-v1/README.md)

A/B contact sheet 当前明确标记 `pending-human-review`；自动测试没有伪造人工偏好或人工签核。

## 4. CK3 原生结果

当前 Delta-Q v9 首选：

- 浏览器→CK3 原生像素 7 / 7 通过；Copy→再 Apply 7 / 7 通过。
- 实例数、逻辑层数和 block 数 7 / 7 保持。
- 首次严格文本语义 2 / 7 逐值相等；其余仅为 CK3 对小数旋转值的正规化。正规化后的 Copy→再 Apply 为 7 / 7 严格稳定。
- 首次 Apply 最坏 MAE / MSE / edge / spatial 为 0.037478 / 0.007890 / 0.132058 / 0.116166，全部通过冻结门限。
- Copy→再 Apply 最坏 MAE / MSE / edge / spatial 为 0.0000700 / 0.000000275 / 0.000365 / 0.000289，全部通过更严格门限。
- Steam 离线、无 OCR/键鼠/固定坐标，cleanup、进程树消失与锁释放均有证据。

详见 [Delta-Q v9 原生验收 r19](coat-of-arms-fit-artifacts/delta-q-native-r19/README.md)。历史 v15 基线也已补为 [7/7 视觉与 Copy 稳定](coat-of-arms-fit-artifacts/user-picture-corpus-v15-native-r20/README.md)，因此 Q0 不再残留 native-pending。

## 5. 工程门禁

本地正式 Pages 门禁已经完成：

- 原始与 production build 后素材包均为 1,630 文件逐文件校验通过；
- Vitest 23 文件、102 tests 通过；
- production build、production-boundary、i18n、无 CK3/无后端 E2E 通过；
- benchmark、WebGL/CPU fail-closed、感知校准、检索、结构、128/1,024 真实集与三分辨率最终候选通过；
- Chromium / Firefox / WebKit 通过，离线 Service Worker 通过；
- 取消、暂停、恢复、context-loss、持久 checkpoint 与 128/1,024/10,000 压力场景通过。

CI workflow 已把 `perceptual-final-candidates.spec.ts` 加入正式 Pages 发布门禁。实现与门禁修复已线性进入 `master`，正式 Pages build/deploy 与 canonical URL 回读均已完成。

发布门禁的失败尝试追加保留：run `35613417757` 暴露 Windows CRLF 原始源码哈希在 Linux checkout 上的可移植性假 RED；run `35615542419` 随后暴露 report-only GitHub runner 的 1 层取消后重启仍误用了工作站 128 层 15 秒性能门限。两者都没有降低图像质量、结构、预算、取消或最终完成条件：前者改为验证 LF canonical 与可逆 CRLF 原始哈希，后者在 `COA_E2E_PERFORMANCE_GATE=report-only` 时沿用既有 420 秒诊断上限，而工作站严格门限保持不变。

### 5.1 Release closure

- 实现 release commit 为 `d5c6b4ef3c399acbdc8c358fdfb1458cfb652cf9`；质量实现、跨平台证据修复和 report-only runner 门限修复均已推送到 `master`。
- 正式 [GitHub Pages workflow run 35616837513](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/35616837513) 的 build 与 deploy jobs 均为 GREEN，deploy 于 2026-09-21 15:41:02 UTC 完成。
- canonical URL 回读为 HTTP 200，页面显示 `版本 2026-09-21T15:35:41.445Z · d5c6b4ef`，与该 release commit 一致；线上页面同时成功载入 `ck3-1.19.0.6-base-complete-42p-1578e-8aux` 素材包。
- 无后端浏览器回读共观察到 10 个请求：全部为 `https://xenoamess.github.io` 同源 GET；非 GET、跨源、失败请求，以及 API、localhost、CK3、MCP、Quarkus/Java 可执行依赖均为 0。
- 因此 Q0–Q5、正式部署与公开回读均已收口；匿名 A/B 仍保持 `pending-human-review`，不伪造人工签核，也不阻断已冻结的自动质量门禁。

## 6. 已知边界

- legacy total/edge 在 7 张图中各有 4 张不退化；它们作为公开诊断与安全候选保留，但不会否决感知 v2 明显更优的首选。这是已冻结的质量优先政策，不是隐藏回归。
- 230/512 px 不是自动选优主口径；它们证明没有跨尺度崩坏。未来若把选择器改成多分辨率联合目标，必须新建 benchmark revision，不能事后改写本期数据。
- CK3 会正规化部分小数旋转源码，所以“首次 Copy 文本逐值相等”不能等同于“原生渲染相同”；报告同时保留该 RED 与 7/7 像素、结构和二次稳定证据。
- 人工 A/B 仍需真人查看；这不是继续开发或发布纯前端工具的自动门禁，也不会被工具代签。
