# CK3 家徽编辑器 Epsilon-Q 实施与验收报告

> 日期：2026-09-22（Asia/Shanghai）
>
> 实施提交：`b7be2a43`、`ee35f6f2`、`c41f6bcc`、`f7542362`、`24faf354`、`0f57dd31`
>
> 质量优先级：相似度/效果 > 同质量下的输出与游戏压力 > 网页生成耗时

## 结论

Epsilon-Q 的产品实现和浏览器验收已完成。它不会为了更短输出或更快计算接受更差画面；在 1,024 档七张历史真实图上，所有首选均相对 Delta-Q v9 改善且 96/230/512px 无退化。在独立程序化留出上，16/16 改善，中位改善 21.696%。

预注册的进取目标没有全部达到：真实七图 1,024 档中位改善为 0.291%，低于 10%；128 档为 4.710%，低于 5%；picture-03/06 均未达到 5%。这些是正式未达项，门槛未移动。

## 已实施能力

- 冻结 `96 / 230 / 512px` 感知 v2 三尺度目标，权重为 `0.20 / 0.45 / 0.35`，同时公开逐尺度损失。
- 修正触边背景分量的闭合区域计数，并保留旧 v2 对照，避免把指标修正当作拟合收益。
- 将完整 DDS 候选提前进入复评，保留历史 Delta 首选作为不可退化安全基线。
- 新增固定实例构图的颜色、位置、尺度与旋转联合精调，以及方向化轮廓 proposal；满预算时仍可在不增加实例数的前提下改进现有构图。
- 将 finalizer 移入 Worker，扩展 checkpoint 到 Epsilon-Q v9，持久化优化游标、候选和确定性状态；暂停、恢复、取消和刷新后恢复均有浏览器门禁。
- 对 512+ 质量档启用 Delta compatibility lane。只有三尺度不退化的 Epsilon 候选可以替换历史结果；否则保留 Delta。
- 对纯 block 输入跳过冗余 Delta replay；这只减少重复计算，不改变候选质量判定。

## 正式质量结果

联合目标为：

```text
J = 0.20 * L_v2_96 + 0.45 * L_v2_230 + 0.35 * L_v2_512
```

| 证据集 | 预算 | 改善案例 | 中位相对改善 | 三尺度不退化 | 预注册目标 |
| --- | ---: | ---: | ---: | --- | --- |
| 七张历史真实图 | 1,024 | 7/7 | 0.291% | 7/7 | 中位 10%：未达；至少 5/7 改善：通过 |
| 七张历史真实图 | 128 | 7/7 | 4.710% | 7/7 | 中位 5%：未达；预算：通过 |
| 封存程序化留出 | 16 instances | 16/16 | 21.696% | 16/16 | 中位 5%：通过 |

1,024 档单图相对改善依次为 0.034%、5.737%、0.017%、0.291%、3.308%、0.010%、5.524%。这说明安全选择器有效，但真实图剩余误差主要受表示能力和满预算重分配限制；合成留出的强收益不能外推为真实图片泛化。

留出集按类中位改善：平涂轮廓 16.593%、细节 18.917%、颜色重叠 30.098%、纹理渐变 30.310%。输入是独立程序化家族和原生形状代理，不含外部真实图片。

## 输出大小与游戏压力

1,024 档最终实例数为 `740 / 771 / 1024 / 972 / 920 / 1024 / 978`，合计 6,429；Delta-Q v9 为 `739 / 729 / 1024 / 971 / 922 / 1024 / 1024`，合计 6,433。质量优先选择后总量减少 4，但 picture-02 增加 42 个实例，因此不能宣称普遍降低 CK3 渲染压力。

Epsilon-Q 七图源码合计 2,501,197 UTF-8 bytes。源码字节、block 数与实际绘制实例继续分开报告；没有以牺牲质量换取压缩。本期没有足够显著且配对的 CK3 帧耗时收益，因此不发布性能百分比结论。

## 浏览器与构建门禁

- Vitest：121 passed，1 skipped。
- 静态 DDS pack：1,630/1,630 逐文件验证通过。
- 正式 1,024 七图：总拟合 87.45 分钟，7/7 parse/serialize、预览投影和预算门禁通过。
- 封存留出：总计 3,957.40 秒，逐案例 checkpoint/resume 契约通过。
- 预算压力：128、1,024、10,000 三档通过；10,000 档 2,312 instances、1,010 blocks、674,171 bytes；暂停、持久恢复、继续、取消和重启进度均通过，未观察到非 GET 请求或堆增长。
- 正式站点边界：15/15；standalone 2/2；Chromium/Firefox/WebKit 3/3；Service Worker 安装与离线 1/1；production build 与构建后 pack 复验通过。
- 纯前端边界保持：无 CK3、Java、MCP 或后端运行依赖，素材仍按需从同源静态 pack 获取。

## CK3 原生证据边界

Delta-Q r19 已证明既有 renderer/serializer 路径的 Browser→CK3 与 Copy→re-Apply 像素门禁均为 7/7 GREEN。Epsilon-Q 没有增加 CK3 语法类型，只改变浏览器生成的候选；但这份历史证据不能替代新候选的逐份原生 Apply。

本期新建了隔离的精确 CK3 `1.19.0.6` 原生会话并预登记七个 Epsilon 文档。bridge SHA、游戏 SHA 和传输连接均匹配，但 ApplicationMain mailbox 在 1,800 秒内始终 `ready=false`、`executed_requests=0`，所以七个候选没有开始 Apply。runner 以 RED 退出，并证明 CK3 PID、watchdog 和控制文件全部清理。

因此本报告只给出以下结论：

- 这次 RED 是前端执行器未就绪，不是候选 parse、Apply 或像素比较失败；候选质量没有被 CK3 反证。
- Epsilon 新候选的原生门禁仍是 `not-observed`，不得写成 GREEN。
- 完整失败报告永久保存在 [native-ck3-report.json](coat-of-arms-fit-artifacts/epsilon-q-v14-budget1024/native-ck3-report.json)，紧凑边界见 [native-attempt-summary.json](coat-of-arms-fit-artifacts/epsilon-q-v14-budget1024/native-attempt-summary.json)。

## 证据索引

- [1,024 档七图正式工件](coat-of-arms-fit-artifacts/epsilon-q-v14-budget1024/README.md)
- [128 档七图正式工件](coat-of-arms-fit-artifacts/epsilon-q-v13-budget128/README.md)
- [16 例封存留出](coat-of-arms-fit-artifacts/epsilon-q-v14-holdout/README.md)
- [Delta-Q 原生 r19](coat-of-arms-fit-artifacts/delta-q-native-r19/README.md)
- [Epsilon-Q 原规划与执行结论](../coat_of_arms_editer_of_ck3/docs/fitting-quality-epsilon-q-plan.md)

人工逐图偏好审阅仍是 `pending-human-review`。自动指标和原生一致性各自只证明其声明的边界，不替代真人观感判断。
