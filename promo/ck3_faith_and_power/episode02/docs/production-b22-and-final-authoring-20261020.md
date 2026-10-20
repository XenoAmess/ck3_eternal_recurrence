# 麦加实际结果与88段制作输入

`machine_id: 4-8e1c2f1861`；本页观察截止 `2026-10-20T15:49:38Z`。仅记录本机本场，不外推其他机器或新局面。前轮朝圣及失败边界保留在[上一轮记录](production-b21-and-p3-20261020.md)。

## 麦加实验实际证明了什么

B22/R0013 的 Q21 骑士 reader 在游戏内可用。人物15893、10322同一暂停日期的总量分别为104%、129%，麦加named项均为+4%。对本信仰的麦加26只提交一次降级；独立后态确认eminent由true变false、虔诚4250→3250，完整十资源报价与实际付款均为1000虔诚。原确认ACK未自行授予业务成功，采用后续独立查询确认等级和付款。

即时独立后态的两人总量和named项均未变，`site_attribution_observed=false`，缓存刷新时间未证。本例可以展示真实零差分，不能据此断言降级无效，也不能把总量当作单座圣地贡献。源结果的`required_slots/E2-A1/closed=false`保持原样：[原adapter结果](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b22-a01/live/4-8e1c2f1861--faith-engine--R0013/case-output/mecca26-knight-controlled-result.json)，SHA-256 `986f008c28c90061d75ba2868b09078593757becb9c6fefe47c1962fa3e860ce`。

随后一个自然日触发历史人物事件，第一显示项确有切换玩家效果；实际人物15893→41436。这段已混杂，不并入原人物刷新、钱包或属性后态。离线分析与下一场准备并行完成：[源码分析](knowledge/historical-char-creation-1-source-analysis.json)、[原生实例与独立后态](knowledge/r0013-historical-character-1-observation.json)。共享registry补齐1.20.0.4的九scope精确变体，复用既有第三项保持原人物策略；旧八scope与1.19记录保留。推荐第三项尚未实机执行。七项便携消费者通过，新消费者strict通过；四个生产模块仍有38项既有类型诊断，新增0项，不标为全模块strict通过。

两段原片各74.966秒，原录制job和probe均实际0；每段只审实际PTS5、35、70三帧。第一段仅确认报价画面，未授予拍到Confirm的信用；第二段先见3250，随后事件遮挡。两张原版PNG可用于报价与即时后态，最终换人截图不用于原人物比较。[媒体审阅](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b22-a01/media-review-a01/REVIEW.actual.json)不授连续clean或完整人工听看信用。

退出采用原版GUI，保留句柄于15:29:56实际取得CK3 OS0；原host于15:30:01退出1，公共run原Popen退出0，两者分列。最后确认距离hold约227秒，未达到本轮自定300秒余量，不追认满足。Root在确认游戏和host退出后于15:48:51前写现keeper的STOP；keeper线程实际结束、无failure，原allocator于15:48:52退出0。屏幕释放及后继准入仍须引用实际CAS回执，不能由这些退出码推断。

## 制作与后续执行

最终选择为65条固定讲解、原B12装备1条和22条新案例，共88段；旧73段投影不作为新完整输入。当前A1三句旁白实际33.816秒，展示35.733秒，MP3完整解码与测长通过，尚未人工听审。[实际声音索引](C:/workspace/ck3-faith-and-power-20261017/episode02/case-voices-b25-a01/batch-a1-mecca3-a01/measured-narration.actual.json)已接入作者输入，保留前段“智慧之地外交”与新麦加骑士实验的明确过渡，不改65条固定声音。

原FormalInputs元数据验收已实际通过当前69段子集：65固定＋B12＋A1三句；必需结果槽2/24已绑定，22项待补，`content_ready=false`。这个比例是结果字段，不能当作影片制作百分比。当前仍只有70段24:33.600可播放预览；88段约28—29分钟属于编辑预算，尚未新渲染。

下一场优先补一次完整普通朝圣，分别验证出发、抵达、结算、活动终态和独立当前位置；不为固定事件ID或正奖励重刷。原生位置DTO仍未绑定，采用已有角色窗口与原版头像位置提示作独立视觉观察，方法单列。遗物个人装备／供奉两冷臂、普通／major完整双报价、同世界一次H2建制及H3只读状态并行准备。H1/H2新显式串联caller的7项消费者和修改范围strict检查通过，公共prepare与实机仍未执行。

容量修复只把录制服务整场上限896MiB改为2048MiB，raw512MiB、四段、总300秒及实际整场占用守卫保持；3项定向消费者和修改谓词类型检查通过，不是新录制资格。后继使用新的完整准入、当前源码绑定和公共prepare，不回写旧B23被896MiB限制拒绝的原失败。已有Q21 DLL继续沿用精确来源证明，不因离线Python改动重编原生矩阵。
