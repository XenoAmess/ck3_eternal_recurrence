# 主模组庭臣目录跟随 Florin

machine_id: `desktop-3fevhd2-1c74096080`。实际观察2026-11-19 UTC／11月20日上海时间；本机CK3 1.21.0.3/build26785313，EXE SHA256 `859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28`。

主模组庭臣生成器现使用从本机实际`00_traits.txt`由原提取器生成的独立`courtier_traits_1_21_0_3.json`：原版355058B/SHA256 `793718c2388f8d7b6c009468a2f5f8f5d1d8443acec4a015614ffac4f05b98cd`，311个定义。相对旧306定义，新增5个key；原有devoted改为可见，连同merchant_associate、lifestyle_merchant、dealbreaker使目录新增4项。两个新hidden不进目录，不能把它们描述成六个新定义。

分类为25/17/38/36/114，union230、designer-visible229、冲突96。实际原版成本和16岁约束保留；主模组xar前缀、TRAIT宏及原Rite/gameplay模板后缀逐字相同。三份生成消费者、九语言指定帮助行110→114、共享制备器Main114读回、四visible／两hidden标记及主case真实GUI要求一起同步。未套用独立Vivhite产品身份或改变其生产源。

公共字段复用既有单一TraitMetadata／TypeGuard，消费前拒绝缺字段、错容器及bool/float类型混淆。提取CLI现要求显式已审`--game-version`、真实源SHA与新版本显式输出，并拒绝覆写三个历史快照路径；历史默认和实际FileID/mtime/SHA均保留。22项现有回归零skip通过，三个完整模块strict及另两个完整模块标准mypy通过；原未注解失败保留后以明确`dict[str,set[str]]`修复。三条实际非法CLI分别拒绝，未被计为成功提取。[软件与生产链](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/main-courtier-121003-source-software.json)、[类型](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/main-courtier-121003-types.json)。

集成全部20个目标前逐项匹配原SHA和补丁目标SHA；九语言只交付精确patch，因此由已验证的原diff parser回放，未强行覆盖其他改动。实际仓库生成器`--check`退出0并读回114/230/96。[正式路径生成检查](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/living-main-public-integration.json)。

此项是主模组庭臣来源单元，不授整主模组、完整fixture CLI或GUI通过。新特质／年龄／互斥的真实窗口、实际创建／交付／扣款、Rite、进阶／评分／死亡／重启及全产品构建仍待完成；Native/Full/Actor/SAVE守卫没有扩宽。共享制备器读到新引擎metadata不等于实际装载了新ABI。
