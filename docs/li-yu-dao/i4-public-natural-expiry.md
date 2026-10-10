# I4 既有修派冷却的公开自然时间观察

2026-10-10 新增独立案例 `i4-existing-school-cooldown`。源码准备范围为
`PARTIAL_EXISTING_COOLDOWN_OBSERVATION`：观察原0240无宗主分支中**既已存在**的
`lyd_school_cooldown` 自然消失。源码与新增离线合同检查就绪后也只记 `STATIC_READY`；
实际准备、启动、时间推进、保存、正常关闭及后续冷重载各自需要真实回执。

它不依赖正在调查的 I3b B4 工厂缓存问题。正式 I3b、B5、新宗主政治保护冷重载、C3、
I4 完整矩阵仍保持原未完成状态。此案例不执行修派选择，不改变 C2 冷却，不删除宗主，
不直接设置日期或变量，不将合成夹具当成实机成功。

## 已知输入及其限制

默认输入为原0240 checkpoint：91,669,783 bytes，SHA-256
`1d98f0d2482c02477f460127044690b1df128e806b2ffbfab399e945e3551a1d`。
其只读原始观察为426,067 bytes、SHA-256
`e08d6f60d54085594297d227dc0213343fd86e372ff4c6cea558e847f5064323` 的
`BASELINE-0240.json`，schema `lyd.i3b0240.cached-baseline.v1`。
原观察记录 actor31254、Faith107、main Rite169、HoR31254、HoF空值4294967295，
date_raw53144712、暂停、无事件及待处理交互。

修派 flag 的实际保存形状为：

```json
{"flag":"lyd_school_cooldown","tick":"349","data":[]}
```

`tick349` 只作为原始值保存。当前没有绝对到期日或“剩余349天”的已证合同；
`remaining_days`、`expiry_date` 始终为NULL。不能声称本案例覆盖了新选择后完整365日周期。
如以后需要完整周期，应从一次真实新修派选择建立独立起点，另行验收。

原 seed 与历史 metadata 只提供起点来源。游戏加载后，在同一个实际暂停日期先执行一次
**新 initial SAVE**，用既有 lossless reader 读取该新 body 一次，确认 flag实际存在、角色存活且有地、
成员flag、实际Rite→Faith、无宗主及主Rite绑定。初始决议必须实际不可执行。
初始flag已消失、身份变化或决议已启用都拒绝本案例信用。

## 公开接口与运行步骤

通过既有 `tools/ck3_mod_acceptance.py` 的 `prepare → allocate → preflight → run → verify`。
adapter不选择机器、host、DLL或解释器；共同runtime manifest提供这些实际参数。
只挂载官方production product，无fixture/诊断overlay。显卡缓存复用按既有合同独立判断，
不从其他挂载树推断兼容。

准备输入的闭合形状为：

```json
{
  "state_dir": "<新的外置state路径>",
  "saved_campaign": {
    "save": "<仍可读取的原0240路径>",
    "bytes": 91669783,
    "sha256": "1d98f0d2482c02477f460127044690b1df128e806b2ffbfab399e945e3551a1d",
    "player_id": 31254,
    "date_raw": 53144712
  },
  "case_inputs": {
    "product_dir": "<正式production staging>",
    "product_inventory": {"path":"<实际inventory.json>","bytes":null,"sha256":null},
    "plain_configuration": {
      "pdx_settings.txt": {"path":"<原件>","bytes":null,"sha256":null},
      "tutorial.txt": {"path":"<原件>","bytes":null,"sha256":null},
      "presets.txt": {"path":"<原件>","bytes":null,"sha256":null},
      "player/game_rules/presets.txt": {"path":"<原件>","bytes":null,"sha256":null}
    },
    "origin_metadata": {
      "path":"<BASELINE-0240.json实际路径>",
      "bytes":426067,
      "sha256":"e08d6f60d54085594297d227dc0213343fd86e372ff4c6cea558e847f5064323"
    }
  }
}
```

上例的四个配置键以 `ck3_mod_acceptance_prepare.CONFIG_NAMES` 为准；任何缺失或额外键均拒绝。
所有NULL需ROOT填入真实ref，模板本身不能运行。product inventory沿现有合同包含实际
`source_head` 和完整 `files[{path,bytes,sha256}]`。不猜未来运行ID、PID、session或revision。

```text
<Python> -B -X utf8 tools/ck3_mod_acceptance.py prepare --runtime <actual-runtime.local.json> --products tools/ck3_mod_acceptance_products.json --product li-yu-dao --case i4-existing-school-cooldown --case-inputs <actual-input.json> --prepare-output <new-prepared-dir>
<Python> -B -X utf8 tools/ck3_mod_acceptance.py plan --runtime <actual-runtime.local.json> --products tools/ck3_mod_acceptance_products.json --product li-yu-dao --case i4-existing-school-cooldown --prepared-case <prepared-case.json>
```

