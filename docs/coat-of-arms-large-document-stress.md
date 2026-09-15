# CK3 家徽编辑器 10,000 实例完整文档压力证据

状态：`WP5 in_progress / complete-document sub-gate passed`  
日期：2026-09-15（Asia/Shanghai）  
合同：`ck3-coa-large-document-v1`

## 合同边界

此测试与“最大拟合预算为 10,000”不同。它确定性构造恰有 10,000 个实际绘制 `instance` 的文档，用来证明大文档不会因 UI
窗口、复制或保存路径而截断。产品预算仍由用户决定，10,000 不是上限。

- 用户预算：不适用（这是完整文档压力夹具，不冒充拟合结果）。
- 逻辑图层：1 个 `colored_emblem`。
- `colored_emblem` 块：1。
- 实际绘制实例 / `instance`：10,000。
- 确定性 CK3 源码：1,653,890 UTF-8 bytes，70,014 行，CRLF。
- 编辑窗口：32 个实例卡；复制和项目保存直接读取完整模型，不读取这 32 个 DOM 节点。
- 项目文件：`ck3-coa-browser-project-v1`；保存模型、选中图层、asset-pack receipt、源码计数及 SHA-256。导入时重新序列化并验证
  SHA-256 和全部计数，版本或内容不一致时拒绝载入。

首次浏览器运行前冻结的门禁位于
[`largeDocumentContract.ts`](../coat_of_arms_editer_of_ck3/src/domain/largeDocumentContract.ts)：项目导入 < 15,000 ms，跳到尾部并编辑
< 1,000 ms，完整剪贴板复制 < 5,000 ms，项目下载 < 10,000 ms。加入恢复工作包后，在执行第一轮自动保存压力试验前，又固定了
自动保存 < 15,000 ms、刷新后发现并恢复 < 15,000 ms。若 Chromium 提供 `performance.memory`，同一页面生命周期的 JavaScript
heap 增长须 < 256 MiB。内存值只覆盖 JS heap，不代表 GPU 或浏览器进程总内存。

## 失败与修复

第一轮没有截断，但“跳到第 10,000 项并编辑”耗时 4,683 ms，超过预先冻结的 1,000 ms 门禁。原因是每次尾部数值变化都会同步重绘
全部 10,000 个实例。未放宽门禁；修复改为：

- 每个活动图层仅物化 32 个可定位的实例编辑卡；任意索引仍可跳转。
- 大于 2,048 实例时显式延后整幅实时预览，页面清楚提示；模型、复制和保存保持完整。
- 确定性源码预览只显示前 64 KiB，并明确标为 UI 摘要；剪贴板和项目文件不使用摘要。
- 无完整 DDS 时的 fallback 预览最多物化 512 个简单元素，避免加载瞬间生成 10,000 个 DOM 节点。

修复后的同一 E2E 通过，门禁确实能够发现并阻止原来的同步重绘缺陷。

## 通过结果

浏览器：本机 Microsoft Edge headless；Vite 开发服务器；正式页面配置（无 CK3 companion）。

| 指标 | 实测 | 门禁 |
| --- | ---: | ---: |
| 项目导入并完成 SHA/计数验证 | 4,487 ms | < 15,000 ms |
| 跳到实例 10,000 并修改 rotation | 724 ms | < 1,000 ms |
| 完整剪贴板复制 | 178 ms | < 5,000 ms |
| 完整项目下载并重新验证 | 403 ms | < 10,000 ms |
| 页面实例卡 | 32 | = 32 |
| 复制后重新解析的实例 | 10,000 | = 10,000 |
| measured JS heap delta | 139,473,681 bytes | < 268,435,456 bytes |
| 非 GET 请求 | 0 | = 0 |

DOM-less Vitest 的同一文档还记录：序列化 19.73 ms、解析 191.97 ms、创建项目 65.92 ms、恢复项目 57.28 ms、尾部纯模型编辑
0.0261 ms。该进程不暴露浏览器/GPU 内存，因此其内存证据明确记为不可用。

## 自动保存、恢复与撤销工作包

实现提交：`d265503e`。编辑器现在把源码快照作为撤销/重做单位，以 450 ms 合并连续输入；历史最多 32 项且总 UTF-8 bytes 最多
16 MiB。单个超限快照不进入历史栈，但当前文档不被丢弃。自动保存使用浏览器 IndexedDB 的单槽覆盖记录，项目格式仍是
`ck3-coa-browser-project-v1`；刷新后必须重新验证源码 SHA-256 和计数，失败时拒绝恢复。整个链路没有用户内容网络写入。

同一 10,000 实例 E2E 加入自动保存和 reload 恢复后通过：

| 指标 | 实测 | 门禁 |
| --- | ---: | ---: |
| 项目导入并完成 SHA/计数验证 | 4,668 ms | < 15,000 ms |
| 跳到实例 10,000 并修改 rotation | 737 ms | < 1,000 ms |
| 完整剪贴板复制 | 161 ms | < 5,000 ms |
| 完整项目下载并重新验证 | 365 ms | < 10,000 ms |
| 10,000 实例 IndexedDB 自动保存 | 1,096 ms | < 15,000 ms |
| reload 后发现、校验、恢复并核对尾实例 | 5,899 ms | < 15,000 ms |
| 同页 measured JS heap delta | 188,860,210 bytes | < 268,435,456 bytes |
| 页面实例卡 / 恢复后实例 | 32 / 10,000 | = 32 / 10,000 |
| 非 GET 请求 | 0 | = 0 |

reload 后 `usedJSHeapSize` 的单点观测为 328,066,982 bytes，但不与 reload 前样本相减，也不用于门禁：Chromium 可能在 GC 前同时保留
旧、新 document，跨导航差值不是同页 JS heap 增长。独立小文档 E2E 另行通过编辑→自动保存→撤销→重做→reload→SHA 恢复→丢弃→
再次 reload 无恢复项的完整状态循环。

## 复现命令

在 `coat_of_arms_editer_of_ck3/` 中执行：

```text
pnpm exec vitest run src/domain/largeDocumentContract.test.ts --reporter=verbose
pnpm exec playwright test e2e/editor-recovery.spec.ts --reporter=line
pnpm exec playwright test e2e/large-document-stress.spec.ts --reporter=line
pnpm build
```

此证据只通过 WP5 的完整 10,000 实例文档子门禁。WP4 的真实 10,000 拟合预算、暂停/恢复/checkpoint、取消阶段矩阵和 GPU 批量
候选搜索仍须独立验收；WP5 的直接画布拖拽/缩放/旋转和候选对比也仍待完成。
