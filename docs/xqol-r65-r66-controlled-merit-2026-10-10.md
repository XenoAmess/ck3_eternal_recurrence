# R65/R66 与贤能受控正例（2026-10-10）

当前执行范围仍为天朝二期以外的原十模组迁移，正式7/10；剩余QOL、重整河山、361既有0.3.1维护。Root采用本次两文件测试夹具修订，尚未授业务或发布通过。[范围](handover/2026-10-10-non-phase2-mod-migration-scope.md)。

## R65：首次真实等级诊断，旧正例仍GAP

R65/a166在clean `1e792f58fd8658a3d5d18bc00c560f567994c451`、Source17 runtime `171dca156f6e0f7b318e8c319c209164067975f4f2bd8fcccccc9fa32335e31a`、DLL0394下执行。原2步/root及独立贤能制帝国资格通过。唯一诊断于12:40:45.289471Z返回available=true、actor31883/title16982、ordinal0、extension存在、accumulated_raw=0、cap=3、native_level=0、tier=3、floor=3、meets=false。这是当前真实任命规则分支的等级比较；ordinal脚本名称与可消费merit balance的通用映射仍不外推。

本场candidate_limit=1仅作诊断，没有完整池信用；两法百万三相、恢复与GetHeir仍NOT_RUN。原版 `APPOINTMENT_MERIT_TIER={0 1 1 3 5 7 9}` 的低级自然爵位仍最低1，因此停止无效爵位搜索。未改变资源、开关或自然日期。

[R65薄件](C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/meritocratic_appointments--a166/ROOT-FIELD-RETURN-R65-01.json)：10422B / `1c1e023b06fd7fcca6607cd07d3439645db57e37ce0052116b7b8fb8133af2f8`。12:43:25Z trueCLOSED，run2/verify2，normal/OS0/native0、原allocator9307实际0、keeper0、CAS8367释放；原GAP保留。

## 原版来源与Root批准的夹具前提修订

本机1.20.0.4/build25734779的 `common/script_values/01_starting_values.txt:305-321,475-499` 默认starting_merit=0，只给非独立ruler或相应courtier分支初值。`common/on_action/game_start.txt:3505-3525` 调用的考试setup仅补标记，不能修复此等级；高丽holder历史也未另给merit。换另一独立皇帝或降低primary tier不能据此解决。已查的普通即时发展决议只有60、低于首级100且有冷却，没有已证零日自然升阶路径。

旧harness把零资格独立玩家与必须进入合法候选池组合成正例，无法覆盖减分功能。Root明确批准新的 `controlled-qualified-merit-positive-v1`：保留自然高丽holder、原政府/日期/帝国身份，在现有成功AI-holder guard内同一scope仅一次普通 `change_merit=2000`，记录SETUP BEGIN/DONE，随后保持原切换玩家及资格流程。原AI guard切换后不再成立，第二阶段不重复加值。原版 `10_dlc_tgp_china_values.txt:13` 的duchy_starting_merit_value=2000；普通标量effect例见dynastic_cycle_scripted_effects:204-206、imperial_examination_scripted_effects:408-414。

这显式修订测试准备资源，不能称未修改自然开局或将R65改判通过。真实当前rule等级/floor、完整引擎生成的合资格人类与AI池、两项原法律、OFF/ON/restored精确百万、原开关/日期/actor恢复和eligibleAI chosen==actual_successor/nativeconfirmed全部保留。等级是否实际上升仍待新场读回；SETUP日志不是资源状态证明。覆盖只计controlled fixture-live。产品27文件、shared adapter、host/native/runtime不变，原2 business steps/0 natural days与全部预算保留。

[冻结候选](C:/workspace/ck3-upgrade-20261010/resume-qol-02/controlled-qualified-merit-candidate-32/ROOT-CONTROLLED-QUALIFIED-MERIT-CANDIDATE-32.json)：4697B / `b1a8e29e0c62c50a2a2f12c3efb5ee09246c31b31a949901b6c6d3af58f766f2`；patch3952B / `67756bb55663f4893ba92da3dfce7234559489600d83918175d5a3b98bb68aa2`。仅fixture及case contract两个author文件，scope和准备值明确入合同，required marker追加且原前三索引保留。旧prepared、旧contract、R65证据原样保全。

唯一离线检查为既有open_kaishek generic corpus语法解析，exit0、约0.5秒、2文件/2561B，corpus SHA `0e3c351d86fcc083207af5147549bc3da634a1407650ee6e9fa240fa9c08ed14`。实际JAR artifact version=0.1.0-SNAPSHOT、来源commit UNKNOWN；当次checkout `522ac2d93bd6c534a6a242a227057de40a8977c1`不能外推为JAR build。未选游戏semantic profile，EXE目标SHA沿Source17为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，parser自身不校验EXE。语法与JSON/support pin通过不证明effect运行、等级或功能，未重复parser/构建。

## R66：旧窗口缓存导致ON查询拒绝

R66/a167的d_optimatoi1861/holder30599/law appointment_succession_law完整池含human29912及eligibleAI37981，OFF human raw=-92700000/scale100000，GUI -927。开关ON已由真实GUI确认，但仍打开的旧任命窗口保留cached -92700000；请求breakdown实际返回 `breakdown_total_differs_from_cached_native_score`。保留native缓存与即时getter相等门槛，不能归因为产品减分失败。后继需要合法刷新同title任命窗口，继续同场原三相及继任，不能只重复旧窗口查询。

[R66薄件](C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/administrative_appointments--a167/ROOT-FIELD-RETURN-R66-01.json)：12609B / `9235bb00dda5d31a44f33c0e25d37a5572aa2b1d483351853cfefbe9607faafa`。ON后未恢复OFF、第三池/GetHeir NOT_RUN。consumer自动退出，13:03:35.952988Z trueCLOSED；run2/verify2、normal/OS0/native0、allocator85407实际0、keeper0、CAS8387释放。旧RED和最终开关状态保留。

## CI与后继

`1e792f58` [官方CI38051721807](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38051721807) attempt1/static114212039916，于12:39:34Z实际终态66成功、20条件跳过、0失败；仅内存API读取，无新日志或artifact下载。它不授后继提交CI或业务信用。

三相验证绑定同现场title/law/holder，不绑定物理window pointer。每次toggle后合法重开同title窗口、取得fresh revision/reference再采该相完整池；同相分页中不重开、不换token，原getter/cache相等门槛保留。既有collector没有typed refresh入口，沿现有GUI及canonical mapper执行，无新runtime改动。

本次在R66真闭场后采用夹具与永久记录。新clean HEAD后继续现成PAM负/正、UI、ransom等独立用例；受控merit须fresh prepare/new state。公共运行时仍Source17，未消费输入只需其原有效绑定。正式发布仍需全部功能、真实上传、公开Notes全文、真实下载文件匹配与CK3加载、永久changelog提交推送；缓存不重做业务。
