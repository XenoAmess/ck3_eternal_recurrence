# 验收方案

目标构建：CK3 `1.19.0.6`。验收坚持 MCP/原生 bridge 优先：状态判断首先读取 `GameplayBridgeService` 暴露的暂停帧与角色/头衔查询；只有 bridge 尚无相应 UI 入口时才使用屏幕 OCR/点击，并在报告中单列该降级。

## 槽位与隔离

- runner 必须先进入 `xar_autoplayer.locking.exclusive_launch_lock(ck3.exe)`；锁被占用时等待，不抢占、不关闭别人的 CK3。
- 另对一次性 state dir 取得 `exclusive_state_lock`。
- 使用一次性 `-userdir`、仅加载正式 staging 与验收夹具；不读写真实播放集、工坊缓存和真实存档。
- 退出后要求 CK3 进程树为空，再释放槽位。

## L0 静态矩阵

1. 所有运行时 `.txt`/`.yml` 带 UTF-8 BOM；descriptor 无 `remote_file_id`。
2. 四个决议均有 `is_ai = no` 闸门，开关成对且默认关闭。
3. 三份原版 appointment 文件只允许五处受控插入；去掉插入块后逐字节等于 1.19.0.6 原版。
4. 五种 appointment type 均命中追加扣分；AI/关闭分支不命中。
5. 禁转标志的设置、所有权与清理对称；`on_vassal_change` 和 yearly 自愈均存在。
6. 英中 key 集合一致；其余七语言按日常开发策略使用英文占位并明确不宣称完成翻译。
7. 640×640 `thumbnail.png` 小于 1 MiB；release staging 与 ZIP 可复现。

## L1 启动与加载

仅加载本 Mod，进入主菜单及一局天朝/行政制验收夹具。要求 `error.log` 中无 `xqol` 解析或运行时错误，并由 bridge 确认 paused/map-ready。

## L2 功能矩阵

对行政制、贤能制、天朝制各执行：

1. 关闭态基线：在切换产品开关前冻结两个真实省份的原版 `current_heir`；exact-byte 静态投影另行证明关闭分支不改变任命定义。
2. 开启自动继任：决议设置变量；确认卸任样本仍选择冻结的原版最高分非玩家候选，并为另一真实省份记录启用态非玩家 `current_heir`；分别触发死亡、卸任，确认主头衔归对应候选，玩家未获得目标头衔。
3. 再关闭：变量消失；未扰动的控制省份恢复为先前冻结的原版 `current_heir`。
4. 开启禁转：受保护封臣及新加入角色同时出现两个标志；AI 的 `grant_vassal_interaction` 对向玩家上交路径不可发送或不选择。
5. 再关闭：仅本 Mod 所有的标志被清理，同构 AI 路径恢复原版。

每个场景保存：初始/最终 paused frame、角色与 title ID、候选分数、变量/flag、动作 ACK、结果查询、相关日志区间和截图索引。

## L3 工坊包复验

首次上传后从空路径下载新 Workshop item，以 item-ID sidecar 对缓存逐文件验证；再对 fresh cache 重跑 L1 与一组天朝制 death/removal/transfer 核心矩阵。只有内容包、缩略图、描述正文和 fresh-cache 验收均 GREEN 才公开。
