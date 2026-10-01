# 本机 CK3 升级与全产品兼容验收

2026-10-01，用户授权更新本项目 master、本机 CK3，并逐个检查、测试和修复项目中的 mod。本页滚动记录这台机器的实际结果；其他机器的 native、profile 或实机结果保持各自身份。

## 已完成的环境更新

- 仓库使用 `fetch`、`rebase origin/master` 和普通 fast-forward push 同步；并发远端更新均线性接入，未创建合并提交。
- Steam 更新完成：CK3 从 1.19.0.6 / build 23530548 升至 **1.20.0.2 Crozier / build 25588574**；当前 EXE SHA-256 为 `ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d`。
- 游戏实际安装在 `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III`。仓库内被忽略的参考链接指向该安装。旧 EXE、manifest、特质、继承 GUI 和 3591 个原版文本文件已保全至外置 `baseline/`。
- 更新后 Steam 已恢复离线；启动前直接检查每次新鲜离线截图。在线期间发现其他机器正在使用账号，未启动游戏或接管其会话。
- 使用本仓库 `tools/.venv/Scripts/python.exe`（Python 3.14.7），分别安装常规、静态和独立宣传工具链依赖。本轮不制作宣传视频。

## 产品工作包

| 产品 | 源码/静态检查状态 | 新版实机状态 |
| --- | --- | --- |
| 永恒轮回 | 特质目录、Rite、原生继承窗投影已迁移；L0 GREEN | 待隔离验证 |
| 白绮独立版 | 上游与本机候选合成、独立快照/文案合同验证中 | 待隔离验证 |
| 肃清曼荼罗 | L0、可复现构建、profile-free parser GREEN | R0001：9 个严格核心断言通过，日志无错误；fixture 核心覆盖 |
| XenoAmess 体验优化 | 三类总督任命及改信/释放/赎金迁移；L0 GREEN、26 文件构建 | 待隔离验证 |
| 重整河山 | 新版原生臣服、政府预算与毁头衔后果迁移中 | 待隔离验证 |
| 驱策朝贡国 | L0、构建、parser GREEN；外置核心后果夹具已准备 | 待隔离验证 |
| 天朝经商贪腐维护版 | 从新原版保留政府机制，只加经商能力；L0 GREEN | 待隔离验证 |
| 自动升级建筑维护版 | 45 项门禁按新版 potential/rite/DLC 迁移；L0 GREEN | 待隔离验证 |
| 牛来 | L0、构建、parser GREEN；生产拒绝/招募 UI 夹具已准备 | 待隔离验证 |
| 天朝特色361制 | 新原版依赖审计无删除；8 组静态 GREEN，既有内容审计一组 RED | 待隔离验证 |

以上是开发兼容工作，不是 Steam Workshop 发布。静态、parser 或版本声明不代替功能实机通过。七语正式翻译和公开发布流程未进入本轮。

## 本机实机记录

原版基线完整 ID：`4-8e1c2f1861--vanilla--R0001`。已成功进入原版大厅、新建 1066 罗贝尔开局、读取暂停 HUD 并保存；`error.log` 和 `gui_warnings.log` 均为空。保存文件 10,935,391 bytes，SHA-256 `a122e52d4339129d692cd1266fe57795d7c509c0274a739b9b8165bf940cdfeb`，副本在 `baseline/vanilla-save/`。该进程已关闭，仅证明新版原版基线，不证明任何 mod 功能。

本机当前可用工具、EXE 与 native 输入按每次启动记录；不把其他机器的已构建 DLL 当作本机准入。没有适配本机新版本的可用 typed 能力时，官方 UI/引擎夹具路径记录实际覆盖及缺口，禁止以旧 RVA 替换哈希冒充新版原生迁移。

外置根目录：`C:/workspace/ck3-upgrade-20261001/`。`new-build/identity.json` 绑定本次游戏；`audits/`、各产品目录绑定原版差异与 L0；`live/<完整ID>/` 保留 raw PNG、坐标换算回执、独立 userdir、生产 staging、游戏日志和启动身份。所有失败 attempt 与过程素材保留。

源码工作包按必要验证后逐包提交推送。报告后续追加实际功能结果、修复和最终主线身份，不把待验项目填成 GREEN。
