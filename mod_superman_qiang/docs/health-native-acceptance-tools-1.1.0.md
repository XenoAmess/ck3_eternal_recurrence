# 1.1.0 针对性健康实机入口

本页对应实际R19机制、R20冷重载及R21/R22普通界面证据。旧`prepare_live_fixture.py`与`verify_fixture_log.py`仍用于首发1.0.0六项42场景，不能将其随机预期直接用于七项健康候选。会话runner的默认结束标记也保留首发语义；健康流程必须显式选择基线就绪标记，基线就绪不等于20项完成。

## 生成与独立检查

在主树实际验证的解释器为`tools/.venv/Scripts/python.exe`3.14.7；冻结SDK根为`D:/sxad-freeze-20261004`，不是其`ck3_autonomous_player`子目录。下面命令是Python/CMD，无PowerShell。所有输出必须是新的外置目录，旧attempt保持原样。

```text
tools/.venv/Scripts/python.exe mod_superman_qiang/tools/prepare_health_fixture.py --output C:/new-health-run/health-fixture
```

实际六件生成输出与R19 A0004载入字节一致，20份contract相同。新manifest包含新路径及新生成器来源，所以manifest整体SHA不会冒充原A0004。生成器只写外置夹具，不启动游戏；其非生产角色、变量和测试窗口不得用于宣传。

新入口包含三天分段执行与真实可见基线事件`sxat.2`。先保存并独立解码基线，再选择事件选项启动动作；之后等待`SXAT: END health-1.1.0-targeted-matrix`及20个unique PASS，再暂停、真实保存并解码。不能用固定等待时间或日志PASS单独代替保存断言。

先按AGENTS领取独占屏幕、启动keeper、MCP/operator进程预检，取得当次新离线窗口变化/新像素并直接审图。正式production只能来自本产品build_release的22文件stage。通用runner保留inbox中每项真实MCP请求/收据，受管停止保全owned树退出。示例参数入口：

```text
tools/.venv/Scripts/python.exe mod_superman_qiang/tools/run_acceptance.py --prepare --output C:/new-health-run/session --production C:/new-product-stage/mod_superman_qiang --fixture C:/new-health-run/health-fixture --game "C:/SteamLibrary/steamapps/common/Crusader Kings III" --dll D:/sxad-native-20261004-a01/xar_ck3_bridge.dll --injector C:/new-health-run/xar_ck3_bridge_injector.exe --fixture-ready-marker "SXAT: BASELINE_READY health-1.1.0"
tools/.venv/Scripts/python.exe mod_superman_qiang/tools/run_acceptance.py --live --run-dir C:/new-health-run/session --screen-task ACTUAL_FRESH_SCREEN_TASK --timeout 1200
```

实际R19–R22冻结SDK由`SXAD_REPO_ROOT`显式指向`D:/sxad-freeze-20261004`，`SXAD_SOURCE_COMMIT`记录真实SDK HEAD f643b32e6146dce73f77fedfefd8471da59fb04f；产品来源另在manifest/purpose记录，不混同。当前已加载DLL和injector必须逐字节核对，示例路径不是承诺今后文件仍存在。`--live`成功仅证明会话完成与cleanup，不代表产品验收GREEN。

原生health查询为`ck3_query_campaign_root_context_v1`、以fresh revision调用，字段`result.campaign_root_context.player_health.raw/scale`。当前SDK只提供玩家的这个独立native health读值，不能声称任意NPC独立native getter。R19真实466160→466235/100000；NPC的有效值由脚本取样及独立saved基础字段/账本/倍率互证。

保存使用实际native autosave-command-v1并保留checkpoint，Rakaly0.8.19 melt后执行：

```text
tools/.venv/Scripts/python.exe mod_superman_qiang/tools/inspect_health_save_readback.py --run C:/new-health-run/session --save-dir C:/new-health-run/before-save --sdk D:/sxad-freeze-20261004 --player-id 31254 --output-dir C:/new-health-run/before-readback
tools/.venv/Scripts/python.exe mod_superman_qiang/tools/inspect_health_save_readback.py --run C:/new-health-run/session --save-dir C:/new-health-run/after-save --sdk D:/sxad-freeze-20261004 --player-id 31254 --output-dir C:/new-health-run/after-readback
tools/.venv/Scripts/python.exe mod_superman_qiang/tools/verify_health_readback.py --before C:/new-health-run/before-readback/health-readback.json --after C:/new-health-run/after-readback/health-readback.json --fixture C:/new-health-run/health-fixture.fixture.json --output C:/new-health-run/health-gate.json
```

decoder保全每个真实character块，读取唯一`alive_data.health`保存字段及六基础数组，UInt64有符号Q100000变量、raw modifier倍率用Decimal核对。它只读保存文件，不向游戏写状态。健康小数不能当整数截断；`integer_exact`仅在ticks可整除100000时有值。

## 真冷重载与普通UI

冷重载只挂原fixture的descriptor、modifier/SV定义，排除on_action/events，避免重置数据。`--checkpoint`指定实际after保存。重载后再次实际保存/解码，并将两个真实native health收据传给：

```text
tools/.venv/Scripts/python.exe mod_superman_qiang/tools/verify_health_reload.py --before C:/new-health-run/after-readback/health-readback.json --after C:/new-health-run/reload-readback/health-readback.json --native-before C:/new-health-run/native-after.json --native-after C:/new-health-run/native-reload.json --output C:/new-health-run/reload-gate.json
```

普通UI单独加载真实production-only普通P2档，不挂fixture、不调用测试事件或写变量。普通右键查看自身与NPC，实际审原始尺寸通知正文与持有人特质，前后独立checkpoint核XP、七账本/倍率、基础健康/数组和traits保持。游戏正常设置70%经新原图及真实config共同验证；此前settings写入被SDK profile prepare覆盖0.5的attempt保留，不把设置ACK当可读性通过。

实际实验性受管helper、controller argv/stdio、inbox和保存入口完整保留于`C:/ck3-superman-qiang-110-20261004/acceptance/live-H0002`至`live-H0005`，精确SHA由[最终汇总](acceptance-1.1.0-20261004.json)及原始过程索引绑定。没有把这些helper宣称为通用自动UI导航；native缺口用有证据的官方UI路线，映射坐标与keyboard焦点合同照常执行。

本轮不验证统计分布、寿命年数、多人/成就、所有14修正各一个窗口或其他游戏版本。原42矩阵、首发错误/修复与发布事实继续以1.0.0历史文档为准。
