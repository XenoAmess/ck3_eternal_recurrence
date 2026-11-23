#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kRiteBlockersRequestSchema267V1[]="ck3.rite_creation_blockers.current267_request.v1";
inline constexpr char kRiteBlockersSourceSchema267V1[]="ck3.rite_creation_blockers.current267_source.v1";
inline constexpr char kRiteBlockersResultSchema267V1[]="ck3.rite_creation_blockers.current267_result.v1";
inline constexpr char kRiteBlockersBackend267V1[]="ck3-1.21.0.3-native-application-main-rite-creation-blockers";
inline constexpr char kRiteBlockersStep267V1[]="query-current-rite-creation-blockers-v1";
inline constexpr char kRiteBlockersCapability267V1[]="game.query.current-rite-creation-blockers.v1";
enum class RiteBlockersStatus267V1 { unavailable,expired,stale_source,available,indeterminate };
struct RiteBlockersRequest267V1 { ck3_1210::CoreSnapshotPrefix expected{};std::uint32_t expected_source_rite_id=0xFFFFFFFFU;std::uint64_t deadline_unix_ms=0;std::array<char,97>request_id{};std::uint8_t request_id_size=0;std::string_view id()const noexcept{return{request_id.data(),request_id_size};} };
struct RiteBlockersSource267V1 { std::uint32_t source_rite_id=0xFFFFFFFFU;std::int32_t actor_id=-1;bool is_creating=false,native_can_create=false;std::string blockers_text;bool window_visible=false,window_enabled=false,sampled_twice=false;friend bool operator==(const RiteBlockersSource267V1&,const RiteBlockersSource267V1&)=default; };
struct RiteBlockersResult267V1 { RiteBlockersStatus267V1 status=RiteBlockersStatus267V1::unavailable;bool source_available=false,cleanup_known=true,facts_available=false;std::uint64_t provider_generation=0,query_sequence=0,connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;ck3_1210::CoreSnapshotPrefix facts{};std::optional<RiteBlockersSource267V1>source;std::string reason; };
bool RiteBlockersRequestShape267V1(const RiteBlockersRequest267V1&)noexcept;
bool ParseRiteBlockersRequest267V1(std::string_view,RiteBlockersRequest267V1&)noexcept;
std::string SerializeRiteBlockersResult267V1(std::string_view,const RiteBlockersResult267V1&);
}
