# R0014：准备存档与开局初始化的边界

`machine_id: 4-8e1c2f1861`；本次整理 `2026-10-18T09:53:59.268869+00:00`。原始观察和精确文件身份见[来源索引](evidence/faith-power-r0014-saved-input/source-pins.json)。来源HEAD为0050e88；实际游戏安装仍为1.20.0.4/build25734779，本场没有启动CK3。

R0013母档已经完成角色、资源与领地准备。R0014改走普通saved_campaign入口，却沿用了带 `on_game_start_after_lobby` 的新开局夹具，公共 `prepare_saved_campaign` 在创建CK3前拒绝。原public run为2、host为1；没有native-report、launch或control，不能由此授原生动作、正常GUI关闭或游戏OS退出码资格。keeper原始allocate等待为0，实际STOP后于09:44:54.733525Z释放CAS11759。

修复保留公共守卫。后继六文件saved-only投影只调整一份on_action，完整移除初始注册和准备定义，其他五文件字节不变；保留新Faith创建后的角色准备链及显式事件。D2也受同一守卫检查，其原F输入已无该注册器，不存在v2合同豁免。投影通过静态检查仍不等于存档恢复、原版许可或采用成功。

公共资源闭场识别补齐这一项真实预启动原因，以及原intent／process／exit分文件回执。Windows venv启动器PID13664与真正supervise PID22016保留原值；该窄分支用已有唯一launch ticket、冻结argv、run/keeper路径、lease、proof与原host wait绑定，明确没有当时父子进程树证据。旧原因维持原行为，未知原因或存在native/game/control仍拒绝。候选对本场原件只读验证通过；一项focused回归包含坏ticket、缺实际wait、出现native和未知原因的负例，通过后不重复运行相同检查。

R0013物理母档为68,958,787B，SHA `62d18fe254d658356671269f194319a316729394da6f38b32da0d503bae1cd58`；saved-only README曾误写69,958,787B，独立勘误保留原文。旧driver的save_binding_mismatch仍在；新场必须重新读取实际角色、日期、Faith／Rite、钱包和持有关系，没有由物理文件存在取得恢复资格。

可迁移经验归入[系列制作经验](../../promo/ck3_faith_and_power/docs/production-experience.md)：运行模式或阶段改变后重新匹配输入与执行入口，研究或媒体只修受影响部分；原失败、资源闭场和实际玩法结果分别记录。下一步为新common与未用state，经公共准备恢复，再核真实hello、原版许可与一次教改／采用后态。
