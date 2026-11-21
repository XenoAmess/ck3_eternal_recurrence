#pragma once
#include "xar_bridge/ck3_121003_letter26785313_raw_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct LetterFrame267V1{bool facts_verified=false;ck3_1210::CoreSnapshotPrefix core{};LetterScene267V1 scene{};std::vector<GuiWindowNodeV1>witness;};
struct LetterContext267V1;
class LetterSession267V1{
 public:LetterSession267V1();~LetterSession267V1();LetterSession267V1(const LetterSession267V1&)=delete;LetterSession267V1&operator=(const LetterSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteLetterInner267V1(LetterContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockLetterUnknown267V1(LetterSession267V1&)noexcept;
};
struct LetterContext267V1{
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 LetterRequest267V1 request{};LetterResult267V1 result{};LetterSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;
};
void ArmLetterDeadline267V1(LetterContext267V1&)noexcept;
void BlockLetterUnknown267V1(LetterSession267V1&)noexcept;
bool ExecuteLetterOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadLetterFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,LetterFrame267V1&,std::string&)noexcept;
bool LetterStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchLetterRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
} // namespace
