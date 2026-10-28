# Resume63 06Z：receiver、registry 与 SAVE 的有限原生结果

machine_id: `xenoamess-full-tower-eb9d2c1186`。观察日：2026-10-28 UTC；本页复用各 case 的已保留结果，独审截止06:00Z。来源为 CK3 1.20.0.4/build25734779，EXE101040248B，SHA256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。

Official REA/Owned、解码/CFG、ABI与实机资格分记。下述均先minclose、owned0，无新增业务代码、测试或Game信用。各peer与对应owner同目录。

## M6：初始化不是最终 loaded bank

552B/96指令先写 P 的 vptr-shaped 字段，再以17组、每组16B写 QWORD+BYTE（仅9/16B）；P+1170交给三个 opaque helper。最后的3214800现已取完整379B/77指令：实际从 P+50 的 rows 和 signed DWORD P+5C、步长8遍历；F1非零时同一快照写39个QWORD至[P+1000,P+1138)，F1零支只是 opaque4226F10。join再次读 F2→P+1138，不能认F1=F2。

后续 a=u8[row+26F8]只排39；当前 T=[P+1000+8a] 的 DWORD[T+38] marker检查后可写该槽。b=u8[row+26FE]只排1，随后写[P+1138+8b]。因此 a=46 或 b=7 的静态路径可能写 P+1170，不能说此窗保持初始化值；未采实际索引，不冒现场覆写。marker属于当前T，不能偷换成每个row的marker。空rows路径RET为0，非空正常RET为末轮b；外层552另行赋RAX=P。

与R13七×24地址窗只闭相对偏移，不授对象相等、owner/fullID或loaded资格。现 Native Definition rows/count/stride合同获支持；未出现需要改 Java typed wire/ordinary direct_landed 消费者的反例。

552 [owner][6ao]7581/`5fb274f5c00938dd1b2ae7cac22133e9d010e8cbbcb70860f7dc013adcd182c3`；`FN-INDEPENDENT-REA02.json`3288/`d1559003e200e547246bcd59c883de3dac4c5cbeae952fb903d92a51dd5216fe`。
379 [owner][6bo]8076/`65eaa9fd02e3d3a18d26c55137ac3522fbbe1a3e6f499ae867d0c63e7c796cd1`；`FN-INDEPENDENT-REA02.json`3270/`da67acf4dc0ec6a23bf9417ee3c09eb6f48a76b29447a41e00373e17cbcb924a`。379原字节/双decoder/p8、8signed、2RIP、12块17边及portable65424B回环一致。

## M5：receiver 来源在首 opaque 调用处仍断开

1070B/272指令中，42247B0发生在 MOV RBX,RCX之前，所以B只能命名为该调用后的RCX，不能直接命为入口O；也未证RAX仍2130。可见B+50/58/5C以及RBX=B+178后的+8/+14/+18条件写。13个direct CALL无31C7680，只给本体有限否定，不排间接/跨callee注册。

35块51条内部边一致；错误块CALL4232A70若返回，NOP后可落出RF末EE，不能借自动noreturn抹除此边。现完整power producer→ArmyForecastReads/typed codec→RootWarPowerReads/Collector/Priority守卫不变。下一需要已接受的同帧actor/target/effectiveTarget/date/nativeRevision/scopes/provenance；receiver命名另需入口/调用后RCX及S/F10身份见证，不继续凭编译器形状猜helper。

[owner][5o]6949/`cd1f79c6840dba5918a49efb6fe4750d73f74570d32750a224cf08d0c7dd2b40`；`INDEPENDENT-REA63-REVIEW01.json`3343/`c5847e43452b7a6b103e8c03d5f7fc80ae35c077c52363d7a99527bad59dc92b`。36signed/4RIP及portable224100B一致；两个unsafe整数仅保词法，不作身份。

## M4：GUI 复制门参数闭合，净退款仍无 producer

97B/24指令证明 P=[entryRCX+D8]；非NULL时 P+10的完整DWORD写command+24，global54DBC00的完整DWORD写command+20，两个表地址为476C420/476C3F0。显式 RCX=&command、EDX=0→2982700；R8/R9及额外实参未证明不存在。NULL只清AL；正常路径传递callee原AL，均不授全EAX为规范bool。

这补的是既有复制gate的GUI来源。paid incarnation、付款账户、最终提交校验、净quote及取消后钱包/项目归因仍缺。同帧合格reader/readPermit未取得时继续missing；Java empty quote/credit0不变。

[owner][4o]12050/`5f5dab860be295ce66f682f365b449504d11f37760dc4be5797252ffa92873c3`；`INDEPENDENT-REA63-REVIEW01.json`3316/`3b76eec4873dceeb4f5b187fc98140a1a63d03e2dd479656ba05ff93d4ee2ac0`。双解码/p8、2signed/3RIP、手3块2边及portable17786B一致；未请求自动图。

