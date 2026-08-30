# 国际化翻译工作流

## 开发阶段策略

- 日常功能开发只创作、修改和审阅简体中文与英文。简体中文是琉焰卿人格和世界观语义的主要基准，英文是共同校对基准。
- 当前目录结构支持简体中文、英文、法文、德文、日文、韩文、波兰文、俄文和西班牙文。发布前的目标语言集合必须以当时实际目录和加载规则重新检查，不可只依赖这份列表。
- 用户明确表示“要发布了”或给出等价发布指令之前，不主动翻译或润色其余七种语言，也不执行或宣称完成发布级国际化验收。
- 如果生成器或 CK3 的加载规则要求九语言结构完整，可以用已审阅英文作为非中英文语言的临时占位。占位只用于保持 key、custom localization 和文件结构可加载，不算目标语言翻译。
- 日常仍运行项目既有静态检查，避免 BOM、缺 key、custom localization 和文件语法损坏；这类结构检查不能替代发布时的翻译完整性和语义审计。

## 发布触发条件

只有用户明确要求发布后，才执行以下国际化流程。未收到发布指令时，不得把七种外语占位列为当前功能开发阻塞，也不得擅自发起批量翻译。

普通 push/PR 的 CI 只运行本地化解析、键结构、BOM、生成器和调用器离线合同；不得运行会把七语候选升级为阻塞项的正式
release-localization audit。该 audit 只允许在明确的 ZhongGuo 发布 tag 或人工 release workflow dispatch 中执行。历史版本已经
留下 audit snapshot 时，开发中的中英增量可以暂时使它落后；等所有者明确进入发布阶段后，再集中翻译、重建 snapshot 并验收。

## 一、检查环境与项目

1. 检查环境变量 `MINIMAX_API_KEY` 是否存在。
2. 只能判断它是否已配置，严禁在终端输出、日志、代码、报错信息、artifact 或最终回复中泄露 API Key。
3. 如果变量不存在，立即停止。不要编造 Key，不要开始翻译，也不要修改项目；明确告诉用户需要配置 `MINIMAX_API_KEY`。
4. 检查项目现有国际化目录、语言文件、命名规则和加载方式，重新确定：
   - 基准语言；
   - 已支持语言；
   - 各语言缺少的 key；
   - 哪些英文占位或新增文案确实需要翻译。
5. 修改前阅读 `AGENTS.md`、README、贡献指南、`docs/grammar/localization.md`、相关生成器和本工作流，遵守当时的项目规范。

安全的存在性检查只能输出状态，例如 PowerShell：

```powershell
if ($env:MINIMAX_API_KEY) { "configured" } else { "missing" }
```

不得运行会展开或打印变量值的命令。

## 二、MiniMax 的职责边界

MiniMax-M3 只能承担低风险、机械性的翻译工作。

允许 MiniMax 完成：

- 把已经确定的源文案翻译为指定语言；
- 在不改变语义的情况下给出简短的本地化 UI 文案；
- 按指定 JSON schema 返回批量翻译结果。

严禁 MiniMax 完成：

- 编写、修改或审查任何代码；
- 分析项目结构或决定修改哪些文件；
- 设计国际化方案；
- 推断业务逻辑；
- 决定 key 名称；
- 直接操作文件；
- 生成 shell 命令、正则表达式、脚本或配置；
- 判断最终修改是否正确或是否通过验收。

所有代码、脚本、文件修改、差异检查和验收必须由当前执行者亲自完成。即使 MiniMax 主动输出代码，也不得写入项目。

## 三、调用方式

### 仓库复用状态

截至 2026-08-27，仓库此前已经沉淀了 MiniMax 的职责边界、请求格式和发布审核记录，但历史提交中没有受版本
控制的通用调用器；过去的翻译调用属于一次性执行，不能作为可复现工具链继续调用。现已统一为
`tools/translate_localization_minimax.py` 与 `tools/test_translate_localization_minimax.py`：以后任何 mod 都复用这一个
只读候选生成入口，不再为单个产品复制临时请求脚本。

使用环境变量中的 `MINIMAX_API_KEY` 调用：

- 模型：`MiniMax-M3`
- Anthropic 兼容地址：`https://api.minimaxi.com/anthropic`
- OpenAI 兼容地址：`https://api.minimaxi.com/v1`

可以自行选择 Python、Node.js 或 `curl`。优先复用项目已有依赖；没有必要时，不为翻译任务增加永久依赖。

仓库内 CK3 本地化优先复用 `tools/translate_localization_minimax.py`。它读取调用者明确指定的基准/参考 yml，
只向 MiniMax-M3 发送 key-value、目标语言、短语境与自动提取的保护 token；每种语言最多重试两次，拒绝
非单一严格 JSON、重复 key、key 集合异常和 token 漂移。调用使用 MiniMax-M3 当前接口的
`max_completion_tokens` 并关闭 adaptive thinking，不依赖该接口不支持的 JSON schema 模式。工具只向标准输出
返回候选 JSON，**不会写入 yml**；
候选仍必须由当前执行者亲自审阅并用正常文件编辑流程落盘。示例：

```powershell
py tools/translate_localization_minimax.py `
  --source path/to/source_l_english.yml --source-language English `
  --reference path/to/source_l_simp_chinese.yml --reference-language "Simplified Chinese" `
  --target french="French (France)" --context "Short, task-specific UI context" `
  --key first_key --key second_key --protect "Product Name"
```

`--key` 用于由调用者选择最小必要的小批次；不传时才翻译源文件全部 key。`--protect` 可重复传入必须逐字保留的
品牌名或项目术语。工具自动保护 CK3 scope、scripted loc、图标、格式标记、换行与常见占位符；极少出现的嵌套
ICU plural/select 块会整块逐字保护，若块内自然语言也必须翻译，应退出自动调用并人工处理，不能冒险改坏结构。

