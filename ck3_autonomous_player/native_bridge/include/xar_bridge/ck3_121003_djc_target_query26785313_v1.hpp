#pragma once
#include "xar_bridge/ck3_121003_djc_declarations26785313_raw_v1.hpp"
#include <array>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kDjcTargetQueryStep267V1[]="query-current-djc-declarable-wars-for-target-v1";
inline constexpr char kDjcTargetQueryCapability267V1[]="game.query.current-djc-declarable-wars-for-target.v1";
inline constexpr char kDjcTargetQuerySchema267V1[]="ck3.declarable_wars.current267_target_request.v1";
inline constexpr char kDjcTargetQueryResultSchema267V1[]="ck3.declarable_wars.current267_target_result.v1";
inline constexpr char kDjcTargetQueryBackend267V1[]="ck3-1.21.0.3-native-headless-main-thread";
struct DjcTargetQueryRequest267V1 {
 ck3_1210::CoreSnapshotPrefix expected{};std::int32_t target_character_id=-1;
 std::uint64_t deadline_unix_ms=0;std::array<char,97> request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return {request_id.data(),request_id_size};}
};
enum class DjcTargetQueryStatus267V1 {unavailable,expired,stale_core,available,indeterminate};
struct DjcTargetQueryResult267V1 {
 DjcTargetQueryStatus267V1 status=DjcTargetQueryStatus267V1::unavailable;
 DjcRawTarget267V1 raw{};bool core_available=false;
 ck3_1210::CoreSnapshotPrefix observed{};std::uint64_t connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;std::uint64_t provider_generation=0,query_sequence=0;std::string reason;
};
bool DjcTargetQueryRequestShape267V1(const DjcTargetQueryRequest267V1&) noexcept;
bool ParseDjcTargetQueryRequest267V1(std::string_view,DjcTargetQueryRequest267V1&) noexcept;
std::string SerializeDjcTargetQueryResult267V1(std::string_view,const DjcTargetQueryResult267V1&);
}
