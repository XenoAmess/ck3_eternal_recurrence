#pragma once
#include "xar_bridge/ck3_121003_lyd26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kRmtmEventRequestSchema267V1[]="ck3.rmtm_event.current267_request.v1";
inline constexpr char kRmtmEventSourceSchema267V1[]="ck3.rmtm_event.current267_source.v1";
inline constexpr char kRmtmEventResultSchema267V1[]="ck3.rmtm_event.current267_result.v1";
inline constexpr char kRmtmEventBackend267V1[]="ck3-1.21.0.3-native-application-main-rmtm-event";
inline constexpr char kRmtmSummaryDefinition267V1[]="rmtm.1001";
inline constexpr char kRmtmChaosDefinition267V1[]="tgp_dynastic_cycle.0081";
inline constexpr char kRmtmSummaryOption267V1[]="rmtm_loyalty_summary_acknowledge";
inline constexpr char kRmtmChaosOption267V1[]="tgp_dynastic_cycle.0081.a";
inline constexpr std::array<std::string_view,5>kRmtmEventSteps267V1{"query-rmtm-summary-current-v1","ack-rmtm-summary-current-v1","query-rmtm-chaos-current-v1","ack-rmtm-chaos-current-v1","choose-rmtm-post-succession-first-available-current-v1"};
inline constexpr std::array<std::string_view,5>kRmtmEventCaps267V1{"game.query.current-rmtm-summary.v1","game.command.ack-current-rmtm-summary.v1","game.query.current-rmtm-chaos.v1","game.command.ack-current-rmtm-chaos.v1","game.command.choose-current-rmtm-post-succession-first-available.v1"};
enum class RmtmEventAction267V1{query_summary,ack_summary,query_chaos,ack_chaos,choose_post_succession_first_available};
enum class RmtmEventStatus267V1{unavailable,expired,stale_source,claim_consumed,available,selection_dispatched,indeterminate};
struct RmtmEventRequest267V1{
 RmtmEventAction267V1 action=RmtmEventAction267V1::query_summary;ck3_1210::CoreSnapshotPrefix expected{};
 std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;std::optional<std::int32_t>instance_id;
 std::array<char,97>request_id{};std::uint8_t request_id_size=0;std::string_view id()const noexcept{return{request_id.data(),request_id_size};}
};
struct RmtmEventSource267V1{
 LydEventSource267V1 event_census{};std::optional<std::int32_t>fixed_instance_id;
 bool case_bound=false,ack_admissible=false,sampled_twice=false;
 friend bool operator==(const RmtmEventSource267V1&,const RmtmEventSource267V1&)=default;
};
struct RmtmEventResult267V1{
 RmtmEventAction267V1 action=RmtmEventAction267V1::query_summary;RmtmEventStatus267V1 status=RmtmEventStatus267V1::unavailable;
 bool source_available=false,effect_attempted=false,native_returned=false,native_handled=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix facts{};std::optional<std::int32_t>instance_id;
 std::optional<RmtmEventSource267V1>source;std::string reason;
};
// DATA derivation only; this grants no action lease, actor epoch or case custody.
// Existing specialized strategies take priority. The caller never chooses an index.
struct RmtmPostSuccessionChoice267V1 {
 std::int32_t instance_id=0,authored_option_index=-1;
 friend bool operator==(const RmtmPostSuccessionChoice267V1&,const RmtmPostSuccessionChoice267V1&)=default;
};
std::optional<RmtmPostSuccessionChoice267V1> FindRmtmPostSuccessionChoice267V1(
 const RmtmEventSource267V1&,std::int32_t actor,std::int32_t actual_instance)noexcept;
bool RmtmEventRequestShape267V1(const RmtmEventRequest267V1&)noexcept;
bool RmtmEventSourceShape267V1(const RmtmEventSource267V1&)noexcept;
bool ParseRmtmEventRequest267V1(std::string_view,RmtmEventRequest267V1&)noexcept;
std::string SerializeRmtmEventResult267V1(std::string_view,const RmtmEventResult267V1&);
}

namespace xar::ck3_121003::build26785313 { inline bool RmtmEventQuery267V1(RmtmEventAction267V1 a)noexcept{return a==RmtmEventAction267V1::query_summary||a==RmtmEventAction267V1::query_chaos;} }
