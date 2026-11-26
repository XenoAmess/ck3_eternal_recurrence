#pragma once
// Candidate only. Independent finite LYD namespace; old curated9/health35 do not gain permissions.
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
#include <vector>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kLydRequestSchema267V1[]="ck3.lyd.current267_request.v1";
inline constexpr char kLydResultSchema267V1[]="ck3.lyd.current267_result.v1";
inline constexpr char kLydSourceSchema267V1[]="ck3.lyd.current267_source.v1";
inline constexpr char kLydBackend267V1[]="ck3-1.21.0.3-native-application-main-lyd";
enum class LydAction267V1{query_decisions,open_list,open_detail,confirm_decision,query_events,
 choose_known_event_option,query_personal,open_personal,start_add_personal,select_personal_candidate,
 query_add_confirmation,confirm_personal_add,query_readback};
inline constexpr std::array<std::string_view,13>kLydActionNames267V1{"query_decisions","open_list","open_detail","confirm_decision","query_events","choose_known_event_option","query_personal","open_personal","start_add_personal","select_personal_candidate","query_add_confirmation","confirm_personal_add","query_readback"};
inline constexpr std::array<std::string_view,13>kLydSteps267V1{"query-lyd-decisions-current-v1","open-lyd-decisions-current-v1","open-lyd-decision-current-v1","confirm-lyd-decision-current-v1","query-lyd-events-current-v1","select-lyd-known-event-option-current-v1","query-lyd-personal-current-v1","open-lyd-personal-current-v1","start-add-lyd-personal-current-v1","select-lyd-personal-candidate-current-v1","query-lyd-add-confirmation-current-v1","confirm-lyd-personal-add-current-v1","query-lyd-readback-current-v1"};
inline constexpr std::array<std::string_view,13>kLydCapabilities267V1{"game.query.current-lyd-decisions.v1","game.command.open-current-lyd-decisions.v1","game.command.open-current-lyd-decision.v1","game.command.confirm-current-lyd-decision.v1","game.query.current-lyd-events.v1","game.command.select-current-lyd-event-option.v1","game.query.current-lyd-personal.v1","game.command.open-current-lyd-personal.v1","game.command.start-add-current-lyd-personal.v1","game.command.select-current-lyd-personal-candidate.v1","game.query.current-lyd-add-confirmation.v1","game.command.confirm-current-lyd-personal-add.v1","game.query.current-lyd-readback.v1"};
enum class LydDecision267V1:std::uint8_t{entry,ritual_music,reverent_heaven,knowing_acting_support,begin_readonly};
inline constexpr std::array<std::string_view,5>kLydDecisionKeys267V1{
 "lyd_enter_decision","lyd_play_ritual_music_decision","lyd_play_reverent_heaven_decision",
 "lyd_play_knowing_acting_support_decision","lyd_i3b_begin_decision"};
inline constexpr std::string_view LydDecisionKey267V1(LydDecision267V1 key)noexcept{const auto n=static_cast<std::size_t>(key);return n<kLydDecisionKeys267V1.size()?kLydDecisionKeys267V1[n]:std::string_view{};}
std::optional<LydDecision267V1>ParseLydDecisionKey267V1(std::string_view)noexcept;
enum class LydPersonal267V1:std::uint8_t{reverent_heaven,knowing_acting_support};
inline constexpr std::array<std::string_view,2>kLydPersonalKeys267V1{"lyd_tenet_reverent_heaven","lyd_tenet_knowing_acting_support"};
enum class LydEventRole267V1:std::uint8_t{welcome_continue,ritual_music_pay,ritual_music_cancel,reverent_heaven_pay,reverent_heaven_cancel,knowing_acting_inquiry,knowing_acting_cancel};
inline constexpr std::array<std::string_view,7>kLydEventRoleNames267V1{"welcome_continue","ritual_music_pay","ritual_music_cancel","reverent_heaven_pay","reverent_heaven_cancel","knowing_acting_inquiry","knowing_acting_cancel"};
enum class LydKind267V1{decisions,events,personal,readback};
LydKind267V1 LydKindForAction267V1(LydAction267V1)noexcept;
bool LydQueryAction267V1(LydAction267V1)noexcept;
enum class LydStatus267V1{unavailable,expired,stale_source,claim_consumed,available,navigation_dispatched,
 selection_dispatched,confirmation_dispatched,indeterminate};
