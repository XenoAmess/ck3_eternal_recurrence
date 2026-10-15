# Historical locked-route production clock source

R12/R0175 and R13/R0176 both pin the complete `native_driver.py` source at commit `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`, SHA `48fee62f0bc2f6c0c43bc8b4156faea86060c78e4189d71709f5555d0847707f` (1527840B). The named ZIP preserves that exact local Git blob and is shared by both replays. It is a Python source artifact, never a native executable or runtime dependency.

The archive's expected whole-file SHA selects this exact source through SOURCE-INDEX.json. ZIP/member bytes and the full historical source SHA are verified before compiling the original four pure clock definitions plus literal reason table. A newer checkout's `native_driver.py` does not reinterpret historical clock results. Missing/mismatched historical artifacts fail closed. Clone plus this checked-in ZIP can replay offline without Git history, network or a source-machine path.

SOURCE-FREEZE.actual-a01.json records the current checkout source SHA separately and the two new positive replay results. New replay reports expose `production_clock_source` selection/commit/artifact/current-source comparison. Original archives, indexes, statuses and clock flags are unchanged; no mutant or prior matrix was rerun.
