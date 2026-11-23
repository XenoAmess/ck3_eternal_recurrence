#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
#include <vector>
namespace xar::ck3_121003::build26785313 {
inline constexpr std::array<std::string_view,1> kCccDecisionKeys267V1{"xccc_corruption_policy_decision"};
enum class CccDecision267V1:std::uint8_t{corruption_policy};
inline constexpr std::string_view CccDecisionKey267V1(CccDecision267V1 key)noexcept{const auto i=static_cast<std::size_t>(key);return i<kCccDecisionKeys267V1.size()?kCccDecisionKeys267V1[i]:std::string_view{};}
std::optional<CccDecision267V1> ParseCccDecisionKey267V1(std::string_view)noexcept;
inline constexpr char kCccDecisionRequestSchema267V1[]="ck3.ccc_decision.current267_request.v1";
inline constexpr char kCccDecisionResultSchema267V1[]="ck3.ccc_decision.current267_result.v1";
inline constexpr char kCccDecisionSourceSchema267V1[]="ck3.ccc_decision.current267_source.v1";
inline constexpr char kCccDecisionBackend267V1[]="ck3-1.21.0.3-native-application-main-ccc-decision";
inline constexpr std::array<std::string_view,4> kCccDecisionSteps267V1{"query-ccc-decision-current-v1","open-ccc-decisions-current-v1","open-ccc-decision-current-v1","confirm-ccc-decision-current-v1"};
inline constexpr std::array<std::string_view,4> kCccDecisionCapabilities267V1{"game.query.current-ccc-decision.v1","game.command.open-current-ccc-decisions.v1","game.command.open-current-ccc-decision.v1","game.command.confirm-current-ccc-decision.v1"};
enum class CccDecisionAction267V1{query,open_list,open_detail,confirm};
enum class CccDecisionStatus267V1{unavailable,expired,stale_source,claim_consumed,available,navigation_dispatched,selection_dispatched,confirmation_dispatched,indeterminate};
struct CccDecisionRequest267V1{CccDecisionAction267V1 action=CccDecisionAction267V1::query;ck3_1210::CoreSnapshotPrefix expected{};std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;std::optional<CccDecision267V1>decision;std::array<char,97>request_id{};std::uint8_t request_id_size=0;std::string_view id()const noexcept{return {request_id.data(),request_id_size};}};
struct CccDecisionRow267V1{CccDecision267V1 decision{};bool can_open_detail=false,is_selected=false;friend bool operator==(const CccDecisionRow267V1&,const CccDecisionRow267V1&)=default;};
struct CccDecisionSource267V1{
 bool list_found=false,list_visible=false,list_enabled=false,detail_found=false,detail_visible=false,detail_enabled=false,other_decision_selected=false,open_list_admissible=false,complete_model_census=false,blocked_by_visible_modal=false,confirm_admissible=false;
 std::optional<std::array<bool,4>>corruption_traits;std::optional<bool>fixture_tax_variable_present,fixture_tax_exact_half;
 bool case_bound=false;std::optional<std::string>confirm_tooltip;bool confirm_tooltip_observed=false;
 std::optional<std::int32_t>cooldown_expiry_date_raw;bool cooldown_readback_complete=false;
 std::optional<std::int32_t>groups_count,total_model_rows,widget_state;std::optional<CccDecision267V1>selected_decision;std::optional<bool>native_can_confirm;std::vector<CccDecisionRow267V1>rows;
 friend bool operator==(const CccDecisionSource267V1&,const CccDecisionSource267V1&)=default;
};
struct CccDecisionResult267V1{CccDecisionAction267V1 action=CccDecisionAction267V1::query;CccDecisionStatus267V1 status=CccDecisionStatus267V1::unavailable;bool source_available=false,effect_attempted=false,native_returned=false,native_handled=false,cleanup_known=true,facts_available=false;std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix facts{};std::optional<CccDecision267V1>decision;std::optional<CccDecisionSource267V1>source;std::string reason;};
bool CccDecisionRequestShape267V1(const CccDecisionRequest267V1&)noexcept;
bool ParseCccDecisionRequest267V1(std::string_view,CccDecisionRequest267V1&)noexcept;
std::string SerializeCccDecisionResult267V1(std::string_view,const CccDecisionResult267V1&);
}
