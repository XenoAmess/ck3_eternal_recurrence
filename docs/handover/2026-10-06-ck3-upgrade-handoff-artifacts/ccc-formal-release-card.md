# CCC 1.0.1 正式发布最短卡（备料；实际 .3 与发布待定）

维护目标 **3804807463**；上游 **3596263413 禁止作为目标**。上一公开版为 1.0.0，tag `celestial-commerce-corruption-v1.0.0`，commit `dc91dc1f0a1abd733d274382833a0ab9b3cdb51f`。既有匿名 baseline13 于2026-10-04T19:06:24Z精确核到旧entry `1789875616`：完整显示正文367字符/11行/867B/SHA `bdf4dbc9e7e81993f2a9a10ae15dbd7e67ed6538628606980b0927bd86c0b489`；只去一个展示尾LF后为原冻结366字符/11行/866B/SHA `31bfdd2617fb05cdcc39fb87ded0e6a80d05b9692f211b917b388f53a64d1bea`。基线原件复用，无新HTTP。

现有完整Notes与描述均可直接复用，没有缺失玩家文本。Notes canonical `workshop/change_notes/celestial-commerce-corruption/1.0.1.txt`：**1708B / 1244字符 / 17行 / 无尾LF / SHA `2d74578e9feca3dac77e2efca4791c8cb90c469ad8145b6586d244e3302e0ae3`**。描述3194B/SHA `f5591e6357add8f55dd049705cf2664ce7baa13e7288fb9c7611ddf13fde1957`。本包只读核 canonical22与op16候选22逐字节相同；不重build/static/pure/precheck，不给当前R0002/a75未完成业务信用。

本卡默认新的PUB为 `C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01`；Root先创建其 `formal` parent，旧attempt均不覆盖。全部以下命令由Root执行，本agent未执行。正式stage目标和重建目标必须原先不存在。

1. 只有本次源业务实际通过（原core11/两FAIL0、真实生产决议Confirm/退出事件、三年冷却及实际GUI/日志边界），正常关闭并释放screen后才推进。补源验收事实到现有README/专题，Root统一提交并推送；**CCC正式builder要求整仓clean**。Root创建并推送真实 `celestial-commerce-corruption-v1.0.1` tag到该实际HEAD，不能填未来hash或复用非tag candidate。

2. 正式build与manifest verify；已完成的双构建不重跑。侧车名字由staging basename决定：

```text
"C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe" -B -X utf8 C:/workspace/ck3_eternal_recurrence/tools/build_celestial_commerce_corruption_release.py --release --workshop-item-id 3804807463 --output C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01/formal/mod_celestial_commerce_corruption
"C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe" -B -X utf8 C:/workspace/ck3_eternal_recurrence/tools/build_celestial_commerce_corruption_release.py --verify C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01/formal/mod_celestial_commerce_corruption --manifest C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01/formal/mod_celestial_commerce_corruption-v1.0.1.manifest.json
```

3. file-only materializer检查正式tag/commit/target/22 exact、无inner ID、完整Notes和描述，然后填入既有Native模板。兼容tag由shared registry读取正式descriptor生成，保留 `Gameplay/Balance/Decisions/Events`，版本tag为 `1.20 'Crozier'`；不是tags_only，不省完整Notes。

```text
"C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe" -B -X utf8 C:/workspace/ck3-upgrade-20261006/ccc-formal-release-minimal-prep-agent-01/materialize_ccc_publish_inputs_01.py --publication-root C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01 --staging C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01/formal/mod_celestial_commerce_corruption --manifest C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01/formal/mod_celestial_commerce_corruption-v1.0.1.manifest.json --operation-id ccc-1.0.1-actual-source-pass-01
```

4. Root按现有唯一publisher screen/keeper规则临时上线，当前owner probe必须实际 `BLoggedOn=true` 且owner `76561198273714027`。此后publish只一次，UNKNOWN先回读后态；不重播同operation。完成或终止必要在线任务即恢复Steam离线，审新鲜原图。

```text
"C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe" -B -X utf8 C:/workspace/ck3-upgrade-20261005/root_run_native_workshop_once_01.py --root C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01 --stage probe
"C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe" -B -X utf8 C:/workspace/ck3-upgrade-20261005/root_run_native_workshop_once_01.py --root C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01 --stage publish
```

5. 实际EResult1不能代替公开Notes。既有verifier一轮三端点匿名精确读回全部描述/identity、新唯一最新entry完整Notes/字符/行/SHA、旧条目原文。新增tag/sidebar读回脚本只解析同轮raw，零追加HTTP。

```text
"C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe" -B -X utf8 C:/workspace/ck3-upgrade-20261005/ccc-12003-readiness-agent-01/formal-publication-16/verify_ccc_101.TEMPLATE.py --run-once --output C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01/anonymous-readback-01
"C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe" -B -X utf8 C:/workspace/ck3-upgrade-20261006/ccc-formal-release-minimal-prep-agent-01/verify_ccc_tags_from_existing_readback_01.py --anonymous-output C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01/anonymous-readback-01 --output C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01/anonymous-tags-sidebar-01.json
```

