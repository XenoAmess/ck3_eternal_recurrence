# Review02 当前可剪内容与进入下一次 render 的准确入口

machine_id: `desktop-3fevhd2-1c74096080`；本轮新鲜观察与小文件 SHA 见 `TOOLCHAIN.actual.json`、`INPUTPINS.actual.json`；源码 `60de49f61d23b9c3437af4544c3f12bb28445429`。本轮只写约100 KiB计划，0 SDK／桌面／媒体／provider调用，0原片／MP3／PNG正文读取，不创建native run。

`EDIT-CANDIDATES.actual-a01.json` 是实际69段、58,406帧、32:26.867时钟的候选EDL：每段有既有精确音频引用、中文／英文文本SHA、段落帧范围、真实源卡ID和候选镜头ID。它可供剪辑分配直接读取；所有尚未通过的 `selection`、`capture_clip`、`movie_visual_artifact_id` 保持null。它**不能直接当已合格的 visuals 输入交给 bind_payloads**。

## 已经可以准备剪辑的内容

- 69段实际配音和23张1920×1080解释卡均有已封manifest；本轮逐条stat确认69个MP3仍在、尺寸吻合。没有重新调用TTS，不重做已有卡。旧 `FULL23-JOIN-PLAN.actual-a03.json` 已把69段真实文本／时钟与23卡接到真实xar-promo draft；这是先前的只读验证，不冒称本轮新build。
- R191有完整111.966秒／3,359帧原片与严格7条围城来源physical writer、实扣11。实体21槽1174→1163；cache1184→1173不能混写。候选用于C01-05、C03-01／02／03、C06-01。现在首先审这条原片，不为重复证明11人再开一场。事件精确PTS未校准，不能用原生UTC换算；82.982秒的wall暂停尾段不能当持续游戏推进。
- R12／R13实际动作已经闭合，可继续选旧R175的0–4／4–24／24–43.5秒与R176的0–4／4–10／10–20秒候选。R175右下通知、R174左上提示需具体审；这些都是待审区间，未授continuous clean。
- R173登船3金币例、R174独立未锁停止、R177独立海岸到达均保留其自己的候选ID。R173 raw没有Halt；R174不能剪成它的连续后态。R176 alternate终点在45秒原片外；用明确“后续独立原生读取”结果卡即可继续讲冻结的13日／8日，不能制造片内终点。Review01只作标清版本／主体的短历史附录。

## R09两条新镜头怎样并入

EDL已预留 `R09_FORWARD_NEW` 与 `R09_REVERSE_NEW`，分别覆盖库存／容量／权重、完整兵团、实际统帅和拆合军身份的相关段。前者只标Root本次预期R0192，尚不写actual；反向run尚未分配，不猜编号。

Root拿到两臂后，只需补该候选自己的实际run、完整小回执pins、原片身份、同暂停日期前后native字段及经过审阅的帧区间。不把旧R176的250或角色34232自动填成新样本；反向必须来自同一冻结普通baseline的独立正常冷载。镜头中完整展示split前→两支分别展开→一次merge→目标存续／源消失→全队列／统帅／stock-cap读回；只拍按钮ACK不够。未知结果不重投。没有实际pair／roleweights时C02-12继续是源码解释。

## 现存工具接线与本轮最小真实plan

最新正式release已独立重新查询为v0.2.1，wheel digest与requirements及已安装directURL吻合；版本和顶层、plan、validate帮助均本轮真实exit0。完整命令和正式API原文保存在本目录，不复用R192的probe作为本轮查询。

当前有两条已存在的项目接线：

1. 主仓 `war_ai_promo.episode04_review02:compose` 支持已保留capture clip及解释卡，复用 `capture_visual`／`plan_capture_render`；当前 `RenderOptions` 固定2560×1440。
2. 外置 `review02-real-dry-plan-a02/review02_png_composer.py:compose` 已支持1920×1080、23张真实PNG和69段实际音轨／ASS；当前只接静态方法卡。其 `prepare_png_run_a02.py` 和 `run_png_pipeline_a02.py`、精确argv均已存在。

本轮对现存双语ProjectConfig执行标准 `xar_promo plan ... --composer war_ai_promo.episode04_review02:compose --validate-only`，真实exit2：`Composition requires preserved production inputs in a native run`。`NATIVE-PLAN.actual.json`保留argv/stdout/stderr，拟定workdir没有创建。这个结果准确指出native输入保全尚未做，不是录制／音频／媒体引擎故障。不能把老source-draft validated改称native CLI已通过。

原FHD方法版新run、native-plan和build三个root仍未创建。现存 `ROOT-EXACT-ARGV.NOT-EXECUTED-a03.json` 给出真实prepare→native plan→build入口。当前Root容量明确render_reserved=0，所以本lane不执行prepare/preserve/build，也不隐含续期。

## 下一次render前只需完成这些具体动作

1. 选择交付范围：FHD方法审阅版可直接沿23卡／69音轨方案准备，不必等待所有未闭研究；它保持REVIEW及各段源码／条件边界。完整动态主片仍须真实关键操作和三方案结果，不以方法版冒充完成。
2. 对R191、R175／176和新的R09两臂做一次明确预算的连续画面审阅与边界定位。选出实际干净帧范围；原生事件PTS未证实就继续null，只用有来源的同场结果卡，不制造同步。旧45秒镜头通常短于单段约30秒，不能循环、尾帧填充或减速来覆盖整段；可按已有语句边界在卡与真实clip间切换，保留准确音频时钟。
3. 完整UI读数／角色页和同帧整条ETA＋首段读数仍缺；沿原R184三镜映射补最少镜头。若R13终点没有新画面，保留独立数据卡足以表达冻结稿，别为“连续抵达”伪造新镜头。
4. 闭场解冻后，对现有薄composer作最小接线：FHD几何和字幕避让使用项目配置；动态仍走已有 `capture_visual`／`plan_capture_render`／toolchain pipeline。不给静态FHD composer虚构capture支持，也不重写FFmpeg引擎。1280×720完整游戏框建议放1536×864@(192,0)，底216像素留双语，最终需真实画面核验。
5. Root独立准入输入archive与render容量，沿现存prepare保全精确69音轨／23PNG／ASS／production-inputs-v1，创建新的snapshot-bound native run，再完整validate config/run及标准CLI plan。旧建议输入64MiB、总run/work约3GiB仅是已有估算，CRF无硬sizecap；本轮未新增或采纳该额度。

最终visuals必须满足现有binder：每个原69ID恰好一个真实 `visual_artifact_id`＋`evidence_role=source-explanation-card`，或真实capture_clip＋continuous_clean=true；capture还要保留clip receipt、raw和control artifacts，精确匹配该段实际时长。随后才build/audit/pending review。人工完整1×和signoff继续单列。

本轮不重做研究总审计、不增加业务／动态信用、不改冻结口播、不承诺三方案赢家；所有小文件保护与容量仍受Root当前统一策略和23:17:53Z复核点约束。
