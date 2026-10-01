# Episode02 R0148：本次骑士击杀六项研究关闭

2026-10-02（北京时间）。本期受控原版案例的六项研究已关闭，**6/6，100%**。这是 `knight-killed-case-closure-contract-2026-10-01.md` 声明的有限案例，不代表 CK3 全局状态空间已研究完，也不代表视频已完成。

根语义终件为 [R0148-six-gap-finite-case-semantic-closure-a01.json](C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-12-identifier-append-safe/R0148-six-gap-finite-case-semantic-closure-a01.json)，172344 bytes，SHA-256 `17751A015324D4F995D0F5B9668F9EFE5B70784230A9C9F62CD6622E764E6091`。463 个精确输入文件均二次校验；原报告的全局 false、未发布字段和失败 attempt 保持原样。根结论另行记录，没有重写旧报告。

## 同轮身份与采集边界

- run：`desktop-3fevhd2-1c74096080--vanilla--R0148`；native session：`native-29829-ecf54ba37d29`，connection 1 / hello 0 / PID 13108。
- 冻结源码：`C:/w/e2cap1001i`，commit `431461d6841604ebd19e65670661ca2a732dbff8`；DLL SHA-256 `0189FA3C83B07379ED75467988C4394D02D457BAAA01DBB2ED646ADDE2730857`。
- CK3 1.19.0.6 / Steam build 23530548；EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- actor 29829 / War 4 / PublicUnit 18 / full Combat 16777218；victim 33437 / killer 34120 / event 11。
- 1066.12.29 → 1066.12.30，raw date 53146848 → 53146872；daily token `458466972829638162`，monitor token `458466972829656045`。
- 184 scoped records、7 phase edges、13 monitor records 均 failure flags 0，未截断，实际卸载完成；四份原版保存永久保留。
- 展示窗口在观察 BEGIN 前关闭；FINISH/卸载后才打开次日人物和战斗窗。未禁用原版通知。两段 UI 前后保存的 RNG 净变化均为 0；全天保存的 RNG counter 变化为 949。
- 采集已实际结束、相关进程停止、桌面恢复 1024×768，根已审阅新的 Steam 离线原图，屏幕独占已释放。

## 六项实际结论

| 要求 | 状态 | 原件和结论 |
| --- | --- | --- |
| 骑士次日角色界面 | closed | 同轮原图显示 victim 33437：31岁、存活/勇武4 → 骷髅死亡标记/勇武2；killer 34120 保持27岁/勇武7，威望301 → 451。身份和日期另由原生读数核对。 |
| 名单变化 | closed | 两侧完整 tooltip：左11 → 10，33437 移除；右19 → 19，34120 保留。完整原生 active entries 为69 → 68，Regiment65 在提交中移除。两个分母不可混用。 |
| 完整战斗窗 | closed | 两日实际原图均包含双方指挥官、中心和完整底部构成，原生 GUI owner、完整 Combat ID、paused/date 和几何读回绑定。 |
| 骑士选择器 | closed | 原 materializer 19项、逐候选原谓词返回、短路、尾部交换和最终14项完整；原 index 8 返回34120，counter 1117324859 → 1117324860 / salt 0。draw 1400813912 是精确算法复算值，不冒充直接发布的 draw 字段。 |
| 唯一相关死亡路径 | closed | 本受控窗口内33437 的 request / enqueue / commit 各1次，直接六参数在同 enter/return 与线程11732读取；marker false → true、死亡日期/原因/击杀者与保存一致。casualties seq177–180 先于 deferred commit seq181–182，下一暂停 seq183。唯一性只指本次相关路径。 |
| 完整可变状态链 | closed | 下列13域使用明确的实际写、操作前后、完整未写分支及保存端点分辨率关闭；不能把端点相等自动升级为全天无写。 |

原图、存档、raw trace、MCP 请求/返回和每项精确路径/SHA 均列于根终件。`before-ui-root-review.json` 和 `after-ui-root-review.json` 仍保留采集当时的“后续机制审核待完成”历史字段；当前结论由新的终件追加。

## 13域的分辨率与关键限制

