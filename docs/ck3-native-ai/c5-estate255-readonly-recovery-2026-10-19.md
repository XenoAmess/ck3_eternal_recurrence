# C5 estate255 的只读续行

machine_id: `xenoamess-full-tower-eb9d2c1186`。实际观察时间为2026-10-19 UTC；来源是FROZEN66、CALLBACK-ABSENCE、256/257原响应及其后验文件。

C5 same-Game SEM252/CAP253实际成功后，首AUTO255在0.056209秒报`retained estate differs from the current actor/episode sequence`，未重发。旧estate绑定同actor31254、episode和107日，但public61/native60；新App实际opening为public2/native61。纯invalidator比较跨App的public revision产生误拒。255已完成一次只读campaign-root查询，然后在invalidation guard拒绝；estate assignment/persist、后继retain、before_submit及所选业务dispatch均尚未执行。不能称整条255没有Native读取，不能计完整AUTO99或业务信用。

实际回执563B/SHA`2169d7152cc02bf3b59c39d72f8161fe5c5c5ac151b67bc66f6c537853b93d52`；FROZEN66为6295B/SHA`2596ab289cc30be4befedb33d80ae653b406b69c10ac9d441aa96a4b498f90b8`。M3审精确SRC04调用顺序：原`Driver.execute_step`先记录成功root history，Service完成独立postframe核验后才调用纯invalidator；普通`_prepare_succession_transition_v1`可验证同frame root history，通过原`_planning_root_result`路径避免再次触发fresh-root invalidation，然后用完整当前bundle严格retain。该复用仍由原Frame/actor/episode校验决定，不能假定缓存永远有效。

直接发送PLAN256会被原Clean Queue的halt守卫拒绝。Root明确授权[有限256叶](../../tools/g2_saved_campaign/c5_estate255_predispatch_clear_v1.py)经既有动态`clear_zero_rpc_preflight_rejection`入口，严格绑定上述原件、C5 warm252/253与actualGame出生代、98周期/pending99/AUTO255、实际callback缺失及已审source contract；0RPC仅清已证未提交的pending和halt，estate字段完全不动。T0、107日、lastSaved61、dirtytrue及所有原计数保持。随后257使用原正常`ck3_plan_turn`空参数路径；失败或frame/episode变化时保真halt，不继续AUTO，不放松estate guard，也不重255或重启App/Game/OBS。

[资格producer](../../tools/g2_saved_campaign/prepare_c5_estate255_predispatch_v1.py)实际组合C5 `run_request_loop`、warm→Clean→Cold的原`check_before/call/check_after`及`consume/persist`。它先证明原halt拒直接PLAN，再验证256只变pending字段、0RPC，然后正常257 mock PLAN一调用；mock不声称实际estate已刷新。unknown原件、错误pending及错误Game出生代均在写入/consume前拒绝。[冻结软件与实际证据](evidence/c5-estate255-readonly-recovery01.json)分列这些范围。

runtime随后实际256成功，0RPC、NEXT257、pendingnull、98计数；实际257正常PLAN成功0.051144秒，14096B/SHA`82c89a260d19eaf9d951696a230ac31d096b8c1cae3022f8c3d2d3aa08b0df58`，native61/public2/NEXT258，原255错误保留。后续普通FULL258由唯一runtime执行，本包未新增AUTO或游戏日信用。永久跨SDK revision-domain修复由M3负责，本次没有热改冻结SRC04 SDK。

原失败和恢复review在本次维护闭场后7日复核；遵统一存储策略，不额外复制大Driver/SAVE，不无限保留派生副本。
