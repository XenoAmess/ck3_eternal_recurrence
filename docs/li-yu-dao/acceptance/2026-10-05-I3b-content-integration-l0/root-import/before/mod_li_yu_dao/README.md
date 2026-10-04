# 礼与道：儒家礼仪与学统

独立开发版，目标CK3 1.20.0.3。源码采用`lyd`命名空间，不覆盖原版经学、道学或基督教定义。正式安装仅使用`tools/build_release.py`产生的staging。

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
python tools/build_release.py --check
python tools/run_acceptance.py --output <fresh-attempt>
python tools/run_acceptance.py --preflight-only --output <another-fresh-attempt>
```

只读runner保存当前游戏版本、EXE哈希及每条L0命令的原始输出；不启动游戏。退出码2表示live环境缺失，产品L0仍可单独为GREEN。I2 已实现逐派表决、玩家同意、代表签署及可重复分合流程；I3 已集成师承同意和政治争统；I4 已扩充到36礼仪、36信条和36修习。各自正式实机验收待执行。原生对立领袖登记保持关闭，世俗宗主工厂要求既有教义授权。原生分合准入绑定永久入库的 R0002 原语证据，不代表 I2 流程通过。实机验收使用简体中文，英文只做L0结构检查。

运行脚本统一由 `gen_runtime.py` 编排。I3 独占宗主工厂与迁移钩子；单独运行 `gen_school_consent.py` 默认只生成自己的文件。历史 C2 共享模板仅可用 `--with-legacy-shared` 输出到外置候选，禁止覆盖正式目录。

开发版没有Workshop物品ID，不上传源目录；不得将测试夹具或探针加入正式staging。
