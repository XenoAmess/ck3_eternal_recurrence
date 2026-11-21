#pragma once
#include "xar_bridge/ck3_121003_curated_decisions26785313_raw_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct CuratedDecisionFrame267V1{bool facts_verified=false;ck3_1210::CoreSnapshotPrefix core{};CuratedDecisionScene267V1 scene{};std::vector<GuiWindowNodeV1>witness;};
struct CuratedDecisionContext267V1;
class CuratedDecisionSession267V1{
 public:CuratedDecisionSession267V1();~CuratedDecisionSession267V1();CuratedDecisionSession267V1(const CuratedDecisionSession267V1&)=delete;CuratedDecisionSession267V1&operator=(const CuratedDecisionSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;friend bool ExecuteCuratedDecisionInner267V1(CuratedDecisionContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;friend void BlockCuratedDecisionUnknown267V1(CuratedDecisionSession267V1&)noexcept;
};
struct CuratedDecisionContext267V1{ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};CuratedDecisionRequest267V1 request{};CuratedDecisionResult267V1 result{};CuratedDecisionSession267V1*session=nullptr;std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;};
CuratedDecisionSession267V1&RetainedCuratedDecisionSession267V1();
void ArmCuratedDecisionDeadline267V1(CuratedDecisionContext267V1&)noexcept;
void BlockCuratedDecisionUnknown267V1(CuratedDecisionSession267V1&)noexcept;
bool ExecuteCuratedDecisionInner267V1(CuratedDecisionContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteCuratedDecisionOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadCuratedDecisionFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,CuratedDecisionFrame267V1&,std::string&)noexcept;
bool CuratedDecisionStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchCuratedDecisionRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
