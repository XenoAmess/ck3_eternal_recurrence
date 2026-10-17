#pragma once
#include "xar_bridge/ck3_12004_holy_site_relic_context.hpp"
#include <optional>

namespace xar::ck3_12004::religion::relic_permissions {
inline constexpr std::string_view kQueryStep="query-player-holy-site-relic-permissions-v1";
inline constexpr std::string_view kDomainKey="player_holy_site_relic_permissions_v1";
struct Bindings;
using InventoryGetter=bool(*)(const Bindings&,const void*,const void*&) noexcept;
using CandidatePredicate=bool(*)(const Bindings&,const void*,const void*,bool&) noexcept;
using ArtifactPermission=bool(*)(const Bindings&,const void*,const void*,bool&) noexcept;
using ButtonPermission=bool(*)(const Bindings&,const void*,bool&) noexcept;
struct Bindings {
 holy_site_relic::Bindings model{};
 const std::uint32_t* current_actor_reference=nullptr;
 InventoryGetter player_inventory=nullptr;
 CandidatePredicate candidate_predicate=nullptr;
 ArtifactPermission can_enshrine=nullptr,can_remove=nullptr;
 ButtonPermission enshrine_button=nullptr,remove_button=nullptr;
 std::string_view getter_backend="unavailable";
 bool source_bound=false;
};
struct ObservedBool {
 bool available=false;
 std::optional<bool> value;
 std::string unavailable_reason="native_permission_not_read";
};
struct Slot {
 std::uint32_t slot_index=0;
 std::optional<std::uint32_t> artifact_id;
};
struct SiteSlots {
 bool available=false;
 std::vector<Slot> slots;
 std::string unavailable_reason="site_inventory_slots_not_read";
};
struct CandidateCache {
 bool available=false;
 std::vector<std::uint32_t> artifact_ids;
 std::string unavailable_reason="window_candidate_cache_not_read";
};
struct WindowContext {
 bool available=false;
 std::optional<bool> root_present;
 std::optional<std::uint32_t> selected_holy_site_id,selected_artifact_id,selected_slot_index,selected_slot_artifact_id;
 std::string slot_mode="unknown";
 CandidateCache cached_candidates{};
 std::string unavailable_reason="holy_site_window_not_read";
};
struct PlayerInventory {
 bool available=false;
 std::vector<std::uint32_t> artifact_ids;
 std::optional<std::uint32_t> native_character_owner_id,native_holy_site_owner_id;
 std::optional<bool> owner_matches_player;
 std::string unavailable_reason="player_inventory_not_read";
};
struct CandidateEvaluation {
 std::uint32_t artifact_id=0xFFFFFFFFU;
 bool object_resolved=false,available=false,predicate_called=false;
 std::optional<bool> can_be_candidate;
 std::string unavailable_reason="candidate_not_evaluated";
};
struct CurrentCandidates {
 bool available=false;
 std::vector<std::uint32_t> artifact_ids;
 std::vector<CandidateEvaluation> evaluations;
 std::string unavailable_reason="current_candidates_not_evaluated";
};
struct ArtifactPermissions {
 bool available=false,object_resolved=false;
 std::optional<std::uint32_t> artifact_id,native_holy_site_owner_id;
 std::optional<std::int32_t> rarity_level;
 std::optional<bool> player_inventory_contains_reference;
 ObservedBool can_enshrine{},can_remove{};
 std::string unavailable_reason="artifact_id_not_requested";
};
struct CurrentButtons {
 bool available=false;
 std::optional<std::uint32_t> selected_artifact_id;
 std::optional<bool> context_matches_requested_artifact;
 ObservedBool can_enshrine{},can_remove{};
 std::string unavailable_reason="current_buttons_not_read";
};
struct Snapshot {
 bool available=false,loaded_source_pins_verified=false;
 std::uint64_t capture_epoch=0;
 std::int32_t date_raw=0,played_character_id=-1;
 std::optional<std::uint32_t> player_faith_id,requested_artifact_id;
 std::uint32_t requested_holy_site_id=0xFFFFFFFFU;
 std::optional<std::uint32_t> holy_site_id;
 SiteSlots site_inventory_slots{};
 WindowContext window_context{};
 PlayerInventory player_inventory{};
 CurrentCandidates current_candidates{};
 ArtifactPermissions artifact_permissions{};
 CurrentButtons current_buttons{};
 std::uint32_t native_getter_calls=0;
 std::string getter_backend="unavailable",unavailable_reason="relic_permissions_not_read";
};
Bindings BindHolySiteRelicPermissionsImage12004(std::uintptr_t,std::string_view) noexcept;
// Existing paused application owner callback only. No window setter/rebuild,
// selection, command construction/submission, inventory/cache write or date tick.
// Original getter/script context TLS/static initialization/allocation is allowed;
// deeper original script RNG effects remain unverified, so this is not idempotent.
bool ReadHolySiteRelicPermissions12004(const Bindings&,const void* jomini_owner,
 const ck3_12002::religion::Context&,std::uint32_t holy_site_id,
 std::optional<std::uint32_t> artifact_id,Snapshot&) noexcept;
std::string SerializeHolySiteRelicPermissions12004(const Snapshot&);
std::string SerializeHolySiteRelicPermissionsCommand12004(const Snapshot&,
 std::string_view request_id,std::uint64_t snapshot_revision,std::int64_t date_raw);
}
