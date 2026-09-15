# user-picture-corpus-v7-native-r6

此 run 在浏览器/CK3 rotation 方向修复后重跑全部 7 例。源码 commit `02444758`，耗时 234.84 秒；
总报告 4 passed / 3 failed。picture-07 的原生 crop 首次清楚暴露 depth 层序相反：网页仍有眼睛和
胸前徽记，CK3 中却被后续大块覆盖，因此不能把 4/7 理解为画面全面正确。

该历史 RED 由 v8 depth 降序修复取代，r11/r12 已用原生 UV 校准证明当前 7/7 像素通过。原始报告
由 `.gitignore` 排除，SHA-256 为
`FA8631B21321CC4D3136BC4C033CB1999F312D556FAC37EB6123953E991AAE67`；精简收据和 7 张原生 crop
保留在本目录。
