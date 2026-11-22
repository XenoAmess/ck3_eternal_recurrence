#pragma once
#include "xar_bridge/ck3_121003_letter26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
inline constexpr char kDesInitGuardRequestSchema267V1[]="ck3.des_saved_game_init_guard.current267_request.v1";
inline constexpr char kDesInitGuardResultSchema267V1[]="ck3.des_saved_game_init_guard.current267_result.v1";
inline constexpr char kDesInitGuardSourceSchema267V1[]="ck3.des_saved_game_init_guard.current267_source.v1";
inline constexpr char kDesInitGuardBackend267V1[]="ck3-1.21.0.3-native-application-main-des-init-guard";
inline constexpr char kDesInitGuardStep267V1[]="query-des-saved-game-init-guard-current-v1";
inline constexpr char kDesInitGuardCapability267V1[]="game.query.des-saved-game-init-guard-current.v1";
inline constexpr char kDesInitGuardKey267V1[]="des_saved_game_initialize_gui";
enum class DesInitGuardStatus267V1{unavailable,expired,stale_source,available,indeterminate};
struct DesInitGuardRequest267V1{
 ck3_1210::CoreSnapshotPrefix expected{};std::uint64_t deadline_unix_ms=0;
 std::array<char,97>request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return{request_id.data(),request_id_size};}
};
struct DesInitGuardSource267V1{
 std::int32_t character_id=-1;
 bool character_alive=false,native_is_player=false,native_definition_found=false,native_shown=false,scope_bound=false,sampled_twice=false;
 friend bool operator==(const DesInitGuardSource267V1&,const DesInitGuardSource267V1&)=default;
};
struct DesInitGuardResult267V1{
 DesInitGuardStatus267V1 status=DesInitGuardStatus267V1::unavailable;
 bool source_available=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;
 ck3_1210::CoreSnapshotPrefix facts{};std::optional<DesInitGuardSource267V1>source;std::string reason;
};
bool DesInitGuardRequestShape267V1(const DesInitGuardRequest267V1&)noexcept;
bool ParseDesInitGuardRequest267V1(std::string_view,DesInitGuardRequest267V1&)noexcept;
std::string SerializeDesInitGuardResult267V1(std::string_view,const DesInitGuardResult267V1&);
}
