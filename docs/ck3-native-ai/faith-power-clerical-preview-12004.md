# Faith & Power：1.20.0.4 傀儡互动默认预览与核心槽位悬停

machine_id：`4-8e1c2f1861`。2026-10-19 源知识增量，基线 `28502c33fb2990f879d6ff935b7d97a107678e64`；精确 UTC、文件 SHA 与检查范围见文末证据。固定 EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本文整理静态原件与既有回执；两傀儡预览源码候选尚未编译、派发或取得窗口截图，不能作为当前业务资格。

## 两个原版互动的有限默认态

仅允许 `make_clerical_puppet_interaction` 和 `make_external_clerical_puppet_interaction`。两段定义各声明六个选项，顺序为 `hook`、`skill_support`、`piety_support`、`dread_support`、`friendly_support`、`lunacy_support`，均未写 `starts_enabled`；原版 `.info:349–351` 规定省略时默认 off。两段也未覆盖 `needs_confirmation`；`.info:282–285` 规定省略时默认 true，false 会直接进入效果路径。

因此每次必须重新构造并双读真实默认 context，核到六个固定原生 flag ID、bank=0、原生 selected=false、kind=0、`needs_confirmation=true`。静态默认不代替这个检查，也不证明发送资格。

不得直接调用 `0xAF2810`：同一分派器在 confirmation=false 时会进入 Send 构造与队列。候选仅复用已证明的 true branch 呈现叶，不开放 Send、普通 initiate 或 option selection。

## 原版窗口链与来源守卫

`handler+0xF0` 取得原版 `CInteractionConfirmationWindow`。候选复用既有 Grant context 生命周期和 typed wrapper：

| 阶段 | 固定 .4 来源 |
|---|---|
| 复制默认 context | `0x10E6FE0`，完整 1,358 B；原版窗口 context 在 `model+0xC8` |
| 打开普通确认窗 | `0xAF34A0`，五个连续 .pdata span 合为 603 B；kind0 对应 `enum11, mode1` |
| refresh | `0x10E7800`，完整 136 B |
| 正常关闭 | vtable+`0x88`=`0x110B2C0`；原字节 `48 8b 01 48 ff 60 20`，尾调同 typed vtable+`0x20`=`0x10E6CC0`（Hide 覆盖体 56 B） |

Confirmation primary vtable=`0x45250E8`、secondary=`0x45250C0`、type descriptor=`0x5731D88`、COL=`0x4AFDCF8`。窗口 root 为 `model+0x60`；检查 `character_interaction_confirmation_window` 的同一 root、GUI context、handler/owner 回链与精确方法槽。当前 owner 线程、TLS、paused/date/actor、完整 recipient、connection/revision、双方角色、来源文件 SHA 和固定原字节都必须吻合。可见旧确认窗的 context 不同就拒绝覆盖；动作前再双读窗口与帧。

原版 ctor=`0x10E5E30`，OnInit=`0x10E64D0`，OnOpen=`0x10E6730`；**必须已有原版初始化的 typed root**。候选不强制 OnInit，不绕过此守卫；首次冷载是否已有 root 仍是实际缺口。关闭清理仅核必要 leaf/span；`0x110B2D0` 只保全首个 .pdata 片段，不冒称完整传递调用图。

现有 `ck3_query_faith_power_ui_v1` / `ck3_present_faith_power_ui_v1` 的有限候选协议使用 `window_kind=clerical_interaction`，`subject_id` 为完整 uint32 收件人；target 别名只取 `clerical_puppet` / `external_clerical_puppet`。顺序为默认 query → 带原 receipt 的 `open_clerical_preview` → 独立后帧 query 确认双方/default options/root visible → `close_clerical_preview` → 独立后帧 query 确认 hidden。ACK 只表示 pending，未知结果不重复提交。policy 与 capability 实际准入没有在研究包中修改。

## 已选择核心槽位的悬停

原 census 已由 `left_side/tenets_grid/tenet_name` 的 parent3 识别 `rite_core_tenet_slot`，原 op203 使用同一载体。候选仅把这个已有可见、owned 载体补入 `rite_creation` 的 hover/query target，沿用 exact Hover 原字节、祖先、归属、可见性、modal/source、receipt 和双读守卫；无鼠标、滚动或新增导航。

实际 selected card/slot、原生 definition key、tooltip 完整正文和截图像素分别验收。caption 或“希望选中的 key”不能填造槽位 key，已采 selected card 也不能算 fullbody。

