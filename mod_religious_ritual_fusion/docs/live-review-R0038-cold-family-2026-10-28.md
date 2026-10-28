# R0038 冷载、五日采用及商店实拍

`machine_id: 4-8e1c2f1861`；2026-10-28 UTC；场次 `4-8e1c2f1861--religious-ritual-fusion--R0038`，keeper a45，运行源码 `f31417c18f414f260d5f439ad1f8cb85fb9054cc`。CK3 1.20.0.4，EXE SHA256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。

本场已正常关闭。冷载零日11项通过；五日阶段6项通过、2项未完成，整场业务仍不通过。八名家属和一名封臣的实际采用已得到独立存档读回，不能因阶段未完成而抹去；另一名封臣的原生回复仍未知，不能将预览拒绝或模组待确认名单算成回复。

## 冷载与五日实际结果

原始输入是R0033的真实Save3：68446460 B，SHA256 `45f225aa8f60542c63696cb42fe259dd8ad4a04b75fbf328866fadaea02a9f5d`。新Game PID2592、出生FILETIME `134376712624303320`，不同于来源PID13212／`134375895005445378`。只挂载正式RRF与被动只读fixture；正式89文件、fixture8文件、编译合同1文件及外层descriptor均实际核对，没有重新seed、融合、编辑、邀请或派发家属事件。

零日为1066.9.17／53144376。原只读决议触发一次`rrfa.22`；独立Java V4检查原生Save0，结果153、来源150／151／152、Faith13／103、Religion8的完整有序AST及相关对象表ID均与来源一致。28处人物`landed_data`差异如实保留，没有声称整个角色图相同。

原CaseClient连续完成五次自然日请求，每次`requested_interval_complete=true`，日期53144376→53144400→53144424→53144448→53144472→53144496。没有额外游戏日、事件选择或重复业务输入。第5日只刷新结果一次并保存一次；同一Save5为68751885 B，SHA256 `92f40904fbc8dab45ecef0646e1eba20b6954afd275b5f6173efe37dc8d3d87e`。两个V4原进程均退出0，在同一原生存档句柄的禁止写入／删除保护下完成前后身份核对。

| 对象 | 零日→第5日实际后态 |
| --- | --- |
| 配偶36311；子女38924、39348、39979、40526、40695、40847、41032 | 每人都存活，Rite150→153，Faith13 |
| 已邀请封臣34973 | Rite153／Faith13；模组pending已清除 |
| 已邀请封臣45458 | Rite0／Faith13；仍在模组pending；原生接受、拒绝或送达结果未知 |
| 长名封臣36445 | Rite150／Faith13；未在invited；预览拒绝不能算实际回复 |
| 玩家31254 | 仍采用153；虔诚5400，已记创建费用500；冷却tick3650→3645 |

结果153的完整有序AST、五段文本、两种图标和有序RGB均保持。来源150首领34232→36445，Faith13的四项`tenet_popularity`分数505→501、1311→1307、40→42、414→410；自然人物／对象表变化已逐项保留，不授全图不变结论。

打开真实信仰窗后重新绑定当前153，原生完整catalogue实际列出7项美德和7项罪恶，含各自trait ID、key、classification及十进制权重；数量来自当次原生结果。没有沿用零日列表或预设七项。家属转换的实际后态不支持此前“缺派发”的猜测，未应用相关候选修复。

五日阶段未完成项分别为45458及具体原生回复证据，以及独立原生家属guard谓词资格。每名家属的存活、旧Rite/Faith、首领及序列化关系输入已重读，但guardian／hierarchy等原生trigger未独立读取；八人实际采用与该观测边界分开记录。SDK保存绑定仍为false，原生存档不授SDK continuation通过。

正常闭场后另用原Java V4读取同一Save5的完整`pending_character_interactions`：实际六条在队交互均属于其他角色，没有actor或recipient为31254的条目。这只证明保存当时没有玩家在队交互，不能推断45458从未收到或已拒绝。第二个有界`opinions`／`relations`读取因`projection byte cap exceeded: opinions`真实退出1，无报告；不得解释成没有意见或回复。两个原wait与前后同一存档句柄、身份、SHA均已封存，原五日6/8判定不回写。该补读位于`C/metadata/normal-close-a01/postclose-tail-a01/native-replies-a01`，`CLOSED.json`为3432 B／`98f67e18f28d69e942fd3fe8cc363ad9ff1c04d73b53e57ea0bc1ba2fe805fb1`。

## 资源终态与证据

15:11Z开始原CaseClient的typed正常退出，15:12:55Z host终态。原生退出0、保留OS句柄退出0、host原wait0、keeper原wait0、allocator原wait0；公共run、verify及Root serial原wait均为2，保留业务未完成。`normal_close_qualified=true`。15:12:58Z单次SCREEN CAS14461释放，显示恢复1024×768。

外置根 `C = C:/workspace/rrf-development-20261024/review-fixes-a01/retry-cold-R0033-a01`：

| 证据 | bytes／SHA256 |
| --- | --- |
| `metadata/normal-close-a01/root-business-oracles-a01/R38/zero-day-a01/ROOT-PHASE0-EVIDENCE.actual.json` | 30972／`bbe42ec4a2c9af509819defa11cdb77575c0685c6b0e5f616bb3c4a3bc691cad` |
| 同根`day5-a01/COMPARISON.actual.json` | 325828／`48b555973d8df08dcc884cce7640097145d08ac92933c218038984264f6ffd1a` |
| 同根`day5-a01/ROOT-PHASE5-EVIDENCE.actual.json` | 20487／`8f3ce9a2a62eb817e75b929731cff9d0ccb05f86261d71eab1c1de24f6028699` |
| `live/4-8e1c2f1861--religious-ritual-fusion--R0038/case-output/actual-five-day-existing-invitation-poststate-root-result.json` | 4617／`9d030947d29e7ff6e416df50c87e204371cf603fc096e33d1c8df8b05ea197a0` |
| `metadata/public-operations-a01/root-execution-a45/ALL-ORIGINAL-TERMINALS.actual.json` | 13972／`da174431c48d1dd8a7811300e2491c40ef9a61775aea6ac0525bd66757a0b0f3` |

具名Save0已被合法Save5覆盖，旧原件不可读取；零日比较使用封存V4／custody，不伪称重新读取旧原件。来源Save3与当前Save5保留，必要证据用途复核仍为2026-11-01T04:00Z。

## 已完成的商店图片更新

本场两张实拍已追加到同一Workshop **3826756673**第11、12位：五日家属结果页、当前礼仪美德／罪恶。原图无裁切、无合成；上传仅JPEG编码，均2560×1440。第0日含远程工具浮层的诊断图未上传。旧十图顺序保留，新图匿名HTTP200、bytes／SHA精确匹配；全文说明2144字符、43行经匿名API逐字核对，SHA256 `4c2e03b17c2a148d6408017a9f3785b9b012bf5e7b1d8fa5fa51f60b1331e887`。

公开下载仍为0.1.0-alpha，新增图片标注未发布0.2.0开发预览；没有模组内容或Notes上传。15:29Z后台原生确认Steam仍离线；浏览器SCREEN CAS14464已释放。详见[本次素材与公开回读](evidence/workshop-media-readback-R0038-2026-10-28.json)和[图库说明](../../workshop/religious_ritual_fusion_screenshots.md)。后续仍须完成超过三个核心与最新DES联合实机，不能由本场冷载或图片更新代授。
