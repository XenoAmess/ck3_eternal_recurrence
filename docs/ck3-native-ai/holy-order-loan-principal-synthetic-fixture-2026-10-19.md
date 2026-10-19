# 玩家 root 本金 getter：独立合成生命周期验证

`machine_id: xenoamess-full-tower-eb9d2c1186`，本轮 producer 经 `tools/ck3_live_run_id.py:current_machine_id` 实际读回。[完整小证据](evidence/holy-order-loan-principal-synthetic-fixture-2026-10-19.json)保留UTC、全部实际命令、642个header、工具、CRT/library、原object和新DLL的pin。独立 [fake TU](../../ck3_autonomous_player/native_bridge/research/holy_order_loan_principal_12004_fake_fixture.cpp) 在首次compile/link与一次Python子进程调用中完成 **9/9合成路径**。旧getter源码、source-only四叶与object编译记录均不改写。

只读复用了上一轮33,310B object，SHA `9b5d5d83…3f976`；新增fake TU提供五个精确签名的项目stub，以及自己持有的definition、角色、root/scratch/allocator替身。没有链接Native archive、生产DLL或CK3输入。新fake DLL为43,008B、SHA `3bd8cd8cad2a339f4388f5fb8366d8d70c752920e688b9c4d770e9f57d229c8e`，实际PE恰有一个导出 `RunHolyOrderLoanPrincipalFixture12004`。现有Python `ctypes` 仅加载该fixture并调用这个导出一次。

compiler、linker与调用子进程均是单worker、BELOW_NORMAL，沿用同一个MSVC `/MD /O2` 环境；编译保持 `/W4 /WX`，链接 `/DLL /INCREMENTAL:NO`，没有debug/PDB或新EXE。编译、链接和focused调用均首次通过，失败attempt=0。实际链接library和已加载MSVCP/VCRUNTIME/UCRT逐项pin；Python先已加载的VCRUNTIME路径与VS redist的MSVCP路径分别记录，未追认为同一份运行库。

## 实际合成结果

`R/A/B/E/C/b/a/r` 分别表示root构造、第一/第二scratch构造、求值、第二scratch清值、第二/第一scratch释放、root析构。每条路径比较整个调用顺序，并独立计数；fake allocator同时检查receiver、data、8字节对齐参数与已清零的count。求值替身还检查实际reader传入的`{root,NULL,root,scratch,mode}`、完整玩家ID、source descriptor及root借用位置。

| 路径 | 实际顺序 | 实际结果 |
| --- | --- | --- |
| 正数quote | `RABECbar` | raw=41,500,000；available；eval=1 |
| 真实零值语义 | `RABECbar` | raw=0且optional存在；available；eval=1 |
| definition缺席 | 空 | eval/构造/释放均0；unavailable |
| 第一scratch构造返回NULL | `RAar` | 仅释放已取得第一scratch及root；unavailable |
| 第二scratch构造返回NULL | `RABCbar` | 两scratch及root各清一次；eval=0；unavailable |
| 求值返回错误out | `RABECbar` | eval=1；全部owner清一次；无raw输出 |
| 求值SEH异常 | `RABECbar` | eval=1；全部owner清一次；无raw输出 |
| bookend日期变化 | `RABECbar` | 清理完成后仍拒绝available及raw |
| 第二scratch清值SEH异常 | `RABECar` | 第二释放未确认；第一/root各尝试一次；cleanup=false、unavailable、raw缺席 |

两次SEH由fake callback中的`__ud2`产生，由未修改getter的实际Guard接缝处理。构造失败case是在完整fake初始化后返回NULL；native半构造异常、原生allocator和游戏持有对象的实际生命周期不在此次资格内。definition缺席时cleanup=true表示没有取得owner，计数证明它没有调用构造/释放。

此次验证的是已编译getter的控制流、参数打包和owner处理接缝。全部角色/日期/definition/本金均为固定合成值；它没有验证真实RVA/native ABI、application-main、加载中的脚本、当前借款资格、真实本金或钱包债务读回。资金信用仍为0。当前Native26/SDK/Service/native_driver、Game、RPC、桌面与SAVE未触碰，没有注册query或借款动作。

## 存储闭场

获准新根为 `D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/m4-principal-fixture01`，预计2MiB、硬8MiB（含新增repo源码与证明）。25ms采样的logical高水位为 **3,402,067B**，发生于链接阶段，高于预计但低于硬上限；这是观察下界，不能称为未采样瞬时峰或physical allocation。最终数量见同根`CLOSE01.json`，包含自身、所有新增repo叶、allocated unknown/null、producer/process closed和future writes=0，不返还父预算或physical信用。

旧object根及其他closed child一直只读。外置派生复核为2026-10-21T05:28:31.936273Z，父期限不续；跟踪记录按通用策略180天复核归纳。本轮止于合成fixture，真实集成与原生读回继续保持未资格。
