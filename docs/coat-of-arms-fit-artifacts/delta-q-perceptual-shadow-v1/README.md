# Delta-Q perceptual shadow calibration v1

本目录保留感知评分 v2 在参与搜索选优前的校准证据。

- 最终校准合同：`linear-rgb40-multiscale30-gradient20-bidirectional-edge7-structure3-shadow-v2`。
- 指标维度：线性光颜色、多尺度颜色布局、双向轮廓距离，以及边缘质量/重心/连通分量/封闭区域结构。
- 当前只由 CPU reference 计算并作为 shadow evidence 输出，不改变 legacy `0.62 color + 0.38 edge` 搜索排序；因此不存在把未实现的 GPU v2 结果冒充一致性的路径。
- 校准对象：`benchmark-v1` 的 64 个 hash-frozen holdout 真值，分别执行三级颜色、位置、缩放和旋转扰动。
- 自动门限是各扰动族“严重扰动不得优于轻微扰动”的样本比例：颜色 98%、位置 90%、缩放 85%、旋转 75%。中间档仍完整记录，但不把像素采样、裁切或旋转对称造成的局部逆序误报为 RED；较低的旋转门限明确容纳原生对称纹章。
- `report-r001-red.json` 保留最初误用“三级逐项严格单调”的 RED attempt，不覆盖、不删除。
- `report-r002.json` 保留把语义参数扰动误当作纯评分校准的 RED attempt；mask 混色、裁切和纹章对称会改变实际像素严重度，因此 Q1 改用冻结真值渲染上的确定性像素空间扰动，语义参数恢复由 Q2/Q3 单独验收。
- `report-r003.json` 保留直接平移真实纹章像素的 RED attempt；周期性图案会让较大位移偶然获得更低像素差。后续平移梯度固定同一个 12% 位移终点，再按 `1/12、4/12、12/12` 连续混合，从而校准评分对同一扰动方向的严重度响应。
- `report-r004.json` 证明 v1 的硬阈值轮廓/拓扑项即使面对同一终点的连续混合也会跳变。v2 保留双向轮廓、连通分量和封闭区域作为独立诊断，但总分以连续的线性颜色、多尺度颜色和梯度差为主，离散轮廓/结构合计只占 10%。
- `report-r005.json` 是最终 64 例留出集 GREEN 校准：颜色 100%、位置 96.875%、缩放 100%、旋转 100%。
- `real-v14-shadow-report.json` 对七张冻结真实图的 v14 首选候选以精确 DDS 在 96/230/512 px 全量重算 v2，绑定输入、源码、素材包和指标实现哈希；它只建立可比较基线，不参与旧版候选选择。

复现：

```text
cd coat_of_arms_editer_of_ck3
set COA_PERCEPTUAL_CALIBRATION_ARTIFACT=../docs/coat-of-arms-fit-artifacts/delta-q-perceptual-shadow-v1/report.json
pnpm exec playwright test e2e/perceptual-metric-calibration.spec.ts --workers=1 --reporter=line
set COA_PERCEPTUAL_REAL_ARTIFACT=docs/coat-of-arms-fit-artifacts/delta-q-perceptual-shadow-v1/real-v14-shadow-report.json
pnpm exec playwright test e2e/perceptual-real-baseline.spec.ts --workers=1 --reporter=line
```

`report.json` 逐样本保存四种扰动阶梯的总损失和单调判定，并绑定语料、素材包和评分源码 SHA-256。
