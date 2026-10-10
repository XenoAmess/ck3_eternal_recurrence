# 公共暂停读回收敛与 R55/R56 原失败（2026-10-10）

R54 的公共暂停失败来自两份独立采样短暂不同步：ACK 后语义 snapshot native9 仍为 paused=false，附加 heartbeat1056 已为 paused=true、ready=false；PID、generation、actor、owner 和日期均存在。原 host 第一轮即报 running owner stamp 不完整，没有等待原 deadline。231.430ms 后，真实 native10 才发布完整 paused=true 帧。heartbeat 不作为业务暂停真值。

本次 canonical 只改三个函数。仅 post-ACK 已知过渡形状允许继续只读等待；完整身份、日期、事件、revision/pump 单调、拒绝计数和原 deadline 都保持。只提交一次原暂停，移除原方法一秒后的额外重发；只有实际完整语义暂停后继帧才返回。起点拒绝计数必须原样保持，1→2 或 0→1 仍失败。Source14 只替换共同 host，native fd1f、queue04、正常退出 helper03 不变；旧 Source13、manifest、prepared 和 R54 失败不改。

已执行的一次必要回归使用原 R54 MCP 混帧和原 wire，经未改生产 driver 在内存中离线投影后继 native10，自然保留 rejection count=1。九个实际 host 向量及十项相关暂停测试通过，进程 exit0、4.423秒。离线投影不称为原 host 后继 MCP 回执，也不授实机或产品 PASS。精确候选、源证据和回归 pins 见[外置封交卡](C:/workspace/ck3-upgrade-20261010/common-pause-owner-readback-r54-01/ROOT-COMMON-PAUSE-OWNER-CONVERGENCE-05.md)；回归回执13003B / `b6c6e05f5450a7fecd51b7124a040a8ffb20a3234efb43bdd6d331b8e37079bc`。canonical host 251232B / `5f1edbfa927b7923fa4b33207758b4541cf32e2697be06787364ad086130c300`，Source14 host 234210B / `a20854002470e0f1b1c8f04d7889031560b28b9c89c510df950e72805697dea9`。

## c46 新派发路径的实际结果

| 原场 | 原结果及仍未取得的资格 | 实际闭场 |
| --- | --- | --- |
| R55 / a156 ordinary | 原十二次完整自然日推进及前十一天 no-fail 通过，第十二天报 async_reply_bounded_12_day_timeout。只能证明当时 pending 变量仍存在；原日志没有该时刻的 accepted/refused/pending 值、收件人旗标，不推测哪封卡住或队列被取消。 | run2/verify2、normal-qualified=false；retained OS0 为失败收尾，原 allocator/keeper0、三项 closure=true、CAS8151 done/resources[]。 |
| R56 / a157 PAM positive | 新 piety_level4 准备后，原 personal acts 与 personal mendicant fulfillment 仍各 false，业务步骤0；SF>=0 与 SF<=0 均 true，stock major10/minor3、两项 rite、legitimacy 等实际资格 true。没有进入发送流程，不能推断 PAM 负例必败或奖励已经验过。 | run2/verify2、normal-qualified=false；retained OS0 为失败收尾，原 allocator/keeper0、三项 closure=true、CAS8159 done/resources[]。 |

原 R55/R56 回执分别为[ordinary 闭场](C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/ordinary_async--a156/POST-RUN-CLOSE-05.json)3655B / `2f8924e956fd89cd74f034ff4c284bb9cb99a7066e126f0f1bcee6f03ae5f826`，及[PAM 正例闭场](C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/pam_positive--a157/POST-RUN-CLOSE-05.json)3653B / `dc13f2007dd030e990b57e6e2156138bb9727f4b6bd028e38b75f5e34f1b0594`。这些失败不被源码修改或正常资源释放冲销。

ordinary 仅在原第12天 FAIL 分支后增加只读诊断：原计数、pending 离散值、原 owner/actor、两目标的存在/存活/旗标/faith/rite，以及当前 private/stock validity。原 FAIL、12天、1接受1拒绝、计划和全部预算不变，不改变生产27文件，不触发回复。新夹具14048B / `f74346847cf63445502ea2702d6416bc40791538f840927f620304bfcae4d39a`，contract只改对应 pin。现有 parser 一次 exit0、0.302秒，1文件/0错误、corpus `0dc620fd4b311a9ec75eecdc6b247169f0a1ca1f9776f16ae4a94dd9f54f3242`；只授语法子集，current .4 semantic profile UNSUPPORTED 保持。没有延长等待、强制回调、删除 hidden 或猜测生产修复。

