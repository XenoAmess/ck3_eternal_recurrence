# 1.1.0 健康转移与查看通知的 L0 证据

候选 `superman-qiang-health-toast-L0-A0001-20261004` 将查看性经验改为原生通知，并增加健康为第七个等权候选。健康以每次 `0.00075` 在双方同项账本严格一增一减，供给者当前有效健康至少为 `3.00075`；接收者无需健康大于零。账本保持 ±1,000,000 的容量边界，最后合法点为接收者 `999999.99925`、供给者 `-999999.99925`。基础健康不直接写入，双方写完后重建对应正负 modifier。原六项技能和经验计数合同继续验证。

静态求值器改为 Decimal，精确验证健康的小数步长、总值 getter、scale 正负号、容量最后合法点与再超出 `0.00001` 的拒绝，以及从相反方向离开 ±1,000,000 的合法资格。独立 AST 同时验证七项等权随机、双方同项守恒及重建、查询不写持久状态、通知发给 actor 并使用 recipient 图标，以及不再派发旧查看事件窗口。

| 实际检查 | 结果 |
| --- | --- |
| 生成字节检查 | `gen_runtime --check` PASS，共 20 文件。 |
| 静态验证 | GREEN，正式清单仍为 22 文件，九语言各 25 keys；BOM/header/引用/保护 token/图像重建检查通过。 |
| 静态测试 | 8 tests PASS；同一个独立合同负例覆盖 71 个实际 subcases。 |
| 发布边界测试 | 5 tests PASS。 |
| 双构建预检 | 使用 Workshop ID `3812991990`，manifest 与 ZIP 字节可复现。 |
| 已覆盖 parser 子集 | 原执行者实际解析过的四项健康机制脚本、两项通知脚本全部 grammar/roundTrip PASS、零 diagnostics；当前六文件正文与原 corpus 逐一相同，复用原回执而不重跑。runtime semantics 仍为 UNSUPPORTED。 |

源基线 HEAD 为 `a4306b508dda9f7330585de50c2a6c544a9f548c`，当时包含已审阅但尚未提交的 1.1.0 改动。该 HEAD 不能冒充新候选的正式源码提交；[精确候选字节 manifest](build-evidence-1.1.0-2026-10-04-L0-A0001/candidate-source-byte-manifest.json) 记录 22 个运行文件及七份构建/生成/合同源码的完整 SHA。其 SHA-256 为 `dda598e932d941f5fd6284a03b11d938460974b8754b7abb5b04ba0844b2bc87`。

- 双构建预检 manifest SHA-256：`ee51f08328702cbd6f0f506f2daf38833c8d0ec677d0f8ef9d1cd9ed68577211`。
- 双构建预检 ZIP SHA-256：`188dbc90e2216f7b3cbf7dd051dd3d4073125ebc09989d3e074774e8c26a8315`。
- 外置原始 receipt SHA-256：`e0d8a227bdd059d0481295d42c9ba73d74f088f4e833728e5bc6ffd9d83900ba`。

这些哈希属于临时双构建的机器预检；本轮没有生成 cold candidate 或正式 staging，没有创建 tag，也没有上传。[完整机器报告](build-report-1.1.0-2026-10-04-L0-A0001.json) 和新 `build-evidence-1.1.0-2026-10-04-L0-A0001/` 保存实际 argv、stdout/stderr、原 parser 回执/corpus 和精确源码摘要；旧版本与所有外置 attempt 保留原样。

健康实际 CFixedPoint 精度、modifier 生效、供给者最低健康、保存重载以及正常通知界面须由新的 CK3 实机证据判断。1.0.0 的实机 GREEN 不能外推到新增健康或通知行为，语法通过也不能认证原生效果上下文。
