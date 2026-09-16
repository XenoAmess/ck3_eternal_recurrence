#include "xar_bridge/faction_gift_receivers_v1.hpp"

#include <array>
#include <algorithm>
#include <cstddef>
#include <cstring>
#include <limits>
#include <string>
#include <utility>

#if defined(_WIN32)
#include <windows.h>
#endif

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotSize = 0x10;
constexpr std::size_t kStorageSlotObjectOffset = 0x08;
constexpr std::size_t kFactionIdentityOffset = 0x10;
constexpr std::size_t kFactionWarIdOffset = 0x8C;
constexpr std::size_t kWarIdentityOffset = 0x08;
constexpr std::uint32_t kIdentityIndexMask = 0x00FFFFFFU;
constexpr std::int32_t kMaximumComponentCount = 1 << 24;

template <typename T>
bool TryLoad(const void *base, std::size_t offset, T &output) noexcept {
  output = {};
  if (base == nullptr ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() -
                   reinterpret_cast<std::uintptr_t>(base)) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&output, static_cast<const std::byte *>(base) + offset,
                sizeof(output));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = {};
    return false;
  }
#endif
}

bool AddRva(std::uintptr_t base, std::uintptr_t rva,
            std::uintptr_t &output) noexcept {
  output = 0;
  if (base == 0 ||
      rva > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    return false;
  }
  output = base + rva;
  return true;
}

bool ResolveStoredExact(void *storage, std::uint32_t identity,
                        std::size_t round_trip_offset,
                        void *&object) noexcept {
  object = nullptr;
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!TryLoad(storage, kStorageSlotsOffset, slots) ||
      !TryLoad(storage, kStorageCapacityOffset, capacity) ||
      slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCount) {
    return false;
  }
  const auto index = identity & kIdentityIndexMask;
  if (index >= static_cast<std::uint32_t>(capacity)) return true;
  void *candidate = nullptr;
  if (!TryLoad(slots,
               static_cast<std::size_t>(index) * kStorageSlotSize +
                   kStorageSlotObjectOffset,
               candidate)) {
    return false;
  }
  if (candidate == nullptr) return true;
  std::uint32_t round_trip = 0;
  if (!TryLoad(candidate, round_trip_offset, round_trip)) return false;
  if (round_trip == identity) object = candidate;
  return true;
}

struct AtWarSampleV1 {
  void *faction = nullptr;
  std::uintptr_t faction_vtable = 0;
  std::uint32_t faction_identity = 0;
  std::uint32_t war_identity = 0;
  void *war = nullptr;
  std::uintptr_t war_vtable = 0;
  std::uintptr_t war_alive_leaf = 0;
  std::uint32_t war_round_trip = 0;
  bool at_war = false;

  friend bool operator==(const AtWarSampleV1 &,
                         const AtWarSampleV1 &) = default;
};

bool ReadSample(const FactionAtWarExactStoresV1 &stores,
                std::uint32_t faction_id,
                AtWarSampleV1 &sample) noexcept {
  sample = {};
  if (faction_id == 0 || stores.faction_storage == nullptr ||
      stores.faction_fallback == nullptr || stores.war_storage == nullptr ||
      stores.war_fallback == nullptr ||
      stores.expected_faction_vtable == 0 ||
      stores.expected_war_vtable == 0 ||
      stores.expected_null_war_vtable == 0 ||
      stores.expected_war_alive_leaf == 0 ||
      stores.expected_null_war_alive_leaf == 0) {
    return false;
  }

  if (!ResolveStoredExact(stores.faction_storage, faction_id,
                          kFactionIdentityOffset, sample.faction) ||
      sample.faction == nullptr || sample.faction == stores.faction_fallback ||
      !TryLoad(sample.faction, 0, sample.faction_vtable) ||
      sample.faction_vtable != stores.expected_faction_vtable ||
      !TryLoad(sample.faction, kFactionIdentityOffset,
               sample.faction_identity) ||
      sample.faction_identity != faction_id ||
      !TryLoad(sample.faction, kFactionWarIdOffset, sample.war_identity)) {
    return false;
  }

  void *resolved_war = nullptr;
  if (!ResolveStoredExact(stores.war_storage, sample.war_identity,
                          kWarIdentityOffset, resolved_war)) {
    return false;
  }
  sample.war = resolved_war == nullptr ? stores.war_fallback : resolved_war;
  if (!TryLoad(sample.war, 0, sample.war_vtable) ||
      !TryLoad(sample.war, kWarIdentityOffset, sample.war_round_trip)) {
    return false;
  }

  if (resolved_war == nullptr) {
    // Exact TPdxNullObject<CWar> is the stock legal no-war receiver. Its
    // component identity is -1 and its virtual IsAlive result is false.
    std::uintptr_t slot_one = 0;
    if (sample.war_vtable != stores.expected_null_war_vtable ||
        sample.war_round_trip != 0xFFFFFFFFU ||
        !TryLoad(reinterpret_cast<const void *>(sample.war_vtable),
                 sizeof(std::uintptr_t), slot_one) ||
        slot_one != stores.expected_null_war_alive_leaf) {
      return false;
    }
    sample.war_alive_leaf = slot_one;
    sample.at_war = false;
    return true;
  }

  if (sample.war_vtable != stores.expected_war_vtable ||
      sample.war_round_trip != sample.war_identity) {
    return false;
  }
  std::uintptr_t slot_one = 0;
  if (!TryLoad(reinterpret_cast<const void *>(sample.war_vtable),
               sizeof(std::uintptr_t), slot_one) ||
      slot_one != stores.expected_war_alive_leaf) {
    return false;
  }
  sample.war_alive_leaf = slot_one;
  // Frozen leaf 0x10495A0 is exactly `CWar+0x08 != -1`. Reproduce that
  // deterministic predicate after the full-generation and vtable checks.
  sample.at_war = sample.war_round_trip != 0xFFFFFFFFU;
  return true;
}

} // namespace

bool ReadFactionAtWarFromExactStoresV1(
    const FactionAtWarExactStoresV1 &stores, std::uint32_t faction_id,
    bool &at_war) noexcept {
  at_war = false;
  AtWarSampleV1 first{};
  AtWarSampleV1 second{};
  if (!ReadSample(stores, faction_id, first) ||
      !ReadSample(stores, faction_id, second) || first != second) {
    return false;
  }
  at_war = first.at_war;
  return true;
}

