#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
#include <vector>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kFullscreenEventRequestSchema267V1[]="ck3.fullscreen_event.current267_request.v1";
inline constexpr char kFullscreenEventResultSchema267V1[]="ck3.fullscreen_event.current267_result.v1";
inline constexpr char kFullscreenEventSourceSchema267V1[]="ck3.fullscreen_event.current267_source.v1";
inline constexpr char kFullscreenEventBackend267V1[]="ck3-1.21.0.3-native-application-main-fullscreen-event";
inline constexpr std::array<std::string_view,2> kFullscreenEventSteps267V1{
 "query-current-fullscreen-event-v1","acknowledge-known-current-fullscreen-event-v1"};
inline constexpr std::array<std::string_view,2> kFullscreenEventCapabilities267V1{
 "game.query.current-fullscreen-event.v1","game.command.acknowledge-known-current-fullscreen-event.v1"};
inline constexpr char kKnownFullscreenEventDefinition267V1[]="gdp_guelph_ghibelline.0500";
inline constexpr char kKnownFullscreenEventOption267V1[]="gdp_guelph_ghibelline.0500.a";
enum class FullscreenEventAction267V1 {query_fullscreen,acknowledge_known};
enum class FullscreenEventStatus267V1 {unavailable,expired,stale_source,claim_consumed,available,ack_dispatched,indeterminate};
struct FullscreenEventRequest267V1 {
 FullscreenEventAction267V1 action=FullscreenEventAction267V1::query_fullscreen;
 ck3_1210::CoreSnapshotPrefix expected{};
 std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;
 std::optional<std::int32_t> instance_id;
 std::array<char,97> request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return {request_id.data(),request_id_size};}
};
struct FullscreenEventOption267V1 {
 std::int32_t authored_option_index=-1;bool native_can_select=false;
 std::string text,disabled_reason;std::optional<std::string> source_bound_option_key;
 friend bool operator==(const FullscreenEventOption267V1&,const FullscreenEventOption267V1&)=default;
};
struct FullscreenEventSource267V1 {
 std::int32_t splash_item_count=0;
 bool fullscreen_found=false,named_root_bound=false,window_visible=false,window_enabled=false;
 std::optional<std::int32_t> instance_id,recipient_character_id;
 std::optional<std::string> definition_key,opening,description;
 std::vector<FullscreenEventOption267V1> options;bool known_ack_admissible=false;
 friend bool operator==(const FullscreenEventSource267V1&,const FullscreenEventSource267V1&)=default;
};
struct FullscreenEventResult267V1 {
 FullscreenEventAction267V1 action=FullscreenEventAction267V1::query_fullscreen;
 FullscreenEventStatus267V1 status=FullscreenEventStatus267V1::unavailable;
 bool source_available=false,effect_attempted=false,native_returned=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix facts{};
 std::optional<std::int32_t> instance_id;std::optional<FullscreenEventSource267V1> source;std::string reason;
};
bool FullscreenEventRequestShape267V1(const FullscreenEventRequest267V1&)noexcept;
bool ParseFullscreenEventRequest267V1(std::string_view,FullscreenEventRequest267V1&)noexcept;
std::string SerializeFullscreenEventResult267V1(std::string_view,const FullscreenEventResult267V1&);
} // namespace
