# 重整河山 0.4.1：CK3 1.20.0.3 维护准备

2026-10-05 状态：**PREPARED / RUNTIME NOT_RUN / NOT_PUBLISHED**。候选源码元数据为 `0.4.1` / CK3 `1.20.0.3`；当前公开版本仍为 `0.4.0`。本次只准备版本声明、公开文案、冻结更新说明和实际门槛界面输入，未启动 CK3、操作桌面、使用原生 Steam SDK 或上传。

产品：`mod_reclaim_the_motherland`。唯一发布目标：Workshop `3798404599`。上一公开 tag 为 `reclaim-motherland-v0.4.0`，commit 为 `23078f51d1b294b9db5dfc0a195051a48e3563a4`；候选 tag `reclaim-motherland-v0.4.1` 尚未创建。当前机器游戏为 CK3 `1.20.0.3` / build `25652598`，EXE SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。

## 已审阅源码与旧证据

源码迁移仍为[2026-10-01 兼容专题](reclaim-the-motherland-ck3-1.20-compatibility-2026-10-01.md)记录的改动：新版提议附庸 modifier 布局与品级公式、私有后朝身份规则、三省六部预算 flag、群雄割据重组和改国号顺序，以及新版天命条件。`1.20.0.3` 的七份原版依赖与已审阅 `1.20.0.2` 完全同字节，比较记录在 `C:/workspace/ck3-upgrade-20261004/p2-rmtm-ccc-readiness-agent-01/source-12003-compare.json`，SHA-256 `657a2ce5060fca87e804dfcfa6b5239dd81cdf48b25ae805966b1d10930b6aa2`。

已通过的 `.2` 静态合同、解析和构建继续复用；本轮不重复旧业务 L0，不重新生成同字节文件，也不把它们写成 `.3` 实机 GREEN。生产机制与 GENERATED 文件没有修改。只有候选 descriptor 及相应静态版本合同从 `0.4.0` / `1.19.0.6` 改为 `0.4.1` / `1.20.0.3`。

## 核心链冷输入

原准备包入口：`C:/workspace/ck3-upgrade-20261004/p2-rmtm-ccc-readiness-agent-01/HANDOFF.md`。原 36 文件投影、14 文件原字节夹具及 `fixture-state/profile` 保留原样；原投影仍携带旧 descriptor，只代表当时输入，不能当作新 tag 的正式发布树。有效规则和初始观察计划在 `plans-02/rmtm/`，不要使用保留的错误 `inputs-01/rmtm/frontend-rules-plan.json`。

最短前台链：

1. 当次取得屏幕独占及新鲜 Steam 离线原图，启动一次新的隔离 profile。实际 Start 后在 D0 核实当前宋帝、天朝、霸权、独立及初始化标记。完整 87 个游戏规则必须以实际应用实例读回证明。
2. 逐个真实日推进，遇未知事件停止。原版 `tgp_dynastic_cycle.0081` 只有一个选项，但仍应先核对当次真实事件 definition、ROOT、instance、revision 和 shown/enabled 选项，不能按旧 ID 或固定屏幕坐标盲点。
3. 到 `RQA120: TEST READY ui_after_chaos` 停留，取空法理后朝、个人领地、忠臣封臣树、九席原任和预算控件。夹具决议【继续重整河山核心验收】描述显示两个当次真实附庸目标；分别取实际【提议附庸】的 `-50`、品级差大于一级时固定 `+10` 及其他原版理由。
4. 执行唯一夹具继续决议 `rqa120_continue_decision`，确认文本为【继续继承验收】，再自然推进到 core DONE。既有 36 marker 每个恰一次，FAIL 族为零，实际诊断须归因并保全。

该夹具先切换至继承人再杀前任，只能证明相应 title/realm 继承结果，不能算玩家原生死亡/Continue 窗口验收。定时值从生产 `1825` 日压缩为夹具 `14` 日，不能把实际压缩到期写作自然经历五年。该核心夹具在同一 effect 中连续建立 50% 和 51% 状态，因此相关 marker 不能单独证明两档实际生产决议界面。

## 独立 50% / 51% 生产决议界面 cell

额外冷输入：`C:/workspace/ck3-upgrade-20261005/rmtm-release-readiness-agent-01/threshold-ui-inputs-01/`。此输入将原夹具 14 个文件逐字保留，另加 4 个文件，总共 18 文件；profile 仍为 6 文件、只加载本产品和本夹具。原核心 profile 不修改。