namespace {

bool LoadFactionAtWarStoresExact11906V1(
    std::uintptr_t module_base, FactionAtWarExactStoresV1 &stores) noexcept {
  stores = {};
  std::uintptr_t faction_storage_slot = 0;
  std::uintptr_t faction_fallback_slot = 0;
  std::uintptr_t war_storage_slot = 0;
  std::uintptr_t war_fallback_slot = 0;
  return AddRva(module_base, kFactionGiftFactionStorageSlotRvaV1,
                faction_storage_slot) &&
         AddRva(module_base, kFactionGiftFactionFallbackSlotRvaV1,
                faction_fallback_slot) &&
         AddRva(module_base, kFactionGiftWarStorageSlotRvaV1,
                war_storage_slot) &&
         AddRva(module_base, kFactionGiftWarFallbackSlotRvaV1,
                war_fallback_slot) &&
         TryLoad(reinterpret_cast<const void *>(faction_storage_slot), 0,
                 stores.faction_storage) &&
         TryLoad(reinterpret_cast<const void *>(faction_fallback_slot), 0,
                 stores.faction_fallback) &&
         TryLoad(reinterpret_cast<const void *>(war_storage_slot), 0,
                 stores.war_storage) &&
         TryLoad(reinterpret_cast<const void *>(war_fallback_slot), 0,
                 stores.war_fallback) &&
         AddRva(module_base, kFactionGiftFactionVtableRvaV1,
                stores.expected_faction_vtable) &&
         AddRva(module_base, kFactionGiftWarVtableRvaV1,
                stores.expected_war_vtable) &&
         AddRva(module_base, kFactionGiftNullWarVtableRvaV1,
                stores.expected_null_war_vtable) &&
         AddRva(module_base, kFactionGiftWarAliveLeafRvaV1,
                stores.expected_war_alive_leaf) &&
         AddRva(module_base, kFactionGiftNullWarAliveLeafRvaV1,
                stores.expected_null_war_alive_leaf);
}

bool SameFactionAtWarStoresV1(const FactionAtWarExactStoresV1 &left,
                              const FactionAtWarExactStoresV1 &right) noexcept {
  return left.faction_storage == right.faction_storage &&
         left.faction_fallback == right.faction_fallback &&
         left.war_storage == right.war_storage &&
         left.war_fallback == right.war_fallback &&
         left.expected_faction_vtable == right.expected_faction_vtable &&
         left.expected_war_vtable == right.expected_war_vtable &&
         left.expected_null_war_vtable == right.expected_null_war_vtable &&
         left.expected_war_alive_leaf == right.expected_war_alive_leaf &&
         left.expected_null_war_alive_leaf ==
             right.expected_null_war_alive_leaf;
}

} // namespace

bool ReadFactionAtWarExact11906V1(std::uintptr_t module_base,
                                 std::uint32_t faction_id,
                                 bool &at_war) noexcept {
  at_war = false;
  FactionAtWarExactStoresV1 first_stores{};
  FactionAtWarExactStoresV1 second_stores{};
  AtWarSampleV1 first{};
  AtWarSampleV1 second{};
  if (!LoadFactionAtWarStoresExact11906V1(module_base, first_stores) ||
      !ReadSample(first_stores, faction_id, first) ||
      !LoadFactionAtWarStoresExact11906V1(module_base, second_stores) ||
      !SameFactionAtWarStoresV1(first_stores, second_stores) ||
      !ReadSample(second_stores, faction_id, second) || first != second) {
    return false;
  }
  at_war = first.at_war;
  return true;
}

bool ReadFactionMetricsFromExactFixtureV1(
    const FactionMetricsExactFixtureV1 &fixture, std::uint32_t faction_id,
    std::int64_t &power_raw, std::int64_t &discontent_raw) noexcept {
  power_raw = 0;
  discontent_raw = 0;
  if (!fixture.available || faction_id == 0 ||
      fixture.faction_identity_first != faction_id ||
      fixture.faction_identity_second != faction_id ||
      fixture.expected_faction_vtable == 0 ||
      fixture.faction_vtable_first != fixture.expected_faction_vtable ||
      fixture.faction_vtable_second != fixture.expected_faction_vtable ||
      fixture.power_first != fixture.power_second ||
      fixture.discontent_first != fixture.discontent_second) {
    return false;
  }
  power_raw = fixture.power_first;
  discontent_raw = fixture.discontent_first;
  return true;
}

namespace {

using FactionItemFixedGetterV1 = std::int64_t *(*)(
    const std::uint32_t *faction_item_identity,
    std::int64_t *fixed_output);

struct FactionMetricsSampleV1 {
  void *storage = nullptr;
  void *faction = nullptr;
  std::uintptr_t faction_vtable = 0;
  std::uint32_t faction_identity = 0;
  std::int64_t underlying_discontent = 0;
  std::int64_t power_raw = 0;
  std::int64_t discontent_raw = 0;

  friend bool operator==(const FactionMetricsSampleV1 &,
                         const FactionMetricsSampleV1 &) = default;
};

bool ReadFactionMetricsSampleV1(std::uintptr_t module_base,
                                std::uint32_t faction_id,
                                FactionMetricsSampleV1 &sample) noexcept {
  sample = {};
  std::uintptr_t storage_slot = 0;
  std::uintptr_t fallback_slot = 0;
  std::uintptr_t expected_vtable = 0;
  std::uintptr_t power_leaf_rva = 0;
  std::uintptr_t discontent_leaf_rva = 0;
  void *fallback = nullptr;
  if (faction_id == 0 ||
      !AddRva(module_base, kFactionGiftFactionStorageSlotRvaV1,
              storage_slot) ||
      !AddRva(module_base, kFactionGiftFactionFallbackSlotRvaV1,
              fallback_slot) ||
      !AddRva(module_base, kFactionGiftFactionVtableRvaV1,
              expected_vtable) ||
      !AddRva(module_base, kFactionGiftPowerLeafRvaV1,
              power_leaf_rva) ||
      !AddRva(module_base, kFactionGiftDiscontentLeafRvaV1,
              discontent_leaf_rva) ||
      !TryLoad(reinterpret_cast<const void *>(storage_slot), 0,
               sample.storage) ||
      !TryLoad(reinterpret_cast<const void *>(fallback_slot), 0,
               fallback) ||
      sample.storage == nullptr || fallback == nullptr ||
      !ResolveStoredExact(sample.storage, faction_id,
                          kFactionIdentityOffset, sample.faction) ||
      sample.faction == nullptr || sample.faction == fallback ||
      !TryLoad(sample.faction, 0, sample.faction_vtable) ||
      sample.faction_vtable != expected_vtable ||
      !TryLoad(sample.faction, kFactionIdentityOffset,
               sample.faction_identity) ||
      sample.faction_identity != faction_id ||
      !TryLoad(sample.faction, 0x28,
               sample.underlying_discontent)) {
    return false;
  }

  const auto get_power =
      reinterpret_cast<FactionItemFixedGetterV1>(power_leaf_rva);
  const auto get_discontent =
      reinterpret_cast<FactionItemFixedGetterV1>(discontent_leaf_rva);
  const std::uint32_t faction_item_identity = faction_id;
  if (get_power(&faction_item_identity, &sample.power_raw) !=
          &sample.power_raw ||
      get_discontent(&faction_item_identity, &sample.discontent_raw) !=
          &sample.discontent_raw) {
    return false;
  }
  std::uintptr_t vtable_after = 0;
  std::uint32_t identity_after = 0;
  std::int64_t discontent_after = 0;
  return TryLoad(sample.faction, 0, vtable_after) &&
         TryLoad(sample.faction, kFactionIdentityOffset,
                 identity_after) &&
         TryLoad(sample.faction, 0x28, discontent_after) &&
         vtable_after == sample.faction_vtable &&
         identity_after == sample.faction_identity &&
         discontent_after == sample.underlying_discontent;
}

} // namespace

