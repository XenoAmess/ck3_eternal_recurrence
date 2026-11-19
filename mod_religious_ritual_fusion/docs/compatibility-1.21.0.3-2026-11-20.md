# CK3 1.21.0.3 Florin 离线适配候选

本次候选版本为 `0.2.2-alpha`，沿用 Workshop `3826756673`。本页记离线源码与软件资格，正式提交、真实 tag、实机业务和工坊发表由集成负责人分别记录。旧版已发表事实及原业务矩阵 GAP 保持原范围。

源码来自本机 `desktop-3fevhd2-1c74096080` 的 `C:/SteamLibrary/steamapps/common/Crusader Kings III/game`。本轮 Root 已确认 CK3 `1.21.0.3` / Steam build `26785313`，EXE SHA-256 `859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28`。此 EXE 身份不授予旧 Native DLL 或旧机实机资格。

## 实际迁移

- 通过原有 Java/Quarkus `generate --game ... --machine-id ...` 重新读取原版，catalog 从 157 个源码 pin / 223 条定义变为 166 / 239。新增 16 条教义；31 条原有定义的可选规则发生变化。完整来源 SHA 与规则保存在 `catalog/generated-catalog.json`，没有从旧 SHA 重建缺失文件。
- 新增饮食、饮酒、放贷和特殊教义组；加冕、葬礼分类移到 `precepts`。重新生成的 60 个文件带入原版互斥、DLC、actor rite 和 Sinitic 条件，继续沿用来源成员、双方贡献、核心数量和最终选择验证。隐藏 Yazidi 元数据仍排除于玩家内容。
- `gui/window_rite_creation.gui` 补入当前原版的戒律分类、礼仪编辑教义可选性与禁选提示、美德／罪恶 tooltip 接口、教义 tooltip 槽、原生随机命名与简介生成按钮、由 define 指定的简介长度，以及原版多行分歧／皈依预览布局。保留 RRF 同对象设置与核心锁定、apply/skip/defer、MTS 多核心滚动和既有融合／结果窗口修复。
- 本机保留的 build26622941 原版 GUI 与当前 build26785313 原版 GUI 完全同字节，SHA-256 都是 `301f01a92e84d3ffd68323f1895e362cf787a19385249af490638c4a687edb2e`。此次 GUI 差异来自产品仍保留的 1.20 底稿，不能解释成热修独有变化。旧 ZIP 仅为选定子集，未覆盖的旧原版教义文件不作逐文件 266 对照。
- 重新核实 acceptance fixture 的原版 `add_known_tenet` / `add_known_doctrine`、历史角色 `1128`、书签与 after-lobby 历史链接来源，更新本机 SHA/行号及版本范围。历史角色 ID 与实机每场 runtime ID 仍严格区分。
- 运行 allowlist 从 36 个手工文件 + 54 个生成文件（90）变为 36 + 60（96）。canonical producer/consumer 测试按真实 allowlist 验证完整库存，不继续把旧版的 90 文件写死。九语文件没有改变，现有术语、受保护 token 与键集继续完整校验。

## 验证边界

在独立 D 盘开发目录复用同一增量输出，最小 Maven reactor 只选择 `ck3-save-core` 与 `religious-ritual-fusion-tools`，使用命令行默认 Maven、`-T2`、Java 21 release 与 `-Xlint:all -Werror`。借用的现有 D 盘 Maven cache 在此工作包期间为唯一 writer；C 盘原缓存仅作只读 file repository。

实际生产器首次重采与内容校验通过，报告 96 runtime files / 239 definitions / 22 blocked definitions。完整测试、真实 CLI consumer 与双构建的最终数目、退出码、SHA 和原失败由交付记录列出。正式 builder 继续要求真实 tag 指向 source HEAD；离线合成身份的测试产物不能充当正式发布包。

本离线岗位没有启动 Game、连接 Native live、操作 Steam、取得新截图或工坊发表。旧 0.2.1 的已发表、缓存、主菜单和业务证据不外推到此新 EXE。后继实机须由现场 owner 在当前机器、版本、独立 profile 下按现有发布合同执行，并保持最小化静默。
