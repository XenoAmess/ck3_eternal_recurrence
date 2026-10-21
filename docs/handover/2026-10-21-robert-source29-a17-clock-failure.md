# 罗贝尔 Source29／A17：时间推进失败与后继修复

`machine_id: xenoamess-full-tower-eb9d2c1186`。现场截止 2026-10-21T00:25Z；承接 [Source26／A05 交接](2026-10-20-robert-source26-a05-vacation-handoff.md)及[后续实际执行记录](../ck3-native-ai/robert-a15-retry02-war-query-closure-2026-10-21.md)。旧交接中的 Steam 截图前置已被用户 2026-10-21 指令替代：只准后台查询，不激活、移动窗口或截图。

**仍为 5429／10950 个已保存游戏日、4753 个已保存完整周期；G2 6／8，M6 终态、M7 实际 H 与广度未完成。30 年和 1 秒／日均未完成。A17 实际完成五个普通周期，但未保存，新增天数信用为零；下次冷恢复须回退这五个周期。** 原全墙钟起点仍是 `2026-10-19T03:26:49.420926Z`，维护、失败和研究时间均计入，不能重置。

本机外置根简称：

```text
P = D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep
C = P/robert30-v20261019-campaign01
T = C/runtime
U = C/runtime-a17
O = P/p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100
B = D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01
```

## 实际执行与闭场

Source29 canonical commit 为 `d02d9907fa7a26ab60a6a75456fa276be78387c4`，1464 文件／59296139 B，双导出已资格。A17 运行 `xenoamess-full-tower-eb9d2c1186--vanilla--R0015`，Game PID 83948，出生 FILETIME `"134370118417378359"`。实际 Native31 DLL SHA256 为 `3d43cd01c908013f7bb2704aa1844acd518fa691ae96ef4e09413284dd59038d`。这些事实仅属于本机该场。

启动前的后台 Steam 回执于 2026-10-20T23:11:12Z 观察到 offline／true；启动于 23:17:21Z。该回执现在过期，不能授权下一场。后续启动须重新运行 `tools/steam_offline_state_probe.py --receipt <new-path>`，只有新鲜 offline／true 且身份、来源一致才准入；不可用时修复后台通道，不转截图。

原生 2560×1440、1:1 实际首帧通过；未更改桌面分辨率。SEM10552、CAP10553、冷绑定及原 feeder 资格通过，feeder 唯一提交 FULL10554。五个周期结算至 4758，随后 AUTO10565 在时间推进后验失败：resume 已观测，游戏日期未在等待期内前进，后续四个暂停请求仍为 submitted／unknown。pending cycle 4759，原动作不得重放；没有发布 CONTINUE。

CAP10566 与普通 tool 形式的 journal10567 均被原队列拒绝，未到 MCP／Native。正确的五字段 Root journal 控制10568实际读取成功，保留 HALT；NEXT 为10569。其 journal 60 events／lost0／coverage_gaps64；64 是 no_token 位，不是丢失64条。后来的 scalar 和画面出现1081-08-01，仍不能证明10565完成或暂停队列已排空，天数信用保持零。

23:59:39Z 原监督闭场：正常 WM_CLOSE 未确认，owned Game 被强制清理 exit1／Job0；SDK queue exit1、SDK app exit0。三个 Task 均注销并读回 absent，screen116 CAS7900→7901释放，run 标为 completed-red。录制正常结束并产生原 completed 回执，H264／2560×1440／30fps，媒体1343245478 B；闭场复用原消费者哈希，没有再次通读影片。

唯一闭场入口为 `U/ROOT-A17-ACTUAL-CLOSURE-INDEX01.json`，7191 B，SHA256 `3ebbf5eb221814cab62bbef01ea0a6570a8da6a48420c064ca30155b5980aa53`，绑定原 FULL、failed AUTO、journal、Driver／SAVE复核、媒体及所有释放回执。当前无本任务游戏、录制或屏幕租约。

## 瓶颈与已经验证的修复

