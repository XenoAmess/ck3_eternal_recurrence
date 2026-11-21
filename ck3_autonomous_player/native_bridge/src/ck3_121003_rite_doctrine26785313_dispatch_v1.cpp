#include "xar_bridge/ck3_121003_rite_doctrine26785313_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {
bool RiteDoctrineRouteEnabled267V1([[maybe_unused]]const game::AdapterDescriptor&d) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1
 return game::IsCk3_121003Core26785313Descriptor(d)&&
  std::find(d.capabilities.begin(),d.capabilities.end(),kRiteDoctrineCapability267V1)!=d.capabilities.end()&&
  std::find(d.capabilities.begin(),d.capabilities.end(),ck3_1210::kCoreFrameCapabilityV1)!=d.capabilities.end();
#else
 return false;
#endif
}
std::string DispatchRiteDoctrineRequest267V1(const game::GameAdapter&game,std::uint64_t generation,
 std::string_view id,std::string_view step,std::string_view payload,ck3_11906::MainThreadQueryMailboxV1&mailbox) {
 RiteDoctrineContext267V1 query{};
 const auto answer=[&](){return SerializeRiteDoctrineResult267V1(id,query.result);};
 if(!ParseRiteDoctrineRequest267V1(payload,query.request)||step!=RiteDoctrineStepForAction267V1(query.request.action)||query.request.id()!=id) {
  query.result.reason="invalid_exact_current_rite_doctrine_request";return answer();
 }
 query.result.action=query.request.action;
 query.result.provider_generation=query.request.provider_generation;query.result.query_sequence=query.request.query_sequence;
 if(!game.enabled()||!RiteDoctrineRouteEnabled267V1(game.descriptor())||!game.supports_step(step)||!generation||
    (IsRiteFinalConfirmAction267V1(query.request.action)&&!game.supports(kRiteFinalConfirmCapability267V1)))return answer();
 // A connection or WorkerState teardown cannot retire original effect claims.
 static RiteDoctrineSession267V1 retained_claims;
 query.session=&retained_claims;query.game=&game;query.connection_generation=generation;
 query.request.window.connection_generation=generation;query.mailbox=&mailbox;
 query.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);
 ArmRiteDoctrineDeadline267V1(query);
 if(!query.monotonic_deadline_ms){query.result.status=RiteDoctrineStatus267V1::expired;return answer();}
 const auto submitted=ck3_11906::TrySubmitMainThreadQueryV1(mailbox,&ExecuteRiteDoctrineOnOwner267V1,&query,query.ticket);
 if(submitted!=ck3_11906::MainThreadQuerySubmitResultV1::submitted)return answer();
 auto waited=ck3_11906::WaitForMainThreadQueryV1(mailbox,query.ticket,8000);
 while(waited==ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)
  waited=ck3_11906::WaitForMainThreadQueryV1(mailbox,query.ticket,2000);
 auto reclaimed=ck3_11906::ReclaimMainThreadQueryV1(mailbox,query.ticket);
 // Retain this exact stack/context until the original mailbox owner releases
 // it; no detached context and no second executor after a timeout.
 while(reclaimed==ck3_11906::MainThreadQueryReclaimResultV1::not_terminal) {
  waited=ck3_11906::WaitForMainThreadQueryV1(mailbox,query.ticket,2000);
  reclaimed=ck3_11906::ReclaimMainThreadQueryV1(mailbox,query.ticket);
 }
 if(waited!=ck3_11906::MainThreadQueryWaitResultV1::completed||reclaimed!=ck3_11906::MainThreadQueryReclaimResultV1::reclaimed) {
  const bool uncertain=query.result.effect_attempted;
  if(uncertain)BlockRiteDoctrineUnknown267V1(retained_claims);
  query.result.status=uncertain?RiteDoctrineStatus267V1::indeterminate:RiteDoctrineStatus267V1::unavailable;
  query.result.reason=uncertain?"current_rite_owner_result_unknown_no_replay":"current_rite_owner_executor_unavailable";
 }
 return answer();
}
} // namespace xar::ck3_121003::build26785313
