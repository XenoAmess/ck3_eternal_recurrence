# 原版儒家反馈版本：R0064 开局前失败

北京时间 2026-10-12。源码为 `a894a25dd36abd9654c688002454bf236fcd7489`，CK3 为 1.20.0.4；本场没有进入战役，没有执行七个业务检查点，不能据此声称原版儒家、信条数值或个人选择已经通过实机。

## 结果与修复

- 公共入口在原有 400 秒准备期限内未就绪，实际 exit 2。原 host 随后报告严格 Robert 启动绑定失败，并保持现场。Cbr3 的 `XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1=OFF` 与 fixture 要求 Robert 冲突；原报告未保存模型的候选列表，不能推断具体哪个准入子条件先失败。下一冷构建须启用既有选项，并重新绑定实际 DLL、配置和 runtime；不能只修改 Python 身份或绕过 native setter。
- 产品加载日志实际出现 `Unknown trigger type 'hidden_trigger'`，位于挑战者决议。修复权威模板并重新生成：16 项可读条件留在 `is_valid`，最终原后端守卫放在原版支持的 `is_valid_showing_failures_only`。两字段共同限制执行，未放宽任命资格。生成和两项针对性 AST 检查实际 exit 0；修复后的引擎加载和提示画面仍待下一场验证。
- 日志另有无有效条目的 `lyd_faith_history.txt` 警告。该文件当前是无活动历史的占位，没有覆盖原版主礼仪；此警告尚未消除，不能宣称加载日志无告警。
- 后继 `vanilla-faith-feedback` 的准备预算在启动前改为 900 秒，总超时仍为 3000 秒、hold 仍为 1800 秒。R0064 的原期限和失败记录不改写、不续期。

## 正常退出与现场释放

ROOT 在原 hold 期限内使用新的关闭客户端接管收尾，沿用同一 PID 13868/create_time 1791742946.8013368；没有重新运行业务 case 或延长 hold。实际从选人界面返回主菜单，按“退出到桌面”，保留原图和规范坐标换算回执。未开局，也没有出现保存对话框。

保留的 OS 句柄证明游戏 exit 0；失败生命周期 `failure_lifecycle_completed=true`，原 host 的 wait 1 与错误保留，`normal_close_qualified=false`、`business_pass=false`。Steam 新鲜位移图经 ROOT 直接审阅为离线，分辨率恢复至原 1024×768；原 allocator 实际 wait 0 后释放屏幕槽，CAS sequence 4998→4999。后续只消费精简投影，不重读本场或 R58–R63 的 native 正文。

## 最小证据入口

机器外置根 `C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0064`：

- `normal-close-recovery-001/normal-close-result.json`：实际关闭及保留失败。
- `host-original-process-exit.json`：原 host wait 1。
- `release-command-001/RESULT.actual.json`：实际 CAS 释放。
- `native-cleanup-projection.actual.json`：3281 bytes，SHA-256 `59dbbaccb6abed9e4212d6ca915ab01deb4b154a1d7c313b8be13bceb4ee31fb`。
- `terminal-failure-projection.actual.json`：1022 bytes，SHA-256 `9be2dc61c118506fdd7e10c767eaea776af8cc0fcd917e6fb1895e87e6faad1b`。

准入根 `C:/workspace/ck3_lyd_runtime_20261004/i4-root-storage-admission-20261012-026` 内的 `case15-run-command-001`、`r64-normal-close-recovery-command-001`、`tooltip-fix-generate-command-001`、`tooltip-fix-tests-command-001` 保存真实命令及返回码。`fixture-robert-binding-fix-candidate-001/REPORT.zh.md` 保存选角配置诊断。

`a894a25` 的三个实际 CI 均成功（Official 38163278022、LYD 38163277915、Linear 38163278017）；这项静态结果不覆盖上述实机失败。工坊仍为已发布的 0.1.0 Beta；0.1.1 未发布，一期保持 NOT_GREEN。
