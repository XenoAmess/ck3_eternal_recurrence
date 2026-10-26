# Resume63：独立有限 raw case 复用方法

machine_id: `xenoamess-full-tower-eb9d2c1186`。2026-10-26T17:12Z 方法交接；来源为当前安装的 REA 6.8.0 / Rizin 0.9.1 和已完成的 member-validity case。Root 依据用户新的并发要求，将此前单 backend 调度改为最多 **4 个独立 raw provider**；这是资源上限，不是启动授权或共享可变数据库的许可。

先提出可证伪问题，列实际 caller、actor/consumer/trigger 的已知与 UNKNOWN，查已有完整原件和 RF 元数据；没有新问题不启动 provider。每 case 独立 PLAN、输出、TMP、export、stdout、Rizin 会话和 WindowsOwnedProcess。PE、安装包只读；不共享可变 DB/cache，不导全 PE，不自动跟 callee/incoming/vtable/globaldata。每题的 body/RF 条件、1 GiB provider、120 秒 work + 60 秒 close 都由 capacity 新卡批准；卡不复用、不延时。四 slot 的分配以 capacity 的实际鲜卡为准，本页不是锁或调度 runner。

## 已真实成功的模板

公共根 `D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m1-member-validity01/controls/`：

| 文件 | bytes | SHA-256 |
| --- | ---: | --- |
| REA-DIRECT-INVOCATION01.json | 6951 | f4304ef14985aea1e3aa441a5fd4798a781f39e6916da7c0622a46f7fd6cded6 |
| CAPSTONE-DIRECT-INVOCATION01.json | 5655 | ba68b3f0d2cc6de0b4c730d1de5b43cba7d3a18694478c708a4102642a555a5d |
| DECODE-BODY01.json | 6722 | 9ffd0a37418c05a4e70f97371a75c988c519cc97ff18d7d2df303e98a5e9a203 |
| MINIMAL-CLOSE-INVOCATION01.json | 4013 | ccabcdab20ac295c66ee7502b166e889b4061a64440a25fd760141f18439feda |
| MINIMAL-CLOSE-CHECK01.json | 2112 | 1cd46ead6eff66551b49090a4bf175f3e603f189fa869b3fc08fc3aa97945a77 |

这些 JSON 是 case 专属的真实命令，不可原样回放。`arguments[2]` 中 base64 解出 Node 源码后，只在新 case metadata 中改本题 root、RF/读取范围、输入守卫、输出和实际 PID；保留官方 service 和 OwnedProcess。Capstone Python 是已有离线研究工具，不能演变成新 Python 生产或编排模块。新题先用实际旧 closed records exercise 最小 close；metadata-only RF 拒绝路径也须能闭场。命令先编译检查并确认 cmd 长度低于 8191，不能等长 JSON 组装后才关闭进程。

实际 Node：`tools01/node/node.exe --max-old-space-size=128`；包：`tools01/rea/package`。生产入口为 `dist/composition/reverseEngineering.js` 的 `createReverseEngineeringService`，依赖原 `dist/process/OwnedCommand.js`、`ProviderProcess.js`；`executeRizinCommand({path,command,command_timeout_ms:30000})` 后在 `finally` 调 `service.close()`。launcher 只观察原进程 spawn/exit/close，返回原 OwnedProcess，不另建 runner。正常函数命令使用：

```text
e analysis.limits=true; e analysis.in=range;
e analysis.from=VA_BEGIN; e analysis.to=VA_END;
e analysis.calls=false; e analysis.hasnext=false;
e analysis.jmp.after=false; af @ VA_BEGIN;
afij @ VA_BEGIN; pdfj @ VA_BEGIN; agf json @ VA_BEGIN
```

必须按本题已准范围替换地址。raw prefix 无已确认 RF 时只 `p8` / 有界 `pDj`，不把中间字节当指令入口。`agfj`、`omj` 等可能 exit0 却返回诊断；解析 payload 后才认具体查询成功。Rizin 0.9.1 映射列表为 `omlj`；C4 的 `omj` 失败和 late close 原样保留，不为形式补测。REA raw Evidence 不具 native dossier/facets 资格。保 flat Evidence 与 portable bundle；内容身份不能替代 PE/工具/来源真实性。

先关 provider、核 exit/close/streams/activeProcesses 与实际 owned PID 后态，立刻写最小 close；再进行 CFG、独审和富 receipt。缺 stage 或未查 PID 写 UNKNOWN，不能冒 0。provider 早 close 不等于整个 180 秒批次通过；outer Job0、联合峰值未测即 `NOT_MEASURED`。Shared 旧 pre-child 拒绝保持失败，官方 direct 成功不授 Shared 资格。

## 旧原件导航与并发交接

`Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/` 下 `shared-span-cache`、`function-match-core` 和 `NEW-RUNTIME-FUNCTIONS.json` 可先按精确地址/文件名复用；只报实际查过的 scope，same ordinal 不是函数语义证据。历史无 machine_id 原件仍为 unknown。当前 PE contract：1.20.0.4/build25734779，101040248 B，SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，image base `0x140000000`；每题仍须绑定当前实际读取。

本次已向 M0/M2/M3/M4/M6/M7 发送上述 exact refs。17:12Z REA63 自报 0 provider，仅 gate2C7DED0 metadata 准备；M7 自报 0 provider，正处理 Java 诊断。其他岗准备中的问题不计作已启动或占槽。READY 应带 PLAN exact ref、旧资料复用、RF 条件、最大新字节、实际 argv、close exercise；capacity 鲜核 RAM/卷及 slot 后才能执行。各岗把真实 begin/close、原件 refs 与 UNKNOWN 回报 Root/REA63；本页的时间点声明不替代实时鲜卡或进程测量。
## 本轮后继实际方法验证

M3 已通过官方 service 实际对派生 `raw/assembled407.bin` 执行 `p8`/有界 `pDj`，显式 x86/64，逐 byte与相对/RIP算术重核；subject 的 arch=null 原样保留，没有 native dossier。此法可在已持 bytes 上分析，不能把派生文件的Evidence当原PE分析资格。确切原件由 sources 的 peer retained-nav→M3 receipt定位；后者另绑原PE、旧296和新111 B来源。M1 Base850同时证实pdata RF850与Rizin可达849可不同，原始尾CC保留；不为凑格式补backend。retained-nav只列已收原件，不是锁、runner或未列域的研究缺席证明。
