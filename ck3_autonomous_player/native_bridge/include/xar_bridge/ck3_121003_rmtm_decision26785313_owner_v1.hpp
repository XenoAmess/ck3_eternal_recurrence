#pragma once
#include "xar_bridge/ck3_121003_rmtm_decision26785313_raw_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
#include "xar_bridge/ck3_121003_rmtm_owner26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct RmtmDecisionFrame267V1{bool facts_verified=false;ck3_1210::CoreSnapshotPrefix core{};RmtmDecisionScene267V1 scene{};std::vector<GuiWindowNodeV1>witness;};
struct RmtmDecisionContext267V1;
class RmtmDecisionSession267V1{
 public:RmtmDecisionSession267V1();~RmtmDecisionSession267V1();RmtmDecisionSession267V1(const RmtmDecisionSession267V1&)=delete;RmtmDecisionSession267V1&operator=(const RmtmDecisionSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;friend bool ExecuteRmtmDecisionInner267V1(RmtmDecisionContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;friend void BlockRmtmDecisionUnknown267V1(RmtmDecisionSession267V1&)noexcept;
};
struct RmtmDecisionContext267V1{
 RmtmOwnerInvocation267V1 invocation{0x524D544D32363731ULL,RmtmInvocationKind267V1::decision,this};ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};RmtmDecisionRequest267V1 request{};RmtmDecisionResult267V1 result{};RmtmDecisionSession267V1*session=nullptr;std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;};
RmtmDecisionSession267V1&RetainedRmtmDecisionSession267V1();
void ArmRmtmDecisionDeadline267V1(RmtmDecisionContext267V1&)noexcept;
void BlockRmtmDecisionUnknown267V1(RmtmDecisionSession267V1&)noexcept;
bool ExecuteRmtmDecisionInner267V1(RmtmDecisionContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteRmtmDecisionOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadRmtmDecisionFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,RmtmDecisionFrame267V1&,std::string&)noexcept;
bool RmtmDecisionStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchRmtmDecisionRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
