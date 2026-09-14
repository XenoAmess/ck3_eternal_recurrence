# 重整河山 0.4.0 验收报告

状态：**COMPLETE。L0、源码树 MCP-first L1、Workshop 发布、公开描述与 Change Notes 精确回读、全新订阅缓存及 fresh-cache L3 均为 GREEN；Steam 已恢复离线模式。**

验收日期：2026-09-14

目标游戏：CK3 `1.19.0.6`

产品：`mod_reclaim_the_motherland`

Workshop item：`3798404599`

上一公开版本：`0.2.0`（tag `reclaim-motherland-v0.2.0`）

## 1. 0.4.0 当前结论

三期与四期已经在同一条真实 CK3 链中完成源码树验收。CK3 `1.19.0.6` 会在旧君死亡事务中暂时销毁空法理动态霸权，即使该 title 已有 `single_heir_succession_law` 与正确 `current_heir`；最终实现因而保留同一 title object，在次日把它、原直属忠臣 realm 和九席 incumbent 交给引擎已经算出的主继承人。其他个人头衔没有被本 mod 抢救或重分配。

最近失去天命的后朝继续获得唯一三省六部官署资格；群雄割据前后、旧君死亡前后九名 exact incumbents 全部一致。离朝者清退、真实空缺交回原版任免，正式中书门下权力分享、天命和 `h_china` 专属特权没有延续。

后朝不再取得现任中华霸权在【提议附庸】中的三项身份优惠。本轮实际释放的直属诸侯主头衔获得五年、绑定确切后朝 title object 的【新近自立】-50；实机中两个通过完整原版 interaction validity 的独立目标均即时拒绝，定时状态随后自然到期。该项是软抗拒，不是硬禁；长期外交统一路线仍保留。

二期的【人心离散】、忠臣国号与封臣树、旧天子个人伯爵领保留，以及一期的 50%/51% 门槛、【宣称天命】封锁和【宣称复辟】全链均完成联合回归。

## 2. L0 与离线预验

- `tools/test_reclaim_the_motherland_contract.py`：19/19 GREEN。
- `tools/validate_reclaim_the_motherland_static.py`：GREEN；35 个运行时文件、9 种语言、每种 113 个本地化键、15 个玩法脚本。
- `tools/test_build_reclaim_the_motherland_release.py`：10/10 GREEN。
- `tools/build_reclaim_the_motherland_release.py --check`：双构建可复现；当前候选 manifest SHA-256 `aed036fcacd8f10facd1b0bce1bc09567782b9dcfadce7aa870d2b52f724a6e9`，ZIP SHA-256 `73d52162d28c67b5e9f144017dfaf4c52f7483fd4407718efaf870a90362c64d`。正式 master/tag 会改变内嵌 Git identity，发布哈希在 L3 收口时替换为最终值。
- `open_kaishek` commit `890b32de49081b7b5510e40c5518dfb59d5c8a6d`、CLI contract `b306a95`、JAR SHA-256 `7262e771ad3e1f5d724d663ac259a20e2a7df0c491d4c125f56cb4c3a604e75c`。
- product root parser：15 文件、107,678 bytes、0 diagnostics、SHA-256 `97642005f11453d1e91e819229795f4b21e74a50add6485f8857f2b484661162`，GREEN。
- fixture root parser：9 文件、44,101 bytes、0 diagnostics、SHA-256 `0027d268eb0fa62792d631ed45dd6b055290129ad8bc473abe9ffeec1278d1d1`，GREEN。
- 该工具尚未注册两个产品 fixture，validator/IR/runtime 对 CK3 动态头衔、council 和 interaction opcode 返回 `unknown-fixture/UNKNOWN_OPCODE`，故语义层诚实归类为 `not-applicable`；parser root scan 不替代实机结论。preflight 报告 SHA-256 `e1af7ab317bd8044e9ea70e2d534edd8ffaf9ed0a6eef7c594e2b9cd06693c9d`。

## 3. 源码树 MCP-first L1

Run：`D:\workspace\ck3_reclaim_phase34_20260914_process_assets\reclaim\runs\R0024-source`