6. SDK fresh subscription/download前保全已有缓存，证明本次fresh安装完成；严格核22，唯一允许cache descriptor增加正确维护ID的最后一行。新安装内容仍要进入下一项缓存business cell。

```text
"C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe" -B -X utf8 C:/workspace/ck3-upgrade-20261005/root_run_native_workshop_once_01.py --root C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01 --stage download
"C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe" -B -X utf8 C:/workspace/ck3_eternal_recurrence/tools/build_celestial_commerce_corruption_release.py --verify "C:/Program Files (x86)/Steam/steamapps/workshop/content/1158310/3804807463" --manifest C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01/formal/mod_celestial_commerce_corruption-v1.0.1.manifest.json --workshop-cache
```

7. **必需缓存L3：一个简中代表生产核心cell，不能以strict22代替。** 产品现有正式基线 `docs/celestial-commerce-corruption-acceptance-1.0.0.md:30–38` 明确fresh22＋同外置夹具，观察barter、当前真实官员、生产决议/事件、第四档特质及0.50税率；原先formal-publication-16短卡遗漏此业务腿，本卡补齐。当前.3 source路线为D0宋帝→D1真实官员→D2生产effect打开真实1001选`.d`→D3原11 markers；它不把脚本effect称为物理决议Confirm，Root另外确证真实生产决议Confirm/`.f`退出与当次冷却。缓存腿复用后来真正通过的这一代表路径及同Source/harness/controller/fixture，保留相同实际GUI证据和边界。不新增全档位、所有天朝能力、九语实机、保存重载或其它产品cell；原合同没有新增再次快进三年的条件，本卡不制造该新要求。

Root以现有canonical allocator取得新的真实CCC run_id（未执行），然后file-only准备cache挂载的新独立profile：

```text
"C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe" -B -X utf8 C:/workspace/ck3_eternal_recurrence/tools/ck3_live_run_id.py allocate --mod celestial-commerce-corruption
"C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe" -B -X utf8 C:/workspace/ck3-upgrade-20261006/ccc-formal-release-minimal-prep-agent-01/prepare_ccc_cache_profile_01.py --source-frozen-argv <ACTUAL_SOURCE_PASS_LIVE>/frozen-argv.json --source-report <ACTUAL_SOURCE_PASS_LIVE>/native-report.json --cache "C:/Program Files (x86)/Steam/steamapps/workshop/content/1158310/3804807463" --formal-manifest C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01/formal/mod_celestial_commerce_corruption-v1.0.1.manifest.json --run-id <ROOT_NEW_CANONICAL_CCC_RUN_ID> --live-root C:/workspace/ck3-upgrade-20261006/live
```

脚本读取实际源场 `input-snapshots/profile` 的6个冻结输入，避免复制已运行logs/save；只替换outer product.mod的path为真实cache，另5份byteexact。重绑prep/policy并调用同Source actual typed loader；原预算/Start/schema/bridge无改动。输出file-only `<NEW_LIVE>/root-launch-argv.json`、`cache-file-inputs-receipt.json`。Root仍须审实际源PASS、这些新cache输入/当前离线原图、按已有方法封存新launch资格并取得独占后唯一启动；脚本不调用screen/bus/game/Git，不冒充已有launcher接受的frozen输入包。旧allocator16无cache参数，勿改旧freeze或直接拿旧state启动当cache。

复用源场 `ROOT-OPERATOR-CARD-16.md`、`ROOT-OPERATOR-CARD-10.md`、`root-gate-review-14/ROOT-GATE-CARD-14.md` 和 `root-live-observer-17/ROOT-OBSERVER-CARD-17.md` 的实际允许接口/controller。所有epoch/PID/gen/actor/event-instance取新cache当前值，不抄源marker信用。完成后保存新的actual cache core/GUI/normal-exit/cleanup/thread/CAS。

8. 上传原stage保留，正式无ID重建到新output并strict22核验。实际SDK、完整匿名Notes/tag/sidebar、freshcache业务、离线、正常退出和永久changelog/master commit/push齐全后才标完成。永久 `docs/release-changelogs/celestial-commerce-corruption/1.0.1.md` 只在事实成立后填：真实日期/tagcommit/manifestZIP/actual源和cache run/SDK与entry全文SHA/限制/offline/CAS，新增永久 `docs/release-evidence/celestial-commerce-corruption/1.0.1.json` 可索引全部回执。不能提前写未来master hash。

```text
"C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe" -B -X utf8 C:/workspace/ck3_eternal_recurrence/tools/build_celestial_commerce_corruption_release.py --release --workshop-item-id 3804807463 --output C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01/postupload-pristine/mod_celestial_commerce_corruption
"C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe" -B -X utf8 C:/workspace/ck3_eternal_recurrence/tools/build_celestial_commerce_corruption_release.py --verify C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01/postupload-pristine/mod_celestial_commerce_corruption --manifest C:/workspace/ck3-upgrade-20261006/ccc-workshop-publish-1.0.1-01/postupload-pristine/mod_celestial_commerce_corruption-v1.0.1.manifest.json
```

当前真实newtag/publicentry/cachebusiness均为空。备料完成和脚本编译帮助不等于实机或发布成功。
