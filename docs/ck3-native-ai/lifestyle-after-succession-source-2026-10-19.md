# 自然继承后的 LIFE2 阻塞：来源与修复边界

记录机器 `xenoamess-full-tower-eb9d2c1186`，来源 `python -B tools/ck3_live_run_id.py machine`，汇总 UTC `2026-10-19T09:05:17Z`（clock工具读回）。本节是关闭文件与源码审查；没有追加 Game/RPC、读取活 Driver/SAVE 或修改运行中的 SDK。现场只读诊断由 sole runtime 执行，不能把以下源码与合成测试视为已经部署或实际诊断结果。

## 已关闭的实际证据

封包父目录为 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01`，原关闭响应位于其同级 `robert30-v20261019-campaign01/runtime/p37-responses`。

`c7-lifestyle4102-blocked79/FROZEN.json`：14237B，SHA256 `25f8cd84a5d4305d3ed3cd0c41d106d370d334698e67c15e1443a3394bb4a8bd`。其 `p37-responses/4102-1-result.json`：52237B，SHA256 `896f6c4aa7658a7bfc9bf1f4c2380c445faf94cd8284ccb5081cde46ced4a484`。

实际 AUTO4102 `status=blocked`、`selected_step=null`、`phase=lifestyle_native_query_unavailable`；查询状态只有 `current_state_unavailable`，显示的 `native_error=null`。当前 actor40526、episode `native-40526-1bec95182886`、Native3134/public2716/date53188032。没有 LIFE focus/perk 业务提交；内部只读查询可能已发送，不能把 selectednull 解释为零 RPC。

实际 Python 源固定于 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/sdk-v20261019-candidate/src06`，提交 `8e1e59f073f239d266f5b59f57c65b5645658512`。其中 `xar_autoplayer/lifestyle_formal_consumer.py` 12395B/SHA256 `cbb2320a59789a85d8e1c46712a201e0815f64a0e3ccdc7b2cd65aa165f31621`；private transport 41204B/SHA256 `8f4e8346a3f55468dc4654d8fb188196ea358fec4062fd4c736e7b41010535ac`。

已关闭3895 root 行 79406B/SHA256 `41359f78d0fe3f73b8a1c7ca8efdbe2dde356d93afe992abc67cb1bf4068d122` 不含年龄/成年资格；4100 是战争条款查询。肖像、历史年龄与这些 root 行均不能证明4102的合法未成年负结果。

## 确定的错误信息丢失

`player_lifestyle_private_transport_v1.py:592–597` 把失败的 LIFE2 原返回保存于 `state`，包装为 `current_state_unavailable`。消费者只取外层 `native_error`，因此错误字符串丢失，并将所有失败显示为“LIFE2/LIFE4没有绑定”。这不能证明真正发生了 FrameMismatch；combined 在该分支尚未读取 LIFE4 focus。

消费者的最小改动保留整个原 `lifestyle_query`，并从命名的 `state`、`focus` 组件保留原 `native_error`；没有改变原 block、身份、资格或动作。生产文件13054B/SHA256 `6299037d745ddfc7b11a6ce889924eb2236033dd05a694bf30a80baaba32fcd1`，已由 Root 提交 `0f42b331`；当前src06未因此改变。

合成回归 `test_lifestyle_native_negative_binding_v1.py` 与原 `test_lifestyle_formal_private_consumer.py` 一次执行55pass/2.04s，包含 getter错误、超时、旧actor/Native材料、native-illegal、缺失查询与原战争路由。它们不授实机资格。

## 现成教育焦点查询的真实能力

现有 Driver 方法 `query_child_education_focus_private_v1(child_full_id=当前玩家, target_key="education_stewardship", expected_revision=当前public)` 调用现有 `private-query-child-education-focus-v1`。公开 MCP 没有对应的独立注册工具；generic execute 并不因此获得未 advertised 私有步骤权限。

原 Python transport SHA256 `8a97b27c594128ffe38e011431af00928172b4d842671b798981390fc198a247`，19253B，与实际src06字节相同。它校验 exact.4、当前 controller/episode/date/Native、原 public 和前后帧，完整保留原 DTO。

