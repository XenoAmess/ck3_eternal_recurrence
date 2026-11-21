#pragma once
#include "xar_bridge/ck3_121003_letter26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
inline constexpr char kLetterSetRequestSchema267V1[]="ck3.letter_set.current267_request.v1";
inline constexpr char kLetterSetResultSchema267V1[]="ck3.letter_set.current267_result.v1";
inline constexpr char kLetterSetSourceSchema267V1[]="ck3.letter_set.current267_source.v1";
inline constexpr char kLetterSetBackend267V1[]="ck3-1.21.0.3-native-application-main-letter-set";
inline constexpr std::array<std::string_view,2> kLetterSetSteps267V1{
 "query-current-letter-set-v1","reply-known-current-letter-instance-v1"};
inline constexpr std::array<std::string_view,2> kLetterSetCapabilities267V1{
 "game.query.current-letter-set.v1","game.command.reply-known-current-letter-instance.v1"};
enum class LetterSetAction267V1{query_letters,reply_known_instance};
struct LetterSetRequest267V1{
 LetterSetAction267V1 action=LetterSetAction267V1::query_letters;
 ck3_1210::CoreSnapshotPrefix expected{};
 std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;
 std::optional<std::int32_t> instance_id;
 std::array<char,97>request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return {request_id.data(),request_id_size};}
};
struct LetterSetSource267V1{
 std::int32_t resident_count=0,named_root_count=0;
 bool census_complete=false;
 std::vector<LetterSource267V1> letters;
 friend bool operator==(const LetterSetSource267V1&,const LetterSetSource267V1&)=default;
};
struct LetterSetResult267V1{
 LetterSetAction267V1 action=LetterSetAction267V1::query_letters;
 LetterStatus267V1 status=LetterStatus267V1::unavailable;
 bool source_available=false,effect_attempted=false,native_returned=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix facts{};
 std::optional<std::int32_t> instance_id;
 std::optional<LetterSetSource267V1>source;std::string reason;
};
bool LetterSetRequestShape267V1(const LetterSetRequest267V1&)noexcept;
bool ParseLetterSetRequest267V1(std::string_view,LetterSetRequest267V1&)noexcept;
std::string SerializeLetterSetResult267V1(std::string_view,const LetterSetResult267V1&);
} // namespace
