# R202：中途保存、遭遇战与正常续行来源

`machine_id: desktop-3fevhd2-1c74096080`；本候选核对时间 `2026-10-17T17:42:23.492804+00:00`。实际完整run为 `desktop-3fevhd2-1c74096080--vanilla--R0202`，source/native source均 `26449eb2676b4ccb71cb818fb0cc398b0a5fd1e6`、a34b；PID25928/create134367302122744909/gen1/episode `native-31254-ea56d104695f`，actor31254。当前主线19024/a35构建不追认为本场运行源。

## 两段推进与县条件

第一actor闭合23日，到date53148768、Army18在2633并达到本阶段stop_target2633。自动保存回执SHA `b1ab6d63c04375200740a321c97939317c0ec14687c13e595a98390513317685`，当时checkpoint74,787,359B/SHA `a48d1b61d552210414f0dddfd68ef26d6b9a8ca9311f5b66ea60dc79aa54ce3c`。这里游戏继续运行，不能将这次保存单独称为正常exit后的S0；该路径之后由最终保存覆盖，不制造旧同名替代文件。

独立17:18:01.871037Z snapshot为public82/native81、paused/date53148768、仍moving向2629，剩余route `[2627,2626,8753,2629]`。同帧preview的first remaining edge是2627，不是远终点2629：P返回false，receiver34232/actor31254，relation返回false、full_war_id=-1、direct_war_gate=false、unknown_or_inputs=true；最终county condition=false、actual_loss_observed=false。未知OR不能填成完整根因，来源/兵数/物理扣兵均不从preview推断。

后继只换新case/prefix，原S0、source/date、capacity和identity保持同一绑定，同PID继续。actor在guard前只结算26个完整循环、末53148840；独立第27日原件在17:26:36.952026Z读到53148864/paused、Army18仍2633、in_combat=true、controllable=true、retreating=false。敌Army32/owner33732同在2633且combat。因战斗停止不是抵达home2629；没有R06 ADD样本或战斗胜负结论。

## 最终正常闭场与恢复决定

17:26:47.715824Z最终Save绑定 **74,351,284B**、SHA `5b629e2b980f6ff53781f2b4c65718c8a2ef4aa64c58f57958a961585835755f`、date53148864。bootstrap于17:32:31Z结束，elapsed1818.801秒、process_exit、process_exit_code0及CK3 exit0，tree_gone/cleanup_proven=true、SDK线程结束；Root报告outer0。17:33:02Z helper exit0、screen taskdone6267/resources[]，这次是正常闭场，不借R201 timeout作资格。

R203可从这份正常闭场的**2633战斗中**checkpoint独立冷载、继续或拍摄；不能描述已返home2629，也不预填R203启动/胜负。[机器可读决定](evidence/episode04-r202-movement-combat-12004/continuation-decision.json)保留该区分。recorder为NOT_STARTED；研究9/14、业务6/11、合格动态0/11、ABC0/3不涨，clean/1×/人工签核没有新增。

[精确小原件与来源索引](evidence/episode04-r202-movement-combat-12004/source-index.json)、[JSON pointer字面投影](evidence/episode04-r202-movement-combat-12004/literal-observations.json)可供agent恢复与视频核稿。七份小原件原字节入ZIP，完整snapshot/preview仅pin和局部投影，不冒充全量consumer重放；绝对C/D路径仅是来源机器的历史位置，跨机不执行原producer。大save、Driver、EXE与媒体读取/重hash均0。