仓库 Native 源的 `bridge.cpp` 在同 LIFE 编译宏内路由子焦点查询；`child_education_focus_private_12004.cpp` query 分支先读取当前 focus，再执行 validator。只有 submit 分支调用 dispatch。`ResolveChild` 校验 full-ID/liveness，没有禁止 subject 与当前 controller 相同，也没有在此入口要求后代 roster。现有 DTO 返还独立的 `current_focus.available/presence/key` 与 `source_frame`；`native_legal` 只回答请求的教育焦点能否改变，不能代替当前焦点事实。

`ck3_12004_child_current_focus_readonly.hpp` 双读等价29194B0的两个 nullable link 与实际 focus key，不要求 focus→lifestyle。仓库源6771B/SHA256 `22d6c72bbf2823ae7932d51d764f3a1585cd74bf035a1bbd6e811de9656657e6`；Native handler21060B/SHA256 `b6f10c36a15c5260fe7c5c39210e25a08b0ea3ab1edc03ffc096eb6941c8fb83`。这些是仓库源审 pin，实际 Native26 编译闭包须另核，不能以 master 源冒充运行 DLL 的来源。

Native owner 后续报告已核 Native26 `INPUT-PLAN.json/frozen_sources/16` 指向 `p26-all-lifestyle-frontier01/jobs/51cd4348df2f/child_education_focus_private_12004.cpp`，字节与上述 handler 相同；实际 `build/jobs/4a0208e0fd98/attempt01/COMPILE-RESULT.json` 编译此叶，argv含 LIFE 宏=1。`frozen_project_header_versions/702` 指向同 SHA 的 readonly focus 头。此处如实区分 owner 已查的编译元数据与本执行者直接核的源字节；最终 DLL/依赖闭包由 owner 的独立小回执提供，不能仅凭本段授实际调用资格。

Native owner 于 UTC `2026-10-19T09:06:11Z` 补齐 source/object 可达证明，同机器ID（来源 Native26 QUALIFICATION 与实际 compile receipt，再由当前机器工具匹配）。Native26 根为 `D:/codex-ck3-demos/2026-10-19-robert-v20261019-native26-performance01`；bridge receipt `build/jobs/769c280bdfe8/attempt01/COMPILE-RESULT.json` 14692B/SHA256 `921f6c5154c1a5da9570cf41bcdf2a5f026d1af8d8f1b7022b95a8b34ab54ee3`，child receipt `build/jobs/4a0208e0fd98/attempt01/COMPILE-RESULT.json` 11015B/SHA256 `7c1bd05ae8786ee9abd63e3dfa8720957710e471ac10fcdfbf088c594541e752`。二者 new dependencies 实际消费各自 P26 frozen readonly header，均为同6771B/22d6c72...头；实际冻结 bridge17968–18000确在 LIFE 宏内处理该 query。不能把仓库当前行号当冻结行号。原 CMake 单叶 pin 仍 unknown；实际 argv/source/object/dependencies 已有独立证明，不补造 CMake 来源，也不把尚未执行的原生查询算通过。

原版 `common/focuses/00_education_focuses.txt` 12235B/SHA256 `f24d82c5d6d349bcd60f481ef10ccf711550f2738d2efa4f3b7829047e70ec5d`，五个 `education_*` 定义均为 `type=education`。实际.4 LIFE reader `ck3_12004_lifestyle_state.cpp:387–412` 则要求 present focus 有可读 lifestyle；源码41578B/SHA256 `04fd5101bb889915181a649bd7dd52abde34e7b4360848a47247212b4d6efb33`。这是离线阶段的来源候选；其后取得的实际读回与原4102未保留的内层错误须区分，见后文。

## 隔离的有限诊断

`tools/g2_saved_campaign/lifestyle_current_state_once_diagnostic_v1.py` 5954B/SHA256 `5f0d172a30be21051b3e6117edb7a5da1445e11c7c0117cd3e15b24fc151cd35`：由现有 factory 的实际 Driver 注册，按新 SEM public 调原 LIFE2 method 一次，保原返回与前后帧；先占 `.started.json`，失败不重发。2个合成测试一次执行2pass/0.51s，包括 foreignactor 在查询前拒绝。

