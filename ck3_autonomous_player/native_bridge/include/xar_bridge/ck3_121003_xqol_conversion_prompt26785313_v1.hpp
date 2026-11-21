#pragma once
#include "xar_bridge/ck3_121003_letter26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
inline constexpr char kXqolPromptRequestSchema267V1[]="ck3.xqol_conversion_prompt.current267_request.v1";
inline constexpr char kXqolPromptResultSchema267V1[]="ck3.xqol_conversion_prompt.current267_result.v1";
inline constexpr char kXqolPromptSourceSchema267V1[]="ck3.xqol_conversion_prompt.current267_source.v1";
inline constexpr char kXqolPromptEventSchema267V1[]="ck3.xqol_conversion_prompt.current267_event.v1";
inline constexpr char kXqolPromptBackend267V1[]="ck3-1.21.0.3-native-application-main-xqol-conversion-prompt";
inline constexpr std::array<std::string_view,3>kXqolPromptSteps267V1{"query-xqol-conversion-prompt-current-v1","confirm-xqol-conversion-prompt-current-v1","cancel-xqol-conversion-prompt-current-v1"};
inline constexpr std::array<std::string_view,3>kXqolPromptCapabilities267V1{"game.query.current-xqol-conversion-prompt.v1","game.command.confirm-current-xqol-conversion-prompt.v1","game.command.cancel-current-xqol-conversion-prompt.v1"};
enum class XqolPromptAction267V1{query_prompt,confirm_conversion,cancel_conversion};
enum class XqolPromptStatus267V1{unavailable,expired,stale_source,claim_consumed,available,confirmation_dispatched,cancellation_dispatched,indeterminate};
struct XqolPromptRequest267V1{XqolPromptAction267V1 action=XqolPromptAction267V1::query_prompt;ck3_1210::CoreSnapshotPrefix expected{};std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;std::optional<std::int32_t>instance_id;std::array<char,97>request_id{};std::uint8_t request_id_size=0;std::string_view id()const noexcept{return {request_id.data(),request_id_size};}};
struct XqolPromptSource267V1{std::int32_t resident_count=0,named_root_count=0;bool census_complete=false;std::optional<LetterSource267V1>event;std::optional<std::int32_t>authored_option_count;bool confirm_admissible=false,cancel_admissible=false;friend bool operator==(const XqolPromptSource267V1&,const XqolPromptSource267V1&)=default;};
struct XqolPromptResult267V1{XqolPromptAction267V1 action=XqolPromptAction267V1::query_prompt;XqolPromptStatus267V1 status=XqolPromptStatus267V1::unavailable;bool source_available=false,effect_attempted=false,native_returned=false,cleanup_known=true,facts_available=false;std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix facts{};std::optional<std::int32_t>instance_id;std::optional<XqolPromptSource267V1>source;std::string reason;};
bool XqolPromptRequestShape267V1(const XqolPromptRequest267V1&)noexcept;
bool ParseXqolPromptRequest267V1(std::string_view,XqolPromptRequest267V1&)noexcept;
std::string SerializeXqolPromptResult267V1(std::string_view,const XqolPromptResult267V1&);
}
