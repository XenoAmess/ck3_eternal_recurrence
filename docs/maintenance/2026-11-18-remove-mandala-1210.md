# 肃清曼荼罗 1.0.2：CK3 1.21.0 迁移

machine_id: `desktop-3fevhd2-1c74096080`。目标为 CK3 `1.21.0 (Florin)`／build `26622941`／EXE SHA-256 `2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc`。

候选版本从 1.0.1 升至 1.0.2，descriptor 声明 1.21.0 与实际工坊分类 `1.21 'Florin'`；四份生产脚本及其原有六个 sweep 事件不变。新版原版仍定义 `wanua_government`、`mandala_government`、`temple_citadel_holding`、`mandala_nuke_mandala_decrees_effect` 与三个启动／年度／政体改变钩子。源定位在外置 `D:/ck3-state/upgrade-20261118/mandala-stock-references.json`；静态门通过 15 文件、9 语言、6 个 sweep 事件。

共同 exact-build registry 增加实测 1.21.0 version/SHA 对，供原有 fixture 准备记录实际引擎身份；该 registry 的既有合同明确不授 gameplay capability。prepare helper 扩展到此已登记身份，保留旧版匹配及未知 SHA 拒绝；3 项生产 registry／receipt 测试通过。未加载、重标或绕过旧 native DLL。

现有公共 GUI-only 准备原来只能挂载正式产品，无法运行已有的独立业务夹具。现增加成对的 `fixture/fixture_manifest` 输入，分别校验、计费、复制、冻结并挂载；正式产品树不被污染，发布后 cache 路由不接受夹具。共同完整 20 项离线回归通过，含真实文件复制、错 SHA／缺 manifest 拒绝和准备预算计费；已接到原 static CI。软件通过不授本产品实机资格。

复用既有 MRM 业务夹具及其八日合同，未执行旧 runner 的启动入口。当前 emitter 已按实际 1.21.0 身份生成外置夹具；`MRMA120` 仅保留既有 marker/调度命名，不是旧 ABI 采用声明。保留启动清除、首日政体、次日地产、AI 重定向、月度及年度 dispatcher 的全部断言；GUI 实际规则／移除后态和正常 Quit 仍须由公共 run/verify 取得。

Open Kaishek 实际 JAR 对四份生产脚本的通用语法 parse 均退出 0。报告保存实际命令、JAR SHA、checkout HEAD 与原始输出 SHA：`D:/ck3-state/upgrade-20261118/mrm-kaishek-summary.json`；该检查只授语法子集，未提供 CK3 1.21 语义 profile，也不把 checkout HEAD 推断为此旧 JAR 的编译来源。

当前为源码／软件候选，实机与工坊发布仍 NOT_RUN。后续只更新 canonical Workshop `3797711947`；正式 1.0.2 Notes、公开全文读回、真实缓存加载及永久 changelog 完整后才记发布完成。

首次公共启动尝试 R0001 在创建游戏进程前被门禁拒绝：后台探针已取得当前客户端的 exact-source CEF 离线回执，但旧启动消费者只资格化 native provider。共同门禁现对 CEF 路由重新调用实际 source-qualified／owned background producer，并要求 Steam incarnation、源文件与 CEF endpoint 全部匹配原新鲜回执；Popen 前再次执行相同重验。旧 native producer 的 exact profile／anchor 合同保留。9 项消费者回归及单文件 strict mypy 通过；此修复不授 R0001 实机信用，原拒绝保留。


2026-11-17T20:03Z（本机）实际业务已通过：公共 GUI-only `desktop-3fevhd2-1c74096080--remove-mandala--R0003`，正式 tag 的 15 文件与独立夹具挂载。实际规则页默认启用并 Apply，1066 罗贝尔单次 Start；1066-09-15 → 09-23 八日，十个完整 marker 各一次、FAIL0、error.log 0 B。月／年为原 dispatcher 加速检查，不授自然一年或旧档矩阵。实际成功事件与角色页“村社领地”已直接审阅；显式暂停后经游戏菜单“退出到桌面”，原 Popen.wait 返回0，无 WM_CLOSE/STOP，keeper 与 CAS 闭合。公共 verify 的 case_acceptance_pass=true，产品发布仍待完整工坊闭环。R0002 在创建进程前再次被旧 native identity 检查拒绝，后继把该检查保留在 native 分支；新版本 CEF 单测及实际门禁／Popen前重验均通过。

原件：`D:/ck3-state/upgrade-20261118/mrm-business-verification.json`，业务 review SHA `1a704117bf9c247fc5e32e6ae667a57c6b870af094547918473d5c645adb5e59`；实际 debug.log 1,201,033 B／SHA `8352e9e5e59d14d78681bf0c8814d9b804c616e765761ffbce5e443c3aec668c`。初次 EULA 有前后截图与创建时 profile pins，但未取得紧邻点击前 root marker hash；隐私页补齐即时前后 marker hashes，不补造首次缺件。R0002 release summary 误写R0001，真实 task/run identity 仍为R0002，原错误保留。系统 Toast 按既有授权实际设置 HKCU ToastEnabled=0 并读回。
