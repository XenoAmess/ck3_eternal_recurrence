# CK3 家徽编辑器：用户图片回归集与预览偏差排查

## 本轮结论（2026-09-16）

`pictures.zip` 中的 7 张图片已全部纳入可追溯回归集，不做抽样。原始压缩包大小为
6,240,071 bytes，SHA-256 为
`0D6C529035333E22E34758D1128A713218D877831206FF60E11990CD362C575F`。每张图片的文件名、尺寸、字节数与
SHA-256 保存在
`coat_of_arms_editer_of_ck3/e2e/fixtures/pictures/cases.json`。

已稳定复现并修复一个独立缺陷：拟合报告下方的预览和右侧结构化编辑器预览原本来自两条不同渲染链。

- 下方预览按拟合分辨率单独渲染；小预算时只有 `56×56`，且漏掉了原生盾面
  `coa_mask_texture.dds` 与命名色。
- 右侧预览按 `230×230` 的 shader 模型渲染，包含盾面 mask 和命名色；CSS 还把它拉伸并裁成盾形。
- 因此同一份代码在页面内都会显示成两幅不同的图。修复后两处强制引用同一个 canonical
  data URL，并使用相同的盾形比例、拉伸和 clip-path。
- 拟合 Worker、WebGL 交叉评分与精确剪枝 Worker 也改为使用和右侧/原生目标一致的
  surface-mask 与命名色合同，不再优化一幅最终不会显示的“裸正方形”。

最小失败证据使用 `picture-01`和预算 1：旧链的下方图像为 56×56 PNG，右侧为
230×230 PNG，字节不一致；修复后同一用例通过。完整 7 图串行回归为 `7 passed
(2.9m)`，并逐图断言两处 data URL 字节一致、展示几何一致、`surfaceMaskApplied=true`。

## 1024 预算浏览器质量基线

下表是 7 张图用相同的 1024 绘制实例预算逐一运行的实测数据。总损失、边缘损失与相对改善只是
`alpha-weighted-srgb8-mse62-luma-gradient-l1-38-v1` 合同下的浏览器比较，不代表 CK3
像素已验。

| 用例 | 原图 | 实际实例 | 总损失 | 边缘损失 | 相对改善 | 代码 bytes / 行 |
|---|---|---:|---:|---:|---:|---:|
| picture-01 | `718c….jpg` | 726 | 0.026529 | 0.052951 | 41.63% | 286,960 / 10,171 |
| picture-02 | `a124….jpg` | 580 | 0.035329 | 0.064976 | 41.67% | 232,336 / 8,127 |
| picture-03 | `baiqi2.png` | 877 | 0.027418 | 0.055756 | 53.84% | 346,485 / 12,285 |
| picture-04 | `BV1bt421G7qL.png` | 913 | 0.055554 | 0.106272 | 57.63% | 363,063 / 12,789 |
| picture-05 | `BV1oe411i7oF.png` | 881 | 0.057423 | 0.100367 | 74.56% | 347,408 / 12,341 |
| picture-06 | `Cache_5d2e1902d7c282d2.png` | 722 | 0.018526 | 0.035506 | 82.28% | 282,025 / 10,115 |
| picture-07 | `人类化头像.png` | 956 | 0.053918 | 0.090944 | 64.30% | 378,300 / 13,391 |

这组数据证明用户反馈的第一类问题不能解释为“只是上下预览不一致”。`picture-01`和
`picture-02` 在 1024 预算下仍只有约 42% 相对改善；`picture-04/05/07` 的绝对边缘损失也明显偏高。
目前实现虽会在 96/192/256 上重评候选，但主要块画搜索和局部边缘修复仍发生在 96×96
平面，复杂人脸的眼睛、头发边界和细线被量化成明显方块。这是下一质量修复包的已量化基线，
不得把“能识别大致轮廓”冒充成与原图高保真。

## 验收分级和剩余工作

## v6 预算穷尽边缘修复（2026-09-16）

继续排查后发现另有两个直接导致“拟合一点也不像”的实现问题：页面把早期 smoke test 的 `6` 层作为
默认预算；且原生块构图完成后，边缘热点修复被 `Math.min(8, remaining)` 无条件截断，即使仍有数百个
严格改善候选也会提前停止。现已把默认预算改为 1,024（用户仍可输入任意安全整数，不 clamp），并让边缘
修复一直运行到预算耗尽或完整一轮没有改善。

