# user-picture-corpus-v8-native-r7

此 run 在 CK3 depth 降序修复后重跑全部 7 例。源码 commit `4f000a7c`，耗时 227.358 秒。原生
picture-07 已恢复眼睛和胸前徽记，证明层序修复有效；但当时的 framebuffer v2 把会话中的圆框/盾框
包围盒直接缩放到网页正方形，7 例数值门禁因此全部为 RED，不能作为产品像素结论。

r8-r10 随后用于开发原生 UV 标定和稳定前台捕获，r11/r12 才是可比较的晋级证据。本目录保留 r7
现场而不改写。原始报告由 `.gitignore` 排除，SHA-256 为
`CCDA1B466AD44BB76D87D94A3EBC0F22D5799E0F96FB2353CE2B9AEB2C86DABB`。