## M2：实例查询不等于选项或效果资格

134B/35指令先保存entryRCX，RCX/EDX至CALL29C5640前未改。opaque返回EAX<0时返回NULL；非负时读QWORD[QWORD[entry+1F18]+8*index]，本体无bounds/null-array检查，元素本身仍可NULL。R11D初值-2跨opaque未证保留，后续XADD不能无条件叫decrement2/release。全六RIP指向5C6A2A8，实际含原子写与spin，不能当纯getter随意调用。

仅本体未直接读choice/disabled字段，不排callee资格。原EventWindow rendered/native-index仍是动作authority；typed receiver/vptr定位仍需本帧原窗口输入。

[owner][2o]2920/`ae068bc6a03b826cc2fe0340807d7325e62ca73e865e515badbb88534a5afef4`；`INDEPENDENT-REA63-REVIEW01.json`3375/`d67b45ea9afe2b09babce4cb7d85082eb4609fb4c35f3e14f22edc91d11489e1`。双解码/p8、6signed/6RIP、手8块10边、capsule65979B回环一致；没有自动CFG声明。

## M7：open 拒绝来源闭合，不等于 saved

613B的164条Rizin pD记录及原字节相对控制核对：mode home=0选handler+28表的+48，非零选+50；底层IO仍opaque。ECX40的间接调用返回N后，可见N+0=IO、+10=handler及若干零字段，再把N+38接入fresh context+48。具体IO/vptr、OS flags、flush和持久完成未闭。两个error CALL之后只有最终一个INT3，不擅授noreturn。

这解释已存在error tag1/number4的打开拒绝来源。bridge仍只回submitted，未外露该工作callback，不能倒写为dispatch前拒绝。Checkpoint原链仍需要真实ACK/outbound、同Game/source/session/actor/date/episode/lineage后帧、changed且两次稳定FileWitness、完整Driver/pair及canonical APPLIED_CONFIRMED；缺项保持Pending/Unknown且不重发，不加callback新门禁。cold继续核原public Restore/两READ及物理pair。

[owner][7o]13410/`680c8559eec6b3dfec960897202b8da7620efc58a2bc34b60d805ea040d831be`；`INDEPENDENT-REA63-REVIEW01.json`3355/`21ac2fb5ec2db9ab2768b54b7b64024a70369e815ebdcc66d15e178ba4597551`。34signed、手34块49边、两official record及portable28201B一致。没有第二独立decoder/自动CFG或SAVE完成信用。

## 执行与成本边界

|题|记录wall_ms|最小close UTC|producer显式整PE相关逻辑读取B|
|---|---:|---|---:|
|M6 552|Cap2213/REA13491|03:57:17.388|202081060|
|M5 1070|Node570/Cap375/REA5631|04:41:35.460|202081578|
|M7 613|RF4896/body3572|04:41:36.064|见下|
|M4 97|REA1606|04:51:27.858|202080613|
|M6 379|Cap497/REA4421|04:52:16.643|202080887|
|M2 134|Cap439/REA4065|05:00:34.435|101040942|

wall含wrapper，非CPU、整批墙钟或游戏速度。各case顺序受管，跨case上限4；所有上述首close均期限内owned0。已观察M5/M7真实执行重叠，不以逻辑岗位或lease数当实际并发。单个Rizin峰约12–594MB；未测joint峰或物理I/O。

M7显式preflight身份读取195964085B；SDK四次整PE摘要404160992B为源码/保留字段支持的口径，合600125077B，未instrument历史pass counter。M5/M6/M2官方subject为原PE，SDK额外digest另计且不冒provider实际I/O；M4为派生97B，不能把raw SHA当PE SHA。选中代码字节数不是总I/O。

新case区分scalar aggregate与对象per-stream；失败API text、UTF8/JSON上界入账，不称原binary。M2旧未执行READY撤回、02修export异常保partial capsule及双原流；旧原件不改。目录仅导航；不重扫107refs，旧失败/source/close保原身份。

[6ao]: D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m6-global-init552-01/FN-SOURCE-NOTE02.json
[6bo]: D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m6-final-p-init379-01/FN-SOURCE-NOTE02.json
[5o]: D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m5-receiver2e40cc0-01/CASE-RECEIPT01.json
[4o]: D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m4-gui-gate12aec90-rf97-01/ACTUAL-REVIEW01.json
[2o]: D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m2-instance29c56f0-01/CASE-CLOSE01.json
[7o]: D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m7-save-mode1-open01/RESULT01.json
