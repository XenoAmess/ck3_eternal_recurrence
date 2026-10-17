# 第一期R0003：最终采用许可为false，原因正文仍缺

`machine_id: 4-8e1c2f1861`；CK3 1.20.0.4，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。查询截止2026-10-17T10:17:45.195186Z，闭场截止10:28:47.200534Z；本页实际编写2026-10-17T10:34:34.541991+00:00。小型[规划观察索引](evidence/faith-and-power-episode01-r0003/planning-observation.json)保存11份来源pin、精确帧、详情字段与规划缺项；原件根为 `C:/workspace/ck3-faith-and-power-20261017/episode01/`。本lane只读，无游戏操作。

R3使用独立新PID4876/gen1，runtime manifest绑定源码 `e54c8c7456dc865f3d42af9cc92a115fbf631eb5`、a14 DLL SHA `6a1cd648db5133a6e5f1af41ac16bc81467565a68a3e723976a4eb4926a507fe`。实际玩家15893、date_raw51394920、native:2/public revision3/native revision2，rite13/faith50。本场不能由[R2](faith-and-power-episode01-r0002-observations.md)或后合源码替代资格。

10:14:10.725428Z，采用入口实际绑定原版fallback receiver `1/3/1/3/4/0`，`native_dispatch_attempted=true`，开详情ACK先为verification_pending。10:14:11.350171Z独立原生详情查询才确认 `decision_key=adopt_holy_site_decision`、detail/root存在、三个actor字段均15893、requested/parameter/selected HolySite均32、parameter_and_selection_match=true。实际selected index14、candidate_count21、动态token361；21不是21个合法动作，index/token不能当成永久目标身份。

10:17:45.195186Z第二次查询上述值一致；`bypass_requirements_observed=true/raw=0`、`normal_requirements_legality_observed=true`，原版`native_can_confirm=false`，普通条件`normal_requirements_can_confirm=false`。这次取得的是**真实最终拒绝**，不是把R2灰叉或receiver绑定失败译成false。`decision_confirm_invoked=false`、`adoption_completed_observed=false`；没有Confirm，没有采用。

原生confirm tooltip只有泛化的“你未满足所有要求”，并非完整Requirements正文；`native_resource_quote_available=false`，结构化quote=null、action_ready=false。直接审阅owner提供的 `r2-frame-20261017T101424Z.png` 可见实际采用详情、部分要求和显示花费1000，但正文在屏幕中截断；截图前缀保留原名，不据其名称认作R2证据。不得把部分勾选/文字补成完整失败集合，也不能把像素中的1000写成已取得结构化原生报价。10:11:29的决策overlay截图明确展示“保留Hanafi与原版规则、仅正常条件通过才确认、尚未采用”；它是事前决策记录，不是业务后验。

对游玩智能体，当前可执行结论是：**不提交确认，保留目标和当前拒绝状态。** 下一观察口需要返回完整Requirements文本或结构树、完整性/截断标记、各条件真实scope/值/通过状态与AND/OR分组，并补报价/付款者/free/冷却。原生入口尚unknown，不猜ABI，不用源码条件模型代替当前全部原因。在原因齐全前，不能把改宗、换礼仪、征服或加虔诚指定为已经证实的修复方案。窗口/actor/参数、最终许可、完整原因和采用后态是五个独立进度项；原版caller与合同见[采用专题](holy-site-adoption-native12004.md)。

R3 `case-output/normal-close-result.json` SHA `5546a890b3b7cdd339fbed5ad53b162667dbedca1f32fa4df87634beced44f77`：正常GUI退出、原HANDLE exit0、normal_close_qualified=true；原public Popen等待0、keeper原父等待0；CAS11282于10:28:47Z完成resources[]释放。R1退出RED保持，正常收尾不等于采用业务。两take完整QA由producer单独收口，本页不结算媒体/clean/人审信用。

本候选只写小型文档和索引，不复制图片、存档或wire；按统一存储策略1.0.0，记录2027-04-15复核，应用核验后的patch按48小时派生期限复核。
