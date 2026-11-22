#pragma once
#include "xar_bridge/ck3_121003_letter26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
inline constexpr char kCourtierControlsRequestSchema267V1[]="ck3.courtier_creator_controls.current267_request.v1";
inline constexpr char kCourtierControlsResultSchema267V1[]="ck3.courtier_creator_controls.current267_result.v1";
inline constexpr char kCourtierControlsSourceSchema267V1[]="ck3.courtier_creator_controls.current267_source.v1";
inline constexpr char kCourtierControlsBackend267V1[]="ck3-1.21.0.3-native-application-main-courtier-creator-controls";
inline constexpr std::array<std::string_view,2>kCourtierControlsSteps267V1{"query-courtier-creator-controls-current-v1","execute-courtier-creator-control-current-v1"};
inline constexpr std::array<std::string_view,2>kCourtierControlsCapabilities267V1{"game.query.current-courtier-creator-controls.v1","game.command.execute-current-courtier-creator-control.v1"};
enum class CourtierProduct267V1{main,vivhite};
enum class CourtierControl267V1{cancel,confirm,age_minus_one,age_plus_one};
enum class CourtierControlsAction267V1{query_control,execute_control};
enum class CourtierControlsStatus267V1{unavailable,expired,stale_source,claim_consumed,available,control_dispatched,indeterminate};
struct CourtierControlsRequest267V1{
 CourtierControlsAction267V1 action=CourtierControlsAction267V1::query_control;
 CourtierProduct267V1 product=CourtierProduct267V1::main;CourtierControl267V1 control=CourtierControl267V1::cancel;
 ck3_1210::CoreSnapshotPrefix expected{};std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;
 std::array<char,97>request_id{};std::uint8_t request_id_size=0;std::string_view id()const noexcept{return{request_id.data(),request_id_size};}
};
struct CourtierControlsSource267V1{
 CourtierProduct267V1 product=CourtierProduct267V1::main;CourtierControl267V1 control=CourtierControl267V1::cancel;
 bool confirmation_layer_found=false,creator_window_found=false,modal_found=false,panel_found=false,window_visible=false,window_enabled=false,execute_admissible=false;
 std::optional<bool>native_definition_found,native_shown,native_valid;
 friend bool operator==(const CourtierControlsSource267V1&,const CourtierControlsSource267V1&)=default;
};
struct CourtierControlsResult267V1{
 CourtierControlsAction267V1 action=CourtierControlsAction267V1::query_control;CourtierControlsStatus267V1 status=CourtierControlsStatus267V1::unavailable;
 CourtierProduct267V1 product=CourtierProduct267V1::main;CourtierControl267V1 control=CourtierControl267V1::cancel;
 bool source_available=false,effect_attempted=false,native_returned=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;
 ck3_1210::CoreSnapshotPrefix facts{};std::optional<CourtierControlsSource267V1>source;std::string reason;
};
bool CourtierControlsRequestShape267V1(const CourtierControlsRequest267V1&)noexcept;
bool ParseCourtierControlsRequest267V1(std::string_view,CourtierControlsRequest267V1&)noexcept;
std::string SerializeCourtierControlsResult267V1(std::string_view,const CourtierControlsResult267V1&);
}
