#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
#include <vector>
namespace xar::ck3_121003::build26785313 {
inline constexpr std::array<std::string_view,9> kCuratedDecisionKeys267V1{
 "xqol_enable_auto_appointment_decision","xqol_disable_auto_appointment_decision",
 "xqol_enable_no_vassal_transfers_decision","xqol_disable_no_vassal_transfers_decision",
 "xqol_enable_auto_call_defenders_decision","xqol_disable_auto_call_defenders_decision",
 "xqol_mass_conversion_decision","xar_courtier_creator_decision","ervc_courtier_creator_decision"};
enum class CuratedDecision267V1:std::uint8_t{enable_auto_appointment,disable_auto_appointment,enable_no_vassal_transfers,disable_no_vassal_transfers,enable_auto_call_defenders,disable_auto_call_defenders,mass_conversion,main_creator,vivhite_creator};
inline constexpr std::string_view CuratedDecisionKey267V1(CuratedDecision267V1 key)noexcept{const auto i=static_cast<std::size_t>(key);return i<kCuratedDecisionKeys267V1.size()?kCuratedDecisionKeys267V1[i]:std::string_view{};}
std::optional<CuratedDecision267V1> ParseCuratedDecisionKey267V1(std::string_view)noexcept;
inline constexpr char kCuratedDecisionRequestSchema267V1[]="ck3.curated_decisions.current267_request.v1";
inline constexpr char kCuratedDecisionResultSchema267V1[]="ck3.curated_decisions.current267_result.v1";
inline constexpr char kCuratedDecisionSourceSchema267V1[]="ck3.curated_decisions.current267_source.v1";
inline constexpr char kCuratedDecisionBackend267V1[]="ck3-1.21.0.3-native-application-main-curated-decisions";
inline constexpr std::array<std::string_view,4> kCuratedDecisionSteps267V1{"query-curated-decisions-current-v1","open-curated-decisions-current-v1","open-curated-decision-current-v1","confirm-curated-decision-current-v1"};
inline constexpr std::array<std::string_view,4> kCuratedDecisionCapabilities267V1{"game.query.current-curated-decisions.v1","game.command.open-current-curated-decisions.v1","game.command.open-current-curated-decision.v1","game.command.confirm-current-curated-decision.v1"};
enum class CuratedDecisionAction267V1{query,open_list,open_detail,confirm};
enum class CuratedDecisionStatus267V1{unavailable,expired,stale_source,claim_consumed,available,navigation_dispatched,selection_dispatched,confirmation_dispatched,indeterminate};
struct CuratedDecisionRequest267V1{CuratedDecisionAction267V1 action=CuratedDecisionAction267V1::query;ck3_1210::CoreSnapshotPrefix expected{};std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;std::optional<CuratedDecision267V1>decision;std::array<char,97>request_id{};std::uint8_t request_id_size=0;std::string_view id()const noexcept{return {request_id.data(),request_id_size};}};
struct CuratedDecisionRow267V1{CuratedDecision267V1 decision{};bool can_open_detail=false,is_selected=false;friend bool operator==(const CuratedDecisionRow267V1&,const CuratedDecisionRow267V1&)=default;};
struct CuratedDecisionSource267V1{
 bool list_found=false,list_visible=false,list_enabled=false,detail_found=false,detail_visible=false,detail_enabled=false,other_decision_selected=false,open_list_admissible=false,complete_model_census=false,blocked_by_visible_modal=false,confirm_admissible=false;
 std::optional<std::int32_t>groups_count,total_model_rows,widget_state;std::optional<CuratedDecision267V1>selected_decision;std::optional<bool>native_can_confirm;std::vector<CuratedDecisionRow267V1>rows;
 friend bool operator==(const CuratedDecisionSource267V1&,const CuratedDecisionSource267V1&)=default;
};
struct CuratedDecisionResult267V1{CuratedDecisionAction267V1 action=CuratedDecisionAction267V1::query;CuratedDecisionStatus267V1 status=CuratedDecisionStatus267V1::unavailable;bool source_available=false,effect_attempted=false,native_returned=false,native_handled=false,cleanup_known=true,facts_available=false;std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix facts{};std::optional<CuratedDecision267V1>decision;std::optional<CuratedDecisionSource267V1>source;std::string reason;};
bool CuratedDecisionRequestShape267V1(const CuratedDecisionRequest267V1&)noexcept;
bool ParseCuratedDecisionRequest267V1(std::string_view,CuratedDecisionRequest267V1&)noexcept;
std::string SerializeCuratedDecisionResult267V1(std::string_view,const CuratedDecisionResult267V1&);
}
