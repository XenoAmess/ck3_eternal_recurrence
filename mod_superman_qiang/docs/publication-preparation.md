# 《超人强》1.0.0 发布准备

状态：准备阶段，未发布。中文名《超人强》；工坊标题《超人强：越超人越强》。用户已授权开发、测试验收及发布；正式动作仍须等本产品实机与候选门完成，不能把本页当作上传成功事实。

## 文案与输入

- 主描述：[superman_qiang_description.bbcode](../../workshop/superman_qiang_description.bbcode)。
- 独立的完整Steam Change Notes草稿：[superman_qiang_change_notes.txt](../../workshop/superman_qiang_change_notes.txt)。
- 首发真实玩法图清单：[superman_qiang_screenshots.md](../../workshop/superman_qiang_screenshots.md)，目前待GREEN截图。
- 正式候选本地冻结工具：[prepare_publication.py](../tools/prepare_publication.py)。它调用已有严格manifest校验和native plan本地校验，绑定tag、commit、正式manifest的精确库存、实机报告SHA与封面，冻结主描述及完整notes的字符数、行数和SHA。不会加载Steam DLL、切换模式或上传。
- 匿名公开读回工具：[verify_publication.py](../tools/verify_publication.py)。它复用现有完整notes解码比较器，另核对精确item/AppID/owner/可见性/tags、公开封面、media库存、原图字节与解码像素，并保全原始匿名响应；真实图片审阅仍单独记录。
- 待根任务交付后使用的[发布窗口输入与收据方案](publication-execution-inputs.md)：准确记录真实provider的模式控制缺口、现有官方Steam菜单/UIA路径、原生工具JSON和命令，以及基于官方正例的匿名sidebar依赖解析规则。该页不是实机或发布成功证据。

该helper当前尚无已证明的DLC/required-mod机器字段。报告分别给出`metadata_notes_cover_media_ok`与`dlc_and_required_mods.state=not_observed`，两个实际ID数组保持`null`，不把API缺字段当成无依赖。后者未观察时整体`ok=false`，其余公开核对通过会标记`pending_dependency_observation`。正式发布窗口必须从同一item的真实匿名Page DOM/sidebar记录“Required DLC”与“Required items”的实际解析规则、页面正文SHA和两个ID数组，由最终发布报告合并判断；本准备包不新增未必要的原生能力。

2026-10-04的只读准备核对确认Steam公开页确有两个独立栏目，一手正例分别为[Royal Court Event Pack](https://steamcommunity.com/sharedfiles/filedetails/?id=3360676953)与[CFP/EPE韩语补丁](https://steamcommunity.com/sharedfiles/filedetails/?id=3538192508)。本机三次匿名原HTML请求均收到HTTP429，正文与SHA保留在`D:/ck3-experience-drain-feasibility-20261004/publication-dependencies-research-01/`；没有从这些失败响应推断任何依赖状态，也没有重试或改变Steam模式。

产品机制仍在实机验证，文案是可审阅草稿。最终属性转移和数值边界确定后再冻结；之后有字节变更必须创建新的冻结目录，不能覆盖旧输入。

## 本机API预检

2026-10-04使用本仓`tools/.venv/Scripts/python.exe`（Python3.14.7、`mcp==2.0.0`）通过official in-memory MCP client调用`workshop_native_symbols`。实际DLL为本机Steam管理安装的`steam_api64.dll`，SHA-256为`1db3fd414039d3e5815a5721925dd2e0a3a9f2549603c6cab7c49b84966a1af3`。Create/Submit、additional previews、download/ManualDispatch所需exports均存在；没有加载DLL、操作Steam模式或发布。原始输出保留在`D:/ck3-experience-drain-feasibility-20261004/publication-preparation-01/`。

首次新物品需要真实订阅后才能走预期的普通订阅缓存路径。既有`workshop_native_download`明确不订阅，因此补充通用exact-target `workshop_native_subscribe`，合同见[共享订阅能力](../../docs/workshop-native-subscribe.md)。它以真实call handle读取callback1313，核对精确item ID与EResult，再读取同一item的Subscribed bit。订阅完成仍不证明安装或文件内容。

订阅、下载、媒体、native Create/Submit和MCP surface的相称静态回归共44项通过。真实订阅留待最终发布窗口，不从静态成功外推。源文件SHA、stdio和官方symbols输出保留在`D:/ck3-experience-drain-feasibility-20261004/publication-subscribe-static-01/`。

## 正式执行顺序

1. 根任务确认L0–L3、干净玩法图、九语发布格式审计、exact clean commit/tag、builder staging与manifest。外层`.mod`指向正式staging，首次无ID，内层descriptor始终无ID。
2. 取得屏幕排他槽；结束CK3，核对任务总线及当前账号占用后，为发布任务进入必要在线窗口。不得顶掉其他机器会话。运行native probe，绑定当前AppID和owner身份。
3. 冻结完整Create plan及notesA，使用同一耐久receipt执行`workshop_native_publish`。Create返回ID立即保全，未知callback不得重建。新的Workshop Legal Agreement只能由物品所有者亲自处理。
4. 匿名核对新item元数据。对该item调用`workshop_native_previews`取得现有strip，冻结独立media update及完整notesB，再追加至少一张干净真实玩法图。每图须严格小于1MiB。notesB包含实际媒体变化，避免把相同正文的多个条目混为最终版本。
5. 真实`workshop_native_subscribe`取得callback1313及Subscribed状态；保存任何自动下载的旧cache，证明该精确缓存路径不存在，再调用`workshop_native_download`，等待exact callback3406与真实安装路径；严格比对正式manifest，按产品要求复核实机等价性。
6. 原生联网任务完成或失败立即恢复Steam离线，并审阅新的真实像素，不能用旧帧或回执时间代替。重建canonical无内层ID的staging，外层`.mod`保留新ID。
7. 在Steam离线时匿名读取最终标题、主描述、tags、DLC/依赖、可见性、封面、media数量/顺序，下载公开CDN图核对字节/像素。独立读取本次Change Notes entry ID与HTML解码、换行归一化后的全文，精确匹配冻结字符数、行数与SHA；若native未公开更新，优先在Steam离线时使用既有登录网页会话编辑owner page的同一条目并再次匿名核对。仅实际原生动作需要时另开短在线窗口，不为HTTP等待让客户端保持在线。
8. 根任务发布GitHub Release并验证附件SHA。只有真实上传、公开notes/media、fresh-cache、离线恢复均通过后，才形成永久`docs/release-changelogs/superman-qiang/1.0.0.md`与本mod发布报告，并commit/push master。源码tag不移动。

以上是执行方案，不代表任何一步实际完成。原片、失败attempt、输入快照、回执和缓存保留，不能为收口删除。
