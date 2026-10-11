# 2026-10-11：I4 冷重载入口与 B4 首次夹具

本次交付是公共入口与离线夹具的有限推进，整体仍 **NOT_GREEN**。I4 冷重载尚未执行，上游、冷载 run/PID/session、持久化 PASS 和 release 信用全部为 NULL；B4 没有安装器或 CK3 实机资格。

I4 新 case 复用公共 `CaseClient`、natural adapter 与既有 cold persistence 合同，不改 native、默认工具或 O15 manifest。ROOT 已审阅导入源码、注册与 CI 接点，尚不授新 CI PASS。

| 原始检查 | 实际结果 |
| --- | --- |
| [首版 8 项][t1] | exit0；合成夹具，无 CK3/SDK/真实 SAVE |
| [portable 入口 8 项][t2] | exit0；测试类 AST 不变，入口改动后的一次复测 |
| [外置 wrapper 检查][t3] | 新增 1 项 exit0；首跑多行 marker 夹具 [RED][red] 保留，随后仅修夹具为真实单行形状 |
| [永久第 9 个 method][t4] | 只运行新增 method 一次 exit0；[原始 stderr][t4s]。旧 8 项未重跑，不能称新 9 项整套已跑 |

wrapper 保留直接 CLI，要求原 exit0、固定源码 SHA、stderr 唯一 EXECUTE_ONCE/public_argv，以及 manifest/frozen 的 source、环境、Python、cwd、prepared/context 一致。永久回归使用 inert 原件，真实 bytes guard 在替身之外核验正确 SHA/badSHA；旧失败不改写。

冷重载只接收本轮真实 qualified expiry finalSAVE、public verify0、同 manifest 与 normal GUI/OS/native close；显式 upstream run_id 必须贯穿原件一致。不能用原0240、R55失败世界或不完整到期记录替代。[R56 原 verify exit2][r56] 仍拒绝：完成 71 个合格自然日后，首个活动事件触发普通推进的事件谓词拒绝，host1/public2，没有 qualified expiry、finalSAVE 或 normal GUI0。[待绑定输入][pending] 保持 NULL。

未来冷载核 cooldown flag absent、actor31254 alive/landed/member、Faith107、Rite169、HoR31254、headless、正式决议 enabled。公共 check_pin 保留；新 SAVE 若证明冷载序列化，正文读一次且如实记录，不重复解析原 SAVE。不授完整365日、精确到期、I3b/C3/完整I4信用。

B4 [九模式原始索引][modes] 中 direct、empty-direct 两项 exit0；其余七项 exit3，代表 [metadata/install admission][admission] 尚未通过，不能把它们写成 EH/安装器 PASS。[编译结果][build] 的 configured/built/build_succeeded 为 true，编译与链接完成；[原命令][outer] 实际 exit1，原因是 Defender WMI/COM settings_failed。未取得匹配 broker policy 或排除生效资格，未改为成功，也没有游戏信用。

[闭账原件][closed] 于 2026-10-11 02:08:12Z 结束未来写入预留，carry 为 **136190943622 B**，剩余 reservation 为0；这不是物理回收，未新增 cleanup 扣减或续期。已有来源复核期限保留。

ROOT 已回读前序06db的 [Official 38103022910](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38103022910) 与 [Linear 38103022898](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38103022898) 成功；不外推为本次未发布代码、冷重载或 B4 的业务验收。本次只整理原件，无测试或实机重跑。

[t1]: acceptance/2026-10-11-i4-coldreload-entry/focused-original8.json
[t2]: acceptance/2026-10-11-i4-coldreload-entry/focused-portable8.json
[t3]: acceptance/2026-10-11-i4-coldreload-entry/wrapper-external1.json
[red]: acceptance/2026-10-11-i4-coldreload-entry/wrapper-first-fixture-red.stderr.txt
[t4]: acceptance/2026-10-11-i4-coldreload-entry/wrapper-portable9th.json
[t4s]: acceptance/2026-10-11-i4-coldreload-entry/wrapper-portable9th.stderr.txt
[pending]: acceptance/2026-10-11-i4-coldreload-entry/CASE-INPUTS.pending.json
[r56]: acceptance/2026-10-11-i4-coldreload-entry/R56-public-verify-RED.json
[modes]: acceptance/2026-10-11-i4-coldreload-entry/B4-modes-INDEX.json
[admission]: acceptance/2026-10-11-i4-coldreload-entry/B4-inplace-normal.stdout.log
[build]: acceptance/2026-10-11-i4-coldreload-entry/B4-native-msvc-result.json
[outer]: acceptance/2026-10-11-i4-coldreload-entry/B4-build-command.json
[closed]: acceptance/2026-10-11-i4-coldreload-entry/B4-CLOSED-RESERVATION.json
