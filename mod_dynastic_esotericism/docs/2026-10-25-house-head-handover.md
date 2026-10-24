# 家族族长交接与建族候选

观察时间：2026-10-24T21:12Z；`machine_id: desktop-3fevhd2-1c74096080`。用户提出“卸任家族族长，然后创建新宗族”。本包仍为未实机验收的实现候选，不追认 R0009。

R0009 原生 `create_dynasty` 首次拒绝现任 House head；后来由另一名真实信徒建族，47 人已迁入。这两件事实并存。不能把初次拒绝说成最终绑定失败，也不能把后来成功外推到只有族长一名信徒的情况。

CK3 1.20.0.4/build25734779，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` 的 House scope 原语 `set_house_head` 接受真实人物。执行链 `0x142D63EB0 → 0x1422F1E10 → 0x1422F2B20 → 0x142453410` 写 House head、处理家族头衔归属，并同步从实际 House heads 重算 Dynasty head。这不是独立的 `set_dynasty_head` 原语。底层仅检查非空有效目标及目标不同现任；产品必须另行限制真实存活、同一旧 House、不是原人物。

现成 `renounce_noble_family_title_decision` 不是纯交接：它要求特定家族头衔／DLC／继承人，经 `.0101 → tgp_renounce_estate_effect` 处理退休、头衔和宝物并切换玩家，不能整套复用于本功能。直接 `set_house_head` 也会转移该 House 的 noble-family title；不能承诺行政或贵族家族资产全不变。普通封建领地头衔不由该原语直接退位，实际仍须保存读回。

候选只修改既有绑定生产路径：当前人物合法则沿用；受 head 限制时，优先从同 Rite 找另一名存活、既非 House head 也非 Dynast 的真实信徒。仍无此类人物时，才由当前旧 House 的另一名真实存活成员接任。交接后重新检查原人物两个职位均已解除，再在选定真实 founder 的 Character scope 执行唯一 `create_dynasty` 及原双向对象绑定。低born路径保留；草案和取消不调用这一流程。迁族、犯罪和维护仍共用原生产模块，没有另一套补迁器。

旧 House 只有本人时，没有真实接任者，也未发现合法空族长参数。用户随后明确选择“生成一名同礼仪创始人物，保证建族”。最终候选据此增加最后兜底：先锁定原 Rite 的初始化阶段，再生成一名真实同 Faith／Rite、同文化、同地点的低born成年人，将其选为 founder，仍复用唯一的 `create_dynasty` 和原双向对象绑定路径。人物保留在世界中，不杀死、不删除、不切换玩家、不收额外费用，也不追改旧后代。初始化锁在整条生产流程结束后清除；重复初始化须复用已绑定对象，不能反复生成创始人物。该路径仍须实际验收，用户选择不是业务通过。

下一轮必须从实际场景保存验证：其他合格信徒优先路径、唯一信徒且有旧 House 接任者、旧 House 仅本人、低born、草案取消，以及有 noble-family title 时的额外身份变化。每项记录真实人物／玩家／Rite／旧新 House／Dynasty／头衔持有者和双向绑定；单有 setter ACK、语法或 Maven 通过不授业务资格。可在同一受管场次复用输入，但不写产品绑定或伪造回调。

外置证据：`C:/ck3-dynastic-esotericism-20261024/house-head-resignation-research-a01/FINAL.md`（8225 B，SHA-256 `c16fa0f0a745e13e628f81e4c2747f6d36c8af304299177b453322cf00456401`）；`R9-voluntary-house-head-transfer-a01/INDEX.actual.json`（1351 B，`0bb9c74ba3c2db291735adc65f0b8fca171fd6a1ee258b61f6fe8adebe56c18c`）。候选生产文件 5286 B，`9e1e8043f5783b4143e5ba7a3133ea7b05627bfed92962451a344c60a7022996`，保留 BOM。既有 Java parser 原退出 0、diagnostics 空、roundTrip true，只是 grammar。新独立 SDK 来源候选 `61b4b05afefb9b424bbf7805d6675ec1440f7297` 未改 SDK/native，完整默认 Maven 16 项通过、严格编译通过；真正交接及建族仍待实机。以上必要原件按通用策略保护至 2026-10-31 用途复核。

用户最终选择后的a02候选6555 B，SHA-256 `5cf9dd5280f6d0175c13a5e109306eaca97af3759176f8f05df57d4f6bff1a06`；外置索引 `C:/ck3-dynastic-esotericism-20261024/R9-voluntary-house-head-transfer-a02/INDEX.actual.json`，1888 B，`6a0211426df546c701a837d324d98ac0f1d2f0b1a1c64c2f0c738196f943b87b`。既有Java parser实际退出0，AST读回确认仅一个人物生产、一个建族原语、原三项绑定写入及入口初始化锁／末项清除；这些不等于NPC或交接实机通过。中英文正式选项说明同步披露两个影响；其他语言在正式发布阶段按最小变更重新翻译和格式检查。旧a01及两个构建原件保留，不冒充新源回执。

2026-10-24T21:40Z实际构建补记（同machine_id）：最终隔离候选 `2e7b8bf26cb4fa6606402f5689db8bdd1043e693` 已包含用户最终兜底、两语说明及原生输入cell。默认Maven原会话94612退出0，16项无失败／错误／跳过；实际生产者validate/build/fixture/verify全部0。15个JAR资源与源一致，17文件开发包／ZIP由既有清单消费者核验，13文件fixture／14来源pins一致。回执 `C:/ck3-dynastic-esotericism-20261024/resume-builder-a13/SUMMARY.actual.json`，68282 B，SHA-256 `e8d9eb3da11d67d4f81168c38cc8383c25e47d640507140432847d0d1c340ed3`。这些仅授离线生产链资格，尚未启动新场或完成实际交接／NPC建族。

原生输入夹具以正常决议 `des_acceptance_head_cells_decision` 在原玩家完成primary members_verified后只运行一次。独立无地成年A有旧House接任者B；独立C的旧House仅本人。两者仅经原版 `create_dynamic_rite` 创建测试Rite，先核实际原族长／Dynast及隔离关系，不写产品绑定、不调用私有业务effect、不覆写教义。实际Rite未继承宗族化或输入不合格记INPUT_NOT_READY；输入合格而产品后态错误仍为FAIL。Root另以+2完整原生成员和SDK保存验证旧新House／Dynasty、真实NPC、同Rite／Faith及Root身份；fixture旗标和grammar不能授分支通过。a02 effect 27411 B，SHA `f241e6a61fbd111bbe1846cebba96133af4483d68b78fba635fbc833c2c43e30`，含真实玩家／主头衔及持有者／House／Dynasty／可选head的前后保全检查。
