# 信仰引擎第二期 V8 清晰度修订交接

**最新图标修订补注（2026-10-24，`machine_id: 4-8e1c2f1861`）：** 已按用户反馈检查135张图片配置，统一19张卡片及62处引用，重编整片，原父wait退出0；全部19张修订卡的最终帧已实际查看。当前视频与完整范围见[图标修订制作记录](../../promo/ck3_faith_and_power/episode02/docs/production-v8-icon-consistency-2026-10-24.md)。完整人工1×听看仍待审；下列旧交接截点和准入继续保持历史身份。

**后继完成补注（2026-10-24，`machine_id: 4-8e1c2f1861`）：** 已继续完成六项修订并编码V8，29分30.93秒；全片自动检查与37处最终帧抽查通过，完整人工1×听看待审。当前文件、源码、失败保留和存储闭账指针见[正式制作记录](../../promo/ck3_faith_and_power/episode02/docs/production-v8-local-review-2026-10-24.md)。下文及原配对JSON保留07:09Z交接事实，旧准入不授新任务运行资格。

交接观察时间：2026-10-24 07:09 UTC；`machine_id: 4-8e1c2f1861`；交接人 `/root`。用户最新要求是温和收尾、交由同事接手，因此本轮停止新增制作，不启动配音、渲染或游戏。此交接覆盖信仰引擎第二期，不恢复此前已撤回的 Java 56 并发／G2任务。

V8 已保存研究、12段中英修订稿和首批7张新图卡，**尚未生成 V8 视频**。接手先读本页及配对[机器可读交接](../ck3-native-ai/evidence/faith-engine-episode02-v8-vacation-handover-20261024.json)，再读各 lane 的 `HANDOFF.actual.json`。不要从旧 V7 的闭场状态或旧容量卡直接启动新任务。

## 1. 六项反馈现在到哪一步

| 用户反馈 | 已保存成果 | 继续工作 |
|---|---|---|
| 另一回应左侧缺虔诚图标，两边不对称 | C01已从原作者重建；左右使用同一原版DDS、64×64图标与相同底片；Root实际查看通过 | N01与N09都引用C01，需在新Formal里同时换成新图 |
| 删除“这里没有另外一档叫允许”整句 | 新N03中英稿已删除整句 | 重新配音、按实测时钟生成字幕，不能只删字幕或留等长空白 |
| 两个“深思熟虑”与“忠诚栏”解释不清 | N08/N10/N13/N22/N23已改稿；首称“活动选项里的朝圣态度（游戏栏名‘忠诚’）” | 新配音与逐项图卡；原游戏UI保留原字 |
| 为什么本次只显示三个意图 | 主持／来宾候选池、每项显示条件、实机R32边界已入库，N15已改稿 | N13同名比较、N15逐项条件卡仍是分镜；不要把显示等同全部按钮可选 |
| 旅行费用没有每类公式 | N16已补2KW／5KW／10KW和公爵4/10/20、带技能3/7.5/15；29项映射已入库 | 制作逐步费用卡，补最终文字审阅、TTS和入片 |
| 账单数字太粗、太密 | N17–20逐数稿已保存，研究员已审全文数学与18枝顺序；改成先分项后汇总 | 费用逐步卡尚未制作；新配音、实测时钟、完整重编和抽检均待做 |

已完成的是这些素材与研究，六项修订尚未完成入片。不要将当前V7文件称为已修复的V8。

## 2. 直接使用的文件

外置路径缩写：

```text
R2 = C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02
V8 = R2/v8-clarity-20261024-a01
V7作者输入 = R2/v7-authoring-final-a09/V7.FORMAL-INPUT.a11.candidate.json
```

新稿：`V8/authoring/V8.CHANGED-12.SCRIPT.a01.draft.json`，66021B，SHA-256 `db18607ce67a3be27f4a5e3b78b9692fabed6f9f918bc9c91c007dba0839d11a`。配套可读稿 `V8.CHANGED-12.SCRIPT.a01.review.md` 为26686B，SHA-256 `034c14d476edccb73490d12e2005d7ac8db09787d5891649e5a2ce9a036b6c21`。Root已经实际读完12段中文；`root_approved=false`，未批准TTS，英文与最终逐句分镜尚未完整审阅。

改稿保持原33个稳定cue ID，只改 `N03、N08、N10、N13、N15、N16、N17、N18、N19、N20、N22、N23`。旧21段可以复用各自原音频与字幕证据。新12段不能绑定旧音频或旧provider request。

