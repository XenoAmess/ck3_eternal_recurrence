# E2-04 a08：第 6 日真实保存与独立 V3 冷载计划

2026-09-29 CST，无屏计划。H2743 当前占用 `ck3-screen`；本页没有 a08 no-launch、CK3、录像、d06 存档或 V3 结果。a07 的同轨录像及原生 trace 已封存，但 [a07 回执](e2-04-a07-live-evidence-20260929.md)没有 d06 保存：战报新增 `knight_maimed_by_enemy(34333,47032)` 后，暂停 d06 列表和 trace 仍为勇武 11、团 61 攻防 raw 96250000/19250000。a08 目标是产生**a08 自己**的 d06 真实保存及复载结果，而非把历史 039→040 接在 a07 后面。

## 已核静态来源和屏幕入口

- a08 的新 d05 冷载候选仍为 `episode01-paired-counter-trace-attempt-010/d05-immutable.ck3`，52,172,645 B，SHA-256 `695F1FDE17457004EB8D060C1F21146C3605374806DABACF6FB5FAB386882885`，配 `ck3-output/interactive-requests-responses/d05-save.json` SHA-256 `6650C0DB79D063E066AB72402735C22FAE9FCB5D458A56CE1C10B9545CD1F3C7`。039 live 与 a07 也从这对字节独立冷载；039 内生成的 `D978…` seed 只属于后续投影链，不得替代冷载源。三次都是独立随机运行。
- 计划中的原生 GUI100 来源是 a04 UI 保存快照 SHA-256 `E6AD4D44435F17B77C6A5BD6554AB812FBF396D9A27370DB7CF9B56D658FDF7D`，需在 a08 新 profile before/postmap/posthold 逐次验证原生 `value="1"` 区块及实际 2560×1440 画面。EXE、DLL、injector 候选分别为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`、`EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7`、`CE8A20C7B25A697058AB69B03629D6B7655BB2935AD147DF1E84895A826BF247`；每个新 run 开始前重新按实际路径、字节哈希和 hello 核验，不能只引用 a07 值。
- 2026-09-29 当次只读查询独立 `xar_promo_toolchain` 最新**正式** GitHub Release 仍为 v0.2.1，仓库 `tools/requirements-promo-toolchain.txt` 记录 wheel SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`。a08 真正开 run 前再查最新正式发布，以选定解释器验证 wheel、`--version` 和相关 `--help`，冻结 ProjectConfig 精确 bytes / 新 RunManifest。此页本身不是 run。
- 屏幕须待 H2743 正式 RELEASE 且 CK3/FFmpeg/OBS 零残留；领取 a08 独占且有常驻 heartbeat 的 `ck3-screen:acquired`。新鲜 Steam“离线模式”原图须有当前像素/窗口挑战并由执行者直接审阅；若冻结依 AGENTS 恢复，不能复用 a07 图。只有随后才可新根 no-launch（精确 d05 save/sidecar/UI/EXE/DLL/injector）、新 pipe、新受管冷载。a08 的 d05 采集与后面的 d06 V3 冷载是**两个** managed CK3 启动，每次重新过新鲜离线、空进程、版本/源配对门；保持各自独立 state/output/pipe 和 append-only receipt。

## a08 d05→d06 单日取材门

1. d05 暂停原生 frame 必须回读 actor29829、date_raw53146344、War4、Army18、Combat16777218、province2633 和匹配的 wrapper/native revision 域；GUI100 原图确认战斗窗双方兵数、优势、MAA、11/13 人骑士行可读，并取 d05 双方名单。录制前返回战斗窗再拍独立最终入录原图。若任一项 RED，零 recorder/零日期并受管清场。
2. 一次新工作目录的 600s raw 与 `d05-before` 同帧 mark 就绪后，`remaining_live_step.py observe`/`advance` 只用 a08 的源绑定和**新的**正数 sequence token；helper 现有 `advance` 只在 `ck3_execute_step` **之前**调用一次 `ck3_save_checkpoint`。该保存是 d05，不是所需 d06。`advance` 最多一次，超时或不明响应不得重发；原生 trace/日界 `53146344→53146368`、post snapshot、mark 与实际画面全部保全。
3. 只以 a08 新 trace 判断事件分支。若没有同 token/CombatID 中 `knight_maimed_by_enemy` 且 left34333/right47032，或 34333/团61/War4 身份不闭合，则 E2-04 指定致残结果 RED；保全本次实际分支、录像及回执，停止数字口播，不重置 RNG 或重复日期动作寻找想要结果。若数据仍可安全保存，可把实际 d06 存档仅作独立研究件，绝不追认 E2-04 目标。若受管窗口/lease/录制不允许后存档，安全收尾并标 d06 保存 RED。

## 现有 helper 的最小缺口

`remaining_live_step.py` 只有 `observe`、`advance`、`finish`；`advance()` 在原生前态 `ck3_save_checkpoint(expected_revision)`，然后 begin/one-day/trace-finish/post-snapshot，**没有**受管后态保存模式。`capture_session.py` 已能用真实保存回执配对外置 `.ck3` 冷载：`checkpoint_source` 比对 save bytes/SHA、保存日期/actor、pure-vanilla lifecycle 与 exact-build hello；无需改其合同。最小新增是一个 opt-in、单用途、经独立测试的 `postframe-save` operator（可作为 `remaining_live_step.py save-postframe` 或独立脚本），默认旧流程不变：

