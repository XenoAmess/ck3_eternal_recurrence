#pragma once
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ck3_121003_commands26785313_v1.hpp"
#include "xar_bridge/ck3_1210_date_sentinel_v1.hpp"
#include <array>

namespace xar::ck3_121003::build26785313 {
inline constexpr char kDateAdvanceStep267V1[]="advance-date-one-day-v1";
inline constexpr char kDateAdvanceStatusStep267V1[]="query-date-one-day-v1";
inline constexpr char kDateAdvanceSchema267V1[]="ck3.current_date_advance_request.v1";
inline constexpr char kDateAdvanceResultSchema267V1[]="ck3.current_date_advance.v1";
inline constexpr char kDateAdvanceCapability267V1[]="game.command.current-date-one-day.v1";
struct DateAdvanceRequest267V1 {
 std::array<char,97> request_id{},operation_id{};
 std::uint8_t request_id_size=0,operation_id_size=0;
 bool status_query=false;
 ck3_1210::CoreSnapshotPrefix expected_core{};
 std::uint64_t deadline_unix_ms=0;
 std::string_view id() const noexcept{return {request_id.data(),request_id_size};}
 std::string_view operation() const noexcept{return {operation_id.data(),operation_id_size};}
 std::string_view step() const noexcept{return status_query?kDateAdvanceStatusStep267V1:kDateAdvanceStep267V1;}
};
enum class DateAdvanceStatus267V1 {unavailable,expired,stale_core,source_changed,claim_consumed,
 capacity_exhausted,submitted,running,completed,rejected,indeterminate};
struct DateAdvanceResult267V1 {
 DateAdvanceStatus267V1 status=DateAdvanceStatus267V1::unavailable;
 bool claim_found=false,owner_before_verified=false,arm_attempted=false,resume_attempted=false,resume_submitted=false;
 bool exact_day_confirmed=false,shutdown_safe=false,access_cleanup_unknown=false,armed=false;
 std::uint64_t claim_sequence=0,generation=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0,failure_flags=0;
 ck3_1210::CoreSnapshotPrefix core_before{};
 ck3_11906::TacticalDailySentinelStatusV1 sentinel{};
};
struct DateAdvanceSource267V1 {std::uintptr_t module_base=0,game_state=0,jomini_state=0;};
// Permanent process-lifetime custody. Neither disconnect nor a changed action
// ID can retire UNKNOWN. Only an actual exact-day terminal admits a later date.
class DateAdvanceSession267V1 {
 public:
 DateAdvanceSession267V1() noexcept=default;
 DateAdvanceSession267V1(const DateAdvanceSession267V1&)=delete;
 DateAdvanceSession267V1&operator=(const DateAdvanceSession267V1&)=delete;
 private:
 struct Claim {DateAdvanceRequest267V1 request{};DateAdvanceSource267V1 source{};DateAdvanceResult267V1 result{};};
 SRWLOCK lock_=SRWLOCK_INIT;
 std::array<Claim,64> claims_{};std::size_t size_=0;bool unknown_=false;
 ck3_1210::DateSentinelStateV1 *runtime_=nullptr;
 friend bool BindDateAdvanceSession267V1(DateAdvanceSession267V1&,ck3_1210::DateSentinelStateV1&) noexcept;
 friend bool DateAdvanceRuntimeMatches267V1(DateAdvanceSession267V1&,const ck3_1210::DateSentinelStateV1&) noexcept;
 friend bool ClaimDateAdvance267V1(DateAdvanceSession267V1&,const DateAdvanceRequest267V1&,
  const DateAdvanceSource267V1&,DateAdvanceResult267V1&) noexcept;
 friend void StoreDateAdvance267V1(DateAdvanceSession267V1&,const DateAdvanceResult267V1&) noexcept;
 friend DateAdvanceResult267V1 QueryDateAdvance267V1(DateAdvanceSession267V1&,
  const DateAdvanceRequest267V1&,const ck3_1210::DateSentinelStateV1&) noexcept;
 friend void BlockDateAdvanceUnknown267V1(DateAdvanceSession267V1&) noexcept;
};
bool DateAdvanceRequestShape267V1(const DateAdvanceRequest267V1&) noexcept;
// One permanent typed binding from the actual initialized a43 runtime. This
// reuses its production factory; no fixture/state/qualification bool is input.
bool BindDateAdvanceSession267V1(DateAdvanceSession267V1&,ck3_1210::DateSentinelStateV1&) noexcept;
bool DateAdvanceRuntimeMatches267V1(DateAdvanceSession267V1&,const ck3_1210::DateSentinelStateV1&) noexcept;
bool ClaimDateAdvance267V1(DateAdvanceSession267V1&,const DateAdvanceRequest267V1&,
 const DateAdvanceSource267V1&,DateAdvanceResult267V1&) noexcept;
void StoreDateAdvance267V1(DateAdvanceSession267V1&,const DateAdvanceResult267V1&) noexcept;
void BlockDateAdvanceUnknown267V1(DateAdvanceSession267V1&) noexcept;
// Pure status read: exact original claim body, including its original deadline.
// Expired status lookup is allowed, but never refreshes or authorizes an action.
DateAdvanceResult267V1 QueryDateAdvance267V1(DateAdvanceSession267V1&,
 const DateAdvanceRequest267V1&,const ck3_1210::DateSentinelStateV1&) noexcept;
struct DateAdvanceContext267V1 {
 ReadonlyBindings bindings{};ck3_11906::MainThreadQueryMailboxV1 *mailbox=nullptr;
 ck3_11906::MainThreadQueryTicketV1 ticket{};DateAdvanceRequest267V1 request{};
 DateAdvanceSession267V1 *session=nullptr;ck3_1210::DateSentinelStateV1 *sentinel=nullptr;
 DateAdvanceResult267V1 result{};std::uint64_t connection_generation=0,monotonic_deadline_ms=0;
 bool command_ownership_entered=false;
};
void ArmDateAdvanceDeadline267V1(DateAdvanceContext267V1&) noexcept;
bool ExecuteDateAdvanceOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&) noexcept;
bool ReadDateAdvanceCoreOnOwner267V1(const ReadonlyBindings&,
 ck3_11906::MainThreadQueryMailboxV1*,const ck3_11906::MainThreadQueryTicketV1&,
 const ck3_11906::MainThreadExecutionStampV1&,void*,ReadonlyObservation&) noexcept;
bool DateAdvanceRouteEnabled267V1(const game::AdapterDescriptor&) noexcept;
bool ParseDateAdvanceRequest267V1(std::string_view,DateAdvanceRequest267V1&) noexcept;
std::string SerializeDateAdvanceResult267V1(std::string_view,const DateAdvanceRequest267V1&,const DateAdvanceResult267V1&);
} // namespace
