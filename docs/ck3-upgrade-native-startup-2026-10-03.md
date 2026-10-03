# 兼容接续：本机 `.3` 原生启动 R0002

本包接续 [2026-10-03 接手记录](ck3-upgrade-resume-2026-10-03.md)，只记录真实准备与首次启动。主/白绮七 cell 仍为 `.3` 实机 **0/7**；AUB 没有到地图、政策菜单或自动建造循环。

## 冻结输入

复用已有 `.3` 原生迁移源 `f4e1bb33fd1c31820b6d2fe29be8185d51663703`，冻结树位于 `C:/workspace/ck3_uuii/_runtime/upstream-migration-20261003-root-a01/native-wake-sdk-dependency-root-a01/source`。只启用已有的 1066 bookmark model、selected-character Start 和 Robert target 三个构建开关，没有修改该源树。新构建目录为 `C:/workspace/ck3-upgrade-20261003/courtier-agent-01/native-robert-frontend-build-01`：404/404 构建成功，model test 通过；registry test 因既有 strict-combat mapping 失败，原 RED 保留，不能称全 registry 通过。

DLL 为 4,539,392 bytes，SHA-256 `561bfe3fd38d20cbca750bcd3724ea1967f80e8c040f555e714eb13c6293ec9a`；injector 为 39,936 bytes，SHA-256 `740f7155ab3340b889baf51c0dc7bbe9f5cc6f8a0cdc52eb055a40ad4fef00cd`。本机游戏 EXE 仍为 `.3` / build 25652598 / SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。

外置 harness 使用实际 MCP route/NewGame/selected Start，不用 OCR、键盘或鼠标导航。文件 `courtier-agent-01/run_ck3_12003_product_mcp_live.py` SHA `42cce1ef9fdbfad5c8e87144292f71821a8dceea16e37549338ebd3b2d662680`；实际输入在 run 的 `frozen-argv.json`。AUB 17 文件生产投影、descriptor-only 空 fixture、85 项原版默认规则的准备依据见 [AUB/TED 后续准备](ck3-1.20-aub-ted-log-continuation-2026-10-03.md)。

官方 singleton runtime fingerprint 调用缺少 CUDA/rfc3339-validator 依赖，保留 **ENVIRONMENT_RED**，没有生成指纹。此次使用已有的显式 `--fixture-profile` 隔离启动路径；文件/source/EXE/DLL 绑定不能替代 runtime fingerprint 或 native save state 指纹。

主/白绮另有六个可独立准备的 `.3` cell：main UI、Vivhite UI、两种双 mod 加载顺序、writer、no-heir。reader 必须等真实 writer，cold 必须等真实 Robert checkpoint。准备报告 `courtier-agent-01/remaining-courtier-cell-preparation-01/report.json` SHA `816db235cddb962e199fa7a3eaff7e22c9365a4ca6345af2e2a17738195caa76`；14 个实际挂载目录的 parser 证据逐字节绑定在 `courtier-parser-evidence-bound-01.json` SHA `312484bdc2eefc26aa6181590bfbaca208a806bae8f5e52a311ae625f24e238b`。未改文件复用原检查，仅 changed writer/no-heir fixture 新检查 5/5、6/6，通过且零 error。均不是实机通过。

## 当次离线与屏幕占用

屏幕 task `ck3-upgrade-screen-20261003-a01` 于 13:09 UTC 领取独占，keeper 固定 clean checkout `6440948e73490808f78977daa44fa672fa3bcb74`。原始桌面为 1920×1080，当前 desktop size 相同。恢复工具反复取得相同背景画面，背景时钟停在 19:19；没有据文件时间判断整幅桌面已恢复。

13:24 UTC 的新 attempt `steam-offline-a03` 确认 CK3/录制进程为零、唯一 owner 和实际 C 盘 bus。随后依据已有桌面恢复合同，临时原生 challenge 窗口产生两次不同 nonce。执行者直接审阅 `steam-challenge-a03/challenge-2.png`，读到 `0c538bf9675c`、当前 UTC 和同一原图内 Steam 的“离线模式”。PNG SHA `f6011f6b4d62ce0de3e0007851cf2fc127e08b38d1ef95ce14b6777523edb717`。这只证明新 challenge 像素及同图离线标识，未证明整幅背景实时；没有切 Steam 在线、重启 ToDesk 或坐标点击。

两次过期证据的启动前拒绝均发生在 Popen 前，没有启动 CK3；原 review 和命令失败保留。实际启动直接审阅后随即执行，收据在 run 的 `offline-visual-review-a02.json`（文件名保留当时操作，内容绑定 a03）。

## 真实运行结果

Run **`4-8e1c2f1861--auto-upgrade-buildings--R0002`**，执行目录 `C:/workspace/ck3-upgrade-20261003/live/4-8e1c2f1861--auto-upgrade-buildings--R0002`。13:24:43 UTC 建立 native 会话，实际 CK3 PID 14020；原生 DLL、hello、心跳、mailbox 与 MCP 已接通。初始 executor rejection/unavailable 随游戏加载过去，不视为 mod 失败。

13:26:11 UTC 首个可用 typed route 是 `bookmarks`。当前驱动只允许初始 `main_menu`，于是报告 **RED**；没有调用 NewGame 或 selected-character Start，没有开始战役。`native-report.json` SHA `48536131cf8b669cd9301247253b03011e233d3b69a85280ceedc38a90d1435c`，原始 MCP/native wire 和 stderr 全部保留。13:26:33 的 `loading-observation-01` 保存了当时日志，error.log 为零 bytes；这只是加载观察，不能写为完整 loader 门禁通过，更不能和旧 `.2` AUB93 条错误作单变量因果比较。

退出由受管会话进行 containment：`cleanup_ok=true`、最终 job active 0，CK3 exit code 1、清理前仍有一个活动游戏进程。故记录为清理完成，**不记正常游戏退出**。13:28 UTC 本机复核 CK3 为零，keeper 停止且 CAS release 成功，随后才更新 checkout。

后续诊断已定位两个具体驱动阻点：无 checkpoint 的 owned launch 固定 `-continuelastsave`，但 route=`bookmarks` 本身不足以证明可操作的实际 picker，需要 typed tree；`.3` adapter 的 hello 目前遗漏已启用 flags 对应的 bookmark model/selected Start capability，Python 会在缺 capability 时拒绝下一步。修复必须保持真实注册与条件一致，不能绕过缺失声明。后续使用新源/二进制、新 run 和新 userdir，旧 R0002 原样保留。