bool ReadFactionMetricsExact11906V1(std::uintptr_t module_base,
                                    std::uint32_t faction_id,
                                    std::int64_t &power_raw,
                                    std::int64_t &discontent_raw) noexcept {
  power_raw = 0;
  discontent_raw = 0;
  FactionMetricsSampleV1 first{};
  FactionMetricsSampleV1 second{};
  if (!ReadFactionMetricsSampleV1(module_base, faction_id, first) ||
      !ReadFactionMetricsSampleV1(module_base, faction_id, second) ||
      first != second) {
    return false;
  }
  power_raw = first.power_raw;
  discontent_raw = first.discontent_raw;
  return true;
}

namespace {

constexpr std::size_t kGiftPlayerLandStateOffsetV1 = 0x1B8;
constexpr std::size_t kGiftTargetingIdsOffsetV1 = 0x120;
constexpr std::size_t kGiftTargetingCountOffsetV1 = 0x12C;
constexpr std::size_t kGiftFactionTargetOffsetV1 = 0x40;
constexpr std::size_t kGiftFactionLeaderOffsetV1 = 0x44;
constexpr std::size_t kGiftFactionMemberRowsOffsetV1 = 0x48;
constexpr std::size_t kGiftFactionMemberCountOffsetV1 = 0x54;
constexpr std::size_t kGiftMemberStrideV1 = 0x20;
constexpr std::size_t kGiftMemberCharacterOffsetV1 = 0x08;
constexpr std::size_t kGiftMemberOwnerOffsetV1 = 0x0C;

struct DirectSourceSampleV1 {
  void *player = nullptr;
  void *land_state = nullptr;
  void *source_ids = nullptr;
  std::int32_t source_count = 0;
  bridge::FactionTargetingRowProbeResultV1 rows{};
};

bool ReadDirectSourceSampleV1(
    const FactionGiftDirectSourceStoresV1 &stores,
    const bridge::FactionTargetingRowProbeBindingV1 &required,
    DirectSourceSampleV1 &sample) noexcept {
  sample = {};
  if (!required.paused || required.proof_epoch == 0 ||
      required.proof_epoch >
          (std::numeric_limits<std::uint64_t>::max)() / 2 ||
      required.snapshot_revision == 0 ||
      required.player_character_id == 0 ||
      stores.character_storage == nullptr ||
      stores.faction_storage == nullptr ||
      stores.faction_fallback == nullptr ||
      stores.expected_faction_vtable == 0 ||
      !ResolveStoredExact(stores.character_storage,
                          required.player_character_id, 0x18,
                          sample.player) ||
      sample.player == nullptr ||
      !TryLoad(sample.player, kGiftPlayerLandStateOffsetV1,
               sample.land_state)) {
    return false;
  }
  sample.rows.required_binding = required;
  sample.rows.observed_binding = required;
  sample.rows.published_generation = required.proof_epoch * 2;
  if (sample.land_state != nullptr) {
    if (!TryLoad(sample.land_state, kGiftTargetingIdsOffsetV1,
                 sample.source_ids) ||
        !TryLoad(sample.land_state, kGiftTargetingCountOffsetV1,
                 sample.source_count) ||
        sample.source_count < 0 ||
        sample.source_count > static_cast<std::int32_t>(
            bridge::kFactionTargetingRowObserverMaximumRowsV1) ||
        (sample.source_count != 0 && sample.source_ids == nullptr)) {
      return false;
    }
  }
  sample.rows.faction_count =
      static_cast<std::uint32_t>(sample.source_count);
  for (std::int32_t index = 0; index < sample.source_count; ++index) {
    auto &row = sample.rows.factions[static_cast<std::size_t>(index)];
    if (!TryLoad(sample.source_ids,
                 static_cast<std::size_t>(index) * sizeof(std::uint32_t),
                 row.faction_id) ||
        row.faction_id == 0) {
      return false;
    }
    void *faction = nullptr;
    std::uintptr_t vtable = 0;
    std::uint32_t generation = 0;
    if (!ResolveStoredExact(stores.faction_storage, row.faction_id,
                            kFactionIdentityOffset, faction) ||
        faction == nullptr || faction == stores.faction_fallback ||
        !TryLoad(faction, 0, vtable) ||
        vtable != stores.expected_faction_vtable ||
        !TryLoad(faction, kFactionIdentityOffset, generation) ||
        generation != row.faction_id ||
        !TryLoad(faction, kGiftFactionTargetOffsetV1,
                 row.target_character_id) ||
        row.target_character_id != required.player_character_id) {
      return false;
    }
    std::uint32_t raw_leader = 0;
    if (!TryLoad(faction, kGiftFactionLeaderOffsetV1, raw_leader)) {
      return false;
    }
    if (raw_leader != 0) {
      void *leader = nullptr;
      if (!ResolveStoredExact(stores.character_storage, raw_leader,
                              0x18, leader) || leader == nullptr) {
        return false;
      }
      row.leader_present = true;
      row.leader_character_id = raw_leader;
    }
    void *members = nullptr;
    std::int32_t member_count = 0;
    if (!TryLoad(faction, kGiftFactionMemberRowsOffsetV1, members) ||
        !TryLoad(faction, kGiftFactionMemberCountOffsetV1,
                 member_count) ||
        member_count < 0 ||
        member_count > static_cast<std::int32_t>(
            bridge::kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1) ||
        (member_count != 0 && members == nullptr)) {
      return false;
    }
    row.character_member_count =
        static_cast<std::uint32_t>(member_count);
    for (std::int32_t member_index = 0; member_index < member_count;
         ++member_index) {
      const auto offset = static_cast<std::size_t>(member_index) *
                          kGiftMemberStrideV1;
      std::uint32_t member_id = 0;
      std::uint32_t owner_id = 0;
      void *member_character = nullptr;
      if (!TryLoad(members, offset + kGiftMemberCharacterOffsetV1,
                   member_id) ||
          !TryLoad(members, offset + kGiftMemberOwnerOffsetV1,
                   owner_id) ||
          owner_id != row.faction_id || member_id == 0 ||
          !ResolveStoredExact(stores.character_storage, member_id,
                              0x18, member_character) ||
          member_character == nullptr) {
        return false;
      }
      row.character_member_ids[static_cast<std::size_t>(member_index)] =
          member_id;
    }
    auto begin = row.character_member_ids.begin();
    auto end = begin + row.character_member_count;
    std::sort(begin, end);
    if (std::adjacent_find(begin, end) != end) return false;
    row.leader_present_in_character_members =
        row.leader_present &&
        std::binary_search(begin, end, row.leader_character_id);
  }
  auto begin = sample.rows.factions.begin();
  auto end = begin + sample.rows.faction_count;
  std::sort(begin, end, [](const auto &a, const auto &b) {
    return a.faction_id < b.faction_id;
  });
  for (auto row = begin + (begin != end ? 1 : 0); row != end; ++row) {
    if ((row - 1)->faction_id == row->faction_id) return false;
  }
  sample.rows.terminal =
      sample.source_count == 0
          ? bridge::FactionTargetingRowProbeTerminalV1::known_empty
          : bridge::FactionTargetingRowProbeTerminalV1::ready;
  return true;
}

bool SameDirectSourceSampleV1(const DirectSourceSampleV1 &a,
                              const DirectSourceSampleV1 &b) noexcept {
  if (a.player != b.player || a.land_state != b.land_state ||
      a.source_ids != b.source_ids ||
      a.source_count != b.source_count ||
      a.rows.faction_count != b.rows.faction_count ||
      a.rows.terminal != b.rows.terminal) {
    return false;
  }
  for (std::size_t index = 0; index < a.rows.faction_count; ++index) {
    const auto &left = a.rows.factions[index];
    const auto &right = b.rows.factions[index];
    if (left.faction_id != right.faction_id ||
        left.target_character_id != right.target_character_id ||
        left.leader_present != right.leader_present ||
        left.leader_character_id != right.leader_character_id ||
        left.leader_present_in_character_members !=
            right.leader_present_in_character_members ||
        left.character_member_count != right.character_member_count) {
      return false;
    }
    for (std::size_t member = 0;
         member < left.character_member_count; ++member) {
      if (left.character_member_ids[member] !=
          right.character_member_ids[member]) {
        return false;
      }
    }
  }
  return true;
}

} // namespace

