# R345 行政总督续任确认次数边界（2026-09-09）

## 实机结果

- R345 从冻结 R248 候选存档推进 cross-cycle/endgame source 路径；输入为
  `83,449,160` bytes / SHA-256
  `C7E5CA119F4DB4D9BFE738859DD5E32DEC6F9F1F804D91F9B26ED5D256E219DA`。
- 同一运行中出现三次 `ep3_decisions_event.2001`：
  - `date_raw=53204640` / instance `203` / `confirmation_vassal=26936`；
  - `date_raw=53226000` / instance `343` / `confirmation_vassal=27928`；
  - `date_raw=53246304` / instance `353` / `confirmation_vassal=28679`。
- 三帧的 root/`confirmation_liege` 均为玩家 `32904`，saved scopes 都精确为
  `confirmation_vassal` 与 `confirmation_liege`，两个 enabled rendered/native
  options 都为 `(0,0)`、`(1,1)`。前两次选择 option `2` / native `1` 后
  postcondition GREEN；第三次在选择前被旧 `max_occurrences=2` fail-closed。
- typed failure 为 `known-interrupt-occurrence-bound`，第三帧
  `occurrence_count=2`、`selection_attempted=false`。cleanup GREEN、failed
  checks 为空、最终 CK3 进程槽清空，原始输入存档未变。report / cleanup
  SHA-256 分别为
  `DE62FB59DDF4BC78AA68FEF4D2050AB2FB3526368B4DB1631587D26ADC5F183D` /
  `80D1C0C82E700093AC4DF140F87AE9700A28220E1BC5A94878CD2432AF593CF4`。

## 精确原版合同

CK3 1.19.0.6 原版
`events/dlc/ep3/ep3_decisions_events.txt` SHA-256 为
`716F014CDCC11119D652A7F20F80DD98D74A8A3EBD2AF9873D8E0DFF140913E3`。
`.2001` 是行政制封臣向其领主申请确认续任的信件事件。native `0` 会开启
后续典礼事件链；native `1` 执行已写明的 refusal effect 并结束玩家窗口，
所以 bounded source capture 继续选择 native `1`。

原版 `admin_confirmation_decision` 可由不同 AI governor vassals 分别触发；
封臣侧 `confirmation_cooldown_vassal` 为 25 年，而领主侧
`confirmation_cooldown` 仅为 2 年。R345 三名不同封臣的间隔分别为 890 天
与 846 天，符合领主节流后由不同封臣再次进入的语义。角色 ID 漂移仅发生
在已经按动态第三方约束处理的 `confirmation_vassal`；scope、option、enabled
和 native 映射均无漂移。

因此最小修复只是把当前 bounded Phase-2 observation window 的出现上限从
`2` 提高到已有实证的 `3`。该事件理论上可在更长局期继续重复，但没有第四次
实机证据时不预防性放宽。

## 验证与 Git

- promotion source checkpoint runner normal / `-O` 各 `83/83` GREEN；
- `py_compile` 与 `git diff --check` GREEN；
- 代码在并发远端 `a8acdc1` 之后通过独立干净 worktree 执行 rebase，最终
  commit `071870e233a65b5340e224c0320b8d827bba3d97` 已 ordinary
  fast-forward push 到 `origin/master`；未 merge、未 force-push。

本轮只解除真实重放中的次数边界，不新增业务 scene、definition、stage 或
宣传素材计数。canonical source registry 仍为 `3/4`，R346 继续
`capture_cross_cycle_endgame`。