`V8/authoring/HANDOFF.actual.json`：8024B，SHA-256 `b7cc6f834999ea5ce2488d543605af73c985d24c59a940f444dd2aacc3edaaaf`。包含真实消费者、当前源码pin、未完成范围和原进程退出记录。基线33段轻量文本为同目录 `V8.BASELINE-33-TEXT.a01.json/.md`。

首批图卡在 `V8/graphics/`：`C01.symmetry-v8-a01.png`、`A02.terms-v8-a01.png`、`F01.terms-v8-a01.png`、`C07.stage1/2/3.terms-v8-a01.png`、`C08.terms-v8-a01.png`。精确pin与原版素材来源见 `REPLACEMENTS.FIRST-BATCH.actual.json`；分镜及未完成页面见该目录 `HANDOFF.actual.json`。**A02目前完成的是全表术语更新，三个单态度焦点页仍待做。** C07现有三图还是旧“总式／65算例／75算例”，尚未改成运算三阶段。

研究已原字节入库到 [evidence/faith-e02-v8-clarity-20261024](../ck3-native-ai/evidence/faith-e02-v8-clarity-20261024)，四份JSON分别为 `intent-conditions.actual.json`、`travel-costs.actual.json`、`activity-costs.actual.json`、`native-invoices.actual.json`；同目录另存12段候选JSON和后续图卡分镜JSON，方便同事直接评阅小文件。主索引见[既有智能体参考第150行](../ck3-native-ai/faith-and-power-episode02-agent-reference-12004.md:150)。这是原版来源研究和历史观测归纳，不是新的Native业务验收。

## 3. 接手必须保留的机制与剪辑结论

两个“深思熟虑”是不同选项：朝圣态度的 Contemplative 影响速度修正及主虔诚计算；意图的 Reflection 影响反思事件／行为。前者显示检查高级活动功能，可选还检查耐心／朝圣者／朝觐者；后者没有这组特质门槛。不要再称“意图和忠诚栏同名”。

原版朝圣主持者显式池是深思熟虑、行善、热忱，来宾显式池只有深思熟虑。行善显示检查高级活动功能、存活、未囚禁；热忱显示检查高级活动功能；深思熟虑无额外显示门槛。天主教、虔诚朝圣类型、人物奉献等级不参与这三项显示谓词。R32只证明实际显示三项，未资格化三个按钮全部CanPick；也没有闭合所有上游继承／追加场景。不要说全球永远固定三选一或四选一。`advanced_activities`到具体品牌DLC的映射本轮未闭合，旁白称“高级活动功能”。

旅行低／中／高是不同选项使用的收费类别。`K=max(主头衔等级−1,1)`；`W=0.75`仅在有准备充分技能时，否则1；费用分别为 `2KW、5KW、10KW`。本模型非部落制公爵K2：4／10／20，带技能3／7.5／15。部分政体另用国库或游牧分支，最多选2项。17项无直接cost定义不等于全旅程免费。

费用模型F0固定玩家、非部落制公爵、K2、早期中世纪E1、公式月收入I10、调整Q1、讲究排场、收费距离平方50000、雇佣登山者、无折扣。小额动态金币30、中额60；活动60、排场100、距离12、登山者4，**四项小计176**。仅开踏过圣路后活动30、排场75、距离12、登山者4，小计121，节省55。主管独立出发报价尚未闭合，不能填0或将四项小计称为原生完整付款。

18枝活动折扣顺序已在activity-costs JSON完整保存。重点是固定减项读取原始B或BE，倍率读取当前值；庄园减原始`.2BE`；动态最低额之后才有户部头衔的`.85`。灵性满足高级／普通折扣互斥，没有两种资格就不变。独立国王算例要明确换参数：玩家、非部落、B140、E1、I10、Q1，仅宫廷／赞助／庄园：`140→105→52.5→24.5→下限30`；错误把庄园前移会算出42。

实际账单和规则演算分开：R32是**基础60＋距离10＝70**，主管空位、未出发未付款；10不是主管费。R39报价182／初始扣182，R46报价128／初始扣128；底层收入／时代／资本距离等未全部读回，不能拿两场差价解释模型。顶栏14.8未绑定公式收入，0.10/月是未任命主管候选月薪，都不能塞进一次性费用公式。

排场正式中文名为**朴素、适度、讲究、盛况空前**，不要继续使用“卑微朝圣／适当／人山人海”等解释性译名。新稿N16仍可正向改成“低、中、高是不同旅行选项使用的收费类别”，并将“源码算例”改为“固定参数规则演算”，减少无关否定与实现术语；本轮未另起a02。

## 4. 继续制作的顺序