c46 官方[CI 38022831614](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38022831614)已实际 completed/success：66 success、20 条件 skipped、0 failed。该事实只绑定 c46；后续提交 CI 与实机资格另取实际回执。正式发布仍7/10（70%），QOL/RMTM/361 均未新增正式发布事实。

## 2026-10-10 Source14 已选定

后续未消费产品场唯一使用[Root选定mapping](C:/workspace/ck3-upgrade-20261010/root-source14-adoption-01/runtime.adopted-source14-native-fd1f-queue04-helper03-01.json)，12610B / SHA-256 `1eed7310a0c9314d54d9520d086ba1dce2f2d44d32988b91396c2bbf2f888f67`；共同manifest46927B / `bf326bb7005cd01ec482cbceaee02459dc2cf1400941b1dbe611c02905de60b2`，host234210B / `a20854002470e0f1b1c8f04d7889031560b28b9c89c510df950e72805697dea9`。实际增量物化exit0、7.620秒：6906文件copy2和sizecheck，6905行原SHA继承，只hash新host；native fd1f、queue04、helper03和全部能力合同不变。现有公共plan/Selection/hostCLI/prepare callable一次exit0、0.202秒，没有创建profile或启动游戏。旧Source13、manifest/prepared、R54/R55/R56结果保留，选择不授实机或产品PASS。

7个未消费prepared只创建新manifest-pin sibling；新ransom因observer fixture改变实际public prepare一次exit0、0.799秒，复用c46既有QA27且不重build。下一现场先admin→merit→ransom，UI/PAM−暂不消费待改信机制证据。正式仍7/10。

PAM 正例也只在原 startup FAIL 诊断函数补7个 stock只读原子：实际piety>=4、剩余slots>=2/==0、两个个人tenet membership、cynical/zealous。原setup/资格/奖励/计划/预算不变。实际现有 parse_clausewitz 对新fixture一次exit0（外层0.060秒），只授结构语法；回执3717B / `f303ad491b9dd0d5b6647aa0d12267fa5eea85fd4e11f2cd42368cd1fc109f45`。新fixture15423B / `af9e4892f1665a1024eeab808b669bef5017956803636e410b64c033a856a1d1`。R56没有piety/slots/membership原读回，不能把set调用当成功，或断言先祈愿、具体trait、DLC/player-data为当场根因。

## R55 原生持续资格自阻塞修正已采用

当前 .4 的真正 is_character_interaction_valid key/factory/RTTI/eval 已追至人类 actor+recipient 待回复查重；该匹配不排除自身，也不比较 definition。每日资格失效会静默删请求，绕过 accept/decline 回调。原 private is_valid 再查询 stock 完整互动时具有这一结构缺陷；原 R55 没有实例/计数现场原子，仍不声称直接观测到某一封的删除。先前 potentially_accepted 类误归属已在原生22卡纠正，不能继续引用错误路径。

已采用的作者 generator 从当前精确 stock definition 提取 is_shown/is_available/is_valid_showing_failures_only 原 body，保持所有纯条件和 scope；三处 authored dispatcher 在首次发送前同时核完整 stock 与 private 资格。合法 valid query 只有 recipient/interaction，没有 ignore-pending 参数；不改原版定义、不泛删资格，不改 AI 接受度、回复时限、回调、计数、转换/奖励后果或原12天预算。两个生产文件改变，其他25份保持；生成文件由 generator 产生，未手改。

UI/R33 来源支持增加精确两文件逆变换，旧单文件支持保留；固定旧证据pin、其余25exact，仅保留原defense23/reverse/final6范围。生成检查、完整static、两文件现有parser实际一次exit0，真实prior_core五个向量符合预期；精确pins与独立审查见[采用卡](C:/workspace/ck3-upgrade-20261010/resume-qol-02/r55-stock-ongoing-projection-01/adoption-02/ROOT-R55-STOCK-PENDING-FIX-ADOPTION-02.md)。原native机理卡8960B / `c444ce07c2f71901bf20fc85741573e919a2c8f72c55e9f214462c49d5c1b08c`，离线回执7156B / `287d871196280ea7774270c650d3e83a88c7fec236c4203959b46c712c89e4f2`。Root实际采用后，现有builder `--check`单次exit0（0.974秒），两构建27文件可复现，ZIP SHA `f64d06df5c6aefb5e26d9f74c38337bacdb91c77570eaef8158bcf941df23971`；未重复前述通过的静态和parser。修后真实1接受/1拒绝及PAM/UI均待新输入实机；R33/R48/R46不因全局指纹变化盲重跑。
