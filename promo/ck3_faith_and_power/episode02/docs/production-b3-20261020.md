# 二期生产通路与前四章样片

machine_id: `4-8e1c2f1861`。本页截至 `2026-10-19T20:56:00Z`（北京时间10月20日04:56），来源为同机外置 `C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01`。这是实际构建、离线资格和配音进度，尚未授予新实机业务通过或成片签核。

## 生产 DLL 已完成

新生产 DLL 为 `native/publish/xar_ck3_bridge.dll`，15,038,976 B，SHA-256 `479514f2e30d42a7744579bfec2f0744da93bbf1b99f4a7d60d7479b277f0be9`。朝圣身份查询使用独立 Read gate，Start、完整费用、Gold 与 CanStart 动作依赖仍关闭；R5保留已选决议的条件和十资源只读报价，不打开建制确认。

真实生产编译为552个runtime TU、255个DLL TU，原构建进程于 `20:42:57Z—20:51:04Z` 执行并退出0。实际链接闭包没有fixture支持库。原始P18 flag提取曾因CRLF读取错误被configure前置检查拒绝；修正外置profile生成器后才执行本次构建，原拒绝保留。

| 验证 | 实际结果与边界 |
| --- | --- |
| Read／Start四组合 | 四次真实生产TU的宏矩阵执行退出0；ON为定义1，OFF未定义。包含专用permission的Install、Allow、owner／TLS／ticket、Uninstall，以及both ON的新旧槽共存。不是四份完整生产DLL。 |
| 其余原生执行 | router、真实reader／serializer、R5默认518 checks（含25项selected terms）、management 182 checks、GUI导航，共五次退出0；默认与management不相加冒充唯一覆盖数。 |
| 新C++包到Python／MCP | 本轮四个真实serializer packet经strict consumer、真实Driver方法、注册MCP，6项测试通过、0skip。外层frame／nonce仍是fixture，不是游戏pipe实测。 |
| Defender | 八个新EXE精确路径经既有helper登记，并有管理员fresh实际读回；不推广到其他路径或机器。 |
| 来源 | 3,759项native source／header／CMake pin没有漂移；实际EXE SHA匹配1.20.0.4 exact profile，Steam build为25734779。PE资源FileVersion的1.0.0.0不冒充游戏版本。 |

总回执为[原生闭环](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/CLOSURE.actual.json)，7,333 B，SHA `f18ab0735d2e2bb7bb8c47007504477a9064064fd5f7d613d8ca9c91912e4da0`；[独立审阅](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/independent-review/NATIVE-FINAL-REVIEW.actual.json)与接缝独立审阅分别保留。最初Python raw pin仅因BOM不同而拒绝，后继同时核raw及去BOM正文后才实际执行6项，不能把首次拒绝算测试通过。R5消费者已通过的B2资格只在源码同字节范围复用，不虚增本轮重跑次数。

## 前四章配音已实测

29段中28段新配音、1段精确复用一期免责声明，全部成功。实际为Edge TTS 7.3.1、`zh-CN-XiaoxiaoNeural`、rate `-5%`，未安装新provider。净语音552.120秒，含既有停顿和帧对齐后 **565.866667秒，即9分25.87秒**。

| 章 | 对齐后时长 |
| --- | ---: |
| 已有圣地，下一笔投给谁 | 102.933秒 |
| 同一份加成，真正改变了谁 | 131.200秒 |
| 类型、地点与目标 | 210.667秒 |
| 同一件圣物的用途 | 121.067秒 |

冻结样片为2,444字符；第四章一句按实际素材改为“物品本身的个人修正，需要另看完整说明”，差异账独立保存。第二章仍是规则算例，第三章是未确认的创建预览，第四章不能冒充个人装备后态。29段文本、provider请求与MP3的pin已独立核对；没有人工正常速度听审。本工具环境不支持音频输入，Root不能声称已经听过音频。

