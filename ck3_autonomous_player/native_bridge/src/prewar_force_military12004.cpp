#include "xar_bridge/prewar_force_military12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <cstddef>
#include <cstring>
#include <limits>
#include <map>
#include <set>
#include <utility>

namespace xar::ck3_12004 {
namespace {

constexpr std::int32_t kMaximumDatabaseCapacity = 1'000'000;
constexpr std::int32_t kMaximumRegiments = 65'536;
constexpr std::size_t kMaximumOwners = 256;
constexpr std::size_t kMaximumSelectedArmies = 4096;
constexpr std::int32_t kMaximumSampleRegimentOccurrences = 262'144;

template <class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

struct Storage {
  const void *entries = nullptr;
  std::int32_t capacity = 0;
};

bool ReadStorage(void **slot, Storage &output) noexcept {
  if (slot == nullptr || *slot == nullptr) return false;
  output.entries = Load<const void *>(*slot, 0x20);
  output.capacity = Load<std::int32_t>(*slot, 0x2C);
  return output.capacity >= 0 &&
      output.capacity <= kMaximumDatabaseCapacity &&
      (output.capacity == 0 || output.entries != nullptr);
}

void *Resolve(const Storage &storage, std::int32_t id,
              std::optional<std::int32_t> *observed_id = nullptr) noexcept {
  if (id == -1) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  if (index >= static_cast<std::uint32_t>(storage.capacity)) return nullptr;
  void *object = Load<void *>(storage.entries,
      static_cast<std::size_t>(index) * 0x10 + 8);
  if (object != nullptr && observed_id != nullptr)
    *observed_id = Load<std::int32_t>(object, 0x10);
  return object != nullptr && Load<std::int32_t>(object, 0x10) == id
      ? object : nullptr;
}

bool Add(std::int64_t &sum, std::int64_t value) noexcept {
  if (value < 0 || sum > std::numeric_limits<std::int64_t>::max() - value)
    return false;
  sum += value;
  return true;
}

void FailArmy(PrewarForceRaisedArmy12004 &row, std::string_view reason) {
  row.available = false;
  row.current_lower_bound_ready = false;
  row.current_soldiers.reset();
  row.maximum_soldiers.reset();
  row.failure = reason;
}

void ReadArmy(const ck3_12002::ArmyBindings &bindings,
              const Storage &army_storage, const Storage &regiment_storage,
              void *unit, std::int32_t &remaining_regiment_budget,
              PrewarForceRaisedArmy12004 &row) {
  row.native_carmy_id = Load<std::int32_t>(unit, 0x178);
  void *army = Resolve(army_storage, row.native_carmy_id,
                       &row.observed_carmy_full_id);
  if (army != nullptr)
    row.observed_carmy_public_unit_id = Load<std::int32_t>(army, 0x124);
  if (army == nullptr || Load<std::uint32_t>(army, 0x14) != 0x41726D79U ||
      row.observed_carmy_public_unit_id != row.public_unit_id) {
    FailArmy(row, "carmy_full_generation_or_public_backlink_invalid");
    return;
  }
  if (bindings.get_unit_state != nullptr) {
    const auto state = bindings.get_unit_state(unit);
    if (state >= 1 && state <= 9) row.unit_state_code = state;
  }
  const void *ids = Load<const void *>(army, 0x38);
  const auto capacity = Load<std::int32_t>(army, 0x40);
  const auto count = Load<std::int32_t>(army, 0x44);
  if (capacity < 0 || capacity > kMaximumRegiments || count < 0 ||
      count > capacity || (count != 0 && ids == nullptr)) {
    FailArmy(row, "regiment_vector_invalid");
    return;
  }
  if (count > remaining_regiment_budget) {
    FailArmy(row, "regiment_sample_budget_exceeded");
    return;
  }
  remaining_regiment_budget -= count;
  std::int64_t current = 0;
  std::int64_t maximum = 0;
  std::set<std::int32_t> seen;
  bool valid = true;
  for (std::int32_t index = 0; index < count; ++index) {
    PrewarForceRegiment12004 regiment{};
    regiment.army_regiment_id = Load<std::int32_t>(ids,
        static_cast<std::size_t>(index) * 4);
    void *object = Resolve(regiment_storage, regiment.army_regiment_id,
                           &regiment.observed_full_id);
    if (!seen.insert(regiment.army_regiment_id).second)
      ++row.duplicate_regiment_occurrences;
    if (object == nullptr ||
        Load<std::uint32_t>(object, 0x14) != 0x41725267U) {
      regiment.failure = "arrg_full_generation_or_identity_invalid";
    } else {
      regiment.full_generation_ready = true;
      const auto c = Load<std::int32_t>(object, 0x38);
      const auto m = Load<std::int32_t>(object, 0x3C);
      regiment.current_soldiers = c;
      regiment.maximum_soldiers = m;
      if (c < 0 || m < 0) {
        regiment.failure = "arrg_headcount_invalid";
      } else {
        if (!Add(current, c) || !Add(maximum, m))
          regiment.failure = "arrg_headcount_sum_overflow";
      }
    }
    valid = valid && regiment.failure.empty();
    row.regiments.push_back(std::move(regiment));
  }
  if (!valid) {
    FailArmy(row, "regiment_rows_invalid");
    return;
  }
  const auto native_current = bindings.get_army_current_soldiers(
      static_cast<std::byte *>(army) + 0x38, 0);
  const auto native_maximum = bindings.get_army_maximum_soldiers(army);
  row.observed_native_current_soldiers = native_current;
  row.observed_native_maximum_soldiers = native_maximum;
  if (native_current < 0 || native_maximum < 0 ||
      native_current != current || native_maximum != maximum) {
    FailArmy(row, "native_headcount_sum_mismatch");
    return;
  }
  row.current_soldiers = native_current;
  row.maximum_soldiers = native_maximum;
  row.available = true;
  row.current_lower_bound_ready = row.duplicate_regiment_occurrences == 0;
}

bool FrameMatches(const game::Snapshot &frame,
                  const PrewarForceMilitaryRequest12004 &request) noexcept {
  return request.snapshot_revision != 0 && frame.paused && frame.map_ready &&
      frame.has_played_character && frame.played_character_alive &&
      frame.played_character_id == request.actor_character_id &&
      frame.date_raw == request.date_raw;
}

} // namespace

PrewarForceMilitaryStatus12004 ReadPrewarForceMilitary12004(
    const ck3_12002::ArmyBindings &armies,
    const ck3_12002::MilitaryBindings &military,
    const ck3_12003::PlayerArmyReserveBindingsV1 &reserve,
    const ck3_12002::MilitaryWorldAccess &world,
    std::string_view executable_sha256,
    const PrewarForceMilitaryRequest12004 &request,
    PrewarForceMilitarySnapshot12004 &output) noexcept {
  output = {};
  output.snapshot_revision = request.snapshot_revision;
  output.date_raw = request.date_raw;
  output.actor_character_id = request.actor_character_id;
  try {
    if (executable_sha256 != kExecutableSha256) {
      output.failure = "exact_12004_build_required";
      return output.status;
    }
    output.exact_build_ready = true;
    std::set<std::int32_t> owners(request.owner_character_ids.begin(),
                                  request.owner_character_ids.end());
    if (request.actor_character_id <= 0 || owners.empty() ||
        owners.size() > kMaximumOwners ||
        owners.size() != request.owner_character_ids.size() ||
        owners.contains(-1) || !owners.contains(request.actor_character_id)) {
      output.failure = "explicit_owner_request_invalid";
      return output.status;
    }
    if (world.read_snapshot == nullptr || world.resolve_character == nullptr) {
      output.failure = "world_callbacks_unavailable";
      return output.status;
    }
    game::Snapshot before{};
    if (!world.read_snapshot(world.context, before) || !FrameMatches(before, request)) {
      output.failure = "paused_actor_frame_unavailable";
      return output.status;
    }
    for (const auto id : request.owner_character_ids) {
      PrewarForceOwnerMilitary12004 owner{};
      owner.owner_character_id = id;
      void *character = world.resolve_character(world.context, id);
      owner.character_identity_ready = character != nullptr &&
          Load<std::int32_t>(character, 0x18) == id &&
          Load<std::uint32_t>(character, 0x1C) == 0x43686172U;
      if (!owner.character_identity_ready) owner.failure = "owner_full_generation_invalid";
      output.owners.push_back(std::move(owner));
    }
    Storage unit_storage{}, army_storage{}, regiment_storage{};
    const bool storage_ready = armies.enabled &&
        armies.get_army_current_soldiers != nullptr &&
        armies.get_army_maximum_soldiers != nullptr &&
        ReadStorage(armies.unit_storage_slot, unit_storage) &&
        ReadStorage(armies.internal_army_storage_slot, army_storage) &&
        ReadStorage(armies.regiment_storage_slot, regiment_storage);
    output.unit_scan_complete = storage_ready;
    std::size_t selected_army_count = 0;
    auto remaining_regiment_budget = kMaximumSampleRegimentOccurrences;
    if (storage_ready) {
      for (std::int32_t index = 0; index < unit_storage.capacity; ++index) {
        void *unit = Load<void *>(unit_storage.entries,
            static_cast<std::size_t>(index) * 0x10 + 8);
        if (unit == nullptr) continue; // Empty database slots are normal.
        const auto id = Load<std::int32_t>(unit, 0x10);
        const auto magic = Load<std::uint32_t>(unit, 0x14);
        if (magic != 0x556E6974U || id == -1 ||
            (static_cast<std::uint32_t>(id) & 0xFFFFFFU) !=
            static_cast<std::uint32_t>(index)) {
          ++output.malformed_unit_slots;
          output.unit_scan_complete = false;
          output.malformed_unit_slot_observations.push_back({index, id, magic, std::nullopt});
          continue;
        }
        const auto owner_id = Load<std::int32_t>(unit, 0x174);
        if (owner_id == -1) {
          ++output.malformed_unit_slots;
          output.unit_scan_complete = false;
          output.malformed_unit_slot_observations.push_back({index, id, magic, owner_id});
          continue;
        }
        auto owner = std::find_if(output.owners.begin(), output.owners.end(),
            [owner_id](const auto &row) { return row.owner_character_id == owner_id; });
        if (owner == output.owners.end()) continue;
        if (selected_army_count >= kMaximumSelectedArmies) {
          output.unit_scan_complete = false;
          if (owner->failure.empty()) owner->failure = "selected_army_sample_budget_exceeded";
          continue;
        }
        ++selected_army_count;
        PrewarForceRaisedArmy12004 row{};
        row.public_unit_id = id;
        row.owner_character_id = owner_id;
        if (owner->character_identity_ready)
          ReadArmy(armies, army_storage, regiment_storage, unit,
                   remaining_regiment_budget, row);
        else
          FailArmy(row, "owner_full_generation_invalid");
        owner->raised_armies.push_back(std::move(row));
      }
    }
    // Invalidate every conflicting row, including the first occurrence. A
    // shared CArmy alias or ArRg contributes no duplicate credit to subtotals.
    std::map<std::int32_t, PrewarForceRaisedArmy12004 *> carmy_first;
    std::map<std::int32_t, PrewarForceRaisedArmy12004 *> regiment_first;
    for (auto &owner : output.owners) {
      for (auto &row : owner.raised_armies) {
        if (row.native_carmy_id != -1) {
          const auto [at, inserted] = carmy_first.emplace(row.native_carmy_id, &row);
          if (!inserted) {
            FailArmy(*at->second, "duplicate_carmy_in_selected_scope");
            FailArmy(row, "duplicate_carmy_in_selected_scope");
          }
        }
        for (const auto &regiment : row.regiments) {
          if (regiment.army_regiment_id == -1) continue;
          const auto [at, inserted] = regiment_first.emplace(regiment.army_regiment_id, &row);
          if (!inserted && at->second != &row) {
            FailArmy(*at->second, "duplicate_arrg_between_carmies");
            FailArmy(row, "duplicate_arrg_between_carmies");
          }
        }
      }
    }
    bool complete = output.unit_scan_complete;
    PrewarForceOwnerMilitary12004 *actor = nullptr;
    for (auto &owner : output.owners) {
      owner.raised_scan_complete = output.unit_scan_complete && owner.character_identity_ready;
      owner.raised_current_lower_bound_ready = storage_ready &&
          output.unit_scan_complete && owner.character_identity_ready &&
          output.global_physical_ownership_ready;
      for (const auto &row : owner.raised_armies) {
        owner.raised_scan_complete = owner.raised_scan_complete && row.available;
        if (!row.available || !row.current_lower_bound_ready)
          owner.raised_current_lower_bound_ready = false;
        if (!row.available) continue;
        if (!Add(owner.observed_raised_current_sum, *row.current_soldiers) ||
            !Add(owner.observed_raised_maximum_sum, *row.maximum_soldiers) ||
            (row.current_lower_bound_ready &&
             !Add(owner.raised_current_lower_bound, *row.current_soldiers))) {
          owner.raised_current_lower_bound_ready = false;
          owner.raised_scan_complete = false;
          owner.failure = "owner_headcount_sum_overflow";
        }
      }
      if (!owner.raised_scan_complete && owner.failure.empty())
        owner.failure = storage_ready ? "raised_scope_partial" : "raised_storage_unavailable";
      complete = complete && owner.raised_scan_complete;
      if (owner.owner_character_id == request.actor_character_id) actor = &owner;
    }
    if (actor != nullptr && actor->character_identity_ready) {
      ck3_12002::PlayerDefaultRaiseObservationV1 raise{};
      (void)ck3_12002::ReadPlayerDefaultRaiseV1(military, world, raise);
      if (raise.actor.character_id == request.actor_character_id &&
          raise.date_raw == request.date_raw && raise.default_raise_legality_ready) {
        output.native_default_raise_legal = raise.actor.native_default_raise_legal;
        output.default_raise_legality_ready = output.native_default_raise_legal.has_value();
      }
      ck3_12002::PlayerDefaultRaiseObservationV1 unraised{};
      unraised.actor.character_id = request.actor_character_id;
      unraised.date_raw = request.date_raw;
      (void)ck3_12003::ReadPlayerUnraisedTroopsV1(reserve, world, unraised);
      output.actor_unraised_current = unraised.unraised_soldiers;
      output.actor_unraised_ready = unraised.unraised_troops_ready &&
          unraised.unraised_soldiers.has_value();
      output.actor_unraised_failure = output.actor_unraised_ready
          ? std::string{} : std::string(unraised.unraised_troops_failure);
    } else output.actor_unraised_failure = "actor_full_generation_invalid";
    if (actor != nullptr && actor->raised_current_lower_bound_ready &&
        output.actor_unraised_ready && output.default_raise_legality_ready &&
        output.native_default_raise_legal == true) {
      auto lower = actor->raised_current_lower_bound;
      if (Add(lower, *output.actor_unraised_current)) {
        output.actor_mobilizable_lower_bound = lower;
        output.actor_mobilizable_lower_bound_ready = true;
      } else output.actor_lower_bound_failure = "actor_lower_bound_overflow";
    } else {
      output.actor_lower_bound_failure = !output.default_raise_legality_ready
          ? "native_raise_legality_unavailable"
          : output.native_default_raise_legal == false ? "native_raise_not_legal"
          : !output.global_physical_ownership_ready ? "global_physical_ownership_unclosed"
          : "actor_current_sources_unavailable";
    }
    game::Snapshot after{};
    output.source_frame_ready = world.read_snapshot(world.context, after) &&
        FrameMatches(after, request) && after == before;
    if (!output.source_frame_ready) {
      output.actor_mobilizable_lower_bound.reset();
      output.actor_mobilizable_lower_bound_ready = false;
      output.unit_scan_complete = false;
      output.default_raise_legality_ready = false;
      for (auto &owner : output.owners) {
        owner.character_identity_ready = false;
        owner.raised_current_lower_bound_ready = false;
        owner.raised_scan_complete = false;
        owner.failure = "source_snapshot_changed";
        for (auto &row : owner.raised_armies) {
          row.available = false;
          row.current_lower_bound_ready = false;
          row.failure = "source_snapshot_changed";
        }
      }
      output.actor_unraised_ready = false;
      output.actor_lower_bound_failure = "source_snapshot_changed";
      output.actor_unraised_failure = "source_snapshot_changed";
      output.failure = "source_snapshot_changed";
      return output.status;
    }
    // "Available" qualifies the bounded observations, not an all-category
    // upper bound or the deliberately unclosed global physical force floor.
    // Unknown final raise legality remains an explicitly partial observation.
    complete = complete && output.actor_unraised_ready &&
        output.default_raise_legality_ready;
    output.status = complete ? PrewarForceMilitaryStatus12004::available
                             : PrewarForceMilitaryStatus12004::partial;
    if (!complete) output.failure = "military_observation_partial";
    return output.status;
  } catch (...) {
    output = {};
    output.failure = "military_sample_exception";
    return output.status;
  }
}

} // namespace xar::ck3_12004