`tools/g2_saved_campaign/lifestyle_child_focus_once_diagnostic_v1.py` 4882B/SHA256 `6f98b72081dbc677c5bbf256431cc270894b7fbadc1a17b8e4777e2f04df8781`：仅前一原 LIFE2 诊断同机器、同完整帧且错误为 current_lifestyle getter/key failure，才准一次原 child-focus query；不修改第一诊断叶。3个合成测试一次执行3pass/0.49s，wrongreason 在查询前拒绝。物理 Game birth/DLL 资格仍归 runtime 的已批准 warm factory，不由 PID 猜出生身份。

当前不能从未知读错误生成合法不适用，也不能把所有 LIFE 模块永久关闭。若后验同帧证明当前玩家实际持有来源明确的教育焦点，可据此限定成人生活方式不适用；仍不推断年龄、已解锁 perk 或焦点更改合法。若只剩可选只读模块故障，可另以完整身份与帧证明、无未知写 pending、有限重试与原因债务保留 unavailable 并继续其它合法运营；本包尚未改变该策略。

## C8 实际只读后验与最窄业务修复

同机器，runtime 唯一调用4106的观察 UTC `2026-10-19T09:18:06.316078Z`，关闭原行 `p37-responses/4106-1-result.json` 3899B/SHA256 `6813b0fc6929f2c5b174630c66019430de324804afed1a4e7415e24bacf4407d`。原 method 返回 `native_query_unavailable`，exact error 为 `native_lifestyle_current_state_current_lifestyle_key_read_failed`，request `life-query-8b23ff8acb584e85af6bb9673ce9117d`。前后 Native3136/public2/connection6/date53188032/actor40526/episode完全相同。这次实际错误属于 lifestyle key 读取，而不是泛称绑定失败；不将它倒填为4102已观测的内层错误。

Root 条件授权的4107唯一只读调用于 UTC `2026-10-19T09:18:16.562237Z` 完成，关闭原行5488B/SHA256 `4ae9cc87100123704eea156f31541f8e8355cc583e9efd7814f42d4607d94e6b`。前后仍同一 Native3136/public2/connection6/actor/episode/date。原 DTO 中独立 `current_focus={available:true,presence:present,key:education_intrigue,unavailable_reason:null}`；当前 controller 与被读 subject 均为40526，原 source_frame/context、exact.4/EXE绑定完整。至此有实际当前教育焦点事实，不能再把这帧的成人 LIFE key 失败一概写成未知 FrameMismatch。

同一原 DTO 的请求目标 `education_stewardship` 返回 `status=unavailable`、`education_definition_missing`、`native_legal=null`。按源码执行顺序，current_focus已读，但 target definition 缺失令查询在最终 validator 之前返回；没有提交命令。这是教育焦点目标 lookup 的独立剩余缺口，不能当作请求焦点非法、全部候选为空、已取得更改权限，或读取当前焦点失败。

最小业务修复不改 Native、Service 或 Driver：

- 新 `lifestyle_education_focus_scope_v1.py`：将来源已审的五种教育键与 exact.4 typed query、当前 actor/Native/date/episode/public/paused/alive 绑定；独立 current_focus 可用才产生 `adult_lifestyle_not_applicable_current_education_focus`。不推年龄或 LIFE 写权限。
- 原 private transport 仅遇两种明确的 lifestyle getter/key错误，才调用现成 child-focus只读方法最多一次，比较前后帧并保留原错误与原 DTO。其它错误、超时、未知键、缺失focus或旧帧仍保持 unavailable。
- 原 consumer重新核该事实及来源review，并与当前 root scope的玩家/Native匹配，才保留原 baseline合法续行；不提交成人focus/perk或教育focus写。每个后继完整PLAN重新取当前事实，没有永久actor、年龄或禁用LIFE开关。

