# 两教派帝国领袖与纹章（2026-10-26）

machine_id: desktop-3fevhd2-1c74096080。来源为本机 CK3 1.20.0.4；文件哈希及观察时刻见 [来源回执](evidence/empire-heads-source-2026-10-26.json)。本文记录源码实现，不授予实机通过。用户已撤销政府绑定要求；本轮政府转换及维持回调已全部移除，a06历史构建结果保留，不作为撤销后产物的验证。

繁育教派绑定 `e_des_procreation_papacy`（繁育教廷），白绮教派绑定 `e_des_vivhite_papacy`（白绮教廷）。两者均为帝国级，不指定或转换持有者政体。Faith 的 `faith_details.religious_head` 指向各自头衔；没有历史持有人或本模组开局免费授予。两头衔的原生 CoA 数据库别名分别指向已有用户图纹章，没有复制 DDS 或添加未经支持的 landed_titles 字段。

`landless` 沿世俗宗教头衔 `d_sunni`／`h_dar_al_islam` 省略，按 `.info` 默认 `no`；原动态世俗领袖 setup 也不设置它。没有法理子级的 titular 头衔不因此等同于 landless 类型。`k_papal_state` 另有 `landless = yes`、`allow_domicile = no` 的教会领袖配置，本次不沿用该配置；实际失地与继承仍待验。

原决议 `create_hof_decision` 沿共享资格 trigger → `force_create_head_of_faith_title_effect` → `faith_creation.0011` 领取预定义空头衔。保留无现任领袖、世俗领袖教义、一处符合控制与同信仰持有人要求的圣地、奉献等级3及原计费；正常玩家基础虔诚费250。两教派另须独立，或直属领主主头衔高于帝国级，不把直属领主换成最高领主。不额外添加为政府转换服务的 TGP 门；原教义自身 DLC 资格保持。

原版信仰建立与礼仪更新还会有条件触发 `.0001`／`.0011`。产品保留这些正常自动建立／恢复流程；共享 dynamic setup 仅为两教派复用预定义帝国，其余信仰仍生成原动态公国。保留 `NEW_HOLDER`、正式转移事务、原 `new_title` scope 链及原继承法；两教派固定用户图 CoA，其余仍原生随机生成。没有政府转换、维持回调或相关贵族家族／庄园调用。原神权圣职＋世俗领袖静态预置及 stock `can_pick` 互斥规则保持。

## 原版来源

- `faith_types/_faith_types.info:7`：Faith 的 `religious_head`；`landed_titles/_landed_titles.info:7–20、206–218`：等级前缀与普通／分割继承创建门。本产品禁用这两个创建旁路。
- `landed_titles/00_landed_titles.txt:292–310` 的 `d_sunni`：宗教头衔继承属性；`:36–54` 的 `h_dar_al_islam` 及 `00_major_decisions_scripted_effects_3.txt:1108–1148`：更高层级宗教领袖先例。本 build 未找到静态 Faith 预绑定 `e_` 的原版先例。
- `coat_of_arms/coat_of_arms/01_landed_titles.txt:5744` 的 `b_vaticano = k_papal_state`：同数据库别名。`set_coa` 使用产品已有实际 bare key。
- `pam_decisions.txt:1091、1157–1222`；`00_religious_triggers.txt:1452–1552`；`00_religion_effects.txt:279–308、347–381`；`faith_creation_events.txt:5–23、112–153`；`religion_on_actions.txt:398–405、822–828`：正常决议和自动建立／恢复链。
- `02_religion_values.txt:4094、4102–4159`、`00_basic_values.txt:668、1134`：圣地、成本及奉献等级。

## 构建与实测边界

Java `SectPreset` 保存 title ID、颜色、路径及每语25键合同，不含预期政府元数据。validator 校验标题、CoA 别名及两个有限兼容脚本的 token 合同。正式清单56文件，开发35文件，外语增量21文件。既有真实生产者→staging／manifest／ZIP→独立 AST／公共导入／generic prepare 回归保留帝国／纹章范围；撤销后的完整 Maven 由 Root 统一重建。

直接源 AST、库存和 diff 检查只证明源码合同。还须实测正常取得、自然继承、非法领主层级及已有领袖拒绝，以及实际帝国头衔、主头衔、领袖指针与用户 CoA。旧预发布动态领袖不被本轮自动抢夺；没有两静态头衔的旧0.1存档不虚构迁移结果。
