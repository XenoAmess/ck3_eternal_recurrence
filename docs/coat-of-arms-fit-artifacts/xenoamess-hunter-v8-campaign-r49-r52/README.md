# xenoamess-hunter-v8 campaign R49–R52

状态：`passed-limited`（2026-09-21）。本目录冻结 Gamma G3 的角色设计器王朝家徽 → 战役保存 → 新进程冷重载证据。它只提升实际走通的王朝路径，不把角色或头衔家徽、战役内编辑器重开、通用二进制存档解析器写成已支持。

## 冻结身份

- 实现提交：`9c77d7a9`（原生语义动作）与 `30e2127f`（仅对 campaign-root completion 同帧竞态做三次有界重试）。
- CK3：`1.19.0.6`，`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- 原生 DLL：`C:/xb/coa-g3-r39/xar_ck3_bridge.dll`，SHA-256 `42FE982AC89876DF7F72448AB7E708D3337A878D99EF92DD07CA99F39C7B7E6E`。
- 全部 live run 使用 fresh userdir、Steam 离线、typed native GUI activation；没有 OCR、键盘、鼠标或固定坐标。

## 追加式 attempt

- R49 原样保留为 RED：Apply/Copy/reopen 已通过，但首次进入地图后的 campaign-root 查询返回 `campaign-root completion snapshot changed`；cleanup GREEN。原始报告 `D:/ck3_coa_gamma_g3_r49/raw-report.json`，1,610,456 bytes，SHA-256 `574F3B3927C54270F9166350529E9379E3BDE1CD1EA3D4AB7181C473FE58BDED`。
- R49 后仅加入窄化的三次重试；未知 native rejection 仍立即失败。对应合同测试总计 18/18 GREEN。
- R50 GREEN：角色设计器王朝家徽 Apply → Finish → reopen/Copy → 关闭家徽页 → 生成合法名字 → Finalize/确认 → 大厅 Start → paused campaign root → `save-checkpoint` 全链通过。原始报告 `D:/ck3_coa_gamma_g3_r50/raw-report.json`，2,571,369 bytes，SHA-256 `68C2E14E189B0F4121ABFAF677817CE931C1F5E5A82FB4299DE29E35E13D0614`；耗时 220.272 秒，cleanup GREEN。
- R51 原样保留为 RED：冷启动调用使用了新 pipe 名，v2 driver-state 在启动 CK3 前 fail closed；checkpoint 未改变。报告 1,145 bytes，SHA-256 `991A04C421D3C5B9CEFCB61A18F55CBE7FFA871BF3B8232B6EDEA62E31D4E467`。
- R52 GREEN：沿用 v2 driver-state 的原 pipe 身份后，新 PID `25132` 替换旧 PID `30384`；角色 `61075`、日期 `53144328`、paused/map-ready、campaign root 和 cleanup 全部一致。报告 `D:/ck3_coa_gamma_g3_r50/cold-reload-r52-report.json`，51,192 bytes，SHA-256 `005B8973565D88134F146731A9844263410FFCC91B9152ED1495E4C0E12DF615`；耗时 183.549 秒。

## 家徽与 checkpoint

- R50 原生 Copy key 为 `coa_rd_dynasty_4128508758`，331 bytes，SHA-256 `AEECE65224C8DBB86FCBB59D8535C1BE4CAD6458248CF54E3EFBF6E569E09E3D`。
- 语义为 `pattern_solid.dds`、`rgb { 17 83 149 } / white / black`、`ce_martlet.dds`、mask `{1 0 0}`、position `{0.37 0.61}`、scale `{-0.42 0.58}`、depth `1.01`、rotation `-23`。
- checkpoint 为 50,461,746 bytes，SHA-256 `F368D77D38B559422961BE2BA9A2F543406E415812D3EACDF83FA59B4CAFA3EF`；R52 冷启动前后 hash 不变。
- [checkpoint-audit.json](checkpoint-audit.json) 在存档 metadata 和 serialized game state 中找到同一 204-byte exact-build tokenized 语义片段，共三处，fragment SHA-256 `8C0ABD44CCA61138E830FBDEA7007EDBCFEB5A59E5A45116C13DD7A0CCD786EA`。该审计器只识别本次冻结的 CK3 `1.19.0.6` 片段，不是通用存档解析器。

## 支持范围

| 目标 | 状态 | 证据边界 |
| --- | --- | --- |
| 角色设计器中的王朝家徽 | `passed` | 原生 Apply、Finish、reopen/Copy、开局、保存、二进制语义记录和新进程冷重载全部闭环。 |
| 战役内重新打开同一王朝家徽编辑器 | `limited` | 存档与重载语义已证明，但当前 exact-build route 没有安全的战役内编辑器入口。 |
| 角色个人家徽 | `not-supported` | 当前设计器路径绑定王朝，不外推为角色个人家徽。 |
| 头衔家徽 | `not-supported` | 未建立稳定目标寻址、编辑器重开和保存/重载矩阵。 |

结论不依赖“Finish 成功”的单点推断：它同时绑定提交前后的 native Copy、checkpoint 精确 bytes、存档内语义片段、替换进程身份以及冷重载后的角色/日期/campaign root。
