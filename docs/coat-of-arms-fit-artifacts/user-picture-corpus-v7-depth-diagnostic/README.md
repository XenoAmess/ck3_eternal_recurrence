# user-picture-corpus-v7-depth-diagnostic

本目录用 r6 固定校准取得的 `picture-07` CK3 crop，离线比较相同代码的两种 depth 方向。原生 crop
SHA-256 为 `AE81AE19E174A9F18DAC62D37A37A4E4D3F0BE22782CE0F264F98AD9F06151DC`；候选只改变
renderer 合同，不重新定位、裁切或启动 CK3。

结果明确支持 CK3 按 depth 降序绘制，即较小 depth 最后绘制并位于上层：

| 候选 | MAE | color MSE | edge | 综合 score |
|---|---:|---:|---:|---:|
| native clockwise + depth descending | 0.022078 | 0.004063 | 0.065893 | 0.027558 |
| native clockwise + depth ascending（旧生产逻辑） | 0.062193 | 0.028912 | 0.123880 | 0.065000 |

降序候选令综合 score 降低 57.60%，并恢复与 CK3 一致的遮挡结果。完整 8×8 空间误差、候选 PNG
哈希和排名见 `comparison.json`。该诊断促成 v8：网页预览默认采用降序；拟合器内部仍按追加前景层
搜索，交付前反转有限 depth 区间，并逐像素断言反编码前后的浏览器图像完全一致。

复现：

```bat
cd coat_of_arms_editer_of_ck3
set COA_NATIVE_TRANSFORM_DIAGNOSTIC=true&& set COA_NATIVE_TRANSFORM_CASES=picture-07&& set COA_NATIVE_TRANSFORM_CORPUS=docs/coat-of-arms-fit-artifacts/user-picture-corpus-v7-budget-1024&& set COA_NATIVE_TRANSFORM_OUTPUT=docs/coat-of-arms-fit-artifacts/user-picture-corpus-v7-depth-diagnostic&& pnpm exec playwright test e2e/native-transform-diagnostic.spec.ts --workers=1
cd ..
tools\.venv\Scripts\python.exe coat_of_arms_editer_of_ck3\tools\compare_native_transform_candidates.py --candidate-root docs\coat-of-arms-fit-artifacts\user-picture-corpus-v7-depth-diagnostic --native-root docs\coat-of-arms-fit-artifacts\user-picture-corpus-v7-native-r6 --output docs\coat-of-arms-fit-artifacts\user-picture-corpus-v7-depth-diagnostic\comparison.json
```