ROOT沿公共入口取得新offline/screen lease并分配一次实际run，使用其真实run-context执行
preflight/run/verify。不能在本案例中复用旧现场或延长旧hold。

实际业务顺序：

1. 实际载入原seed并保留进程句柄；确认暂停、event-free、actor/date一致。
2. 公开打开决议并选择 `lyd_change_school_decision` 的详情，**不点击确认**。
   Source09先保留原生选择ACK，再独立回读实际详情。原ACK的
   `selected_after_verified=false` 可以保持原值；只有官方最终
   `postcondition_verified=true`、`status=verified_selected_detail`、
   `verification_pending=false`，且 `later_actual_observation` 与随后独立模型均证明
   同一目标/actor/暂停frame，才接受选中完成。未完成或错误目标仍拒绝，不重放选择。
3. keyed模型确认唯一目标/实际actor及frame；窗口树读取真实确认按钮 `enabled=false`。
   模型 `available=true` 仅表示找到正确对象，不证明决议可执行。
4. 新initial SAVE/read一次；以已经读出的同一bytes写入独立
   `initial-school-cooldown-checkpoint.ck3`，保留精确descriptor。
   公开SAVE使用固定路径，随后final SAVE不能覆盖这个独立初始原件。
5. 每次只提交 `CaseClient.advance_day(days=1)`：既有host按speed1自然resume/poll/pause，
   不使用日期setter。每次真实elapsed为24≤hours<48，原生date delta与之精确相等；
   同PID/gen/actor、暂停、无事件，每次日期必须从上一次连续推进。
6. 每次暂停后重新读取keyed模型→完整详情树→keyed模型。确认按钮从false首次变true即停止推进。
   窗口树按原生 `ConfirmReceiver` 的 `cost` / `back` /
   `cram_study_start_tutorial_highlight` 三个命名锚点和footer7/regular3/custom2布局推导，
   可见确认leaf必须唯一；缺失、截断、歧义均拒绝，不解释为disabled。
7. distinct final SAVE/read一次，确认flag缺失、实际相同Faith/Rite及无宗主、成员/存活/有地保持；
   实际enabled决议同时证明其他脚本资格。记录自然elapsed hours及hours/24，不能预测到期日。
8. 由现有共享normal-close收尾；原句柄OS0、native0、lease/CAS等仍按公共合同。
   新checkpoint冷启动重载属于后续独立实机步骤，此案例结果保持`cold_reload=NULL`。

GUI树当前不返回frame身份字段；现有公共实现以两个已绑定模型将树读取包在同一暂停
PID/connection/actor/date内。它不能证明树与模型逐字段拥有同一个`native_revision`，
不得把该包夹证据写成树自身的原生revision绑定。

上限同时约束366个单日区间及**累计实际自然时长≤366×24小时**；任何事件、actor变更、
超时、日期不连续或到上限仍未启用都停止并保留RED。不处理/跳过随机事件，不重放动作。
新case固定hold7200秒、总timeout8400秒、Quit reserve90秒；这不是完成365日所需耗时保证。

## 静态验证与实机边界

本次新增专项检查17项实际通过，五个来源字节在测试前后保持一致；仅授`STATIC_READY`。
[原始小回执及首次fixture错误](acceptance/2026-10-10-i4-natural-source-only/INDEX.json)均保留。
首次错误是合成parser样本缺少必要分节换行，修正样本后通过，没有修改生产parser。

随后只读接口审阅发现原ACK待验证时会被误拒，现已采用官方later实际证明；新增3项
专项检查实际通过，未重跑原17项。[修正与原审阅回执](acceptance/2026-10-10-i4-natural-source-only/selected-detail-fix/INDEX.actual.json)
单独保存，当前仍无实机信用。

新增的纯Python测试只验新guard：缺失/错误flag形状、tick不可解释、GUI缺失或歧义、
伪日期跳跃、事件/连接变化、累计实际时间上限、两次真实保存的预期parser形状及中间日期缺口。
parser小样本不模拟flag自然到期，不产生实机或完整I4信用。

`open_kaishek`：本步骤无现成CK3 1.20 saved-flag自然tick、原生GUI enabled、
speed1自然推进profile/fixture，沿现有 `mod_li_yu_dao/tools/run_acceptance.py` 的
`not-applicable` 边界，不为形式重复运行1.19默认fixture。当前共同runtime目标为
CK3 1.20.0.4/build25734779、EXE SHA
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；
实机仍需公共入口按选定manifest精确绑定，源码说明不替代新回执。

大seed、两个新checkpoint与runtime输出均留Git外。开始、写入前及闭场按
[通用存储策略](../storage-retention-policy.md)和版本化参数检查/登记预算与复核期限；
既有小型观察可复用，原件过期回收时如实标记不可读，不造同名替代。
