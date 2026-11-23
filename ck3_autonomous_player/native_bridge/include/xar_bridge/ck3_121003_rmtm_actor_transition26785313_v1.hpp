#pragma once
// External RMTM source candidate; NOT_COMPILED/NOT_QUALIFIED. Independent of TED public permission.
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kRmtmTransitionRequestSchema267V1[]="ck3.rmtm_actor_transition.current267_request.v1";
inline constexpr char kRmtmTransitionResultSchema267V1[]="ck3.rmtm_actor_transition.current267_result.v1";
inline constexpr char kRmtmTransitionSourceSchema267V1[]="ck3.rmtm_actor_transition.current267_source.v1";
inline constexpr char kRmtmTransitionBackend267V1[]="ck3-1.21.0.3-native-application-main-rmtm-actor-transition";
inline constexpr std::array<std::string_view,4>kRmtmTransitionSteps267V1{
 "query-current-rmtm-role-v1","advance-current-rmtm-one-day-v1",
 "query-current-rmtm-one-day-v1","confirm-current-rmtm-actor-epoch-v1"};
inline constexpr std::array<std::string_view,3>kRmtmTransitionCapabilities267V1{
 "game.query.current-rmtm-actor-transition.v1","game.command.current-rmtm-one-day.v1",
 "game.command.confirm-current-rmtm-actor-epoch.v1"};
inline constexpr std::uint32_t kRmtmMaximumNaturalDays267V1=14;
inline constexpr char kRmtmSongWitnessKey267V1[]="rqa120_native_song_role_gui";
inline constexpr char kRmtmSuccessorWitnessKey267V1[]="rqa120_native_successor_role_gui";
enum class RmtmTransitionAction267V1{query_role,advance_day,query_operation,confirm_epoch};
enum class RmtmActorRole267V1{song,successor};
enum class RmtmTransitionStatus267V1{unavailable,expired,stale_source,claim_consumed,
 capacity_exhausted,available,submitted,running,completed_day,transition_pending,epoch_confirmed,indeterminate};
struct RmtmTransitionRequest267V1{
 RmtmTransitionAction267V1 action=RmtmTransitionAction267V1::query_role;
 ck3_1210::CoreSnapshotPrefix expected{};
 std::uint64_t provider_generation=0,query_sequence=0,actor_epoch=0,deadline_unix_ms=0;
 std::array<char,97>request_id{},operation_id{};std::uint8_t request_id_size=0,operation_id_size=0;
};
struct RmtmPendingTransition267V1{
 std::string operation_id;
 std::uint64_t claim_sequence=0,generation=0,original_deadline_unix_ms=0;
 std::int32_t before_actor_id=-1,after_actor_id=-1,starting_date_raw=0,target_date_raw=0;
 std::uint32_t completed_daily_ticks=0;
 bool exact_day_confirmed=false,shutdown_safe=false,cleanup_known=true;
 friend bool operator==(const RmtmPendingTransition267V1&,const RmtmPendingTransition267V1&)=default;
};
struct RmtmTransitionSource267V1{
 RmtmActorRole267V1 role=RmtmActorRole267V1::song;
 bool definition_found=false;std::optional<bool>native_shown;
 std::uint64_t actor_epoch=0;
 std::optional<std::int32_t>song_actor_id,successor_actor_id;
 std::optional<RmtmPendingTransition267V1>pending;
 std::uint32_t completed_natural_days=0,maximum_natural_days=14;std::int32_t case_start_date_raw=0;
 bool case_start_captured=false;std::optional<bool>execute_time_identity_confirmed;
 bool runtime_ready=false,predecessor_resolved=false,advance_admissible=false,confirm_admissible=false;
 friend bool operator==(const RmtmTransitionSource267V1&,const RmtmTransitionSource267V1&)=default;
};
struct RmtmTransitionProgress267V1{
 std::uint64_t generation=0;
 std::int32_t starting_date_raw=0,target_date_raw=0,last_observed_date_raw=0,before_actor_id=-1,after_actor_id=-1;
 std::uint32_t completed_daily_ticks=0,failure_flags=0;
 std::int32_t overshoot_days=0;
 bool arm_attempted=false,resume_attempted=false,resume_submitted=false,exact_day_confirmed=false,
  transition_pending=false,shutdown_safe=false,armed=false,access_cleanup_unknown=false;
};
struct RmtmTransitionResult267V1{
 RmtmTransitionAction267V1 action=RmtmTransitionAction267V1::query_role;
 RmtmTransitionStatus267V1 status=RmtmTransitionStatus267V1::unavailable;
 std::string request_id,operation_id,reason;
 bool accepted=false,source_available=false,effect_attempted=false,native_returned=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,actor_epoch=0,deadline_unix_ms=0,
  connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;
 std::uint32_t completed_natural_days=0;
 ck3_1210::CoreSnapshotPrefix facts{};std::optional<RmtmTransitionSource267V1>source;
 std::optional<RmtmTransitionProgress267V1>progress;
};
} // namespace
