# 罗贝尔 A15 retry02：战争只读查询失败与后续修复

`machine_id: xenoamess-full-tower-eb9d2c1186`。记录时间：2026-10-20T22:40Z；北京时间2026-10-21。承接[Source26交接](../handover/2026-10-20-robert-source26-a05-vacation-handoff.md)。本记录不增加游戏验收信用。

## 实际进度与闭场

30年保存进度仍为 **5429／10950日、4753个已保存周期**，SAVE10480／count74，1081-07-31。G2仍为6／8；M6终态、M7实际H与广度未完成。1秒／日尚未达标，原全墙钟起点 `2026-10-19T03:26:49.420926Z` 保留，维护、失败和研究时间均未扣除。

本机证据根：

```text
P = D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep
N = P/robert30-v20261019-campaign01/runtime-a15-retry02
B = D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01
```

本轮R0014／execution `79533355-cde9-4bae-a5ba-b8395f95da79`，实际Game84988／出生FILETIME `"134370052880257844"`。FULL10543提交4个AUTO、3个MET；前三个普通周期4753→4756均未推进日期，第四个AUTO10550失败，pending周期4757保留。下一冷启动恢复SAVE10480，明确记录放弃3周期／0日，不重放10550，不清除旧HALT。

10550耗时11.8456624秒，原生步骤为 `query-war-termination-options-134217814`，明确拒绝文本为 `war-termination completion snapshot read failed`，不是等待超时。该错误不能证明底层getter执行或未执行，更不能证明外交动作完成。一次额外只读journal10551耗时约17毫秒、events为空；空journal不提供失败查询未执行或已经完成的证明。下一序号10552。

22:09Z实际闭场为Game强制退出1／Job0，SDK Queue1／Application0；不能称正常游戏退出或双零。OBS与publisher正常退出0，三个托管Task已注销，screen115以CAS7873→7874释放，R0014已标`completed-red`。

闭场索引 `N/ROOT-RETRY02-ACTUAL-CLOSURE-INDEX01.json`：14825B，SHA256 `a85b5098e7961828d50955c5b4d596d4202a13be37b0ec22cbb172f9c3bb4deb`。其中绑定实际Game／SDK／Task／媒体／屏幕释放、失败回执及连续性账本。当前Driver38413228B／history5278，SHA256 `fcc3c4abf1e98ab3e27754f737c6f935f654fed47fccfca94d0a556f4425f40d`；SAVE身份、尺寸、mtime与原SHA绑定未变。Driver完整读取与SAVE复制分别计数，不能沿用旧producer错误的“全部零读取”字段。

媒体1402326753B，既有SHA256 `cac3b8324baf1cfdc1341ae8b5485257f73d2df39cc9ab6bcca5e6306264ddfe`；闭场不重复hash媒体体。8个唯一PNG合计48952459B／实际分配48963584B，低于本轮64MiB。实际编码2560×1440／30fps；未改变桌面分辨率。Root此前亲审过原始地图帧、暂停日期和灰色栏；新的富化业务文本仍待实际审阅，不将等待画面算作富化验收。

## Source29修复范围与资格

战争修复仅匹配明确的只读拒绝，并核原request、Native31真实五字段失败frame、版本、步骤、战争ID及来源身份。完成材料缺失时返回`accepted=false`、`status=unavailable`、`war_termination_options=null`，保留拒绝证据；不把未知材料解释为空选项或无安全议和。相同来源、同日、同战争输入可以延后重复可选查询，继续其他合法军事和资金规划。写动作错误、身份漂移、未知结果仍保留原失败语义。

永久回归实际通过13项／81个子测试，producer与test两个完整模块严格类型检查零错误。回归使用仓库真实Driver方法、完整strategy及合成协议夹具，无D盘或原生调用依赖；未宣称Linux实跑。原生失败frame五字段来自实际Native31生成器。历史Driver末条只保存命令／错误文本，没有原始wire，合成夹具不得追认为历史抓包。

Root另用真实SEM10541直接验证新来源合同，并对源码派生拒绝夹具作JSON往返：`B/ROOT-SOURCE29-WAR-ACTUAL-SEMANTIC-CONTRACT-QUAL01.json`，2542B／SHA256 `5321f0204eb163b69d9bc3185c6aa6f1e36530f65318f59a77cfd967ca5c3b04`。零RPC、零日信用。

性能修复只将两处仅消费元数据的生活方式规划观察改为精简快照，省去完整命令历史的两次复制。真实Source28服务函数及当前仓库函数分别通过12组输出／异常／查询次数等价检查。5278条合成历史的一次复制对照只说明复制成本，不能分摊10546的20.58秒规划时间或证明1秒／日。优化没有改变战争选择偏好。

跨模块消费检查实际拒绝了性能候选01清单中的字段错误：`before_pin`／`after_pin`用了Git Pin，消费者要求`{path, bytes, sha256}`。保留旧清单和资格记录；生产者改为单一FileRef合同，并新增02清单及真实消费者验证。Source29固定版本、双导出和A17尚在准备，候选与静态通过不等于已部署或实机通过。当前master其他类型修复也不能自动计入这一窄Source29包。

