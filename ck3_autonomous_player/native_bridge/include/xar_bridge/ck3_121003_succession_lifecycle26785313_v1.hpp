#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kSuccessionRequestSchema267V1[]="ck3.succession_lifecycle.current267_request.v1";
inline constexpr char kSuccessionResultSchema267V1[]="ck3.succession_lifecycle.current267_result.v1";
inline constexpr char kSuccessionWorldSchema267V1[]="ck3.succession_world.current267_prefix.v1";
inline constexpr char kSuccessionSourceSchema267V1[]="ck3.succession_default_source.current267.v1";
inline constexpr char kSuccessionBackend267V1[]="ck3-1.21.0.3-native-application-main-succession";
inline constexpr char kSuccessionQueryStep267V1[]="query-current-succession-default-v1";
inline constexpr char kSuccessionContinueStep267V1[]="continue-current-succession-default-v1";
inline constexpr char kSuccessionQueryCapability267V1[]="game.query.current-succession-default.v1";
inline constexpr char kSuccessionContinueCapability267V1[]="game.command.current-succession-default-continue.v1";
enum class SuccessionAction267V1 {query_default,continue_default};
enum class SuccessionStatus267V1 {unavailable,expired,stale_source,claim_consumed,available,dispatched,indeterminate};
enum class SuccessionPlayerRelation267V1 {pending_predecessor,heir_already_assigned,unassigned_during_transition};
struct SuccessionRequest267V1 {
 SuccessionAction267V1 action=SuccessionAction267V1::query_default;
 std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;
 std::int32_t expected_dead_character_id=-1,expected_continue_character_id=-1;
 std::array<char,97>request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return {request_id.data(),request_id_size};}
};
struct SuccessionSource267V1 {
 std::int32_t dead_character_id=-1,continue_character_id=-1;
 SuccessionPlayerRelation267V1 player_relation=SuccessionPlayerRelation267V1::unassigned_during_transition;
 bool dead_character_dead=false,continue_character_alive=false;
 bool handler_source_verified=false,named_root_bound=false,window_visible=false,window_enabled=false;
 bool default_button_admissible=false,default_native_route=false,stable_two_pass_verified=false;
};
struct SuccessionResult267V1 {
 SuccessionAction267V1 action=SuccessionAction267V1::query_default;
 SuccessionStatus267V1 status=SuccessionStatus267V1::unavailable;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0;
 bool source_available=false,world_available=false,effect_attempted=false,native_returned=false;
 ck3_1210::CoreSnapshotPrefix world{};std::optional<SuccessionSource267V1>source;
 std::uint64_t connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;
 std::string reason;
};
// This family never creates a living CoreFrame or a CoreReceived authority.
bool SuccessionRequestShape267V1(const SuccessionRequest267V1&) noexcept;
bool ParseSuccessionRequest267V1(std::string_view,SuccessionRequest267V1&) noexcept;
std::string SerializeSuccessionResult267V1(std::string_view,const SuccessionResult267V1&);
}
