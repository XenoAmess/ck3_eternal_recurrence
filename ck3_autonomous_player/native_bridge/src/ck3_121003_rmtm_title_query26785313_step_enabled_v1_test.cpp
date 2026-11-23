#include "xar_bridge/ck3_121003_rmtm_title_query26785313_owner_v1.hpp"
#include <array>
#include <iostream>
#include <stdexcept>
#include <cstdlib>
using namespace xar::ck3_121003::build26785313;
int main(){try{std::array<std::string_view,1>caps{kRmtmTitleQueryCapability267V1};xar::game::AdapterDescriptor d{kAdapterId,kGameVersion,kExecutableSha256,"xar_checkpoint",caps};
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_QUERY_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_QUERY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1
 if(!RmtmTitleQueryStepEnabled267V1(d,kRmtmTitleQueryStep267V1))throw std::runtime_error("actual StepEnabled ON must admit actual cap");
#else
 if(RmtmTitleQueryStepEnabled267V1(d,kRmtmTitleQueryStep267V1))throw std::runtime_error("actual StepEnabled OFF must refuse");
#endif
 if(RmtmTitleQueryStepEnabled267V1(d,"query-des-saved-game-init-guard-current-v1"))throw std::runtime_error("old DES step must not substitute");d.capabilities={};if(RmtmTitleQueryStepEnabled267V1(d,kRmtmTitleQueryStep267V1))throw std::runtime_error("missing actual cap");d.capabilities=caps;d.adapter_id="wrong-adapter";if(RmtmTitleQueryStepEnabled267V1(d,kRmtmTitleQueryStep267V1))throw std::runtime_error("wrong actual adapter");d.adapter_id=kAdapterId;d.game_version="1.20.0.4";if(RmtmTitleQueryStepEnabled267V1(d,kRmtmTitleQueryStep267V1))throw std::runtime_error("old build cannot substitute");d.game_version=kGameVersion;d.executable_sha256="wrong-exe";if(RmtmTitleQueryStepEnabled267V1(d,kRmtmTitleQueryStep267V1))throw std::runtime_error("wrong exact EXE");std::cout<<"PASS actual linked query StepEnabled, ON/OFF/HEALTH-only/missing-Raw profile; no native execution\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}

// Trap-only NoGame dependencies for the unused transport function in the same actual TU.
// The tested StepEnabled symbol itself is linked unchanged; no substitute body.
namespace xar::game {bool GameAdapter::supports_step(std::string_view)const noexcept{std::abort();}}
namespace xar::ck3_121003::build26785313 {
bool ParseRmtmTitleQueryRequest267V1(std::string_view,RmtmTitleQueryRequest267V1&)noexcept{std::abort();}
std::string SerializeRmtmTitleQueryResult267V1(std::string_view,const RmtmTitleQueryResult267V1&){std::abort();}
RmtmTitleQuerySession267V1&RetainedRmtmTitleQuerySession267V1(){std::abort();}
void BlockRmtmTitleQueryUnknown267V1(RmtmTitleQuerySession267V1&)noexcept{std::abort();}
void ArmRmtmTitleQueryDeadline267V1(RmtmTitleQueryContext267V1&)noexcept{std::abort();}
bool ExecuteRmtmTitleQueryOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept{std::abort();}
}
namespace xar::ck3_11906 {
MainThreadQuerySubmitResultV1 TrySubmitMainThreadQueryV1(MainThreadQueryMailboxV1&,MainThreadQueryExecutorV1,void*,MainThreadQueryTicketV1&,MainThreadQueryQueuedWakeTraceV1*)noexcept{std::abort();}
MainThreadQueryWaitResultV1 WaitForMainThreadQueryV1(MainThreadQueryMailboxV1&,const MainThreadQueryTicketV1&,std::uint32_t,MainThreadQueryQueuedWakeTraceV1*,std::uint32_t)noexcept{std::abort();}
MainThreadQueryReclaimResultV1 ReclaimMainThreadQueryV1(MainThreadQueryMailboxV1&,const MainThreadQueryTicketV1&)noexcept{std::abort();}
}
