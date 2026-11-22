#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
#include <vector>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kSupermanHealthRequestSchema267V1[]="ck3.superman_health.current267_request.v1";
inline constexpr char kSupermanHealthResultSchema267V1[]="ck3.superman_health.current267_result.v1";
inline constexpr char kSupermanHealthSourceSchema267V1[]="ck3.superman_health.current267_source.v1";
inline constexpr char kSupermanHealthBackend267V1[]="ck3-1.21.0.3-native-application-main-superman-health";
inline constexpr std::array<std::string_view,2>kSupermanHealthSteps267V1{"query-superman-health-current-v1","select-superman-health-known-option-current-v1"};
inline constexpr std::array<std::string_view,2>kSupermanHealthCapabilities267V1{"game.query.current-superman-health.v1","game.command.select-current-superman-health-known-option.v1"};
enum class SupermanHealthAction267V1{query_health,choose_known};
enum class SupermanHealthPhase267V1{baseline,completed};
enum class SupermanHealthStatus267V1{unavailable,expired,stale_source,claim_consumed,available,known_choice_dispatched,indeterminate};
inline constexpr std::array<std::string_view,20>kSupermanHealthCases267V1{"player-native-health-75","health-flat-75","health-floor-below-3_00074","health-floor-at-3_00075","health-floor-same-day-repeat","health-penalty-mitigation","health-rebuild-idempotent","health-ledger-growth","health-ledger-to-zero","health-upper-balance-block","health-upper-balance-last","health-lower-balance-block","health-lower-balance-last","six-skill-diplomacy-regression","six-skill-prowess-regression","equal-experience-health-no-transfer","only-health-eligible-dispatch","health-zero-receiver","health-negative-receiver","health-reverse-capacity-boundaries"};
inline constexpr std::array<std::string_view,14>kSupermanHealthValueNames267V1{"sxad_diplomacy_value","sxad_martial_value","sxad_stewardship_value","sxad_intrigue_value","sxad_learning_value","sxad_prowess_value","sxad_health_value","sxad_diplomacy_balance_value","sxad_martial_balance_value","sxad_stewardship_balance_value","sxad_intrigue_balance_value","sxad_learning_balance_value","sxad_prowess_balance_value","sxad_health_balance_value"};
struct SupermanHealthRequest267V1{
 SupermanHealthAction267V1 action=SupermanHealthAction267V1::query_health;SupermanHealthPhase267V1 phase=SupermanHealthPhase267V1::baseline;
 ck3_1210::CoreSnapshotPrefix expected{};std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;
 std::array<char,97>request_id{};std::uint8_t request_id_size=0;std::string_view id()const noexcept{return{request_id.data(),request_id_size};}
};
struct SupermanHealthCharacter267V1{
 std::string case_key,role;std::int32_t character_id=-1;std::array<std::int64_t,14>values{};
 friend bool operator==(const SupermanHealthCharacter267V1&,const SupermanHealthCharacter267V1&)=default;
};
struct SupermanHealthOption267V1{
 std::int32_t authored_option_index=-1;std::string text,disabled_reason;bool native_can_select=false;std::optional<std::string>source_bound_option_key;
 friend bool operator==(const SupermanHealthOption267V1&,const SupermanHealthOption267V1&)=default;
};
struct SupermanHealthSource267V1{
 SupermanHealthPhase267V1 phase=SupermanHealthPhase267V1::baseline;bool fixture_state_available=false;
 std::optional<std::int64_t>baseline_ready_raw,matrix_done_raw;std::int32_t reference_count=0;std::vector<SupermanHealthCharacter267V1>characters;
 bool event_census_complete=false;std::int32_t named_root_count=0;bool event_found=false,named_root_bound=false,window_visible=false,window_enabled=false;
 std::optional<std::int32_t>instance_id,recipient_character_id,authored_option_count;std::optional<std::string>definition_key,opening,description;
 std::vector<SupermanHealthOption267V1>options;bool native_choice_admissible=false;
 friend bool operator==(const SupermanHealthSource267V1&,const SupermanHealthSource267V1&)=default;
};
struct SupermanHealthResult267V1{
 SupermanHealthAction267V1 action=SupermanHealthAction267V1::query_health;SupermanHealthPhase267V1 phase=SupermanHealthPhase267V1::baseline;SupermanHealthStatus267V1 status=SupermanHealthStatus267V1::unavailable;
 bool source_available=false,effect_attempted=false,native_returned=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;
 ck3_1210::CoreSnapshotPrefix facts{};std::optional<SupermanHealthSource267V1>source;std::string reason;
};
bool SupermanHealthRequestShape267V1(const SupermanHealthRequest267V1&)noexcept;
bool ParseSupermanHealthRequest267V1(std::string_view,SupermanHealthRequest267V1&)noexcept;
std::string SerializeSupermanHealthResult267V1(std::string_view,const SupermanHealthResult267V1&);
}