bool ReadFactionGiftDirectTargetingRowsFromStoresV1(
    const FactionGiftDirectSourceStoresV1 &stores,
    const bridge::FactionTargetingRowProbeBindingV1 &required,
    bridge::FactionTargetingRowProbeResultV1 &rows) noexcept {
  rows = {};
  DirectSourceSampleV1 first{};
  DirectSourceSampleV1 second{};
  if (!ReadDirectSourceSampleV1(stores, required, first) ||
      !ReadDirectSourceSampleV1(stores, required, second) ||
      !SameDirectSourceSampleV1(first, second)) {
    return false;
  }
  rows = first.rows;
  return true;
}

bool ReadFactionGiftDirectTargetingRowsExact11906V1(
    std::uintptr_t module_base, const Bindings &bindings,
    const bridge::FactionTargetingRowProbeBindingV1 &required,
    bridge::FactionTargetingRowProbeResultV1 &rows) noexcept {
  rows = {};
  if (!bindings.enabled || bindings.character_storage_slot == nullptr) {
    return false;
  }
  std::uintptr_t faction_slot = 0;
  std::uintptr_t fallback_slot = 0;
  FactionGiftDirectSourceStoresV1 stores{};
  if (!AddRva(module_base, kFactionGiftFactionStorageSlotRvaV1,
              faction_slot) ||
      !AddRva(module_base, kFactionGiftFactionFallbackSlotRvaV1,
              fallback_slot) ||
      !AddRva(module_base, kFactionGiftFactionVtableRvaV1,
              stores.expected_faction_vtable) ||
      !TryLoad(bindings.character_storage_slot, 0,
               stores.character_storage) ||
      !TryLoad(reinterpret_cast<const void *>(faction_slot), 0,
               stores.faction_storage) ||
      !TryLoad(reinterpret_cast<const void *>(fallback_slot), 0,
               stores.faction_fallback)) {
    return false;
  }
  return ReadFactionGiftDirectTargetingRowsFromStoresV1(
      stores, required, rows);
}

namespace {

bool ReadIndependentEntitySampleV1(
    const FactionGiftDirectSourceStoresV1 &stores,
    std::uint32_t faction_id,
    FactionGiftIndependentEntityV1 &entity) noexcept {
  entity = {};
  if (faction_id == 0 || stores.character_storage == nullptr ||
      stores.faction_storage == nullptr ||
      stores.faction_fallback == nullptr ||
      stores.expected_faction_vtable == 0) {
    return false;
  }
  void *faction = nullptr;
  if (!ResolveStoredExact(stores.faction_storage, faction_id,
                          kFactionIdentityOffset, faction)) {
    return false;
  }
  if (faction == nullptr) return true; // Known absent full-generation slot.
  std::uintptr_t vtable = 0;
  std::uint32_t round_trip = 0;
  if (faction == stores.faction_fallback ||
      !TryLoad(faction, 0, vtable) ||
      vtable != stores.expected_faction_vtable ||
      !TryLoad(faction, kFactionIdentityOffset, round_trip) ||
      round_trip != faction_id ||
      !TryLoad(faction, kGiftFactionTargetOffsetV1,
               entity.target_character_id) ||
      entity.target_character_id == 0) {
    return false;
  }
  void *target = nullptr;
  if (!ResolveStoredExact(stores.character_storage,
                          entity.target_character_id, 0x18, target) ||
      target == nullptr) {
    return false;
  }
  std::uint32_t leader_id = 0;
  if (!TryLoad(faction, kGiftFactionLeaderOffsetV1, leader_id)) {
    return false;
  }
  if (leader_id != 0) {
    void *leader = nullptr;
    if (!ResolveStoredExact(stores.character_storage, leader_id, 0x18,
                            leader) || leader == nullptr) {
      return false;
    }
    entity.leader_character_id = leader_id;
  }
  void *members = nullptr;
  std::int32_t member_count = 0;
  if (!TryLoad(faction, kGiftFactionMemberRowsOffsetV1, members) ||
      !TryLoad(faction, kGiftFactionMemberCountOffsetV1, member_count) ||
      member_count < 0 ||
      member_count > static_cast<std::int32_t>(
          bridge::kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1) ||
      (member_count != 0 && members == nullptr)) {
    return false;
  }
  for (std::int32_t index = 0; index < member_count; ++index) {
    const auto offset = static_cast<std::size_t>(index) *
                        kGiftMemberStrideV1;
    std::uint32_t member_id = 0;
    std::uint32_t owner_id = 0;
    void *member = nullptr;
    if (!TryLoad(members, offset + kGiftMemberCharacterOffsetV1,
                 member_id) || member_id == 0 ||
        !TryLoad(members, offset + kGiftMemberOwnerOffsetV1, owner_id) ||
        owner_id != faction_id ||
        !ResolveStoredExact(stores.character_storage, member_id, 0x18,
                            member) || member == nullptr) {
      return false;
    }
    entity.member_character_ids.push_back(member_id);
  }
  std::sort(entity.member_character_ids.begin(),
            entity.member_character_ids.end());
  if (std::adjacent_find(entity.member_character_ids.begin(),
                         entity.member_character_ids.end()) !=
      entity.member_character_ids.end()) {
    return false;
  }
  std::uintptr_t vtable_after = 0;
  std::uint32_t identity_after = 0;
  std::uint32_t target_after = 0;
  std::uint32_t leader_after = 0;
  void *members_after = nullptr;
  std::int32_t count_after = 0;
  if (!TryLoad(faction, 0, vtable_after) || vtable_after != vtable ||
      !TryLoad(faction, kFactionIdentityOffset, identity_after) ||
      identity_after != faction_id ||
      !TryLoad(faction, kGiftFactionTargetOffsetV1, target_after) ||
      target_after != entity.target_character_id ||
      !TryLoad(faction, kGiftFactionLeaderOffsetV1, leader_after) ||
      leader_after != leader_id ||
      !TryLoad(faction, kGiftFactionMemberRowsOffsetV1, members_after) ||
      members_after != members ||
      !TryLoad(faction, kGiftFactionMemberCountOffsetV1, count_after) ||
      count_after != member_count) {
    return false;
  }
  entity.present = true;
  return true;
}

} // namespace

