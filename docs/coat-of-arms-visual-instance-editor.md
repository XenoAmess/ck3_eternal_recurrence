# CK3 家徽可视化实例编辑证据

状态：`WP5 in_progress / direct transform sub-gate passed`  
日期：2026-09-15（Asia/Shanghai）  
实现提交：`39e18a9d`

## 已实现合同

结构化编辑区中的任意当前 `colored_emblem.instance` 都可以成为预览编辑目标。预览上显示三个语义明确、可聚焦的操作点：

- 中心点拖拽 `position`，画布手势把位置约束到 `[0, 1]`；数值输入仍可表达画布外位置。
- 右下操作点等比调整 `scale`，保留 X/Y 原比例和负号（镜像语义）。
- 顶部操作点连续调整 `rotation`，写入 0.001° 精度的有限数值；它不把导出值重新离散到 45°、1° 或 0.1°。
- 32 项实例窗口中的“在预览中编辑”切换精确实例；大文档无需物化全部实例卡。

每次 pointer gesture 是一个显式历史事务。首次测试发现 450 ms 文本输入防抖会在较慢的实时重绘中把一次拖拽切成多个中间撤销点；
实现未放宽断言，而是让手势开始时冻结源码快照、结束时一次性提交历史。因此一次位置、缩放或旋转手势均只需一次撤销即可精确恢复。
变换继续触发同一 IndexedDB 自动保存，并由完整 `CoatOfArms` 模型进入序列化和复制；操作点 DOM 不参与导出。

## 自动化验收

`e2e/visual-transform-editor.spec.ts` 在正式独立页面配置下完成：

1. 选择第 1 个实例并拖动中心，结构化 X/Y 数值实际变化。
2. 一次撤销恢复原始 `position = { 0.3 0.5 }`。
3. 沿当前视觉半径放大，X/Y scale 同时增长；一次撤销恢复 `{ 0.35 0.35 }`。
4. 绕实例中心旋转约 90°；一次撤销恢复 `rotation = -20`。
5. 从实例窗口选择第 2 个实例，预览编辑目标和选中样式同步切换。

同次回归还通过自动保存恢复 E2E 与 10,000 实例完整文档 E2E。后者实测尾部编辑 753 ms、自动保存 1,209 ms、reload 恢复
6,105 ms、同页 JS heap delta 90,523,547 bytes、非 GET 请求 0，均在既有冻结门禁内。

## 复现命令

在 `coat_of_arms_editer_of_ck3/` 中执行：

```text
pnpm exec playwright test e2e/visual-transform-editor.spec.ts --reporter=line
pnpm exec playwright test e2e/editor-recovery.spec.ts e2e/visual-transform-editor.spec.ts e2e/large-document-stress.spec.ts --reporter=line
pnpm test
pnpm build
```

这只通过 WP5 的直接 transform 子门禁；候选对比、键盘微调/可访问性扩展，以及 WP4 拟合任务 pause/resume/checkpoint 仍待完成。
