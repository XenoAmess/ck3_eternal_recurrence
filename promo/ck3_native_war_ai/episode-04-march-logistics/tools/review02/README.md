# Common T0 control（离线工具）

`validate_common_t0_control.py`只消费显式archive中的小JSON，复用生产付款normalizer，不发SDK/游戏/桌面请求。`bind_common_t0_control_runner.py`先通过实际baseline，才从显式SHA绑定的既有逐日runner生成供Root审阅的新控制组候选；生成不是执行，Halt/enable仍由Root原生操作完成。

工具与[方法/当前研究缺口](../../../../../docs/ck3-native-ai/episode04-common-t0-control-12004.md)配套。manifest为v2；复制模板后填写archive machine、来源commit/DLL、freeze pin及实际分支绑定。所有路径archive相对；历史响应内绝对路径用显式`archive_prefix_map`映射到archive内目录。不得将旧C路径当默认可用输入。machine为证据所属机器，验证机可以不同。普通savedT0 replay只复用同一存档身份，不能混用历史window原始包。

```text
py -B promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/validate_common_t0_control.py --archive-root <explicit-archive-directory> --manifest pair.json --phase baseline --output <new-baseline-result.json>
py -B promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/validate_common_t0_control.py --archive-root <explicit-archive-directory> --manifest pair.json --phase pair --output <new-pair-result.json>
py -B promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/bind_common_t0_control_runner.py --archive-root <explicit-archive-directory> --manifest pair.json --runner-source <archive-relative-reviewed-runner.py> --runner-sha256 <exact-reviewed-source-sha256> --output <new-candidate.py>
py -B -m unittest discover -s promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/tests -p test_common_t0_control.py -v
```

输出create-only，缺少未来PID或实际证据会exit2并写BLOCKED_OR_REJECTED；不会把pending变observed。archive manifest本身必须相对archive路径；所有JSON读取≤16MiB，freeze≤1MiB；不会读/哈希.ck3、EXE或raw。完整ordinary原件只按成功response顶层`army_history_evidence.raw_result_reference`读，校验大小/SHA/query/profile/revision/episode；不glob/latest、不使用陈旧driver-state command history替代引用。原始存档SHA来自已保留正常保存回执，不重新计算。

manifest `control`必填：assets_root/run_dir/run_id、pid/create_filetime/generation/episode、prepared/identity_receipt/admission、driver_state_path、t0_snapshot/t0_ordinary_response、baseline_cash_before_snapshot/baseline_cash、halt_response/after_halt_snapshot、21个显式daily_summaries。treatment同形但无Halt字段；`two_new_loaded_arms`时必填。事件恢复日显式day_source_overrides.N给original arm_response、successful read-only clock_response、final_snapshot，沿用旧动作原件，不能重放未知结果。

tests只用编译B fixture的一份必要personal正例（合成事件而非实机）和临时JSON；覆盖跨机器可读、角色/来源/DLL/EXE/窗口/create-time混用、引用越界/冻结pin、raw金额与NET区别、高32位非日期、pending与已登船控制拒绝。离线test通过不代表新控制组已运行。现有源normalizer可能升级；出现源schema不兼容须保留真实失败并检查对应版本，不放宽来源资格。
