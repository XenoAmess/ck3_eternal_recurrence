#include "xar_bridge/ck3_121003_rmtm_actor_transition26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_event26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_decision26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_rmtm_observation26785313_owner_v1.hpp"
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <vector>
namespace c=xar::ck3_121003::build26785313;
struct Entry {std::string_view step,cap;bool(*enabled)(const xar::game::AdapterDescriptor&,std::string_view)noexcept;};
int main(){try{
 std::vector<Entry>rows;
 for(std::size_t n=0;n<4;++n)rows.push_back({c::kRmtmTransitionSteps267V1[n],c::kRmtmTransitionCapabilities267V1[n==0||n==2?0:n==1?1:2],c::RmtmTransitionStepEnabled267V1});
 for(std::size_t n=0;n<4;++n)rows.push_back({c::kRmtmEventSteps267V1[n],c::kRmtmEventCaps267V1[n],c::RmtmEventStepEnabled267V1});
 for(std::size_t n=0;n<4;++n)rows.push_back({c::kRmtmDecisionSteps267V1[n],c::kRmtmDecisionCapabilities267V1[n],c::RmtmDecisionStepEnabled267V1});
 for(std::size_t n=0;n<8;++n)rows.push_back({c::kRmtmObservationSteps267V1[n],c::kRmtmObservationCaps267V1[n],c::RmtmObservationStepEnabled267V1});
 const auto need=[](bool x,const char*why){if(!x)throw std::runtime_error(why);};
 std::vector<std::string_view>caps;for(const auto&r:rows)if(std::find(caps.begin(),caps.end(),r.cap)==caps.end())caps.push_back(r.cap);
 xar::game::AdapterDescriptor d{c::kAdapterId,c::kGameVersion,c::kExecutableSha256,"xar_checkpoint",caps};
 for(const auto&r:rows){
#if XAR_RMTM_PROFILE_EXPECT_ON
  need(r.enabled(d,r.step),"actual linked Step method must be ON with its exact cap");
#else
  need(!r.enabled(d,r.step),"actual linked Step method OFF/HEALTH-only/missing-dependency refuses");
#endif
  auto foreign=d;foreign.adapter_id="wrong";need(!r.enabled(foreign,r.step),"wrong adapter");foreign=d;foreign.game_version="1.20.0.4";need(!r.enabled(foreign,r.step),"old build");foreign=d;foreign.executable_sha256="wrong";need(!r.enabled(foreign,r.step),"wrong exact image");foreign=d;foreign.capabilities={};need(!r.enabled(foreign,r.step),"missing capability");
  need(!r.enabled(d,"query-current-ccc-role-v1"),"CCC step cannot substitute");need(!r.enabled(d,"advance-current-date-by-one-day-v1"),"old Date permission cannot substitute");
  for(const auto&cap:caps){const std::array<std::string_view,1>one{cap};auto only=d;only.capabilities=one;
#if XAR_RMTM_PROFILE_EXPECT_ON
   need(r.enabled(only,r.step)==(cap==r.cap),"each actual Step maps only its exact cap; role/status shared cap is intentional");
#else
   need(!r.enabled(only,r.step),"no capability can override a disabled actual method");
#endif
  }
 }
 std::cout<<"PASS twenty real StepEnabled methods and nineteen exact caps; no extracted/replacement body\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
// Only dependencies of the unused Dispatch functions are traps. All four real
// Dispatch TUs are linked unchanged; every tested StepEnabled body is genuine.
namespace xar::game {bool GameAdapter::supports_step(std::string_view)const noexcept{std::abort();}}
namespace xar::ck3_121003::build26785313 {
#define RMTM_TRAPS(Family) \
 bool ParseRmtm##Family##Request267V1(std::string_view,Rmtm##Family##Request267V1&)noexcept{std::abort();} \
 std::string SerializeRmtm##Family##Result267V1(std::string_view,const Rmtm##Family##Result267V1&){std::abort();} \
 Rmtm##Family##Session267V1&RetainedRmtm##Family##Session267V1(){std::abort();} \
 void BlockRmtm##Family##Unknown267V1(Rmtm##Family##Session267V1&)noexcept{std::abort();} \
 void ArmRmtm##Family##Deadline267V1(Rmtm##Family##Context267V1&)noexcept{std::abort();}
RMTM_TRAPS(Transition)
RMTM_TRAPS(Event)
RMTM_TRAPS(Decision)
RMTM_TRAPS(Observation)
#undef RMTM_TRAPS
bool ExecuteRmtmOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept{std::abort();}
RmtmTransitionResult267V1 QueryRmtmTransitionOperation267V1(RmtmTransitionSession267V1&,const RmtmTransitionRequest267V1&,std::uint64_t,bool*)noexcept{std::abort();}
}
namespace xar::ck3_11906 {
MainThreadQuerySubmitResultV1 TrySubmitMainThreadQueryV1(MainThreadQueryMailboxV1&,MainThreadQueryExecutorV1,void*,MainThreadQueryTicketV1&,MainThreadQueryQueuedWakeTraceV1*)noexcept{std::abort();}
MainThreadQueryWaitResultV1 WaitForMainThreadQueryV1(MainThreadQueryMailboxV1&,const MainThreadQueryTicketV1&,std::uint32_t,MainThreadQueryQueuedWakeTraceV1*,std::uint32_t)noexcept{std::abort();}
MainThreadQueryReclaimResultV1 ReclaimMainThreadQueryV1(MainThreadQueryMailboxV1&,const MainThreadQueryTicketV1&)noexcept{std::abort();}
}
