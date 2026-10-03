# 测试计划

目标：CK3 `1.20.0.3 (Crozier)`、Steam build `25652598`，EXE identity 见 [upstream.md](upstream.md)。按用户2026-10-03明确修正，真实游戏验收仅用简体中文，其他八语只做基本格式／键／占位符规范检查，不设英文或其他语言实机门禁。R0001简中费用已执行；R0002英文调试原样保留，不作为简中签核，完整简中矩阵待验。

## 离线预验与 L0

- 原始来源 manifest 与 import diff；descriptor 禁止上游 ID、remote ID、开发 path。
- 结构 parser、BOM、重复顶层 key；九语言只做编码、header、条目语法、重复键、完整UI键集与占位符格式检查，不设非简中文案语义、术语或翻译完成度门禁。
- 三档成本／威望等级、AI 双闸门、目标 tier、法理目标集合及当前战争存在性门。
- 所有引用的原版 trigger、effect、script value 与 CB metadata 字段对照 exact-build 文件，不凭名称相似判定兼容。
- `open_kaishek` 对支持语法／确定性子集先执行；报告 commit、profile／version、EXE SHA、fixture hash、实际命令、结果与不支持项。战争引擎不在覆盖范围时记明原因。
- 明确 runtime allowlist；从源码生成两次 manifest／ZIP 做逐字节复验；docs／tools／fixture 和 upstream ID 不得入包。

## 隔离实机矩阵

统一使用 production projection、外置 fixture、一次性 `-userdir`，与其他产品串行占用 `ck3-screen:acquired`。启动前取得当次新鲜 Steam 离线画面；双源枚举 CK3 进程；保护真实存档／tutorial／设置／订阅缓存。启动与退出只管理本 attempt 的自有 PID。

| ID | 场景 | 必须读取的结果 |
| --- | --- | --- |
| DJC-01 | 无 mod 基线／仅维护版加载 | 主菜单／地图可达，产品解析诊断 0，准确加载 runtime hash |
| DJC-02 | 三档威望不足及刚达到 | 原生 CB 列表／目标 tier／资格 true-false，不能仅靠命令 ACK |
| DJC-03 | AI 同等级与资源充分 | 三档 `can_declare_war` 不可用，AI 无进攻入口 |
| DJC-04 | 威望或虔诚不足、恰好足额 | 不足不宣战不扣款；成功扣款读取原始差值，区分一次CB费用与原版条件性附加后果，不能把CB预览当作操作总扣款 |
| DJC-05 | 公国内多独立领主、法理外土地 | 同一战争参与方精确集合；领土集合与 war goal 一致 |
| DJC-06 | 王国、帝国多参与方 | 三档各至少一次真实生产宣战、胜利和战争结束 |
| DJC-07 | 胜利后领土 | 目标县的 owner／liege／title、目标外县不误转移、战争退出 |
| DJC-08 | 白和平／战败／无效化 | 资格与终结路径、没有意外领土转移、资源／休战副作用符合合同 |
| DJC-09 | 主攻击者／防守者死亡、保存重载 | CB 与参与方可继续或按声明失效，存档不残留阻塞战争 |
| DJC-10 | 评论所述并发战争 | 本场胜利后另场参与方与 CB 仍一致；可结束，无永久负分不可选状态 |
| DJC-11 | 原生自动军队 | 读取集结／计划／移动／战斗阶段；无法证明时记录限制 |
| DJC-12 | 简中战争确认与结果 | 原生 GUI 文案、成本／参与方可见；raw key 0。其他八语仅基本规范检查 |
| DJC-13 | 其他已维护 mod 一起加载 | 不覆写无关 top-level ID；回归基础三档借口 |

功能断言只来自原生 MCP／桥接、paused snapshot、生产路径 fixture marker、资源和头衔状态；OCR 功能断言数为 0。截图是补充玩家视角。直接执行测试 effect 可搭建场景，不能替代原生宣战／执行和平条约入口。

每轮报告包括 argv、解释器／依赖 probe、源码／runtime／fixture hash、CK3 EXE／build、开始结束时间、日志增量与全部诊断、断言、保护资料前后 hash、进程退出读回、失败分类和 artifact 路径。明确区分 environment、harness、产品 RED 与 NOT_RUN。

## 当前外置脚本矩阵

`tools/gen_acceptance_fixture.py` 当前已输出 `C:/workspace/two-mod-maintenance-20261003/de-jure-fixture-R0005-CN/`，仅1066罗贝尔1128真人入口自动触发。R0001加载的fixture namespace／未使用变量RED及最小修复见 [永久记录](fixture-initial-load-red-2026-10-03.md)，旧输出保留。三档各执行胜利／白和／战败，共9场，72个预期PASS及一个DONE。读原生 can_declare_war、战争侧、生产CB宣战回调捕获在确切war上的目标变量、县持有人与战争退出。目标断言有存在性guard，捕获缺失明确FAIL，不把fixture预设目标写成生产读回。d_capua用capua／napoli，k_sicily包含玩家apulia，e_italy用roma／firenze，vannes作为目标外观察点。

R0002英文调试第一格8项通过，第二格 `duchy_white_peace_native_eligibility` 实际FAIL；clean LoadGame已丢弃此前GUI白和后态。新夹具只在每格恢复县后取消玩家向当格实际主守方top liege的定向停战，记录取消前后原生 `has_truce` 条件；宣战资格失败立即停下，不再强制开战。诊断TRUE／FALSE不计入72条语义PASS。来源、失败、修复与静态回执见 [完整记录](matrix-native-eligibility-red-2026-10-03.md)。R0005-CN仍未实机，真实停战读回与九格简中矩阵必须由新attempt取得。

此fixture通过生产CB与on_action，`start_war`用于搭场，`end_war`调用实际结算。它没有覆盖正常宣战扣款、原生议和合法性、并发战争、自动军队、低威望、重载；根执行者另补原生UI／MCP。`verify_fixture_log.py --log <debug.log> --contract <fixture-contract.json> --report <fresh.json>` 只证明markers，完整报告仍须绑定runtime／EXE／日志诊断／受保护资料／进程退出。

## 发布验收

新 Workshop item 与上游 ID 分离；公开标题、描述与可见性读回；从干净目标取得订阅缓存并精确核对 manifest；Change Notes 冻结文本的 entry ID、HTML 解码／换行归一后全文、字符数、行数与 SHA-256 匿名回读。上传完成后立即恢复 Steam 离线；changelog 永久提交／推送 master 后才能宣布发布完成。
