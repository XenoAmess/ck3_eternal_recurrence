#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
#include <vector>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kDjcUiRequestSchema267V1[]="ck3.djc_declaration_ui.current267_request.v1";
inline constexpr char kDjcUiResultSchema267V1[]="ck3.djc_declaration_ui.current267_result.v1";
inline constexpr char kDjcUiSourceSchema267V1[]="ck3.djc_declaration_ui.current267_source.v1";
inline constexpr char kDjcUiBackend267V1[]="ck3-1.21.0.3-native-application-main-djc-ui";
inline constexpr std::array<std::string_view,6> kDjcUiSteps267V1{
 "query-current-djc-declaration-ui-v1","open-current-djc-declaration-ui-v1",
 "select-current-djc-declaration-choice-v1","send-current-djc-declaration-ui-v1",
 "query-current-djc-declaration-warning-v1","accept-current-djc-declaration-warning-v1"};
inline constexpr std::array<std::string_view,6> kDjcUiCapabilities267V1{
 "game.query.current-djc-declaration-ui.v1","game.command.open-current-djc-declaration-ui.v1",
 "game.command.select-current-djc-declaration-choice.v1","game.command.send-current-djc-declaration-ui.v1",
 "game.query.current-djc-declaration-warning.v1","game.command.accept-current-djc-declaration-warning.v1"};
inline constexpr std::array<std::string_view,3> kDjcUiCbKeys267V1{
 "duchy_de_jure_greatwar","kingdom_de_jure_greatwar","empire_de_jure_greatwar"};
enum class DjcUiAction267V1 {query_ui,open_ui,select_choice,send_ui,query_warning,accept_warning};
enum class DjcUiStatus267V1 {unavailable,expired,stale_source,claim_consumed,available,open_dispatched,
 selection_dispatched,send_dispatched,warning_pending,warning_ready,warning_dispatched,indeterminate};
struct DjcUiRequest267V1 {
 DjcUiAction267V1 action=DjcUiAction267V1::query_ui;ck3_1210::CoreSnapshotPrefix expected{};
 std::int32_t target_character_id=-1;std::uint8_t cb=0;
 std::uint64_t provider_generation=0,query_sequence=0,choice_token=0,origin_claim_sequence=0,deadline_unix_ms=0;
 std::array<char,97> request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return {request_id.data(),request_id_size};}
};
struct DjcUiTuple267V1 {
 std::string cb_key;std::int32_t claimant_character_id=-1;
 std::vector<std::int32_t>target_title_ids,extra_configuration_ids;bool source_row_enabled=false;
 friend bool operator==(const DjcUiTuple267V1&,const DjcUiTuple267V1&)=default;
};
struct DjcUiChoice267V1 {std::uint64_t choice_token=0;DjcUiTuple267V1 tuple;
 friend bool operator==(const DjcUiChoice267V1&,const DjcUiChoice267V1&)=default;};
struct DjcUiSource267V1 {
 std::int32_t target_character_id=-1;std::string cb_key;
 bool interaction_definition_verified=false;std::uint8_t loaded_interface=0;
 std::optional<bool>native_confirmation,native_is_valid;bool open_admissible=false,resident_available=false;
 bool named_root_bound=false,window_visible=false,window_enabled=false;
 std::int32_t actor_id=-1,recipient_id=-1,additional_role_id=-1;
 std::optional<DjcUiTuple267V1>selected;std::vector<DjcUiChoice267V1>choices;
 std::optional<bool>native_can_send;bool send_admissible=false,warning_source_available=false;
 std::optional<bool>native_can_accept;bool accept_admissible=false;
};
struct DjcUiResult267V1 {
 DjcUiAction267V1 action=DjcUiAction267V1::query_ui;DjcUiStatus267V1 status=DjcUiStatus267V1::unavailable;
 bool source_available=false,effect_attempted=false,native_returned=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix facts{};std::optional<DjcUiSource267V1>source;std::string reason;
};
bool DjcUiRequestShape267V1(const DjcUiRequest267V1&)noexcept;
bool ParseDjcUiRequest267V1(std::string_view,DjcUiRequest267V1&)noexcept;
std::string SerializeDjcUiResult267V1(std::string_view,const DjcUiResult267V1&);
} // namespace xar::ck3_121003::build26785313