## 本轮核心选择的必要知识

顺应 `tenet_adaptive` 的 can_pick 排除 `doctrine_pluralism_fundamentalist` 与 `doctrine_pluralism_righteous`，通常应选 `doctrine_pluralism_pluralistic`。R28 初始草稿为 righteous，独立 choices 的顺应 `passed_selectable_trigger/final_selectable=false`；初次动作另报 typed-source-row 拒绝，不能把这条错误文案冒充某个 can_pick 分支的原生诊断。随后独立 `selected_slots[12]` 读到 pluralistic，再读到顺应被选入 slot0。本轮冲突不能解释为“顺应不存在”或用跳过 can_pick 解决。其核心 `parameters` 提供 `allow_adopt_any_holy_site`，个人同名版本没有该参数；采用消费者查操作人的当前 Rite，仍须满足其他 AND 条件。

继承说／义子论／嗣子论均对应 `tenet_adoptionism`。定义要求 `by_god_alone` DLC，`is_shown` 查 `has_pam_dlc`；核心 can_pick 要求 Christianity，并满足 `unique_christology_trigger`，不能同时选合性论／一性论等冲突核心。具体中文名按原版 `first_valid` 命名条件决定，不能概括为只随当前礼仪语言变化。其采用参数也只在核心版本。

本轮原版像素由唯一操作者 `/root/capture_runtime` 审阅，本文只复用其已封 index/pins，没有重读或重 hash 图片：

| R28 UTC | 独立原生读回与实际卡片 | 仍缺 |
|---|---|---|
| 04:15:20 / 04:15:31 | slot0=`tenet_adaptive`；顺应卡片、975 费用与 pluralistic 前提 | 完整核心 tooltip 正文 |
| 04:24:37 / 04:24:39 | slot0=`tenet_adoptionism`；继承说卡片、325 费用 | 完整核心 tooltip 正文 |

精确 receipt、JSON pointer、原图 SHA 和操作者审阅声明见[有限观察投影](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v6-20261019/resume-20261019/research/doc-source-a07/R28-SELECTED-CARDS-a07.json)，SHA `bfa776ffba980b08d7ee7556e238d68a906e7ce63b42a2a40b4119ec1faada95`。原 groups 回执的 current-category 缓存仍显示 righteous，实际 `selected_slots[12]` 为 pluralistic，两者不能混作同一观测。卡片选中不代表 fullbody、新 Faith/Rite 提交或采用业务通过；本轮无 world Confirm。

## 精确来源与检查层次

| 原版相对 game 路径 | SHA-256 |
|---|---|
| `common/character_interactions/00_puppet_interactions.txt` | `7f2b5d1541ca0e3568f6bff9fb74a17fc21ea21b364c2855a92f13a147d19fa7` |
| `common/character_interactions/_character_interactions.info` | `cc2442a313a6b1a2a7fa02b92a094276edfe39c60835c3286172c5b6d7b70a37` |
| `gui/interaction_confirmation.gui` | `34b86f5253bc564f3e3ecdd4a037f4d66397c4063defa450208db5eb702dac68` |
| `gui/interaction_templates.gui` | `8dc57c1edd8c682c78a0c54cd2d709f95707c6a33ad98d6242991e449db835bc` |
| `common/religion/tenet_types/00_tenet_types.txt`（1708–1780） | `d9e18a077d81f18f030d795ef45cb4aa5b7db246007043d5b0fe401baaf88abd` |
| `common/religion/tenet_types/00_pam_tenets.txt`（1575–1649） | `5d57cf371aedf4d2266286b8fe30d7f0c90eb8d4079019712c907a4b954ce02a` |
| `common/scripted_triggers/00_religious_triggers.txt`（2061–2070） | `e9d0b56130464eabdcd670fa6cf814534d11c99da1e8b3fc1e69e9c3e36d2bb2` |
| `common/scripted_triggers/pam_scripted_triggers.txt`（78–112，命名） | `0ad98f123b6739593b9ab2c170d0e8c9b3d9d941baa9d3580296dd2139b2ea6e` |

源知识复用：[采用知识 payload](evidence/holy-site-cross-religion-adoption12004-v5/knowledge-payload.json)、[参数与命名作用域](faith-rite-parameter-scopes12004-v6.md)。以下外置原件仅证明记录的这台机器，保留期限见各 CLOSED，不能外推其他机器安装／实机状态：

