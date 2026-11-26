#pragma once
#include "xar_bridge/ck3_121003_lyd26785313_raw_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct LydFrame267V1{
 bool facts_verified=false;ck3_1210::CoreSnapshotPrefix core{};LydScene267V1 scene{};
 std::vector<GuiWindowNodeV1>witness;std::vector<std::byte>name_witness;
};
struct LydContext267V1;
class LydSession267V1{
 public:LydSession267V1();~LydSession267V1();LydSession267V1(const LydSession267V1&)=delete;LydSession267V1&operator=(const LydSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteLydInner267V1(LydContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockLydUnknown267V1(LydSession267V1&)noexcept;
};
struct LydContext267V1{
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 LydRequest267V1 request{};LydResult267V1 result{};LydSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;
 bool native_observation_entered=false,full111_ordinary_events_only=false;
};
LydSession267V1&RetainedLydSession267V1();
void ArmLydDeadline267V1(LydContext267V1&)noexcept;
void BlockLydUnknown267V1(LydSession267V1&)noexcept;
bool ExecuteLydInner267V1(LydContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ExecuteLydOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadLydFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,
 const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,
 LydKind267V1,std::uint64_t,std::uint64_t,LydFrame267V1&,std::string&)noexcept;
bool LydStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchLydRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
