# R0047：双启动标记对照

R46 的首次 campaign 查询在进入执行器前取消，owner pump 停滞原因仍 UNKNOWN。本轮只验证已采用的启动顺序候选：本场完整 history-loaded completion 与 In Game 两行均出现后才注入，先后不限；原生双 owner 帧、单次注入、900 秒绝对期限及业务输入保持。准备或单测通过不等于实机修复。

## 新预算与实际 Source08

R46 的 4 GiB 预留已按实际闭场核销，剩余预留为0；已知保留逻辑量924,798,428 B，历史峰值和精确物理占用未测。R47 于06:28:12 UTC在原卷锁下登记新的4 GiB峰值预留。保守已用120,604,915,355 B，加本场峰值124,899,882,651 B，小于既有128 GiB限额；现场空闲626,470,379,520 B。配额例外仍到2026-10-12T05:19:51.814083Z，不因续跑延期。

- [实际准入](C:/workspace/ck3_lyd_runtime_20261004/r47-root-storage-admission-20261010-001/ADMISSION.actual.json)：4,775 B / SHA-256 `6276902ee2150dd757a774f085c49d4d68d6cf880e095cefe12cbdb5db4f8db4`。
- [原预算核销](C:/workspace/ck3_lyd_runtime_20261004/r46-root-storage-admission-20261010-001/CLOSED-RESERVATION.actual.json)：3,042 B / `2166ecf90af0736dacfde648de96000106ecb368d01918fbff0e0adc3dfcf322`。

Source08实际于06:29:24至06:29:37 UTC单次生产，12.965秒、exit0。冻结提交 `86214a2b770ba16ff79ff0c8f8953df988afe67a` 的唯一父是Source07 `e8562cc04fae188f73c59ed33215126bb8bca7ac`；四路径取自已发布 `cfc17e346e5b017dbe8b57eeca1fdaaef31a4eaa`，包括runtime、专属延后注入测试、graphics helper及其测试。7,902继承文件仅copy/stat并继承已验证SHA，四个变化文件重新hash。未生成全树ZIP、未重编native、未改变MAIN分支或index。

实际选择为 `C:/csr8` 与 `C:/workspace/ck3-common-runtime/20261010-007`；[SOURCE08-BIND](C:/workspace/ck3-common-runtime/20261010-007/SOURCE08-BIND.actual.json)绑定manifest 5,221 B / `255fd41ba7d5156660054ccbeb03ebded8b2e6978e838d94968797a5ddf15b3e`，runtime 2,011 B / `993e19f335efadbac6232373f211707371bc02c8c3625e9700ca1b80fe87aa75`。host、DLL、injector及完整native输入沿用Source07精确pins；Source08是本机运行输入，不是新业务验收或产品release。

源码提交cfc17e346的[Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38030611652)与[Linear history](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38030611518)已终态success，实际一次查询06:29:26 UTC；LYD专题未触发。采用后的16项启动测试及17项缓存测试见[R46报告](2026-10-10-r46-startup-query-red.md)，不重复运行同一套检查。

下一步从实际闭场R44重新派生新key的缓存，再走公共prepare/plan/preflight/allocate/run/verify；旧seed不改写、不绕过key校验。原D2a存档、71正式文件加6 overlay、actor31254、日期53144712、事件instance121与option0均保持。现场须重新取得并亲审新鲜Steam离线与nonce画面。当前一期仍NOT_GREEN，75%仅为工作量估计。
