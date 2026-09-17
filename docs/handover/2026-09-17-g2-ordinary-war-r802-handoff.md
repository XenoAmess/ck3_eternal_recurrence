# G2 ordinary campaign / R802 handoff

交接时间：2026-09-17（Asia/Shanghai）

范围：用户可运行预览、R797 Council 查询、R798-R802 WarID5 恢复/物质终局/cold restore、后续 ordinary campaign 队列。

权威合同：[`../autonomous-agent-progress/g2-requirements-v1.json`](../autonomous-agent-progress/g2-requirements-v1.json)

## 用户现在能否获取并启动

能。当前仍应交付已经合格的冻结 bounded ordinary preview，而不是把本轮新代码未经包装资格测试就替换进去：

- ZIP：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-r783-stage-20260916T134805Z-6cfba744\g2-preview-ordinary-5ac64152-r783.zip`
- SHA-256：`AA9CABB5D4CA709E55AB367A94D0C58A088AAD20D540B76F7990DAD1FC81517C`
- GO manifest SHA-256：`A5CB85FE0D9BF96EF844B68055532220498FE8E298F8B2769515EC026AAD4B1D`
- live qualification SHA-256：`1EF45C2B14D43C6AA2E953D5BB0E56925F181CDC3819FA3ECE70BCC6F7E5361A`
- exact CK3：`1.19.0.6`，EXE SHA `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- 启动、状态、stop-file、checkpoint、日志与 cold restore：[`../ck3-native-ai/g2-preview-release.md`](../ck3-native-ai/g2-preview-release.md)

支持边界仍仅为该冻结 R783 标准封建 `xar_off` bounded continuation。它不广告任意存档、Council、战争终局、自然继承、整局或第二种子。R800-R802 已把新战争恢复链验成 production-live，但尚未进入新合格 ZIP。

## 权威状态

- G2：**1/8**，仅 G2-M1 complete。
- GEN-034：**2/4**；ordinary WarID5 不能代替 Raiktor-specific C/D。
- Council final gate：**1/4**；public query/action/advertisement OFF。
- 首条 1066→1453：0/1；双种子：0/2。

## Git 与代码

本轮功能最终 master 点为 `aba36a4efd4d4b9fb740acbde30f67c54cbf7801`；包含：

| Commit | 作用 |
| --- | --- |
| `0aa366ef` | durable Council gate candidate materializer |
| `b9b6f249` | terminal `submitted_pending` 后立即保存 checkpoint |
| `881e1ba5` | exact-build sender-side outbound white-peace receipt query，native/driver/service/MCP |
| `f5a8914d` | bounded production-owned query CLI/runner |
| `36a25a55`, `c9c371b4` | ordinary `xar_off` 与 succession lifecycle 绑定 |
| `851c36dc` | cold restore ledger 接受 checkpoint-prefix truncation |
| `aba36a4e` | 已物质和平后 30 天内禁止立即重启战争 |

测试：sender query Python normal/`-O` 3/3；recovery bookkeeping normal/`-O` 9/9；postwar policy normal/`-O` 5/5；新 native DLL 11 个聚焦 CTest GREEN。DLL SHA `DA7CA992...7D3B7`，injector SHA `46D43267...C75F`。

所有功能分支均已普通快进进入 master，随后远端/local 临时分支和 tracking refs 已删除；无 merge commit、无 shared-master force push。

## 实机轮次

| Round | 结果 | 关键证据 |
| --- | --- | --- |
| R797 | GREEN query / evidence-not-observed | 14 provider、11 ordinary；already3/guest0/pending0/replacement-denial0；report `B6345292...4641` |
| R798 | harness RED | readiness timeout，query/action/date/checkpoint 全零，pair 未污染 |
| R799 | harness RED with diagnostic exact-absent | query 成功但旧 ledger 错误假设 append-only；未授权动作 |
| R800 | GREEN_READ_ONLY exact-absent | history264→260、restore261；一条 sender query；report `257104F8...133A` |
| R801 | GREEN material, cold pending | 唯一 white peace；h269 pending checkpoint；WarID5 独立消失；下 turn 解散残军；h289 和平 checkpoint `F48AD4E5...D97F6` |
| R802 | GREEN production cold restore | 新 PID；恢复 h289 并截断弃置尾；`native_postwar_reentry_cooldown`，+32 天，零 reoffer/declaration；h293 `DFC96CFD...71AF7` / `7C79FE4C...48EF0` |

R801 的 20-turn 尾部曾在 turn16 重新向同一目标宣战。该 history290-301 尾巴没有被冒充 postwar 证据；它被封存为真实 B1，并由 `aba36a4e` 修复。R802 已实机证明修复生效。

## 下一 ordinary campaign 恢复点

封存 pair：

`D:\ck3_mod_rewrite_process_assets\g2-war-r802-postwar-h289-aba36a4e\final-pair-h293`

- checkpoint SHA：`DFC96CFDF8BD8AB72D6A6FC8429E2E50E5B09B40767D4AC48354D540ACD71AF7`
- driver SHA：`7C79FE4C6338925284C854DE23B2C4F3F30D291C7AF0854DE9823BECE9D48EF0`
- date：`53150976`
- actor：`31853`
- active wars / armies：空
- lifecycle：ordinary campaign succession / `xar_off` / no pact

下一次启动前必须从这个 pair 建立新的隔离 state，使用届时 clean `origin/master` 重新 `prepare-state` / `ordinary-seed-rebind-v1` / no-launch preflight；不要直接运行旧 R802 environment，因为报告提交会改变 source commit。登记新的单调轮次后，再由正式 `g2_preview_operator.py run -> native-auto-run` 继续同一 campaign。

首选下一个 live 工作包是把该 pair 作为既定 100-year/full-campaign 前缀继续，而不是另开专项永久长跑。被动采集自然玩家死亡/继承与 `.1007`；治理、婚姻外交按已有正式策略消费。Council 只有出现 materially-different guest/pending/non-fireable scene 才再查询；不要重复 R797 场景。`.0030` 需要独立合法 celestial/TGP 自然场景，不得用标准封建线冒充。

## 证据位置

- R800-R801 root：`D:\ck3_mod_rewrite_process_assets\g2-war-r800-white-peace-h260-851c36dc-`
- R802 root：`D:\ck3_mod_rewrite_process_assets\g2-war-r802-postwar-h289-aba36a4e`
- R800 seal：`evidence\R800-post-run-seal.json`
- R801 material/projection seals：`evidence\R801-material-seal.json`、`evidence\R801-postwar-h289-projection.json`
- R802 seal：`evidence\R802-postwar-cold-restore-seal.json`
- 单实例 ledger：`C:\ck3_mod_rewrite_process_assets\ck3-single-instance-rounds\R797-closed.json` 至 `R802-closed.json`

## 不得误报

- ordinary WarID5 完整链只关闭当前标准封建 exact-build branch 的连续运行 B0，不自动更新任何正式 G2 milestone。
- GEN-034 仍是 2/4；Raiktor C/D 的投影、评估、唯一动作、物质结果与冷恢复合同仍需各自证据。
- R797 没有关闭 Council 新门；后三类仍 OPEN。
- 当前可交付 ZIP 仍是冻结旧包；新 master 只有在生成新 ZIP 并通过匹配的真实 package smoke/cold restore 后才可替换交付地址。
