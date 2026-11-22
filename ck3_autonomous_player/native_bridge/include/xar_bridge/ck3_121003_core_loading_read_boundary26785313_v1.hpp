#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include "xar_bridge/main_thread_timeline_policy_v1.hpp"
namespace xar::ck3_121003::build26785313 {
// Only the already registered current Core-only read may reject its stale
// result without poisoning the process during loading. This grants no success,
// new source, control callback, old failure reset, or frontend transition right.
inline bool IsCurrentCoreLoadingRead267V1(const ck3_11906::MainThreadQueryMailboxV1&m,
 ck3_11906::MainThreadQueryExecutorV1 executor,const void*context)noexcept{
 if(!context||!m.module_base||executor!=&ExecuteReadonlyOnOwner||executor!=m.permitted_executor||
  !ck3_11906::IsMainThreadTimelineReadExecutorV1(m,executor)||
  m.pump_exact_return_rva!=kPeekReturnRva||m.sdl_poll_event_exact_return_rva!=0||
  m.sdl_poll_event_hook_installed.load(std::memory_order_acquire)||
  !m.iat_hook_installed.load(std::memory_order_acquire))return false;
 if(!m.offline_fixture&&(
  m.peek_message_iat_slot!=reinterpret_cast<void**>(m.module_base+kPeekMessageWIatRva)||!m.original_peek_message||
  m.global_rng_wrapper_slot!=m.module_base+kRngWrapperSlotRva||
  m.jomini_state_slot!=m.module_base+kJominiStateSlotRva||m.game_state_slot!=m.module_base+kGameStateSlotRva||
  m.tls_initialized_flag!=m.module_base+kTlsFlagRva||
  reinterpret_cast<std::uintptr_t>(m.tls_context_getter)!=m.module_base+kTlsGetterRva))return false;
 __try{const auto&q=*static_cast<const ReadonlyContext*>(context);
  return q.mode==ReadonlyModeV1::core_only&&q.mailbox==&m&&q.ticket.sequence&&
   q.ticket.sequence==m.published_sequence.load(std::memory_order_acquire)&&
   q.bindings.exact_image_admitted&&q.bindings.module_base==m.module_base&&
   q.bindings.core.game_state_slot==reinterpret_cast<void**>(m.game_state_slot)&&
   q.bindings.core.jomini_state_slot==reinterpret_cast<void**>(m.jomini_state_slot)&&
   !q.observation.offline_fixture;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
}
