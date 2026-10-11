# 礼与道：儒家礼仪与学统

0.1.0 Beta 已于 2026-10-11 发布到 [Steam 创意工坊](https://steamcommunity.com/sharedfiles/filedetails/?id=3817934804)，兼容声明 CK3 1.20.*，当前实机版本 1.20.0.4。源码采用`lyd`命名空间，不覆盖原版经学、道学或基督教定义。正式安装仅使用`tools/build_release.py`产生的staging。

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

I3b 候选新增无宗主共同体的制度议案、明确提名、逐派三分之二学者授权、全体存活玩家同意和代表签署。原生实施按实际业务授权条件开放；独立外置制度原语夹具不证明正式共识流程通过，也不授予礼仪领袖身份。新增制度模块由 `gen_runtime.py` 统一生成；`gen_institution.py --check` 可独立只读核对，其单独写入仅允许外置目录。

整合003候选实际执行155项产品测试和6项外置边界检查，13条检查命令通过；包括校验器错误接受反向门禁及纯展示效果的真实回归。运行与机构的实机验收另行记录，不以这些离线检查替代。

Workshop 物品 ID：`3817934804`；[首次发布记录](../docs/release-changelogs/li-yu-dao/0.1.0.md)。不上传源目录，不得将测试夹具或探针加入正式 staging；`remote_file_id` 只保留用户目录外层 `.mod`。
