# QOL R67/R68：路径修正与候选资格缺口

2026-10-10。本执行线只负责天朝二期以外原十 mod 迁移；正式交付仍 **7/10**，剩余顺序 QOL、重整河山、361 既有 0.3.1 维护。G2/天朝二期不在本线范围。

## 已发生的实机结果

R67（a168，Source17，Main afba3d1）个人自足负例启动资格成立，共用 anchor/map 通过；原步骤 3 读取顶层 `player_legitimacy_v1` 失败。实际字段位于 `campaign_root_context.player_legitimacy_v1`，status=available、raw=375431000、scale=100000。原35步为1 PASS、1 FAIL、33 NOT_RUN，推进0天；自然回复、奖励和D1未执行。两份 PAM original-plan 的初始/最终读取路径及对应合同 pin 已修正，未改期望值、步骤、天数或业务字节。旧 R67 与未消费但绑定旧合同的 PAM+ 输入不能冒充新合同准备结果。

R68（a169，Source17，同一 Main）使用一次原版 `change_merit=2000` 准备自然1066高丽玩家31883。唯一等级诊断证明 raw=200000000、cap=5、native level=3、target tier=3、当前规则 floor=3，等级资格成立。`d_haeju` 16982 的完整引擎池为5名AI；唯一允许检查的自然县 `c_gokju` 16974 为38名AI；两池均无玩家31883。两law百万分三相、恢复及真实GetHeir **NOT_RUN**，整体仍资格 GAP，不能由等级通过计作任命通过。

R67于13:20:57Z真闭场（normal=false，OS退出0的失败回执保留）；R68于13:49:23Z正常真闭场，OS/native均0。两场各一次公共verify退出2，allocator/keeper已停止，三项现场资源释放。证据：`C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/pam_negative--a168/ROOT-FIELD-RETURN-R67-01.json`（9635B，c9d726317473d638468f55cb87801ec8f84a2c512351567d050c88aa1ee79e7a）；`meritocratic_appointments--a169/ROOT-FIELD-RETURN-R68-01.json`（12726B，ec0bb803abcac210b9479847171c01f6d7104f27143d2e03e51501a94a82a4bf）。原始失败不覆盖。

## 共用客户端修正与下一场

只读任命收集遇到 `Appointment collection rejected:` 时，共用客户端重新检查原 deadline、reserve、fresh frame 和已提交步骤的健康完成状态；通过才返回 REJECTED/NOT_ASSESSED 并保留同一检查点，允许合法刷新同一窗口后查询。原步骤不重放。宿主错误、未完成步骤、其他异常仍须停止；本改动不提供 R67 这种 host.error 的热续跑。

聚焦测试 `Wiring.test_r66_collection_rejection_keeps_checkpoint_but_host_failure_stops_it` 实际1项通过，0.056s，命令退出0；覆盖收集拒绝后的新引用重试以及宿主失败仍传播。尚无本修正的新实机信用。实际公共入口导入 Main 中的 canonical client；Source17旧 manifest 内外置客户端候选路径仅保留历史来源，不能称为当前实际导入。冻结 host/DLL 未改，不因此重建 Source18。

下一场复用已准备的 admin34；每次开关切换后合法关闭并重新打开同一领地窗口，取得新引用/revision，再收集全部页。精确缓存/getter一致性、完整池、百万分、恢复及真实继任门禁保持。贤能池继续只读定位实际源集合/过滤/截断原因，不盲目加资源重开冷场。原版 `e_goryeo` 确含 `k_goguryeo/d_haeju`，不能把无玩家解释为静态非de-jure；实机de-jure尚无新证据。

## 发布与存储

1.1.1 Change Notes仍DRAFT_NOT_PUBLISHED，当前4487B、3257字符、31行，SHA-256 `4040d16558f2af2aa2b02d0d5e0e29b1b86eb2dec219cc8107090b00b2c78cc0`；旧3991字符稿保存在 afba3d1 Git历史。尚未创建正式tag、上传或公开回读。

R67/R68真闭场后分别仅清理可再生SDK cache 157999920B/3780files、161198896B/3824files；累计实际删除33268383896B/620512files，无损压缩另计。R68后free30157127680B；新场仍需fresh准入，不降低原30071062528B容量门槛。旧失败、当前证据、572个增量构建依赖及未授权清理对象保留。Root交付helper154原16KiB/600s窗口不重置，超时如实记录，不替换为合规成功。
