# user-picture-corpus-v8-depth-diagnostic-r7

这是以 r7 的 v2 crop 为 reference 生成的 8 组 picture-07 变换/层序候选探索。`comparison.json`
SHA-256 为 `CBB92E3D19AFB8EEDE0AC2291ACDD7016C46A5A393C59ADD7A50337B3449DD8B`。

该诊断不能用于当前 renderer 晋级：r7 的 v2 reference 已混入会话原生框体和错误的矩形缩放，导致
候选分数共同偏高，且 `rotation-after-scale-negative` 的表面胜出与随后原生 UV 对照不一致。它只作为
“旧评分合同会误导候选选择”的过程 RED 保留。depth 根因的有效证据来自 r6 同一原生 crop 下的受控
升/降序消融；最终验证来自 r11/r12 的 reference-independent UV 校准。
