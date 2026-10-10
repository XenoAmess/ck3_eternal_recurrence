# R57 行政候选池原因边界与现有资格发现入口

结论：本次选定的 d_antioch 没有满足原合同的“独立人类自然位于完整合法候选池”前提。现有原始数据和源实现没有显示 provider 漏采、分页截断或选错窗口。R57 保留业务 RED；本包不修改 fixture、产品、native、helper 或原断言，也不授实机信用。

## 本场确证

- 原件 `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0057/case-output/case-appointment-0003-page-0000.actual-results.json`：34,616 B，SHA-256 `e2d717a6f837d1df629c0a83f85fb16fada779485363ef23443f40b736a4a5a0`。已先 stat，小于 1 MiB 才整读；未读取大 native report/export。
- 请求 title8923/holder29392 → group-first8923 → resolved8923 → current-window8923，key 均为 d_antioch，有效 law 为 appointment_succession_law。归一化关系匹配。
- full/source/base 池均为1，offset0→1，token `fnv1a64:78bd896962e31140`。唯一候选 fullID34484 是实际 AI，score_raw=-993200000。当前人类 actor29912 不在池。
- 对29912的 breakdown_available=false，原因 requested_full_character_id_not_in_current_pool；getter 没有调用。公共 helper 因此严格拒绝。本场没有 toggle、任命或继任业务信用。
- 另一实际 title-holder 小原件确认 d_antioch8923 为公国，holder29392 是 actor29912 的直属臣属；不是玩家本人持有。该原件30,020 B，SHA-256 `b1d5708192406662cd2df40f9919f0c66ad2cb5290ffee58a2d529a5e7646404`。

## 源证据及限制

`ck3_autonomous_player/native_bridge/src/appointment_window_snapshot_v1.cpp:40–65` 读取 window+D0 的 base(+18/+24)、source(+1C8/+1D4)、score cache(+9F8/+A04)，要求三个 count 一致，并逐项 fullID/指针/cache join。`:137–150` 对不在完整池的人物拒绝 breakdown。`:154–164` 再读完整快照以核验稳定性。不是 GUI filter/sort 的 list+48。

已有 exact .4 ABI：171BCD0 调用273A390填候选池；273A741..273A790 调用273AA40并 swap-remove 规则拒绝者。因此保留 base 池是引擎规则过滤后的合法候选集合。原 provider 能力文件、ABI freeze 和 fd1f DLL不重测、不重链。

实际加载的 admin_governor.txt 为1,800 B / `ebbca495f92da744310c18ef987ef8799678bbc8eb8181dbd9ee65a37f41c97c`，与 canonical相同；默认来源仅 `default_candidates = { holder_close_family }`。官方本机 .4 `game/common/succession_appointment/_succession_appointment.info:15–17` 将 default_candidates 定义为默认有继承资格类别；`:32–41` 规定有地统治者获任较低有地头衔时的 de-jure 条件，以及默认 lower / lower_or_equal / any 层级规则。`game/common/laws/00_succession_laws.txt:616–649` 把 appointment_succession_law 接到 admin_governor。

实际 fixture `events/zqagov_events.txt` 仅确定 e_byzantium 当前持有者切为独立行政人类，并确认任命法臣属存在；它没有保证所选臣属头衔的候选池含该人类。加载文件1,781 B / `a22160dbfba94b75c034e9c46b89fb4eede2f87f4d7236e298a128faf61088d7`。

尚不能区分29912是没有进入默认来源，还是被273AA40的某个规则剔除。现有小 typed 数据不含实际家属关系或该人物针对该头衔的 de-jure/逐规则结果，不能硬指 family、tier、de-jure 或其他单一分支，也没有证明另一个自然合格头衔一定存在。因此不写 fixture修补。

## 唯一 operator 下一新场的现有合法入口

在原 government checkpoint 暂停场景中，先从实际 GUI/title-holder原件取得真实 title fullID/key，并正常打开其实际任命窗口。使用既有公共 `appointment-full-pool` 只读 action；arguments 提供 `requested_title_id`、`requested_title_key`、`expected_law=appointment_succession_law`，以及 `navigation_step_id` 或 `title_reference_step_id` 二选一。**资格发现时省略 breakdown_character_id**，不要请求尚未确认在池中的 actor。

`tools/ck3_mod_acceptance_client.py:340–397` 已支持该参数省略并逐页64项完整合并；`tools/ck3_mod_acceptance_appointment.py:157–170` 只在显式请求 breakdown时才要求 getter与总分。该现有入口仍强制同PID/generation/paused actor/date/revision、请求→实际title关系、有效law、完整count/token与fullID/AI事实。不得手改label、用显示过滤名单替代base、猜title/人物ID，或把只读完整池成功当业务通过。

只有完整池实际同时含本场独立人类actor（human=true、AI=false、score_present=true）和可选实际AI时，才继续在同实际窗口请求 actor的真实 breakdown，然后按原 off/on/off 百万差分、原switch恢复、AI真实任命及继任完成观察。否则保留资格GAP；不能制造家属或候选、放宽资格、替换原业务。查询发现只是导航选择，沿用同一公共provider/client，不增加 per-product fork、新能力或新门禁。

原全部判据来源：`tools/ck3_mod_acceptance_cases/xqol_government_adapter.py:34–61,65–86`。本包不改变其要求或既有预算；后续场序、现场资格及容量仍由 Root/sole operator安排。

完整小证据和source pins见同目录 `R57-SMALL-TYPED-FACTS35.json` 与 `R57-MINIMAL-CAUSAL-SOURCE-CHAIN35.json`。原失败、原prepared和原live目录保持原样。
