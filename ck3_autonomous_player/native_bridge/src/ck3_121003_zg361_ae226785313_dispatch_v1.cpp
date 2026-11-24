#include "xar_bridge/ck3_121003_zg361_ae226785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
namespace xar::ck3_121003::build26785313 {
const game::AdapterDescriptor&Zg361Ae2Descriptor267V1(const game::AdapterDescriptor&base)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1) && XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1
 if(!game::IsCk3_121003Core26785313Descriptor(base))return base;
 static const auto caps=[&]{std::vector<std::string_view>v(base.capabilities.begin(),base.capabilities.end());
  for(const auto cap:kZg361Ae2Capabilities267V1)if(std::find(v.begin(),v.end(),cap)==v.end())v.push_back(cap);return v;}();
 static const game::AdapterDescriptor d{base.adapter_id,base.game_version,base.executable_sha256,base.checkpoint_save_name,caps};return d;
#else
 return base;
#endif
}
bool Zg361Ae2StepEnabled267V1(const game::AdapterDescriptor&d,std::string_view step)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1) && XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1
 if(!game::IsCk3_121003Core26785313Descriptor(d)||step!=kZg361Ae2Step267V1)return false;
 for(const auto cap:kZg361Ae2Capabilities267V1)if(std::find(d.capabilities.begin(),d.capabilities.end(),cap)==d.capabilities.end())return false;
 return true;
#else
 (void)d;(void)step;return false;
#endif
}
std::string DispatchZg361Ae2Request267V1(const game::GameAdapter&game,std::uint64_t connection,
 std::string_view id,std::string_view step,std::string_view payload,ck3_11906::MainThreadQueryMailboxV1&mailbox){
 Zg361Ae2Context267V1 q;q.result.reason="zg361_ae2_actual_request_or_profile_unavailable";
 const auto emit=[&]{return SerializeZg361Ae2Result267V1(id,q.result);};
 if(!ParseZg361Ae2Request267V1(payload,q.request)||q.request.id()!=id)return emit();
 q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;
 if(!game.enabled()||!connection||!Zg361Ae2StepEnabled267V1(game.descriptor(),step)||!game.supports_step(step)||
  mailbox.permitted_executor_sextrigintary!=&ExecuteZg361Ae2OnOwner267V1)return emit();
 q.session=&RetainedZg361Ae2Session267V1();q.connection_generation=connection;q.mailbox=&mailbox;
 ArmZg361Ae2Deadline267V1(q);
 if(!q.monotonic_deadline_ms){q.result.status=Zg361Ae2Status267V1::expired;q.result.reason="zg361_ae2_original_deadline_expired";return emit();}
 const auto submit=ck3_11906::TrySubmitMainThreadQueryV1(mailbox,&ExecuteZg361Ae2OnOwner267V1,&q,q.ticket);
 if(submit!=ck3_11906::MainThreadQuerySubmitResultV1::submitted){q.result.reason="zg361_ae2_actual_application_owner_not_ready";return emit();}
 auto wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,8000);
 while(wait==ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);
 auto reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);
 while(reclaim==ck3_11906::MainThreadQueryReclaimResultV1::not_terminal){wait=ck3_11906::WaitForMainThreadQueryV1(mailbox,q.ticket,2000);reclaim=ck3_11906::ReclaimMainThreadQueryV1(mailbox,q.ticket);}
 if(wait!=ck3_11906::MainThreadQueryWaitResultV1::completed||reclaim!=ck3_11906::MainThreadQueryReclaimResultV1::reclaimed){
  if(q.observation_entered||q.result.effect_attempted){BlockZg361Ae2Unknown267V1(*q.session);q.result.cleanup_known=false;q.result.status=Zg361Ae2Status267V1::indeterminate;}
  q.result.source_available=false;q.result.source.reset();q.result.reason="zg361_ae2_original_owner_completion_unavailable";
 }return emit();
}
}
