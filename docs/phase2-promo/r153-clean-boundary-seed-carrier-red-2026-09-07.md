# R153 clean boundary 的 seed carrier RED（2026-09-07）

R153 冻结 commit 为 `4f17d3aaa6e48cb43594095f19ed9d60becde422`，产品投影
`phase2-full-release-r153-4f17d3a` 为 1,031 files / 32,278,871 bytes。产品树 SHA-256
`196e557e06ffa09ef488c819168f16237f5466089ab0d8087ac3f977398e4205` 与 R152 完全一致，产品 ZIP
SHA-256 仍为 `969156a1ab552d228e04325d2c18448b742a7c4a4696346fd686fe7e885067aa`；runner 修订没有改变
正式交付字节。no-launch preflight GREEN，SHA-256 为
`44afeff4ffa8072a0d739ab555e8a3b30845777de97715b57a2c20912f07d4e4`。

实机使用单一 CK3 PID `161112` / connection generation `1`。loader 303/303、fatal 0；默认 5 速从
R131 管理者 checkpoint 续跑。`tribute_mission.1002` 与 `.1005` 两次 drain 均 GREEN；本轮没有生成
`tgp_movement_events.0150`，所以不把 R152 新增的合同冒充为实机触发。manager recovery 最终 GREEN，
在 `date_raw=53154144` 得到 `review_now_eligible=true`、B1/Central/PP 全 false 的暂停 clean boundary。

暂停等待 1 秒仍没有生成 `zga_phase2_manager_seed.1`。runner 随后 arm 原生 date-only daily sentinel，
只提交一次 speed-5 resume，在 daily final-stage 后精确于 `53154168` 暂停：completed daily ticks 为 1、
overshoot 为 0、external pause 为 false、玩家 `32904` 仍 alive、active event 为空。再次暂停等待仍没有 seed，
所以本轮 scenario/seed RED；这不是产品 parser、loader 或 runtime RED。

载入 debug log 证明 diagnostic GUI 已执行并安装 acceptance-only health +10 / epidemic resistance +100
modifier，但没有证据表明 B1 数百日后结束时另一个 GUI animation state 会重新进入。R153 因此否定把
scripted GUI animation state 当成长期条件轮询器。最小修复从已证明执行的载入 diagnostic effect arm 一个
单实例 `days = 1` 隐藏 retry event：完整业务 gate 未满足时只调度一个 successor，seed 启动后永久停止。
该 fixture effect 文件由 4 个增至 5 个顶层 effect，仍满足每文件 1–10；它不写任何 `zg361_*` 产品变量、
receipt 或历史行，也不会进入 release staging。fixture、bootstrap、static 与 seed runner 都必须在 normal/`-O`
通过后才能冻结下一轮。

R153 manager recovery、runner report、cleanup、bootstrap event wait 的 SHA-256 分别为
`f6bae82fb3723817a606ab141a86ce5a276feebcea2a64341565ec3ab2184190`、
`3837b422c758a41baeaa4d5f4c62116f679548db81f604c0091680bf62ebbd67`、
`ab6d884b4c55046af75a04c737dc6d0c775a6a23f94f1a9de76ab3263ad1b132`、
`345defc4e3312dd6d33533ca8d97833395c329d3d5b2b9f3af524ee310ceac4a`。cleanup GREEN，restart count
为 0，最终 CK3 inventory 为空。玩法状态和事件判断使用 MCP/native；OCR/image 只用于非玩法 legal gate。
