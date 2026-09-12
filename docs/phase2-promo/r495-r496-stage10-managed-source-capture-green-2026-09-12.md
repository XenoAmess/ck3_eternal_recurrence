# R495/R496 Stage 10 受管来源捕获 GREEN（2026-09-12）

## 结论

R495 只执行前台预热并在 R496 启动前完成受管终止。R496 是唯一 gameplay 实例；它从 R494 留下的受管 autosave 恢复，原生切换到候选玩家经理 `27181`，在同一暂停帧复核 campaign root，然后通过 MCP 原生保存新来源。切换和保存前后均为 `date_raw=53155680`，`game_time_advanced=false`。

这一工作包关闭了“替代玩家经理来源是否可真实保存并重新准入”的前置项。它没有执行 Stage 10 `.120`，所以 P1 仍为 `8/9`，P2 最终宣传视频继续 `LOCKED`。

## 实机绑定

- 来源 activation：`520740503829833DFF1B13B429928AE01FD629986BA74CB125524EDA04A9B4BD`
- target profile：`F868BA3D8C8AD39FBE2BC2876EC28BC4D2704E0713A68ED1D8E58AB711882ABB`
- no-launch validation：`131D84B368E5D043FDC8576E159BC0E758674C46DABA902AF50C275999DB150B`
- R496 live source evidence：`1C511EC6E9383407E0067CC6E2AAF2C6BD24403A69D0AABFB07B49DA6E87ED87`
- 新 checkpoint：`65,244,992` bytes，SHA-256 `50B713F2B479E92386302A45B5790A327ABC7862F55CF0E000EC0943DB7AC7E4`
- 离线 topology：`335E566D2F7F7148733C50997A5DB4EA0296A44FE50AD4D32D0F64BA7BAD7B32`
- 受管 cleanup：`02BF37E8FAC4D1B0B019D4B647725E5A70028F407D267361AED020F2F4958E6A`

新 checkpoint 的 live 与 offline 证据一致：唯一 played/current player 为 `27181`，直属领主为 `36354`，主头衔 `k_henan`、tier `4`、`celestial_government`，`zg361_on` 已启用。topology 中有七名直属有地封臣；这与 B1 case 的五名 exact subject 是两个不同计数。

## 当前 B1 输入

通用 character-scope 检查器对新 checkpoint 生成 `ck3_character_scope_offline_v1`：

- 报告 SHA-256：`E5E976143A2CCAC3A485ABAE27C14730CB4E263884AB1FF4C1219778814C97D1`
- manager cycle/case：`5/5`
- `zg361_b1_subjects` 与 `zg361_b1_processing_subjects` 均为同一五人：`30159, 28288, 26859, 29247, 45027`
- 五人都满足 `owner=27181 / subject=self / cycle=5 / case=5 / state=7 / active=1 / roster=1`

scheduled-event 报告 SHA-256 为 `4F031946C8C2432D7F2B0264DC997835F3EE71A6DDCA677B354C56946CC97753`。它只命中上述经理域中的五个 `zg361b1.122`，全部位于 checkpoint 后 30 天。

## v7 来源收据

旧 `zg361_stage10_player_publication_source_v6` 固定绑定 R492 的旧玩家、旧 checkpoint、三段历史 RED、调试日志以及 `.102 +1d` 尾链，不能诚实描述新来源。因此 operator 保留 v6 兼容，并新增 `zg361_stage10_player_publication_source_v7`。

v7 只接纳当前来源事实：

1. checkpoint 与当前产品树的 exact hash；
2. 单玩家 offline topology 与唯一候选 `27181 -> 36354`；
3. R496 的 exact-build、零时间推进、MCP 原生保存及受管 cleanup GREEN；
4. 当前五人 exact B1 roster/processing；
5. 五个 `.122 +30d` 队列和 120 日既有动作上限。

真实 v7 receipt SHA-256 为 `B687CC041D25537F19CA02FF45E8B6E084A8B76DEF60660AF23E5FA7E8DBFFBA`，已通过 operator 的 no-launch validator。聚焦 operator 测试在 normal/optimized 下各 `4/4` GREEN；测试同时证明任一 `.122` 日数由 30 改为 31 都会拒绝准入。`py_compile` 与 `git diff --check` GREEN。

## 资源与门禁

R496 cleanup 后 CK3、injector、受管 worker、Operator MCP 与监听端口均为零。当前轮次 R496 和旧轮次 R495 均已终止。本包未修改 mod 产品树、DLL、游戏文件、加载顺序或启动配置，因此没有新建 CK3 轮次。

下一步是只使用该 v7 来源执行一次 120 游戏日绝对上限的 Stage 10 product attempt。出现新的原版场景 RED 或产品 RED 时保留现场并停止，不原位 retry，不延长为永久长跑。
