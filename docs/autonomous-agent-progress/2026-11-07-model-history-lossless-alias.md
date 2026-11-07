# 无损模型历史alias保持完整有序内容

机器：`xenoamess-full-tower-eb9d2c1186`。本单元继P104继续修复普通自动游玩模型输入；不修改规划资格、实际命令、encoder或当前UNKNOWN恢复链。

真实`requestPayload`中的ROOT事实字典与整份declarable-wars数组alias原先按树结构相等复用。A/B/A三行中，B仅改变未知对象成员顺序，旧谓词仍可能把B引用到A；无损恢复因而无法还原B的原有顺序。当前两处按固定`FullJsonTree`完整编码的Base64精确键查找：B保留为独立内容，第三个真正相同A仍可复用。WAR引用保留原history首次实际位置，ROOT引用保留facts数组位置与原两份revision stamp。

索引只存在于本次payload调用，每个当前完整数组或去原两stamp后的ROOT facts只编码一次并进行Map查找，不对每个新值重编码所有旧值。原schema、碰撞回退、unknown/unfamiliar行、source元数据与原技术五字段删除规则保持；不新增全局或跨请求缓存。

family alias保持原样：实际生产先经ActionCodec/PublicDataJson递归排序arguments，再进入family alias，未证存在可达成员顺序错误；没有拿私有helper的乱序输入冒充真实管线缺陷。

## 验证范围

新DATA复用P104已合格的纯fixture构造器，调用真正payload。ROOT验证A/B/A→refs0/1/0及两份facts的完整有序inverse（仅原协议技术字段省略）；WAR验证不同B保留、第三A命中原history首次位置及整份history字节inverse；原碰撞名回退、原输入、command字节/SHA、数字与大整数保留分别覆盖。没有重跑P104三个方法。

生产ROOT私有helper增加局部Map参数。唯一现有反射测试消费者已同步到新三参签名，原断言保持；这属于必要消费者同步，不为测试新增生产兼容重载。私有签名变化不授既有方法体原地热替能力。

一次完整本地模型候选的局部字典/一次编码核心部分采用，owner将UTF8解码String键改为已有Base64精确字节键；这是保守接线选择，不描述为已证明模型方案有业务错误。模型HTTP与软件通过、发表及实际装载分开记录。

必要生产编译仅Selector1TU，actual exit0/4class/6.1407942秒，14:44:34.705636Z资源关闭；P104的Council与其他已绿依赖复用。新inverse Test1TU exit0/1class/3.5679268秒，仅三个新方法实际3P/0F/0E/0skip，3.5978985秒，14:47:54.778857Z资源关闭。上述软件结果不授业务动作或实际装载。

必要反射消费者同步另编一个实际修改的既有Test TU：exit0/1class/4.2502457秒，仅运行受影响`equalFactsShareReferenceButStampsAndUnknownDifferencesRemain`，实际1P/0F/0E/0skip，3.2926611秒。最终14:50:05.598401Z资源关闭、held=false、三槽null。总计1生产TU、1新Test TU、1修改既有Test TU；执行3个新case加1个受影响既有case，不写成4个新case或旧测试0。P104三个方法未重跑。

软件输出分别保留在`D:/ck3-state/resume91-native-integration/p105-model-alias01/`、`p105-model-alias-test01/`与`p105-model-alias-oracle01/`；所有原ACTUAL、终态、输出与资源关闭回执保留。Root已独读实际phase及两个JUnit计数/方法名。

最终资格：`D:/ck3-state/resume91-native-integration/p105-model-alias-test01/QUALIFIED-P105-THREE-NEW-ONE-AFFECTED-DATA.json`，19104 B，SHA-256 `d6054a66b3669b27af44c7dca5c393d802060f4cd9f02ecc79c18056fbe3e325`。其中也保留runner参数抄写错误在0JVM时拒绝的owner记录，不改述为模型或编译失败。

原件前缀：`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261105/model-lossless-history-alias105/`。`PRODUCTION-READY01.json`、`TEST-READY01.json`、`AFFECTED-ORACLE-READY01.json`指向实际源；完整TASK/SPEC/REQUEST/CONTENT/RESULT在原件及`model01`下。

本单元尚不授实际装载、决策质量、端到端性能、新保存日或G2整体验收。实际Game、Guard、原UNKNOWN、deadline、账本与冻结工作树保持。
