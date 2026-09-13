# “自动升级建筑”决议插图

## 当前资产

- 人物参考：`images/glassfire_avatar.png`，SHA-256 `635FE7827B75008AF4D72C234C071A8D18593D26D2CFE0EF336A3B24CD77A935`。
- 定稿源图：`images/auto_upgrade_buildings_decision.png`，`1983×793` PNG，SHA-256 `8411B32F663E4208B66D446B5DE9A59AA109A210923850C7243F47F759C52805`。
- 最终视觉要求：人物忙于处理堆积的建筑图纸与公文，神情安静、悲伤、疲惫，而非愤怒或急躁；保留参考图的绿色代码雨、RGB 错位、扫描线与青红赛博撕裂。
- 最终生成提示词：`images/auto_upgrade_buildings_decision_prompt.txt`。

源图由 Codex 内置图片生成能力按用户逐轮反馈生成。提示词和人物参考用于记录创作意图；生成式模型不承诺从提示词重新得到相同字节，因此已选择的 PNG 才是后续投影的权威源。

## CK3 投影

运行：

```powershell
py tools/compose_auto_upgrade_buildings_decision_art.py
py tools/compose_auto_upgrade_buildings_decision_art.py --check
```

脚本读取源图真实宽高，按目标 `1100×440` 比例居中 cover-crop，不拉伸，然后生成 DXT1 DDS：

`mod_auto_upgrade_buildings/gfx/interface/illustrations/decisions/decision_auto_upgrade_buildings.dds`

当前 DDS SHA-256 为 `B41C0961BE1EE9B8046CC2CA439E611C1200664779974CFD9DD6962D7AD688F1`。启用与禁用决议共同引用该资产。静态校验会从权威 PNG 重新编码，并逐字节比较 DDS，同时检查尺寸和 DXT1 FourCC。

加入该 DDS 后，正式 Workshop staging 从历史 15 个运行时文件增加为 16 个；源 PNG、提示词和生成脚本不进入 Workshop payload。

## 实机验收

`desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0033` 在 CK3 `1.19.0.6` 中使用 exact 16-file release projection 完成聚焦验收：

- 系统级 `exclusive_launch_lock` 等待 `0.114` 秒后取得唯一 CK3 槽；受管 PID `27452` 退出后 Get-Process 与 WMI 均为 0。
- 原生决议框正确加载定稿图，没有缺图紫块或异常拉伸；人物的悲伤疲惫表情、书写动作、堆积图纸、绿色代码雨、RGB 撕裂和施工城堡均在实际裁切中可辨，按钮与文字仍清楚。
- 六项策略 hover 与自然确认文案顺带保持 GREEN；项目诊断为 `[]`，产品与 fixture 树未变化，一次性 userdir 已删除，受保护存储未变化。
- 顶层报告：`D:\workspace\ck3_auto_upgrade_runtime\phase4-art-live-20260914\report.json`，SHA-256 `0C0C380F8C953180EA63EB0D525369FB5CFD3C2E2C577869CB0C5BC2B7952663`。
- 原始桌面截图：`cell\05_policy_selector_clean_surface.png`，`2560×1440`，SHA-256 `CA1687BACED2205882C27192E8546705079E03358C213454CEE57041CC38DA9D`。
- 人工视觉复核：`visual-review.json`，SHA-256 `0008BC922C59DDC668E470FCC407F9AF64FCADD4FA0CB8F2CFE54435EB049E18`。

该轮只覆盖 R0032 后新增的美术加载面，不重复 R0032 已闭合的玩法状态机和建筑／付款矩阵。
