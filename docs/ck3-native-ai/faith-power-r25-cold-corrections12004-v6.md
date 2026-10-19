# R25 展示冷修与个人窗口正常关闭

machine_id: `4-8e1c2f1861`；来源 EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，CK3 1.20.0.4。来源提交 `8e1205135b6d7d675e6dbe76e4e9be47960db6f2`。本页是源码与 R25 历史诊断，不授后继编译或实机通过。

2026-10-18T23:49:36Z 的 `live/4-8e1c2f1861--faith-and-power--R0025/r25-preparation-guard-probe-a02.json`（SHA `13544ee75eb8aac7eeb5f9ea54701d0148b0d92a80af75faf124be8c163d4d64`）整体为 `bounded_read_failed`：112 次读取、2040 B，个人按钮 count=0 后安全停止，未取得完整的前后稳定性复读。局部原字节可证明：TypeDescriptor RVA5769298 的首 qword 是实际 image_base+44210A0，后24B相同；应按加载后的重定位比较首指针，保留后缀逐字校验。四处 strategy E8 均仍为原版。

实际 frozen-argv 有 `--saved-campaign-inject-after-load`，实际 saved_campaign_launch 记录 `after_saved_campaign_setup_completion`。路径为 shared-host.py651→runtime.py3138→`--pipe` injector→`InjectLibraryAndStart`→`XarCk3BridgeStartWithPipe`，未调用 `PrepareStartup`。不能在热 attach 谎称主线程尚未恢复。后继使用已有预 resume 冷注入，保留 saved-only/F；不修改安装算法。下一场须真实验证 hook 与 tooltip，而不是从 fixture 授信。

原坐标消费者 `3A75EA0..3A75FB4` 完整276B SHA `7a5c5c374af2aded4bc88ee6ae9a6e0ac7223780e047590662886ed16e1a7883`，原字节保存在外置 `native-tooltip-live-red-a01/finite-3a75ea0.json`。3A75ED4 读源+110；3A75F10..4D 的祖链仅读+110/E8；有 parent 时3A75F65才读**源本身**+114，无 parent 时3A75F77只读源+110。故不要求未消费的 ancestor/root+114 为正数；仍验证每个+110、源有 parent 时+114、同 context、有限无环链及重读稳定。R25 采样时 Faith 已隐藏且链中值均为正，不能把此静态过约束称为23:28的实际首因。

## 有限个人关闭接口

现有 `ck3_present_faith_power_ui_v1(operation="close_presentation_window",window_kind="personal_beliefs",subject_id=<当前玩家>,expected_revision=<新帧>)`，有限 op208；不接受 target/index/tab/receipt（显式空或0也拒绝）。复用已有工具、step、optin、原 owner mailbox；默认 OFF。Driver 已限制 personal subject 为实际玩家；原生重读当前 owner/handler/actor/typed窗口、可见性、精确方法与虚槽，主线程/TLS/暂停帧及 modal 门仍有效，一次调用原类 normal Close/Hide。

MCP Literal→有限 request_fields→Service→Driver `_ingame_ui_v1`→原 navigate step/中央准入→GuiRequestContext/已登记 owner executor→同 adapter op208；正常序列化与原两种 query 不变。没有新 tool、flag、原生任意点击入口或 managed readonly allowlist 增权。后继受管拍摄 policy 可仅新增本 UI op，不改变 A-only 世界写保护。

ACK 保留调用前 source metadata，`post_window_visible=null`、pending=true。随后以现 `ck3_query_faith_power_ui_v1` 同 subject 独立读取 `effective_visible=false`；原 window/handler 槽仍存在也是合法关闭结果。异常或后帧失配保留 attempted/unknown，不能重复提交。

调用的是原 class normal-close，不声称已证明 GUI 反射 Close 注册边；保留原关联 view 关闭及 GUI hide 回调行为，不自造 bitset=0 门，也不把其传递闭包称为纯函数。以下完整体都从保留 exact4 cache `native-candidate/shared-source/text.bin` 以 RVA-1000 有界读取，无新 EXE 扫描：

| 入口 | 字节 | SHA-256 | 原职责 |
|---|---:|---|---|
| `17E1130` | 28 | `dc4b91e6b1f1dcae19ed51b81c0b5ef3292d72b891d43771f88424d907a19702` | 个人 primaryVT4592C08+88 normal Close |
| `110B0E0` | 116 | `ecc415f36df2b1276a89702c96e3d596878a8ddae72fdb8e37695c280820780b` | VT+20 normal hide，最终关联 view 关闭 |
| `2160380` | 144 | `4af93fa4073aec88c4d4b87950c4d6b90b7fc677ba38ed224b9e3a555f505aa4` | VT+38 当前原生 open 状态 |
| `AED360` | 6 | `c5264b41ff2cd91ca34fc5b460d7a9373bf0f98ec1b6f41fec25d8e1abff46b4` | VT+50 返回0x80，不取0x800分支 |
| `110B2D0` | 339 | `0b519eeefebb4ad9533d1bceae1e1ad168564dcb3ab855f30de10a81b0abaed5` | 关联 view bitset→各原 normalClose |
| `3A76580` | 520 | `23f56580937c7abbe1ea43adf58dd421635fb7502fe8c1ab62fe661b5bc4da03` | 原GUI隐藏请求/动画状态 |
| `3A76790` | 480 | `edb63e98dd3d9ce454b30d0dcefffc6b068b5932b377c3705a1ad9f886ca1007` | GUI隐藏事件与原回调/子树传播 |

个人主 VT 的 +20/+38/+50/+88 均须匹配上述入口；保留 secondary/RTTI、window+98/A0/+E8、当前 handler+5E0 等既有绑定。现原 GUI header button 声明 `PersonalBeliefsWindow.Close`，但 R25 的 one-button probe 未闭合其 compiled descriptor，不能当作该反射边的实测。

静态/合约测试与真实运行分开：新增既有 navigation fixture 的 parser、源码/虚槽拒绝 case 不调用 CK3；Python 两个聚焦测试走真实生产合同与 MCP/Service/Driver，transport/snapshot 为 synthetic。后继 DLL 编译、原窗口实际隐藏与目标 tooltip/建筑条件像素仍须实机读取。

长于392B的方法体按连续片段逐字节校验：520B为392+128，480B为392+88；不削减完整体或放宽原reader上限。原两候选共享的fixture插入点在合入时保留两组用例；各自apply检查不替代合成后的编译执行。