生产冻结：新 scope叶4332B/SHA256 `28db68a630239803c14908e72e571aa7cbedd8f56429abc1f1d8a42864157476`；private transport42857B/SHA256 `dafc1c198928b3f68fa88976f1431bf29c5abb00e20a6c437a1b7792f3f6a47b`；consumer14386B/SHA256 `d971e1737acd5654a6fdd9c7219a3982a6bce3de44b0c95bc0fac735922b7df2`。源码通过不代表C8运行中的src06已经采用；后继实际采用由Root/runtime另记。

仅复制必要实际输入的小投影 `tests/unit/fixtures/lifestyle_after_succession_4106_4107_v1.json` 2702B/SHA256 `75f01d2699f1306c8f2b8c9b93edfb8f773b32020a19258831e8cbf21563b425`，含机器、UTC及两原行SHA，清楚标明离线重放不授实机修复资格。15个新回归与7个错误保留回归、48个原消费者回归一次执行70pass/2.57s，命令为 `python -B -X utf8 -c __import__('sys').path.insert(0,'ck3_autonomous_player/src');__import__('sys').exit(__import__('pytest').main(['-q','-p','no:cacheprovider','ck3_autonomous_player/tests/unit/test_lifestyle_education_focus_scope_v1.py','ck3_autonomous_player/tests/unit/test_lifestyle_native_negative_binding_v1.py','ck3_autonomous_player/tests/unit/test_lifestyle_formal_private_consumer.py']))`。测试覆盖实际闭件投影、target missing与当前focus独立性、旧actor/Native/date/episode/public、未知focus、其它原生错误、前后frame变化和来源review漂移。

## C9 暴露独立 opening 消费漏口

同机器，C9在 UTC `2026-10-19T09:36:26.484951Z` 的实际4113行13866B/SHA256 `7221d70fb28946fa0515f04b005b3a50ba4c623bdf9e172397d536e91eced177` 再次 blocked。其前后 Native3137/public2/date53188032/actor40526/episode相同，stock已由新代码返回 `education_focus_not_applicable`，但独立 opening gate仍要求 formal.available 与成人stock状态，记录的失败谓词仅 `formal_status_unavailable`、`stock_status_unavailable`。第一轮普通战争只读成功并不资格第二轮opening，此失败不能被前述70项纯消费/回归通过覆盖。

最窄C10补丁只接 Service的初始LIFE专用段：重验原 formal/state的exact错误、完整教育proof、前后同帧与无LIFE pending后，仅结束该episode的初始成人focus prerequisite；保留 `completion_kind=education_focus_not_applicable`，不授焦点写或checkpoint信用，然后调用原完整 `_plan_turn_internal()` 一次，重新处理普通候选。未知、旧帧或pending仍RED。summary同时保存教育原DTO，避免再次丢内因；4113旧summary未保完整教育proof，因此测试复用未改写的4106/4107 Native3136原事实，不把它重写成3137冒实测。

精确两hunk在 [C9→C10来源包](evidence/lifestyle-opening-education-scope-C9-to-C10-2026-10-19.json)，6072B/SHA256 `a36c8fe7c08dc9ed35a888cef304279647a72081629a926c01af00141b5a3a8e`。从实际C9 Service867972B/SHA256 `5b46e116e7a65c753eac099a82f79fcb8a3a25112a5dcf5e55e534a521f239d1` 只替换两唯一片段，候选870245B/SHA256 `7d83d149c842642fec321aeec06a4b4a21af5ec0f91c2c656b7af72ae22efabf`；不能复制含其它M1变更的整份master Service。

UTC `2026-10-19T09:48:53Z` 汇总：以该准确C9+hunk候选在内存中加载真实Service，三个相关测试文件一次72pass/1.33s。新集成用真实 `Service.auto_turn` 穿opening、完整普通规划入口及合法受支持root-query派发；ordinary选择/Driver为明确合成fixture，未提交LIFE动作。未知focus、跨frame、pending均无ordinary选择/派发。全部combined调用点已核：Driver透传、普通consumer、共享opening入口，以及最终selected-focus的严格写守卫；后者的保守RED不因本修复放宽。此时已交harness/runtime准备，尚不将C10源码资格写成实际推进通过。
