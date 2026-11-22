#pragma once
#include "xar_bridge/ck3_121003_courtier_controls26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_courtier_controls26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct CourtierControlsFrame267V1{bool facts_verified=false,native_read_entered=false,cleanup_known=true;ck3_1210::CoreSnapshotPrefix core{};CourtierControlsScene267V1 scene{};std::vector<GuiWindowNodeV1>witness;};
struct CourtierControlsContext267V1;
class CourtierControlsSession267V1{
 public:CourtierControlsSession267V1();~CourtierControlsSession267V1();CourtierControlsSession267V1(const CourtierControlsSession267V1&)=delete;CourtierControlsSession267V1&operator=(const CourtierControlsSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteCourtierControlsInner267V1(CourtierControlsContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockCourtierControlsUnknown267V1(CourtierControlsSession267V1&)noexcept;
};
struct CourtierControlsContext267V1{
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 CourtierControlsRequest267V1 request{};CourtierControlsResult267V1 result{};CourtierControlsSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;
};
CourtierControlsSession267V1& RetainedCourtierControlsSession267V1();
void ArmCourtierControlsDeadline267V1(CourtierControlsContext267V1&)noexcept;
void BlockCourtierControlsUnknown267V1(CourtierControlsSession267V1&)noexcept;
bool ExecuteCourtierControlsOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadCourtierControlsFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,CourtierControlsFrame267V1&,std::string&)noexcept;
bool CourtierControlsStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchCourtierControlsRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
} // namespace
