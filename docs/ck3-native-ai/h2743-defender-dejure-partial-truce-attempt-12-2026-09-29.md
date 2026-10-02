# H2743 de-jure 守方退出：v4 部分休战输入只读 attempt-12

2026-09-29 本机受管只读重放 **GREEN**。不可变证据位于 `D:/ck3-research-artifacts/war31-h2743-20260928/attempt-12-dejure-baseline-no-launch/live-dejure-partial-truce-v4/`；退出后 `read-only-result.json` SHA-256 `9414C6D397553F1C00D974DB179EF8C96630C2CAB4C75020E1CDED4FAB37DC9E`。这次使用新候选 DLL `1361FC0991D1FA09CB7272112D73F7F50736B7BBAD6A3656C33F9FB200CA1BAA`，与 [旧 attempt-11](h2743-defender-dejure-readonly-attempt-11-2026-09-28.md) 的 title-prestate DLL 分属两个独立 attempt；没有修改旧资产或回执。

## 准入与清场

- `ready-summary.json` SHA-256 `F07B0EEF8E1412794D345ED1E5E1CE51B2BACC40483BE70C4350C41A47E5E25A`：精确四源 save `A5012030…5106E9`、driver `F31460BA…15069`、family sidecar `12D7B2B0…4B5724`、源 DLL `8C3A9523…7A8A5C`，候选 DLL `1361FC09…CA1BAA`、injector `C89F1A91…A84FF` 与 CK3 EXE `2D00FF31…3DB86` 均按完整 SHA 通过；prepare、rebind、native preflight 返回 0，且 no-launch 未启动游戏。
- 本次 Steam 窗口位移原图 `steam-frame-v4-attempt12-001/steam-moved.png` SHA-256 `0E9FAFC5863B44D4DFC044F8AA33EA67F9EE95BBDA74973B3E76057EF667AAAD`；位移像素变化回执 SHA-256 `03799B51CE03202F6249632C74A1EDBFC7DB86A98FE6F599F29F0DAC2C654F9C`。直接审阅该原图可见 Steam 左下“离线模式”，`steam-gate.json` SHA-256 `281B83E5545B5A2826A419C9BA183C22F4DC47A64CB6C2C52CDFD5D3EF979B5D`。
- 任务总线独占 `ck3-screen` 从 seq1944 到 **RELEASE seq1959**（2026-09-28T17:31:55Z）。`lease-heartbeats.jsonl` SHA-256 `EB19FF97EAFCF4A633B8B71EDE49EBE1C194975E006702ABFB8DA3B65D20F2D7`，续租均成功。`binary-audit-live.json` SHA-256 `820CD1F92E47C832F229AE5183F35A879F7182318A93C5423C6CDFB07EF7A87E` 绑定运行中 CK3 EXE 和已加载候选 DLL 的**路径及当前磁盘字节**；不声称内存映像 bytes 已校验。
- `session-exit.json` SHA-256 `5E118BAEC292D2FFFB3D1031DB4FCCAFCF1878668B41B29931A171B3AD1A23EC`：supervisor 返回 0、stdout reader 已停、CK3 PID 空，四源/候选 DLL/injector/EXE/已放置 save 与 sidecar 后哈希匹配。独立进程表复查 CK3、FFmpeg、OBS 均为零，之后才释放屏幕。

## 同帧原生读数

前后快照与两次基线的同帧身份一致：`native:3`、public/native revision `4/3`、raw date `53217264`、connection generation `1`、episode `native-29829-2bc2d599f7f9`；WarID `16777231`，Robert `29829` 是主守方，Landolf `30097` 为主攻方，CB index `17` `individual_county_de_jure_cb`，目标 Title `2128`。两次原始 baseline payload SHA-256 分别为 `EAB40AC965BC36E2BA119ED2944AC5A211FECA3D0E34959FADB27DFE1D4B19CF`、`2ED3D4320A01E619CBFFF1165B0E4E54CFF2FB6B384B8F2A9F4DBA2B2A73BB9D`；原始字节分别保全，runner 比较了两次 payload 的条款子结构。Title2128 当前 holder `33435`、其 immediate personal liege `29829` 以及双方 14 行资源余额与两行月度金币收入仍只属于**行动前态**。

新 `truce_inputs_v1` 两次均给出相同的部分值：

| 原版条件所需输入 | 同帧读口结果 |
| --- | --- |
| Landolf owned-perk span 含 `flexible_truces_perk` | `observed=false` |
| Landolf `government_is_nomadic` | `observed=false` |
| Robert `government_is_nomadic` | `observed=false` |
| 两方均游牧 `nomad_both` | `observed=false`（前两项政府读数的合取） |
| `short`、`long`、`border_raid_pair` | 各 `unavailable / stock_condition_reader_unavailable` |

FLEX 是经非玩家攻方 owned-perk span 读取的**键命中**，仍不能单凭列表命中或不命中宣称已完整验证原版 `has_perk` 谓词语义。剩余三个条件尚无同帧只读读口，因此 `evaluated_days=null`、`persisted_expiry_date_raw=null`、`directed_truce=null`；不能用基础天数或零值补齐实际有向休战期限。

同会话终战选项的原始 request/envelope/payload SHA-256 分别为 `FD2C5068A33C0D4673145A8533F2F4FFF834E5485B25030AF192A6535AD498D8`、`A15347875644C005FB5975FA5F09AD2464E457EBA52CF5FC2BBFD30F58FF0D2D`、`D7C6A50F5120944B4C53C42B52D0C64734BE9B169235F1C5764B3AABEA0DD2EB`；它们与早期同帧直接查询一致：投降当前合法、对方会接受，但 `terms_observable=false / cb_specific_terms_not_observable`。该**直接查询**没有 formal planner 的 `selected_step` 和 typed `priced_command`，不能供 R0266 单独填写即时费用 0。

本次只执行两次基线与一次终战选项的只读查询，没有投降、白和平、日期推进或其他游戏动作。`material_complete=false`、`title_vassal_delta=null`、`signed_resource_delta=null`、`recommended_outcome=null`、`action_literal=null`。运行时目标 scope、`cb_prestige_factor`、完整领地/封臣及资源后果、实际休战期限和给定时域续战损失上界仍缺；[比较合同](h2743-formal-exit-comparison-contract-2026-09-28.md)继续 fail closed，当前 checkpoint 不获终战动作授权。

固定 OneDrive `WAR/H2743-EXIT-READONLY-V3-20260928/` 已追加本机 `LOCAL-RESPONSE-PARTIAL-TRUCE-V4-ATTEMPT12-v1.json`，SHA-256 `271D3EBDA6BAF1F3B75720C3A6E2AE73A01AFE97D88DB810EDA391566171EDB4`；独立只读 intake 保全于 `D:/ck3-research-artifacts/war-intake-20260928/h2743-partial-truce-attempt12-001/receipt.json`。该文件是本机 receiver 的部分读数回件；来源机是否收到及其后续 ACK 尚未证实，且它不满足完整终战条款请求。
