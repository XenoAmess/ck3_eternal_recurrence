#include "xar_bridge/ck3_121003_superman_health26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
namespace xar::ck3_121003::build26785313 {
bool SupermanHealthStepEnabled267V1([[maybe_unused]]const game::AdapterDescriptor&d,[[maybe_unused]]std::string_view step)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_SUPERMAN_HEALTH_V1) && XAR_CK3_ENABLE_121003_26785313_SUPERMAN_HEALTH_V1
 if(!game::IsCk3_121003Core26785313Descriptor(d))return false;
 const auto found=std::find(kSupermanHealthSteps267V1.begin(),kSupermanHealthSteps267V1.end(),step);
 if(found==kSupermanHealthSteps267V1.end())return false;const auto cap=kSupermanHealthCapabilities267V1[static_cast<std::size_t>(found-kSupermanHealthSteps267V1.begin())];
 return std::find(d.capabilities.begin(),d.capabilities.end(),cap)!=d.capabilities.end();
#else
 return false;
#endif
}
std::string DispatchSupermanHealthRequest267V1(const game::GameAdapter&game,std::uint64_t connection,
 std::string_view id,std::string_view step,std::string_view payload,ck3_11906::MainThreadQueryMailboxV1&mailbox){
 SupermanHealthContext267V1 q;q.result.reason="superman_health_request_or_profile_unavailable";
 const auto emit=[&]{return SerializeSupermanHealthResult267V1(id,q.result);};
 if(!ParseSupermanHealthRequest267V1(payload,q.request)||q.request.id()!=id)return emit();
 q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;q.result.phase=q.request.phase;
 const auto index=static_cast<std::size_t>(q.request.action);if(index>=kSupermanHealthSteps267V1.size())return emit();const auto wanted=kSupermanHealthSteps267V1[index];
 if(step!=wanted||!game.enabled()||!connection||!SupermanHealthStepEnabled267V1(game.descriptor(),step)||!game.supports_step(step))return emit();
 auto&retained=RetainedSupermanHealthSession267V1();q.session=&retained;q.connection_generation=connection;q.mailbox=&mailbox;ArmSupermanHealthDeadline267V1(q);
 if(!q.monotonic_deadline_ms){q.result.status=SupermanHealthStatus267V1::expired;q.result.reason="superman_health_original_deadline_expired";return emit();}
 const auto submit=ck3_11906::TrySubmitMainThreadQueryV1(mailbox,&ExecuteSupermanHealthOnOwner267V1,&q,q.ticket);
 if(submit!=ck3_11906::MainThreadQuerySubmitResultV1::submitted){q.result.reason="superman_health_actual_application_owner_not_ready";return emit();}
 auto wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,8000);
 while(wait==ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);
 auto reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);
 while(reclaim==ck3_11906::MainThreadQueryReclaimResultV1::not_terminal){wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);}
 if(wait!=ck3_11906::MainThreadQueryWaitResultV1::completed||reclaim!=ck3_11906::MainThreadQueryReclaimResultV1::reclaimed){
  if(q.result.effect_attempted||q.native_observation_entered)BlockSupermanHealthUnknown267V1(retained);
  q.result.status=(q.result.effect_attempted||q.native_observation_entered)?SupermanHealthStatus267V1::indeterminate:SupermanHealthStatus267V1::unavailable;q.result.reason="superman_health_original_owner_completion_unavailable";
 }return emit();
}
}
