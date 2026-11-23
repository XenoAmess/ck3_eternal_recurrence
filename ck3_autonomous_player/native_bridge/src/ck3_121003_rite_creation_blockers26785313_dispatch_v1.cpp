#include "xar_bridge/ck3_121003_rite_creation_blockers26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
namespace xar::ck3_121003::build26785313 {
bool RiteBlockersStepEnabled267V1([[maybe_unused]]const game::AdapterDescriptor&d,[[maybe_unused]]std::string_view step)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_CREATION_BLOCKERS_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_CREATION_BLOCKERS_V1
 if(!game::IsCk3_121003Core26785313Descriptor(d))return false;
 if(step!=kRiteBlockersStep267V1)return false;
 return std::find(d.capabilities.begin(),d.capabilities.end(),kRiteBlockersCapability267V1)!=d.capabilities.end();
#else
 return false;
#endif
}
std::string DispatchRiteBlockersRequest267V1(const game::GameAdapter&game,std::uint64_t connection,
 std::string_view id,std::string_view step,std::string_view payload,ck3_11906::MainThreadQueryMailboxV1&mailbox){
 RiteBlockersContext267V1 q;q.result.reason="rite_creation_blockers_request_or_profile_unavailable";
 const auto emit=[&]{return SerializeRiteBlockersResult267V1(id,q.result);};
 if(!ParseRiteBlockersRequest267V1(payload,q.request)||q.request.id()!=id)return emit();
 const auto wanted=std::string_view{kRiteBlockersStep267V1};
 if(step!=wanted||!game.enabled()||!connection||!RiteBlockersStepEnabled267V1(game.descriptor(),step)||!game.supports_step(step))return emit();
 auto&retained=RetainedRiteBlockersSession267V1();q.session=&retained;q.connection_generation=connection;q.mailbox=&mailbox;ArmRiteBlockersDeadline267V1(q);
 if(!q.monotonic_deadline_ms){q.result.status=RiteBlockersStatus267V1::expired;q.result.reason="rite_creation_blockers_original_deadline_expired";return emit();}
 const auto submit=ck3_11906::TrySubmitMainThreadQueryV1(mailbox,&ExecuteRiteBlockersOnOwner267V1,&q,q.ticket);
 if(submit!=ck3_11906::MainThreadQuerySubmitResultV1::submitted){q.result.reason="rite_creation_blockers_actual_application_owner_not_ready";return emit();}
 auto wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,8000);
 while(wait==ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);
 auto reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);
 while(reclaim==ck3_11906::MainThreadQueryReclaimResultV1::not_terminal){wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);}
 if(wait!=ck3_11906::MainThreadQueryWaitResultV1::completed||reclaim!=ck3_11906::MainThreadQueryReclaimResultV1::reclaimed){
  if(q.native_observation_entered)BlockRiteBlockersUnknown267V1(retained);
  q.result.status=q.native_observation_entered?RiteBlockersStatus267V1::indeterminate:RiteBlockersStatus267V1::unavailable;q.result.reason="rite_creation_blockers_original_owner_completion_unavailable";
 }return emit();
}
}
