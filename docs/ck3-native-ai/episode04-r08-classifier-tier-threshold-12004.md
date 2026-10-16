# R08：classifier own-tier 阈值分支（1.20.0.4）

本专题只补 d05 已入库 `2C6A810` 的一个 helper：`28AC690`。在祖先 holder 已匹配且 returned object `G+4D6==5` 的分支，原 P20 的 own-tier 与 signed DWORD `G+4CC` 比较；小于返回 raw2，否则 raw1。`G+4CC` 可称“此分支使用的 tier 比较阈值”，其正式定义名、G 的业务类型及 byte5 的业务含义仍未知。

这是精确 build 的静态来源整合；没有新增实机观察或 R08 整卡分子。paid military amount、币种与 cadence 均为 unknown/null，maintenance attribution 仍 unclosed；不把 raw4、context4A0 或此 tier 比较命名为已经支付的军费。

## 来源与同源连接

原始来源机器为 `desktop-3fevhd2-1c74096080`，新140B采集/合同时间为 `2026-10-16T16:26:35.767858+00:00`。整合机器相同，整合实际UTC见[便携记录](evidence/episode04-r08-rate-application-12004/classifier-tier-a06.json)的 `integration_observed_at_utc`；观察仓库提交为 `d05b0c780b615faa714fdf0535403bb2e6941faf`。来源为 CK3 **1.20.0.4 / Steam build25734779**，EXE SHA-256：

`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`

既有任命/家族 typed reader 已解释该 RVA；历史 raw 路由在来源机器当前不可读，因此原作者经 Root 授权只补 exact140B、metadata0、read1。没有将缺失历史原件写成仍可读取，也没有重哈希 EXE。新来源 ZIP 保留140B原件、全部41条指令、原 capture，以及693B classifier caller、其 SOURCE 和原 DWORD 宽度勘误。五份 typed/doc 来源保留原 Git blob bytes、SHA-256 和 Git object ID；原 ZIP 与全部 PORTABLE-INDEX 输入逐字节嵌入新 JSON，CRLF 不经转换。

与[d05 local88 来源](evidence/episode04-r08-rate-application-12004/local88-components-a05.json)逐字节比较：新包的 caller693B、caller SOURCE 和宽度勘误均与原 canonical 原件相同。`2C6AA65 E8 26 1C C4 FF` 的真实目标为 `28AC690`；`2C6AA6A CMP EAX,DWORD[RBX+4CC]` 接 signed `JL`，小于跳到 `2C6AAB7 MOV EAX,2`，其余到 `2C6AA72 MOV EAX,1`。原来“6个 helper 尚未展开”的历史 SOURCE 不改；本次只追加这个 helper 的来源。

| 连接 | 可证结论 |
|---|---|
| ancestor holder match → G+4D6==5 | 才进入此 tier 比较；不覆盖其他 classifier 分支 |
| `2C6AA65 → 28AC690(P20)` | 返回 own-tier raw32，下一指令按 signed32 比较 |
| own-tier < signed G+4CC | classifier raw2；否则 raw1 |
| 原 `24C7BB0` 消费 raw1/raw2 | raw1 跳过缩放，raw2 选择替代 raw factor；当前 factor 值未知 |

## 140B 内的选择与回退

`[28AC690,28AC71C)` 覆盖41条指令、11个内部短跳转和3个 RET，无 CALL、无直接内存写。先读 Character+1C0：非空时读取 signed cachedTier(+1D4)，**只要不等于 sentinel7 就直接返回原值**。等于7才按 DWORD count(+1EC) 选择列表(+1E0)首个完整 Title ID；count 为0选择 FFFFFFFF。1C0 空时改读1D0，以+74 count、+68列表选择首ID；两个对象都空直接返回0。它没有排序或扫描所有 Title，也没有写回 cache。

Title 解析使用 registry5D1DAF8：low24 index、capacity、16B entry 和 Title+10 完整 generation ID 相等检查；失败/无 registry 时使用5D1DAE0 fallback Title。最后读 Title+48 template 的 signed32 +64。缓存 producer、失效与刷新周期、sentinel7 的生产时机均未证明；不能强制绕过 cache 总是读首 Title。

## 原生返回与我方可用性守卫

原生 `cachedTier!=7` 没有0..6范围夹值；任意其他 signed32 raw都可直接返回。现有 `CaptureCandidateTier` 的 `0<=tier<=6` 是我方 availability guard，unread/stale ID 返回 unavailable。原生选择 fallback Title 与我方拒绝读取的行为也不始终相等。将 guarded reader 的拒绝称为原生返回0、原生 clamp 或不存在该分支均不成立。叶本体没有独立验证 P20 的 Character magic，输入资格依赖上游。

智能体如需实际选择，仍须同一准入暂停帧中的 P20/fullID、所选 cache/Title 路径、G 对象身份、G4D6、signed G4CC 与独立分类后验；未读到保持 unknown。本包没有新增 runtime getter、sampler 或动作。其他机器可复用来源及代码，来源机器的安装/运行事实不能外推。

## 离线复核与原件提取

在新 clone 的仓库根运行（任意标准 Python；不需 CK3、capstone、Git executable、源机器盘符或网络）：

```text
python -B -O docs/ck3-native-ai/evidence/episode04-r08-rate-application-12004/verify_r08_classifier_tier.py
```

校验器验证原件/ZIP成员 SHA、140B指令边界和所有短跳转、RET、call-free形状、同源693B caller及其真实 CALL/条件/结果字节、5个原 typed Git blob ID；它不以这些检查替代人工语义审阅或实机资格。可加 `--extract-originals <不存在的新目录>` 提取原作者 exact ZIP 与小记录；其中绝对路径仅为历史 provenance，不会据其读取文件。原 SOURCE/PLAN/check/render/原验证器与旧容量时限原样保留，当前整合不延长旧准入。

关联：[local88组件](episode04-r08-local88-components-12004.md)、[contract贡献链](episode04-r08-contract-contributions-12004.md)。本次为静态条件知识，未改变 paid/cadence、业务整卡状态或任何已录场次的来源绑定。
