# 活武器说明首行标记

用户指定文字为 `【它是活的】`。中文说明从此行开始，换行后保留原说明全文。新增标记只作用于满足既有 `xalw_is_living_trigger` 的宝物，不改普通装备、名字或成长数据。

实现位于既有 `tools/living_artifacts_core.py` 生成器：独立 `xalw_ensure_living_description_effect` 保存当前宝物作用域，再以 `set_artifact_description` 设置 `xalw_living_description`；本地化通过 `[xalw_described_artifact.GetDesc]` 引用原说明。变量 `xalw_living_description_marked` 在设置后写入，避免重复前缀，不借用旧物已有的 `xalw_star_named`。

新觉醒和常规刷新进入该效果；月度宝物处理也在结算守卫之前调用，以便旧存档中已带★、甚至尚未装备的活武器在下次处理时补标记。不能据此宣称安装后暂停状态下所有旧物立刻更新。其他模组或原版日后主动重写整段说明的行为不在本次拦截范围内。

生成后仅两份 core 脚本及中英本地化发生变化，正式文件清单仍为57项。静态检查器同时纳入 `set_artifact_description` 的显示文本引用校验。按日常开发约定未翻译其余七语，未执行发布检查、正式构建或上传。

## 原版依据

`machine_id: pc-20260924rtuf-f11af23c08`，观察时间 `2026-10-25T05:22:07Z`。来源根为该机器的 `C:/SteamLibrary/steamapps/common/Crusader Kings III/game/`；路径只描述来源，不是其他机器的安装要求。

| 当前安装来源 | SHA-256 | 对应事实 |
| --- | --- | --- |
| `common/scripted_effects/sanctify_artifact_effects.txt` | `c9845702e20e84b1f52c37103d368ef9f5de8df3a389fc57556762c79d356901` | 保存宝物scope后调用 `set_artifact_description` |
| `localization/english/interactions/sanctify_artifact_l_english.yml` | `56ffadb31baca23e1f426e763055ae6b302b34e93d487a691a1a5e8fee64519b` | 原版以 `[sanctified_artifact.GetDesc]` 拼接原说明 |
| `gui/window_artifact_details.gui` | `718c86ae7abc6b884a52ffb8807e94638e5e03ec8042ca5f2b55bc8e89e4699e` | 说明区直接显示 `[Artifact.GetDesc]`，本次不覆盖GUI |

## 本次验证

同机实际退出均为0：生成器重新投影49份受控文件；`validate_static.py --game <上述 game 根>` 通过；既有 `test_core_generation.py` 的26项离线回归通过；修改的完整 `living_artifacts_core.py`、`validate_static.py` 通过 mypy strict。首次 mypy 未配置共享工具搜索路径而报告3个导入不可见；显式设置 `MYPYPATH=mod_living_artifacts/tools;tools` 后完整检查通过，未忽略导入错误。

命令、实际退出和输出保存在该机器的 `D:/workspace/ck3-living-artifacts-20261022/environment/living-description-marker-20261025-a01/`。本次只证明源码与离线检查；未启动CK3，未验证实际页面显示或旧存档中的原生运行结果，未更新创意工坊。
