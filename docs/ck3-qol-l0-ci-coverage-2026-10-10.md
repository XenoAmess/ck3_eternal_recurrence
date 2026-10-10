# QOL本机L0与CI覆盖（2026-10-10）

fde5官方run38020302422实际64成功/20条件跳过，不覆盖QOL完整L0。本轮在同一`static-ci.yml`只接入现有`test_build_xenoamess_quality_of_life_release.py`与`build_xenoamess_quality_of_life_release.py --check`，未新增产品runtime或partial validator。两命令无需已安装CK3；builder单测9项及实际源双构建已在本机一次通过，后继官方结果仍待对应commit。

完整QOL validator和phase2生成器读取未入库原版游戏输入，因此在本机实际执行；不把hosted CI总绿、registry14产品身份覆盖或builder通过外推为原版业务语义通过。本轮必要六项工具实际全exit0、约4.24秒，parser语法16产品文件及4个PAM夹具文件0错误；current .4 semantic profile UNSUPPORTED边界不变。精确源、命令、corpus及回执见[R52/R53后继记录](xqol-r52-r53-dispatch-and-qualification-2026-10-10.md)。

CI覆盖跨现有workflow统计。de-jure/holding已有`independent-maintained-mods.yml`执行公共构建单测、各产品普通静态与双构建；li-yu已有`li-yu-dao-static.yml`执行产品单测、生成器/静态与双构建。它们缺少static-ci的重复步骤，不构成全仓缺测。本轮只补原本缺明确入口的QOL。发布及验收工具统一不要求一个CI文件，现有workflow保留；七语发布格式仍仅在显式发布阶段执行，不搬入普通开发CI。既有非中文格式检查不授语义或实机信用。