- wrapper/cell：GREEN / GREEN；SHA-256 `566e3588a5e531d9de421407184edd404b36d392a58ecb43ee6e82bd5db3420b` / `18dac69ef3812dae34b32c9f804570cca357920aa7cb48859dbb24fb480b0c4e`。
- native episode：`native-29829-ab6e73e23df7`；MCP readiness GREEN，visual fallback disabled。
- CK3 EXE SHA-256：`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
- bridge DLL/injector SHA-256：`973b9eb1a4baa926811cd06237a8b8173cc4459c7f9140221afd45242e537095` / `3200204d0c883cc6f05d5c6b7d74b562ecb281eb1efce47db6b205c877683e64`。
- runtime product/fixture tree SHA-256：`30ecb34ae286991f4d243958efc0ec7e18db9c0fc09925875d49a665933560af` / `dce171a266a630036d6623c3a68a03a39fdf9b28db255c8cfef84c047bca517c`。
- 36 个顺序 marker 全部出现；`project_diagnostics=[]`；总时长 788.545 秒，slot wait 0.126 秒。
- source/runtime 未改写，保护存储 unchanged，隔离 userdir 与 CK3 原生进程树完成回收，`cleanup_proven=true`。

关键机器证据：

| 证据 | SHA-256 | 证明内容 |
| --- | --- | --- |
| `cell/07_loyalty_summary.png` | `807f2a3abbc9d71d1be5df1a8c1ff414bfd4a90c6ae581beced59fe9adf0947b` | 【人心向背】与二期忠叛回归 |
| `cell/08_later_dynasty_character.png` | `701b550b803779d85c2364432a0f5b83285ceda485a82094d7db730e27c4e381` | 后朝角色与头衔呈现 |
| `cell/08_song_capital_map.png` | `6642e1cdef298ce94251f56619b4fa2a0202fee5afadb2026d583c994b048ab0` | MCP 镜头位于大宋首都开封 |
| `cell/09_succession_recovery.json` | `064067bdef7c3ee8ab97e25110bbf3aea3f40f82d0990888dd99273b27472a88` | 同一后朝、个人伯爵领、忠臣 realm、官署 entitlement 与九席继承 |
| `cell/09_recent_independence_expiry.json` | `4671404424c86a821146b3616a3023ad2ddb593d953ef4b17790b8e8776de2fb` | 两项目标的 title-bound 定时状态自然到期 |
| `cell/09_decision_visibility.png` | `101ffff5d9e23fabac485dcffb888e12158734e3693606b01f14e1e9ebb9f20b` | 复辟入口及天命封锁回归 |
| `cell/11_restore_confirm.png` | `71cd043ef3879b3b8b071d144fa913b1a4eadffb5f779658f2770ef5f60fb` | 宣称复辟确认 |
| `cell/12_acceptance_complete.png` | `ce21ebfa117e1a418c98e1b03e848a01d93dadea4f37e0154763ddcd2823b398` | 全链完成事件 |

## 4. 保留的 0.4.0 RED

`R0008..R0023-source` 均永久保留在 `D:\workspace\ck3_reclaim_phase34_20260914_process_assets\reclaim\runs\`，没有覆盖。它们先后暴露并修复：title law 添加时序、销毁 `h_china` 后才补官、官署 entitlement scope、landless ministry title 被弱势头衔裁剪、批量补官上收忠臣 realm、随机外交样本失去 eligibility、死亡窗口内强移交被 CK3 后续结算覆盖、空法理动态霸权被销毁、次日恢复后的 loyal realm、已留任大臣重复授职，以及强制相位 fixture 缺少原版 `movement_member` 前置条件。`R0024-source` 是取代这些 RED 的首个全绿候选。

## 5. 正式构建与 Steam 发布

- 版本／tag：`0.4.0` / `reclaim-motherland-v0.4.0`；release tag target `23078f51d1b294b9db5dfc0a195051a48e3563a4`。
- 正式树：35 文件；manifest SHA-256 `34a950d331de7bff525c56df7fa5d0b018ee61cc42050924cc0c56aa7e6dd935`；deterministic ZIP SHA-256 `73d52162d28c67b5e9f144017dfaf4c52f7483fd4407718efaf870a90362c64d`；thumbnail SHA-256 `564a558d5dc280e9049fb6907db36418a9a29085802da2ce8bed0f1dff6e1c38`。
- 第一次原生 MCP submit 因 11,017-byte 双语描述超过 Steam 8,000-byte 字段上限返回 `EResult=8`，没有更新公开物品；失败回执 SHA-256 `37976aa76fb72e202a8afd381505798b3931cc69eb5ae31a86b5c40a34ad3aca` 已永久保留。
- BBCode 在不改变机制口径的前提下压缩为 7,946 bytes／5,720 个规范化字符，并先以 commit `ffb60e535346038ec43ae94c1ffd642d315d0bd0` 推送。新 operation 随后只更新既有 item `3798404599`，`EResult=1`、无需法律协议；成功回执 SHA-256 `3222f4d29eb06765750eec58d8c23046ca1d46d31f61a3ae5e902b2c81ae4f54`。
- 匿名公开回读为 `result=1`、public、标题 `Reclaim the Motherland — 重整河山`、文件大小 1,006,824 bytes、`time_updated=1789357628`；公开描述与入库 BBCode 精确一致，规范化 SHA-256 `d31d4fea0c0c1b383dca4c67d911970be6bf99dc1de31eb7122d37d33b05309f`。
- Change Notes entry `1789357628` 与入库 542 字／11 行正文逐字一致，规范化 SHA-256 `127609b585ed5268d998d8439614c023ec4133557889f8f977343ddab9ce63f5`。四张真实游戏图均 HTTP 200，公开页继续显示所需 DLC `Crusader Kings III: All Under Heaven`。
- 永久 item／Change Notes 回读位于 `D:\workspace\reclaim-motherland-v0.4.0-publication\steam\`，JSON SHA-256 分别为 `9ab39b5d67fc28b869e7ed390d2cbe998ea0c6d206b785e239a235b94506b81d` / `f8726e6ff7932d41c075aeec61cc81b9840b6f7b31ea61c7cead3d98ba1bb25b`。

## 6. Workshop fresh-cache L3

- 原 32 文件／949,064-byte 缓存已完整移动到 `D:\workspace\reclaim-motherland-v0.4.0-publication\steam\3798404599.before-v0.4.0-20260914-1149`，没有删除；Steam console 强制下载后得到 `C:\SteamLibrary\steamapps\workshop\content\1158310\3798404599` 的 35 文件／1,006,824 bytes 新缓存。
- builder 严格 Workshop-cache verifier 逐文件匹配最终 manifest；内层 `descriptor.mod` 无 `remote_file_id`，thumbnail SHA 与正式树一致。
- 最终 run：`D:\workspace\ck3_reclaim_phase34_20260914_process_assets\reclaim\runs\R0026-workshop`；wrapper/cell SHA-256 `8c5e80d758a2b109e139696d5adf091345eec10f237883394f8fa9ce173f49e4` / `c479210aaea41fe914235c14d6488275b436db18a8c36708c54f159c1c261968`。
- wrapper/cell GREEN；36 个严格 marker、MCP readiness、保护存储、source/runtime 不变与原生进程树清理全部 GREEN；`project_diagnostics=[]`。总时长 783.749 秒，slot wait 0.142 秒，native episode `native-29829-f02dab9d7d5e`。
- runtime product/fixture SHA-256 与源码树 L1 相同：`30ecb34ae286991f4d243958efc0ec7e18db9c0fc09925875d49a665933560af` / `dce171a266a630036d6623c3a68a03a39fdf9b28db255c8cfef84c047bca517c`。
- `R0025-workshop` 是未显式传入迁移后 `C:` CK3 路径的 environment-only preflight RED，未启动游戏；没有覆盖。`R0026-workshop` 以 exact EXE 路径完成取代。
- fresh-cache／Offline Mode attestation SHA-256 `cebddf4bea4b73412ecee286a6f53f12dc92b48d5b3806baa14c2c57ebfb65f8` / `687bb2b274b95afc7549d4b682c90312ddd2e0aca0b26d99a682be0d4a0f7b82`。Steam native probe 确认 `BLoggedOn=false`，连接日志记录 user-initiated logoff 且不自动重连；Steam 保持运行，CK3 为 0。

完整发行记录见 `docs/release-changelogs/reclaim-motherland/0.4.0.md`。受控验收证明已定位公式、两个真实 interaction 目标、跨代后朝／官署、定时到期和复辟全链；没有把尚未执行的三个自然局首年分布冒充为统计结论。

---

## 附录 A：0.2.0 历史验收（原文保留）

状态：**COMPLETE。L0 GREEN、源码树 L1 GREEN、Workshop fresh-cache L3 GREEN，公开发布后复核通过。**

验收日期：2026-09-13

## 1. 当前结论

二期机制已在真实 CK3 中完整跑通：默认【人心离散】会在群雄割据前冻结尊王派直属诸侯的一次性抉择；必留忠臣保留原主头衔、国号、直属关系和完整下级封臣树，必叛诸侯按原版流程脱离。玩家随后能看见【人心向背】总结，并继续完成一期的后宋、51% 门槛、【宣称复辟】和后朝销毁全链。

最终源码树 run 为 `desktop-3fevhd2-1c74096080--reclaim-the-motherland--R0004`。wrapper/cell 均为 `GREEN`，20 个顺序标记全部出现，项目 diagnostics 为 0；source/runtime、保护存储均未被改写，隔离 userdir 已删除，CK3 进程树已回收。

0.2.0 已上传到同一 Workshop item。公开标题、可见性和描述与入库源一致；公开 Change Notes 已逐字符精确回读。旧缓存被完整移到可恢复备份后重新下载，32/32 文件与正式 manifest 一致；最终 L3 从这份缓存再次获得完整 GREEN。

## 2. 机制断言

- 规则【尊王诸侯的抉择】默认【人心离散】；【誓死尊王】保留一期全员留朝行为。
- 候选人是裂解瞬间直属、有地、伯爵级以上且具有冻结尊王派身份的封臣。
- 战争、深仇、不忠、极低好感和针对旧天子的独立/宣称者派系构成必叛条件；明确羁绊构成必留条件；公开决裂优先。
- 其他 AI 诸侯按冻结事实计算 5%—95% 留朝概率并只结算一次；人类诸侯采用相同因素及公开的 50 分确定性分界。
- 留朝者不进入独立、弱势王/帝头衔裁剪、改国号或重新归属分支；其原 title object、显示/自定义名称、直属关系及 realm subtree 保持不变。
- 叛者和原本不属尊王派的直属封臣继续按原版群雄割据逻辑运转。
- 【人心向背】总结事件在结算后立即显示，列出代表性留朝者与反叛者。
- 一期回归项全部继续成立：旧天子保留个人领地与其他头衔，取得空法理后朝霸权；后朝持有者看不到【宣称天命】；50% 不足、51% 达标；【宣称复辟】执行原版天命效果并额外销毁后朝霸权。

## 3. L0：静态、合同与可复现构建

在 commit `a496d9fc` 的最终源码树执行：

- `tools/test_reclaim_the_motherland_contract.py`：13/13 GREEN；另有 1 项因 detached worktree 不含被忽略的原版游戏副本而显式 skip。
- `tools/validate_reclaim_the_motherland_static.py`：GREEN；32 个发布运行时文件、9 种语言、每种 112 个本地化键、12 个玩法脚本。
- `tools/test_build_reclaim_the_motherland_release.py`：10/10 GREEN。
- `tools/build_reclaim_the_motherland_release.py --check`：双构建可复现；manifest SHA-256 `b3cdaa33f4ad1dc8a707e807533da339e1002533be2e582b67e4abd51c048712`，ZIP SHA-256 `5981535815e61dd92c5f681a2fea9f9804cd58ffb545f5fe6f1310d9af6c8550`。

正式 tag 会改变 manifest 内嵌的 Git identity，因此正式发布哈希以发布 changelog 为准。

## 4. open_kaishek 离线预验

- commit：`890b32de49081b7b5510e40c5518dfb59d5c8a6d`
- CLI contract：`b306a95`
- JAR SHA-256：`7262e771ad3e1f5d724d663ac259a20e2a7df0c491d4c125f56cb4c3a604e75c`
- profile：`ck3-1.19.0.6`
- CK3 EXE SHA-256：`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`
- 产品 root parser：12 文件、50,804 bytes，GREEN；root SHA-256 `d8f6001c810261521ecbd744cd121e8930dfdf9cc8dea8bb4ae2174ff0f04ee1`。
- 外置 fixture parser：8 文件、20,308 bytes，GREEN；root SHA-256 `18e7ae11e6cec6e71df789f4766c3dd3349ec873f1b4c08f54eb114a023a0694`。
- validator 分别返回 880/311 个 `UNKNOWN`。当前 profile 不覆盖动态头衔、封臣重组和决议语义，因此诚实归类为 `not-applicable / cli-red`；parser 结果只作确定性预检，不替代 CK3 实机。

## 5. L1：源码树 MCP-first 实机

Run：`D:\workspace\ck3_reclaim_phase2_20260913_process_assets\reclaim\runs\desktop-3fevhd2-1c74096080--reclaim-the-motherland--R0004-source`

- execution ID：`ee251056-c718-44ed-ba92-6b3dd3b3ee8b`
- wrapper `report.json` SHA-256：`962c679a10ae669201eff32cb62f2cb442ab5189cffd0037ee9af4f03071f85a`
- cell `cell/report.json` SHA-256：`53ed9ecf85166c4f3e0335777c641b64f5043ffe7b7ec0fe56db1fd6b9bb83e9`
- live identity receipt SHA-256：`e5a4624ea1f58db27a1e39dbbe1682d080a7b6eeee66e38d3a6f08b374b7857d`
- preflight SHA-256：`e9eb1da6cc35bd24615996d771146746825315d7c31df6a0748169f9d2635b13`
- runtime product tree SHA-256：`b849da37bcb8901aa27b9a06d53b4bb4a247025ac9f2c775e54588d40933e119`
- fixture tree SHA-256：`8aea8e4e2df5eec325ff8d3315c184064f00fc798633228a0ee2098205c5ab99`
- 总时长：772.984 秒；CK3 排他槽等待 0.102 秒。
- bridge DLL SHA-256：`a71f38dfc26c8aa8e9f442f549e38973cb71049329710d1bae1e7aca87c26e03`
- injector SHA-256：`41230bf1a081a034897fd18fac33acdf74a0107cedc3d67f5cc6eb53c846577e`

关键证据：

- `cell/07_loyalty_summary.png`：SHA-256 `981150fa0f62f43c19cbb8c5b5157cb890b72b6e50f8e8f2fb01062472c1a1a9`。
- `cell/08_later_dynasty_character.png`：SHA-256 `f915eb1492c4c64934a2ba04e029730f1b207167331a6eabb248a653749a1897`。
- `cell/08_song_capital_map.png`：SHA-256 `a3da7a1f379d9b18ebc544f571ff53fce9d28e29f81005c626a40d5cef5d6d3e`。
- `cell/08_song_capital_navigation.json`：SHA-256 `a94386f1750e3f40a071ac8e2493e4f96e7d1bff0af52b3e934e6b5ae79a67b5`；原生 MCP 将镜头定位到 `b_kaifeng`，而非欧洲或意大利。
- `cell/09_decision_visibility.png`：SHA-256 `b10f2c4dcdd358482833e6ebfa1e5eb57ae20900a6462f0eb563c86544f6b656`；配套 JSON SHA-256 `6b8086a818777b89efd1456a776bfacb6a8d7595252a3f0acc98f809d4657fba`。
- `cell/10_restore_confirm.png`：SHA-256 `3f98010160a33f17b7b8f1c0bcd18a6c9f3a3ed21b4a7f4beb5123d8bf48ec85`。
- `cell/11_acceptance_complete.png`：SHA-256 `1ee5765b0dab7221f3ad43ae0483f9cddceca337b4cf04a2ac4fb6ac32cc2bf4`。

## 6. 保留的 RED 与修正

- `R0001`：忠臣国号/头衔/封臣树和叛者脱离已经通过，但延时总结事件丢失父事件 scope。修正为在同一结算链即时排入 `rmtm.1001`。
- `R0002`：完整玩家链通过，但 AI 普通候选人的同链变量读取在 tooltip evaluation 中产生错误。修正为先冻结叛乱结果，再通过单个 `random` 原子地改为留朝，消除顺序变量依赖。
- `R0003`：机制 GREEN；人工审图发现验收抽屉和带头衔人名影响宣传呈现。后续仅调整裁切及总结人名，最终结论由 `R0004` 取代。

失败 attempt 均永久保留，没有覆盖为 GREEN。

## 7. 四张真实游戏素材

四张 JPEG 都由 `R0004` 的真实 CK3 画面确定性裁切和编码，没有生成或改写游戏内容：

| 文件 | 尺寸 | bytes | SHA-256 |
| --- | --- | ---: | --- |
| `00_divided_hearts_live.jpg` | 1390×740 | 228,473 | `bdf2d4b38c6daa66ffe81b1dc881d7d017da137cbd5048d37427d09dd8944888` |
| `01_later_dynasty_live.jpg` | 1500×1050 | 512,586 | `3be1a698e51a96c4064311e04216784f676c31388888da13f639e23810597743` |
| `02_restoration_decision_live.jpg` | 1140×375 | 114,128 | `b443e478e90acf29608fe87b19cb5ce0b1d1c17d2bd78a9eb966a6a898bfc309` |
| `03_restoration_confirm_live.jpg` | 1420×855 | 286,425 | `07dfd518e43762918e4681deb3218656e761a20fa85af60a795ceef413021ba2` |

## 8. L3：Workshop fresh-cache

公开与构建身份：

- Workshop item：[`3798404599`](https://steamcommunity.com/sharedfiles/filedetails/?id=3798404599)
- tag：`reclaim-motherland-v0.2.0`；target `6486a0c72dda61c3b4e4466bc9db1193e83c74bc`
- 正式 32 文件 manifest SHA-256：`2d63b2c6d72db677a06644d61ee6b909e639c30d99f2ce9fc153f12f16ccce73`
- deterministic ZIP SHA-256：`5981535815e61dd92c5f681a2fea9f9804cd58ffb545f5fe6f1310d9af6c8550`
- 原生 Steam 上传回执 SHA-256：`d33334e040b59c21fc7757f78445ee70596c8a4b3f80d7b10788caadeaffbc11`；`EResult=1`
- 公开 API：`result=1`、`visibility=0`、949,064 bytes、`time_updated=1789251577`；标题与 5,446 字规范化描述精确一致。
- Change Notes entry `1789251577`：公开正文与入库源均为 508 字、14 行，UTF-8 SHA-256 `368a357002ec6e9bdb3fb181881257926e5a8184c8d8ee86aa29d9f7dc06cad2`。
- 永久回读：`public_item_readback.json` / `public_changelog_readback.json` 的 SHA-256 分别为 `ade3b8fe6423c800edfd7d14ec05f687103acf6d319bf97821ad8ed0d41f669b` / `7840809031cc91794c30dbc3fc576c93b757ee12287766ab97b7294696dcbad5`，均位于 `D:\workspace\reclaim-motherland-v0.2.0-publication\steam\`。

缓存：`C:\SteamLibrary\steamapps\workshop\content\1158310\3798404599`。旧 0.1.1 的 28 文件缓存已完整移动到发布证据目录，没有删除；强制下载后的 32 文件全部通过正式 manifest 严格核对。Steam 原生提交保留无 ID 的 canonical inner descriptor，验证器已修正为同时接受这种精确形式与 Launcher 的唯一末行 ID 形式。

最终 run：`D:\workspace\ck3_reclaim_phase2_20260913_process_assets\reclaim\runs\desktop-3fevhd2-1c74096080--reclaim-the-motherland--R0007-workshop`

- execution ID：`dee5e47a-6108-4720-86e9-c8370e5f8cf7`
- wrapper/cell：GREEN / GREEN；SHA-256 `fc77bbff14ef2be971f727d0875c52e181aac35bce52d7a2808e56d283286512` / `8cc4cfbfc57b3bb7e1a6eac3385052bf58d364a5caa95501ae505b0193eebfb2`
- live identity receipt SHA-256：`39f62d4eeb16a6df8c9226f2ef42ccb37c779ce8c640fda9297e3e779a97b58d`
- open_kaishek preflight SHA-256：`cff13f7d2be8ed65610a22886195536b569458b12daac8906a1464c4664189cf`
- 完整 20 个顺序标记；项目 diagnostics 为 0；MCP readiness GREEN。
- runtime product/fixture SHA-256：`b849da37bcb8901aa27b9a06d53b4bb4a247025ac9f2c775e54588d40933e119` / `8aea8e4e2df5eec325ff8d3315c184064f00fc798633228a0ee2098205c5ab99`
- 总时长 764.041 秒；CK3 槽位等待 0.125 秒。
- source/runtime、保护存储未改写；隔离 userdir 删除、原生进程树回收均已证明。

`R0005` 保留为 environment RED：未显式设置迁移后的 `XAR_CK3_EXE`，preflight 即停止且没有启动 CK3。`R0006` 是单独的 GREEN preflight-only 记录。二者均未覆盖，也未被冒充为最终 L3。

上传后已从 exact tag 重建正式 staging；manifest/ZIP 哈希保持不变，内层 `descriptor.mod` 不含 `remote_file_id`。Steam 最终恢复 Offline Mode，CK3 进程数为 0。缓存核对与最终离线记录 SHA-256 分别为 `d03e70fb410b22a01b548883a086b851b5bf784c3769124191b2c5c296a9471c` / `a48c09d45e2f2c57b5bd0d056af91b055723d67c510292b73dceb72d9cd34561`。