并行工作包：战争修复与回归已完成；性能字段合同收口、Source29固定版本与双导出、A17启动适配及测试继续推进；Native32仅分析完成快照失败诊断。下一门槛是固定候选→真实消费者→完整启动前置→新鲜后台Steam离线回执→实际普通规划。未替换运行中的SDK或DLL。

## Steam与CI

本机22:25:15.348574Z后台重新确认Steam `status=offline`、`offline_mode=true`。PID165096／出生FILETIME `"134362593935766296"`／版本10.96.30.42，来源绑定SteamUI.dll；native当前用户字节两次为1，并核托盘状态4。回执 `B/STEAM-BACKGROUND-SOURCE29-PREP01.json`：2480B／SHA256 `b6e73f0d575f8c41f3acad99bc873e178016de6407b7640c74362cb4d47aff5b`。全程未截图、移动或激活窗口、抢焦点或切换模式。启动时仍需600秒内新鲜回执，准备阶段回执不无限续期。

公开master `ad11f3ef0792ca04c1a38a60542d6ee96992f301` 的[Official CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39504429916/job/118909684555)于22:23:19Z成功，39／55／94均绿；[Linear CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39504429996/job/118909685923)于21:57:57Z成功。CI执行机器`machine_id: unknown`；这些结果不提供本机游戏信用。

## 23:33Z 追加：Source29 已部署，A17 已启动

观察机器仍为 `xenoamess-full-tower-eb9d2c1186`。Source29 固定业务提交为 `d02d9907fa7a26ab60a6a75456fa276be78387c4`；双导出、BASE 及实际包的26项测试已通过，455个模块来源锁定实际src29。资格原件为 `O/source29-sdk-prep01/SOURCE29-ACTUAL-PACKAGE-QUALIFICATION01.json`，7643B／SHA256 `0a15e0f63a943e85ba7cb02e206cc5e75bbc50b49e4ccffd40c87d49f261b937`。本节追加当时准备状态的后续事实，不改写上文历史。

A17 的144文件已逐字节读回。首次落盘最后的 OuterBinding 检查因 Root 使用虚拟环境解释器而拒绝；没有覆盖144文件。随后独立基础 Python `-B -S` 重验全部原后验、47个入口、8个规范入口及实际 saved_basis，最后才创建 `O/A17-PREPARED01.json`，39396B／SHA256 `4bea2c7969dab35dcf2460577c65180503d17d440d24c383e6aeb280675b22ab`。完整原 main 在首次 ADMITTED 写入前的真实前缀另已通过，实际SDK路径指向src29。

本轮运行身份为 `xenoamess-full-tower-eb9d2c1186--vanilla--R0015`。Game PID83948，出生FILETIME为十进制字符串 `"134370118417378359"`，23:17:21Z实际创建；screen116由实际总线租约维持。启动消费23:11:12Z后台Steam离线正例，全程没有Steam截图、激活、移动或焦点操作。Game实际窗口及客户区2560×1440，用户桌面和前台窗口均未改变；OBS源与输出也是2560×1440、1:1、30fps。

Root亲审了冻结地图与录制合成帧：日期1081-07-31、暂停、右侧灰栏可见、无退役蓝窗和影片标题。首帧位于 `runtime-a17/recordings/dc26d8b0-e372-4e36-98bc-90b994371e94/FIRST-FRAME-ADMITTED.json`，2282B／SHA256 `7d447c85b6ca2d3758cea800b26fd95e802cb145a4802085f39f0a39ad7fa9d4`；原 `verify_segment` 实际通过。灰栏当前是等待文本，尚不授予丰富业务决策上屏验收。

真实 cold_owner 输入又揭示了外层 A08→A17 投影遗漏的冻结文件名。修复只把该唯一查找改回已部署的 A15 basename，不建立别名、不修改运行中的144文件。实际四输出双演一致；永久回归13项／90个子例和两个完整模块严格类型检查通过。最终生成器44761B／SHA256 `e9bbb74abfd0481a9c4da145e76cb7db0135b6dcb9ba2591c4715cc7e3ce9d13`，与原冻结图生成器4493历史身份分别记录。准入四文件按原顺序发布，gate最后；实际SDK已启动。SEM10552已提交一次，后继CAP10553与完整规划仍待实际结果。

保存成绩仍是5429／10950天、4753个已保存循环；新进程、ACK、首帧及静态测试均不增加成绩。G2仍为6／8，1秒／日和30年目标均未完成。原全墙钟起点继续保留。

工具包已普通推送为 `63af2d71ac5aaf88d7153a2f20885d1bc3e67191`，父提交c710，未强推。[Official CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39514460759/job/118943162943)的旧R06测试夹具遗漏新 `steam_offline_receipt`，step19失败，后续39／55／94跳过；[Linear CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39514460777/job/118943162907)通过。该夹具已迁移到真实共享ProbeWire的明确unavailable回执，当前生产5项测试通过；与共享准入core的9项组合14项通过。生产离线守卫未放宽，修复及新接线尚待后继提交的远端CI。
