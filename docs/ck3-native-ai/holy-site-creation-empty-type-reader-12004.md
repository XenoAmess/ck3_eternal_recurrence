# 新建圣地：空类型选择不等于没有候选

2026-10-17 UTC 补录；machine_id: `4-8e1c2f1861`。来源绑定 CK3 1.20.0.4，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。[证据索引](evidence/holy-site-creation-empty-type12004/observation.json)保存实际时间、路径、SHA、源码行号及主张状态。修复后实机枚举、选择和新建仍待验收。

R0007 于 15:51:35.617169–15:51:36.042493 UTC 调用原生打开，返回派发 pending。随后两个独立读取均报 `holy_site_creation_selected_type_unavailable`；context 读到 window Faith 50，但候选模型没有成功暴露。不能把 unavailable 的 null 模型解释成“没有可选类型”，也不能把未合格结果中的默认 `window_exists=false` 当作实际窗口消失。

15:52:07 UTC 的原始 2560×1440 画面经人工直接审阅：原版新建窗口可见，十个类型按钮未见选中，三空槽和拥有的圣物列表可见，底部红色 2000 虔诚报价，钱包显示 1750。这些像素不能提供原生类型键、D0 指针、最终 CanCreate 或命令收费；2000 仍是 UI 报价，不能直接记为最终支出。

## 来源和修复

原版构造器、reset、SetData 把 `*(image+0x5D21700)` 写入窗口 D0，候选生产器独立填充模型；原版 GUI 有明确的无效／未选类型分支。证据索引钉选 `window-factory.asm` 42–44、`vslot17e9220.asm` 6–7、`setdata_17e92f0.asm` 24–29、`dynamic-type-producer-complete.asm` 6–7/58–60，以及 `window_holy_site_creation.gui` 164/448/679。R7 的失败与原版默认对象一致，但旧回执没有暴露实际 D0/default 相等性，因此原因仍是来源支持的推断。

最小修复只改 `holy_site_creation12004.cpp`：正常非空 TypeKey 路径保持；只有 TypeKey 失败或为空时才读精确默认对象，要求选中指针等于它，并再次验证默认对象稳定。正常空选中态返回 `selected_type_key=null`，保留候选；其他损坏、不可读、非默认或变动指针继续拒绝。候选校验、费用和原版 CanCreate 未放宽，没有更换 opener 或猜类型键。

空类型时 Create preview 仍为 null。Python 原合同已允许空选中类型，无需改 schema 或填入虚构类型。补丁只有一个生产 CPP，没有新宏、头文件、CMake 或编译单元定义。

## 游玩规划合同

| 实际观察 | 规划器动作 | 仍未知 |
|---|---|---|
| context unavailable／models 不完整 | 诊断读口，保留 unknown | 候选、许可、最终费用 |
| context available、models complete、type null | 从本次原生候选规划 typed 选择 | 完整参数与最终许可 |
| 选择返回 ACK／pending | 独立读取选中后态；未知不重复派发 | 是否生效、原窗口是否有效 |
| preview null | 不提交 Create | 缺失参数及最终许可 |
| fresh preview、原生 CanCreate=true、bypass=0 | 才进入既有 once 守卫，随后独立后验 | 新 Site、归属与资源净变化 |

```mermaid
flowchart LR
 A[R7 打开 pending] --> B[独立读口拒绝空类型]
 B -. D0 未实读 .-> C[原版默认对象解释]
 C --> D[精确稳定默认对象允许空选择]
 D --> E[离线生产代码与 MCP 查询通过]
 E -. 待新冷载 .-> F[真实候选及 typed 选择后验]
 F -. 完整参数和最终许可 .-> G[Create once 与独立新 Site 后读]
```

新增离线 17 项针对性检查通过；一份未经改写的生产 serializer 包经实际 Driver→Service→MCP 查询通过，完整候选保留，type 与 preview 均为 null。该查询绑定 actual clean `ea7e78e56c5b871d2f025e5df21323a79ac84d6d` 的 Python 来源，没有 Open、Select、Create 或进程访问，不计实机结果，不重复旧矩阵。

修复补丁 SHA-256 `315e371c96e379797bb50e875c57733910c082cbf38b35b3db3512421a3740df`；core SHA-256 `c5db595e80703e4f46ac71a02a11dd7120c6d97fbfc944bf66d232b9c7a4c48c`。完整条件见[新建 once 合同](holy-site-creation-create-once12004.md)。
