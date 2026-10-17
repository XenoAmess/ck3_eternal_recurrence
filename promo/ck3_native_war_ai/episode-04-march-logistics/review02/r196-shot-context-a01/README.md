# R196 实际入海与3金币：Review02镜头候选

machine_id: `desktop-3fevhd2-1c74096080`。历史R196来源`611bc985ae95f477dd7314df11f8602cd1e595f3`；本次只新增剪辑意图候选，不改旧a01、69段声音、composer或历史资格。

**首选C04-10，原音轨可用。** [rough输入](rough-inputs.candidate-a01.json)在R194候选基础上加入源帧`[1080,1783)`，即36–59.433333秒，703帧恰好匹配现有23.433333秒。已审38秒陆营、41秒船分别落在cue第2秒与第5秒；首句说入海时可以用这段状态变化作候选。这个选择不是精确事件切点，付款callback的encoded PTS仍为null，clean=false、approval=pending与REVIEW标记保持。

当前为 **3 rough／20机制卡／46关键画面pending**，`render_ready=false`。本次只移除C04-10的rough待配槽，未宣称其他R07镜头完成。当前composer同一raw只许一个窗口；[逐句映射](r07-cue-map.candidate-a01.json)中的备选C06-08`[1230,1967)`为41–65.566667秒／737帧，若采用须撤回C04-10并恢复其pending，再启用C06-08，不能两者同时用，也不换路径别名绕过。未制作分片或新增CLI。

R196唯一raw49,062,501B，SHA `7a302e9b674504c0705caa8fbaedf99abb349ee279bcf79825c916ecbe4831e9`；实际2369帧、78.966秒，wall82.824864秒，1280×720客户区区域、无音轨。全解码／PTS已由媒体owner完成，本包不再读raw或8张PNG。有限原图审阅记录只把营地→船视觉变化括在(38,41]，首尾画面日期为1067-03-24与03-27。所有原生完成时间与controller elapsed不代换成encoded PTS；这78.966秒也不是完整32日录像。

实际3金币来自**独立原生付款链**：[证据分层](boarding-evidence-facts.actual-a01.json)保存personal payer31254、Army18、海1032与SUB300000/Q100000，同一回调账户26010399→25710399，即260.10399→257.10399。不要沿用旧R173的254.48407钱包数字，不用UI260→257或两臂最终余额差定价，不由payer恰等于commander推“总由统帅付钱”。

| cue | 本次处理 |
| --- | --- |
| C01-02 | 原说明可保持，R196只是独立新case末段背景；不把三天片段当32日或三方案结果。 |
| C04-09 | 3金币实际支付句可按R196复用，但下令前费用warning／quote没有拍到，县损失也未由本片证明；整cue仍pending。 |
| C04-10 | 首选；个人账户、3金币及已登船都由本场独立来源支持。可不改TTS，用数据卡注明“本笔回调入口→返回”；若另改精确措辞只留候选。 |
| C05-13 | 记账规则可保持；登船SUB、generic ADD与未知维护费分别列，不给费用排名。 |
| C06-08 | 互斥备选船面板背景；只重申登船3金币，军事维护仍unknown，不能解释免费。 |
| C06-10 | 本场没有Halt；抵海空route不能冒充旧未锁定停止。保留R173/174独立故事与镜头，或另版改中句，不能偷换旧音轨。 |

[Root既有R07-v2决定](../../../../../docs/ck3-native-ai/evidence/episode04-r196-r07-boarding-pair-12004/root-research-decision.actual.json)采用同S0两次fresh、各32个exact自然日、day31实际入水及个人SUB、双臂正常闭场的现行合同。原v1≤7日且避经济结算依旧false。原production replay在正常闭场前生成的false标签原样保留；较晚Root整体判断另引，不能重写旧回执。该决定不授影片clean、完整1×或signoff；费率通式、quote、commander因果和实际军事维护费归因仍未取得。

[真实只读plan](plan.actual-a01.json)只验证新候选与现存69段输入的结构，不创建run/workdir、不调用媒体/provider。本目录来源与机器字段见[小pins](source-pins.actual-a01.json)；绝对C/D路径只定位来源机器，跨机须映射并重新核输入。下一步是有预算的连续内容审阅与实际片段选择，保留原片精确身份及全部pending；本包不复制raw、PNG或音频，也不延长[存储期限](../../../../../docs/storage-retention-policy.md)。
