#include "xar_bridge/ck3_121003_ccc_actor_transition26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
namespace xar::ck3_121003::build26785313 {
bool CccTransitionStepEnabled267V1([[maybe_unused]]const game::AdapterDescriptor&d,[[maybe_unused]]std::string_view step)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1
 if(!game::IsCk3_121003Core26785313Descriptor(d))return false;
 const auto found=std::find(kCccTransitionSteps267V1.begin(),kCccTransitionSteps267V1.end(),step);if(found==kCccTransitionSteps267V1.end())return false;
 const auto n=static_cast<std::size_t>(found-kCccTransitionSteps267V1.begin());const auto cap=kCccTransitionCapabilities267V1[n==0||n==2?0:n==1?1:2];
 return std::find(d.capabilities.begin(),d.capabilities.end(),cap)!=d.capabilities.end();
#else
 return false;
#endif
}
std::string DispatchCccTransitionRequest267V1(const game::GameAdapter&game,std::uint64_t connection,std::string_view id,std::string_view step,std::string_view payload,ck3_11906::MainThreadQueryMailboxV1&mailbox){
 CccTransitionContext267V1 q;q.result.request_id=std::string(id);q.result.reason="ccc_request_or_profile_unavailable";const auto emit=[&]{return SerializeCccTransitionResult267V1(id,q.result);};
 if(!ParseCccTransitionRequest267V1(payload,q.request)||std::string_view(q.request.request_id.data(),q.request.request_id_size)!=id)return emit();
 q.result.action=q.request.action;q.result.request_id=std::string(id);q.result.operation_id=std::string(q.request.operation_id.data(),q.request.operation_id_size);q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;q.result.actor_epoch=q.request.actor_epoch;q.result.deadline_unix_ms=q.request.deadline_unix_ms;
 const auto n=static_cast<unsigned>(q.request.action);if(n>=kCccTransitionSteps267V1.size()||step!=kCccTransitionSteps267V1[n]||!game.enabled()||!connection||!CccTransitionStepEnabled267V1(game.descriptor(),step)||!game.supports_step(step))return emit();
 auto&retained=RetainedCccTransitionSession267V1();q.session=&retained;q.mailbox=&mailbox;q.connection_generation=connection;
 if(q.request.action==CccTransitionAction267V1::query_operation){q.result=QueryCccTransitionOperation267V1(retained,q.request,connection,&q.deferred_observation_only);
  const auto&p=q.result.progress;if(!q.deferred_observation_only||q.result.status!=CccTransitionStatus267V1::running||q.result.actor_epoch||!p||!p->exact_day_confirmed||p->transition_pending||p->before_actor_id!=p->after_actor_id)return emit();
  q.deferred_observation_only=true;
 }
 ArmCccTransitionDeadline267V1(q);if(!q.monotonic_deadline_ms){if(q.deferred_observation_only){BlockCccTransitionUnknown267V1(retained);q.result.status=CccTransitionStatus267V1::indeterminate;q.result.reason="ccc_original_deferred_deadline_expired_no_new_permission";}else{q.result.status=CccTransitionStatus267V1::expired;q.result.reason="ccc_original_deadline_expired";}return emit();}
 const auto submit=ck3_11906::TrySubmitMainThreadQueryV1(mailbox,&ExecuteCccOnOwner267V1,&q.invocation,q.ticket);if(submit!=ck3_11906::MainThreadQuerySubmitResultV1::submitted){q.result.reason="ccc_actual_application_owner_not_ready";return emit();}
 auto wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,8000);while(wait==ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);
 auto reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);while(reclaim==ck3_11906::MainThreadQueryReclaimResultV1::not_terminal){wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);}
 if(wait!=ck3_11906::MainThreadQueryWaitResultV1::completed||reclaim!=ck3_11906::MainThreadQueryReclaimResultV1::reclaimed){if(q.native_observation_entered||q.result.claim_sequence||q.result.effect_attempted){BlockCccTransitionUnknown267V1(retained);q.result.status=CccTransitionStatus267V1::indeterminate;q.result.cleanup_known=false;}else q.result.status=CccTransitionStatus267V1::unavailable;q.result.source_available=false;q.result.source.reset();q.result.reason="ccc_original_owner_completion_unavailable";}
 return emit();
}
}