FULL 的业务 RPC 并集74.6311405秒；失败 AUTO10565 占50.777052秒，其中时间等待50.2378588秒，约占 RPC 总量67.3%。两次持久化合计0.2942207秒，并非本批主瓶颈。游戏 owner 为什么延迟，现有证据尚未证明；不能靠延长等待、把心跳当业务进展或重放 unknown 掩盖。

暂停／恢复 ACK 修复保留原生 request ID，严格验证 envelope、protocol、step 和身份；不把 ACK 变成实际执行证明。新增 helper 与测试，以及实际 driver 修改范围的严格类型检查通过；新旧相关回归合计32项测试、47个子例通过。没有热改 Source29、runtime 或已结束的进程。

[Native32 被动诊断候选](../../tools/g2_saved_campaign/candidates/native32_passive_journal_diagnostics_20261021/README.md)增加 no_token 执行对象与有限退休记录，并区分显式历史查询与空 ID 集合。Python 8项测试、4文件严格类型检查及8项验证通过；实际 MSVC C++ host→Python reader 三帧通过。第一次 `/W4 /WX` 编译失败原件仍在，修正后第二次通过。**这只是 host／源码资格；尚无生产 DLL 构建、ABI、部署或游戏准入。** host EXE 的 Defender 登记实际 admin-required、未 Add，没有取得排除设置成功。生产后继必须一致重编四个 TU，不能把 host PASS 当生产 DLL 已可用。

## 决策信息与字段合同

Root 亲审 A17 冻结原始 scene：灰色面板可见完整行动、多个理由、对象／局面／风险和实际失败／unknown 结果，无旧蓝窗、无影片标题。证据 `U/ROOT-A17-RICH-PIXELS-VERIFIED01.json` 1288 B／`9400be4fcdd7f544ced0175b80d6e0d0684a8bd637dc3c85a317dd1162d5f6bc`，绑定910 B实际决策文本及原图。

10559 暴露婚姻回查继承旧战争展示字段的问题；[真实生产者修复](../../ck3_autonomous_player/src/xar_autoplayer/family_marriage_formal_consumer.py)只移除被替换行动的旧展示字段，保留业务数据和身份守卫。生产者→formatter→JSON→展示消费的3项回归通过。修改范围严格检查零错误；全文件原有68项诊断未增加，不能声称历史全文已严格类型化。

后台离线接线新增后，旧 pinned queue 只加载三个模块而遗漏实际 Steam 依赖。现统一为精确十模块合同、私有绑定和完整来源校验，无 ambient fallback。旧协议 fixture 使用其原始冻结 launcher，不改历史协议 SHA。相关89项中86项直接在真实文件系统通过；另外3项仅因当前 sparse checkout 缺两份已跟踪输入，使用当前 HEAD 精确 blob 的只读 RAM 补齐后通过，不能写成89项原样文件系统通过。6个完整模块及2个实际修改 AST 范围严格检查通过。

公开 `c145b473ce846279f47ba63b699313cacc44c445` 的 [Official CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39517170756/job/118952000158)失败于第22步历史 launcher fixture；第19步通过。[Linear CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39517170684/job/118951999874)通过。上述新修复正在单独交付，不将旧 CI 或本地测试追认为下一提交的远端 GREEN；CI 执行机器 `machine_id: unknown`。

## 后继执行边界

保留 SAVE10480／raw53274624／1081-07-31、actor40526／episode `native-40526-1bec95182886`；原 campaign `native-31254-6271ac8cd441`、T0 53144328、终点53407128、固定D0=174不变。先完成公共提交、远端 CI、后继 Source 的机械清单与独立冻结资格，再决定新冷启动。不得改 sealed Source29、旧144叶或把已有普通周期当新增保存进展。

全部机器继续使用[统一存储策略](../storage-retention-policy.md)及版本化参数；旧 holds 不退款，不删除当前恢复基线、未知动作原证据或唯一恢复输入。当前人工复核截至2026-10-21T01:00:00Z，只授权有限源码／fixture／闭场复核和已独立登记的构建，不自动授权新游戏、录制或续期。后继需核当前机器、全部保留项、实际卷容量和精确输出峰值。
