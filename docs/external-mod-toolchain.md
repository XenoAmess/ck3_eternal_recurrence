# 独立 CK3 mod 迁移、验收与发布工具链

2026-10-03，从 More Tenets Slots(XA) 迁移到 CK3 1.20.0.3 和 v10 发布提炼。此页连接框架已有能力，供其他 mod 复用；产品定义、译文、素材、存档和具体验收收据仍在独立项目。来源为 [产品迁移报告](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/b10d50faac3c8462354cfa235ea62d72265ee54d/docs/migration-report.md) 和 [正式发布报告](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/b10d50faac3c8462354cfa235ea62d72265ee54d/docs/workshop/publication-v10.md)。

## 可复用的现有入口

| 工作 | 现有工具 / 合同 | 本次沉淀与边界 |
| --- | --- | --- |
| 迁移完整原版覆盖文件 | [ck3_text_projection.py](../tools/ck3_text_projection.py) 的 `blocks`、`named_block`、`project`、`recover`；[可逆投影指南](external-mod-source-projections.md) | 本次新增的通用结构扫描和 SHA 绑定投影已提交为 `36a225237`；原版 SHA、唯一锚点和反向恢复帮助发现额外修改，但不证明引擎语法或业务合法性。 |
| 审查实际生效值与 GUI 槽位 | [可逆投影与实机反例](external-mod-source-projections.md)；[桌面坐标映射](desktop-coordinate-mapping.md) | 同名数据库定义的合并、define 与 script value 的镜像、列表生产者与弹窗消费者索引分别核对。数量、滚动可达、末端选择、费用、创建、保存和冷载分别取证。 |
| 核验保存后的实体身份 | [结构扫描工具](../tools/ck3_text_projection.py)；[保存层核对方法](external-mod-source-projections.md#创建结果与保存层的权威身份) | 在明确容器内定位角色引用及实体数据库头，避免标签后缀、首次正则命中或新建草稿冒充实际保存状态。结构扫描不是完整存档解析器。 |
| 语言发现、翻译候选与格式认证 | [本地化流程](localization-workflow.md)；[translate_localization_minimax.py](../tools/translate_localization_minimax.py) | 复用 `parse_ck3_localization`、`assert_protected_tokens` 与现有候选调用器。由当次 launcher 语言选项确定支持集合；产品层配置键集、显式空键及所需实机语言。 |
| 正式构建 | [build_release.py](../tools/build_release.py) 的 `create_manifest`、`manifest_bytes`、`write_deterministic_zip` | 独立产品适配器提供源码、版本、冻结 commit 和显式文件清单，复用清单与确定性 ZIP 原语。不能直接沿用该脚本主产品的默认源码或 allowlist。 |
| 更新工坊内容与附加截图 | [Workshop MCP](../ck3_workshop_mcp/README.md)；[native 附加图片合同](workshop-native-additional-previews.md) | 本次新增 `workshop_native_previews` 和 native 发布计划中的替换、追加、删除字段，提交 `26c9943e1`。主 thumbnail、附加 strip 和 BBCode 图片是三个独立通道。查询、替换和追加在本产品首轮实机通过；删除等路径仍仅静态验证。 |
| 全新工坊下载 | [native 下载合同](workshop-native-download.md)；[steam_download.py](../ck3_workshop_mcp/src/ck3_workshop_mcp/steam_download.py) | 本次新增 `workshop_native_download`，提交 `fcc29d14d`。独立进程等待准确 AppID/item 的 callback 3406，再核验安装路径和 flags；本次成功路径实机通过。MCP 不移动旧缓存、不订阅、不切换 Steam 模式。 |
| 公开描述、完整 Change Notes 与内容校验 | [verify_workshop_publication.py](../tools/verify_workshop_publication.py)；[validation.py](../ck3_workshop_mcp/src/ck3_workshop_mcp/validation.py) 的 `_validate_manifest_tree` | 复用已有全文回读器及严格文件清单校验器。公开正文与独立 Notes entry 分别核对归一化全文、字符/行数及 SHA；下载目录再逐文件核对路径、大小、SHA。 |
| 发布后恢复离线 | [现有离线恢复指南](ck3-native-ai/desktop-steam-offline-recovery-2026-09-27.md) | 本次补录正常退出客户端、核对并取消本机孤儿 crash reporter、重开与官方菜单切换的实际组合路径。新鲜画面须明确离线；这仍是操作经验，不是已实现的离线控制 MCP。 |

## 本次可以复用的判断方法

迁移应先查数据库目录、对象 scope、原生 GUI 控件和同名定义的实际提供方。旧文件仍存在或 descriptor 版本匹配不能证明兼容。保留已有原生合法性与费用路径，优先使用已存在的空槽语义；显示词 `Absent`、`None` 等先追查本地化 key 和实际对象定义，避免把真实规则拒绝误认成缺失对象后旁路按钮。具体反例及撤回的归因见 [投影指南](external-mod-source-projections.md)。

扩容测试以末端操作和保存结果闭合。连续少量条目、尾部空槽、跨页末端与中间空槽是不同路径。本产品 R0012 用末端第 100 槽和中间 96 个空槽真实创建，R0013 再独立冷载和原生保存；方法可复用，四个具体信条、隐藏选择器教条和准备效果属于产品实现，不上收为其他 mod 的默认方案。

实机语言与格式认证范围分开记录。本产品按用户要求后续只用简体中文实机，其他语言仅格式认证；这一产品约束不自动修改框架其他产品的验收矩阵。隐藏条目仍可能解析名称与描述元数据，空字符串应作为显式合同保留，不能把它当成翻译遗漏统一填入可见文字。

发布成功分别取得原生回执、匿名完整文案回读、三类媒体回读和新下载内容证据。`SubmitItemUpdate` 成功、`DownloadItem` 启动 ACK、旧订阅缓存和 CDN HTTP 200 各自只覆盖部分事实。本次图片还核对实际顺序、文件名、文件字节与解码像素；正文外链使用固定提交 raw URL。遭遇公开 changelog 429 后按当次记录退避再读相同 canonical 页面，不重提上传，也不把失败回读改标通过；现有工具没有因本例新增自动重试。

产品发布 tag 可以指向冻结上传源，报告提交随后记录正式发布事实。构建 manifest 当时的 `git_tag=null` 应保留原样，不能事后改变已上传清单的身份。上一公开版本以实际公开元数据与已冻结内容为依据；本地开发 descriptor 的版本不能替代公开基线。

## 复用与继续施工的范围

以上现有实现由参数或操作者配置提供游戏、Python、源码、AppID/item 和运行目录。产品适配器保留自身的 GUI 锚点、scope、allowlist、键集、版本和验收样本，不复制一份通用 parser、翻译器或发布器。

本次代码能力已经落入框架；此轮补齐稀疏槽位、保存身份、本地化发现方法与入口索引，属于文档整理，没有改动工具执行路径。保留已有定向回归和首轮实机证据，不为索引重复运行游戏、上传或下载。独立下载和图片更新的成功结果不升级未实测的删除、超时或其他 mod 路径；Steam 离线自动控制仍未实现。
