#pragma once
#include "xar_bridge/ck3_121003_living_inventory26785313_v1.hpp"
#include "xar_bridge/ck3_121003_living_manage26785313_private_v1.hpp"
namespace xar::ck3_121003::build26785313 {
// New SOURCE-only entry family. The sealed query/UI13 families are unchanged.
inline constexpr char kLivingEntryStep267V1[]="ck3_121003_living_entry.execute";
inline constexpr char kLivingEntryCapability267V1[]="game.command.current-living-fixed-entry.v1";
inline constexpr char kLivingEntryBackend267V1[]="current267-fixed-living-entry-v1";
inline constexpr char kLivingEntryRequestSchema267V1[]="xar.living-entry.request/v1";
inline constexpr char kLivingEntryResultSchema267V1[]="xar.living-entry.result/v1";
inline constexpr char kLivingEntrySourceSchema267V1[]="xar.living-entry.source/v1";
enum class LivingEntryAction267V1 {query_manage,open_manage_list,open_manage_detail,
 confirm_manage,query_inventory_entry,open_inventory,query_detail_entry,open_detail};
enum class LivingEntryKind267V1 {manage,inventory,detail};
enum class LivingEntryStatus267V1 {unavailable,available,dispatched,rejected,expired,stale_source,indeterminate};
struct LivingEntryRequest267V1:LivingInventoryQueryRequest267V1 {
 LivingEntryAction267V1 action=LivingEntryAction267V1::query_manage;
 std::uint64_t provider_generation=0,query_sequence=0;
 // No caller artifact, owner, decision, view, event, index, widget or handle.
};
struct LivingEntryViewData267V1 {
 std::uint32_t expected_payload_full_id=0xFFFFFFFFU;
 bool window_found=false,visible=false,enabled=false,payload_bound=false;
 bool blocked_by_visible_modal=false,open_admissible=false;
 friend bool operator==(const LivingEntryViewData267V1&,const LivingEntryViewData267V1&)=default;
};
struct LivingEntrySource267V1 {
 LivingEntryKind267V1 kind=LivingEntryKind267V1::manage;
 std::uint32_t actor_full_id=0xFFFFFFFFU;
 std::optional<LivingManageSource267V1>manage;
 std::optional<LivingEntryViewData267V1>inventory,detail;
 bool sampled_twice=false;
 friend bool operator==(const LivingEntrySource267V1&,const LivingEntrySource267V1&)=default;
};
struct LivingEntryResult267V1 {
 LivingEntryAction267V1 action=LivingEntryAction267V1::query_manage;
 LivingEntryStatus267V1 status=LivingEntryStatus267V1::unavailable;
 std::uint64_t provider_generation=0,query_sequence=0,claim_sequence=0;
 std::uint64_t connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;
 bool facts_available=false,source_available=false,effect_attempted=false,native_returned=false,cleanup_known=true;
 ck3_1210::CoreSnapshotPrefix facts{};
 std::optional<LivingEntrySource267V1>source;
 std::string reason;
};
const char*LivingEntryActionName267V1(LivingEntryAction267V1)noexcept;
LivingEntryKind267V1 LivingEntryKindFor267V1(LivingEntryAction267V1)noexcept;
bool LivingEntryQuery267V1(LivingEntryAction267V1)noexcept;
bool LivingEntryRequestShape267V1(const LivingEntryRequest267V1&)noexcept;
bool LivingEntrySourceShape267V1(const LivingEntrySource267V1&,const ck3_1210::CoreSnapshotPrefix&)noexcept;
bool ParseLivingEntryRequest267V1(std::string_view,LivingEntryRequest267V1&)noexcept;
std::string SerializeLivingEntryResult267V1(std::string_view,const LivingEntryResult267V1&);
}