- [a05 原版脚本／GUI 行与 SHA](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v6-20261019/resume-20261019/research/confirmation-abi-a05/SOURCE-PINS-a05.json)，SHA `2867b4a9387c21db54efed58e9fd8d8bb5a0e4458ce71e24af1b9a52b42c2936`。
- [a05 RVA／true branch／连续 handler 原字节索引](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v6-20261019/resume-20261019/research/confirmation-abi-a05/ABI-CANDIDATE-a05.json)，SHA `223b08aaf059391ae570a2dadd13d22617d5a9f59c66c91e129442f52bb7dba6`；它的历史 pending 由 a06 部分补齐，不追认实机。
- [a06 最终 37 个 RVA spans／6,520 B 的逐项原件映射](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v6-20261019/resume-20261019/research/clerical-preview-source-a06/SOURCE-INDEX-a06.json)，SHA `7c3908d7b606b6034d969f49812ce8203c66e0552eaa7de8bbd468f1eddd5e9a`；[正常关闭原字节](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v6-20261019/resume-20261019/research/clerical-preview-source-a06/native-close-thunk-a04.json)，SHA `68c6197f581cfc23a03d1186641337b357c26b84b9d72ab29091d59355dec134`。
- [a06 合成 MCP 检查](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v6-20261019/resume-20261019/research/clerical-preview-source-a06/FOCUSED-CHECK-a06.json)，SHA `0045510fbade73b1280d3d004c5ce87bb039c0ce729730f063e5055249d2a2dd`，通过 3 个检查、12 次有限转发；[交付状态](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v6-20261019/resume-20261019/research/clerical-preview-source-a06/DELIVERY-a06.json)明确原生 fixture 未执行、未编译、未实机。`runtime_observed`、`callback_qualified`、`new_screenshot_observed`、`business_pass` 仍为 false。

## R30 默认预览实际边界与下一目标来源

`machine_id: 4-8e1c2f1861`，2026-10-19T06:45–07:08Z。当前court-chaplain58490来自实际campaign root；原默认query→open→独立visible/context一致／六项off→close→独立hidden已成立，无Send。但两张确认页原图都受旧locked继承说提示覆盖，不授完整正文画面。外部候选30490只来自相邻角色31531的当次liege关系，默认query实际拒绝default_context_not_qualified，receiptnull/dispatchfalse/未open，不能称其教宗或归因某个未返回的具体触发分支。

`d_papacy`定位实际title_key_not_found；原版`common/landed_titles/00_landed_titles.txt:68`的真实key为`k_papal_state`（SHA `fc8ea76e8bcc8c3aa8557dfb7226dc75b4aee8830e906c434754599ab8c75f55`）。下一场有限title map必须先取真实holder完整ID，再核默认context；原版is_shown要求双方同Faith、recipient为clergy且ruler，并排除actor本身、own realm-priest和own clerical puppet。title key存在不证明当前持有人满足这些条件。来源小件`resume-20261019/EXTERNAL-CLERICAL-TARGET-SOURCE-a01.json` 2,600 B／SHA `7aad5d5bed6d3922a5860f0ba781d53c9e578d7704084a70ad83ce32a10413ec`；原会话未新增head ID查询。

## R32干净own窗口、真实外部身份与未分型拒绝（2026-10-19）

`machine_id: 4-8e1c2f1861`；本节依据08:34–08:38Z实际小回执及09:32Z最终原图索引更新，上文未编译／首次root待验及R30遮挡是各自历史截点。R32使用P18实际DLL与98ee→8efe源码等价复用，具体编译来源见[展示专题](faith-power-presentation-ui12004-v6.md)。本场typed root确实已初始化；不因此保证任意未来冷载均有root。

同一campaign-root council读到actor31254的court-chaplain为58490。默认query→一次open→独立visible/context相同→close→独立hidden均已实际成立，key为`make_clerical_puppet_interaction`，kind0、needs_confirmation=true、六个固定flag／bank0／全部off。08:34:22干净原图显示“傀儡领地司祭”、实际对象、接受度+85及100虔诚报价；这是预览报价，没有Send、支付或关系变化。原图与全部五步native回执由[最终index-a02的screenshots/0](C:/workspace/ck3-faith-and-power-20261017/episode01/live/4-8e1c2f1861--faith-and-power--R0032/ORIGINAL-GUI-CAPTURE-INDEX-a02.json)绑定，PNG SHA `59dbcc0b47bb7eb76d4f767854fff1eda01934305b16c64e9ae656b32d4c3d6d`。这里复用operator／Root的原图审阅，不新增直接审图记录。

