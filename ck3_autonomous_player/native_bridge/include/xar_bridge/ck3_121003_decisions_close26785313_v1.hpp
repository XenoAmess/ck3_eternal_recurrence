#pragma once
#include "xar_bridge/ck3_121003_curated_decisions26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
inline constexpr char kDecisionsCloseRequestSchema267V1[]="ck3.decisions_close.current267_request.v1";
inline constexpr char kDecisionsCloseResultSchema267V1[]="ck3.decisions_close.current267_result.v1";
inline constexpr char kDecisionsCloseBackend267V1[]="ck3-1.21.0.3-native-application-main-decisions-close";
inline constexpr std::array<std::string_view,2>kDecisionsCloseSteps267V1{"query-current-decisions-close-v1","close-current-decisions-list-v1"};
inline constexpr std::array<std::string_view,2>kDecisionsCloseCapabilities267V1{"game.query.current-decisions-close.v1","game.command.close-current-decisions-list.v1"};
enum class DecisionsCloseAction267V1{query_close,close_list};
enum class DecisionsCloseStatus267V1{unavailable,expired,stale_source,claim_consumed,available,close_dispatched,indeterminate};
struct DecisionsCloseRequest267V1{
 DecisionsCloseAction267V1 action=DecisionsCloseAction267V1::query_close;ck3_1210::CoreSnapshotPrefix expected{};
 std::uint64_t provider_generation=0,query_sequence=0,deadline_unix_ms=0;std::array<char,97>request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return{request_id.data(),request_id_size};}
};
struct DecisionsCloseResult267V1{
 DecisionsCloseAction267V1 action=DecisionsCloseAction267V1::query_close;DecisionsCloseStatus267V1 status=DecisionsCloseStatus267V1::unavailable;
 bool source_available=false,close_admissible=false,effect_attempted=false,native_returned=false,native_handled=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;
 ck3_1210::CoreSnapshotPrefix facts{};std::optional<CuratedDecisionSource267V1>source;std::string reason;
};
bool DecisionsCloseRequestShape267V1(const DecisionsCloseRequest267V1&)noexcept;
bool ParseDecisionsCloseRequest267V1(std::string_view,DecisionsCloseRequest267V1&)noexcept;
std::string SerializeDecisionsCloseResult267V1(std::string_view,const DecisionsCloseResult267V1&);
}