bool ReadFactionGiftIndependentEntityFromStoresV1(
    const FactionGiftDirectSourceStoresV1 &stores,
    std::uint32_t faction_id,
    FactionGiftIndependentEntityV1 &entity) noexcept {
  entity = {};
  FactionGiftIndependentEntityV1 first{};
  FactionGiftIndependentEntityV1 second{};
  if (!ReadIndependentEntitySampleV1(stores, faction_id, first) ||
      !ReadIndependentEntitySampleV1(stores, faction_id, second) ||
      first != second) {
    return false;
  }
  entity = std::move(first);
  return true;
}

bool ReadFactionGiftIndependentEntityExact11906V1(
    std::uintptr_t module_base, const Bindings &bindings,
    std::uint32_t faction_id,
    FactionGiftIndependentEntityV1 &entity) noexcept {
  entity = {};
  if (!bindings.enabled || bindings.character_storage_slot == nullptr) {
    return false;
  }
  std::uintptr_t faction_slot = 0;
  std::uintptr_t fallback_slot = 0;
  FactionGiftDirectSourceStoresV1 stores{};
  if (!AddRva(module_base, kFactionGiftFactionStorageSlotRvaV1,
              faction_slot) ||
      !AddRva(module_base, kFactionGiftFactionFallbackSlotRvaV1,
              fallback_slot) ||
      !AddRva(module_base, kFactionGiftFactionVtableRvaV1,
              stores.expected_faction_vtable) ||
      !TryLoad(bindings.character_storage_slot, 0,
               stores.character_storage) ||
      !TryLoad(reinterpret_cast<const void *>(faction_slot), 0,
               stores.faction_storage) ||
      !TryLoad(reinterpret_cast<const void *>(fallback_slot), 0,
               stores.faction_fallback) ||
      !ReadFactionGiftIndependentEntityFromStoresV1(
          stores, faction_id, entity)) {
    return false;
  }
  if (!entity.present) return true;
  FactionGiftIndependentEntityV1 after{};
  std::int64_t power_raw = 0;
  std::int64_t discontent_raw = 0;
  if (!ReadFactionMetricsExact11906V1(
          module_base, faction_id, power_raw, discontent_raw) ||
      !ReadFactionGiftIndependentEntityFromStoresV1(
          stores, faction_id, after) ||
      entity != after) {
    entity = {};
    return false;
  }
  entity.power_raw = power_raw;
  entity.discontent_raw = discontent_raw;
  entity.metrics_available = true;
  entity.metric_scale = kFactionGiftMetricScaleV1;
  return true;
}

