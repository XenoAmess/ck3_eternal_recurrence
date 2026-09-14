# active-scheme native command adapter v1（private）

状态：`static-ready private adapter`。本合同堆叠在 SCHEME5
`871daea905f67939760e050146cb022472af777a`，只为
`ActiveSchemeSemanticActionV1PrivateAccess.submit` 提供 exact-build native adapter。
它没有接入 shared heartbeat/bridge/schema/MCP，也没有启动 CK3；fixture GREEN 不能写成
production-live action。

## exact-build 门

版本固定为 CK3 `1.19.0.6`，`ck3.exe` SHA-256 固定为
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
bind 时逐字节读取并核对以下完整指令前缀；任一不符都不安装 submit callback：

| seam | RVA | prefix bytes |
| --- | ---: | ---: |
| construct character-interaction context | `0x2C3EE50` | 39 |
| validate character-interaction context | `0x2C43F00` | 29 |
| construct send-character-interaction command | `0x26B3220` | 39 |
| submit command | `0x0973E00` | 39 |
| destroy character-interaction context | `0x2C3F380` | 38 |

其中 validator 与 send-command constructor 来自冻结的
`scheme_state_1_19_0_6@a5438595` action reuse evidence；其余三个前缀从同一 SHA 的本机
exact executable 直接读取，用于本 private adapter 的 route/lifetime 门。构造后的 command
还必须 round-trip 为 primary vtable `module+0x40829F8`、secondary vtable
`module+0x40829C8`。

## 不猜 interaction offset

现有冻结证据没有给出 `sway_interaction`、`start_murder_interaction` 在 character-interaction
database 中的固定偏移。本 adapter 因此没有硬编码这两个偏移，也不扫描猜测布局。shared
glue 必须提供按完整稳定 key 解析的 callback，并返回：

- interaction key 与推导出的 `sway`/`murder` type round-trip；
- 非零 stable-key hash、definition generation 与 transaction proof epoch；
- actor/target 的完整 generation-bearing CharacterID、slot index、generation 和 native
  identity round-trip；
- command manager identity/generation，以及 submitter 地址等于 exact-build submit seam。

bind 还要求 evidence revision 与四个外部 proof gate：稳定 key lookup、完整 character
identity/generation、starter package encoding、command-copy lifetime。缺任何一项都保持不可绑定。

## 单次 native transaction

SCHEME5 完成双次 semantic precondition 读取后才调用 adapter。adapter 的一次 callback 内：

1. 解析 actor、target、interaction definition 与 command manager，要求同一个非零 proof
   epoch；CharacterID 的高 8 位 generation 和低 24 位 slot 必须分别 round-trip。
2. 构造 character-interaction context。sway 必须没有 starter option；murder 必须把
   `agent_focus_balance/success/speed/secrecy` 之一 round-trip 为四项互斥 option。
3. 使用 exact validator 重验 context，并核对 validator address、context identity、generation
   与 proof epoch。
4. 提交前重新解析 actor、target、definition 与 command manager。地址、完整 identity、
   generation、stable hash 与 proof epoch 任一漂移即停止，且 native submit 次数为零。
5. 构造 send command，核对 constructor address、双 vtable、复制 context 的 generation、
   actor/target 与 interaction hash。
6. 只以 channel `0x0E` 调用一次 native submit；无重试。随后按 native 所有权顺序释放 command
   内复制 context 与原 context。

adapter 返回 true 只让 SCHEME5 生成 `submitted_verification_pending` ACK。它不生成 applied
receipt；最终成功仍必须由 SCHEME5 自行 fresh SCHEME4 reread，观察到新的唯一
owner/type/target 匹配 instance。任何 identity/generation/proof/signature 失败都会在 submit
前 fail-closed；native submit 返回 false 时同一事务也不重试。

## 仍需完成

- shared owning-thread glue 要用现有 exact-build `Bindings` 提供本 adapter 的 callback，特别是
  按 stable key 查找 sway/murder definition；未闭合前不得用固定数据库偏移替代。
- `scheme-start-preview-v1` 生产 reader 必须提供 SCHEME5 的 shown/valid/
  `can_start_scheme` 与 starter option precondition callback。
- paused sway 与 paused murder 各需一次真实 submit + fresh active-instance receipt；在这两项
  live artifact 完成前保持 static-ready。
