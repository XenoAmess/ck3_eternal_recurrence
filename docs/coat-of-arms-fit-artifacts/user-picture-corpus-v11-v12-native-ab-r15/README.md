# user-picture-corpus-v11-v12-native-ab-r15

本目录是 v11/v12 形状替换的同一 CK3 会话 A/B。它不是新的七张用户图全集，而是把两个发生代码
变化的案例交替排列，并加入重复样本测量会话内噪声：

| A/B 槽 | 来源 |
|---|---|
| picture-01 | v11 picture-05 |
| picture-02 | v12 picture-05 |
| picture-03 | v11 picture-07 |
| picture-04 | v12 picture-07 |
| picture-05 | v11 picture-05 重复 |
| picture-06 | v12 picture-05 重复 |
| picture-07 | v12 picture-07 重复 |

全部案例共用一次 reference-independent UV 校准。运行源码为 commit `1080affa`；Steam 离线，全程
结构化 MCP，无 OCR、键盘和鼠标。7/7 首次原生像素与 7/7 Copy 再 Apply 像素均通过绝对门禁；
因为所有来源都属于带小数 rotation 的 05/07，严格 source → Copy 字段序列为 0/7，唯一失败字段
均为 `rotations`，计数完整。

## 同会话比较

| 候选 | MAE | MSE | edge | 最坏空间块 |
|---|---:|---:|---:|---:|
| v11 picture-05（第一次） | 0.04153668 | 0.00959922 | 0.13907681 | 0.22522105 |
| v11 picture-05（重复） | 0.04153969 | 0.00960099 | 0.13908339 | 0.22522105 |
| v12 picture-05（第一次） | 0.04178674 | 0.00970801 | 0.13931611 | 0.22518261 |
| v12 picture-05（重复） | 0.04178678 | 0.00970826 | 0.13931483 | 0.22518261 |
| v11 picture-07 | 0.02548051 | 0.00501182 | 0.08855295 | 0.09281543 |
| v12 picture-07（第一次） | 0.02547987 | 0.00501260 | 0.08854289 | 0.09282536 |
| v12 picture-07（重复） | 0.02548125 | 0.00501200 | 0.08855721 | 0.09282536 |

picture-05 的 v12 MAE 比 v11 高约 `0.000250`，而相同候选的重复漂移仅约 `0.000003`；MSE 和
edge 也同向退化。浏览器报告的形状改进没有转化为 CK3 原生改进，故 v12 picture-05 **原生比较
门禁失败**。picture-07 的 v11/v12 差异落在 v12 重复样本漂移量级，不能证明原生收益，也不能晋级。

因此 v12 作为实验和失败证据保留，但当前交付基线仍为 v11。后续实现必须让形状替换通过保守的
可迁移收益门禁，并改善非矩形 DDS 的 renderer/评分校准；不得只凭浏览器内部损失晋级。

`summary.json` SHA-256 为
`04EB316ADB2BB70F042A177A21B253F231F176D606FD679104B5B579FBDA4103`。被 `.gitignore` 排除的
原始 report 为 22,660,681 bytes，SHA-256
`F0B428769C1072D46ACED35141F38144E4BA2C3D8EC1EA927422B5DE9CD6AA93`。清理收据证明 CK3 进程树
归零、watchdog 消失、共享锁释放。

复现时先按上表把对应 v11/v12 目录中的 `coat_of_arms.txt` 与 `canonical-preview-230.png` 复制到
独立的七槽 corpus，再运行与 r14 相同的 runner，并把 `--picture-corpus` 指向该 corpus、输出指向
本目录。源文件的字节数和 SHA-256 已写入 `summary.json`，可核对映射而无需信任目录名。
