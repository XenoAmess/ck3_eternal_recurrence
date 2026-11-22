#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kRiteTextRequestSchema267V1[]="ck3.rite_text.current267_request.v1";
inline constexpr char kRiteTextSourceSchema267V1[]="ck3.rite_text.current267_source.v1";
inline constexpr char kRiteTextResultSchema267V1[]="ck3.rite_text.current267_result.v1";
inline constexpr char kRiteTextBackend267V1[]="ck3-1.21.0.3-native-application-main-rite-text";
inline constexpr char kRiteTextStep267V1[]="current-rite-text-v1";
inline constexpr char kRiteTextCapability267V1[]="game.command.current-rite-text.v1";
enum class RiteTextAction267V1{query,set_name,set_description};
enum class RiteTextStatus267V1{unavailable,available,expired,stale_source,claim_consumed,prerequisite_rejected,text_dispatched,indeterminate};
struct RiteTextRequest267V1{RiteTextAction267V1 action=RiteTextAction267V1::query;ck3_1210::CoreSnapshotPrefix expected{};std::uint32_t expected_source_rite_id=0xFFFFFFFFU;std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;std::array<char,97>request_id{};std::uint8_t request_id_size=0;std::string text;std::string_view id()const noexcept{return{request_id.data(),request_id_size};}};
struct RiteTextSource267V1{std::uint32_t source_rite_id=0xFFFFFFFFU;std::int32_t actor_id=-1;bool is_creating=false;std::string name,description;bool window_visible=false,window_enabled=false,blocked_by_unrelated_modal=false,write_admissible=false;friend bool operator==(const RiteTextSource267V1&,const RiteTextSource267V1&)=default;};
struct RiteTextResult267V1{RiteTextAction267V1 action=RiteTextAction267V1::query;RiteTextStatus267V1 status=RiteTextStatus267V1::unavailable;bool source_available=false,cleanup_known=true,facts_available=false;std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;bool effect_attempted=false,native_returned=false,native_handled=false;ck3_1210::CoreSnapshotPrefix facts{};std::optional<RiteTextSource267V1>source;std::string reason;};
bool RiteTextRequestShape267V1(const RiteTextRequest267V1&)noexcept;
bool ParseRiteTextRequest267V1(std::string_view,RiteTextRequest267V1&)noexcept;
std::string SerializeRiteTextResult267V1(std::string_view,const RiteTextResult267V1&);
}
