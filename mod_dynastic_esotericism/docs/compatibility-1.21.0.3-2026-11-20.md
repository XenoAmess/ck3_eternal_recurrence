# CK3 1.21.0.3 Florin 适配候选

候选版本 `0.2.2`，沿用 Workshop `3826991345`。已公开版本仍为 `0.2.1`；2026-11-02 的实际上传、全文回读与恢复离线事实见原[发布记录](acceptance/publication-0.2.1-2026-11-02.json)。旧 0.1 初测、0.2.1 预置信仰可见与宗族化、创建／改革者拿回族长，以及所有失败、未完成业务矩阵，均保持原版本和原场次范围。

本次原版来源为 `desktop-3fevhd2-1c74096080` 的 `C:/SteamLibrary/steamapps/common/Crusader Kings III/game`。Root 已确认 CK3 `1.21.0.3` / Steam build `26785313`，EXE SHA-256 `859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28`。源码比对、Java 检查不授予旧 DLL 或旧实机新资格。

## 实际修改

- 按当前原版重新合并 `gui/window_faith.gui`。除原有的一条 `And( DoctrineType.IsVisible, ... )` 和 BOM／LF 格式外，其余内容严格使用当前原版；保留详情隐藏“无”、编辑器仍可选择“无／宗族化”的原合同。新版圣地窗口入口、信仰交互控件、信条名、tooltip、圣人／圣物页及原版布局变化随本次基线更新进入候选。GUI 引擎类型与实际画面仍需当前实机检查。
- 世俗信仰领袖 trigger 同步当前原版：删除原版已经移除的 `exists = situation:the_christian_church`，保留其他原版条件和两项帝国级预置领袖专属的直属领主等级限制；更新 Java 的精确 token 合同。领袖 title／CoA effect 的两项预置分支不变，其余 token 与当前原版一致，没有新增政体转换。
- 两项预置礼仪显式补入 Florin 饮食与饮酒槽的中立值 `doctrine_diet_unrestricted`、`doctrine_alcohol_permitted`，与当前原版 Roman Rite 一致。其余原来指定的 25 项普通教义与核心信条不变；Java 精确预置合同相应为 27 项。新的放贷教义继续继承当前 Christianity 默认 `doctrine_usury_forbidden`，没有另设产品政策。
- 复制的家庭皈依事件去除既有两处 DES 同步 hook 与 override priority 后，全部 token 与当前原版一致；事件局部合法人物 helper 也完全一致，监护与向下级联保护保持。更新其来源版本说明。
- 重新核对当前原版 creator／edited Rite／updated Rite／UI-only consume token 的源码注释合同。867.1.1 的两项 `created = yes` 历史、初始化保护、None 可选性、成员与犯罪索引、真实创建／改革者一次性族长交回、已有 Dynasty／House 身份与 CoA 保全、专用预置纹章及自创礼仪随机回退没有改动。

原版 build26622941 的选定 ZIP 中，`window_faith.gui` 与当前 build26785313 完全同字节。本次主要 GUI 迁移来自产品仍使用的旧底稿；旧 ZIP 是选定子集，未覆盖源不伪称完整旧安装对照。

## 离线资格与边界

容量受限阶段使用一个稀疏 D 盘开发目录，复制必要的 57 个 runtime 源、12 个 Java 生产源、实际 fixture 资源、测试与共享 save leaf；4.42 MB 的原图导入来源未复制。SDK／通用 tools 仅通过只读目录联接作为真实现有测试输入，不进入产品包。

4 MiB 初始额度内已取得实际 `javac --release 21 -Xlint:all -Werror` 退出 0，并通过原 `ReleaseCommand` 的九语完整静态校验：`0.2.2` / 57 文件 / 1,955,641 源字节。它没有启动 Quarkus 服务、Game 或 Steam；它不是 Maven 完整测试、Quarkus 打包、正式双构建或实机业务资格。后继完整命令及原退出码由交付记录给出，不以“静态通过”替代。

本岗位没有 primary 写入、正式 Git／tag、Game、Native live、Steam 或工坊发表。正式集成与当前版本实机、同条目更新由主任务接续；不将原矩阵未覆盖项任意增加为新发布硬门，也不将历史公开测试当作新 EXE 已验收。