namespace {

constexpr std::size_t kCharacterExtensionOffset = 0x1A8;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kDefinitionHashOffset = 0x14;
constexpr std::size_t kDefinitionKeyOffset = 0x18;
constexpr std::size_t kNamedValueSecondaryOffset = 0x88;
constexpr std::size_t kOpinionRowsOffset = 0x08;
constexpr std::size_t kOpinionRowCountOffset = 0x14;
constexpr std::size_t kActiveOpinionModifierOffset = 0x08;
constexpr std::int32_t kMaximumOpinionRows = 1 << 20;
constexpr std::int64_t kFixedPointScale = 100000;
constexpr std::size_t kScopeSize = 0x168;
constexpr std::size_t kSupport118Size = 0x118;
constexpr std::size_t kSupport2A8Size = 0x2A8;
constexpr std::size_t kInternalContextSize = 0x28;
constexpr std::uintptr_t kDestroyScopeTailRva = 0x81E900;
constexpr std::uintptr_t kDestroyRows48Rva = 0x81E980;
constexpr std::uintptr_t kDestroySupport2A8RowsRva = 0x969BA0;

using StableHash = std::uint32_t (*)(void *, const char *, std::uint32_t);
using ReadCharacterOpinion = std::int32_t (*)(void *, void *);
using LookupOpinionModifier = void *(*)(void *, std::uint32_t);
using FindOpinionGroup = void *(*)(void *, std::uint32_t);
using SumOpinionModifier = std::int32_t (*)(void *, void *);
using DefinitionIsValid = bool (*)(const void *);
using GetNamedValueDatabase = void *(*)();
using LookupNamedValue = const void *(*)(void *, std::uint32_t);
using CloneScope = void *(*)(void *, const void *);
using ConstructContainer = void *(*)(void *);
using EvaluateNamedFixed = std::int64_t *(*)(
    const void *, std::int64_t *, void *, void *, const void *);
using DestroyScopePart = void (*)(void *);
using DeallocateRows = void (*)(void *, void *, std::size_t);

template <std::size_t Size>
void *Aligned(std::array<std::byte, Size> &storage) noexcept {
  const auto value = reinterpret_cast<std::uintptr_t>(storage.data());
  return reinterpret_cast<void *>((value + 15U) & ~std::uintptr_t{15U});
}

bool ReadMsvcStringExact(const void *storage, std::string &output) noexcept {
  output.clear();
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  if (!TryLoad(storage, 0x10, size) || !TryLoad(storage, 0x18, capacity) ||
      size > capacity || size > 128) {
    return false;
  }
  const char *data = nullptr;
  if (capacity < 16) {
    data = static_cast<const char *>(storage);
  } else if (!TryLoad(storage, 0, data)) {
    return false;
  }
  if (size != 0 && data == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    output.assign(data == nullptr ? "" : data, static_cast<std::size_t>(size));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output.clear();
    return false;
  }
#endif
}

bool ResolveCharacterExact11906(std::uintptr_t module,
                                std::uint32_t identity,
                                void *&character) noexcept {
  character = nullptr;
  std::uintptr_t storage_slot = 0;
  std::uintptr_t fallback_slot = 0;
  void *storage = nullptr;
  void *fallback = nullptr;
  if (identity == 0 ||
      !AddRva(module, kFactionGiftCharacterStorageSlotRvaV1, storage_slot) ||
      !AddRva(module, kFactionGiftCharacterFallbackSlotRvaV1, fallback_slot) ||
      !TryLoad(reinterpret_cast<const void *>(storage_slot), 0, storage) ||
      !TryLoad(reinterpret_cast<const void *>(fallback_slot), 0, fallback) ||
      storage == nullptr || fallback == nullptr ||
      !ResolveStoredExact(storage, identity, kCharacterIdentityOffset,
                          character) ||
      character == nullptr || character == fallback) {
    character = nullptr;
    return false;
  }
  return true;
}

bool ValidateDefinitionIdentity(std::uintptr_t module, const void *definition,
                                std::uintptr_t primary_vtable_rva,
                                std::size_t secondary_offset,
                                std::uintptr_t secondary_vtable_rva,
                                std::uint32_t expected_hash,
                                std::string_view expected_key) noexcept {
  std::uintptr_t primary = 0;
  std::uintptr_t secondary = 0;
  std::uint32_t hash = 0;
  std::string key;
  std::uintptr_t expected_primary = 0;
  std::uintptr_t expected_secondary = 0;
  std::uintptr_t valid_leaf = 0;
  if (definition == nullptr ||
      !AddRva(module, primary_vtable_rva, expected_primary) ||
      !AddRva(module, secondary_vtable_rva, expected_secondary) ||
      !TryLoad(definition, 0, primary) || primary != expected_primary ||
      !TryLoad(definition, secondary_offset, secondary) ||
      secondary != expected_secondary ||
      !TryLoad(definition, kDefinitionHashOffset, hash) ||
      hash != expected_hash ||
      !ReadMsvcStringExact(static_cast<const std::byte *>(definition) +
                               kDefinitionKeyOffset,
                           key) ||
      key != expected_key ||
      !TryLoad(reinterpret_cast<const void *>(primary), 0, valid_leaf) ||
      valid_leaf == 0 ||
      !reinterpret_cast<DefinitionIsValid>(valid_leaf)(definition)) {
    return false;
  }
  return true;
}

bool ResolveOpinionModifier(std::uintptr_t module, void *&database,
                            void *&definition) noexcept {
  database = nullptr;
  definition = nullptr;
  std::uintptr_t database_slot = 0;
  if (!AddRva(module, kFactionGiftOpinionModifierDatabaseSlotRvaV1,
              database_slot) ||
      !TryLoad(reinterpret_cast<const void *>(database_slot), 0, database) ||
      database == nullptr) {
    return false;
  }
  const auto hash = reinterpret_cast<StableHash>(
      module + kFactionGiftStableHashRvaV1)(
      nullptr, kFactionGiftOpinionModifierKeyV1.data(),
      static_cast<std::uint32_t>(kFactionGiftOpinionModifierKeyV1.size()));
  if (hash != kFactionGiftOpinionModifierStableHashV1) return false;
  definition = reinterpret_cast<LookupOpinionModifier>(
      module + kFactionGiftOpinionModifierLookupRvaV1)(database, hash);
  return ValidateDefinitionIdentity(
      module, definition, kFactionGiftOpinionModifierVtableRvaV1,
      kFactionGiftOpinionModifierSecondaryOffsetV1,
      kFactionGiftOpinionModifierSecondaryVtableRvaV1,
      kFactionGiftOpinionModifierStableHashV1,
      kFactionGiftOpinionModifierKeyV1);
}

struct GiftOpinionSampleV1 {
  void *recipient = nullptr;
  void *player = nullptr;
  void *modifier_database = nullptr;
  void *modifier_definition = nullptr;
  std::uint32_t recipient_identity = 0;
  std::uint32_t player_identity = 0;
  std::int32_t opinion = 0;
  bool modifier_present = false;
  std::optional<std::int32_t> modifier_value;

