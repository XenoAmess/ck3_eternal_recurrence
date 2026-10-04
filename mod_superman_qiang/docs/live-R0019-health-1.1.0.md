# R0019：1.1.0 健康20项实际机制

结果：GREEN，仅本轮针对性机制及保存读回；UI与冷重载独立验证。完整身份 `desktop-3fevhd2-1c74096080--superman-qiang--R0019` / execution `4a16cc67-7b39-4ddd-87b5-d36b8b0b8f93`。

三轮实际 CK3 1.20.0.3，EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。同一冻结 native SDK `D:/sxad-freeze-20261004` / commit `f643b32e6146dce73f77fedfefd8471da59fb04f`，DLL SHA `ad3bbb4e7bc19f2737bba10c468d26cabcae4058c6c2ae4f3b8675e95c5b8518`；R18仅环境预备失败后从原obj/lib最小重链接injector，实际新binary SHA `bf0c1bb12f9f091a315b5b05be69ae01c8e5bceecf47708f2faae692909f1d63`，未重新编译DLL或声称新SDK能力。实际解释器 `tools/.venv/Scripts/python.exe` 3.14.7。产品源 `ff5b112d8bde46948538678b58705ad88b69e406` / live-candidate-A0003，22件production；SDK commit不冒充产品来源。task bus独占+keeper、当轮localoperator/新离线窗口位移像素/直接审图及完整加载SHA均位于对应外置attempt。

外置 A0004 六件夹具先通过5条实际open_kaishek JAR解析/roundtrip及1条YML格式检查。原生读取基线事件 `sxat.2` 后先真实保存，再选择原生事件选项执行生产helper；日志20 unique PASS / 0 FAIL，独立存档40角色读回20/0/0。不能仅以日志PASS或controller退出码宣称机制通过。native玩家健康 `466160/100000 → 466235/100000`，精确+75ticks。40角色基础健康原始字段和六项基础数组逐项保持，账本增量守恒，健康正/负单个modifier保存倍率与账本绝对值准确相同。

| # | case | 双方健康账本变化ticks | 独立后态 |
| --- | --- | --- | --- |
| 1 | player-native-health-75 | [75, -75] | PASS |
| 2 | health-flat-75 | [75, -75] | PASS |
| 3 | health-floor-below-3_00074 | [0, 0] | PASS |
| 4 | health-floor-at-3_00075 | [75, -75] | PASS |
| 5 | health-floor-same-day-repeat | [75, -75] | PASS |
| 6 | health-penalty-mitigation | [75, -75] | PASS |
| 7 | health-rebuild-idempotent | [75, -75] | PASS |
| 8 | health-ledger-growth | [75, -75] | PASS |
| 9 | health-ledger-to-zero | [75, -75] | PASS |
| 10 | health-upper-balance-block | [0, 0] | PASS |
| 11 | health-upper-balance-last | [75, -75] | PASS |
| 12 | health-lower-balance-block | [0, 0] | PASS |
| 13 | health-lower-balance-last | [75, -75] | PASS |
| 14 | six-skill-diplomacy-regression | [0, 0] | PASS |
| 15 | six-skill-prowess-regression | [0, 0] | PASS |
| 16 | equal-experience-health-no-transfer | [0, 0] | PASS |
| 17 | only-health-eligible-dispatch | [75, -75] | PASS |
| 18 | health-zero-receiver | [75, -75] | PASS |
| 19 | health-negative-receiver | [75, -75] | PASS |
| 20 | health-reverse-capacity-boundaries | [75, -75] | PASS |

底线3.00074排除、3.00075最后合法减到3、同日第二次不扣；±百万方向边界最后合法转移、已到边界跳过和反向离开实际保存。负健康抵消样例来源有效值不减但raw账本−75，接收+75；不承诺健康显示总是对称。接收0/−1仅实测同effect即时getter与账本，夹具随后去除危险负修正，不构成跨日生存/寿命证明。重复重建无叠加、归零清投影，外交/勇武代表回归基础数组保持。only-health与reverse通过生产pair/七项dispatcher实际选健康；不把强制health helper冒充随机接入，也不声称七项分布已统计证明。本轮没有重新覆盖原版had_sex_with_effect的projection入口，既有首发事实保持历史版本范围。

