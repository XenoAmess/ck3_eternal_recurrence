# R0222：writer 失败与后续行政正常闭场

`machine_id: desktop-3fevhd2-1c74096080`。本记录依据 2026-10-20 13:29–14:03Z 的原件，14:05Z 起离线整理。执行 source 为 `39e59acce6624edbc30322e4797d2e421c0a44aa`，载体 native compile tree 为 `fee86631356f556271445157523c62abfd62951e`；不把后续候选修复或其他编译来源当成本场已验收源码。来源、大小和 SHA 见 [索引](evidence/episode04-r0222-20261020/index.json)。

R0222 从普通原生存档恢复，actor 33388，日期 `53149056`。初次 payment query 在 Python request 字段构造阶段报 `No module named 'tools'`；原始 actual-results 保留该错误。随后 actor cleanup 的 tactical daily sentinel 因 speed 字段不合预期而拒绝。原 `R08-WRITER-RESULT/TERMINAL` 保持 `actual_days=0`、`exact_day_verified=false`、`OFFclear=false`、`Save=false`、`business_pass=false`。这是业务执行失败，不因后续行政操作补写成成功。

Root 后来在独立 `case-output-root-normalclose-a01` 完成 6 条行政 rows：pause、九族 research sampling OFF、独立 query、paused readback、一次普通 Save、独立 after。6 条均实际 `ok=true`；保留计划与小结果，省略的大型 result/snapshot 子树在 [派生投影](evidence/episode04-r0222-20261020/projections/ADMIN-SIX-ROWS.derived.json) 明确标注。该投影不是原始 SDK transport；471,758B `ROOT-ADMINISTRATIVE-CLEANUP.json` 与 14,833,097B `native-report.json` 只保留原件路径、大小、SHA 与必要投影。

九族 OFF/clear 的行政读回为 true，**payment 专用 OFF 读回仍 unknown/null**。已有 payment default/source 与 wire-prefix 证明当时默认关闭，初次 query 在提交 native request 前失败，所捕获 prefix 中没有 payment enable 命令；这些证据不能改写成独立 payment OFF/clear 读回。后续行政 rows 同样不包含 payment enable。九族、独立 supply journal 和 payment window 不能互相替代为同一个开关。

普通 Save 原件为 74,272,517B，SHA `b1aab6da1f0ba3b61537fd7fd393a0553848b53381cc093061878f5a3a9cf657`；独立 after 仍为 `53149056`、paused。其 episode 为普通 `native_campaign`，`episode_run_id/episode_character_id=null`，不授 one-life 资格。

关闭证据也分层保留：CK3 PID 16468 的 retained handle 实际 OS exit=0，native shutdown exit=0、tree gone/cleanup proven；9651B `normal-close-result.json` 的 SHA 为 `95e603ff029375b17a969e356fdac31574ebc873371368531074ffe7799d387c`，行政 `normal_close_qualified=true`。原 host Popen 988 仍 wait=1，原 public run Popen 11656 仍 wait=2；另开的 Root close Popen 31288 wait=0，keeper 30260/allocator 27740 原 wait=0。screen CAS 由 7548 到 7549，任务 done、resources=[]。不能把行政 Popen=0 或 CK3 OS=0 写成原 host/public=0。

两个前置辅助失败也保留。旧 quit-menu helper 硬编码原 `case-output/normal-quit-awaiting.json`，原 Popen 32188 wait=1、stdout 空、stderr 为 FileNotFound，失败在输入前。Root 随后仅为实际行政目录制作外置 exact-path 适配。原 manual-review helper 拒绝 custom output 的证据仅在 Root 工具 transcript（`ValueError: Select actual canonical normal-quit-awaiting request`），无独立本地 stderr 文件；不能伪造一份“原始回执”。后续适配 receipt 保留原 helper 与外置副本的 SHA，成功 review/截图仅引用已有 pin。这不表示原公共 helper 已支持 custom output。

行政闭场与容量结算均不授 R08 业务通过。正式源镜头 `3/11`、研究 `10/14`、业务 `7/11`、B `0/2`、ABC `0/3` 保持不变；不声明影片完成。源码 fix-candidate 与测试仍单独审阅，尤其 Save gate 修复尚在候选阶段，不能提前称已修复并实机通过。

## 后续源码修复，非本场实机通过

付款模块改用共享运行环境已有的 `ck3_live_run_id`；未 claim 时仅接受完整、类型匹配的 idle0。新支付窗口先独立确认 natural-phase ON；cleanup 独立收敛 payment 和九族 OFF。正常退出新增 `save_verified` 闸，仅一次普通 Save 与独立同日后态完成后设置，未知结果不重投。源码、真实父/子进程边界及故障回归原件见[修复证据](evidence/episode04-r08-runtime-repair-20261020/ROOT-INTEGRATION.actual.json)。这些检查不增加 R08 实机、业务或镜头资格。

## 归档字节更正

首次公开提交 `fe7711cf` 的部分复制件被 Git 文本规则从 CRLF 规范化为 LF。原始来源一直保留；后继提交从这些原件恢复精确字节，并为本专题两个证据目录登记 `-text`。旧提交保留，未修改历史 SDK 结果或重新执行动作。逐文件前后大小、SHA 和来源见[更正回执](evidence/episode04-r08-runtime-repair-20261020/BYTE-PRESERVATION-CORRECTION.actual.json)。
