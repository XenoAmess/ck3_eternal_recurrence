#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kZg361Ae2RequestSchema267V1[]="ck3.zg361_ae2.current267_request.v1";
inline constexpr char kZg361Ae2ResultSchema267V1[]="ck3.zg361_ae2.current267_result.v1";
inline constexpr char kZg361Ae2SourceSchema267V1[]="ck3.zg361_ae2.current267_source.v1";
inline constexpr char kZg361Ae2Backend267V1[]="ck3-1.21.0.3-native-application-main-zg361-ae2";
inline constexpr char kZg361Ae2Step267V1[]="ck3_121003_zg361_ae2.execute";
inline constexpr std::array<std::string_view,3>kZg361Ae2Capabilities267V1{
 "game.query.current-zg361-ae2.v1","game.command.current-zg361-ae2-fixed-controls.v1","game.command.current-zg361-ae2-pay-now.v1"};
enum class Zg361Ae2Action267V1:std::uint8_t{
 query_controls,open_controls_list,open_present_detail,confirm_present,
 query_ae2,choose_pay_now,open_verify_detail,confirm_verify,query_review_requirements,open_review_detail,query_scoreboard,open_scoreboard,close_scoreboard};
inline constexpr std::array<std::string_view,13>kZg361Ae2Actions267V1{
 "query_controls","open_controls_list","open_present_detail","confirm_present",
 "query_ae2","choose_pay_now","open_verify_detail","confirm_verify","query_review_requirements","open_review_detail","query_scoreboard","open_scoreboard","close_scoreboard"};
// review is private census/dispatch identity; old public controls remain exactly present/verify.
enum class Zg361Ae2Control267V1:std::uint8_t{present,verify,review};
inline constexpr std::string_view kZg361ReviewKey267V1="zg361_review_now_decision";
inline constexpr std::array<std::string_view,2>kZg361ReviewCapabilities267V1{
 "game.query.current-zg361-review-requirements.v1","game.command.current-zg361-review-detail.v1"};
inline constexpr std::array<std::string_view,2>kZg361Ae2ControlKeys267V1{
 "zga_ae2_present_decision","zga_ae2_verify_decision"};
inline constexpr std::string_view kZg361Ae2Definition267V1="zg361comp.1";
inline constexpr std::int32_t kZg361Ae2AuthoredCount267V1=42;
inline constexpr std::array<std::int32_t,3>kZg361Ae2AuthoredIndices267V1{15,16,17};
inline constexpr std::array<std::string_view,3>kZg361Ae2OptionKeys267V1{
 "zg361comp.1.ae2.r1","zg361comp.1.ae2.r2","zg361comp.1.ae2.r3"};
inline constexpr std::array<std::string_view,2>kZg361ScoreboardCapabilities267V1{
 "game.query.current-zg361-scoreboard.v1","game.command.current-zg361-scoreboard-open-close.v1"};
inline constexpr std::string_view kZg361ScoreboardWindow267V1="zg361_scoreboard_window";
inline constexpr std::string_view kZg361ScoreboardModal267V1="zg361_scoreboard_modal";
inline constexpr std::string_view kZg361ScoreboardClose267V1="zg361_scoreboard_header_close";
inline constexpr std::array<std::string_view,3>kZg361ScoreboardEntries267V1{
 "zg361_scoreboard_entry_managed","zg361_scoreboard_entry_received","zg361_scoreboard_entry_system"};
enum class Zg361Ae2Kind267V1:std::uint8_t{controls,events,review,scoreboard};
enum class Zg361Ae2Status267V1:std::uint8_t{
 unavailable,expired,stale_source,claim_consumed,available,navigation_dispatched,
 selection_dispatched,confirmation_dispatched,indeterminate};
