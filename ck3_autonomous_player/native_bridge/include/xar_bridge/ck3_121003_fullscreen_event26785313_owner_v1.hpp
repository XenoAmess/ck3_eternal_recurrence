#pragma once
#include "xar_bridge/ck3_121003_fullscreen_event26785313_raw_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct FullscreenEventFrame267V1{bool facts_verified=false;ck3_1210::CoreSnapshotPrefix core{};FullscreenEventScene267V1 scene{};std::vector<GuiWindowNodeV1>witness;};
struct FullscreenEventContext267V1;
class FullscreenEventSession267V1{
 public:FullscreenEventSession267V1();~FullscreenEventSession267V1();FullscreenEventSession267V1(const FullscreenEventSession267V1&)=delete;FullscreenEventSession267V1&operator=(const FullscreenEventSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteFullscreenEventInner267V1(FullscreenEventContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockFullscreenEventUnknown267V1(FullscreenEventSession267V1&)noexcept;
};
struct FullscreenEventContext267V1{
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 FullscreenEventRequest267V1 request{};FullscreenEventResult267V1 result{};FullscreenEventSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;
};
FullscreenEventSession267V1& RetainedFullscreenEventSession267V1();
void ArmFullscreenEventDeadline267V1(FullscreenEventContext267V1&)noexcept;
void BlockFullscreenEventUnknown267V1(FullscreenEventSession267V1&)noexcept;
bool ExecuteFullscreenEventOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadFullscreenEventFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,FullscreenEventFrame267V1&,std::string&)noexcept;
bool FullscreenEventStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchFullscreenEventRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
} // namespace
