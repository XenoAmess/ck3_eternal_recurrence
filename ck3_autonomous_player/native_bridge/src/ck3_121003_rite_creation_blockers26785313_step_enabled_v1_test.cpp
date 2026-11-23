#include "xar_bridge/ck3_121003_rite_creation_blockers26785313_owner_v1.hpp"
#include <array>
#include <iostream>
#include <stdexcept>
#include <cstdlib>
using namespace xar::ck3_121003::build26785313;
int main(){try{std::array<std::string_view,1>caps{kRiteBlockersCapability267V1};xar::game::AdapterDescriptor d{kAdapterId,kGameVersion,kExecutableSha256,"xar_checkpoint",caps};
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_CREATION_BLOCKERS_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_CREATION_BLOCKERS_V1
 if(!RiteBlockersStepEnabled267V1(d,kRiteBlockersStep267V1))throw std::runtime_error("actual StepEnabled ON must admit actual cap");
#else
 if(RiteBlockersStepEnabled267V1(d,kRiteBlockersStep267V1))throw std::runtime_error("actual StepEnabled OFF must refuse");
#endif
 if(RiteBlockersStepEnabled267V1(d,"query-des-saved-game-init-guard-current-v1"))throw std::runtime_error("old DES step must not substitute");d.capabilities={};if(RiteBlockersStepEnabled267V1(d,kRiteBlockersStep267V1))throw std::runtime_error("missing actual cap");d.capabilities=caps;d.adapter_id="wrong-adapter";if(RiteBlockersStepEnabled267V1(d,kRiteBlockersStep267V1))throw std::runtime_error("wrong actual adapter");std::cout<<"PASS actual linked StepEnabled ON/OFF and step/cap/descriptor negatives; no fake route substitute\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}

// Trap-only NoGame dependencies for the unused transport function in the same actual TU.
// The tested StepEnabled symbol itself is linked unchanged; no substitute body.
namespace xar::game {bool GameAdapter::supports_step(std::string_view)const noexcept{std::abort();}}
namespace xar::ck3_121003::build26785313 {
bool ParseRiteBlockersRequest267V1(std::string_view,RiteBlockersRequest267V1&)noexcept{std::abort();}
std::string SerializeRiteBlockersResult267V1(std::string_view,const RiteBlockersResult267V1&){std::abort();}
RiteBlockersSession267V1&RetainedRiteBlockersSession267V1(){std::abort();}
void BlockRiteBlockersUnknown267V1(RiteBlockersSession267V1&)noexcept{std::abort();}
void ArmRiteBlockersDeadline267V1(RiteBlockersContext267V1&)noexcept{std::abort();}
bool ExecuteRiteBlockersOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept{std::abort();}
}
namespace xar::ck3_11906 {
MainThreadQuerySubmitResultV1 TrySubmitMainThreadQueryV1(MainThreadQueryMailboxV1&,MainThreadQueryExecutorV1,void*,MainThreadQueryTicketV1&,MainThreadQueryQueuedWakeTraceV1*)noexcept{std::abort();}
MainThreadQueryWaitResultV1 WaitForMainThreadQueryV1(MainThreadQueryMailboxV1&,const MainThreadQueryTicketV1&,std::uint32_t,MainThreadQueryQueuedWakeTraceV1*,std::uint32_t)noexcept{std::abort();}
MainThreadQueryReclaimResultV1 ReclaimMainThreadQueryV1(MainThreadQueryMailboxV1&,const MainThreadQueryTicketV1&)noexcept{std::abort();}
}
