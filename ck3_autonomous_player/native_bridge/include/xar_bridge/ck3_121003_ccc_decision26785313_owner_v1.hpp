#pragma once
#include "xar_bridge/ck3_121003_ccc_decision26785313_raw_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
#include "xar_bridge/ck3_121003_ccc_owner26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct CccDecisionFrame267V1{bool facts_verified=false;ck3_1210::CoreSnapshotPrefix core{};CccDecisionScene267V1 scene{};std::vector<GuiWindowNodeV1>witness;};
struct CccDecisionContext267V1;
class CccDecisionSession267V1{
 public:CccDecisionSession267V1();~CccDecisionSession267V1();CccDecisionSession267V1(const CccDecisionSession267V1&)=delete;CccDecisionSession267V1&operator=(const CccDecisionSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;friend bool ExecuteCccDecisionInner267V1(CccDecisionContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;friend void BlockCccDecisionUnknown267V1(CccDecisionSession267V1&)noexcept;
};
struct CccDecisionContext267V1{
 CccOwnerInvocation267V1 invocation{0x4343433236375631ULL,CccInvocationKind267V1::decision,this};ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};CccDecisionRequest267V1 request{};CccDecisionResult267V1 result{};CccDecisionSession267V1*session=nullptr;std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;};
CccDecisionSession267V1&RetainedCccDecisionSession267V1();
void ArmCccDecisionDeadline267V1(CccDecisionContext267V1&)noexcept;
void BlockCccDecisionUnknown267V1(CccDecisionSession267V1&)noexcept;
bool ExecuteCccDecisionInner267V1(CccDecisionContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteCccDecisionOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadCccDecisionFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,CccDecisionFrame267V1&,std::string&)noexcept;
bool CccDecisionStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchCccDecisionRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
