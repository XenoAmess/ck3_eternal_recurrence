#pragma once
#include "xar_bridge/ck3_121003_courtier_configuration26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
inline constexpr char kCourtierChoicesRequestSchema267V1[]="ck3.courtier_creator_choices.current267_request.v1";
inline constexpr char kCourtierChoicesResultSchema267V1[]="ck3.courtier_creator_choices.current267_result.v1";
inline constexpr char kCourtierChoicesSourceSchema267V1[]="ck3.courtier_creator_choices.current267_source.v1";
inline constexpr char kCourtierChoicesBackend267V1[]="ck3-1.21.0.3-native-application-main-courtier-creator-choices";
inline constexpr std::array<std::string_view,2>kCourtierChoicesSteps267V1{"query-courtier-creator-choices-current-v1","select-courtier-creator-choice-current-v1"};
inline constexpr std::array<std::string_view,2>kCourtierChoicesCapabilities267V1{"game.query.current-courtier-creator-choices.v1","game.command.select-current-courtier-creator-choice.v1"};
enum class CourtierCatalog267V1{education,commander,physical,personality,other,culture,faith};
enum class CourtierChoicesAction267V1{query_choices,select_choice};
enum class CourtierChoicesStatus267V1{unavailable,expired,stale_source,claim_consumed,available,choice_dispatched,indeterminate};
struct CourtierChoicesRequest267V1{
 CourtierChoicesAction267V1 action=CourtierChoicesAction267V1::query_choices;CourtierProduct267V1 product=CourtierProduct267V1::main;CourtierCatalog267V1 catalog=CourtierCatalog267V1::education;
 std::array<char,97>choice_token{};std::uint8_t choice_token_size=0;std::string_view token()const noexcept{return{choice_token.data(),choice_token_size};}
 ck3_1210::CoreSnapshotPrefix expected{};std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;
 std::array<char,97>request_id{};std::uint8_t request_id_size=0;std::string_view id()const noexcept{return{request_id.data(),request_id_size};}
};
struct CourtierChoice267V1{
 std::string choice_token,key;bool native_shown=false,native_valid=false,selected=false,execute_admissible=false;
 friend bool operator==(const CourtierChoice267V1&,const CourtierChoice267V1&)=default;
};
struct CourtierChoicesSource267V1{
 CourtierProduct267V1 product=CourtierProduct267V1::main;CourtierCatalog267V1 catalog=CourtierCatalog267V1::education;
 bool confirmation_layer_found=false,creator_window_found=false,modal_found=false,panel_found=false,window_visible=false,window_enabled=false,model_available=false,complete_model=false;
 std::optional<std::int32_t>catalog_count;std::vector<CourtierChoice267V1>rows;std::optional<CourtierConfigurationValues267V1>configuration;
 friend bool operator==(const CourtierChoicesSource267V1&,const CourtierChoicesSource267V1&)=default;
};
struct CourtierChoicesResult267V1{
 CourtierChoicesAction267V1 action=CourtierChoicesAction267V1::query_choices;CourtierChoicesStatus267V1 status=CourtierChoicesStatus267V1::unavailable;
 CourtierProduct267V1 product=CourtierProduct267V1::main;CourtierCatalog267V1 catalog=CourtierCatalog267V1::education;std::string choice_token;
 bool source_available=false,effect_attempted=false,native_returned=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;
 ck3_1210::CoreSnapshotPrefix facts{};std::optional<CourtierChoicesSource267V1>source;std::string reason;
};
bool CourtierChoicesRequestShape267V1(const CourtierChoicesRequest267V1&)noexcept;
bool ParseCourtierChoicesRequest267V1(std::string_view,CourtierChoicesRequest267V1&)noexcept;
std::string SerializeCourtierChoicesResult267V1(std::string_view,const CourtierChoicesResult267V1&);
}