struct LydRequest267V1{
 LydAction267V1 action=LydAction267V1::query_decisions;ck3_1210::CoreSnapshotPrefix expected{};
 std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;
 std::optional<LydDecision267V1>decision;std::optional<LydPersonal267V1>personal;
 std::optional<LydEventRole267V1>event_role;std::optional<std::int32_t>instance_id;
 std::string choice_token;std::array<char,97>request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return{request_id.data(),request_id_size};}
};
struct LydDecisionRow267V1{LydDecision267V1 decision{};bool can_open_detail=false,is_selected=false;friend bool operator==(const LydDecisionRow267V1&,const LydDecisionRow267V1&)=default;};
struct LydDecisionSource267V1{
 bool list_found=false,list_visible=false,list_enabled=false,detail_found=false,detail_visible=false,detail_enabled=false,
  other_decision_selected=false,open_list_admissible=false,complete_model_census=false,blocked_by_visible_modal=false,confirm_admissible=false;
 std::optional<std::int32_t>groups_count,total_model_rows,widget_state;std::optional<LydDecision267V1>selected_decision;
 std::optional<bool>native_can_confirm;std::vector<LydDecisionRow267V1>rows;
 // Actual text only when its own current typed getter is qualified; never static explanation as observed text.
 std::optional<std::string>conditions_text;
 friend bool operator==(const LydDecisionSource267V1&,const LydDecisionSource267V1&)=default;
};
struct LydEventOption267V1{
 std::int32_t authored_option_index=-1;bool native_can_select=false;std::string text,disabled_reason;
 std::optional<std::string>source_bound_option_key;std::optional<LydEventRole267V1>permitted_role;
 friend bool operator==(const LydEventOption267V1&,const LydEventOption267V1&)=default;
};
struct LydEventRow267V1{
 std::int32_t instance_id=0,recipient_character_id=-1,authored_option_count=0;
 std::string definition_key,opening,description;bool named_root_bound=false,window_visible=false,window_enabled=false;
 std::vector<LydEventOption267V1>options;
 friend bool operator==(const LydEventRow267V1&,const LydEventRow267V1&)=default;
};
struct LydEventSource267V1{
 bool census_complete=false;std::int32_t named_root_count=0;std::vector<LydEventRow267V1>events;
 friend bool operator==(const LydEventSource267V1&,const LydEventSource267V1&)=default;
};
struct LydPersonalRow267V1{
 std::uint8_t group_category=0;std::string definition_key,choice_token;
 bool group_can_pick=false,is_personal=false,select_admissible=false;std::optional<bool>native_can_pick;
 friend bool operator==(const LydPersonalRow267V1&,const LydPersonalRow267V1&)=default;
};
struct LydPersonalSlot267V1{
 bool is_empty=false,is_personal=false;std::optional<std::string>definition_key;
 friend bool operator==(const LydPersonalSlot267V1&,const LydPersonalSlot267V1&)=default;
};
struct LydAddModalSource267V1{
 bool found=false,named_root_bound=false,visible=false,closed=false;std::optional<LydPersonal267V1>personal;
 std::optional<bool>native_can_accept;bool accept_admissible=false;
 friend bool operator==(const LydAddModalSource267V1&,const LydAddModalSource267V1&)=default;
};
struct LydPersonalSource267V1{
 bool resident_available=false,named_root_bound=false,window_visible=false,window_enabled=false,actor_bound=false,is_adding=false,
  model_materialized=false,slots_complete=false,groups_complete=false,empty_slot_found=false,
  actual_personal_complete=false,blocked_by_visible_modal=false,open_admissible=false,start_add_admissible=false;
 std::optional<std::int32_t>slot_count,group_count;std::vector<LydPersonalSlot267V1>slots;std::vector<LydPersonalRow267V1>rows;
 std::optional<bool>native_window_visible;
 std::vector<std::string>actual_personal_keys;LydAddModalSource267V1 add_modal{};
 std::optional<std::int64_t>spiritual_fulfillment_raw;
 // ADD currency quote is not proven by the static fulfillment contribution; these remain null until an authoritative getter exists.
 std::optional<RawResources>quoted_currency_costs;
 friend bool operator==(const LydPersonalSource267V1&,const LydPersonalSource267V1&)=default;
};
struct LydReadbackSource267V1{
 std::optional<RawResources>resources;
 // Unqualified fields remain null. They do not become0 or gate an unrelated complete decision/event/personal source.
 std::optional<std::int64_t>legitimacy_raw,diplomacy_xp_raw,learning_xp_raw,capital_control_raw;
 bool original_case_readback_complete=false;
 friend bool operator==(const LydReadbackSource267V1&,const LydReadbackSource267V1&)=default;
};
struct LydSource267V1{
 LydKind267V1 kind=LydKind267V1::decisions;
 std::optional<LydDecisionSource267V1>decisions;std::optional<LydEventSource267V1>events;
 std::optional<LydPersonalSource267V1>personal;std::optional<LydReadbackSource267V1>readback;
 friend bool operator==(const LydSource267V1&,const LydSource267V1&)=default;
};
bool LydPublicSourceShape267V1(const LydSource267V1&)noexcept;
bool LydPublicAdmissible267V1(const LydSource267V1&,const LydRequest267V1&)noexcept;
inline constexpr std::string_view kFull111EventRendererStep267V1 = "query-current-ordinary-event-renderer-26785313-v1";
inline constexpr std::string_view kFull111EventRendererCapability267V1 = "game.query.current-ordinary-event-renderer.26785313.v1";
inline constexpr std::string_view kFull111EventRendererResultSchema267V1 = "ck3.full111.ordinary_event_renderer_result.v1";
struct Full111RenderedOption267V1 {
 std::int32_t authored_option_index = -1;
 bool native_can_select = false, widget_visible = false, widget_enabled = false;
 std::string text, disabled_reason;
};
struct Full111EventRendererSource267V1 {
 std::int32_t instance_id = 0, recipient_character_id = -1, authored_option_count = 0;
 std::string definition_key;
 std::vector<Full111RenderedOption267V1> options;
};
struct LydResult267V1{
 LydAction267V1 action=LydAction267V1::query_decisions;LydStatus267V1 status=LydStatus267V1::unavailable;
 bool source_available=false,effect_attempted=false,native_returned=false,native_handled=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix facts{};std::optional<LydDecision267V1>decision;
 std::optional<LydPersonal267V1>personal;std::optional<LydEventRole267V1>event_role;std::optional<std::int32_t>instance_id;
 std::optional<LydSource267V1>source;std::string reason;
 std::optional<Full111EventRendererSource267V1>renderer;
};
bool LydRequestShape267V1(const LydRequest267V1&)noexcept;
inline constexpr auto kLydEventQueryIndex267V1=static_cast<std::size_t>(LydAction267V1::query_events);
bool ParseLydRequest267V1(std::string_view,LydRequest267V1&)noexcept;
bool ParseFull111LydEventRequest267V1(std::string_view,LydRequest267V1&)noexcept;
bool ParseFull111EventRendererRequest267V1(std::string_view,LydRequest267V1&)noexcept;
bool Full111EventRendererRequestShape267V1(const LydRequest267V1&)noexcept;
std::string SerializeFull111EventRendererResult267V1(std::string_view,const LydResult267V1&);
std::string SerializeLydResult267V1(std::string_view,const LydResult267V1&);
std::string SerializeFull111LydEventResult267V1(std::string_view,const LydResult267V1&);
}
