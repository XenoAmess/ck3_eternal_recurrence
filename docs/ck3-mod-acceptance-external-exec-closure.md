# 外部工具启动的未使用实机分配闭场

2026-10-24实际阻断：`exec_command(shell="cmd.exe")`启动公共allocate并返回可续读session，最后由`write_stdin`观察到退出0。原`ck3_mod_acceptance_unrun.py`只接收自行保存的无shell wrapper回执或原Popen三联；二者都不是该次真实生产者。不能事后伪造intent、Popen身份或`shell=false`来满足旧入口。

在现有[unrun模块](../tools/ck3_mod_acceptance_unrun.py)增加`--allocator-external-exec`，与旧两种证据形式互斥。`external-exec-completion-v1`绑定机器、原请求、初始running响应、最终completion请求及响应、完成观察时间、退出码，以及最终工具响应中output的精确UTF-8字节。原shell与命令文本保留；只解析受支持的单条literal cmd命令，不执行该文本、不把它改写为无shell调用。

初始session与最终续读请求必须一致；ID、token计数和退出码拒绝bool、相等float及超出安全整数范围的值。文件pin先核字段、实际大小和SHA，再读取JSON。最终output不能归一CRLF后冒充原字节。它是**最终工具响应包含的完整终态JSON块**，不宣称保存了进程启动以来的全部stdout流；此前续读可能已经返回其他块。

该形式只证明观察到公共allocate工具退出0。它不证明allocator的原Popen身份，也不证明host或CK3退出。原600秒unused超时、keeper真实退出0、run/机器/计数器身份、固定来源、未产生launch/native/control/save、真实CAS释放和当前进程清单守卫全部保留；闭场始终不给游戏或业务通过。

本机实际链：`machine_id: desktop-3fevhd2-1c74096080`，`desktop-3fevhd2-1c74096080--superman-qiang--R0023`。2026-10-23T16:00:20Z，父代理直接观察原session97171返回0并保存原始工具数据；原keeper于15:59:46Z结束，随后实际CAS8444完成释放。新消费者于16:07:29Z实际返回0，生成`C:/ck3-superman-validation-20261023/r23-unrun-close-a01/ALLOCATED-UNRUN.actual.json`，SHA-256为`827dc1bf71221e6a0f4ddf508f782bf804425d1d53743232874171911c322b65`。它保留原ready/frozen，确认未启动host、native或游戏，没有把本轮计入模组实机通过。

原工具请求与响应、逐字节终态块及父生产的合同保存在同一项目`ops/R0023-EXTERNAL-EXEC-*.actual.json`；最终块2389字节，SHA-256为`2464da13c865129f8b4de5c39d04d09b1d77735970ae6c4ffa05a10f052dbc76`。这条改动服务所有公共验收调用者，独立产品不另建闭场协议。旧无wrapper失败和旧共享版本合同不改写。保存回执不是自动容量或业务资格。

后续真实分配必须选用同一份更新后的公共helper清单，并重新固定变更文件；不能热改旧frozen或把新helper写入旧来源树。原始操作证据按通用策略30天复核，小型闭场记录180天复核；作为下一场必要前驱时，另按策略记录有限保护及复核理由，不默认永久保留。

同机修改范围验证：既有`test_ck3_mod_acceptance_unrun_stages.py`共11项通过，已由原`static-ci.yml`命令发现；生产模块普通mypy与该测试文件strict mypy实际通过，不外推为整个共享CI step或旧动态代码已经全部严格类型化。本轮解释器为项目`tools/.venv/Scripts/python.exe`，typechecker为外置mypy2.4.0；16:14Z前后为解决实际缺少psutil类型声明，安装`types-psutil 7.2.2.20260906`到该venv，仅增加静态声明，未升级psutil运行包。检查来源为本轮命令的实际退出码和终端输出。