同一 1,024 预算、同一评分合同的逐图非劣化回归通过：picture-01/03/04/06 的总损失和边缘损失均下降，
picture-02/05/07 在没有更多严格改善时保持 v5 数值。picture-01 总损失由 `0.026529` 降至 `0.018757`，
picture-06 由 `0.018526` 降至 `0.008202`。完整逐图结果和代码已冻结在
`docs/coat-of-arms-fit-artifacts/user-picture-corpus-v6-budget-1024/`。

真实压力合同也已通过：128 / 1,024 / 10,000 三个输入预算均不被静默修改；10,000 档自然收敛到
2,320 个严格改善实例，耗时 100.864 秒，复制得到 905,361 UTF-8 bytes、32,487 行，重新解析仍为
2,320 块/实例。暂停响应 36.2 ms，刷新恢复 3.385 秒，继续完成 4.470 秒，取消 61 ms；观测到的
JS heap 增量为 30,873,829 bytes（不包含 GPU/浏览器进程内存）。

这仍不是“所有复杂头像已达到高保真”的声明。picture-02/05/07 的边缘损失仍高，后续需要高分辨率
局部替换和更丰富原生画笔搜索；CK3 原生像素差异仍必须由 MCP framebuffer 能力逐图验证。

## v7 原生旋转方向修复（2026-09-16）

reference-independent framebuffer MCP 的 r5 实机运行完成了 7/7 Apply、Copy 和固定 surface crop，随后
暴露出浏览器 renderer 的独立错误：CK3 的正 `rotation` 在屏幕空间按顺时针解释，浏览器此前按相反方向
渲染。纯 `ce_block_02.dds` 案例不受影响；带有旋转、非等比缩放语义元素的 picture-02/07 因而明显错位。

受控消融保持 r5 CK3 crop 不变，只比较两种仿射顺序和两种旋转方向。picture-02 的综合 score 从
`0.102483` 降到 `0.072964`、MAE 从 `0.143826` 降到 `0.050917`；picture-07 的 score 从
`0.183888` 降到 `0.109572`、MAE 从 `0.236327` 降到 `0.101815`。两例共同选择“保持现有变换顺序、
反转屏幕旋转方向”；完整候选和指标在
`docs/coat-of-arms-fit-artifacts/user-picture-corpus-v6-transform-diagnostic/`。

修复已同时进入完整 renderer、增量拟合 renderer、轮廓 descriptor 和内容重心补偿。七例已在新合同
`cpu-rgba8-bilinear-clamp-pixel-center-native-clockwise-v2` 下重新以 1,024 预算生成，7/7 浏览器闭环通过，
结果冻结在 `docs/coat-of-arms-fit-artifacts/user-picture-corpus-v7-budget-1024/`。新 v7 的损失数值与 v6
保持一致，但语义元素输出角度改为 CK3 的方向；例如 picture-02 从 `223.375°` 改为 `136.625°`。
v7 原生 Apply/Copy/framebuffer 重跑完成前，状态仍是“浏览器修复通过、CK3 新候选待验”。

## v8 原生 depth 顺序修复（2026-09-16）

v7 r6 的 7 例首次粘贴均完成；旋转修复使 framebuffer MAE 全面下降，但 `picture-07` 暴露了更严重的
视觉假阳性：网页仍显示双眼和胸前徽记，CK3 却被后续大块覆盖。保持同一个 r6 crop、同一个 mask 和
同一个评分合同，只切换 depth 排序方向后，降序候选的 MAE 从 `0.062193` 降到 `0.022078`，edge 从
`0.123880` 降到 `0.065893`，综合 score 从 `0.065000` 降到 `0.027558`。这证明 CK3 是较大 depth
先画、较小 depth 后画，而网页旧实现相反。

生产 renderer 已改为 CK3 的 depth 降序。拟合搜索仍在内部追加前景层；交付前把有限 depth 区间反转，
并逐像素断言新原生表示与内部候选完全一致。v8 的七张 canonical preview 与 v7 字节相同，1024 预算
指标也完全相同，只有导出 depth 序列改变；七例上下预览、完整复制、解析计数和序列化闭环均通过。
浏览器产物在 `docs/coat-of-arms-fit-artifacts/user-picture-corpus-v8-budget-1024/`，受控消融在
`docs/coat-of-arms-fit-artifacts/user-picture-corpus-v7-depth-diagnostic/`。

## v8 原生 UV 对照完成（2026-09-16）

framebuffer MCP v3 先用红/绿状态定位动态表面，再通过黑底与 9 个原生白色标记恢复 canonical UV
到原生 framebuffer 的仿射映射，避免 CK3 圆框/盾框变化污染缩放和裁剪。r11 的 9 点最大重投影
误差为 0 px；`pictures.zip` 全部 7 例均完成大载荷 Apply、Copy、UV 对齐截图和空间评分。

