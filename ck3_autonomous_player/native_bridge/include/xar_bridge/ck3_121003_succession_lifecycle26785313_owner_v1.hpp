#pragma once
#include "xar_bridge/ck3_121003_succession_continue26785313_raw_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct SuccessionLifecycleFrame267V1 {
 bool world_verified=false;ck3_1210::CoreSnapshotPrefix world{};GuiWindowV1 window{};
 std::uintptr_t game_state=0,jomini=0,storage=0,game_data=0,player_entries=0,gfx=0,handler=0;
 std::int32_t player_count=0;std::uint32_t default_button_index=UINT32_MAX;
};
struct SuccessionContext267V1;
class SuccessionSession267V1 {
 public:SuccessionSession267V1();~SuccessionSession267V1();
 SuccessionSession267V1(const SuccessionSession267V1&)=delete;
 SuccessionSession267V1&operator=(const SuccessionSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteSuccessionLifecycleInner267V1(SuccessionContext267V1&,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
 friend void BlockSuccessionUnknown267V1(SuccessionSession267V1&) noexcept;
};
struct SuccessionContext267V1 {
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 SuccessionRequest267V1 request{};SuccessionResult267V1 result{};SuccessionSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;
};
bool ReadSuccessionLifecycleFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,
 const ck3_11906::MainThreadQueryTicketV1&,const ck3_11906::MainThreadExecutionStampV1&,void*,
 std::uint64_t connection,std::uint64_t deadline_unix_ms,std::uint64_t monotonic_deadline_ms,
 SuccessionLifecycleFrame267V1&,std::string&) noexcept;
void ArmSuccessionDeadline267V1(SuccessionContext267V1&) noexcept;
void BlockSuccessionUnknown267V1(SuccessionSession267V1&) noexcept;
bool ExecuteSuccessionLifecycleOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
bool SuccessionStepEnabled267V1(const game::AdapterDescriptor&,std::string_view) noexcept;
std::string DispatchSuccessionRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,
 std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
}
