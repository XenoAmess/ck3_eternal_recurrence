本包只提供 frozen632 的外置检查点读取器与断言合同，未读取实际存档正文，未操作游戏、MCP、main 或 Git。未来 PID、revision、TitleID 和实机 PASS 全为 NULL。源读取器最终 SHA 为 `b88305a767a6d793fedd6b117b1ffe4b05e958788bcab1e4710ffae8f12585cd`。

ROOT 在 JOIN2 closed boundary 后另开实际 attempt。先完成正式 I3b，让真正的 `lyd_i3b_result_head_title` 产生 T；使用已封 I3b adapter 的 DISCOVER 与 STRICT_GRAPH 分离结果。`partial_native_title` 不能当成功 T。其后独立执行已审查 exact T→distinct sameFaith NPC65865 的私有夹具。夹具准备与正式宗教领袖创建分开记账。

先获取新的 checkpoint，使用 `ROOT-REQUEST.unbound.template.json` 创建新的 bound request。继承 actor31254、main Rite169、native HoR31254、candidate65865 只用于检查来源预期，必须以当次真实图重新确认；七个政治 Title ID 必须由实际完整基线绑定，不能填历史猜测值。CLI 是 `C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe -B -X utf8 <本包>/challenger_reader.py --request <新外置 request.json>`。本包没有执行该 CLI 的实际存档请求。

第一次只用 DISCOVER。它保留完整当前 Faith AST、所有当前 Faith Rite、每个 native Title ID，以及角色关联的完整 Title/Character AST。正式 saved Title scope typename、完整 native challenger collection、每个 challenger_sponsor 的字段位置必须由 ROOT 的真实 native 观察与 checkpoint 逐项交叉确认。不要直接沿用 synthetic fixture 的 `title`、`synthetic_native_collection` 或 `synthetic_native_sponsor`。

填写新的 `NATIVE-SERIALIZATION.unbound.template.json` 后才运行 strict phase。显式 field path、encoding、item_title_path（record 编码时）和 sponsor_title_path 必须符合实际序列化。支持完整 anonymous scalar、repeated scalar、anonymous record Title集合；sponsor 当前支持 Title AST 内显式路径。若实测 sponsor 位于 collection item 或别处，需要新的外置源码适配，不能猜路径。默认 missing collection 是错误；只有实际 native count0 与缺字段语义被交叉确认后，才可设置 absence_means_empty。重复成员拒绝，不去重；两个以上 challenger 必须全部保存，不取 first。

ROOT 的 authority 字符串与 evidence SHA 绑定只是输入来源声明，读取器不会认证 native 身份。NULL/基本 schema gate 在读 save 前执行，完整 codec/path/typename 语义校验发生在 projection 后。绝不能把本包描述成已证明当前存档原生字段映射、完整人类名单或 native law/property 资格。

| 操作 | 读取/断言 | 额外真实观察 |
| --- | --- | --- |
| N2 handoff | HANDOFF：同一 T、native HoF=NPC、T.holder=NPC、HoR169=actor | 原生 clergy/AI/成年/能力资格；完整政治7/NPC非宗教 Title 和 actor primary/capital 基线 |
| N4–N5 注册 | REGISTER paired with handoff：唯一 C 增量、C.holder=actor、typed owner F/R、native self-sponsor | 当次 `.330`/`.331` instance 与 revision；ACK 不代替集合读回 |
| N6 重复注册 | REGISTER pair + 完整 all_title_record_ids/当前 C3 状态比较 | 只查询真实 hidden/invalid row，不发送重复 confirm |
| N7 撤销再注册 | WITHDRAW pair 明确 watch old C；再 REGISTER 新 C2 | C2 != C1；only C1 消失/invalid holder，其他 challenger 全 AST 与 sponsor 不变 |
| N8 开议会 | ROUND_ACTIVE，捕获 S、F/R/T/NPC、全礼仪原生 HoR 与 owner/serial、全部 captured humans | 当次完整 living is_ai=no roster；actor 正常 `.310`/`.311`；NPC `.312` 原生 35/65 响应 |
| N9 重复开议会 | ROUND_ACTIVE pair + exact actor C3 rows 不变 | 查询 closed row与原生事件集合，不能仅从 saved graph 证明无重复派发 |
| N10 取消再开 | ROUND_CANCELLED；调用 `assert_repeat_round(before, after)` 要求 S+1 | 取消释放当前 owner/S，claim保留；实际新一轮派发独立观察 |
| N10 old `.329` | 调用 `assert_stale_timeout_preservation(new_before, after_old329, old_S)` | 真实 old `.329` 已到达的证据独立绑定；helper 不验证事件投递 |
| N11 认可 | ROUND_READY→同 S RECOGNIZE：同 T 变 actor、C精确撤销、locks/consents清理 | allYES、真实 NPC response、人类完整名单与 live `.320` shown/enabled option；head_yes0 是有效负例 |
| N13 重载 | 新checkpoint保持当前phase图与已封pre-exit pair | ROOT另行 cold load；新的 PID/profile/revision，旧地址/旧 revision不可复用 |

每个 after request 的 `before_state` 都绑定此前 STATE.json 的精确 bytes/SHA；读取器自动带上此前人物与 Title watch，撤销后不会因元数据已删除而漏掉 old C。pair helpers 是读取器的纯源接口，可由 ROOT 在新外置 adapter 中导入并 hash 绑定；它们不是公开 MCP 工具或已执行的实机步骤。

政治7、NPC其他所有 held Title、其他 challenger 的全 Title AST/sponsor、全部 Faith.main/Rite.parent/currentFaith.HoR 必须不变。actor landed_data 只允许精确已验证 T/C 的 anonymous domain 行差异，其他 marked/orphan Title不能蒙混豁免；所有 actor-held Title 原文也保留。N11 认可后 NPC原生primary/court/liege变动需要单独披露，不能自动写作全政治状态不变。

`SAVED_GRAPH_ASSERTIONS_MATCH` 仅表示声明范围内 saved graph 通过源断言。native business credit、law/四属性、全人类名单、真实NPC响应/old329投递、fresh reload 都保持独立 UNKNOWN 或 NULL。default21 仍缺专门 native完整挑战集合接口、多人控制、NPC强制响应、launch/load-save；本包补通用离线读取实现，没有补出这些原生能力。
