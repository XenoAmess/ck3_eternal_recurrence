# 礼仪详情的“无”与教义图标修订

machine_id: `desktop-3fevhd2-1c74096080`。观察于2026-10-25T19:05–19:35Z；安装CK3 1.20.0.4。源提交 `6d38eadf8a4a48688835cbb41035d877bb3f4540`。

R0018实际详情截图仍显示完整“宗族化：无”卡片。教义已经设置 `visible = no`，但原版 `game/gui/window_faith.gui` 第3361行的实例只排除三项信仰领袖教义，没有读取 `DoctrineType.IsVisible`。同文件第3348行的容器已有 `ignoreinvisible = yes`。原版文件150,682 B，SHA `67924e58ccba26d95853ac48af35d91a774f5ce6d2e7f32a0a033de3b9d51521`。

修订仅给该实例的原条件加 `And( DoctrineType.IsVisible, ... )`；正式包提供同路径完整GUI文件，因为另建重复命名类型的替换／加载顺序没有已资格化的合同。原版内容只变一条逻辑行，另含既有Java校验所需UTF-8 BOM。编辑器及 `is_shown = { always = yes }` 不变。原版 `window_knights.gui` 也使用同一getter。需要在新场验证“无”卡片与空白行消失、宗族化卡片仍显示、创建与编辑仍能选两项。

这会覆盖 `gui/window_faith.gui`，与其他覆盖此文件的UI模组组合时需要合并这一条条件。升级游戏版本时应重新基于对应原版文件合并；没有覆盖shader或其他GUI文件。最终连同帝国领袖与纹章后的开发清单35文件、正式九语清单56文件；仅GUI修订时为32／53文件，历史31／52文件回执不改写。

用户实际截图同时否决了金红图标。替代资产按原版黑RGB＋透明alpha格式重做，由原版着色链提供颜色。完整来源、提示词和配方见[图标记录](artwork.md)。新图及GUI修订尚未实机验收。

R0018还在真正创建操作之后出现了Root调用错误：查询事件上下文时漏传必须来自当前snapshot的 `event_instance_id`，SDK校验拒绝，宿主保留RED并自动经共享typed Quit退出。实际Game原保留句柄退出0、host原进程1、公共run／verify均2、keeper／allocator均0，SCREEN9024释放；共享后继清理消费者返回 `previous-shared-managed-session`，只证明清理结束。`normal_close_qualified=false`、`business_pass=false`、核心正式签署0/6保持。没有D0／+1／+2创建后保存，不能据提交回执宣称复用成功，也不能把调用错误归为模组缺陷。

R0018保留了创建前baseline与取消后两份完整SDK保存。独立基线观察确认原D174与H174族长都是玩家31254，D174原纹章1781的完整AST已保全；H174没有自有纹章字段。该缺失须原样保留。启动日志20条重复诊断对应10项unused审计字段，未观察到unknown keyword、非法scope或解析拒绝；这不等于error.log为空。

外置实际证据在 `C:/ck3-dynastic-esotericism-20261024/resume-product-a20/`：`operations-core-a38/R0018-CLOSURE.actual.json`（4,294 B，SHA `607b346c662fdc455cd07c61c63ec031e3b73498807b54fd5922d8b9deb3cd1e`）、`operator-reference/none-visible-r18-fix-a01/SOURCE-AND-CHECKS.json`，以及R0018的 `operator-evidence/r18-none-details-desktop-a01.png`（1,496,885 B，SHA `efd590684f1df77686fcea08bbfc55cda1100c687e22b408ba8862c6b4c50628`）。保留原始失败，不改写冻结场次或其源码。
