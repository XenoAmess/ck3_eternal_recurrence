#pragma once
#include "xar_bridge/ck3_121003_courtier_choices26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_courtier_choices26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct CourtierChoicesFrame267V1{bool facts_verified=false,native_read_entered=false,cleanup_known=true;ck3_1210::CoreSnapshotPrefix core{};CourtierChoicesScene267V1 scene{};std::vector<GuiWindowNodeV1>witness;};
struct CourtierChoicesContext267V1;
class CourtierChoicesSession267V1{
 public:CourtierChoicesSession267V1();~CourtierChoicesSession267V1();CourtierChoicesSession267V1(const CourtierChoicesSession267V1&)=delete;CourtierChoicesSession267V1&operator=(const CourtierChoicesSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteCourtierChoicesInner267V1(CourtierChoicesContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockCourtierChoicesUnknown267V1(CourtierChoicesSession267V1&)noexcept;
};
struct CourtierChoicesContext267V1{
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 CourtierChoicesRequest267V1 request{};CourtierChoicesResult267V1 result{};CourtierChoicesSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;
};
CourtierChoicesSession267V1& RetainedCourtierChoicesSession267V1();
void ArmCourtierChoicesDeadline267V1(CourtierChoicesContext267V1&)noexcept;
void BlockCourtierChoicesUnknown267V1(CourtierChoicesSession267V1&)noexcept;
bool ExecuteCourtierChoicesOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadCourtierChoicesFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,CourtierChoicesFrame267V1&,std::string&)noexcept;
bool CourtierChoicesStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchCourtierChoicesRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
} // namespace
