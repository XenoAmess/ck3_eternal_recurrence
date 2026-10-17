#pragma once
#include "xar_bridge/ck3_12004_holy_site_relic_permissions.hpp"

namespace xar::ck3_12004::religion::relic_action_context {
inline constexpr std::string_view kQueryStep="query-player-holy-site-relic-action-context-v1";
inline constexpr std::string_view kDomainKey="player_holy_site_relic_action_context_v1";
struct Bindings;
using SlotPicker=bool(*)(const Bindings&,const void*,const void*,std::int32_t&) noexcept;
using EquippedGetter=bool(*)(const Bindings&,const void*,const void*,bool&) noexcept;
using TextGetter=bool(*)(const Bindings&,const void*,std::uintptr_t,std::string&) noexcept;
struct Bindings {
 relic_permissions::Bindings permissions{};
 SlotPicker slot_picker=nullptr;
 EquippedGetter equipped=nullptr;
 TextGetter text=nullptr;
 bool source_bound=false;
 std::string_view getter_backend="unavailable";
};
struct Text {
 bool available=false;
 std::string text,unavailable_reason="selected_action_text_not_read";
};
struct Ownership {
 bool available=false,object_resolved=false;
 std::uint32_t artifact_id=0xFFFFFFFFU;
 std::optional<std::uint32_t> character_owner_id,holy_site_owner_id;
 std::optional<std::int32_t> rarity_level;
 std::optional<bool> character_owner_matches_player,holy_site_owner_matches_requested;
 std::optional<bool> player_owned_reference_member;
 relic_permissions::ObservedBool player_equipped_slot_member{},site_equipped_slot_member{};
 std::string unavailable_reason="artifact_ownership_not_read";
};
struct Destination {
 bool available=false,original_picker_called=false;
 std::optional<bool> explicit_slot_type_compatible;
 std::optional<std::uint32_t> selected_slot_index,effective_slot_index,replacing_artifact_id;
 std::string action_kind="unknown";
 Ownership replacing_artifact{};
 std::string unavailable_reason="effective_action_destination_not_read";
};
struct Snapshot {
 bool available=false,loaded_source_pins_verified=false;
 std::uint64_t capture_epoch=0;
 std::int32_t date_raw=0,played_character_id=-1;
 std::uint32_t requested_holy_site_id=0xFFFFFFFFU,requested_artifact_id=0xFFFFFFFFU;
 relic_permissions::Snapshot permissions{};
 Ownership artifact_ownership{};
 Destination destination{};
 Text selected_action_effect_description{},enshrine_disabled_tooltip{},remove_disabled_tooltip{};
 bool selected_artifact_matches_request=false,preview_identity_available=false;
 std::string preview_identity_sha256;
 std::uint32_t native_getter_calls=0;
 std::string getter_backend="unavailable",unavailable_reason="relic_action_context_not_read";
};
Bindings BindHolySiteRelicActionContextImage12004(std::uintptr_t,std::string_view) noexcept;
// Paused religion owner callback only. No selection, cache refresh, command or
// date tick. Description/permission evaluation allocates native context/TLS;
// deeper original script RNG side effects remain unknown, not idempotent.
bool ReadHolySiteRelicActionContext12004(const Bindings&,const void* jomini_owner,
 const ck3_12002::religion::Context&,std::uint32_t holy_site_id,
 std::uint32_t artifact_id,Snapshot&) noexcept;
std::string SerializeHolySiteRelicActionContext12004(const Snapshot&);
std::string SerializeHolySiteRelicActionContextCommand12004(const Snapshot&,
 std::string_view request_id,std::uint64_t snapshot_revision,std::int64_t date_raw);
// Stable canonical current observation, with no persisted process pointers.
std::string RelicActionPreviewCanonical12004(const Snapshot&);
}
