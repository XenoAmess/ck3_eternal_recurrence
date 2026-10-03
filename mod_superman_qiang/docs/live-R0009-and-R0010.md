# 《超人强》R0009 / R0010 实机验收

日期：2026-10-04，简体中文，实际 Steam CK3 1.20.0.3/build 25652598。本报告记录 A0004 的完整机制矩阵、正常查看、真实存档重新加载；正百分比、仅改变量的 scale 对照及真正无模组旧存档加入测试另待后续轮次。发布尚未完成。

## 冻结输入

- 产品源码提交 `2873141e76177f52e218aa7da05e75cbdd312fc1`，builder A0004 22 文件 production staging；manifest SHA `63b0bc75a4c13bfdb343d77d621617eb425c204af081f00658454b193f261aac`，ZIP SHA `551901e384931fb5d465f0eaca3327ef357d004d4e290b7bc205c24cc40c3564`。
- 游戏 EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`，实机目录 `C:/SteamLibrary/steamapps/common/Crusader Kings III`。
- `fixture-a12` 外置 42 项，manifest SHA `2b34e778c0f3d94a1782a3f7bb09cd447222be80a434c89c2774f3b446448fe7`；实际 JAR parse/roundtrip 五文件无诊断，见 [A0004 构建报告](build-validation-2026-10-04-query-localization.md)。grammar 不证明游戏机制。
- SDK clean source `f643b32e6146dce73f77fedfefd8471da59fb04f`，1027 个 Python 文件精确 SHA；生产源码提交不是 DLL 编译提交。DLL `ad3bbb4e7bc19f2737bba10c468d26cabcae4058c6c2ae4f3b8675e95c5b8518`、injector `d332d1a4bb3524ddce5a73b6150449d9b29b21aff8c9fae61333b088796ffa7f`。历史编译 stdio 保全缺口见 [环境报告](live-environment-20261004.md)。
- Python `tools/.venv/Scripts/python.exe` 3.14.7，MCP 2.0.0。每次均有独占屏幕续租、进程检查及当次 Steam 新图“离线模式”直接审阅。

永久外置根目录 `C:/ck3-superman-qiang-20261004/acceptance/`。R0009 完整 ID `desktop-3fevhd2-1c74096080--superman-qiang--R0009`，UUID `a4c8559d-1fc4-4bab-858a-b8a094cfc39e`，PID 15284。R0010 ID 末尾 `R0010`，UUID `1534555c-e70e-49f3-adec-418843ace726`，PID 16052。每轮 `preparation.json`、`sdk-python-input-hashes.json`、原生 MCP request/response、原始日志、存档、melt、角色原始块及 stdio 均保留。

## R0009 机制和独立保存结果

通过原生 MCP 启动正常 1066 Robert 战役，在外置夹具的真实 `on_game_start_after_lobby` 之后运行。debug 日志得到 **42 个唯一 PASS，0 FAIL，0 缺失，一次 START 和一次 END**。跨隐藏事件边界保存 baseline 和后态，每八项跨一天释放递归堆栈；同日双次调用保持在同一个动作事件中。

首个原生 checkpoint 真实返回 `saved`，69,126,866 bytes，SHA `48d573a9e60c009172df481fcffcc8e7349883e6b635945f5461d7a27a96afbd`。原始 melt SHA `9cc5851a00537758919e936e675d5f81fcdb37f38c471a8069aad932983fd3f2`。最终只读 v6 decoder 输出 `save-decode-a04/fixture-readback-v6.json`，SHA `ec4fbddd1b8740c94d2feec6a7a8fef5e8305a5d52f98bf8ddbe3f7db42ae349`：42/0/0，127 个角色，死者 65950 通过玩家保存的 typed reference 独立定位于 level 2，基础数组六项均 10。旧 v4/v5 解码器与失败定位证据保留，未改变游戏输入或旧输出。

六个确定性技能 helper、真实随机 selector、经验正反方向、0/非零 tie、AI/AI、玩家/AI、同日两次、匿名、原版两个接入、tooltip 与 no_sex_memory、16/17 岁、死亡、自身、六项全部不能转移、零基础正修正、零显示接收、负百分比和饱和面板全部得到真实脚本后态。独立角色原始基础数组始终保持；六账本成对守恒，实际保存 modifier 的 sign/count/multiplier 与账本一致。无法仅凭 PASS 或总技能和推断的基础漏点检查由真实存档逐项完成。

99/100/101、1,000,000→1,000,001、安全最大值减一→`92,233,720,368,547`、已达最大值保持都以整数 fixed5 原始身份读回。负值按 uint64 的有符号解释解码；不整除 100000 的值不标记 `integer_exact`。账本正负成长、翻转、回零、±1,000,000 已达边界及最后合法一分均读回正确；来源者负百万最后合法点使用真实正修正 buffer 保证仍有有效技能可贡献。

保留 Norman 原版文化负勇武抵消的独立观察：bellicose +2 与 chanson de geste 抵消 5 点负修正，使净账本 -1 可以显示 12→12。平坦勇武测试先用外置合法 -5 修正消耗抵消额度，再验证双方显示 ±1；独立 Norman 场景仍验证 raw ledger 与 multiplier，不删除历史 R0007 的两项错误断言。

原版性行为压力下降与 had_sex memory、禁用 memory 时依然计数的断言通过；不承诺概率性怀孕必定发生。

## 正常中文 UI 与只读性

使用实际原生能力不足的已记录官方 UI 降级：肖像右键 → 正常“查看性经验”交互 → 正常确认。没有用夹具 `trigger_event` 替代用户入口。原生事件上下文独立核对 `sxad.1`、玩家 root 与真实 `sxad_view_subject`，事件正文直接审阅原图。见 [能力缺口](../../docs/ck3-native-ai/superman-qiang-character-ui-capability-gap-2026-10-04.md)。

| 目标 | 正常入口及直接图审 | 原生身份 | 原图 SHA |
| --- | --- | --- | --- |
| 玩家 | 经验 1001，六有效技能 12/25/14/16/11/21，净修正 0/0/0/1/0/0 | instance 1，root/subject 31254 | `4e885bc24228c8e440a5f6949138870d330fcc35669ee5b0d7c67c07c78da9b9` |
| 原有廷臣约兰达 | 未初始化经验 0，技能 14/3/9/12/7/10，净修正全 0 | instance 2，root 31254，subject 50601 | `5428d395e5248ca4ecb02249359a0d11fb98b2c926a5ef6c61023319d42dcb37` |
| 兰贝特 | 经验 1,000,001，技能 10/10/11/10/10/12，净修正全 0 | instance 3，root 31254，subject 65920 | `03d003f2eae0b1fe1af679ade9f8d184ca74ef8d3118bf4dc8dad1fab41ddd99` |
| 兰贝特特质 hover | 说明显示持有人 1,000,001 次，与玩家 1001 不同 | Court 唯一姓名筛选后同一真实目标；save holder 65920 | `7e1476ad3cadf8ee28fca9d72ca92640bb428ff9189abe23a2fd468a698513cc` |

原图分别在外置根的 `r9-ui-event-a01`、`r9-ui-nonplayer-event-a01`、`r9-ui-million-event-a01`、`r9-ui-million-hover-a01/screen.png`，均 1024×768。查找兰贝特使用原版 Court 姓名筛选；剪贴板两次未写入的真实失败保留，UIA 实测无 ValuePattern，随后标准 Win32 Unicode 文本输入成功，原图逐字读回并观察到唯一角色实际筛选结果。所有点击/hover 有统一坐标映射回执，键盘布局及控件焦点先核验。

查看完三个目标并关闭窗口后，第三个真实 checkpoint SHA `2585a6f72cd5a67fda82163b290ede8478c99ee6639efef6d693b11b7dd6f9cb`，最终 v6 readback SHA `d5d423382f646cbef34fb1aa13ce4bd835f115b22a559b73d787fe469199f3a8`。`ui-readonly-comparison-a01/report.json` 比较前后 127 角色：全部 sxad 变量、六项基础数组、实际 modifier record/scale **0 变化**。原有廷臣 50601 不在夹具索引内，另提取前后原始块确认 sxad 变量和 modifier 均缺失，基础 `[8,2,7,8,6,7]` 保持。不以经验查看的事件窗口声明引擎 RNG 状态没有变化。

root 另直接审阅四张原图，并独立读取全部关键保存字段，证据 `C:/ck3-superman-space-a01/root-r9-v6-readonly-review-a02.json`。本节图片包含夹具角色/人工计数，**不作为 Workshop 干净玩法 media**。

## R0010 真正退出和重新加载

R0009 在 22:28:37 UTC controlled stop，完整进程树退出、watchdog absent、tasklist+ToolHelp32 均空。R0010 使用新的 profile 和新 PID，真实启动参数 `-loadsave=xar_checkpoint`，加载 R0009 首个原始 checkpoint `48d573…`。未使用缺 supervisor 的 restore 接口，未重开 NewGame。原生地图后态是日期 53144544、玩家 31254、paused=true；新日志无 SXAT 标记，夹具没有重执行。

重载后真实 checkpoint 69,127,215 bytes，SHA `40e2ce879a053870a818d9eeee052e1a26fa847f6e87015c681456ee5a4f666f`。v6 readback SHA `4abba71a3d7428410b4d301fd6351663e2359ae4b5a067b3ab6c73cc3d45e636`。`reload-gate-a01.json` 对全部 127 角色的 sxad 变量、六基础数组、实际 raw modifier record/multiplier 与输入存档逐项比较：**0 变化**，独立 42 项保存断言全部通过。百万经验、安全极值、正负百万账本及其真实保存倍率没有截断或丢失。

加载后再正常右键玩家查看，原生 `sxad.1` instance 1，root/subject 31254；`r10-ui-player-event-a01/screen.png` SHA `bcaff0fdb134c29131e5c5c4b9429363b150f76c531ced67bb3fa797ea1b75de`，直接显示经验 1001、有效技能 12/25/14/16/11/21、净修正 0/0/0/1/0/0，证明显示修正已重新应用。随后正常停止，清理证据保留。

## 日志边界和余项

R0009 final error.log SHA `477d34799e467f03211128d016f30b865e28a35dde40ca0682db11a8a1a5b7c0`：无 sxad 本地化 data-chain 错误；Court UI 操作期间原版 `pam_interactions.txt:9254` 的 `ecclesiastic_transfer_land_interaction` 有一条无角色 save_scope_as 错误，原文保留。`pdx_text_formatter.cpp` 的 weak/positive_value 格式错误需独立归因，不能称全局日志零错误。R0010 error.log SHA `d480572c15147c283e85e281a972f012102fe7cfe354068d1d2fbfa8c986f23b`，Script system/data-chain 均 0。R0007 缺行/43 条 UI 错误未改写；A0004 修复用本轮新图与日志证明。

历史 runner 的 report 初始 `ok=false` 没有在 controlled stop 后赋真，wrapper 退出码 0 只表明进程包装器结束。原始 report 不改；本报告机制/UI/reload GREEN 来自独立明确的 gate。后续 runner 已单列 session completion scope，真实执行异常返回非零，session 成功仍不代表所有产品验收通过。

覆盖 L1-01/02；L2-01 至 06、08 至 17 的所述核心场景；L3-01 未初始化他人、L3-02 不同真实计数作用域与 holder、L3-03 多目标查看、L3-04 真实重载。L2-07 的正百分比、L2-17 的仅改变量不重建控制/显式重复重建、L3-01 未初始化自身、L3-05 无模组已有存档加入及 L1-03/L3-06 干净玩法 media 在后续最小轮次完成。本报告不扩展为多人、移除模组、其他游戏版本或随机分布统计证明。