struct Zg361Ae2Request267V1{
 Zg361Ae2Action267V1 action=Zg361Ae2Action267V1::query_controls;
 ck3_1210::CoreSnapshotPrefix expected{};
 std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;
 std::array<char,97>request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return {request_id.data(),request_id_size};}
};
struct Zg361Ae2ControlRow267V1{
 Zg361Ae2Control267V1 control=Zg361Ae2Control267V1::present;
 std::string definition_key;bool native_can_open_detail=false,open_detail_admissible=false;
 std::optional<bool>native_can_confirm;bool confirm_admissible=false;
 friend bool operator==(const Zg361Ae2ControlRow267V1&,const Zg361Ae2ControlRow267V1&)=default;
};
struct Zg361Ae2Controls267V1{
 bool resident_available=false,list_visible=false,detail_visible=false,actor_bound=false;
 bool model_complete=false,blocked_by_visible_modal=false,open_list_admissible=false;
 std::optional<Zg361Ae2Control267V1>selected_control;
 std::vector<Zg361Ae2ControlRow267V1>rows;
 friend bool operator==(const Zg361Ae2Controls267V1&,const Zg361Ae2Controls267V1&)=default;
};
struct Zg361Ae2EventIdentity267V1{
 std::int32_t instance_id=0;std::uint32_t recipient_character_id=0;
 std::string definition_key;
 friend bool operator==(const Zg361Ae2EventIdentity267V1&,const Zg361Ae2EventIdentity267V1&)=default;
};
struct Zg361Ae2Option267V1{
 std::int32_t authored_option_index=-1;std::string option_key;
 bool native_can_select=false;
 std::string text,disabled_reason,tooltip;
 friend bool operator==(const Zg361Ae2Option267V1&,const Zg361Ae2Option267V1&)=default;
};
struct Zg361Ae2Snapshot267V1{
 std::int32_t instance_id=0;std::uint32_t recipient_character_id=0;
 std::string definition_key;std::int32_t authored_option_count=0;
 // This phase is derived from the exact42-authored/current displayed15/16/17
 // material and the sealed production script. Owner/subject/cycle/case guard
 // values are not exported or guessed; choice additionally requires the real
 // current r1 NativeCan and the private present-to-event custody chain.
 bool phase_bound=false;
 bool named_root_bound=false,window_visible=false,window_enabled=false,tooltips_complete=false;
 // Actual displayed order is retained. Every option carries its original
 // authored index; choosing pay_now always joins15, never displayed ordinal.
 std::array<Zg361Ae2Option267V1,3>options;
 bool pay_now_admissible=false;
 friend bool operator==(const Zg361Ae2Snapshot267V1&,const Zg361Ae2Snapshot267V1&)=default;
};
struct Zg361Ae2Events267V1{
 bool census_complete=false;std::vector<Zg361Ae2EventIdentity267V1>census;
 std::optional<Zg361Ae2Snapshot267V1>ae2;
 friend bool operator==(const Zg361Ae2Events267V1&,const Zg361Ae2Events267V1&)=default;
};
struct Zg361Review267V1{
 bool resident_available=false,list_visible=false,detail_visible=false,detail_enabled=false;
 bool actor_bound=false,model_complete=false,blocked_by_visible_modal=false,row_present=false;
 bool selected_review=false,open_detail_admissible=false,requirements_complete=false;
 std::optional<std::string>selected_definition_key;
 std::optional<bool>has_requirements;
 std::optional<std::string>requirements_description;
 friend bool operator==(const Zg361Review267V1&,const Zg361Review267V1&)=default;
};
// Read-only physical GUI DATA. No pointers, arbitrary selectors or action tokens.
struct Zg361Scoreboard267V1{
 bool complete=false,window_found=false,window_visible=false,window_enabled=false;
 bool modal_found=false,modal_visible=false,modal_enabled=false;
 std::uint32_t window_nodes=0,modal_children=0;
 std::optional<std::string>open_entry;
 bool open_admissible=false,close_admissible=false;
 friend bool operator==(const Zg361Scoreboard267V1&,const Zg361Scoreboard267V1&)=default;
};
struct Zg361Ae2Source267V1{
 Zg361Ae2Kind267V1 kind=Zg361Ae2Kind267V1::controls;
 std::optional<Zg361Ae2Controls267V1>controls;
 std::optional<Zg361Ae2Events267V1>events;
 std::optional<Zg361Review267V1>review;
 std::optional<Zg361Scoreboard267V1>scoreboard;
 friend bool operator==(const Zg361Ae2Source267V1&,const Zg361Ae2Source267V1&)=default;
};
struct Zg361Ae2Result267V1{
 Zg361Ae2Action267V1 action=Zg361Ae2Action267V1::query_controls;
 Zg361Ae2Status267V1 status=Zg361Ae2Status267V1::unavailable;
 bool source_available=false,effect_attempted=false,native_returned=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix facts{};
 std::optional<Zg361Ae2Source267V1>source;std::string reason;
};
bool Zg361Ae2Query267V1(Zg361Ae2Action267V1)noexcept;
Zg361Ae2Kind267V1 Zg361Ae2KindFor267V1(Zg361Ae2Action267V1)noexcept;
const char*Zg361Ae2ActionName267V1(Zg361Ae2Action267V1)noexcept;
bool Zg361Ae2RequestShape267V1(const Zg361Ae2Request267V1&)noexcept;
bool ParseZg361Ae2Request267V1(std::string_view,Zg361Ae2Request267V1&)noexcept;
bool Zg361Ae2SourceShape267V1(const Zg361Ae2Source267V1&)noexcept;
bool Zg361Ae2PublicAdmissible267V1(const Zg361Ae2Source267V1&,Zg361Ae2Action267V1)noexcept;
std::string SerializeZg361Ae2Result267V1(std::string_view,const Zg361Ae2Result267V1&);
}