真实停止后完整error.log有164条E header，其中夹具theme1、fixture unused变量148、unknown formatter 14，另原版AI活动报错；无sxad文本。formatter来源未查明，不说‘零错误’或‘原版已证明’，不遮盖其日志。夹具运行与独立机制值准确；全日志原件永久保留。

R17历史为fixture effect `scale=var:...`语义失败，80条Failed to read scale；R18是原injector文件缺失造成预启动voided，无CK3启动。A3未运行、A4用与生产相同definition-local blockscale后R19实测通过，未修改健康生产为消除夹具错误。R17旧诊断对log缺失的猜测被后续真实flush原件纠正，旧note继续保留。

正常受管stop，owned game树与watchdog消失、process inventory[]；keeper保持以供下一串行重载。controller ok仅代表会话完成/cleanup，产品门是上述独立证据。

| 原始证据 | bytes | SHA-256 |
| --- | --- | --- |
| C:/ck3-superman-qiang-110-20261004/acceptance/health-fixture-A0004.fixture.json | 21236 | `a855829e86d8e31d975a0f99bd1a33155bdce3040aba9306cbf46cf6f5659c37` |
| C:/ck3-superman-qiang-110-20261004/acceptance/health-grammar-A0004/receipt.json | 5381 | `35c5bef0132b7263446946f85b1970d94cfedfa434c8ddfa1173258fd1a57bbf` |
| C:/ck3-superman-qiang-110-20261004/acceptance/live-H0002/session/preparation.json | 494600 | `69c5fd47088ca8fcf2a8481ce1ac8b681b978b915710934d48cbd2c97ae28429` |
| C:/ck3-superman-qiang-110-20261004/acceptance/live-H0002/session/receipts/inbox-001-native-health-baseline.json | 38186 | `0f5e4f754557c31826d7b67c72b879abaa40757c099caefda930c9c680f7be66` |
| C:/ck3-superman-qiang-110-20261004/acceptance/live-H0002/session/receipts/inbox-014-native-health-after.json | 38195 | `0a48d2d797f99800267b5acd87c97a6d4c30cdc6140be864f85ddb1a3356d4e5` |
| C:/ck3-superman-qiang-110-20261004/acceptance/live-H0002/health-readback-baseline-A0001/health-readback.json | 111354 | `b3b3d7879667336d779f3fb2f84f22a048f35242e3eb238938ff0df4661b61a7` |
| C:/ck3-superman-qiang-110-20261004/acceptance/live-H0002/health-readback-after-A0001/health-readback.json | 349887 | `1597ab81760e75018298c5b738cd0fc2f832dacb20e42edbeb886216a8e1f4c0` |
| C:/ck3-superman-qiang-110-20261004/acceptance/live-H0002/independent-health-gate-A0001.json | 60733 | `7a79afa74970a866da910e8d5c8ef2a4a46040e5c187a2c44228fbfb881f8acb` |
| C:/ck3-superman-qiang-110-20261004/acceptance/live-H0002/game-stop-gate-A0001.json | 2215 | `fb35064e661eb804a84a1e26f5762241d0c47e9508175a35d384cc1be8bda86d` |
| C:/ck3-superman-qiang-110-20261004/acceptance/live-H0002/stopped-log-archive-A0001/receipt.json | 4031 | `8824a66537133a0a4d1fa7e18dfa9eedf6768add4f44e17b4a30d342e26fd751` |
| C:/ck3-superman-qiang-110-20261004/acceptance/live-H0001/diagnostics-correction-A0002/receipt.json | 14372 | `5724bbe1188bb47abf337d18b0f6c4c2d4406d9201cb96910c58ce1191f09832` |
