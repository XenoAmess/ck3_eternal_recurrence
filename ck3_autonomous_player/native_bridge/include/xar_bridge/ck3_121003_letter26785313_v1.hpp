#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
#include <vector>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kLetterRequestSchema267V1[]="ck3.letter.current267_request.v1";
inline constexpr char kLetterResultSchema267V1[]="ck3.letter.current267_result.v1";
inline constexpr char kLetterSourceSchema267V1[]="ck3.letter.current267_source.v1";
inline constexpr char kLetterBackend267V1[]="ck3-1.21.0.3-native-application-main-letter";
inline constexpr std::array<std::string_view,2> kLetterSteps267V1{
 "query-current-letter-v1","reply-known-current-letter-v1"};
inline constexpr std::array<std::string_view,2> kLetterCapabilities267V1{
 "game.query.current-letter.v1","game.command.reply-known-current-letter.v1"};
inline constexpr char kKnownLetterDefinition267V1[]="ep3_laamps.0003";
inline constexpr char kKnownLetterOption267V1[]="ep3_laamps.0003.a";
enum class LetterAction267V1{query_letter,reply_known};
enum class LetterStatus267V1{unavailable,expired,stale_source,claim_consumed,available,reply_dispatched,indeterminate};
struct LetterRequest267V1{
 LetterAction267V1 action=LetterAction267V1::query_letter;ck3_1210::CoreSnapshotPrefix expected{};
 std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;
 std::array<char,97>request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return {request_id.data(),request_id_size};}
};
struct LetterOption267V1{
 std::int32_t authored_option_index=-1;bool native_can_select=false;
 std::string text,disabled_reason;std::optional<std::string>source_bound_option_key;
 friend bool operator==(const LetterOption267V1&,const LetterOption267V1&)=default;
};
struct LetterSource267V1{
 std::int32_t resident_count=0;bool letter_found=false,named_root_bound=false,window_visible=false,window_enabled=false;
 std::optional<std::int32_t>instance_id,recipient_character_id;
 std::optional<std::string>definition_key,opening,description;std::vector<LetterOption267V1>options;
 bool known_reply_admissible=false;
 friend bool operator==(const LetterSource267V1&,const LetterSource267V1&)=default;
};
struct LetterResult267V1{
 LetterAction267V1 action=LetterAction267V1::query_letter;LetterStatus267V1 status=LetterStatus267V1::unavailable;
 bool source_available=false,effect_attempted=false,native_returned=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix facts{};std::optional<LetterSource267V1>source;std::string reason;
};
bool LetterRequestShape267V1(const LetterRequest267V1&)noexcept;
bool ParseLetterRequest267V1(std::string_view,LetterRequest267V1&)noexcept;
std::string SerializeLetterResult267V1(std::string_view,const LetterResult267V1&);
} // namespace
