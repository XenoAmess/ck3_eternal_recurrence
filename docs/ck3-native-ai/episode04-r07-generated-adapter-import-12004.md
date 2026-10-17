# R07 生成日步 adapter 的跨目录冷导入

machine_id: `desktop-3fevhd2-1c74096080`；2026-10-17，R0195/source611bc985ae95f477dd7314df11f8602cd1e595f3/a33。现场事实只属于该机器该场。

R195 的第一份已绑定日runner为35889B，SHA `da56210ba189245682df2459820f8acf61deb5ce9c7fdc8ea2b66eff52508b02`。首个 `r195-s1-day1-a01` pilot实际exit1：生成脚本line346用importspec执行current_r07.py，在后者line24导入qualification_contract时ModuleNotFoundError。错误发生在Runner初始化与任何SDK/Arm之前，是接线失败，不是精确日业务失败或已消费自然日；该failed attempt原样保留。

原因是生成runner放在scene根，adapter及qualification_contract/owner scope放在另一已pin包目录。importlib.util.spec_from_file_location加载指定文件不会替目标的普通绝对import加入其父目录。旧focused检查仅生成AST/编译，没有覆盖这个真实冷进程跨目录导入场景。

最小生成修正是在动态adapter exec_module之前插入 `sys.path.insert(0, str(Path(_current_adapter_path).resolve().parent))`。该目录来自已固定SHA的实际adapter路径，不能猜工作目录或依赖上一次进程缓存。`future-materializer-import-fix.candidate.patch`将这条缝加在新包生成阶段，旧adapter/bound bytes/运行binding不修改。未来每个新的schema/adapter依赖也应通过相同冷导入case，不把纯编译当作依赖可解析。

R195现场由Root在外置通用runpy启动器 `C:/ck3-e04-resume-20261015-a01/r195-root-env-launch-a01/launch_bound_dayrunner.py` 显式加入已pin包目录，使用新pilot attempt `r195-s1-day1-a02`。不覆盖旧runner，不重绑原baseline，不重投任何已知或未知Arm。Root已独立审到新pilot真正完成tick1/overshoot0后才推进2–24；零callbacks仍不证明免费。

新增必要回归使用真实a33 adapter的import-only子进程：移除父目录时确切缺qualification_contract；插入父目录后模块成功导入。两侧都不初始化Runner、不执行guard、不发SDK、不创建生产资格。测试工具自定义exit7仅为捕获预期导入失败，不能替代首次真实pilot的exit1。证据 `ADAPTER-COLD-IMPORT-CHECK.actual-a01.json`，2585B SHA `a0552dc5078f51e7536c489a916be6c9e98a7d4baef4b5d2f4612b685b5e59db`。

此修复只解决生成代码的Python依赖接线。sameS0/runtime/native source/operation/capacity、single firstsea preview、无Move/Halt控制、日步once claim/实际独立暂停、sampling/window/epoch、完整付款来源及录制/正常关闭门槛均保留；不重跑旧完整矩阵，不宣称control32日/pair或视频完成。

跨机原件与部署备稿的精确字节见[portable provenance](evidence/episode04-r195-r07-baseline-import-12004/deployment-provenance.json)。其中保留原失败、冷导入回执和外置 materializer 候选 patch；不安装新的通用 CLI，不追认旧场已部署。
