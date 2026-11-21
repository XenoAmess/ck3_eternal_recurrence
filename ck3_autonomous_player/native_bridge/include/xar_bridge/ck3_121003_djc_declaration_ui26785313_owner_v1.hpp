#pragma once
#include "xar_bridge/ck3_121003_djc_declaration_ui26785313_raw_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct DjcUiFrame267V1{bool facts_verified=false;ck3_1210::CoreSnapshotPrefix core{};DjcUiExpectedScene267V1 scene{};std::vector<GuiWindowNodeV1>witness;};
struct DjcUiContext267V1;
class DjcUiSession267V1{
 public:DjcUiSession267V1();~DjcUiSession267V1();DjcUiSession267V1(const DjcUiSession267V1&)=delete;DjcUiSession267V1&operator=(const DjcUiSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteDjcUiInner267V1(DjcUiContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockDjcUiUnknown267V1(DjcUiSession267V1&)noexcept;
};
struct DjcUiContext267V1{
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 DjcUiRequest267V1 request{};DjcUiResult267V1 result{};DjcUiSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;
};
void ArmDjcUiDeadline267V1(DjcUiContext267V1&)noexcept;
void BlockDjcUiUnknown267V1(DjcUiSession267V1&)noexcept;
bool ExecuteDjcUiOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadDjcUiFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t wall,std::uint64_t mono,DjcUiFrame267V1&,std::string&)noexcept;
bool DjcUiStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchDjcUiRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
} // namespace
