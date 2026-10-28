# R0033：默认配置完成与一次封臣邀请

观察机器为 `machine_id: 4-8e1c2f1861`。游戏于2026-10-27T15:45Z启动，16:41Z正常退出；文档于2026-10-28（Asia/Shanghai）补录。冻结来源为 `0926b351599b2814f7dbf99b4cd4c5705d3e5a69`。本场没有加载MTS或DES；整场业务仍为 **INCOMPLETE**，未发布0.2。

外置根 `C5=C:/workspace/rrf-development-20261024/review-fixes-a01/fresh-no-mts-review-a05`；`L=C5/live/4-8e1c2f1861--religious-ritual-fusion--R0033`；`B=C5/metadata/normal-close-a01/root-business-oracles-a01`。不复制大型原件进仓库。

## 已实际成立的子集

- 取消并重开后采用来源A默认三核心；最终实际选择ESO／ASTRO／COMM以及允许离婚。一次融合新建Rite153，玩家31254采用，Faith13／Religion8不变。仅新增一个Rite，没有新增Faith或Religion。
- 融合费精确为6000→5500虔诚。原生“保留默认配置”仅提交一次，两个独立保存均包含Rite153的 `rrf_native_configuration_complete=yes`，没有setup／open／apply／waiver活动状态；同一结果ID、核心、30项教义和完整Rite记录保持一致。
- 本场实际复现只读宗教查询的发布帧竞争：原请求被拒后，SDK等待新Condition发布，仅重新查询一次。原融合动作未重放；独立读回成功。这是[共享修复](native-frame-race-R0032-2026-10-27.md)的实机窄验证。
- 对预览中的34973和45458，点击实际产品“邀请预览中的封臣”按钮一次；新鲜原图、真实2560×1440坐标映射、前台HWND／PID和点击回执均保留。结果根的原生census返回截断，未伪造widget ID或重复邀请。
- 邀请阶段另扣100虔诚，5500→5400。保存中两人均进入invited及pending，但其实际Rite仍为150和0；长名封臣36445仍为150。**没有原生回复、改宗成功或五日推进信用。** 五位拒绝预览不是实际拒绝回复。

原生创建、默认配置和邀请分别仅提交一次；融合前、默认配置完成后、邀请后共保存三个checkpoint，每次请求各提交一次，没有重放。最后保存为 `68446460 B / 45f225aa8f60542c63696cb42fe259dd8ad4a04b75fbf328866fadaea02a9f5d`；原生SAVE回执的driver binding仍为unconfirmed，独立读取成功不追认该绑定。

## 独立存档证据与边界

| 原件 | bytes / SHA-256 | 实际范围 |
| --- | --- | --- |
| `B/baseline/FINAL.actual.json` | 7742 / `c8525fc0db179c4e836dfdc5d0334b86f7bd64dcf5e143d3cdbab3e7a27da0d5` | 取消后、融合前保存；两原Java进程0，持有句柄下身份及内容不变 |
| `B/post-recovery-c/combined/report.json` | 997848 / `a439c58c7edd876252ad81b85fc25d189ec863c4355e28e04031badf26b40d0c` | 完成默认配置、邀请前；玩家及三名封臣，完整来源／Faith／Religion与库存 |
| `B/final/combined/report.json` | 1000894 / `8e4fd9a82f87381e124da27ee3f0e4203baeb59a8dd41293f1ddd33ef17281e2` | 邀请后同日保存，同样四actor；decoder0且saveUnchanged |
| `B/final/FINAL.actual.json` | 7455 / `27982ae476f567f257d04e807a968ccb33a1a94d6384e5c962feef686e73f326` | 原Java wait已消费、reader已关闭；累计计费3985408 B，原4MiB帽不变 |

邀请前后Rite153完整记录SHA均为 `8cb5a2c01868e333b84345f86210d18f0658fbdf481350add7bdac1deb5a14ed`。三来源在这两份保存间不变；相对取消baseline，来源150唯一变化为head_of_rite从31254变为34232，不能写成全部来源FULL_RECORD始终不变。151／152、Faith13／103、Religion8完整记录自baseline不变。最终完整库存为living35582、Rite154、Faith104、Religion49。

最初post第二Java进程因单份报告超过1MiB失败；之后数值actor路径projection被既有合同拒绝。两份RED及原stderr均保留。最终使用原ACTOR表读取，仅选四actor以满足原硬帽；八名至亲和十五actor整体未验证，未知D/H/CoA布局不算空库通过。

## 界面、素材及闭场

本场保留四张未裁切实机PNG及sidecar：最终草案、结果诊断、被Faith窗遮挡的结果页、邀请点击后回执。结果页与三核心实际可见，但尚缺长名自然换行的合格镜头；诊断截图没有改标为业务PASS，也未上传为正式0.2素材。

[R0032的两张开发UI宣传图](../../../workshop/religious_ritual_fusion_screenshots.md)已经追加至同一Workshop条目3826756673，原八图保留，十图及完整说明均已匿名回读。公开下载仍为0.1.0-alpha，开发预览不代表0.2已发布。

原deadline守卫16:39:52Z保留未完成phase并触发正常关闭。`L/case-output/normal-close-result.json` 为9586 B／`70c16a98bb7d2b165118868b4152d47a21272eae180fc763548fa68d24364df0`，证明原生及保留OS句柄退出0、host0、cleanup线程结束。keeper及allocator原0，Root原会话94555终态chunk14639b退出2，public／verify2保留。SCREEN原CAS14283→14284释放，显示恢复1024×768；业务失败没有改成通过。

后继需独立冷载本次实际5400钱包及pending名单，再推进五个自然日，不重邀；旧cold fixture固定5500的创建后钱包断言与实际邀请费用冲突，须先修共享观察合同。长文、MTS超过三项、最新DES联合默认／可选宗族化及维护后态仍继续验收。
