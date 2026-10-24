# 第二期 V8 清晰度修订：本地审阅交付

**后继图标修订（2026-10-24，`machine_id: 4-8e1c2f1861`）：** 当前选用[19张卡片图标一致性修订版](production-v8-icon-consistency-2026-10-24.md)。下文与配对JSON保留原a04交付身份；其33个可重建cue中间文件已在后继精确回收，最终视频保留，原109工件通过仅证明当时状态。

2026-10-24，`machine_id: 4-8e1c2f1861`。六项反馈已完成入片，当前交付为 **[V8《朝圣在奖励什么？》：29分30.933秒、1440p](C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/v8-clarity-20261024-a01/final-render-a04/sample/build-a01/native-run/derived/direct/episode02-review.mp4)**。全片自动检查及37处最终帧抽查通过；状态为 `ENCODED_REVIEW_PENDING`，完整人工1×听看与用户签收仍待进行。[双语字幕](C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/v8-clarity-20261024-a01/final-render-a04/sample/build-a01/native-run/derived/direct/text/episode02.bilingual.srt)、[中文](C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/v8-clarity-20261024-a01/final-render-a04/sample/build-a01/native-run/derived/direct/text/episode02.zh.srt)、[英文](C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/v8-clarity-20261024-a01/final-render-a04/sample/build-a01/native-run/derived/direct/text/episode02.en.srt)、[讲稿](C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/v8-clarity-20261024-a01/final-render-a04/sample/build-a01/native-run/derived/direct/text/episode02-script.md)和[机器可读制作记录](production-v8-local-review-2026-10-24.json)配套交付。本机沿用[本地交付偏好](../../../../docs/maintenance/machine-preferences/4-8e1c2f1861.video-delivery.json)。

| 六项反馈 | 实际成片修订 |
|---|---|
| 左侧虔诚图标缺失 | N01、N09同时使用对称C01，左右各有原版64×64虔诚图标。 |
| 删除“这里没有另外一档叫允许” | N03整句从新配音请求、实际字幕与讲稿删除；重新测量时钟。 |
| 两个“深思熟虑”不清 | N08／10／13区分朝圣态度 Contemplative（原UI栏名“忠诚”）与意图 Reflection，N10逐页呈现态度，N13左右比较。 |
| 本次为什么只有三个意图 | N15逐项展示主持者显式池及条件，另说明来宾池；R32仅证明实际显示三项。 |
| 旅行费用缺公式 | N16分别展示低／中／高 `2KW／5KW／10KW`、公爵算例及准备充分折扣；29项映射保留。 |
| 账单太粗、太密 | N17–20按公式、代入、结果逐步揭示，最后汇总；N22／23奖励也改为分步。 |

保留33个稳定cue ID，12段新语音，21段复用原音。最终使用74张焦点页（69张素材页加5张名称补注替换页），30个行内原版图标；N03另有五张原UI与DDS混合画面。引用游戏对象的图卡保留对应游戏素材，浅色底片保障原单色图标可读。技能DDS为原版180×60三帧图，按原GUI60×60帧规则提取未拥有／已拥有帧，无重绘或改色；来源、SHA与命令见外置 `graphics/source-icon-frames-a01/ACTUAL.json`。

机制与译名已核对[研究索引](../../../../docs/ck3-native-ai/faith-and-power-episode02-agent-reference-12004.md)。费用模型F0固定玩家非部落公爵、K2、E1、文化因子C1、公式月收入I10、Q1、讲究排场、距离平方50000、雇佣登山者：活动60＋排场100＋距离12＋选项4＝四项小计176；踏过圣路后30＋75＋12＋4＝121，节省55。旅队主管独立出发报价未知，不填0，不把小计称为完整原生付款。动态金币上限150C／300C与收入调整Q分开。独立国王B140算例明确换参：140→105→52.5→24.5→最低30，庄园减项按原始BE；错误换序42另作反例。最低额后才有户部85%，灵性满足两档互斥。R32基础60＋距离10＝70；R39的182与R46的128保留各自历史来源，未用两场差额证明模型。

英文最终按原版本地化纠正 Humble、Throng、Desire for Pilgrim Badges、Influenced by Ghosts、Clerical Justifications、Path of Fate、Hosting in Retaliation。同一技能 `clerical_justifications_perk` 在无地／游牧UI显示“高效朝圣者／Prolific Pilgrim”，五张后半费用卡补注此动态名称。此次只改N18／19／20英文，中文、音频、原请求与时钟保持不变；后继作者投影、全部字幕消费者和实际ASS已同步。原TTS冻结文本和历史错误材料未被覆写。

