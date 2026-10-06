#pragma once

#include <cstdint>
#include <iosfwd>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12003::religion::holy_order {
struct TroopAssociation;

struct CurrentReinforcementBindings12003 {
  bool enabled = false;
  void **persistent_registry_slot = nullptr;
  std::int64_t *(*monthly_fraction)(void *, std::int64_t *) = nullptr;
  std::int32_t (*months_to_full)(void *) = nullptr;
  bool (*can_replenish)(void *, void *) = nullptr;
  bool (*chunk_can_replenish)(void *) = nullptr;
  void **army_registry_slot = nullptr;
  void **unit_registry_slot = nullptr;
};

struct CurrentReinforcementChunk12003 {
  std::int32_t chunk_index = -1;
  bool available = false;
  std::string unavailable_reason = "not_sampled";
  std::optional<std::int32_t> maximum_soldiers;
  std::optional<std::int32_t> current_soldiers;
  std::optional<std::uint32_t> persistent_regiment_id;
  std::optional<std::int32_t> native_chunk_index;
  std::optional<std::uint32_t> army_regiment_id;
  std::optional<std::uint8_t> pending_raw;
  std::optional<std::int32_t> state_raw;
  std::optional<bool> native_can_replenish;
  std::optional<bool> native_chunk_can_replenish;
};

struct CurrentReinforcementRegiment12003 {
  std::int32_t source_index = -1;
  std::uint32_t persistent_regiment_id = UINT32_MAX;
  bool available = false;
  std::string unavailable_reason = "not_sampled";
  bool resolved = false;
  // Actual persistent owner, distinct from order employer and army commander.
  std::optional<std::uint32_t> owner_character_id;
  std::optional<std::int64_t> monthly_replenishment_fraction_raw;
  std::optional<std::int32_t> native_months_to_full;
  std::vector<CurrentReinforcementChunk12003> chunks;
};

struct CurrentArmyRole12003 {
  std::int32_t association_index = -1;
  std::uint32_t army_regiment_id = UINT32_MAX;
  bool available = false;
  std::string unavailable_reason = "not_sampled";
  std::optional<std::uint32_t> native_carmy_id;
  bool army_resolved = false;
  std::optional<std::uint32_t> commander_character_id;
  std::optional<std::uint32_t> public_army_id;
  bool unit_resolved = false;
  std::optional<std::uint32_t> unit_carmy_backlink;
  std::optional<std::uint32_t> owner_character_id;
};
struct CurrentArmyRoles12003 {
  bool available = false;
  bool applies_to_player = false;
  std::string unavailable_reason = "native_holy_order_army_role_bindings_unavailable";
  std::vector<CurrentArmyRole12003> rows;
};

struct CurrentReinforcement12003 {
  bool available = false;
  std::string unavailable_reason = "native_holy_order_reinforcement_bindings_unavailable";
  std::optional<std::int32_t> source_count;
  // Persistent order+68 occurrences, including duplicate and invalid full refs.
  std::vector<CurrentReinforcementRegiment12003> rows;
  CurrentArmyRoles12003 army_roles;
};

CurrentReinforcementBindings12003 BindHolyOrderCurrentReinforcementImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
// The current-player holy-order provider supplies a verified military order.
// Reads current inputs only; does not invoke reinforcement writes or actions.
CurrentReinforcement12003 ReadHolyOrderCurrentReinforcement12003(
    const CurrentReinforcementBindings12003 &, const void *order,
    std::uint32_t holy_order_full_id) noexcept;
CurrentArmyRoles12003 ReadHolyOrderCurrentArmyRoles12003(
    const CurrentReinforcementBindings12003 &, const TroopAssociation &) noexcept;
void SerializeHolyOrderCurrentReinforcement12003(
    std::ostream &, const CurrentReinforcement12003 &);

} // namespace xar::ck3_12003::religion::holy_order
