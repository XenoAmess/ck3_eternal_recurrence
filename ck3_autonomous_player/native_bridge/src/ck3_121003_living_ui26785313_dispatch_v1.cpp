#include "xar_bridge/ck3_121003_living_ui26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <algorithm>
#include <vector>
namespace xar::ck3_121003::build26785313 {
const game::AdapterDescriptor&LivingUiDescriptor267V1(const game::AdapterDescriptor&base)noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_UI_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_UI_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LYD_V1) && XAR_CK3_ENABLE_121003_26785313_LYD_V1
 if(!game::IsCk3_121003Core26785313Descriptor(base))return base;
 static const auto caps=[&]{std::vector<std::string_view>v(base.capabilities.begin(),base.capabilities.end());if(std::find(v.begin(),v.end(),kLivingUiCapability267V1)==v.end())v.push_back(kLivingUiCapability267V1);return v;}();
 static const game::AdapterDescriptor d{base.adapter_id,base.game_version,base.executable_sha256,base.checkpoint_save_name,caps};return d;
#else
 return base;
#endif
}
bool LivingUiStepEnabled267V1(const game::AdapterDescriptor&d,std::string_view step)noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_UI_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_UI_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LYD_V1) && XAR_CK3_ENABLE_121003_26785313_LYD_V1
 return game::IsCk3_121003Core26785313Descriptor(d)&&step==kLivingUiStep267V1&&
  std::find(d.capabilities.begin(),d.capabilities.end(),kLivingUiCapability267V1)!=d.capabilities.end();
#else
 (void)d;(void)step;return false;
#endif
}
std::string DispatchLivingUiRequest267V1(const game::GameAdapter&game,std::uint64_t connection,
 std::string_view id,std::string_view step,std::string_view payload,ck3_11906::MainThreadQueryMailboxV1&mailbox){
 LivingUiContext267V1 q;q.result.reason="living_UI_new_current_profile_unavailable";
 const auto emit=[&]{return SerializeLivingUiResult267V1(id,q.result);};
 if(!ParseLivingUiRequest267V1(payload,q.request)||q.request.id()!=id)return emit();
 q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;
 if(!game.enabled()||!connection||!LivingUiStepEnabled267V1(game.descriptor(),step)||!game.supports_step(step)||
    mailbox.permitted_executor_artifact_personal_read12004!=&ExecuteLivingOnOwner267V1)return emit();
 q.session=&RetainedLivingUiSession267V1();q.connection_generation=connection;q.mailbox=&mailbox;
 q.invocation.context=&q;ArmLivingUiDeadline267V1(q);
 if(!q.monotonic_deadline_ms){q.result.status=LivingUiStatus267V1::expired;return emit();}
 const auto submit=ck3_11906::TrySubmitMainThreadQueryV1(mailbox,&ExecuteLivingOnOwner267V1,&q.invocation,q.ticket);
 if(submit!=ck3_11906::MainThreadQuerySubmitResultV1::submitted){q.result.reason="living_UI_actual_main_owner_not_ready";return emit();}
 auto wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,8000);
 while(wait==ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);
 auto reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);
 while(reclaim==ck3_11906::MainThreadQueryReclaimResultV1::not_terminal){wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);}
 if(wait!=ck3_11906::MainThreadQueryWaitResultV1::completed||reclaim!=ck3_11906::MainThreadQueryReclaimResultV1::reclaimed){
  if(q.observation_entered||q.result.effect_attempted){BlockLivingFamilyUnknown267V1();q.result.cleanup_known=false;q.result.status=LivingUiStatus267V1::indeterminate;}
  q.result.source_available=false;q.result.source.reset();q.result.reason="living_UI_original_owner_completion_unavailable";
 }
 return emit();
}
}
