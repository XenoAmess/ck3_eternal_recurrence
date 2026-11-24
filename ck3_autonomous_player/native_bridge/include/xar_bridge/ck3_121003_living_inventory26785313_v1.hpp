#pragma once
#include "xar_bridge/ck3_121003_living_inventory26785313_raw_v1.hpp"
#include <string_view>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kLivingInventoryQueryBackend267V1[]="current267-fixed-living-inventory-v1";
inline constexpr char kLivingInventoryQueryStep267V1[]="ck3_121003_living_inventory.query";
inline constexpr char kLivingInventoryQueryCapability267V1[]="game.living.inventory.query.v1";
inline constexpr char kLivingInventoryQueryRequestSchema267V1[]="xar.living-inventory.request/v1";
inline constexpr char kLivingInventoryQueryResultSchema267V1[]="xar.living-inventory.result/v1";
inline constexpr char kLivingInventoryQuerySourceSchema267V1[]="xar.living-inventory.source/v1";
struct LivingInventoryQueryRequest267V1:LivingInventoryRequest267V1 {
 std::array<char,96>request_id{};std::uint8_t request_id_size=0;
 std::string_view id()const noexcept{return {request_id.data(),request_id_size};}
};
using LivingInventoryQuerySource267V1=LivingInventorySource267V1;
enum class LivingInventoryQueryStatus267V1{unavailable,available,expired,stale_source,indeterminate};
struct LivingInventoryQueryResult267V1 {
 LivingInventoryQueryStatus267V1 status=LivingInventoryQueryStatus267V1::unavailable;
 std::uint64_t provider_generation=0,query_sequence=0;
 std::uint64_t connection_generation=0,ticket_sequence=0,pump_epoch=0;std::uint32_t thread_id=0;
 bool facts_available=false,source_available=false,cleanup_known=true;
 ck3_1210::CoreSnapshotPrefix facts{};std::optional<LivingInventoryQuerySource267V1>source;
 std::string reason;
};
bool LivingInventoryQueryRequestShape267V1(const LivingInventoryQueryRequest267V1&)noexcept;
bool LivingInventoryQuerySourceShape267V1(const LivingInventoryQuerySource267V1&,const ck3_1210::CoreSnapshotPrefix&)noexcept;
bool ParseLivingInventoryQueryRequest267V1(std::string_view,LivingInventoryQueryRequest267V1&)noexcept;
std::string SerializeLivingInventoryQueryResult267V1(std::string_view,const LivingInventoryQueryResult267V1&);
}
