# 宗主门槛的否定合取与全信仰提名修复

状态：**源码验证通过，修正版尚未实机运行，0.1.2未上传。** 原因与实际失败见[实机R0076](LIVE-R0076.md)：道学有258名合格学者、缺少代表，封案却放行；随后130票不足2/3，宗主实施仍关闭。

## 最终改动

生成器 `mod_li_yu_dao/tools/gen_institution.py` 中九处直接复合NOT改为显式NAND：五处是名册/成员身份及代表门槛，四处是实施后置检查与失败分类。Jomini的NOT/NOR表达否定析取；要在任一必要条件失效时拒绝，需要NAND。原离线测试把NOT当成NAND，故未发现缺代表却有学者时的错误放行。

本机游戏随附 `jomini/common/trigger_localization/00_logic_triggers.txt` 将not与nand分别映射AND和OR提示，`jomini/localization/jomini/script_system/script_system_l_english.yml` 分别为“All of these”和“At least one of these”；原版宗教trigger另有显式NAND用例。该来源加实际失败支持本次修复，没有声称另跑过引擎真值表。

代表提名另加原版 `use_diplomatic_range = no`，使制度覆盖同信仰各派而不额外要求地理距离。原版 `_character_interactions.info` 规定默认检查距离，宗教交互已有相同no用例。actor、recipient、捕获名册、阶段及提名接受效果全部保留。R0076查询没有返回逐项失败原因，因此本修复不追认该次shown=false已经完整归因。

11份生成结果只有triggers、commit effects和nomination interaction三份改变，另八份字节不变。before/after AST审阅确认业务差异恰为九个逻辑键与一个范围声明，未改投票阈值、AI权重、名册或政治头衔保护。

## 验证与限制

两个测试解释器都分开处理NOT/NOR与NAND。回归消费实际生成AST，检查两项布尔值的完整真值表；258名学者、代表缺失时决议is_valid、effect及seal helper三层均拒绝；分别改变owner、serial、faith、rite、在世/玩家/选举资格时拒绝；全信仰提名仍保留目标资格和原接受effect。历史AST冻结值通过精确条件体的有限逆投影保留，另两份输出字节指纹只在精确差异审阅后更新。

一次必要检查实际通过：tooltip27项、candidate28项、preview55用例/19变异、detached131用例/24变异，生成一致性、静态校验及83文件可复现构建均exit0。detached首轮新增变异未被原反例检出，原exit1保留；补充未进入捕获list的新Faith礼仪/成员及陈旧serial反例后，仅该变化模块重测通过，未降低断言。

小型验证根 `C:/workspace/ck3_lyd_runtime_20261004/lyd-i3b-not-nand-fix-20261013-039`，总131436 B，未启动游戏、SDK或原生构建。`SOURCE-CHECK.actual.json` 18275 B / SHA-256 `39de2731e0782d3e9896cba4ee1d240fce56144ea9c83959e3ec950b6d9584f0` 保留准确argv、cwd、时间、exit及stdout/stderr pins；`INDEX.json` 11359 B / `20afd9b6dfab4a6d6db006ff62c92953b7de1cbf33f24ddc391fc5d8fb77fb12`。失败stderr499 B / `169055c75e0fd3e1fbd87ab3f148ae00d5f8cde8df75bfed6abc93184faae790`。旧A38已经闭账，未再写入。

后继实机须重新冻结并加载修正版，先验证缺代表时封案确实禁用，再完成实际代表提名、各派2/3与签署、所有玩家同意、保存前后政治保护及宗主结果。R0076只能保留为旧实现的失败与部分覆盖，不能向修正版授予成功信用。

## e57563fb CI实际结果（2026-10-13 07:00 CST补记）

提交 `e57563fb24fdbd735be04616fc9b215da1c9cb51` 的 [LYD专项](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38318913881)与[线性历史](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38318914417)均SUCCESS；[全仓检查](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38318914043)为FAILURE，全部attempt1，没有重跑。失败位于shared CK3 acceptance的normal-close/reviewer组：两项等待时间、一项跨scene迟到复核拒绝和一项默认人工退出资格断言，共四项。公共退出实现与测试夹具的归因另行核实，不能把此次全仓CI写成通过或改写为LYD业务失败。CLA当前没有状态报告，不记作失败。

外置 `ci-e57563fb-001/INDEX.json` 7745 B / SHA-256 `50fb4188a70ccd65816d06e0ab57522cfe42076f20da0bde3680ec40e0b384c5`；17份小原件共162806 B，保留原run/check/status/jobs及8192 B失败日志片段。已停止查询该终态提交。
