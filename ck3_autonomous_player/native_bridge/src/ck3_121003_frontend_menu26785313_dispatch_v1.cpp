#include "xar_bridge/ck3_121003_frontend_menu26785313_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
#include <chrono>
namespace xar::ck3_121003::build26785313 {
bool FrontendAdapterAdmitted267V1(const FrontendMenuContext267V1&q,std::string_view cap)noexcept{return q.game&&q.game->enabled()&&game::IsCk3_121003Core26785313Descriptor(q.game->descriptor())&&q.game->supports(cap);}
bool FrontendMenuStepEnabled267V1([[maybe_unused]]const game::AdapterDescriptor&d,[[maybe_unused]]std::string_view step) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_FRONTEND_MENU_V1) && XAR_CK3_ENABLE_121003_26785313_FRONTEND_MENU_V1
 if(!game::IsCk3_121003Core26785313Descriptor(d))return false;
 std::string_view capability=step==kFrontendMenuQueryStep267V1?kFrontendMenuQueryCapability267V1:step==kFrontendMenuQuitStep267V1?kFrontendMenuQuitCapability267V1:"";
#if defined(XAR_CK3_ENABLE_121003_26785313_FRONTEND_SEED_V1) && XAR_CK3_ENABLE_121003_26785313_FRONTEND_SEED_V1
 for(std::size_t i=2;i<kFrontendAllSteps267V1.size();++i)if(step==kFrontendAllSteps267V1[i])capability=kFrontendAllCaps267V1[i];
#endif
 return !capability.empty()&&std::find(d.capabilities.begin(),d.capabilities.end(),capability)!=d.capabilities.end();
#else
 return false;
#endif
}
std::string DispatchFrontendMenuRequest267V1(const game::GameAdapter&game,std::uint64_t connection,
 std::string_view id,std::string_view step,std::string_view payload,ck3_11906::MainThreadQueryMailboxV1&mailbox) {
 FrontendMenuContext267V1 q; q.result.reason="current_frontend_request_profile_unavailable";
 const auto emit=[&]{return SerializeFrontendMenuResult267V1(id,q.result);};
 if(!ParseFrontendMenuRequest267V1(payload,q.request)||q.request.id()!=id||FrontendMenuStep267V1(q.request.action)!=step)return emit();
 q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;
 if(!game.enabled()||!connection||!FrontendMenuStepEnabled267V1(game.descriptor(),step)||!game.supports_step(step))return emit();
 static FrontendMenuSession267V1 process_retained; // never reset on reconnect
 q.session=&process_retained;q.game=&game;q.connection_generation=connection;q.mailbox=&mailbox;
 ArmFrontendMenuDeadline267V1(q);
 if(!q.monotonic_deadline_ms){q.result.status=FrontendMenuStatus267V1::expired;q.result.reason="current_frontend_original_deadline_expired";return emit();}
 const auto submit=ck3_11906::TrySubmitMainThreadQueryV1(mailbox,&ExecuteFrontendMenuOnOwner267V1,&q,q.ticket);
 if(submit!=ck3_11906::MainThreadQuerySubmitResultV1::submitted){q.result.reason="current_frontend_owner_not_ready";return emit();}
 auto wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,8000);
 while(wait==ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)
  wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);
 auto reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);
 // This original stack remains alive until its sole real owner is terminal.
 while(reclaim==ck3_11906::MainThreadQueryReclaimResultV1::not_terminal){
  wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);
  reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);
 }
 if(wait!=ck3_11906::MainThreadQueryWaitResultV1::completed||reclaim!=ck3_11906::MainThreadQueryReclaimResultV1::reclaimed){
  if(q.result.effect_attempted)BlockFrontendMenuUnknown267V1(process_retained);
  q.result.status=q.result.effect_attempted?FrontendMenuStatus267V1::indeterminate:FrontendMenuStatus267V1::unavailable;
  q.result.reason="current_frontend_original_owner_completion_unavailable";
 }
 // These follow-up tickets perform readonly proof only. The original action
 // claim and both deadlines remain fixed; no callback can repeat its effect.
 for(unsigned sample=0;q.seed_readback_only&&q.result.native_returned&&sample<64;++sample){
  const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
  if(wall<=0||static_cast<std::uint64_t>(wall)>=q.request.deadline_unix_ms||GetTickCount64()>=q.monotonic_deadline_ms)break;
  Sleep(20);const auto sent=ck3_11906::TrySubmitMainThreadQueryV1(mailbox,&ExecuteFrontendMenuOnOwner267V1,&q,q.ticket);
  if(sent!=ck3_11906::MainThreadQuerySubmitResultV1::submitted)continue;
  auto observed=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,8000);
  while(observed==ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)observed=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);
  auto released=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);
  while(released==ck3_11906::MainThreadQueryReclaimResultV1::not_terminal){observed=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);released=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);}
  if(observed!=ck3_11906::MainThreadQueryWaitResultV1::completed||released!=ck3_11906::MainThreadQueryReclaimResultV1::reclaimed)break;
 }
 if(q.seed_readback_only){BlockFrontendMenuUnknown267V1(process_retained);q.result.status=FrontendMenuStatus267V1::indeterminate;q.result.reason="current_frontend_original_seed_effect_postproof_unknown_no_replay";}
 return emit();
}
}
