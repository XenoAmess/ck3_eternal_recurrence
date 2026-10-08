# R0031：D2b 授予与结算动作首现继承污染

本轮加载源码固定在 `06159b964d859d30f2f07f4b183284df7d6dac47`，CK3 1.20.0.4，运行 `live-attempt-031`。以历史 R29 已签署 B3 存档作冷启动诊断种子；历史正式信用没有转移到本轮。本轮只执行 D0、D1、D2a、D2b 诊断，正式 I3b B3/B4/B5、新 T 冷重载、C3 与 I4 均 **NOT_RUN/NULL**，整模组 **NOT_GREEN**。

| 阶段 | 原生继承缓存 | 实际存档与保护观察 |
| --- | ---: | --- |
| D0 冷启动基线 | 45 | 新存档与历史签名 B3 六项严格条件匹配；原 87 项保护全真，原生 45 项与保存正文有序相等 |
| D1 教义切换 | 45 | 七个政治头衔及角色领地 AST 不变；原 87 项中教义投影一项如实为假 |
| D2a 创建未持有头衔 | 45 | 原生 `new_title=18373`，存档有唯一标记、Faith 107、四项属性，holder=NULL；七政治头衔和角色领地 AST 不变 |
| D2b 授予与结算 | **40** | 保存前原生已从 45→40，保存后仍为 40 且与存档有序相等；T18373 holder=31254，五个政治头衔的 heir 列表首变 |

D2a→D2b 的完整 AST 比较显示，原政治头衔 2230、2231、2235、2262、2264 仅 heir 列表被改写；2232、2263 未变。角色缓存恰好移除 38561、39045、39171、39352、39527，无新继承人。新 T18373 在 D2b 存档中取得 holder 并带 20 名继承人。角色领地中加入 T18373；原有七个政治头衔依然由 31254 持有。该证据把首次变化限定在 `create_title_and_vassal_change`、`change_title_holder`、`resolve_title_and_vassal_change` 组成的 D2b 原子段，不能再细分为其中单条指令。D2a 的 create 与属性动作已独立排除。本轮没有执行 D3–D6，不推断后续状态；R30 的 D5 law95 事后添加仍为 40 的事实见[上一轮报告](../2026-10-08-r0030-fa0f5e1ee-factory-staged-diagnostic-red/REPORT.md)。

全部四个真实存档各由独立作者只读解析一次，原生前后缓存、事件作用域、SAVE、G2/G3 均绑定同进程、同会话、当次 revision。完整原件与失败尝试均保存在外置 `C:/workspace/ck3_lyd_runtime_20261004`，可移交 JSON/日志收于 [原件 ZIP](raw-evidence.zip) 和 [逐文件索引](INDEX.json)。关键比较为 `D0-comparison` SHA-256 `748bcccf9bc60678ddfbe76b8d39e2ba7da49abf6481e1132392d320f9e16ed0`、`D1-D2a` SHA-256 `efc504a60fd7aad3012c506c0c60a6e76550495fd17c8761ce09e3dd8c95c47f`、`D2a-D2b` SHA-256 `1aac7c40973b16bdfe5116a266cc3154f238bd69af7024616495d174d2bc34ae`。所有原保护假项保留，未降级门禁。

ROOT 审阅了新鲜的启动前 Steam 离线截图。结束时游戏由原生 normal-exit 路径返回 PID 13472/exit 0；Client、keeper、原 HANDLE observer 均 exit 0，屏幕 CAS 4035 已释放。终局 Steam 窗口不可见，独立检查返回 `steam_windows=[]`，因此**没有终局离线画面回读信用**；本轮也没有将 Steam 切为在线。一次过早的 normal-exit observer 请求、一次 UIA 聚焦已退出进程，以及一次小写 CLI SHA 的 CAS 拒绝均保留原 RED 回执；随后观察退出与大写 SHA 的 CAS 完成。游戏退出证明只覆盖本轮诊断现场，不补正式业务信用。

下一轮候选需要在持有 T 前建立正确的宗教头衔继承规则，或以独立实验查明 D2b 三条原生指令中哪一条造成共同继承缓存变化；随后从新 clean HEAD 构建、冷启动，重复原 87/88 及终局保护。只有正式 I3b、成功新 T 冷重载和 C3/I4 各自实机通过后才可报告产品 GREEN。当前官方 CI 的 Official job 仍有独立 RED，不能由本轮局部测试代替。
