# Shared local-launch regression: portable metadata dependency

The exact `af20455212ed75000ba6136b3be308a9288cb06e` push finished **Official Runner CI FAILURE** ([run 37959018781](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37959018781)). `test_original_harmless_child_returncode_is_preserved` imported `psutil` through `retain_host`; the static runner does not install that desktop dependency. Linear history succeeded. Li Yu Dao static checks was **NOT_TRIGGERED**: the actual exact-head API returned only those two runs. It is not counted as a successful Li Yu Dao check.

The fix changes only the harmless-child test. Its optional process creation-time probe uses synthetic `None` metadata; `subprocess.Popen`, the PID, retained original process handle, `wait()` and the child exit code 7 remain actual OS operations. Runtime admission still requires its real process inspection. No runtime launch, lease, normal-exit or product gate is weakened.

The ten targeted local-launch regressions passed after the fix. `RESULT.actual.json` pins the exact modified test bytes, command, stdout/stderr and original API/log evidence inside `raw-evidence.zip`; `ARCHIVE-VALIDATION.actual.json` verifies every extracted byte and the ZIP SHA. No CK3 or Steam process was started, no screen or ID was acquired, and no workflow was dispatched. A passing GitHub CI result for the fix is not claimed here.

The original API response and failed-job log are retained verbatim. Their SHA-256 values and the local regression output are recorded alongside this report; the historical failure is preserved.
