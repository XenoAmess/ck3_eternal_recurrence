# 模型输入历史：只省略真正相同的有序字节

机器：`xenoamess-full-tower-eb9d2c1186`。本单元修复普通自动游玩模型输入的保真错误，不处理当前UNKNOWN或恢复准入。

通用selector、和平Life紧凑任务和Council任务原先用`JsonNode.equals`或typed Map相等判断snapshot里的native history是否与外层history重复。对象成员顺序不同的两份历史会被判等，进而误删当前snapshot历史。例如`{"x":1,"y":2}`与`{"y":2,"x":1}`在旧谓词下相同，但固定wire编码字节不同。

现在三处均比较实际固定`FullJsonTree`编码的完整有序字节，仅真正相同的历史可以省略；不同顺序、未知字段、数组顺序或数字词法仍完整保留。原parser/encoder、原输入、command ID/SHA、决策协议、资格与实际执行边界不变。原`DecimalTokenNode.equals`已经比较原token，`1.0`与`1.00`不属于本次旧误判；数字用例只作保留回归。

compact分支同样使用真正wire的64层/64MiB域，避免改用旧OpportunityJson写入器的32层限制而意外降级。没有新增字段、类型、缓存或权限入口。

## 必要验证与失败保留

新DATA调用真正`requestPayload`，覆盖generic、Life、Council三条接线，按固定编码字节比较导出的snapshot与原件，检查原snapshot/history/command字节及command SHA保持。精确重复、成员顺序差异、嵌套顺序、未知字段、数组顺序、数字/大整数和35层直接构造typed DATA分别验证；深层用例不冒充真实现场曾出现该数据。

首两生产TU编译因owner在64层修正时多加一个右括号而exit1/0class，6.5569381秒，原RED保留。该错误属于owner整合，不计模型失败。只删该括号后，两必要生产TU实际exit0/5class，7.2270825秒，14:35:37.622402Z资源关闭；没有重编旧绿色依赖。

唯一新Test TU编译exit0/2class，4.8803968秒；仅运行三个新DATA方法，实际3P/0F/0E/0skip，exit0/5.4034823秒。14:38:41.209503Z资源关闭、held=false、三槽null。JUnit主XML42935 B，SHA-256 `7b7b8202f20d6f2c2012b17fb9bf2fac677b05d78fded9b90837a4aceb9c5b84`。仅复用旧PlanningFixtures类，未编译或执行旧用例。

两轮本地模型均完整HTTP200/stop/DONE。首轮错用byte[].equals引用比较、错误预算与typed列表，未采用；返工的Arrays.equals/64MiB/typedcopy核心部分采用，owner保留原fallback并纠正compact固定wire域。没有把HTTP成功写成实现成功，首编RED及修正后资格分开保留。

原件前缀：`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261105/model-history-byte-identity104/`，`PRODUCTION-READY03.json`及`TEST-READY01.json`指向实际源；模型原件在`model01`、`model02`。生产与新DATA输出分别在`D:/ck3-state/resume91-native-integration/p104-model-history03/`和`p104-model-history-test01/`。

这是生产输入保真修复的软件验证；没有Native/Game/GET、原动作调查、装载或新增保存信用，不据此授实际决策质量、端到端提速或G2整体验收完成。