| 域 | 证据分辨率及结果 |
| --- | --- |
| skills | 空成长 entry56 / followup57 未 dispatch 与完整 writer 库存证明本事件无成长写；184边界原始三项角色值及四份保存基础六项保持完整。有效战斗属性另列。 |
| trait_set | 完整实际特质顺序、全部边界和四份保存；本事件完整实际树排除特质写。 |
| trait_tracks | 301个当前 loaded 定义完成 stored-order 映射；33437 logistician / 34120 rough_terrain_expert 均为真实一项 `[0]`，不是空数组。实际成长支路无写。非零保存比例仍 UNKNOWN。 |
| death | 原直接 manager/victim/reason/date/killer/artifact 六参、队列与唯一相关 commit、marker 和保存一致。artifact 是非空指针、原读 ID -1；不补造正 artifact 保存字段。 |
| prestige | 原 leaf52 的目标34120；currency 与 accumulated 均 +15000000，原 execute/save 写锚证明字段语义。 |
| regiment/link | 同轮原名单、完整原生 entries、实际移除与四份保存；六组 full-generation army/unit/owner 双向映射一致，未把 commander 当 owner。 |
| entries/current/soft/stats/owner-hard | 7 phase / 12 scoped 完整快照与两次 casualty 前后、6真实owner对账；loss minus soft 与 owner-hard 差值一致。初始41项有效stats刷新差异完整保留，其原 callee 未直接观察，属于本事件写区间之外。 |
| battle ledger | 原 node/context 的 type3/side1 新 row：victim33437 / killer34120；完整前后 ledger 与保存一致。 |
| slain_side_knights | 原 owner/key5786 / typed `[4,33437]` / expiry -1、完整列表从无到一项；保存 `duration=[1]` 是向量数量，不是一天TTL。 |
| killer_kills | 同一原 commit87 的完整 kills vector 从 `[]` → `[33437]`；实际 setter/append 源锚及保存一致。 |
| signature_weapon | 原 writer3 对34120 请求并写入 axe；nearest producer 是实际 `death_management.1202`。四次独立稳定 named `dead_character` 真读33437；通知receiver38574保持独立。原脚本 dead_character → killer → set_signature_weapon_effect 与原写目标对应，不推测具体随机分支。 |
| house_relation | 原 house1105/1053、type0/default_house_relation guard AL false；完整树/writer库存与相关DB保存端点支持本支路 no-write。具体哪个子条件失败仍 UNKNOWN。 |
| accolade/liege | 原 inline59/83/84 无 child dispatch 且 optional 真读 null；相关雇主/liege29829/32725、Accolade125/128 四次完整记录一致。本事件支路 no-write。全局146/323实际10个叶差完整保留，不能称全表不变。 |

## 独立审阅终件

- strict causal：78检查通过；SHA `E3009571C5C1393755C28AC289513B28CF9F512F626A9A55EAFE8246D9216787`。
- strict variable monitor：46检查通过；SHA `9628BF75FA12AA3E16A621FACBA091A09EEAAA2DF079086839FA5A983F821B5B`。
- additive direct/named：实际 `--require-closed` exit0；SHA `BC4B6950C2BFC5D6E89B3561AFCB5510817C78433D7B6FF0C447DCA4818ECD8C`。
- finite entry 结论：SHA `DA3DDD1CC7C746E134D1BF992DB107AB64A7A8C7261823D3446E2E2D113D4757`；完整封存 SHA `80BEDE1705EF1DB064BFD8C883859C383B3DCBB013B70DEED4519D9C13ED98AF`。
- finite growth/accolade：actual normal / `-O` 均 exit0，去 mode/output metadata 后语义相同；双模式 receipt SHA `4FCEB6A29950E7E968A943743E051C124840040B556D7898CA1323AB6CA2C4E8`。

三个外置 schema/入口 RED 已永久保留：包相对导入、RPM 精确 Unix 字符串合同、main C05 未发布 post_snapshot。外置 helper 修正了合同解释，未修改原 native 数据、门限或冻结源码。main post_snapshot 继续标未发布，没有回填。

## 视频接续

六项前置研究完成后，允许使用这些成果优化本期视频。先补一轮 D11 增援前后完整战斗窗与相对军力 tooltip 同帧画面；旧 R0138 只证明上部数字/宽度，底部裁切缺口不能靠换标签关闭。再更新骑士解释、次日人物/名单对照和完整状态链，保持战争系列棕黄配色，建立新的配置快照、run 和不可变过程素材。

现有 a07 仍为历史中间版本，未因此获得新证据绑定或人工1×签核。新成片需实际 render、媒体检查与 review package；机器 PASS 不等于人工完整观看。独立研究分支 `codex/war-e2-mechanism-closure-20261001` 与视频分支 `codex/war-series-brown-gold-20261001` 继续保持；本轮没有 master 拉取、合入或推送。