实际12段新语音合计925.584秒。唯一TTS批次产出12份音频／请求／句边界，但8段边界单位数不匹配使原producer退出2；保留原失败，调用既有 `boundary_fields` 离线逐句核对后形成reconciled回执，未重发TTS。新段按实测语音30fps、16帧对齐，旧21段保留显式阅读停留，不统一宣称旧段均16帧对齐。N20一个长实测句分成六个语义子句，时点为该句内按中文字数比例派生，不能称六个provider原生边界。完整33段真实字幕函数及字体布局通过，两行与安全区校验已执行；`result_voice_batches=[]`。

成片93,124,305B，SHA-256 `ab4513bbabf7455313f9394854aaafb7ed3e2b55580768fa3359bff18d37e7af`。H.264、2560×1440、30fps，共53,128帧；音视频有效时长1770.933333秒，容器1770.954687秒。视频首PTS为0.021354、末PTS为1770.921354，不写成从零开始。AAC双声道48kHz，平均−22.6dB／峰值−3.7dB；Quiet Courtly Tension配乐−17dB、淡入2秒／淡出8秒，五个独立窗口检查通过。

正式输入为外置 `authoring/V8.FORMAL-INPUT.a07.render.json`（768879B，SHA-256 `d3c18b50798360f84448207222f1521c81ce16d0f946ea0cd2640e0669e59734`）。真实公共 `episode01_formal.py plan/build` 链使用单worker、document预算1,776,223,450B；原Popen父进程于09:48:27.788832Z启动，10:25:38.072193Z实际wait完成、退出0，墙钟37分10.283秒，无自动重试。完整音视频解码退出0，全部帧PTS检查通过；真实 `xar_promo.project.load_document(check_files=True)` 校验109份manifest工件，258组字幕及删句／译名检查通过。37张最终concat帧实际逐张查看，覆盖双C01、N03、N10／13／15、N16公式、N17–20各阶段及N22／23；抽查范围没有明显裁切、图标不可读或字幕重叠。单帧抽查与自动信号检查不构成完整人工听看。

新增可复用图卡实现位于独立Java Maven build-tools模块，由既有Quarkus宿主体系的构建工具调用，不新增服务或Python生产模块。[生产合同](../../integration/clarity-cards.md)说明严格v2 record、边界校验、行内图标及PNG实际读回。默认命令行 `mvn` 原为3.9.16，本机在原Maven home更新到3.10.0，PATH顺序不变；实际安装路径仅作带机器和时间的回执事实。最终 `mvn -B -ntp -f java/ck3-control/build-tools/pom.xml -Dtest=ClarityCardsTest -Dck3.build.root=<外置构建目录> test` 实际退出0：75个主源码、93个测试源码以Java21、`-Xlint:all -Werror`编译，8项定向测试零失败／错误／跳过，已被既有ControlCi测试发现。一次误用根reactor选择模块的命令退出1保留，正确独立pom命令通过；未声称全仓CI通过。每次实际公共制作入口新查正式Release，当前实用xar-promo0.3.0与指定外置edge-tts7.3.1，完整版本／wheel／工具SHA保存在fresh-runtime回执。

精确渲染源码为 `d4cb39ed777554aeeed0454f458b0b4e7b9cc40e`，已推送标签 `archive/faith-e02-v8-render-source-20261024`；更早源标签 `archive/faith-e02-v8-pre-rebase-20261024` 保留旧身份。交付文档随后正常fetch／rebase／普通push，集成HEAD与渲染HEAD分开，不追认后继源码参与成片。原a01因N03图卡术语、a02因对象素材缺失、a03因英文译名停止，各自实际退出15和失败证据保留；a02曾完成AV检查，但没有升级为交付。当前a04为后继完成版。

全程未启动CK3、Native或OBS，未拍新raw，未切Steam或操作屏幕，不声明当前Steam离线或新增业务验收。此前取消的SDK／G2任务继续保持取消。

存储沿原origin和203行addback账本，累计addback10,989,906,936B不重置。此次精确回收46,488个旧cache／可重建cue副本等，Native分配总量1,351,152,432B，额度信用0；旧a02最终MP4和a03中间片现已不可读，原失败／来源／精确删除清单仍可查，没有同名替代证据。现用原片、音频、作者输入、V7交付片及一期当前片均保留。一次容量不足的新render准入被拒绝且未启动，后继另签额度；有限76.5GB例外统一复核于2026-10-24T15:00Z，不自动续期。G61已由G62的64MiB文档／Git尾项替代，禁止新增编码／TTS／游戏。推送后执行future归零闭账，最终实际状态读取 `C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/v8-clarity-20261024-a01/CLOSED-V8-PRODUCTION.a01.actual.json` 与卷HEAD；本文不预写尚未发生的CAS成功。限期必要保护到2026-10-30T12:00Z，派生48小时、视频30天、小记录180天到期按用途复核，外置 `RETENTION-V8.actual.json` 记录依据；不宣称已部署自动清理。
