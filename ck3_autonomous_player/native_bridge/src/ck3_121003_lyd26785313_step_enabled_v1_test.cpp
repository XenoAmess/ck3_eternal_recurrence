#include "xar_bridge/ck3_121003_lyd26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_full_profile111.hpp"
#include <array>
#include <iostream>
#include <stdexcept>
#include <cstdlib>
using namespace xar::ck3_121003::build26785313;
int main(){try{
 constexpr bool enabled=
#if defined(XAR_LYD_STEP_TEST_EXPECT_ENABLED) && XAR_LYD_STEP_TEST_EXPECT_ENABLED
 true;
#else
 false;
#endif
 std::size_t checked=0;
 const auto require=[&](bool good,const char*why){++checked;if(!good)throw std::runtime_error(why);};
 for(std::size_t i=0;i<kLydSteps267V1.size();++i){
  std::array<std::string_view,1>caps{kLydCapabilities267V1[i]};
  xar::game::AdapterDescriptor d{kAdapterId,kGameVersion,kExecutableSha256,"xar_checkpoint",caps};
  require(LydStepEnabled267V1(d,kLydSteps267V1[i])==enabled,"Actual linked own LYD profile differs");
  require(!LydStepEnabled267V1(d,kLydSteps267V1[(i+1)%kLydSteps267V1.size()]),"Other capability cannot authorize this step");
  require(!LydStepEnabled267V1(d,"query-current-rite-creation-blockers-v1"),"Other family step cannot substitute");
  d.capabilities={};require(!LydStepEnabled267V1(d,kLydSteps267V1[i]),"Missing actual capability");
  d.capabilities=caps;d.adapter_id="wrong-adapter";require(!LydStepEnabled267V1(d,kLydSteps267V1[i]),"Wrong actual descriptor");
 }
 constexpr bool full111_enabled=
#if defined(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_READ_V1) && XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_READ_V1
 true;
#else
 false;
#endif
 xar::game::AdapterDescriptor full{xar::ck3_121003::full111::kAdapterId,kGameVersion,
  kExecutableSha256,"xar_checkpoint",kLydCapabilities267V1};
 for(std::size_t i=0;i<kLydSteps267V1.size();++i)
  require(LydStepEnabled267V1(full,kLydSteps267V1[i])==(full111_enabled&&i==kLydEventQueryIndex267V1),
   "Full111 must grant at most the one actual read-only action");
 full.capabilities={};
 require(!LydStepEnabled267V1(full,kLydSteps267V1[kLydEventQueryIndex267V1]),"Full111 missing read capability");
 constexpr bool renderer_enabled=
#if defined(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_SNAPSHOT_V1) && XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_SNAPSHOT_V1
 true;
#else
 false;
#endif
 const std::array renderer_caps{kLydCapabilities267V1[kLydEventQueryIndex267V1],kFull111EventRendererCapability267V1};
 full.capabilities=kLydCapabilities267V1;
 require(!LydStepEnabled267V1(full,kFull111EventRendererStep267V1),"legacy LYD capability authorizes renderer");
 full.capabilities=renderer_caps;
 require(LydStepEnabled267V1(full,kFull111EventRendererStep267V1)==renderer_enabled,"actual Full111 renderer capability differs");
 require(LydStepEnabled267V1(full,kLydSteps267V1[kLydEventQueryIndex267V1])==full111_enabled,"renderer hid legacy event read");
 const xar::game::AdapterDescriptor core{kAdapterId,kGameVersion,kExecutableSha256,"xar_checkpoint",renderer_caps};
 require(!LydStepEnabled267V1(core,kFull111EventRendererStep267V1),"core profile acquired renderer");
 full.executable_sha256="wrong-executable";
 require(!LydStepEnabled267V1(full,kFull111EventRendererStep267V1),"renderer accepted a wrong executable");
 require(!LydStepEnabled267V1(full,kLydSteps267V1[kLydEventQueryIndex267V1]),"Full111 wrong executable");
 std::cout<<"PASS actual linked LydStepEnabled, expected="<<enabled<<", checks="<<checked<<", no transport/owner/native calls\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}

// Trap-only NoGame dependencies for the unused transport function in the same actual TU.
// The tested StepEnabled symbol itself is linked unchanged; no substitute body.
namespace xar::game {bool GameAdapter::supports_step(std::string_view)const noexcept{std::abort();}}
namespace xar::ck3_121003::build26785313 {
bool ParseLydRequest267V1(std::string_view,LydRequest267V1&)noexcept{std::abort();}
bool ParseFull111LydEventRequest267V1(std::string_view,LydRequest267V1&)noexcept{std::abort();}
std::string SerializeFull111LydEventResult267V1(std::string_view,const LydResult267V1&){std::abort();}
bool ParseFull111EventRendererRequest267V1(std::string_view,LydRequest267V1&)noexcept{std::abort();}
std::string SerializeFull111EventRendererResult267V1(std::string_view,const LydResult267V1&){std::abort();}
std::string SerializeLydResult267V1(std::string_view,const LydResult267V1&){std::abort();}
LydSession267V1&RetainedLydSession267V1(){std::abort();}
void BlockLydUnknown267V1(LydSession267V1&)noexcept{std::abort();}
void ArmLydDeadline267V1(LydContext267V1&)noexcept{std::abort();}
bool ExecuteLydOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept{std::abort();}
}
namespace xar::ck3_11906 {
MainThreadQuerySubmitResultV1 TrySubmitMainThreadQueryV1(MainThreadQueryMailboxV1&,MainThreadQueryExecutorV1,void*,MainThreadQueryTicketV1&,MainThreadQueryQueuedWakeTraceV1*)noexcept{std::abort();}
MainThreadQueryWaitResultV1 WaitForMainThreadQueryV1(MainThreadQueryMailboxV1&,const MainThreadQueryTicketV1&,std::uint32_t,MainThreadQueryQueuedWakeTraceV1*,std::uint32_t)noexcept{std::abort();}
MainThreadQueryReclaimResultV1 ReclaimMainThreadQueryV1(MainThreadQueryMailboxV1&,const MainThreadQueryTicketV1&)noexcept{std::abort();}
}
