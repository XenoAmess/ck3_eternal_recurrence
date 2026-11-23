#include "xar_bridge/ck3_121003_ccc_actor_transition26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_ccc_event26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_ccc_decision26785313_owner_v1.hpp"
#include <array>
#include <cstdlib>
#include <iostream>
#include <stdexcept>

// Link the THREE actual candidate *_dispatch_v1.cpp files unchanged. No copied
// StepEnabled body, adapter implementation, Game, owner mailbox or native ABI.
#if defined(XAR_CCC_STEP_TEST_HEALTH_ONLY) && XAR_CCC_STEP_TEST_HEALTH_ONLY
#if !defined(XAR_CK3_ENABLE_121003_26785313_SUPERMAN_HEALTH_V1) || !XAR_CK3_ENABLE_121003_26785313_SUPERMAN_HEALTH_V1
#error HEALTH-only test must enable the actual existing health switch
#endif
#if (defined(XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) || (defined(XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1) || (defined(XAR_CK3_ENABLE_121003_26785313_CCC_DECISION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_DECISION_V1)
#error HEALTH-only must not enable any CCC switch
#endif
#endif
using namespace xar::ck3_121003::build26785313;
using Step=bool(*)(const xar::game::AdapterDescriptor&,std::string_view)noexcept;
struct Rule{std::string_view step,cap;Step enabled;};
int main(){try{
 constexpr bool on=
#if defined(XAR_CCC_STEP_TEST_EXPECT_ENABLED) && XAR_CCC_STEP_TEST_EXPECT_ENABLED
 true;
#else
 false;
#endif
 const std::array<Rule,11>rules{{
  {kCccTransitionSteps267V1[0],kCccTransitionCapabilities267V1[0],&CccTransitionStepEnabled267V1},
  {kCccTransitionSteps267V1[1],kCccTransitionCapabilities267V1[1],&CccTransitionStepEnabled267V1},
  {kCccTransitionSteps267V1[2],kCccTransitionCapabilities267V1[0],&CccTransitionStepEnabled267V1},
  {kCccTransitionSteps267V1[3],kCccTransitionCapabilities267V1[2],&CccTransitionStepEnabled267V1},
  {kCccEventSteps267V1[0],kCccEventCaps267V1[0],&CccEventStepEnabled267V1},
  {kCccEventSteps267V1[1],kCccEventCaps267V1[1],&CccEventStepEnabled267V1},
  {kCccEventSteps267V1[2],kCccEventCaps267V1[2],&CccEventStepEnabled267V1},
  {kCccDecisionSteps267V1[0],kCccDecisionCapabilities267V1[0],&CccDecisionStepEnabled267V1},
  {kCccDecisionSteps267V1[1],kCccDecisionCapabilities267V1[1],&CccDecisionStepEnabled267V1},
  {kCccDecisionSteps267V1[2],kCccDecisionCapabilities267V1[2],&CccDecisionStepEnabled267V1},
  {kCccDecisionSteps267V1[3],kCccDecisionCapabilities267V1[3],&CccDecisionStepEnabled267V1}
 }};
 std::size_t checks=0;const auto require=[&](bool good,const char*why){++checks;if(!good)throw std::runtime_error(why);};
 for(const auto&r:rules){
  std::array<std::string_view,1>caps{r.cap};xar::game::AdapterDescriptor d{kAdapterId,kGameVersion,kExecutableSha256,"xar_checkpoint",caps};
  require(r.enabled(d,r.step)==on,"Actual linked own CCC StepEnabled differs");
  // Query role and query operation intentionally use the SAME transition cap.
  // They are both positive with that cap, never foreign-cap negative examples.
  for(const auto&other:rules){std::array<std::string_view,1>one{other.cap};d.capabilities=one;require(r.enabled(d,r.step)==(on&&other.cap==r.cap),"Exact actual step/cap mapping differs");}
  d.capabilities={};require(!r.enabled(d,r.step),"Missing cap must refuse");
  std::array<std::string_view,1>unknown{"game.command.not-a-ccc-capability.v999"};d.capabilities=unknown;require(!r.enabled(d,r.step),"Unknown cap must refuse");
  std::array<std::string_view,2>health{"game.query.current-superman-health.v1","game.command.select-current-superman-health-known-option.v1"};d.capabilities=health;require(!r.enabled(d,r.step),"Real health-only capabilities cannot authorize CCC");
  d.capabilities=caps;
  for(auto step:{std::string_view{},std::string_view{"unknown-ccc-step"},std::string_view{"query-current-ted-role-v1"},std::string_view{"query-ccc-event-current-v1.extra"},std::string_view{"query-current-ccc-role-v1 "}})
   require(!r.enabled(d,step),"Unknown/foreign/partial step must refuse");
  d.adapter_id="wrong-adapter";require(!r.enabled(d,r.step),"Wrong adapter");d.adapter_id=kAdapterId;
  d.game_version="1.20.0.4";require(!r.enabled(d,r.step),"Wrong exact game version");d.game_version=kGameVersion;
  d.executable_sha256="different-executable";require(!r.enabled(d,r.step),"Wrong exact executable");d.executable_sha256=kExecutableSha256;
 }
 require(rules[0].cap==rules[2].cap,"Original transition query role/operation share query capability");
 std::cout<<"PASS linked actual CCC 11 fixed steps, expected="<<on<<", checks="<<checks<<", no dispatch/owner/native call\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}

// Trap-only dependencies of UNUSED transport functions in the actual Dispatch
// translation units. Any accidental call aborts; none substitutes StepEnabled.
namespace xar::game {bool GameAdapter::supports_step(std::string_view)const noexcept{std::abort();}}
namespace xar::ck3_121003::build26785313 {
bool ParseCccTransitionRequest267V1(std::string_view,CccTransitionRequest267V1&)noexcept{std::abort();}
std::string SerializeCccTransitionResult267V1(std::string_view,const CccTransitionResult267V1&){std::abort();}
CccTransitionSession267V1&RetainedCccTransitionSession267V1(){std::abort();}
CccTransitionResult267V1 QueryCccTransitionOperation267V1(CccTransitionSession267V1&,const CccTransitionRequest267V1&,std::uint64_t,bool*)noexcept{std::abort();}
void BlockCccTransitionUnknown267V1(CccTransitionSession267V1&)noexcept{std::abort();}
void ArmCccTransitionDeadline267V1(CccTransitionContext267V1&)noexcept{std::abort();}
bool ParseCccEventRequest267V1(std::string_view,CccEventRequest267V1&)noexcept{std::abort();}
std::string SerializeCccEventResult267V1(std::string_view,const CccEventResult267V1&){std::abort();}
CccEventSession267V1&RetainedCccEventSession267V1(){std::abort();}
void BlockCccEventUnknown267V1(CccEventSession267V1&)noexcept{std::abort();}
void ArmCccEventDeadline267V1(CccEventContext267V1&)noexcept{std::abort();}
bool ParseCccDecisionRequest267V1(std::string_view,CccDecisionRequest267V1&)noexcept{std::abort();}
std::string SerializeCccDecisionResult267V1(std::string_view,const CccDecisionResult267V1&){std::abort();}
CccDecisionSession267V1&RetainedCccDecisionSession267V1(){std::abort();}
void BlockCccDecisionUnknown267V1(CccDecisionSession267V1&)noexcept{std::abort();}
void ArmCccDecisionDeadline267V1(CccDecisionContext267V1&)noexcept{std::abort();}
bool ExecuteCccOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept{std::abort();}
}
namespace xar::ck3_11906 {
MainThreadQuerySubmitResultV1 TrySubmitMainThreadQueryV1(MainThreadQueryMailboxV1&,MainThreadQueryExecutorV1,void*,MainThreadQueryTicketV1&,MainThreadQueryQueuedWakeTraceV1*)noexcept{std::abort();}
MainThreadQueryWaitResultV1 WaitForMainThreadQueryV1(MainThreadQueryMailboxV1&,const MainThreadQueryTicketV1&,std::uint32_t,MainThreadQueryQueuedWakeTraceV1*,std::uint32_t)noexcept{std::abort();}
MainThreadQueryReclaimResultV1 ReclaimMainThreadQueryV1(MainThreadQueryMailboxV1&,const MainThreadQueryTicketV1&)noexcept{std::abort();}
}
