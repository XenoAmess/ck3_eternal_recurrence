#include "xar_bridge/ck3_121003_aub_observer_fixture26785313_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
namespace xar::ck3_121003::build26785313 {
bool AubObserverFixtureRouteEnabled267V1([[maybe_unused]]const game::AdapterDescriptor&d) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1) && XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1
 return game::IsCk3_121003Core26785313Descriptor(d)&&
  std::find(d.capabilities.begin(),d.capabilities.end(),kAubObserverFixtureCapability267V1)!=d.capabilities.end();
#else
 return false;
#endif
}
std::string DispatchAubObserverFixtureRequest267V1(const game::GameAdapter&game,std::uint64_t connection,
 std::string_view id,std::string_view step,std::string_view payload,ck3_11906::MainThreadQueryMailboxV1&mailbox) {
 AubObserverFixtureContext267V1 q;q.result.reason="fixed_fixture_request_or_profile_unavailable";
 const auto emit=[&]{return SerializeAubObserverFixtureResult267V1(id,q.result);};
 if(step!=kAubObserverFixtureStep267V1||!ParseAubObserverFixtureRequest267V1(payload,q.request)||q.request.id()!=id)return emit();
 if(!game.enabled()||!connection||!AubObserverFixtureRouteEnabled267V1(game.descriptor())||!game.supports_step(step))return emit();
 static AubObserverFixtureSession267V1 retained; // Process lifetime, never reset on reconnect.
 q.session=&retained;q.connection_generation=connection;q.mailbox=&mailbox;
 ArmAubObserverFixtureDeadline267V1(q);
 if(!q.monotonic_deadline_ms){q.result.status=AubObserverFixtureStatus267V1::expired;q.result.reason="fixed_fixture_original_deadline_expired";return emit();}
 const auto submit=ck3_11906::TrySubmitMainThreadQueryV1(mailbox,&ExecuteAubObserverFixtureOnOwner267V1,&q,q.ticket);
 if(submit!=ck3_11906::MainThreadQuerySubmitResultV1::submitted){q.result.reason="fixed_fixture_original_owner_not_ready";return emit();}
 auto wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,8000);
 while(wait==ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)
  wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);
 auto reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);
 // The original stack and resource owner remain alive until this ticket terminates.
 while(reclaim==ck3_11906::MainThreadQueryReclaimResultV1::not_terminal){
  wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);
  reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);
 }
 if(wait!=ck3_11906::MainThreadQueryWaitResultV1::completed||reclaim!=ck3_11906::MainThreadQueryReclaimResultV1::reclaimed){
  const bool uncertain=q.result.effect_attempted||q.resource_ownership_entered;
  if(uncertain)BlockAubObserverFixtureUnknown267V1(retained);
  q.result.status=uncertain?AubObserverFixtureStatus267V1::indeterminate:AubObserverFixtureStatus267V1::unavailable;
  q.result.reason="fixed_fixture_original_owner_completion_unavailable";
 }
 return emit();
}
}