临时调用脚本必须满足：

- 只负责组织翻译请求、调用接口和解析响应；
- API Key 只从环境变量读取；
- 不硬编码、不打印 API Key；
- 不混入正式业务代码；
- 除非具有明确长期价值，否则任务完成后不纳入最终修改。

Anthropic 兼容调用示例：

```bash
curl https://api.minimaxi.com/anthropic/v1/messages \
  -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-M3",
    "max_tokens": 2000,
    "messages": [
      {
        "role": "user",
        "content": "Translate the supplied localization entries and return only valid JSON."
      }
    ]
  }'
```

示例仅说明请求结构。实际执行时仍不得让命令、trace、异常或调试输出泄露环境变量值。

## 四、发送给 MiniMax 的任务

不得发送整个代码库、完整源文件或无关上下文。每次只提供完成该批翻译所必需的信息：

- 源语言；
- 目标语言及地区；
- 待翻译的 key-value 列表；
- 必须原样保留的占位符和专有名词；
- 必要的简短业务语境；
- 严格的 JSON 输出格式。

标准提示词：

```text
你只负责翻译，不要编写代码，不要解释，不要添加或删除条目。

源语言：{source_language}
目标语言：{target_language}

要求：
1. 只翻译 JSON 中的字符串值，不修改 key。
2. 保持原意、语气和产品界面风格。
3. 原样保留所有占位符、变量、转义符、HTML/Markdown 标记和特殊符号。
4. 不翻译指定的品牌名、产品名、协议名和技术标识符。
5. 不合并、不拆分、不新增、不删除任何条目。
6. 仅返回合法 JSON，不要使用 Markdown 代码块，不要附带解释。

必须原样保留：
{protected_tokens}

待翻译内容：
{json_payload}
```

使用小批次调用，避免上下文过长导致漏项、串行或格式损坏。接口失败时只做有限次数重试，不得无限重试。

## 五、翻译与文件修改规则

1. 只补充确实缺失或仍为英文占位的目标语言翻译，不无故重写已有文案。
2. 不修改现有 key、层级结构、文件格式、排序和编码方式。
3. 必须原样保留：
   - `{name}`、`${name}`、`{{name}}`、`%s`、`%d` 等变量；
   - ICU MessageFormat 的 plural/select 结构；
   - HTML、Markdown、XML 标签；
   - `\n`、引号、反斜杠和其他转义字符；
   - URL、命令、路径、代码片段和技术标识符；
   - 品牌名、产品名及项目约定不翻译的专有名词。
4. 文案应符合目标语言的自然表达和 UI 习惯，不逐字硬译。
5. 同一术语在同一语言中必须保持一致。
6. 不借机重构国际化系统或修改无关代码。
7. 源文案存在歧义时，先根据项目上下文自行判断。无法可靠判断且选择会明显改变含义时，向用户提问，不得让 MiniMax 自行猜测。
8. 所有 CK3 `.yml` 必须保持 UTF-8 BOM；customizable localization 的当前语言 key、普通 wrapper key 和动态 resolver 规则继续遵守 `docs/grammar/localization.md`。

## 六、审计要求

MiniMax 输出一律视为不可信输入，不得未经检查直接写入项目。当前执行者必须亲自检查：

- 响应是否为合法、可解析的数据；
- 返回 key 集合是否与请求完全一致；
- 是否有缺失、重复、新增或被篡改的 key；
- 占位符、变量、标签和转义符是否与源文案一致；
- 是否夹带解释、Markdown、代码或无关内容；
- 是否误译品牌、技术名词、快捷键、路径或命令；
- 是否有明显语义错误、语气不一致或不适合 UI 的冗长表达；
- 同一语言的术语是否前后一致；
- 文件语法、BOM、排序和格式是否符合项目规范。

对于当前执行者能够理解的语言，必须逐条审阅并修正语义。对于无法可靠审阅的语言，也至少完成结构、占位符、格式、条目数量、专有名词和异常输出检查，并在最终报告中明确标注只完成结构审计、未完成母语级语义审计。

再次询问同一个 MiniMax 模型不算独立验证，也不得用来替代人工或其他独立检查。

## 七、验证与交付

修改完成后：

1. 重新比较所有语言文件与基准语言，确认目标语言不再缺 key 或英文占位。
2. 运行项目已有的国际化校验、静态校验、格式检查和相关测试，至少包括：

```powershell
py tools/validate_static.py
py tools/build_release.py --check
```

3. 如果当时没有对应自动检查，至少自行验证：
   - 所有语言文件可正常解析；
   - key 结构正确；
   - 占位符集合与基准文案一致；
   - 没有修改无关文件；
   - `git diff` 不含 API Key、临时调试内容或 MiniMax 的无关输出。
4. 不得为了通过测试删除或弱化已有校验。
5. 测试失败时，区分本次修改引入的问题与已有问题，不得隐瞒。
6. 按 `docs/release-qa-v1.0.0.md` 完成目标语言的人工术语、人格和游戏内截断签核；结构通过不能冒充母语级审核。

最终回复必须简洁说明：

- 补全了哪些语言；
- 新增了多少条翻译；
- 修改了哪些文件；
- MiniMax 实际承担了什么工作；
- 完成了哪些人工和自动化审计；
- 执行了哪些测试及结果；
- 哪些语言未完成充分的语义审计；
- 是否仍有歧义、风险或待人工确认项。

最终回复不得展示或暗示 API Key 的具体内容。
