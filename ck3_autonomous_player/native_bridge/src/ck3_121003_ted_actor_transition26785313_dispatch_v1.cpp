#include "xar_bridge/ck3_121003_ted_actor_transition26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
namespace xar::ck3_121003::build26785313 {
bool TedTransitionStepEnabled267V1([[maybe_unused]]const game::AdapterDescriptor&d,[[maybe_unused]]std::string_view step)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1
 if(!game::IsCk3_121003Core26785313Descriptor(d))return false;
 const auto found=std::find(kTedTransitionSteps267V1.begin(),kTedTransitionSteps267V1.end(),step);if(found==kTedTransitionSteps267V1.end())return false;
 const auto n=static_cast<std::size_t>(found-kTedTransitionSteps267V1.begin());const auto cap=kTedTransitionCapabilities267V1[n==0||n==2?0:n==1?1:2];
 return std::find(d.capabilities.begin(),d.capabilities.end(),cap)!=d.capabilities.end();
#else
 return false;
#endif
}
std::string DispatchTedTransitionRequest267V1(const game::GameAdapter&game,std::uint64_t connection,std::string_view id,std::string_view step,std::string_view payload,ck3_11906::MainThreadQueryMailboxV1&mailbox){
 TedTransitionContext267V1 q;q.result.request_id=std::string(id);q.result.reason="ted_request_or_profile_unavailable";const auto emit=[&]{return SerializeTedTransitionResult267V1(id,q.result);};
 if(!ParseTedTransitionRequest267V1(payload,q.request)||std::string_view(q.request.request_id.data(),q.request.request_id_size)!=id)return emit();
 q.result.action=q.request.action;q.result.request_id=std::string(id);q.result.operation_id=std::string(q.request.operation_id.data(),q.request.operation_id_size);q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;q.result.actor_epoch=q.request.actor_epoch;q.result.deadline_unix_ms=q.request.deadline_unix_ms;
 const auto n=static_cast<unsigned>(q.request.action);if(n>=kTedTransitionSteps267V1.size()||step!=kTedTransitionSteps267V1[n]||!game.enabled()||!connection||!TedTransitionStepEnabled267V1(game.descriptor(),step)||!game.supports_step(step))return emit();
 auto&retained=RetainedTedTransitionSession267V1();q.session=&retained;q.mailbox=&mailbox;q.connection_generation=connection;
 if(q.request.action==TedTransitionAction267V1::query_operation){q.result=QueryTedTransitionOperation267V1(retained,q.request,connection);return emit();}
 ArmTedTransitionDeadline267V1(q);if(!q.monotonic_deadline_ms){q.result.status=TedTransitionStatus267V1::expired;q.result.reason="ted_original_deadline_expired";return emit();}
 const auto submit=ck3_11906::TrySubmitMainThreadQueryV1(mailbox,&ExecuteTedTransitionOnOwner267V1,&q,q.ticket);if(submit!=ck3_11906::MainThreadQuerySubmitResultV1::submitted){q.result.reason="ted_actual_application_owner_not_ready";return emit();}
 auto wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,8000);while(wait==ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);
 auto reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);while(reclaim==ck3_11906::MainThreadQueryReclaimResultV1::not_terminal){wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);}
 if(wait!=ck3_11906::MainThreadQueryWaitResultV1::completed||reclaim!=ck3_11906::MainThreadQueryReclaimResultV1::reclaimed){if(q.native_observation_entered||q.result.claim_sequence||q.result.effect_attempted){BlockTedTransitionUnknown267V1(retained);q.result.status=TedTransitionStatus267V1::indeterminate;q.result.cleanup_known=false;}else q.result.status=TedTransitionStatus267V1::unavailable;q.result.source_available=false;q.result.source.reset();q.result.reason="ted_original_owner_completion_unavailable";}
 return emit();
}
}
