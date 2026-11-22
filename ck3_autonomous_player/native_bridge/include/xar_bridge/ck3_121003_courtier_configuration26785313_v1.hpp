#pragma once
#include "xar_bridge/ck3_121003_courtier_controls26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
inline constexpr char kCourtierConfigurationRequestSchema267V1[]="ck3.courtier_creator_configuration.current267_request.v1";
inline constexpr char kCourtierConfigurationResultSchema267V1[]="ck3.courtier_creator_configuration.current267_result.v1";
inline constexpr char kCourtierConfigurationSourceSchema267V1[]="ck3.courtier_creator_configuration.current267_source.v1";
inline constexpr char kCourtierConfigurationBackend267V1[]="ck3-1.21.0.3-native-application-main-courtier-creator-configuration";
inline constexpr std::array<std::string_view,2>kCourtierConfigurationSteps267V1{"query-courtier-creator-configuration-current-v1","execute-courtier-creator-configuration-current-v1"};
inline constexpr std::array<std::string_view,2>kCourtierConfigurationCapabilities267V1{"game.query.current-courtier-creator-configuration.v1","game.command.execute-current-courtier-creator-configuration.v1"};

enum class CourtierSetting267V1{choose_female,diplomacy_plus_ten,prowess_plus_ten,choose_same_house};
enum class CourtierConfigurationAction267V1{query_configuration,execute_setting};
enum class CourtierConfigurationStatus267V1{unavailable,expired,stale_source,claim_consumed,available,setting_dispatched,indeterminate};
struct CourtierConfigurationRequest267V1{
 CourtierConfigurationAction267V1 action=CourtierConfigurationAction267V1::query_configuration;
 CourtierProduct267V1 product=CourtierProduct267V1::main;CourtierSetting267V1 setting=CourtierSetting267V1::choose_female;
 ck3_1210::CoreSnapshotPrefix expected{};std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;
 std::array<char,97>request_id{};std::uint8_t request_id_size=0;std::string_view id()const noexcept{return{request_id.data(),request_id_size};}
};
struct CourtierConfigurationValues267V1{
 std::array<std::optional<std::int64_t>,10>raw{};
 friend bool operator==(const CourtierConfigurationValues267V1&,const CourtierConfigurationValues267V1&)=default;
};
inline constexpr std::array<std::string_view,10>kCourtierConfigurationValueNames267V1{"age","female","diplomacy","martial","stewardship","intrigue","learning","prowess","same_house","cost"};
struct CourtierConfigurationSource267V1{
 CourtierProduct267V1 product=CourtierProduct267V1::main;CourtierSetting267V1 setting=CourtierSetting267V1::choose_female;
 bool confirmation_layer_found=false,creator_window_found=false,modal_found=false,panel_found=false,window_visible=false,window_enabled=false,execute_admissible=false;
 std::optional<bool>native_definition_found,native_shown,native_valid;
 std::optional<CourtierConfigurationValues267V1>configuration;bool numeric_complete=false;
 friend bool operator==(const CourtierConfigurationSource267V1&,const CourtierConfigurationSource267V1&)=default;
};
struct CourtierConfigurationResult267V1{
 CourtierConfigurationAction267V1 action=CourtierConfigurationAction267V1::query_configuration;CourtierConfigurationStatus267V1 status=CourtierConfigurationStatus267V1::unavailable;
 CourtierProduct267V1 product=CourtierProduct267V1::main;CourtierSetting267V1 setting=CourtierSetting267V1::choose_female;
 bool source_available=false,effect_attempted=false,native_returned=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;
 ck3_1210::CoreSnapshotPrefix facts{};std::optional<CourtierConfigurationSource267V1>source;std::string reason;
};
bool CourtierConfigurationRequestShape267V1(const CourtierConfigurationRequest267V1&)noexcept;
bool ParseCourtierConfigurationRequest267V1(std::string_view,CourtierConfigurationRequest267V1&)noexcept;
std::string SerializeCourtierConfigurationResult267V1(std::string_view,const CourtierConfigurationResult267V1&);
}