7/7 原生像素门禁通过：MAE 范围为 0.020320–0.043774，MSE 为 0.004009–0.010389，edge 为
0.058618–0.132857，最坏 8×8 空间块为 0.082469–0.140578，全部低于运行前冻结的
0.10 / 0.03 / 0.16 / 0.25 阈值。逐图人工复核同样确认主体和层序一致，picture-07 不再出现前景
被大块覆盖。证据位于 `docs/coat-of-arms-fit-artifacts/user-picture-corpus-v8-native-r11/`。

严格文本 round-trip 为 4/7；picture-02/05/07 的唯一失败字段是 rotation，因为 CK3 Copy 将小数
rotation 规范化为整数。三例当前 Apply 后的像素门禁均通过，但还不能据此宣称“Copy 回读文本再次
Apply”也像素等价；该差异继续单列，不用宽松归一化掩盖。

r12 已补齐上述独立验证：把 7 例首次 CK3 aligned crop 作为 reference，把每例原生 Copy 全文再次
分块 Apply 并重新捕获。7/7 完成二次严格传输/计数/语义闭环，7/7 通过更严格的
0.01 / 0.001 / 0.02 / 0.03 像素门禁；最高 MAE 仅 0.0000771。02/05/07 的文本 rotation 取整仍
记录为字段变化，但在当前原生家徽表面分辨率下已证明像素等价。r12 证据位于
`docs/coat-of-arms-fit-artifacts/user-picture-corpus-v8-native-r12/`。

## v11 高分辨率混合修复与统一展示投影（2026-09-16）

继续排查发现，首版 256px 修复虽然存在，却接在已经耗尽 1,024 槽位的纯矩形 lane 后面；真正胜出的
混合 lane（picture-02/05/07 分别只有 580/881/956 层）没有进入高分阶段。v9 因而 7 图全部与 v8
一致，这个无收益实验保留在 `user-picture-corpus-v9-high-resolution-budget-1024/`，不冒充修复。

v10/v11 把完整 DDS 纹理表和混合候选送入 256px 残差搜索。新层只有在 256px 总损失/边缘损失形成
Pareto 改善、同时 96px 两项均不退化时才接受。picture-02/05/07 分别保留 60/36/30 个高分层：

| 用例 | v8 实例→v11 | v8 总损失→v11 | v8 边缘→v11 | 总损失改善 | 边缘改善 |
|---|---:|---:|---:|---:|---:|
| picture-02 | 580→640 | 0.035329→0.033979 | 0.064976→0.063220 | 3.82% | 2.70% |
| picture-05 | 881→917 | 0.057423→0.052995 | 0.100367→0.095896 | 7.71% | 4.46% |
| picture-07 | 956→986 | 0.053918→0.049606 | 0.090944→0.086218 | 8.00% | 5.20% |

另一个可见差异来自展示层而非 renderer：候选卡把同一 PNG 放进 1:1 正方形，主预览用 260:315
盾形裁剪；主预览还默认显示黄色变换辅助线。v11 让三处引用同一个 canonical PNG、使用同一盾形
clip-path 和纵横比，并把辅助线改成默认隐藏、显式切换。E2E 不再只比较 URL，还逐图比较计算后的
clip-path、纵横比和默认辅助线状态。

v11 浏览器门禁 7/7 通过；picture-01/03/04/06 在预算已满时数值精确不变。最终浏览器证据位于
`docs/coat-of-arms-fit-artifacts/user-picture-corpus-v11-preview-projection-budget-1024/`。

新的 r13 没有继承 v8 结论，而是对 v11 全部 7 例重新执行结构化 MCP Apply、Copy、UV 标定捕获、
Copy 再 Apply。网页 canonical → CK3 为 7/7：最坏 MAE 0.033104、MSE 0.005396、edge
0.098117、最坏空间块 0.108654，全部通过冻结门禁。Copy 再 Apply 也为 7/7，最坏 MAE 仅
0.0000793。严格 source → Copy 字段序列仍为 4/7，因为 CK3 对 picture-02/05/07 的小数 rotation
取整；实例/层/块计数完整，规范化后的 Copy 文本自身 7/7 稳定往返。证据位于
`docs/coat-of-arms-fit-artifacts/user-picture-corpus-v11-native-r13/`。

