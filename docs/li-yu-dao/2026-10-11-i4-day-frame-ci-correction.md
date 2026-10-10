# I4 day-frame 测试夹具的 CI 修正

提交 `2f77206cecd94a684ff274dc20939e5a74eab994` 的 [Official CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38090128909) 实际失败；同一提交的 Linear history 成功。首个失败发生于 `test_ck3_mod_acceptance_i4_day_frame.py` 的 FakeClient：它无条件读取显式 `expected_revision`，但第三个只读查询已使用 `bind_previous_revision:true`。原6项测试中2项因此报 `KeyError`。

本次只修正这份测试：模拟器从同一计划刚完成行的 `after_snapshot` 取得绑定revision；断言改为一个3行计划，并确认首个查询显式9、最后查询省略显式revision并实际绑定11。日推进帧的既有拒绝变体保持。生产adapter、host及业务门槛没有改动。

2026-10-10T22:16:03.596399Z—22:16:03.836326Z，只重验原来失败的两个方法，实际exit0、2 PASS；其他4项及已通过的批处理检查不重跑。[原CI终态、失败原始日志及本次实际回执](acceptance/2026-10-11-i4-day-frame-ci-correction/INDEX.json)保全分别发生的结果，失败日志另有无损ZIP。

Source14先前指向2f的计划、准入和binder候选保持HELD，未物化。修复发布后必须生成绑定新exact的successor，不能借旧CI或旧计划追认新来源。此修正不提供实机、自然到期、最终SAVE或冷重载信用；一期仍75% / NOT_GREEN。
