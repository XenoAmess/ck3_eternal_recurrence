# v6 native transform diagnostic

该目录用 r5 固定校准的 CK3 crop 对 v6 原始代码做受控 renderer 消融。每个强判别用例保持纹理、颜色、
位置、缩放、图层顺序和 CK3 framebuffer 不变，只替换：

- `scale-after-rotation` / `rotation-after-scale` 两种仿射顺序；
- 正/负两种屏幕旋转方向；
- 对胜出方向追加保留小数、截断整数、四舍五入整数三种角度处理。

比较使用与 MCP 相同的
`masked-srgb8-mae-mse-gradient-l1-spatial-8x8-v1`，原生 surface mask 向内腐蚀 5 px；完整结果在
`report.json`。

| 用例 | 旧生产候选 score / MAE | 胜出候选 | 胜出 score / MAE | score 改善 |
|---|---:|---|---:|---:|
| picture-02 | 0.102483 / 0.143826 | scale-after-rotation-negative | 0.072964 / 0.050917 | 28.80% |
| picture-05 | 0.121612 / 0.110180 | rotation-after-scale-negative | 0.121142 / 0.109736 | 0.39%（圆环近旋转对称，不作强证据） |
| picture-07 | 0.183888 / 0.236327 | scale-after-rotation-negative | 0.109572 / 0.101815 | 40.41% |

picture-02 与 picture-07 独立支持相同结论：现有 `mirror → rotation → scale → position` 顺序正确，
错误是浏览器把 CK3 正 rotation 画成了相反的屏幕方向。整数化候选在两例中均略差于保留小数，因此
原生 Copy 的整数规范化不构成浏览器主动量化角度的依据。

复现：

```bat
cd coat_of_arms_editer_of_ck3
set COA_NATIVE_TRANSFORM_DIAGNOSTIC=true&& pnpm exec playwright test e2e/native-transform-diagnostic.spec.ts --reporter=line
cd ..
tools\.venv\Scripts\python.exe coat_of_arms_editer_of_ck3\tools\compare_native_transform_candidates.py --candidate-root docs\coat-of-arms-fit-artifacts\user-picture-corpus-v6-transform-diagnostic --native-root docs\coat-of-arms-fit-artifacts\user-picture-corpus-v6-native-r5 --output docs\coat-of-arms-fit-artifacts\user-picture-corpus-v6-transform-diagnostic\report.json
```
