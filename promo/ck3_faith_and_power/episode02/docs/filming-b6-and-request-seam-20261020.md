# 朝圣第二场诊断与请求接缝修复

machine_id: `4-8e1c2f1861`。实际观察截至 `2026-10-19T22:37:21Z`（北京时间10月20日06:37）。本轮基线为已推送 `f184cd6bd188a83a96b44581c979b04f0cda48ef`，使用[B5已验证DLL](production-b5-and-voices-20261020.md)，没有新的完整旅程或领袖建制通过。

## 本场实际结果

B6经公共prepare／allocate／preflight／run进入原D1保存，运行ID `4-8e1c2f1861--faith-engine--R0003`。当场直接审阅Steam离线原图与nonce图，窗口35→55→35位移和像素差证明新鲜度；桌面OS实际2560×1440。玩家31254、日期53144328、暂停且无事件，原档的钱包243金币／20000虔诚没有推进或补写。

本场原生候选包含两个合法且可负担的默认活动费：地点2577为70金，5965为100金；两者均明确 `journey_cost_included=false`。这是默认活动配置中的费用，不是整个旅行总价、两个最终stage5配置报价或30金币净旅费差。当前来源为[本场两报价回执](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/b6-event-analysis-a01/B6-TWO-LEGAL-ACTIVITY-QUOTES.a01.actual.json)，绑定epoch11432与本场checkpoint原件。五候选均合法，尚没有原版条件拒绝的实证。

首次planner read返回idle／stage2，但selected_pious和目的地为空、操作状态rejected；这不能证明界面已打开。随后只提交一次open，原DLL直接返回 `ok:false,error:typed_pilgrimage_request_invalid`，未取得领域结果或invoked后验。实际画面仍为地图。没有Start意图、Start、活动身份、日推进、新保存、最终配置报价或付款证明，原请求没有重发。

[54.233秒诊断原片](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b6-a01/captures/ordinary-pilgrimage-planner-a01/raw-gameplay.mkv)为60,975,804 B，SHA `b6096e33ccbc916d90fd6175cb9f740d85f53ff34382bacf6a5e0b724b988b08`，2560×1440 H.264、无音轨。recorder和ffprobe退出0；原图有地图tooltip，尚无clean-span或完整解码资格，不计为规划器镜头。

## 原因与有限修复

[精确诊断](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/b6-planner-open-diagnostic-a01/REPORT.md)保留native-wire第1320／1321行、请求ID和生产源码pin。原生产ParseRequest对query及submit均要求 `read_stage`，SDK只在query发送它；submit虽然向内部方法传了0，却遗漏序列化。原生在发布active请求、owner执行器与planner callback之前拒绝，因此MCP的通用错误不是原版CanStart拒绝，也不能当作费用不足。

修复只把read_stage纳入公共payload，保留原生必需字段和策略守卫。生产解析函数原字节块与真实protocol helpers组成小夹具，经真正NativeTransport compact encoder生成wire，实际23项通过：4个旧submit拒绝、8类修复请求接受、4个旧query回归、5个负例拒绝，以及本场实包缺字段／只补stage0的两项对照。新EXE精确路径有Defender管理员实际读回。[闭环回执](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/b6-planner-open-diagnostic-a01/native-validation-a01/exact-parser-a03/CLOSURE.actual.json)保留边界：这是解析源码资格，不是完整DLL执行、界面打开或朝圣出发实测；DLL未重编。

夹具首轮链接RED和归档JSON带空格、不符合实际紧凑wire的执行RED均保留。一次`/GL`输出使原8MiB子额实际达到18,167,139 B；停止后按精确身份计划仅回收两份可重建obj，分配路径和17,166,336 B。原8MiB额度不改写，a03另取2MiB有限额，最终实占797,896 B。不能声称从未超额或保留可读取的两份旧obj。

`22:39:52Z`，当前Root修复后SDK实际重消费B5原8＋4包，共38／38（21 portable＋11 execution＋6 readonly）通过、0skip。[当前SDK回执](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/current-sdk-seam-a02/run-a01/RESULT.actual.json)明确这是尚未commit工作树的精确输入，后继提交须重新核pin绑定，不能追写成原f184或B5当时已经包含修复。

## 并行修订与制作

旅程helper此前只选第一显示项，未消费现有专用事件策略。现在复用共享registry，优先当前合法显示的health.1015“叫医生来！马上！”，再用已有专用推荐，陌生项仍先采集后走实际第一显示项。只有精确来源、同一人物作用域和当前可用选项才可使用医生策略；旅行中该项不显示或禁用时保存真实缺口，不强选隐藏项。取图后重读当前策略和同一实例／已选native项，未知提交不重发。当前Root自包含10项策略与刷新回归通过；没有本场医疗事件或治愈事实。

后36段新增22段有明确来源的规则画面绑定，连同前29段共51／65段；14段实拍画面与24个必需结果槽仍待补，正式消费者实际读回仍为38 gaps、`content_ready=false`。[可合入绑定delta](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/full-review-visual-bindings-a01/README.md)没有复制媒体或渲染。

公共渲染器新增完整二期profile的逐cue prepared精确回收，保留160MiB scratch、全部encoded clips、原画质与24项必需结果检查。当前Root 34项消费者检查通过，仍没有完整视频。27—30分钟在70—80 cue、最长cue120秒的假设下，峰值约1.565—1.720GiB；实际案例长度变化须重算并单独准入。[容量公式与现实现边界](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/full-render-capacity-a01/CAPACITY.md)明确原833MiB候选单独不足。

## 正常关场与容量

Root通过原版GUI的原生callback正常退出：独立读回退出自动保存为false，直接审阅未勾选原图，确认退出只提交一次，随后独立保留进程观察OS0。原公共run退出0，原host实际Popen wait为1、native report保持RED且error为空；这反映open失败，不能改记GREEN。另一方面，正常退出资格、managed thread完成和cleanup均为true，keeper原父进程实际等待0，CAS于22:31:13Z释放为done／sequence12429。闭场Steam新图再次直接审阅为离线，桌面实际恢复1024×768。

[本场闭场与存储后检](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b6-a01/EXECUTION-CLOSURE.actual.json)记录4178文件、raw分配上界60,977,152 B、nonraw306,253,120 B、合367,230,272 B，分别在原640MiB／768MiB子额内。未来重型写入为0，小型metadata须另计后继准入，原ADMISSION不回填。当前失败packet、源码和母档仍为解决问题所需活跃输入，七天内复核；原片和派生材料沿统一策略复核，不无期限保留。

`22:40Z`前，Root另实际回收一期四份已由用户确认V7 final-a04替代的旧完整导出，分配路径和559,218,688 B。执行前重新核所有活跃V7／E02引用交集为0、保留配方和输入、四份完整SHA／Windows文件身份及无写者；当前V7、原片、声音、封面、工具和其余534份候选均未动。[精确执行与availability](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/reclaim-four-old-exports-a01/EXECUTION.actual.json)记录旧四原件现不可读取，没有创建同名替身；实际用途已被替代而提前到期，不能将保留配方当作原件仍存在。计划生成时的单份展开metadata曾超256KiB，已无损压缩核对后只回收该新派生展开副本，原超额与纠正记录保留。