1. 重新登记任务、核机器ID、读取当前卷HEAD和统一存储策略，为新准备／语音／渲染取得新的有限准入。G51本轮额度不授接手运行资格。
2. 复核12段候选和分镜，补上上述N16正向措辞。N10每页只讲一种态度；N13左右比较两个同名选项；N15依次呈现三项及条件。费用N17–20每次只高亮当前运算，先公式、再代入、再结果，最后才同时汇总四项。
3. 在真实producer入口为12段生成新语音与句边界。语音准备见 `V8/voice-preparation-handoff.actual.json`。本轮实核最新正式工具链为xar-promo0.3.0，wheel SHA `f59c4b62b89297e2ff7bb7df4354fc88c6447fa6b1b7eade28de2bc1e6dc974c`；接手新run仍须重查最新正式Release。正式venv默认edge-tts7.2.8，须显式选既有外置7.3.1，不能静默使用默认安装。
4. 按新音频实测句边界重建完整33段voice catalog、字幕、evidence与visual clock。12段TTS脚本不能替代Formal要求的完整33段catalog；保持`result_voice_batches=[]`。帧长用实际语音，30fps并对齐16帧；不要机械平移旧SRT。旧素材与请求保持不可变。
5. 使用真正的 `episode01_formal.py plan/build` 链，`workers=1`，先计算document_budget再取得足额渲染准入。168限制是cue行数，不是cue内部visual_parts，不能以此压缩逐步讲解。现2040秒profile有固定guard，不能随意在JSON把max_seconds写大。字符估计约29–33分钟仅为估计，以实测为准，不提高语速挤进预算。
6. 全片新字节做媒体、PTS、字幕／音乐检查，实际抽看C01双图标、N03删句接缝、N10/13/15条件、N16公式、N17–20每步与汇总、N22/23奖励渐进画面。未经完整人工1×听看，不写human signoff。更新制作记录、README和本地选定视频路径后正常commit＋普通push。

## 5. 现场、存储与交接边界

本轮未启动CK3／Native／录制，也未切Steam或抢焦点；不由此追认Steam当前离线。当前制作仅用原材料。此机器按[永久本地交付偏好](../maintenance/machine-preferences/4-8e1c2f1861.video-delivery.json)交付，无需配置OneDrive。旧蓝色决策面板继续退役。

G51为本轮新签192MiB准备额度，只覆盖Source/Git8、voice104、graphics48、metadata16、scratch8、tail8MiB，未授权Game／编码。额度例外75,000,000,000B，原截止2026-10-24T12:40Z；不能自动续期。Root将在本文提交推送后唯一执行future归零闭账，实际结果读取 `V8/CLOSED-PREPARATION.a02.actual.json` 与 `C:/workspace/.codex-task-bus/storage/volume-C-current.json`；本文不预写尚未发生的CAS成功。候选与helper的精确pin见配对交接JSON；a01保留，唯一选用a02（更正“未执行TTS或编码”的事实范围，V8确实已生成7张PNG）。接手无论读到旧G51仍preparing还是后继closed，都须新签准入，禁止直接复用旧observer启动。

容量研究发现30–34分钟的完整build基础峰已约1.73–1.93GB，另加最长cue准备峰；旧1.6GB不能覆盖。实际预算须等新音频。候选回收本轮**0实际删除、0释放信用**：16组旧cache约927.5MB已有Native清单，R46 loaded存档与受保护canonical同SHA；其余引用／保护闭合未完成，R44两存档未完成SHA。详细计划在 `V8/storage/closed-derived-reclamation-a01/`，不能把候选量当作可立即用空间，更不能宽泛删目录或重置origin／ledger／addback。

限期保护到2026-10-30T12:00Z，由接手者届时按用途复核，不自动续期：V7唯一现交付片、V8当前作者输入／7PNG／分镜／小研究／必要原音和原图、当前仍用的原片与canonical母档、未闭问题最小证据。其他历史资产继续依统一策略分类。V7旧33段MP4可重建且新composer不消费，但仍要当前引用／保护与身份守卫后才可精确回收。

仍可读的旧V7片为 `R2/final-render-a01/sample/build-a03/native-run/derived/direct/episode02-review.mp4`，82,445,250B，SHA-256 `0cbcff0ccc9a7e6809fc61425952ef06c9e38a457bdb0d0b97382a0e2fd3b68e`，22:49.6／2560×1440／30fps。旧片技术检查通过，人工完整审片未做；新六项反馈仍以本次V8工作包继续修订。详见[旧V7制作记录](../../promo/ck3_faith_and_power/episode02/docs/production-v7-local-review-2026-10-24.md)。
