# 共享 CK3 存档读取核心

Java 21 叶模块，供宗教礼仪融合与宗族化密教的 Quarkus CLI 共用。唯一的 Clausewitz lexer、AST、流式选择器和 Rakaly 进程生命周期在此维护；叶模块不启动服务，不进入游戏载荷。默认命令行 Maven 要求不低于3.10.0。

在仓库根目录执行，先按当前机器存储策略批准三个独立构建根和临时输出：

```text
mvn -f pom.xml -pl :ck3-save-core -am -Dsave.build.root=<approved-shared-build-root> -Drrf.build.root=<approved-rrf-build-root> -Ddes.build.root=<approved-des-build-root> verify
```

三条产品CI均从根reactor在同次完整verify中构建、测试并消费实际共享leaf，不再先install私有GAV。没有Python fallback；编译仍使用 `-Xlint:all -Werror`。

两款 CLI 的 `inspect-save-v4 --inputs <request> --output <report>` 使用严格 Request4 和 `ck3-save-inspection-v4` 报告；未知字段、错误整数类型、旧 shared v3 请求与命令均拒绝。选择项采用显式实体种类、表路径和规范十进制 ID；支持 Actor、Rite、Faith、Religion、Dynasty、House、Coat of Arms，以及有界命名路径投影和重复出现记录。结构目录检查必须显式指定 `structureRoots`；启用时非空，关闭时为空，只遍历所选命名根的有限相对深度。不得通过扩大节点／键限额转为全世界转储。

RRF既有 `inspect-save` Request2／Report2和fixture Request3合同继续由薄适配器提供；v2原子字段为 `raw`，v4为 `token`，比较时须尊重版本。DES原来的预置信仰校验也使用同一parser。

工具校验实际加载的JAR或classes与内嵌producer源码，并分别报告仓库源码和加载代码身份。实际decoder的退出、流SHA和原保存身份另行核对；报告不产生游戏业务通过结论。真实验证及已知边界见[产品续工记录](../../mod_religious_ritual_fusion/docs/live-review-resume-2026-10-26.md)。
