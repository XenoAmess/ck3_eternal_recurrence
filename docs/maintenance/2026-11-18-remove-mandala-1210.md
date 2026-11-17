# 肃清曼荼罗 1.0.2：CK3 1.21.0 迁移

machine_id: `desktop-3fevhd2-1c74096080`。目标为 CK3 `1.21.0 (Florin)`／build `26622941`／EXE SHA-256 `2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc`。

候选版本从 1.0.1 升至 1.0.2，descriptor 声明 1.21.0 与实际工坊分类 `1.21 'Florin'`；四份生产脚本及其原有六个 sweep 事件不变。新版原版仍定义 `wanua_government`、`mandala_government`、`temple_citadel_holding`、`mandala_nuke_mandala_decrees_effect` 与三个启动／年度／政体改变钩子。源定位在外置 `D:/ck3-state/upgrade-20261118/mandala-stock-references.json`；静态门通过 15 文件、9 语言、6 个 sweep 事件。

共同 exact-build registry 增加实测 1.21.0 version/SHA 对，供原有 fixture 准备记录实际引擎身份；该 registry 的既有合同明确不授 gameplay capability。prepare helper 扩展到此已登记身份，保留旧版匹配及未知 SHA 拒绝；3 项生产 registry／receipt 测试通过。未加载、重标或绕过旧 native DLL。

现有公共 GUI-only 准备原来只能挂载正式产品，无法运行已有的独立业务夹具。现增加成对的 `fixture/fixture_manifest` 输入，分别校验、计费、复制、冻结并挂载；正式产品树不被污染，发布后 cache 路由不接受夹具。共同完整 20 项离线回归通过，含真实文件复制、错 SHA／缺 manifest 拒绝和准备预算计费；已接到原 static CI。软件通过不授本产品实机资格。

复用既有 MRM 业务夹具及其八日合同，未执行旧 runner 的启动入口。当前 emitter 已按实际 1.21.0 身份生成外置夹具；`MRMA120` 仅保留既有 marker/调度命名，不是旧 ABI 采用声明。保留启动清除、首日政体、次日地产、AI 重定向、月度及年度 dispatcher 的全部断言；GUI 实际规则／移除后态和正常 Quit 仍须由公共 run/verify 取得。

Open Kaishek 实际 JAR 对四份生产脚本的通用语法 parse 均退出 0。报告保存实际命令、JAR SHA、checkout HEAD 与原始输出 SHA：`D:/ck3-state/upgrade-20261118/mrm-kaishek-summary.json`；该检查只授语法子集，未提供 CK3 1.21 语义 profile，也不把 checkout HEAD 推断为此旧 JAR 的编译来源。

当前为源码／软件候选，实机与工坊发布仍 NOT_RUN。后续只更新 canonical Workshop `3797711947`；正式 1.0.2 Notes、公开全文读回、真实缓存加载及永久 changelog 完整后才记发布完成。