新增脚本从旧夹具 threshold effect 的既有县领转移片段拆分出独立停点；不复制或调用生产复辟 effect，不改变 `rmtm_claim_restoration_decision`，不自动确认生产决议。两个新脚本单独 parser 为 `2/2`、零错误；未重扫旧产品或旧夹具。新 startup policy 已通过本轮冻结 source-04 的真实 `load_bound_fixture_start_policy`，只证明精确输入可接纳，不证明游戏结果。

实际前台步骤：

1. 同样实际 Start、自然到 Chaos，并停在 `ui_after_chaos`。
2. 选择夹具决议【验收：准备50%复辟对照】并确认。原核心驱动随之停止，实际控制状态为至少 50% 且不足原版 51%（伯爵领为离散数量，不保证比例恰好等于 0.5000）。查看真实生产【宣称复辟】的可见性、禁用状态和门槛失败理由，保存当次实际画面和 marker。
3. 选择夹具决议【验收：准备51%复辟达标】并确认。它只建立至少原版 51% 的状态，随后停留；重新查看同一个真实生产【宣称复辟】，保存实际可用性、门槛条件和原版【宣称天命】锁。
4. 主线程手动选择、确认真实生产【宣称复辟】。预算或复辟 Confirm 不能冒用白绮或 AUB 的 typed 窗口资格；鼠标兜底必须遵守原始截图、坐标映射和回执合同。
5. 选择夹具【验收：核对实际复辟结果】。该决议只读取已发生的结果，不授予头衔、不执行复辟、不推进时间。必须出现 `RQAUI: TEST PASS actual_production_restoration_effect_observed` 和 `RQAUI: TEST DONE threshold_ui`，并独立核实 `h_china` 持有者、生产 flag 与后朝销毁。该 cell 不代替核心继承、到期或预算取证。

当前状态始终为 **NOT_RUN**。计划、parser、输入 loader 或按钮 ACK 均不是业务成功。

## 本轮元数据验证与新候选投影

授权元数据修改后，专用 static validator 通过；只执行修改版本断言的单个 builder `test_manifest_identity`，通过 `1/1`，没有重跑旧业务合同测试。新的官方 builder 候选在 `C:/workspace/ck3-upgrade-20261005/rmtm-release-readiness-agent-01/production-0.4.1-candidate-01`，36 文件，严格 manifest 复核通过；相对旧 `.3` 准备投影仅 `descriptor.mod` 字节不同。

- 候选 manifest SHA-256：`8db6199d86d97eb64dd7f376d686a55973e5fc92304b60d18d2438c715a64ea0`。
- 候选 ZIP SHA-256：`ffa40557758efbcdb46b847224f48ad7ddebb6855f9f5109fd5892396100d07f`。
- 候选绑定 inspection revision `45c432f4090541ef8905bf9312f86750a95c0708` 及本轮已授权、尚未提交的元数据字节，`git_tag=null`；**不能当作正式 tag 构建**。
- 应优先使用已绑定这个新投影的 `core-0.4.1-state-01/` 与 `threshold-0.4.1-state-01/`，各 6 文件纯净 profile。前者复用原 14 文件 core 夹具，后者用 18 文件阈值 UI 变体；两个 policy 均通过冻结 source-04 的真实 load-bound 校验，均未启动。
- 本轮验证包：`.../metadata-verification-01/result.json`，含命令、退出码、stdio hashes、manifest、ZIP 与两个实际 profile。

Root 现有 `aub-core-12003-candidate-02/runtime_harness_observation240_continue_02.py` 的 policy 和 manual 两条分支都显式调用 `create_server(driver, profile_dir=args.state_dir / "profile")`，无需本产品另行修改 MCP 平台；若换用旧 harness，仍须检查实际源码，不能假定 manual 分支已绑定日志目录。

## 发布准备与剩余门禁

候选公开 description 不再沿用旧版验收声明；四张既有工坊图片明确标为 `0.4.0` / CK3 `1.19.0.6` 历史实机。完整中英更新说明为 [0.4.1.txt](../workshop/change_notes/reclaim-the-motherland/0.4.1.txt)，冻结量和 hash 在同目录 `0.4.1.freeze.json`。相对上一公开版的[永久 changelog 草稿](release-changelogs/reclaim-motherland/0.4.1.md)保持 DRAFT / NOT_PUBLISHED。

完成所需：新版核心与上述实际界面验收、原版规则对照及必要存档/命名回归；本轮最终 tag 的 36 文件正式构建；同一工坊 item 上传；匿名精确回读完整 Change Notes；实际新缓存逐文件复核及本产品要求的 fresh-cache 验收；上传后重建无 ID staging；立即恢复 Steam 离线并保存当次原图；最终 changelog 与发布证据提交并推送 `master`。任何一项缺失都不能标为 release-complete。
