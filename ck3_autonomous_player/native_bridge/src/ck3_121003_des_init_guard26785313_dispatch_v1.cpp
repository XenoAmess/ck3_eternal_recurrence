#include "xar_bridge/ck3_121003_des_init_guard26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
namespace xar::ck3_121003::build26785313 {
bool DesInitGuardStepEnabled267V1([[maybe_unused]]const game::AdapterDescriptor&d,[[maybe_unused]]std::string_view step)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_DES_INIT_GUARD_V1) && XAR_CK3_ENABLE_121003_26785313_DES_INIT_GUARD_V1
 if(!game::IsCk3_121003Core26785313Descriptor(d))return false;
 if(step!=kDesInitGuardStep267V1)return false;
 return std::find(d.capabilities.begin(),d.capabilities.end(),kDesInitGuardCapability267V1)!=d.capabilities.end();
#else
 return false;
#endif
}
std::string DispatchDesInitGuardRequest267V1(const game::GameAdapter&game,std::uint64_t connection,
 std::string_view id,std::string_view step,std::string_view payload,ck3_11906::MainThreadQueryMailboxV1&mailbox){
 DesInitGuardContext267V1 q;q.result.reason="des_init_guard_request_or_profile_unavailable";
 const auto emit=[&]{return SerializeDesInitGuardResult267V1(id,q.result);};
 if(!ParseDesInitGuardRequest267V1(payload,q.request)||q.request.id()!=id)return emit();
 const auto wanted=std::string_view{kDesInitGuardStep267V1};
 if(step!=wanted||!game.enabled()||!connection||!DesInitGuardStepEnabled267V1(game.descriptor(),step)||!game.supports_step(step))return emit();
 auto&retained=RetainedDesInitGuardSession267V1();q.session=&retained;q.connection_generation=connection;q.mailbox=&mailbox;ArmDesInitGuardDeadline267V1(q);
 if(!q.monotonic_deadline_ms){q.result.status=DesInitGuardStatus267V1::expired;q.result.reason="des_init_guard_original_deadline_expired";return emit();}
 const auto submit=ck3_11906::TrySubmitMainThreadQueryV1(mailbox,&ExecuteDesInitGuardOnOwner267V1,&q,q.ticket);
 if(submit!=ck3_11906::MainThreadQuerySubmitResultV1::submitted){q.result.reason="des_init_guard_actual_application_owner_not_ready";return emit();}
 auto wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,8000);
 while(wait==ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);
 auto reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);
 while(reclaim==ck3_11906::MainThreadQueryReclaimResultV1::not_terminal){wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);}
 if(wait!=ck3_11906::MainThreadQueryWaitResultV1::completed||reclaim!=ck3_11906::MainThreadQueryReclaimResultV1::reclaimed){
  if(q.native_observation_entered)BlockDesInitGuardUnknown267V1(retained);
  q.result.status=q.native_observation_entered?DesInitGuardStatus267V1::indeterminate:DesInitGuardStatus267V1::unavailable;q.result.reason="des_init_guard_original_owner_completion_unavailable";
 }return emit();
}
}
