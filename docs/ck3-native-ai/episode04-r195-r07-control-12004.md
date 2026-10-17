# R195：R07 登船实验的 32 日静止对照（1.20.0.4）

R195 已完成 **32/32 个不同的精确自然日与正常闭场**。本页仅收录静止 control；本包未含独立 treatment，`full_v2_qualified=false`、`original_R07_v1_qualified=false`、`zero_fee_proved=false`，没有录制或成片资格。后续配对结论应另加其实际证据，不能倒改本次观察范围。

`machine_id: desktop-3fevhd2-1c74096080`；run `desktop-3fevhd2-1c74096080--vanilla--R0195`。历史执行来源为 `611bc985ae95f477dd7314df11f8602cd1e595f3` / a33；正式包保存了实际 qualification JSON，不能据此追认其他机器的部署。观察发生于 2026-10-17 UTC：正常存档 01:42:15.795571、bootstrap 观察 01:43:53.204779、屏幕释放 01:44:02.581859；便携包封存于 01:48:01.247912。时间与机器来源均可在[原文清单](evidence/episode04-r195-r07-control-12004/R195-CONTROL-EVIDENCE.manifest-a01.json)逐件核对。

## 实际观察

共同 S0 来自 R191 正常 checkpoint，日期 `53148192`，存档 73,689,246B，SHA-256 `bc3d40861e908ba8b05d5c86094a0ff7a399216ef0e4d0c1a72f166559b40ca2`。R195 独立冷载后实际 actor31254、Army18、province2635，空 route；运行 PID29000 / create-filetime134366728035105406 / episode `native-31254-d5ea28d864bc`。32 份 complete 与原 Arm/status 逐日通过生产 sentinel 校验，每日 tick1、overshoot0；终点 `53148960`。control 未执行 Move/Halt，逐日实际 route 仍为空且驻2635。

| 段 | 实际覆盖 | terminal 日期 | window / payment epoch / natural epoch | natural / payment records |
| --- | --- | --- | --- | --- |
| 1 | 日1–24 | 53148768 | 1 / 1 / 1 | 48 / 12 |
| 2 | 日25–32 | 53148960 | 3 / 3 / 3 | 16 / 2 |

两段均 read-complete，无 overwrite、failed append 或 publication failure。第24日暂停归档后，payment 与 natural 分别实际关闭/清空，再独立开第二段；每段都有初始空 journal、natural-only/其余8 families OFF、末尾独立 same-frame cash 与最终全 OFF 原件。序列只在段内解释，不能跨 clear/enable 累加旧 continuation。首海边1032的原生 preview 为单边1→0；county condition 的 Pfalse 是该县入损耗路径的 bypass，不能解释为路线不合法，更不证明实际登船。

两末包生产 reader 均未识别 selected-army boarding debit，**这不证明登船免费**。段1另有一个 generic wallet callback，其原始上下文与 unwind parent 已保留，`maintenance_attribution` 仍为 `unclosed`；不把净钱包差或该 callback 直接命名为登船费/军费。原生 packed date 高32位也不当作另一日期。

首次 baseline 因旧 consumer 期待不存在的 `native_carmy_id_observable` 而真实 exit1；标准 baseline 后由原 query2 完整来源和独立补齐的 commander/cash 恢复，未重发 Army query。首次 dayrunner 因动态 import 未加入 adapter.parent 而在 Runner/SDK 前失败；原 bound bytes 由外置 runpy 环境入口续行。第25日事件在目标日已到、已 Arm/Resume 后中断；原 action claim、wait、选择后验与只补后半读回的新 complete 一起保留，未重放日动作。可复用修复见 [baseline resolution](episode04-r07-baseline-resolution-12004.md) 与 [generated adapter import](episode04-r07-generated-adapter-import-12004.md)，这些故障不能记为首海边资格失败。

实际 native save、bootstrap/result 与 screen CAS release 均在原文包内：正常 process exit0，tree/SDK/keeper 已收净，屏幕资源为空。此 control 的 recorder 为 `NOT_STARTED`，没有 Start/Finish 或影片成功事实。

## 可复用代码与跨机读取

唯一便携索引为 [index.json](evidence/episode04-r195-r07-control-12004/index.json)，实际历史重放结果为 [PRODUCTION-REPLAY](evidence/episode04-r195-r07-control-12004/PRODUCTION-REPLAY.actual-a01.json)，执行 exit0 见[执行回执](evidence/episode04-r195-r07-control-12004/REPLAY-EXECUTION.actual-a01.json)。完整 282 件原文共8,686,535B 无损保存在 [90,694B ZIP](evidence/episode04-r195-r07-control-12004/R195-CONTROL-EVIDENCE.actual-a01.zip) 中；清单记录每件 offset、length、SHA 和原始路径。ZIP_LZMA 的唯一连续容器由 verifier 在内存切片，不展开磁盘。

可复制同 evidence 目录并从该目录运行：

```text
python -B -X utf8 verify_control.py --archive R195-CONTROL-EVIDENCE.actual-a01.zip --manifest R195-CONTROL-EVIDENCE.manifest-a01.json --repo <含清单中精确生产源码的checkout>
```

[verify_control.py](evidence/episode04-r195-r07-control-12004/verify_control.py) 是本场已实际执行的冻结历史 verifier，只接受该 control32/两段/已恢复 baseline 的合同；不是通用新场启动 CLI，也不授予 live 操作。其生产依赖包括 `war_payment_observations_v1.normalize_journal`、`r07_v2_contract.consume_window` 与 `native_driver` 的 sentinel Arm/stop validators，六个源码 exact pins 见清单；原 authoring 脚本仅保留 provenance，不安装到通用 tools。

其他机器可读取研究、复用代码与离线重放历史原文；回放不访问原件绝对路径、不读取存档/native binary、不调用 SDK/桌面。它不证明目标机器的 CK3/Steam/Defender/权限/容量或实机状态。大型 Driver/save/native bodies 未重复收录，精确来源引用仍在原回执中；未因本包删除任何原件。保留与复核按[统一存储策略](../storage-retention-policy.md)执行；原 manifest 的复核时间为2026-10-24T01:46:54.557675+00:00。
