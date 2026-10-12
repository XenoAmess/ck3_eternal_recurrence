# 礼与道：儒家礼仪与学统

0.1.1 Alpha 已于 2026-10-12 发布到 [Steam 创意工坊](https://steamcommunity.com/sharedfiles/filedetails/?id=3817934804)，目前供内部测试；主描述与完整 Steam Change Notes 已完成公开核对，R0068 已确认实际订阅缓存与正式构建一致并由 CK3 加载。兼容声明 CK3 1.20.*，当前实机版本 1.20.0.4。源码采用`lyd`命名空间，不覆盖原版经学、道学或基督教定义。正式安装仅使用`tools/build_release.py`产生的staging。

0.1.1 直接丰富原版儒家：36 种新增礼仪归属 `confucian_faith`，保留经学、道学与原版主礼仪；36 项信条各有常规增益、代价与个人选择效果。正常入门不再新建共宗，旧定义只作历史兼容。当前源码另含未发布的 0.1.2 建立宗主修复候选，其授权运行时变更与未验边界见下文。详见[原版儒家接入与旧档边界](docs/vanilla-confucian-integration.md)。

0.1.2 候选重新设计全部36条常驻与个人效果，并新增36个专属行动、52个选择分支。事功侧重直辖、赋税和营建；六艺允许选择六种训练；知行相资要求先考察、等待一年后再实践。常驻专项成长通常20–30%，技能或勇武通常+2–4，县域发展通常10–20%，主题成本通常3–5%。个人信条必须在原版窗口实际选取，学习或允许不等于生效；主动行动另有真实费用和个人冷却。完整[数值与原版参照](../docs/li-yu-dao/2026-10-12-36-tenet-strength-and-native-specialties.md)、[行动费用与效果](docs/tenet-active-practices.md)均已入库。当前为源码候选，尚未发布，完整实机效果仍待验。

一期验收尚未完成。B4 政治继承候选与玩家继承状态保护有已知失败；新制度头衔冷重载、向同信 NPC 授予和 C3 完整争议链未完成合格验收。推荐独立新存档，后续不保证试玩存档无问题迁移。玩家可见范围见[工坊说明](../workshop/li_yu_dao_description.bbcode)。

当前按迭代施工；运行功能和证据以[验收矩阵](docs/acceptance-matrix.md)及仓库`docs/li-yu-dao/`报告为准。静态通过不代表已完成实机。

一期先做跨时代自由模式、样板祭修与可重复分合；历史开局分布、朝代称号和学派时代门禁另属二期。[专项设计](../docs/ck3-confucian-repeatable-reunion-and-schism-design.md)定义授权与范围。

开发命令使用已验证Python：

```text
python tools/gen_content.py
python tools/gen_runtime.py
python tools/validate_static.py
python tools/test_build_release.py
python tools/test_run_acceptance.py
python tools/test_school_consent.py
python tools/test_content_leadership.py
python tools/test_institution_candidate.py
python tools/build_release.py --check
python tools/run_acceptance.py --output <fresh-attempt>
python tools/run_acceptance.py --preflight-only --output <another-fresh-attempt>
```

只读runner保存当前游戏版本、EXE哈希及每条L0命令的原始输出；不启动游戏。退出码2表示live环境缺失，产品L0仍可单独为GREEN。I2 已实现逐派表决、玩家同意、代表签署及可重复分合流程；I3 已集成师承同意和政治争统；I4 已扩充到36礼仪、36信条和36修习。部分代表路径已有实机证据，完整一期验收仍未完成。C3 与世俗宗主工厂按实际人物、教义及授权条件开放，并非全局关闭。原生分合准入绑定永久入库的 R0002 原语证据，不代表 I2 流程通过。实机验收使用简体中文，英文只做L0结构检查。

运行脚本统一由 `gen_runtime.py` 编排。I3 独占宗主工厂与迁移钩子；单独运行 `gen_school_consent.py` 默认只生成自己的文件。历史 C2 共享模板仅可用 `--with-legacy-shared` 输出到外置候选，禁止覆盖正式目录。

I3b 的“发起宗主制度议案”位于宗教决议。原版儒家 `confucian_faith` 中的新礼仪玩家可发起，不必改信或先成为经学、道学领袖。发起者须已启用本模组、在世成年、有地且持公国以上头衔、无失能，并满足本派教士性别要求；信仰与全部实际礼仪须无宗主、教士制度兼容，且无其他宗主、争议职位或待办议案。按钮可见不等于资格已满足，应查看其条件提示。

建立宗主的步骤是：为每个活跃派提名合格学者代表（学识至少 15）并取得接受，封定名单，再分别取得各派三分之二学者赞成、所有存活玩家的明确同意和各派代表签署，最后查阅完整条款并实施。实际存在的原版经学、道学同样参与，不得用新礼仪多数代替；无信众且无伯爵领的休眠礼仪不贡献赞成票。该决议建立整个当前儒家信仰的真实世俗宗主，完整礼仪名单均接受宗主制度；保留原信仰、经学、道学、主礼仪及所有信条，不自动在开局实施。已有宗主时不能重复建立，应使用“设立我的对立领袖之职”及后续争统入口，仍须满足该入口的实际条件。

发起议案不要求学识15；自提名代表要求本人在世、成年、自由、非无能且实际学识至少15。若本派有信众却没有合格学者，不能封定名单，也不算休眠：先撤回议案，通过正常培养或实际可用的招揽、改信、转派准备同信仰同礼仪的合格学者，再重新发起。仅加入宫廷或获得学识生活方式经验不保证资格达标。

新工厂在授予宗教头衔前检查其专用继承法例，失败时不承认成功。政治继承候选、玩家继承人及全部政治头衔保护尚未取得本次实机证明，静态检查或独立原语夹具不能替代正式 B4 验收，也不能授予礼仪领袖身份。制度模块由 `gen_runtime.py` 统一生成；`gen_institution.py --check` 可独立只读核对，其单独写入仅允许外置目录。

整合003候选实际执行155项产品测试和6项外置边界检查，13条检查命令通过；包括校验器错误接受反向门禁及纯展示效果的真实回归。运行与机构的实机验收另行记录，不以这些离线检查替代。

Workshop 物品 ID：`3817934804`；[首次发布记录](../docs/release-changelogs/li-yu-dao/0.1.0.md)。不上传源目录，不得将测试夹具或探针加入正式 staging；`remote_file_id` 只保留用户目录外层 `.mod`。
