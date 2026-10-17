# R194 进入69段混合rough的最小候选

machine_id: `desktop-3fevhd2-1c74096080`。R194/source `d7135ca3bf40c33c2d5416242ce844077f1e8cbe`。这是新增剪辑上下文候选，原稿、旧a01、TTS、composer和历史actual回执均不改。

[rough输入](rough-inputs.candidate-a01.json)保留原R191 C03-01，再给C05-06加入R194原片源帧`[0,857)`，对应原音轨28.5666667秒。当前为 **2 rough／20机制卡／47关键画面pending**，`render_ready=false`。这只是明确选择的原片前段，不是精确Split／Merge事件窗口。`event_PTS=null`、`continuous_clean=false`、`approval=pending`与REVIEW水印保持；缺镜头时build继续拒绝静帧兜底。

[11cue逐句映射](cue-wording-map.candidate-a01.json)保存原语句与实际provider句边界、原音频引用和每句的R194用途。C05-06原声可保持；C02-11/12可按实际库存与source边界复用。C05-07仍是假设100/50/50、6000/4000，不能换成本场75/175压力实测。C05-09“实际人数”建议新版本改“显示值”；C05-14“新增一人”建议改“一比一角色记录”。

若将C06-05的“这次”改叙R194，使用[a02文字澄清](wording-clarification.candidate-a02.json)作为新稿候选。旧R176“同角色先后当新队与合后原队统帅”不适用于R194：本次选中原队75，另拆新队175，新队统帅36445，合后原队统帅34232。新文字没有配音，不能沿用旧35.6秒充当新音轨时长；保留旧R176稿和明确旧来源卡也是合法选择。

映射中的备选C05-10取`[1055,1887)`，长度832帧／27.7333333秒，起点样本已为合后251，适合作合后背景；它与首选互斥。现有composer同一raw只许一个窗口，不可同时装入两cue，也不能换路径别名绕过。后续多段使用需另有已准入的真实分片与回执或薄composer适配，本包未制作分片。

R194原片71,202,833B，SHA `763bbbec18149543f7ed4d36dc761aa8fe258366037d2727390a25f64d18f1e4`，实际3467帧／115.566秒／1280×720／30fps。六张原尺寸样本实际审阅仅支持面板250→75→251：frame0=250，frame189／6.3s=75，frame1055／35.167s已251，后续38.1/66.633/115.533s样本也251。controller/native elapsed不等于encoded PTS，不据此标精准动作帧。

typed GUI与业务证据确认public93/native85合后cache251／physical250；头像、数字和图标不替代native身份。独立[Root业务决定](../../../../../docs/ck3-native-ai/evidence/episode04-r194-forward-split-merge-12004/root-research-decision.json)授R09研究7/14、业务5/11，动态仍0/11；有限样本、callback／birth PC、continuous clean、人工完整1×与signoff各自记录。原片不是已批准成片素材。

[实际plan结果](plan.actual-a01.json)为原外置source-only标准CLI `war_ai_promo.episode04_review02_mixed_rough:compose` 的真实exit0原字节，验证69段结构，未创建workdir/run或调用媒体/provider。保留当时的外置argv与路径；复制此回执不代表在本仓新目录又执行一次plan。[小来源pins](source-pins.actual-a01.json)绑定来源字节及机器／时间。输入中C/D绝对路径只定位这台机器的来源；其他机器须映射自己的真实输入并重新核文件、版本与运行条件，不能继承本机事实。

下一步是对R194连续内容进行明确预算的审阅，定位真正动作、所选对象和后态，再选择可用帧范围；本目录只保留候选和来源，不补造clean、人审、精确事件PTS或新声音。资料期限继续按[统一存储策略](../../../../../docs/storage-retention-policy.md)复核，不新设永久保护。
