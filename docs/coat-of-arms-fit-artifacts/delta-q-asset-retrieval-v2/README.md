# Delta-Q asset retrieval v2

Q2 把既有 content-addressed 18×18 fit feature sidecar 派生为确定性素材检索 v2：联合使用二值 alpha/颜色形状的有符号距离场、Hu moments、径向直方图、方向直方图、四轴对称性、连通域、孔洞与占用率；素材身份与 24 个 15° 旋转、两种镜像变换分开记录。

检索先以 6×6 稀疏网格扫描 24 个旋转与两种镜像，并辅以旋转/镜像不变量，从完整 1,573 项 colored-emblem 库产生 128 项有界 shortlist，再在完整 18×18 网格与有符号距离场上精排。R001 的 96 项纯不变量前沿只有 43.75% Top-8，R002 即使扩大到 512 项也只有 68.75%，证明问题是粗排合同而非单纯容量；两次 RED 均永久保留。矩形、圆、菱形和楔形 primitive fallback 仍由搜索层强制保留，不依赖召回名次。

`report-r001-red.json` 与 `report-r002-red.json` 永久保留失败尝试；`report.json` 使用 benchmark-v1 的 64 个 hash-frozen holdout，每例取第一项真值素材，并施加真值 rotation 与 X 镜像符号；门限为 Top-8 recall ≥85%、Top-32 recall ≥95%。报告绑定语料、素材包和实现 SHA-256，并逐例记录 rank 与 Top-8。

复现：

```text
cd coat_of_arms_editer_of_ck3
set COA_RETRIEVAL_ARTIFACT=docs/coat-of-arms-fit-artifacts/delta-q-asset-retrieval-v2/report.json
pnpm exec playwright test e2e/asset-retrieval-holdout.spec.ts --workers=1 --reporter=line
```
