#pragma once
#include "xar_bridge/ck3_121003_rmtm_title26785313_raw_v1.hpp"
#include <array>
#include <optional>
#include <string>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kRmtmTitleQueryRequestSchema267V1[]="ck3.rmtm_title.current267_request.v1";
inline constexpr char kRmtmTitleQuerySourceSchema267V1[]="ck3.rmtm_title.current267_source.v1";
inline constexpr char kRmtmTitleQueryResultSchema267V1[]="ck3.rmtm_title.current267_result.v1";
inline constexpr char kRmtmTitleQueryBackend267V1[]="ck3-1.21.0.3-native-application-main-rmtm-title";
inline constexpr char kRmtmTitleQueryStep267V1[]="query-current-rmtm-title-v1";
inline constexpr char kRmtmTitleQueryCapability267V1[]="game.query.current-rmtm-title.v1";
enum class RmtmTitleQueryStatus267V1 {unavailable,expired,stale_source,available,indeterminate};
struct RmtmTitleQueryRequest267V1 {
 ck3_1210::CoreSnapshotPrefix expected{};
 std::uint64_t deadline_unix_ms=0;
 std::array<char,97>request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return{request_id.data(),request_id_size};}
 // No Title ID, role, selector, callback, index, provider/query lease or action.
};
struct RmtmTitleQuerySource267V1 {
 std::int32_t actor_id=-1;
 RmtmTitleSource267V1 title{};
 friend bool operator==(const RmtmTitleQuerySource267V1&,const RmtmTitleQuerySource267V1&)=default;
};
struct RmtmTitleQueryResult267V1 {
 RmtmTitleQueryStatus267V1 status=RmtmTitleQueryStatus267V1::unavailable;
 bool source_available=false,cleanup_known=true,facts_available=false;
 std::uint64_t provider_generation=0,query_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;
 ck3_1210::CoreSnapshotPrefix facts{};
 std::optional<RmtmTitleQuerySource267V1>source;
 std::string reason;
};
bool RmtmTitleQueryRequestShape267V1(const RmtmTitleQueryRequest267V1&)noexcept;
bool RmtmTitleQuerySourceShape267V1(const RmtmTitleQuerySource267V1&,const ck3_1210::CoreSnapshotPrefix&)noexcept;
bool ParseRmtmTitleQueryRequest267V1(std::string_view,RmtmTitleQueryRequest267V1&)noexcept;
std::string SerializeRmtmTitleQueryResult267V1(std::string_view,const RmtmTitleQueryResult267V1&);
}
