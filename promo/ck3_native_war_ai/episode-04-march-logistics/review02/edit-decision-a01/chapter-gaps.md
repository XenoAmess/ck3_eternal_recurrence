# Review02实际配音剪辑决策

作者机器`desktop-3fevhd2-1c74096080`；源码`c4992c304d196135d9590799d69ffb3c9f5510e6`。仅文本/时序/证据索引只读分配；58406帧，32:26.867。研究6/14、业务4/11、合格动态0/11；R180准备态不计信用。

| 章 | 已有SVG可做机制解释 | 新静态版式/旁白等待 | 共享现场任务 |
| --- | --- | --- | --- |
| E4-01 | 6/8段 | C01-03,C01-07；结果等待C01-07 | M_IDENTITY,M_R03,M_R04,M_R05,M_R07,M_R09,M_R10,M_R12,M_R13 |
| E4-02 | 12/12段 | ；结果等待 | M_R05,M_R06,M_R09 |
| E4-03 | 12/12段 | ；结果等待 | M_R03,M_R04,M_R05 |
| E4-04 | 11/11段 | ；结果等待 | M_R04,M_R07,M_R12,M_R13 |
| E4-05 | 10/16段 | C05-02,C05-03,C05-04,C05-05,C05-15,C05-16；结果等待C05-01,C05-02,C05-03,C05-04,C05-05,C05-15,C05-16 | M_R07,M_R08,M_R09,M_R10 |
| E4-06 | 10/10段 | ；结果等待 | M_R03,M_R04,M_R05,M_R06,M_R07,M_R08,M_R09,M_R11,M_R12,M_R13 |

15张D01–D15均为已绑定SVG源码解释卡，可立即进入独立静态素材制作；当前没有把SVG称作已保留的电影PNG。现有9卡生成器仅提供640–1280宽、最多3张preview，a04/a05生成器只输出SVG；需要由下一制作预算明确处理全分辨率still，不伪造一个不存在的SVG→PNG CLI。

69段音频均已实际生成。8段A/B/C方法/边界旁白（C01-07,C05-01,C05-02,C05-03,C05-04,C05-05,C05-15,C05-16）在完整比较主线中保持等待；可明确选作“方法说明”剪辑，但不能拿它代替新的A/B/C结果。其他冻结语句仅按其source/actual/conditional边界使用，不为新结论重合成声音。

先审已有素材：R174未锁Halt、R175锁后停止、R176后缀改道以及R173登船20.1秒候选。它们都没有continuous clean签核，不能直接填movie_visual_artifact_id。R13只缺45秒片外的alternate endpoint；R03研究已闭但正例在片外，若要动态例证只补自然正例画面，不重做已闭审计。R173三金币旁白不能偷换成R178一金币；R174是独立Halt重拍，不能拼成R173连续登船后操作。

缺研究先等条件：R04县界原因、R05低/零库存扣兵、R06实际ADD、R08军事实付、R09完整微实验、R10三臂均使用共享任务，不按69段分别开拍。库存满/资格false/钱包未知等已有负例不应重复拍成正例。旧TERM只作明确标为1.20.0.3的术语历史说明，不能给Robert/.4结果或新clean信用。

## 真实接线

`war_ai_promo.episode04_review02.bind_payloads(script, measured, english, visuals)`已存在；它要求69条唯一视觉绑定。静态输入需真实preserved still的`visual_artifact_id`及`evidence_role="source-explanation-card"`；动态输入需原capture importer合同的`capture_clip`和真实`continuous_clean=true`。本EDL中的null不是可喂入binder的假artifact。

现成wrapper是`python -m war_ai_promo.episode04_review02 --script <actual frozen69 JSON> --measured <production-inputs69.merged.json> --english <hashbound english.cues.json> --visuals <actual69 preserved visual bindings JSON> --output <NEW production-inputs.json>`，这里只给真实已存在的参数合同，没有执行。

项目composer入口`war_ai_promo.episode04_review02:compose`继续由正式`xar_promo plan/build --composer`调用；当前render_ready=false。字幕实际输入可复用`review02-subtitles-actual69-a01/attempt-a02`，EN为比例计时，布局随实际gameplay/still绑定再定位。没有新TTS、音频读取、raw解码、render或signoff。
