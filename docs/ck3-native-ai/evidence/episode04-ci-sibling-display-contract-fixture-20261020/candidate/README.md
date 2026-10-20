# 精确0f548 CI sibling-import fixture修复候选

machine_id: `desktop-3fevhd2-1c74096080`。观察时间2026-10-20T18:20:04Z。唯一仓库修改目标为`ck3_autonomous_player/tests/unit/test_siege_research_continuation_v2.py`，原source为`0f548b643782c479bc3eebd3ffef14d710c13d06`；D/W/Git均未修改。

实际CI run39469117380/job118788198935 step55失败于`decision_observation_feed.py:11`的`decision_display_contract_v1` sibling导入，原记录仍在相邻已闭`ci-0f548-a01`。本候选先按真实路径加载contract，并在`mock.patch.dict(sys.modules, ...)`上下文中临时注册该真实模块，再执行原feed/overlay加载循环。dataclass和canonical sibling import都能取得真实模块；退出时恢复原module状态。没有替换formatter或typed projection，全部原assertion AST不变。

`mirror/`中5个实际文件承担真实资源路径：candidate test、原fixture及三个原tools模块。原输入合132983B，改后镜像133587B。candidate的`__file__`指向确实存在的镜像测试文件；`parents[3]`准确定位镜像tools，fixture也确实在镜像tests/fixtures。W sparse中这些测试文件未materialize，未把虚构W文件当执行来源。

focused命令为`python -B -X utf8 prepare_and_check.py run`。原Popen12524实际wait0，Python3.14。只抽取原失败方法AST执行，绕过该测试类其余方法所需的无关heavy imports。原方法在同一真实镜像上复现指定ModuleNotFoundError；candidate在canonical模块缺失和预先存在sentinel两个状态下均通过全部原业务断言，并完整还原sys.modules/sys.path。每次实际production调用计数为project_plan2/project_card1/reason_text3。

实际D consumer函数源与bc/0f逐字节相等。该函数的全部非builtin global只含Mapping、QUERY_STEP、ROOT_STEP；Mapping为stdlib实物，后两个绑定的来源模块actualD/bc/0f也逐字节相等，并核对实际值。D整棵src与0f仍有26文件差异，故这里不是全类、完整exact checkout、CI Python3.13或整个step55通过。未跑完整CI矩阵，未授业务或native实机资格。

容量原a01把source_paths_only误写为tools下同名测试；真实目标以上述ck3_autonomous_player路径为准。追加勘误保存在父capacity/CI-FIXTURE-REPAIR192-SOURCE4-CHILD-PATH-CORRECTION.actual-a02.json（4531B，SHAb0b9794137e1c1d43075e6402b79d366f4c00563947047a3b95ad6deafe1dfe8）；原a01保持。

后续精确应用输入为SIBLING-CONTRACT-IMPORT.candidate.patch；FOCUSED-ORIGINAL-WAIT.actual.json记录真实测试及原Popen结果，SOURCE-AND-PREPARATION.actual.json给原Gitblob/镜像/只读D绑定pins，CLOSED.actual.json列本包最终字节。发布需要独立Git准入；本包仅候选和局部验证。