| 检查 | 当前状态 | 当前证据能支持的结论 |
|---|---|---|
| 原图→浏览器拟合 | v11 已逐图量化；v12 实验未晋级 | 7 图均完成 1024 预算；v12 形状替换的浏览器微小收益未通过同会话原生比较 |
| 下方预览→右侧预览 | v11 通过 | 7/7 canonical PNG、盾形 clip-path、纵横比一致；编辑辅助线默认隐藏 |
| 完整复制→重新解析 | 通过 | 7/7 代码完整，实例计数一致，serialize/parse 精确闭环 |
| CK3 Apply/Copy | v11 r13 完成 | 7/7 计数完整、Copy 文本自身稳定回读；首次严格字段序列 4/7，02/05/07 有原生 rotation 取整 |
| CK3 空间像素→右侧预览 | v11 r13 通过；v12 r14 绝对门禁通过但 A/B 未晋级 | v3 UV 校准后逐图可追溯；r15 证明 05 假收益、07 无可证收益 |

MCP 的当前定位、指标和隐私边界见
`docs/ck3-coat-of-arms-framebuffer-comparison-v3.md`。v11 的预览一致性、原生 framebuffer 和 Copy
再导入闭环现已完成；后续质量工作继续扩展更丰富画笔和高分辨率局部替换，不再把展示链或原生层序
差异与“拟合本身仍可继续提升”混为一谈。

## v12 迭代混合原生形状替换（2026-09-16）

v11 的大预算混合路径已经有一个语义 seed，但局部原生形状替换固定只尝试一次，且 descriptor
shortlist 不保证矩形、圆、菱形、楔形基础族实际进入评分。v12 保留 descriptor 最强候选，同时把
`ce_block_02`、`ce_billet`、`ce_circle`、`ce_lozenge`、`ce_triangle_mask` 注入真实渲染 shortlist；
替换 pass 随预算对数增长，并在首次无改善时停止。这个子阶段共享用户实例预算，不会 clamp 总预算。

7 图浏览器回归通过。picture-01/02/03/04/06 的代码逐字节不变；picture-02 明确评估 648 个候选后
因无改善停止。picture-05 接受 `ce_billet`×2、`ce_letter_j`、`ce_letter_i`，在仍为 917 实例时将
总损失从 0.052995 降至 0.052549、边缘从 0.095896 降至 0.094820。picture-07 接受
`ce_circle`，在仍为 986 实例时将总损失从 0.049606 降至 0.049541、边缘从 0.086218 降至
0.085786。两例的 192/256px 指标也不退化。完整浏览器证据位于
`docs/coat-of-arms-fit-artifacts/user-picture-corpus-v12-mixed-shape-budget-1024/`。

新的 r14 对全部 7 例完成结构化 MCP 原生复验：网页→CK3 与 Copy→再次 Apply 均为 7/7 像素门禁
通过，严格文本字段仍因 02/05/07 的 rotation 取整为 4/7。但跨会话的未变代码样本也显示明显数值
漂移，不能直接拿 r13/r14 数字判断 v12 是否更好。因此 r15 在同一次 UV 校准内交替导入
v11/v12 picture-05/07，并重复 05 与 07 测量噪声。

r15 证明 picture-05 的 v12 原生 MAE 比 v11 高约 0.000250，而重复样本漂移约 0.000003；MSE 与
edge 也退化。picture-07 的差异处在重复漂移量级，不能证明原生收益。故 v12 浏览器评分产生了
不可迁移的微小假收益，**不晋级**；交付基线继续使用 v11。r14/r15 完整证据分别在
`user-picture-corpus-v12-native-r14/` 和 `user-picture-corpus-v11-v12-native-ab-r15/`。

## 复现命令

```bat
cd coat_of_arms_editer_of_ck3
pnpm exec playwright test e2e/user-picture-preview-consistency.spec.ts --reporter=line
set COA_CORPUS_BUDGET=1024&& set COA_CORPUS_ARTIFACT_ROOT=docs/coat-of-arms-fit-artifacts/user-picture-corpus-v11-preview-projection-budget-1024&& pnpm exec playwright test e2e/user-picture-quality-corpus.spec.ts --workers=1
pnpm test
pnpm build
```

质量套件把每张图的完整 CK3 代码、canonical 230px PNG、拟合报告截图、右侧预览截图和
JSON receipt 写入
`coat_of_arms_editer_of_ck3/test-results/user-picture-quality-corpus/budget-<N>/<case>/`。该目录是本地运行产物；
正式晋级的原生对照会另存到 append-only docs artifact，不覆盖浏览器基线。
