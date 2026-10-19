# 普通朝圣执行资格与七章固定声音

machine_id: `4-8e1c2f1861`。本页观察截至 `2026-10-19T22:12:00Z`（北京时间10月20日06:12），本地证据统一位于 `C:/workspace/ck3-faith-and-power-20261017/episode02`。生产通路、声音和后继拍摄分别记账，没有新的朝圣或领袖建制业务通过。

## 新生产DLL与实际验证

B5新DLL为[原件](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b5-a01/publish/xar_ck3_bridge.dll)，15,234,048 B，SHA `ad68db54342113267654c2f108e6a4db1db8af0178e232542db638a0f40667d6`。实际编译255个DLL TU、566个runtime TU及1个protocol TU；基于423ce封存输入和新增普通朝圣执行包构建，独立Read／Execution、现有ItemActions／Outcome开启，旧宴会Start、passive费用observer、旧FullCost／Gold／CanStart gate仍关闭。仓库默认执行gate保持OFF，公共case必须显式opt-in。

19个命名原生目标最终通过，共21次实际执行中保留两次RED及各自修复后运行。完整费用、planner、目的地、Start安全、生命周期、ON／OFF矩阵、只读身份和原生决议确认分别验证；Confirm正例保留真实reader／guards／action／dispatcher，owned memory与ABI leaf仍是明确fixture，未执行真实游戏callee。19个唯一EXE精确路径均有Defender实际读回，两项重编后再次核对。

同轮12份真实C++ serializer包和2份provenance经Python strict consumer、Driver和注册MCP执行37项：20 portable、11 execution wire seam、6 readonly seam，0skip、0failure、0error，实际进程退出0。外层frame／nonce为fixture，不冒充游戏pipe实测。

原首编缺少声明头失败已保留，只补 `ck3_12004_adapter.hpp`。fixture构建缺research include及Confirm链接闭包的原RED也保留；后者用独立小工程与真实生产对象闭包解决，没有重建第二份runtime。两项planner测试首轮失败是fake NativeString把 `activity_pilgrimage` 长度写18，真实为19；生产guard正确拒绝，只将两处测试改用literal.size()。先前RVA怀疑未被证实，不能作为根因。fixture CMake改动前后823条生产命令逐字相同，5,043份最终源码精确复核。

总回执为[B5闭环](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b5-a01/qualifications/CLOSURE.actual.json)，6,423 B，SHA `edb2029fec4ac47a3c127bc379d4804d78013c70e31acb1608f9188d07f07263`。该包只授予离线原生和消费者资格；下一场需重新读原生planner、实际报价、支付、活动与领袖后态。

## 两条拍摄流程已落源码

普通朝圣case使用D1原档，动态读取真实候选，依次打开pious planner、选择合法单phase目的地、读取完整十资源配置费用和最终许可，再一次Start。Start ACK未知时不重发，仍有限读取原生ledger、新完整活动身份和钱包。全case最多240实际日、480业务控制及128中断，保留120秒正常退出；初始、最终报价、Start后和7000／9001关键窗口都有Root拍摄协调点。取图后刷新同实例和第一显示项，再用当前revision唯一选择；实例或首项变化时零提交。

普通事件按当前原生显示顺序选择第一项，普通交互走合法左侧拒绝，先采样、后操作，ACK和旧窗口消失分开。7000结论加同人物9001归返事件链单列；9001也可能跟随活动失效，单独见到它或活动ID消失都不能冒充成功。未读取的归家坐标、全程旅费和背景净收益保留缺口。Root当前源码的16项流程测试、3项拍摄后刷新回归通过，均为合成状态／实际接口消费，尚未运行该场游戏。

精神领袖case改用R19真实原保存：Faith103／主Rite150、已合法采用Nadjaf32，原件69,030,069 B、SHA `de0f97b142ea88f13797d2f025380a52c5bab396b3d4986b8be6bf3ef653cc07`。当前读回前，是否仍无领袖、243金币是否足以支付都未知；不重新准备Faith、不补金币。只在实际无领袖、决议详情有效、两次真实报价一致、原版许可与可负担为真时，才允许一笔ConfirmOutcome。提交未知不重发，仍独立读取领袖、钱包和当前事件，再合法处理第一显示项；关窗不等于建制成功。Root实际11项入口测试及外置两项公共Selection消费通过，独立审计修复后PASS；实机资格待本场。

## 七章固定声音已实测

B7已完成后36cue：35次新合成、1次精确复用旧结尾；沿Edge TTS 7.3.1、Xiaoxiao、rate `-5%`，没有更换声音或重制前四章。21份原版来源SHA核对后冻结3,668字符固定讲解，未合成未来案例结论。

后36段净语音830.952秒、逐cue帧对齐展示846.4秒（14:06.400）。与B3前29段565.866667秒相加，七章65cue的固定讲解实测 **1412.266667秒，即23:32.267**；这是声音展示长度，完整七章视频尚未渲染。后续800—1600字符实际案例仍未写入／合成，按实测速率加约3—6分钟，全片仍以约27—30分钟为目标。

[B7声音目录](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b7-a01/authoring/voice-authoring-catalog.json)和[116组英文字幕](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b7-a01/authoring/english-translations-a01.json)已齐。全包实际分配5,886,608 B，未来TTS为0，后继小型元数据另计1MiB；[闭场回执](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b7-a01/CLOSURE.actual.json)SHA `4fc159495cf5c5426ee6f7358e4d8109041e06207c7528be8aef98e35a97b9c5`。两次provider请求前的启动拒绝保留；没有人工听审、无完整成片或用户签收。

[完整作者骨架](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/full-review-authoring-a01/README.md)已被现有FormalInputs实际读取：前29段精确引用已制视觉，后36段画面和24项必需结果槽仍待补，另1项特殊槽可选，`content_ready=false`。它没有使用样片例外绕过正式全片门槛，也没有复制旧声音或原片。

## 容量闭账与下一场

B5全部原进程已实际等待结束，Root按[精确计划](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b5-a01/qualifications/reclaim-plan-a01/PLAN-a02.actual.json)回收880份obj／lib，逻辑429,116,596 B、分配路径和430,904,624 B。原件现不可读取，保留所有DLL／EXE（含失败备份）、源码、配置、12包、日志和原RED；重链须重新构建，不能声称保留完整可读构建树。较早计划误用GetCompressedFileSize的logical值，a02已明确更正，实际删除只消费a02。

B1／B4另按8批、每批最多1000份精确清单，回收7502份可重建shadercache和与保留母档fresh SHA相同的恢复副本，分配路径和431,203,936 B；原片、截图、配音、成片、日志、源码pin及恢复资料保护。母档仍可读取，旧profile不再完整，已分别写availability补注；不能制造同名替代证据。执行见[清单与实际结果](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/profile-cache-reclaim-plan-a01/EXECUTION.actual.json)。B4的39.18MiB非视频子额超支仍按[原后检](filming-b4-and-pilgrimage-execution-20261020.md)保留。

B5重写入和B7 TTS预留已闭、按实际占用计入。B6于 `22:11:53Z` 新获640MiB raw＋768MiB nonraw，合1,408MiB；保守项目上界51,098,387,275 B，小于本机有效额51,177,672,294 B，余79,285,019 B。每take仍最多120秒／512MiB；第二take必须在首take结束后，按实际剩余raw至少512MiB才可安排，不无条件承诺。后台流量与恢复等待单列，运行中人工读回容量并预留正常退出；未声称自动容量管理已经部署。当前输入按统一存储策略七天内复核，无永久保护外推。
