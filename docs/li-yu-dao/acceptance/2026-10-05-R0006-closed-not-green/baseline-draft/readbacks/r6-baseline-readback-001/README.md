# R6 baseline save readback

Actual save SHA `291bf3fe63c1d8c3bbbbc97c6d94e47794b031c07934311cbcb83873232fdc8e`, 91,282,203 bytes. Saved local player is Character 31254, history 1128 Robert Guiscard, 1066.9.15. Gold 244, piety 150, prestige 2200 independently match the current SDK receipt.

Player remains Catholic/Roman rite; all 36 LYD catalogue rite keys are loaded, but `lyd_enabled` and fixture initialization are absent. Current spouse history 1123, former spouse 10003, seven children and seven held titles are separately projected.

See [baseline-report.json](baseline-report.json) for explicit checks and [generic-v2/report.json](generic-v2/report.json) for all actual Faith/Rite graphs. Original parser failure remains under `generic/`; updated source is `helper-v2/r6_i2_readback.py`. Missing saved stress remains null; SDK stress 0 is separate.

These facts establish saved player identity and baseline resources, not keyboard delivery, UI focus or LYD gameplay acceptance. No game, attach or desktop operation was performed.