外部身份缺口部分闭合：08:38:38Z实际title-map解析`k_papal_state→TitleID4`，08:38:43Z独立title-holder读到30490，immediate_liege=null、top_liege=30490、不在玩家领地。30490已能准确称为“本场教宗国持有人”，不再仅由相邻人物liege推断；这些字段仍未分别证明其Faith、clergy及其余互动条件。08:38:46Z external默认query仍返回`clerical_preview_default_context_not_qualified`，receipt=null、dispatch=false、未open。

拒绝准确归到provider的`ReadDefault`聚合false，**尚不能分型为原生is_shown=false或某个具体trigger失败**。`ExecuteClericalPreview12004`已经越过exact source/owner/frame及initialized typed root，回执root_bound=true；`ReadDefault`丢弃`Prepare`的Observation细分reason，再把definition/kind、角色与alive、六项default shape、is_shown、needs_confirmation、双读一致性合成一个bool。`default_context=null`表示没有发布合格完整对象，不证明构造从未发生；失败先于window_exists赋值，其false也不能覆盖typed root已通过的事实。`Prepare`要求can_send读取调用成功，却不因can_send=false而拒绝预览，因此不能把本次失败归因为“教宗缺强钩”。当前没有返回精确失败分支，不扩大业务支持或放宽guard。

原版external的is_shown（脚本273–284）要求双方不同且同Faith、recipient为clergy+ruler，并排除own司祭／own theological puppet，不要求独立。kingdom tier涉及的强钩等位于can_send（316–362），不能由title身份反推其native结果。[a11实际来源与诊断](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v6-20261019/resume-20261019/research/r32-external-preview-a11/DELIVERY.a11.json)SHA `b33b4abd1557465237e4a95f6ed170ad0f58147a075488ae59c5c98e5ba50baf`保存9个小回执、6份现源码／脚本／文档SHA及未知边界；没有新增游戏调用或外部窗口。

SC10采用已取得的own原版大图、既有天主教信仰页P02的“信仰领袖／你的总主教”类型身份示例和明确标注的来源条件卡。P02没有30490图像ID绑定，不能称为本场30490人物页，也不把own窗口换标题当external窗口。最终[a35来源范围](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v6-20261019/resume-20261019/authoring/r32-final-lineage-a35/R32-FINAL-SOURCE-SCOPE.a35.json)明确external_interaction_window_obtained=false、100虔诚paid=false/sent=false；作者候选不是整片编码或人工听看完成。

来源条件卡的三个教义键须保留类别和本地化差别：

| key | 简中原版名称 | 作用域 |
|---|---|---|
| `doctrine_theocracy_temporal` | name“神权制”；“圣职专权传统”为类别措辞 | own司祭条件取此项；external三项OR之一 |
| `doctrine_monasticism_accepted` | name“接纳”，descriptive_name“接受隐修” | external三项OR之一；口播“接纳隐修”不是原版descriptive_name逐字全文 |
| `doctrine_monasticism_encouraged` | name“鼓励”，descriptive_name“鼓励隐修” | external三项OR之一 |

`pam_scripted_triggers.txt:1211–1220`给external三项OR及其余外层条件，`:1223–1229`给own司祭条件；复用前表SHA `0ad98f123b6739593b9ab2c170d0e8c9b3d9d941baa9d3580296dd2139b2ea6e`。`religion_l_simp_chinese.yml:837,995–999`为上述名称，SHA `1ba3f480f5255d3def8e9c968544daa2f5f4ee4ff40a9e214e60d623cc461d5c`；`religion_doctrine_triggers_l_simp_chinese.yml:42`为类别措辞，SHA `b878f4cc9f9dbc2f94898c09cb896ca682c17e82f34e0967f541b2ad2dd65ca0`。这些是静态条件，不追认本场external默认context合格。

R32实际原生GUI＋retained HANDLE OS0、public0、host1 RED及CAS12208/future0分别保留，见[展示专题的最终闭场记录](faith-power-presentation-ui12004-v6.md)。全局tooltips原生source/owner拒绝和a12仅修Python错误遮蔽，不补授外部预览、清栈或业务资格。
