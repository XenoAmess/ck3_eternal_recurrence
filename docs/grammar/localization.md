# 本地化（localization）语法

## yml 文件

```yml
﻿l_simp_chinese:
 key:0 "文本"
```

- 必须 UTF-8 **带 BOM**，否则 `Missing UTF8 BOM` 且文件不加载
- 头行 `l_<语言>:`（l_english / l_simp_chinese）
- 键格式 `key:0`（:0 是版本号，惯例）
- 目录：`localization/<语言>/`

## 语言回退规则（实测重要）

- 普通 loc：当前语言缺键 → 回退英文 ✅
- **customizable_localization 引用的键：当前语言必须存在**（parse 校验不吃英文回退，`Missing loc key ... for custom localization`）——所以被 custom loc / GUI `Localize()` 引用的键要在每种语言里都定义
- **customizable_localization 的键本身：用于事件选项名时，当前语言 yml 里也要有静态条目**（否则 `Unrecognized loc key` 且运行期显示 raw key；custom loc 仍会覆盖该静态条目）

## 事件文本中显示动态值

事件 `immediate` 里保存，desc 里显示：

```
# 脚本侧
save_scope_value_as = {
	name = xar_score
	value = global_var:xa_run_score      # 注意：必须用 save_scope_value_as，见下文坑
}

# loc 侧
xar.1001.desc:0 "当局分数：[TopScope.GetValue('xar_score')]"
```

格式修饰：`|+0` 带符号显示（差值用）。

## customizable_localization（自定义本地化）

按条件返回不同 loc 键，`text` 块**按序取第一个 trigger 成立的**（first_valid）：

```
xar_record_level = {
	type = character
	text = {
		trigger = { is_tutorial_lesson_completed = xar_hs_ge_100 }
		localization_key = xar_rec_100
	}
	text = { localization_key = xar_rec_0 }    # 兜底
}
```

- trigger 里可以用 **interface trigger**（如 `is_tutorial_lesson_completed`）——这是它在游戏状态脚本里禁用时的合法使用点
- GUI 读取：`GetPlayer.Custom('xar_record_level')` 返回解析后的文本
- 多语言键校验见上文

## 坑

- 文本内容含 `[...]` 会被当 loc 命令解析：内容 `XAR_SYNC_SENTINEL` 正常， `[XAR_SYNC]` 显示为 `ERROR:[XAR_SYNC]`。**哨兵/标记文本不要带方括号**
