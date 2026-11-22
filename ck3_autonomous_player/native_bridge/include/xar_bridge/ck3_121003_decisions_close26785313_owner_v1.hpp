#pragma once
#include "xar_bridge/ck3_121003_decisions_close26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_decisions_close26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ck3_121003_curated_decisions26785313_owner_v1.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
using DecisionsCloseFrame267V1=CuratedDecisionFrame267V1;
struct DecisionsCloseContext267V1;
class DecisionsCloseSession267V1{
 public:DecisionsCloseSession267V1();~DecisionsCloseSession267V1();DecisionsCloseSession267V1(const DecisionsCloseSession267V1&)=delete;DecisionsCloseSession267V1&operator=(const DecisionsCloseSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteDecisionsCloseInner267V1(DecisionsCloseContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockDecisionsCloseUnknown267V1(DecisionsCloseSession267V1&)noexcept;
};
struct DecisionsCloseContext267V1{
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 DecisionsCloseRequest267V1 request{};DecisionsCloseResult267V1 result{};DecisionsCloseSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;
};
DecisionsCloseSession267V1& RetainedDecisionsCloseSession267V1();
void ArmDecisionsCloseDeadline267V1(DecisionsCloseContext267V1&)noexcept;
void BlockDecisionsCloseUnknown267V1(DecisionsCloseSession267V1&)noexcept;
bool ExecuteDecisionsCloseOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadDecisionsCloseFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,DecisionsCloseFrame267V1&,std::string&)noexcept;
bool DecisionsCloseStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchDecisionsCloseRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
} // namespace
