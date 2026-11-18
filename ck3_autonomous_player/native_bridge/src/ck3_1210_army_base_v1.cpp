#include "xar_bridge/ck3_1210_army_base_v1.hpp"

#include <cstring>
#include <limits>
#include <type_traits>
#include <utility>
#if defined(_MSC_VER)
#include <windows.h>
#endif

// Native source-use: D39110 resolves CArmy fullID10/tag14 via6A666F0.
// CArmyManager RTTI4E9E148 + ctor2FA7CC0 owns registry+48; GameData
// ctor2FDF166 and owner2D27C10 prove data+3AC38. Typed registry4E9DEF0
// is published2FADD63. Default block6A66698 is zeroed at2CEEF24..5A;
// D39159/D39166 -> D39230 proves the legal no-CArmy regular branch.
namespace xar::ck3_1210 {
namespace {
constexpr std::uint32_t kUnitTag = 0x556E6974U, kArmyTag = 0x41726D79U;
constexpr std::uint32_t kCharacterTag = 0x43686172U;
static_assert(std::is_trivially_copyable_v<PlayerArmyStateInputWordsV1>);

bool LocalCopy(void *, const void *source, void *destination, std::size_t size) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(destination, source, size); return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
bool Core(const CoreBindings &bindings, CoreSnapshotPrefix &out) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return ReadCoreSnapshot(bindings, out);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { out = {}; return false; }
#endif
}
bool SameCore(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
std::uint64_t Pointer(const void *p) noexcept {
  return static_cast<std::uint64_t>(reinterpret_cast<std::uintptr_t>(p));
}
std::uint64_t Pair(std::int32_t low, std::uint32_t high) noexcept {
  return static_cast<std::uint32_t>(low) | (static_cast<std::uint64_t>(high) << 32);
}
bool Fail(ArmyBaseObservationV1 &out, std::string_view reason) noexcept {
  const auto calls = out.native_state_calls_attempted;
  out = {}; out.native_state_calls_attempted = calls;
  out.unavailable_reason = reason; return false;
}
struct StateInput {
  const ArmyBaseBindingsV1 &bindings;
  const CoreSnapshotPrefix &expected;
  ArmyBaseReadAccessV1 access;
  std::string_view reason = "army_base_state_input_unavailable";

  template <class T> bool Read(const void *base, std::size_t offset, T &out) noexcept {
    static_assert(std::is_trivially_copyable_v<T> && sizeof(T) <= 8);
    const auto p = reinterpret_cast<std::uintptr_t>(base);
    const auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
    if (p == 0 || offset > maximum - p || sizeof(T) - 1 > maximum - (p + offset)) {
      reason = "army_base_state_input_address_invalid"; return false;
    }
    const auto copy = access.copy != nullptr ? access.copy : LocalCopy;
    if (!copy(access.context, reinterpret_cast<const void *>(p + offset), &out, sizeof(T))) {
      reason = "army_base_state_input_read_failed"; return false;
    }
    return true;
  }
  bool Actor(const void *storage, const void *&actor) noexcept {
    const void *slots = nullptr, *death = nullptr;
    std::int32_t capacity = 0, id = -1; std::uint32_t tag = 0;
    if (!Read(storage, 0x20, slots) || !Read(storage, 0x2C, capacity)) return false;
    const auto index = static_cast<std::uint32_t>(expected.played_character_id) & 0x00FFFFFFU;
    if (capacity <= 0 || capacity > kPlayerArmyStorageLimitV1 || slots == nullptr ||
        index >= static_cast<std::uint32_t>(capacity)) {
      reason = "army_base_state_actor_unresolved"; return false;
    }
    if (!Read(slots, static_cast<std::size_t>(index) * 0x10 + 8, actor) ||
        !Read(actor, 0x18, id) || !Read(actor, 0x1C, tag) ||
        !Read(actor, kCharacterDeathDataOffset, death)) return false;
    if (id != expected.played_character_id || tag != kCharacterTag || death != nullptr) {
      reason = "army_base_state_actor_unresolved"; return false;
    }
    return true;
  }
  bool Capture(const void *unit, std::int32_t expected_reference,
      PlayerArmyStateInputWordsV1 &words) noexcept {
    words = {}; CoreSnapshotPrefix core{};
    if (!Core(bindings.player_armies.core, core) || !SameCore(core, expected)) {
      reason = "army_base_state_core_changed"; return false;
    }
    const auto &cb = bindings.player_armies.core;
    const void *game = nullptr, *jomini = nullptr, *data = nullptr;
    const void *characters = nullptr, *actor = nullptr;
    if (!Read(cb.game_state_slot, 0, game) || !Read(cb.jomini_state_slot, 0, jomini) ||
        !Read(cb.character_storage_slot, 0, characters) ||
        !Read(game, kGameStateDataOffset, data) || !Actor(characters, actor)) return false;
    if (jomini == nullptr || data == nullptr) {
      reason = "army_base_state_roots_unavailable"; return false;
    }
    std::int32_t unit_id = -1, owner = -1, reference = -1;
    std::uint32_t unit_tag = 0;
    if (!Read(unit, 0x10, unit_id) || !Read(unit, 0x14, unit_tag) ||
        !Read(unit, 0x174, owner) || !Read(unit, 0x178, reference)) return false;
    if (unit_id == -1 || unit_tag != kUnitTag || owner != expected.played_character_id ||
        reference != expected_reference) {
      reason = "army_base_state_unit_identity_changed"; return false;
    }
    const void *registry = nullptr, *owned = nullptr, *slots = nullptr;
    std::uintptr_t manager_type = 0, registry_type = 0;
    std::int32_t capacity = 0;
    if (!Read(data, kArmyBaseManagerOffsetV1, manager_type) ||
        !Read(data, kArmyBaseManagerOffsetV1 + kArmyBaseManagerRegistryOffsetV1, owned) ||
        !Read(bindings.native_army_registry_slot, 0, registry)) return false;
    if (manager_type != bindings.native_army_manager_vtable || registry != owned) {
      reason = "army_base_state_registry_owner_mismatch"; return false;
    }
    if (registry != nullptr) {
      if (!Read(registry, 0, registry_type) || !Read(registry, 0x20, slots) ||
          !Read(registry, 0x2C, capacity)) return false;
      if (registry_type != bindings.native_army_registry_vtable) {
        reason = "army_base_state_registry_type_mismatch"; return false;
      }
      if (capacity < 0 || capacity > kPlayerArmyStorageLimitV1 ||
          (capacity != 0 && slots == nullptr)) {
        reason = "army_base_state_registry_header_invalid"; return false;
      }
    }
    const void *army = nullptr, *fallback = nullptr;
    std::int32_t army_id = 0, fallback_id = 0;
    std::uint32_t army_tag = 0, fallback_tag = 0;
    std::uintptr_t object_type = 0;
    if (reference == -1) {
      // The low24 sentinel index is beyond the admitted bounded registry.
      // Verify the actual default block used by D39152, not a fake CArmy row.
      if (!Read(bindings.no_army_fallback_slot, 0, fallback) ||
          !Read(fallback, 0, object_type) || !Read(fallback, 0x10, fallback_id) ||
          !Read(fallback, 0x14, fallback_tag)) return false;
      if (object_type != 0 || fallback_id != 0 || fallback_tag != 0) {
        reason = "army_base_no_army_default_unproven"; return false;
      }
    } else {
      const auto index = static_cast<std::uint32_t>(reference) & 0x00FFFFFFU;
      if (registry == nullptr || index >= static_cast<std::uint32_t>(capacity)) {
        reason = "army_base_state_army_generation_unresolved"; return false;
      }
      if (!Read(slots, static_cast<std::size_t>(index) * 0x10 + 8, army)) return false;
      if (army == nullptr) { reason = "army_base_state_army_generation_unresolved"; return false; }
      if (!Read(army, 0, object_type) || !Read(army, 0x10, army_id) ||
          !Read(army, 0x14, army_tag)) return false;
      if (army_id != reference || army_tag != kArmyTag ||
          object_type != bindings.native_army_vtable) {
        reason = "army_base_state_army_generation_unresolved"; return false;
      }
    }
    // Fixed twenty exact words: roots/actor/unit, full Unit identity+owner/ref,
    // native manager/registry/header, selected CArmy identity or zero-default
    // identity, and actual Core IDs/clock. No pointer/value hashing occurs.
    words[0] = Pointer(game); words[1] = Pointer(jomini); words[2] = Pointer(data);
    words[3] = Pointer(characters); words[4] = Pointer(actor); words[5] = Pointer(unit);
    words[6] = Pair(unit_id, unit_tag);
    words[7] = Pair(owner, static_cast<std::uint32_t>(reference));
    words[8] = manager_type; words[9] = Pointer(registry); words[10] = registry_type;
    words[11] = Pointer(slots); words[12] = static_cast<std::uint32_t>(capacity);
    words[13] = Pointer(army); words[14] = Pair(army_id, army_tag);
    words[15] = Pointer(fallback); words[16] = object_type;
    words[17] = Pair(fallback_id, fallback_tag);
    const auto clock_flags = static_cast<std::uint32_t>(core.clock.speed) |
        (static_cast<std::uint32_t>(core.clock.paused) << 8) |
        (static_cast<std::uint32_t>(core.map_ready) << 9) |
        (static_cast<std::uint32_t>(core.has_played_character) << 10) |
        (static_cast<std::uint32_t>(core.played_character_alive) << 11);
    words[18] = Pair(core.clock.date_raw, clock_flags);
    words[19] = Pair(core.played_character_id, static_cast<std::uint32_t>(core.local_player_id));
    return true;
  }
  static bool Validate(void *context, const void *unit, std::int32_t reference,
      PlayerArmyStateInputWordsV1 &words) noexcept {
    return static_cast<StateInput *>(context)->Capture(unit, reference, words);
  }
};

bool ReadImpl(const ArmyBaseBindingsV1 &bindings, const CoreSnapshotPrefix &expected,
    ArmyBaseObservationV1 &out, ArmyBaseReadAccessV1 access) {
  out = {};
  if (!bindings.exact_build_admitted || !bindings.player_armies.exact_build_admitted)
    return Fail(out, "unsupported_build");
  if (bindings.native_army_registry_slot == nullptr || bindings.no_army_fallback_slot == nullptr ||
      bindings.native_army_registry_vtable == 0 || bindings.native_army_manager_vtable == 0 ||
      bindings.native_army_vtable == 0) return Fail(out, "army_base_state_binding_unavailable");
  StateInput input{bindings, expected, access};
  PlayerArmiesObservationV1 internal{};
  const bool read = ReadPlayerArmiesV1(bindings.player_armies, expected, internal,
      {access.context, access.copy, &input, StateInput::Validate});
  out.native_state_calls_attempted = internal.native_state_calls_attempted;
  if (!read) return Fail(out, internal.unavailable_reason == "player_armies_native_state_input_unavailable"
      ? input.reason : internal.unavailable_reason);
  if (!internal.available || !internal.same_frame_ready || !internal.collection_complete ||
      !internal.player_armies) return Fail(out, "army_base_unit_collection_unavailable");
  std::vector<xar::game::ArmySnapshot> armies;
  armies.reserve(internal.player_armies->size());
  for (const auto &source : *internal.player_armies) {
    if (source.native_army_reference == -1 && source.army_state_code != 1)
      return Fail(out, "army_base_no_army_state_not_regular");
    xar::game::ArmySnapshot row{};
    row.army_id = source.army_id; row.owner_character_id = source.owner_character_id;
    row.has_current_province = source.current_province_id.has_value();
    if (source.current_province_id) row.current_province_id = *source.current_province_id;
    row.route_province_ids = source.route_province_ids;
    row.route_source_count = source.route_source_count;
    row.route_read_status = source.route_read_status == PlayerArmyRouteReadStatusV1::complete_empty
        ? xar::game::ArmyRouteReadStatus::complete_empty : xar::game::ArmyRouteReadStatus::complete_nonempty;
    row.move_target_observable = source.move_target_province_id.has_value();
    if (source.move_target_province_id) row.move_target_province_id = *source.move_target_province_id;
    row.army_state_code = source.army_state_code; row.army_state = source.army_state;
    row.in_combat = source.in_combat; row.retreating = source.retreating;
    row.controllable = source.controllable;
    // Three siege sidecars are optional in the actual base contract; all
    // remain absent. Strength is not a field of game::ArmySnapshot.
    armies.push_back(std::move(row));
  }
  out.available = out.same_frame_ready = out.collection_complete = out.army_base_qualified = true;
  out.frame = internal.frame; out.player_armies = std::move(armies);
  out.unit_slots_scanned = internal.unit_slots_scanned; out.live_unit_rows = internal.live_unit_rows;
  out.unavailable_reason = {}; return true;
}
} // namespace

ArmyBaseBindingsV1 BindArmyBaseImageV1(std::uintptr_t base, std::string_view sha) noexcept {
  ArmyBaseBindingsV1 out{};
  out.player_armies = BindPlayerArmiesImageV1(base, sha);
  if (!out.player_armies.exact_build_admitted) return {};
  out.native_army_registry_slot = reinterpret_cast<void **>(base + kArmyBaseNativeRegistryRvaV1);
  out.no_army_fallback_slot = reinterpret_cast<void **>(base + kArmyBaseNoArmyFallbackRvaV1);
  out.native_army_registry_vtable = base + kArmyBaseNativeRegistryVtableRvaV1;
  out.native_army_manager_vtable = base + kArmyBaseManagerVtableRvaV1;
  out.native_army_vtable = base + kArmyBaseNativeArmyVtableRvaV1;
  out.exact_build_admitted = true; return out;
}
bool ReadArmyBaseV1(const ArmyBaseBindingsV1 &bindings, const CoreSnapshotPrefix &expected,
    ArmyBaseObservationV1 &out, ArmyBaseReadAccessV1 access) noexcept {
  try { return ReadImpl(bindings, expected, out, access); }
  catch (...) { return Fail(out, "army_base_allocation_or_internal_error"); }
}
} // namespace xar::ck3_1210