1. 读 `e2-04-d05-advance.json`、唯一 `advance-intent`、one-day/trace-finish/post-snapshot 原件并重新哈希；要求同一 a08 live root/source/token，`ONE_DAY_ADVANCED_UNREVIEWED`、paused `53146368`、actor29829、War4、Army18、CombatID16777218 仍可同帧证明。先取一个新只读 snapshot，严格比较当前 revision/native_revision/snapshot_id，防止过期响应和其他游戏操作。缺项即停止，**不**发保存请求。
2. 原生保存目标固定为隔离 profile 的 `save games/xar_checkpoint.ck3`，第二次保存可能覆盖本次 d05 pre-save。先将 pre-save 原件与其 checkpoint receipt 逐字节核验，create-exclusive 复制到 a08 外置 `d05-preserved-before-post-save.ck3`，双读 SHA 与 copy SHA 一致并写保全回执；还应冻结 profile 中可能被驱动更新的 `autosave.ck3`、`last_save.ck3`、`xar_episode_seed.ck3` 等实际存在文件的 identity/mtime 清单，不假设每个文件一定存在。任何源不符或目标已占用都 RED。
3. 创建唯一 `post-save-intent.json`（source/advance/post snapshot/已保存 pre-save SHA/expected revision/token），再**只一次**通过现有 `pursuit_live_step.call` 发 `ck3_save_checkpoint(expected_revision=<新 d06 revision>)`。响应必须 `CALL_COMPLETED`、accepted/saved、`checkpoint.date_raw=53146368`、actor29829、exact build/lifecycle、固定隔离路径；保存可能增加 revision，故立即新只读 snapshot 重新核 date/paused/actor/War/Army/Combat，不能沿用旧 revision 作 V3 同帧证明。超时只检查同名 request/response 和实际文件，不自动重发。
4. 直接按响应 size/SHA 校验落盘 `xar_checkpoint.ck3`，create-exclusive 复制到新的 `d06-immutable.ck3`，复制前后重读源 SHA 与目标 SHA 一致；写 `d06-preservation.json` 记录源 response/新 save 的 exact bytes/date/actor/源 DLL hello、前后 profile inventory。原始 response 路径作为真实 sidecar 供下一 run `--checkpoint-receipt`，也可额外复制同字节副本但不可编辑或伪造。保存失败、文件不符或 copy 碰撞均 RED，不能把 d06 post snapshot 当保存回执。

最小离线测试只需构造小型临时保存文件和模拟调用器，覆盖：成功保全 d05→只一次保存 d06→双哈希复制；原生日期不对、source/token/revision 不对、已经存在 intent/目标文件、前态 SHA 变化、超时但已有 pending request、save response 只 ACK 未落盘、保存后 revision/战斗身份变化等负例均零额外提交或 fail closed。禁止以机械镜像测试替代这些失配边界。新 helper review/测试/CI GREEN 后才用于 a08 live；旧 a07 原件不改。

## d06 新档的独立复载与口播

a08 d05 会话封存 raw/全 PTS、finish/CK3 清场后，从刚保存的 `d06-immutable.ck3` 与真实 response **另开** a08-v3 managed run；在新鲜离线和新 no-launch 下冷载。首先对保存字节做只读 Rakaly 解码，选唯一 CharacterID34333 块，读取 `alive_data` / trait（`one_legged`、`disfigured`、`one_eyed`、`maimed`、`wounded_*` 等）与 regiment61 的身份；解析失败或歧义即 UNKNOWN。此离线解析只证明存档状态。

复载后的 paused same-frame 从新 snapshot 取实际两侧 ArmyID、CombatID 和 province/entry 参数，调用 exact-build `ck3_query_combat_simulation_inputs_v3`（显式 `target_province_id`、`attacker_entry_province_id`、两侧 ArmyID 列表、`expected_revision`），保存原始请求/响应和 strict normalization；不得借历史 040 的 request 参数或数值。逐对象读 34333 的有效勇武、团61 的攻防/伤亡、仍属 Army18 的 back-reference，并与 a08 d05/d06 保存解析绑定。若 combat 消失、v3 `unavailable`、人物/团变更、致残随机 trait 不是历史 039 的断腿+重伤，或数值不是 11→7，则据实记实际分支，目标“11→7 同源次帧”保持 RED；不可因为历史 039 与 a08 冷载源相同而拼接 040 镜头。

V3 重新冷载应使用**新**录像/RunManifest/marks（若需要实拍后态）或只读原生验证 run；不能称与 a08 d05 raw 在同一连续录像。任何后态计算卡/旁白都精确标注 a08 第一次 save 和第二次 coldload 的两个来源节点。最终原片仍须独立 PTS、clean span、CK3 adapter bundle、人工 1× 与精确 SHA 签核；机器报告不等于成片或交付。

排程暂按两次本机冷启各 15–20 分钟、第一次 GUI/同帧/受管保存及 600s raw 约 20–30 分钟、两次清场与新鲜离线/配对约 10–20 分钟估算，独占屏幕约 **60–90 分钟**；这不是完成承诺。若服务窗口不足覆盖当前受管动作和清场，停在安全边界并保全 partial，不为赶 V3 放宽日期、lease、recorder 或保存门。a08 未获屏幕/运行前不得在镜头账写“后态已拍”。
