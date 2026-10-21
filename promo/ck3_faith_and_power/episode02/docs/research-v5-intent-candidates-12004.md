# 1.20.0.4 朝圣意图候选：离线原生链

`machine_id: 4-8e1c2f1861`。观察自 2026-10-21T20:09:51Z 开始；EXE 于 20:09:52Z 实际流式重算：101,040,248 B，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本包只读磁盘字节并用 Capstone 反汇编；没有启动 CK3、调用 Native/provider、附加调试器、操作界面或产生媒体。

**已闭合的是候选的读取、过滤和顺序；“共享娱乐是否在更上游自动补入”仍未证明。** 不把用户看见的四选一改判为错误，也不声称第四项对本次人物当前可选。

## 已确认的链

- `window_activity_intent_selection.gui:126` 用 `ActivityIntentSelectionWindow.GetPotentialIntents` 构建 vbox，`:137` 另外调用 `CanPickIntent` 控制按钮 enabled。GUI 在这段没有自行补项或排序。
- `GetPotentialIntents` 字串 RVA `0x457b3d8` 由 SSE 常量复制注册，普通 LEA 字串 xref 为空不能解释成“没有实现”。注册函数 `0x2829e0–0x282b65` 把回调 `0x1665a40` 交给注册器。窗口类名注册 `0x16663e0` 与该组注册器共享类型 ID 存储 RVA `0x5d5814c`。
- 回调 `0x1665a40–0x1665a98` 调用叶函数 `0xc46370`，后者精确 8 字节仅返回 `controller+0xf0` 容器。它包装已有列表，没有在 getter 中枚举或加入共享项。相似的另一组 `0x172d150` 返回 `+0xd0`；不混作此窗口的相同上下文。
- 真实填充函数 `0x16649c0–0x1664e9c`：先将所选活动选项各自 `+0x2e8` 的屏蔽意图合成指针集合；清空候选长度；按活动类型 `+0xd30` 指针数组、`+0xd3c` 长度正向遍历。屏蔽成员被跳过，其余运行意图对象 `+0x40` 的脚本谓词，通过才追加到 `controller+0xf0`。此段保留输入容器顺序，没有结果排序、没有随后追加共享“娱乐”的分支。
- `+0xd30` 的主办列表语义有独立交叉证据：`0x3112120–0x3113fc0` 引用 `activity_type.cpp`，并在 `0x3112f99–0x3113105` 用同一集合检查活动选项屏蔽的主办意图是否合法；失败诊断明确是 “blocking host intent … not a valid host”。宾客分支另取 `+0xd70/+0xd7c`，不能把主办三项外推给宾客。
- 窗口人物 ID 存在 `+0xc8`，初始化 `0x16647c8` 从传入人物对象 ID 读取。候选谓词用此 ID 构造脚本 context；可选性回调 `0x1665b40` 又进入 `0x1664090`，另检查意图 `+0x110` 谓词及需要目标时的合资格目标。因此“在候选列表中”与“CanPick 为真”是两层事实。

## 仍未知的准确边界

本轮没有闭合活动类型主办容器在数据库装载、继承、合并或其他调用者中如何最终形成，因而不能证明全引擎永不补共享项。`+0x40/+0x110` 与源合同 `is_shown/is_valid` 的名称对应是结构和调用分工支持的推断，不冒充已完整逆向其字段解析器。额外 context 的全部命名 scope、缓存全部失效条件及本次四项实际顺序也未取得现场原件。

安装源码 `pilgrimage.txt:2645–2648` 的主办列表显式只有 reflection/altruism/zealot；`shared_intents.txt:3–17` 确有 `reduce_stress_intent`，没有额外 `is_shown` 条件，朝圣 `.6001` 有真实消费者。**这些事实加上 getter 存在，仍不足以证明原生自动将它加入当前四项。** 反之，这次未闭合上游也不能否认用户报告。导演可保留“四选一”的用户观察，并把第四项当前 key/name/CanPick 与运行中完整集合继续标为未读回。

字节、函数边界、源文件 SHA 和分层结论见 [knowledge/pilgrimage-v5-intent-candidates-12004.json](knowledge/pilgrimage-v5-intent-candidates-12004.json)。本包没有扫描旧 R22/R31，没有新增现场证据，也不授予动作或实机资格。
