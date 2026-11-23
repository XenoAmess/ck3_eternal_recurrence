#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
#include <vector>
namespace xar::ck3_121003::build26785313 {
inline constexpr std::array<std::string_view,5> kRmtmDecisionKeys267V1{"rqa120_continue_decision","rqaui_prepare_fifty_decision","rqaui_prepare_fiftyone_decision","rmtm_claim_restoration_decision","rqaui_verify_actual_restoration_decision"};
enum class RmtmDecision267V1:std::uint8_t{continue_core,prepare_fifty,prepare_fiftyone,restore,verify_restore};
inline constexpr std::string_view RmtmDecisionKey267V1(RmtmDecision267V1 key)noexcept{const auto i=static_cast<std::size_t>(key);return i<kRmtmDecisionKeys267V1.size()?kRmtmDecisionKeys267V1[i]:std::string_view{};}
std::optional<RmtmDecision267V1> ParseRmtmDecisionKey267V1(std::string_view)noexcept;
inline constexpr char kRmtmDecisionRequestSchema267V1[]="ck3.rmtm_decision.current267_request.v1";
inline constexpr char kRmtmDecisionResultSchema267V1[]="ck3.rmtm_decision.current267_result.v1";
inline constexpr char kRmtmDecisionSourceSchema267V1[]="ck3.rmtm_decision.current267_source.v1";
inline constexpr char kRmtmDecisionBackend267V1[]="ck3-1.21.0.3-native-application-main-rmtm-decision";
inline constexpr std::array<std::string_view,4> kRmtmDecisionSteps267V1{"query-rmtm-decision-current-v1","open-rmtm-decisions-current-v1","open-rmtm-decision-current-v1","confirm-rmtm-decision-current-v1"};
inline constexpr std::array<std::string_view,4> kRmtmDecisionCapabilities267V1{"game.query.current-rmtm-decision.v1","game.command.open-current-rmtm-decisions.v1","game.command.open-current-rmtm-decision.v1","game.command.confirm-current-rmtm-decision.v1"};
enum class RmtmDecisionAction267V1{query,open_list,open_detail,confirm};
enum class RmtmDecisionStatus267V1{unavailable,expired,stale_source,claim_consumed,available,navigation_dispatched,selection_dispatched,confirmation_dispatched,indeterminate};
struct RmtmDecisionRequest267V1{RmtmDecisionAction267V1 action=RmtmDecisionAction267V1::query;ck3_1210::CoreSnapshotPrefix expected{};std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;std::optional<RmtmDecision267V1>decision;std::array<char,97>request_id{};std::uint8_t request_id_size=0;std::string_view id()const noexcept{return {request_id.data(),request_id_size};}};
struct RmtmDecisionRow267V1{RmtmDecision267V1 decision{};bool can_open_detail=false,is_selected=false;friend bool operator==(const RmtmDecisionRow267V1&,const RmtmDecisionRow267V1&)=default;};
struct RmtmDecisionSource267V1{
 bool list_found=false,list_visible=false,list_enabled=false,detail_found=false,detail_visible=false,detail_enabled=false,other_decision_selected=false,open_list_admissible=false,complete_model_census=false,blocked_by_visible_modal=false,confirm_admissible=false;
 bool case_bound=false;std::optional<std::string>confirm_tooltip;bool confirm_tooltip_observed=false;
 std::optional<std::int32_t>groups_count,total_model_rows,widget_state;std::optional<RmtmDecision267V1>selected_decision;std::optional<bool>native_can_confirm;std::vector<RmtmDecisionRow267V1>rows;
 friend bool operator==(const RmtmDecisionSource267V1&,const RmtmDecisionSource267V1&)=default;
};
struct RmtmDecisionResult267V1{RmtmDecisionAction267V1 action=RmtmDecisionAction267V1::query;RmtmDecisionStatus267V1 status=RmtmDecisionStatus267V1::unavailable;bool source_available=false,effect_attempted=false,native_returned=false,native_handled=false,cleanup_known=true,facts_available=false;std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix facts{};std::optional<RmtmDecision267V1>decision;std::optional<RmtmDecisionSource267V1>source;std::string reason;};
bool RmtmDecisionRequestShape267V1(const RmtmDecisionRequest267V1&)noexcept;
bool ParseRmtmDecisionRequest267V1(std::string_view,RmtmDecisionRequest267V1&)noexcept;
std::string SerializeRmtmDecisionResult267V1(std::string_view,const RmtmDecisionResult267V1&);
}
