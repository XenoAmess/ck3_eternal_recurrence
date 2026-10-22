# Saved campaign profile inventory v2

`prepare_saved_campaign` 现在按已核验的投影角色判断 cold initializer。正式产品自带的 `on_game_start_after_lobby` 可以保留；研究夹具或诊断 overlay 携带相同初始化器仍被拒绝。此改动只恢复离线 profile 准备路径，实际冷载与游戏业务资格仍需各自的实机观察。

旧 `ck3-saved-campaign-product-only-profile-v1` 没有文件来源类别。R05 实际将研究夹具放进 product carrier；部分 LYD case 同时启用正式产品和诊断 overlay。因而不能用旧 schema 名称或目录名字推定所有文件都是正式产品，也不能直接删除旧关键词守卫。

新合同由 [saved_campaign_profile_inventory_v2.py](../../ck3_autonomous_player/src/xar_autoplayer/saved_campaign_profile_inventory_v2.py) 统一编码、解析和核验。JSON 必须恰有六个字段：

| 字段 | 合同 |
| --- | --- |
| `schema` | 固定 `ck3-saved-campaign-profile-inventory-v2` |
| `profile_mode` | `vanilla` 或 `enabled` |
| `profile_path` | 当前准备 profile 的绝对路径 |
| `enabled_mods` | 与实际 `dlc_load.json` 顺序一致的 descriptor 数组 |
| `product_files` | 完整 enabled 投影及其外层 descriptor 的 `{path, bytes, sha256}` 数组 |
| `projections` | 每个 enabled descriptor 恰有一项 `{descriptor, root_path, source_role}` |

`source_role` 只有 `formal_product`、`case_fixture`、`case_overlay`。vanilla 的后三个数组必须全空；enabled 的三个数组必须非空。缺失、`null`、多余字段、旧 schema、未知角色、重复 descriptor／file pin／投影，以及重叠投影都不接受。文件长度必须是有界整数，拒绝布尔值、浮点和字符串；SHA-256 使用小写十六进制。

消费时先把 JSON 校验为不可变 dataclass，再核对实际 profile、enabled 列表、descriptor 解析出的 root、每个文件的长度及 SHA，最后核对完整文件闭包。完整闭包成立后，只有 `case_fixture` 和 `case_overlay` 的 `.txt` 继续接受 cold initializer 拒绝检查。角色不是游戏资格字段；不存在按产品名称放行的列表。

[ck3_mod_acceptance_saved_profile_v2.py](../../tools/ck3_mod_acceptance_saved_profile_v2.py) 复用原共享复制器，写独立 v2 inventory，并实际读回 JSON。现有 19 个后续 profile materializer 入口和 5 个手写 inventory 入口都明确指定角色；R10 空模组消费者、TED 合同字段和对应测试同步迁移。host 只消费 v2，不把 v1 当作兼容别名。

`ck3_mod_acceptance_prepare.py` 继续作为字节固定的旧复制后端，七份既有 XQOL support pin 与历史 compatibility review v2 不改。其内部 v1 inventory 只用于读取这次真实复制结果，未来 host 收到的是新写出的 v2 文件。独立 Workshop cache 合同不属于 saved-campaign 权限，仍按原 cache 范围测试。旧冻结场次及历史来源／回执不追写。

[test_saved_campaign_profile_inventory_v2.py](../../tools/test_saved_campaign_profile_inventory_v2.py) 构建真实 Living Artifacts 正式 staging，经真实复制器、持久 JSON 和从当前 host 提取的实际函数节点进入保存复制路径。它覆盖正式 bootstrap、同字节 fixture／overlay 拒绝、第二个 overlay 不能借正式产品混入、字段／类型／角色／文件闭包错误和序列化往返。保存输入明确为手写 preflight bytes，未冒充可玩的存档或实机加载。该模块、SDK 的实际 host profile 测试及三个新完整文件的 strict 检查已接入 Official Runner CI 的共享 acceptance step。

本次离线记录属于 `machine_id: pc-20260924rtuf-f11af23c08`。原阻断回执位于任务外置目录 `environment/cold-formal-bootstrap-refusal-a01/result.json`，由当前 R11 选定的真实正式 staging 复现。修复后的源码通过不能改写 R11，也不证明新版本已实机冷载；后续必须从新冻结源码启动并观察正式产品 bootstrap 的实际加载后态。
