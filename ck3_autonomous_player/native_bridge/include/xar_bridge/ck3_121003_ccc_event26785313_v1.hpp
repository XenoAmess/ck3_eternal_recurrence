#pragma once
#include "xar_bridge/ck3_121003_lyd26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kCccEventRequestSchema267V1[]="ck3.ccc_event.current267_request.v1";
inline constexpr char kCccEventSourceSchema267V1[]="ck3.ccc_event.current267_source.v1";
inline constexpr char kCccEventResultSchema267V1[]="ck3.ccc_event.current267_result.v1";
inline constexpr char kCccEventBackend267V1[]="ck3-1.21.0.3-native-application-main-ccc-event";
inline constexpr char kCccEventDefinition267V1[]="xccc.1001";
inline constexpr char kCccEventOption267V1[]="xccc.1001.d";
inline constexpr char kCccEventTemporaryCancelOption267V1[]="xccc.1001.f";
inline constexpr std::array<std::string_view,3> kCccEventSteps267V1{"query-ccc-event-current-v1","select-ccc-event-tier-four-current-v1","select-ccc-event-temporary-cancel-current-v1"};
inline constexpr std::array<std::string_view,3> kCccEventCaps267V1{"game.query.current-ccc-event.v1","game.command.select-current-ccc-event-tier-four.v1","game.command.select-current-ccc-event-temporary-cancel.v1"};
enum class CccEventAction267V1{query,select_tier_four,select_temporary_cancel};
enum class CccEventStatus267V1{unavailable,expired,stale_source,claim_consumed,available,selection_dispatched,indeterminate};
struct CccEventRequest267V1{
 CccEventAction267V1 action=CccEventAction267V1::query;ck3_1210::CoreSnapshotPrefix expected{};
 std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;std::optional<std::int32_t>instance_id;
 std::array<char,97>request_id{};std::uint8_t request_id_size=0;std::string_view id()const noexcept{return{request_id.data(),request_id_size};}
};
struct CccEventSource267V1{
 LydEventSource267V1 event_census{};std::optional<std::int32_t>fixed_instance_id;
 bool case_bound=false,select_d_admissible=false,select_f_admissible=false,sampled_twice=false;
 friend bool operator==(const CccEventSource267V1&,const CccEventSource267V1&)=default;
};
struct CccEventResult267V1{
 CccEventAction267V1 action=CccEventAction267V1::query;CccEventStatus267V1 status=CccEventStatus267V1::unavailable;
 bool source_available=false,effect_attempted=false,native_returned=false,native_handled=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix facts{};std::optional<std::int32_t>instance_id;
 std::optional<CccEventSource267V1>source;std::string reason;
};
bool CccEventRequestShape267V1(const CccEventRequest267V1&)noexcept;
bool CccEventSourceShape267V1(const CccEventSource267V1&)noexcept;
bool ParseCccEventRequest267V1(std::string_view,CccEventRequest267V1&)noexcept;
std::string SerializeCccEventResult267V1(std::string_view,const CccEventResult267V1&);
}