  friend bool operator==(const GiftOpinionSampleV1 &,
                         const GiftOpinionSampleV1 &) = default;
};

bool ReadGiftOpinionSample(std::uintptr_t module,
                           std::uint32_t recipient_identity,
                           std::uint32_t player_identity,
                           GiftOpinionSampleV1 &sample) noexcept {
  sample = {};
  if (!ResolveCharacterExact11906(module, recipient_identity,
                                  sample.recipient) ||
      !ResolveCharacterExact11906(module, player_identity, sample.player) ||
      !ResolveOpinionModifier(module, sample.modifier_database,
                              sample.modifier_definition)) {
    return false;
  }
  sample.opinion = reinterpret_cast<ReadCharacterOpinion>(
      module + kFactionGiftReadCharacterOpinionRvaV1)(sample.recipient,
                                                       sample.player);

  void *extension = nullptr;
  if (!TryLoad(sample.recipient, kCharacterExtensionOffset, extension)) {
    return false;
  }
  if (extension != nullptr) {
    void *group = reinterpret_cast<FindOpinionGroup>(
        module + kFactionGiftFindActiveOpinionGroupRvaV1)(extension,
                                                          player_identity);
    if (group != nullptr) {
      void *rows = nullptr;
      std::int32_t count = 0;
      if (!TryLoad(group, kOpinionRowsOffset, rows) ||
          !TryLoad(group, kOpinionRowCountOffset, count) || count < 0 ||
          count > kMaximumOpinionRows || (count != 0 && rows == nullptr)) {
        return false;
      }
      for (std::int32_t index = 0; index < count; ++index) {
        void *active = nullptr;
        std::uintptr_t vtable = 0;
        void *modifier = nullptr;
        if (!TryLoad(rows, static_cast<std::size_t>(index) * sizeof(void *),
                     active)) {
          return false;
        }
        if (active == nullptr) continue;
        if (!TryLoad(active, 0, vtable) ||
            (vtable != module + kFactionGiftActiveOpinionVtableRvaV1 &&
             vtable != module + kFactionGiftTemporaryOpinionVtableRvaV1) ||
            !TryLoad(active, kActiveOpinionModifierOffset, modifier)) {
          return false;
        }
        if (modifier == sample.modifier_definition) {
          sample.modifier_present = true;
        }
      }
      if (sample.modifier_present) {
        sample.modifier_value = reinterpret_cast<SumOpinionModifier>(
            module + kFactionGiftSumOpinionModifierRvaV1)(
            group, sample.modifier_definition);
      }
    }
  }
  if (!TryLoad(sample.recipient, kCharacterIdentityOffset,
               sample.recipient_identity) ||
      !TryLoad(sample.player, kCharacterIdentityOffset,
               sample.player_identity) ||
      sample.recipient_identity != recipient_identity ||
      sample.player_identity != player_identity) {
    return false;
  }
  void *database_after = nullptr;
  void *definition_after = nullptr;
  return ResolveOpinionModifier(module, database_after, definition_after) &&
         database_after == sample.modifier_database &&
         definition_after == sample.modifier_definition;
}

bool DeallocateRowsExact(std::uintptr_t module, void *owner,
                         std::size_t data_offset,
                         std::size_t capacity_offset,
                         std::size_t count_offset,
                         std::size_t allocator_offset,
                         std::uintptr_t destroy_rows_rva) noexcept {
  void *data = nullptr;
  std::int32_t count = 0;
  if (!TryLoad(owner, data_offset, data) ||
      !TryLoad(owner, count_offset, count) || count < 0 ||
      count > kMaximumOpinionRows || (count != 0 && data == nullptr)) {
    return false;
  }
  if (data == nullptr) return count == 0;
  if (destroy_rows_rva != 0) {
    reinterpret_cast<DestroyScopePart>(module + destroy_rows_rva)(
        static_cast<std::byte *>(owner) + data_offset);
  }
  void *allocator = nullptr;
  std::uintptr_t vtable = 0;
  std::uintptr_t deallocate = 0;
  if (!TryLoad(owner, allocator_offset, allocator) || allocator == nullptr ||
      !TryLoad(allocator, 0, vtable) || vtable == 0 ||
      !TryLoad(reinterpret_cast<const void *>(vtable), 0x10, deallocate) ||
      deallocate == 0) {
    return false;
  }
  const std::int32_t zero = 0;
  void *const null_data = nullptr;
  std::memcpy(static_cast<std::byte *>(owner) + data_offset, &null_data,
              sizeof(null_data));
  std::memcpy(static_cast<std::byte *>(owner) + capacity_offset, &zero,
              sizeof(zero));
  std::memcpy(static_cast<std::byte *>(owner) + count_offset, &zero,
              sizeof(zero));
  reinterpret_cast<DeallocateRows>(deallocate)(allocator, data, 8);
  return true;
}

bool DestroyEvaluationState(std::uintptr_t module, void *scope,
                            void *support_118, void *support_2a8) noexcept {
  const bool support_2a8_ok = DeallocateRowsExact(
      module, support_2a8, 0x00, 0x08, 0x0C, 0x10,
      kDestroySupport2A8RowsRva);
  const bool support_118_ok = DeallocateRowsExact(
      module, support_118, 0x00, 0x08, 0x0C, 0x10, 0);
  reinterpret_cast<DestroyScopePart>(module + kDestroyScopeTailRva)(
      static_cast<std::byte *>(scope) + 0x118);
  const bool rows48_ok = DeallocateRowsExact(
      module, scope, 0x100, 0x108, 0x10C, 0x110, kDestroyRows48Rva);
  const bool named_ok = DeallocateRowsExact(
      module, scope, 0x18, 0x20, 0x24, 0x28, 0);
  return support_2a8_ok && support_118_ok && rows48_ok && named_ok;
}

bool ResolveNamedGiftOpinion(std::uintptr_t module, void *&database,
                             const void *&definition) noexcept {
  database = reinterpret_cast<GetNamedValueDatabase>(
      module + kFactionGiftNamedValueDatabaseGetterRvaV1)();
  if (database == nullptr) return false;
  const auto hash = reinterpret_cast<StableHash>(
      module + kFactionGiftStableHashRvaV1)(
      nullptr, kFactionGiftSendOpinionKeyV1.data(),
      static_cast<std::uint32_t>(kFactionGiftSendOpinionKeyV1.size()));
  if (hash != kFactionGiftSendOpinionStableHashV1) return false;
  definition = reinterpret_cast<LookupNamedValue>(
      module + kFactionGiftNamedValueLookupRvaV1)(database, hash);
  return ValidateDefinitionIdentity(
      module, definition, kFactionGiftNamedValueVtableRvaV1,
      kNamedValueSecondaryOffset, kFactionGiftNamedValueSecondaryVtableRvaV1,
      kFactionGiftSendOpinionStableHashV1, kFactionGiftSendOpinionKeyV1);
}

bool ConvertFixedOpinionExact(std::int64_t raw,
                              std::int32_t &output) noexcept {
  const auto minimum =
      static_cast<std::int64_t>((std::numeric_limits<std::int32_t>::min)()) *
      kFixedPointScale;
  const auto maximum =
      static_cast<std::int64_t>((std::numeric_limits<std::int32_t>::max)()) *
      kFixedPointScale;
  if (raw < minimum || raw > maximum) return false;
  const auto rounded =
      (raw < 0 ? raw - kFixedPointScale / 2 : raw + kFixedPointScale / 2) /
      kFixedPointScale;
  if (rounded < (std::numeric_limits<std::int32_t>::min)() ||
      rounded > (std::numeric_limits<std::int32_t>::max)()) {
    return false;
  }
  output = static_cast<std::int32_t>(rounded);
  return true;
}

bool FixtureIdentityComplete(const GiftOpinionReceiverFixtureV1 &fixture,
                             std::uint32_t recipient,
                             std::uint32_t player) noexcept {
  return fixture.available && recipient != 0 && player != 0 &&
         fixture.recipient_identity_before == recipient &&
         fixture.recipient_identity_after == recipient &&
         fixture.player_identity_before == player &&
         fixture.player_identity_after == player;
}

} // namespace

bool ReadGiftOpinionFromExactFixtureV1(
    const GiftOpinionReceiverFixtureV1 &fixture,
    std::uint32_t recipient_character_id,
    std::uint32_t player_character_id,
    GiftOpinionReceiverResultV1 &output) noexcept {
  output = {};
  if (!FixtureIdentityComplete(fixture, recipient_character_id,
                               player_character_id) ||
      fixture.modifier_definition == 0 ||
      fixture.modifier_definition_after != fixture.modifier_definition ||
      fixture.modifier_vtable == 0 ||
      fixture.modifier_vtable != fixture.expected_modifier_vtable ||
      fixture.modifier_hash != kFactionGiftOpinionModifierStableHashV1 ||
      fixture.modifier_key != kFactionGiftOpinionModifierKeyV1 ||
      fixture.opinion_first != fixture.opinion_second ||
      fixture.modifier_present_first != fixture.modifier_present_second ||
      fixture.modifier_value_first != fixture.modifier_value_second ||
      (fixture.modifier_present_first !=
       fixture.modifier_value_first.has_value())) {
    return false;
  }
  output.query_complete = true;
  output.recipient_opinion_of_player = fixture.opinion_first;
  output.gift_opinion_present = fixture.modifier_present_first;
  output.gift_opinion_modifier_value = fixture.modifier_value_first;
  return true;
}

