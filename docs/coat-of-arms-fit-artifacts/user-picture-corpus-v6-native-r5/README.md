# user-picture-corpus-v6-native-r5

首次对 `pictures.zip` 全部 7 例执行固定表面校准后的 CK3 Apply/Copy/framebuffer run。源码 commit
`2ccfce15`，耗时 229.087 秒；总报告 2 passed / 5 failed。它暴露了浏览器把 CK3 正 rotation
解释成相反屏幕方向的缺陷，并证明 7 例核心实例/块计数未被大载荷传输截断。

本目录是历史 RED 根因证据，不是当前产品基线。r6 修复 rotation，r7 修复 depth，r11/r12 又用
原生 UV 校准消除了 v2 原生框体污染。原始报告由 `.gitignore` 排除，SHA-256 为
`78B680E84008FC30D4E65BE06341364C6F98C55DCDFCE938FC016666C51835F2`；精简收据和 7 张原生 crop
保留在本目录。