[实测配音](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/sample/voice-a01/measured-narration.json)为44,570 B，SHA `08dbc005355e23ed184e41bd6ce2db50a60987f5a927bd468d72bd14c391c08a`；声音元数据的独立审阅为 `native/qualifications/independent-review/VOICE-METADATA.actual.json`。实际约259.14字符／分钟与一期基准接近，支持全稿23.69分钟、补案例后26.8—29.9分钟的原预算；全片仍未实测。

样片沿正式FormalInputs与公共concat消费者制作，使用独立570秒／29cue上限profile，保留2560×1440、30fps、CRF21、3M视频上限和192K音频。只对显式规则／预览片段允许空live-result slots；正式全片仍保留原检查。为符合容量，单worker在对应旁白片段实际生成并通过probe后，精确回收本次可重建的prepared visual，保留原素材、字幕、配方、argv及删除前后回执。58项integration离线测试通过；没有用降低画质换容量。

新render run前于 `20:46:13Z` 实际查询官方latest release为 `v0.3.0`，wheel及安装direct_url SHA均为 `f59c4b62b89297e2ff7bb7df4354fc88c6447fa6b1b7eade28de2bc1e6dc974c`，version／help／build-help退出0。该事实只属于此次机器与run，来源为 `sample/voice-a01/fresh-runtime.json`。

## 下一场与完整朝圣的剩余依赖

D1母档用于只读筛选：先取得fresh玩家、日期、Faith／Rite／head，再读当前建立领袖决议的实际条件、币种、报价与拒绝。旧人物31254和日期只是标明来源的启动预期；本次原生首帧才是观测。若不合资格保留拒绝，不准备伪成功。当前公共入口与独立D1 adapter／queue的最小接线候选已完成17项定向测试；独立审计发现新测试依赖外置base，a02已修并重新17项通过，仍须应用后执行。没有建制Confirm或朝圣Start授权入口变化。

`2026-10-19T20:57:01Z`追加：Root已应用a02并给三份新脚本补BOM，从仓库正常位置实际运行17项测试全部通过，无外置source-root override。`native/qualifications/next-scene-plan-a02/TRACKED-TESTS.actual.json`保留实际argv／stdout／stderr。D1-REVIEW-01已由独立复审关闭；仍未prepare／launch，母档现场资格不由此追认。

完整普通朝圣还需要三块能力：专用opener／stage1／单phase目的地选择，当前配置完整十资源费用及最终许可，一次合法Start及独立活动后验。它们已分三路外置施工，不能只把宴会字符串改名；朝圣活动key超过旧16字节buffer，目的地单phase也不同于宴会双phase。成本分项aggregate不能冒充配置总价；完整十资源从已证布局读并以原生命名getter核索引，未知key不能继承旧true回退。最终拒绝tooltip缺getter时明确保留缺口。

该新增执行包初估8—14代理工时，构建与审阅约1—2小时，首场串行实机约1—2.5小时；这是剩余工作估计，不是完成时间。前四章样片制作、D1接线与这三块研究并行，实际CK3／屏幕仍由一位操作者持有。完整首版原目标窗保留为工程目标；后两章能否按时补齐取决于真实planner与场景资格，不能以只读身份包通过代替完整旅程。

## 容量与保存期限

B1、B2均已闭新写入。B3于 `20:35:35Z` 取得合计1,408MiB有限准入，其中native768MiB、sample640MiB，互不借用，至 `2026-10-20T00:35:35Z` 到期；没有自动容量预留部署声明。native闭环时约488MB，所有原构建／测试进程均结束；小型后继源码候选仍计入其子额。样片TTS阶段约3.43MB，小于48MiB阶段上限；渲染仍须用实际peak再准入。

统一沿[存储策略](../../../../docs/storage-retention-policy.md)和版本化参数执行；当前DLL、原片和配音是活跃输入，七天内复核用途，派生prepared可按精确配方提前回收。未完成全片或业务的证据不能被标作永久保护，闭场与后继场次须另记实际容量和资源释放。