bool ReadGiftOpinionDeltaFromExactFixtureV1(
    const GiftOpinionReceiverFixtureV1 &fixture,
    std::uint32_t recipient_character_id,
    std::uint32_t player_character_id,
    std::int32_t &opinion_delta) noexcept {
  opinion_delta = 0;
  if (!FixtureIdentityComplete(fixture, recipient_character_id,
                               player_character_id) ||
      fixture.named_definition == 0 ||
      fixture.named_definition_after != fixture.named_definition ||
      fixture.named_vtable == 0 || fixture.named_secondary_vtable == 0 ||
      fixture.named_vtable != fixture.expected_named_vtable ||
      fixture.named_secondary_vtable !=
          fixture.expected_named_secondary_vtable ||
      fixture.named_hash != kFactionGiftSendOpinionStableHashV1 ||
      fixture.named_key != kFactionGiftSendOpinionKeyV1 ||
      fixture.opinion_delta_first != fixture.opinion_delta_second) {
    return false;
  }
  opinion_delta = fixture.opinion_delta_first;
  return true;
}

bool ReadGiftOpinionExact11906V1(
    std::uintptr_t module_base, const Bindings &bindings,
    std::uint32_t recipient_character_id,
    std::uint32_t player_character_id,
    GiftOpinionReceiverResultV1 &output) noexcept {
  output = {};
  if (!bindings.enabled || module_base == 0 ||
      reinterpret_cast<std::uintptr_t>(bindings.character_storage_slot) !=
          module_base + kFactionGiftCharacterStorageSlotRvaV1) {
    return false;
  }
  GiftOpinionSampleV1 first{};
  GiftOpinionSampleV1 second{};
  if (!ReadGiftOpinionSample(module_base, recipient_character_id,
                             player_character_id, first) ||
      !ReadGiftOpinionSample(module_base, recipient_character_id,
                             player_character_id, second) ||
      first != second) {
    return false;
  }
  output.query_complete = true;
  output.recipient_opinion_of_player = first.opinion;
  output.gift_opinion_present = first.modifier_present;
  output.gift_opinion_modifier_value = first.modifier_value;
  return true;
}

bool ReadGiftOpinionDeltaExact11906V1(
    std::uintptr_t module_base, const void *character_interaction_scope,
    std::uint32_t recipient_character_id,
    std::uint32_t player_character_id,
    std::int32_t &opinion_delta) noexcept {
  opinion_delta = 0;
  if (module_base == 0 || character_interaction_scope == nullptr ||
      recipient_character_id == 0 || player_character_id == 0) {
    return false;
  }
  void *recipient_before = nullptr;
  void *player_before = nullptr;
  if (!ResolveCharacterExact11906(module_base, recipient_character_id,
                                  recipient_before) ||
      !ResolveCharacterExact11906(module_base, player_character_id,
                                  player_before)) {
    return false;
  }
  void *database = nullptr;
  const void *definition = nullptr;
  if (!ResolveNamedGiftOpinion(module_base, database, definition)) {
    return false;
  }

  std::array<std::byte, kScopeSize + 15> scope_storage{};
  std::array<std::byte, kSupport118Size + 15> support_118_storage{};
  std::array<std::byte, kSupport2A8Size + 15> support_2a8_storage{};
  std::array<std::byte, kInternalContextSize + 15> internal_storage{};
  void *const scope = Aligned(scope_storage);
  void *const support_118 = Aligned(support_118_storage);
  void *const support_2a8 = Aligned(support_2a8_storage);
  void *const internal = Aligned(internal_storage);
  if (reinterpret_cast<CloneScope>(
          module_base + kFactionGiftCloneEventTargetScopeRvaV1)(
          scope, character_interaction_scope) != scope) {
    return false;
  }
  const std::uint16_t character_kind = 4;
  const std::uint64_t recipient_payload = recipient_character_id;
  std::memcpy(static_cast<std::byte *>(scope) + 0x00, &character_kind,
              sizeof(character_kind));
  std::memcpy(static_cast<std::byte *>(scope) + 0x08, &recipient_payload,
              sizeof(recipient_payload));
  reinterpret_cast<ConstructContainer>(
      module_base + kFactionGiftSupport118ConstructorRvaV1)(support_118);
  reinterpret_cast<ConstructContainer>(
      module_base + kFactionGiftSupport2A8ConstructorRvaV1)(support_2a8);
  std::memset(internal, 0, kInternalContextSize);
  std::memcpy(static_cast<std::byte *>(internal) + 0x00, &scope,
              sizeof(scope));
  std::memcpy(static_cast<std::byte *>(internal) + 0x10, &scope,
              sizeof(scope));
  std::memcpy(static_cast<std::byte *>(internal) + 0x18, &support_118,
              sizeof(support_118));
  std::uint8_t evaluation_flag = 0;
  bool evaluated = TryLoad(reinterpret_cast<const void *>(
                               module_base + kFactionGiftEvaluationFlagRvaV1),
                           0, evaluation_flag);
  std::memcpy(static_cast<std::byte *>(internal) + 0x20, &evaluation_flag,
              sizeof(evaluation_flag));

  alignas(16) std::array<std::byte, 0x28> source_descriptor{};
  const char *const key_data = kFactionGiftSendOpinionKeyV1.data();
  const auto key_size =
      static_cast<std::uint32_t>(kFactionGiftSendOpinionKeyV1.size());
  const std::int32_t unknown_id = -1;
  const std::uint8_t source_valid = 1;
  std::memcpy(source_descriptor.data() + 0x00, &key_data, sizeof(key_data));
  std::memcpy(source_descriptor.data() + 0x08, &key_size, sizeof(key_size));
  std::memcpy(source_descriptor.data() + 0x10, &unknown_id,
              sizeof(unknown_id));
  std::memcpy(source_descriptor.data() + 0x24, &source_valid,
              sizeof(source_valid));

  std::int64_t first_raw = 0;
  std::int64_t second_raw = 0;
  auto *const evaluator = reinterpret_cast<EvaluateNamedFixed>(
      module_base + kFactionGiftEvaluateNamedFixedRvaV1);
  if (evaluated) {
    evaluated = evaluator(definition, &first_raw, internal, nullptr,
                          source_descriptor.data()) == &first_raw &&
                evaluator(definition, &second_raw, internal, nullptr,
                          source_descriptor.data()) == &second_raw &&
                first_raw == second_raw;
  }
  const bool teardown_ok = DestroyEvaluationState(
      module_base, scope, support_118, support_2a8);
  if (!evaluated || !teardown_ok) return false;

  void *database_after = nullptr;
  const void *definition_after = nullptr;
  void *recipient_after = nullptr;
  void *player_after = nullptr;
  if (!ResolveNamedGiftOpinion(module_base, database_after, definition_after) ||
      database_after != database || definition_after != definition ||
      !ResolveCharacterExact11906(module_base, recipient_character_id,
                                  recipient_after) ||
      !ResolveCharacterExact11906(module_base, player_character_id,
                                  player_after) ||
      recipient_after != recipient_before || player_after != player_before) {
    return false;
  }
  return ConvertFixedOpinionExact(first_raw, opinion_delta);
}

} // namespace xar::ck3_11906
