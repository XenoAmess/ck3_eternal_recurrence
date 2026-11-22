#pragma once
#include "xar_bridge/ck3_121003_courtier_configuration26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_courtier_configuration26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>
namespace xar::ck3_121003::build26785313 {
struct CourtierConfigurationFrame267V1{bool facts_verified=false,native_read_entered=false,cleanup_known=true;ck3_1210::CoreSnapshotPrefix core{};CourtierConfigurationScene267V1 scene{};std::vector<GuiWindowNodeV1>witness;};
struct CourtierConfigurationContext267V1;
class CourtierConfigurationSession267V1{
 public:CourtierConfigurationSession267V1();~CourtierConfigurationSession267V1();CourtierConfigurationSession267V1(const CourtierConfigurationSession267V1&)=delete;CourtierConfigurationSession267V1&operator=(const CourtierConfigurationSession267V1&)=delete;
 private:struct State;std::unique_ptr<State>state_;
 friend bool ExecuteCourtierConfigurationInner267V1(CourtierConfigurationContext267V1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
 friend void BlockCourtierConfigurationUnknown267V1(CourtierConfigurationSession267V1&)noexcept;
};
struct CourtierConfigurationContext267V1{
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1*mailbox=nullptr;ck3_11906::MainThreadQueryTicketV1 ticket{};
 CourtierConfigurationRequest267V1 request{};CourtierConfigurationResult267V1 result{};CourtierConfigurationSession267V1*session=nullptr;
 std::uint64_t connection_generation=0,monotonic_deadline_ms=0;bool native_observation_entered=false;
};
CourtierConfigurationSession267V1& RetainedCourtierConfigurationSession267V1();
void ArmCourtierConfigurationDeadline267V1(CourtierConfigurationContext267V1&)noexcept;
void BlockCourtierConfigurationUnknown267V1(CourtierConfigurationSession267V1&)noexcept;
bool ExecuteCourtierConfigurationOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
bool ReadCourtierConfigurationFrameOnOwner267V1(const ReadonlyBindings&,ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,std::uint64_t,std::uint64_t,CourtierConfigurationFrame267V1&,std::string&)noexcept;
bool CourtierConfigurationStepEnabled267V1(const game::AdapterDescriptor&,std::string_view)noexcept;
std::string DispatchCourtierConfigurationRequest267V1(const game::GameAdapter&,std::uint64_t,std::string_view,std::string_view,std::string_view,ck3_11906::MainThreadQueryMailboxV1&);
} // namespace
