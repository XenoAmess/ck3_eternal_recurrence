# 六项净转移账本候选的 L0 证据

实机暴露 base-skill probe 漏扣及百分比遮蔽后，生产改为六项独立、有符号净转移账本和 scaled character modifiers。生产代码不再使用任何 `add_*_skill`；供给者与接收者在同一技能账本分别 -1 / +1，再重建各自对应的正负 modifier 并刷新总技能缓存。A0001/A0002 继续保留为历史诊断证据，不能作为当前实现的发布验收。

新增独立结构合同验证双方同项守恒、缺失账本的初始化、两方写完后重建、modifier 的技能/正负号/scale、查询无持久状态写入及经验上限保持 `92233720368547`。测试读取实际生成的条件和算术结构，检查 donor 有效技能为 0 时排除、receiver 为 0 时可以接收、±1,000,000 账本容量的最后合法点及饱和边界、六项随机分支等权且关联正确资格标记；不靠全文生成输出比对完成这些规则检查。

新负例共有 54 个 subcases，分别破坏六项增减守恒、初始化、modifier 点数、负 scale 符号、receiver 零值资格、donor 零值限制、两端容量以及禁止 base 写入、重建/刷新、随机权重、查询只读和经验上限。全部实际返回 RED；原有静态测试同时通过。

| 受影响验证 | 实际结果 |
| --- | --- |
| 静态测试 | 8 tests PASS，包含 54 个独立账本负例。 |
| 发布边界测试 | 5 tests PASS。 |
| 静态验证 | GREEN；13 生成文件逐字节一致，九语言各 24 keys，BOM/header/保护 token/引用一致。 |
| 新夹具语法预验 | frozen `fixture-a11` 的 5 文件由实际 open_kaishek JAR parse/roundTrip 通过，零 diagnostics。 |
| 生产语法预验 | 复用执行代理已完成的五项受影响生产脚本原始回执；grammar/roundTrip 通过，runtime semantics 明确 UNSUPPORTED。未重复运行。 |
| 双构建及候选复验 | 精确 22 文件，manifest/ZIP 可复现，verify PASS。 |

候选 staging 为 `D:/ck3-superman-qiang-20261004/builder-L0-A0003/mod_superman_qiang`，绑定 Git commit `599af8da0008fd77f30347f7d3a7b2faef33a852`，没有正式 tag。此候选已经提供给执行代理进行后续原生 R0007，不等待文档归档。

- manifest SHA-256：`0272aa21327336f95b199b36dfca90286c1a7818aab4f679143c601c5f1c17ef`。
- ZIP SHA-256：`4a28f69a97d606bf31ca42dc122b5e3130ffcff307df30807247692abfd9873e`。

[完整 A0003 构建报告](build-report-2026-10-04-L0-A0003.json) 与对应 `build-evidence-2026-10-04-L0-A0003/` 保存原始命令 argv、起止时间、stdout/stderr、真实 parser corpus、原回执、22 文件完整 manifest 和摘要。复制这些原始字节时没有转录或重跑测试。

这些检查只认证声明条件、账本算术和构建。引擎内 modifier scale、百分比或下限的实际总技能显示、原版入口、保存重载及玩家界面由后续实机证据判断；parser 的 grammar 通过不能替代原生效果语义。正式构建应使用完成验收后的同一运行字节，并绑定最终 clean commit/tag；当前包未上传到外部平台。
