#include "xar_bridge/ck3_1210_actor_foundation_v1.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <utility>

#if defined(_MSC_VER)
#include <windows.h>
#endif

// FOUNDATION-ABI-CANDIDATES01.json: new-image names/callees and spouse RTTI
// independently prove Character+1B0 living (+130/+110/+2F8), +1A8 family
// (+10/+14 scalars, +20 pointer/+28 capacity/+2C count, int32 stride4).
// FINANCE-ABI-CANDIDATES01.json separately proves personal gold living+100.
// Only version-independent checked read arithmetic is reused, no old binder.
namespace xar::ck3_1210 {
namespace {
constexpr std::size_t kType = 0x1C, kLiving = 0x1B0, kFamily = 0x1A8;
constexpr std::uint32_t kCharacterType = 0x43686172U;

bool Copy(const void *source, void *target, std::size_t size) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(target, source, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

template <class T>
bool Read(const void *base, std::size_t offset, T &output) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(base);
  const auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
  return address != 0 && offset <= maximum - address &&
      sizeof(T) - 1 <= maximum - (address + offset) &&
      Copy(reinterpret_cast<const void *>(address + offset), &output, sizeof(T));
}

bool Core(const CoreBindings &bindings, CoreSnapshotPrefix &output) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return ReadCoreSnapshot(bindings, output);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { output = {}; return false; }
#endif
}

void *Resolve(const CoreBindings &bindings, std::int32_t id) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return ResolveCoreCharacter(bindings, id);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
#endif
}

bool SamePrefix(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}

bool Fail(ActorFoundationObservationV1 &output, std::string_view reason) noexcept {
  output = {};
  output.resources_unavailable_reason = reason;
  output.relationships_unavailable_reason = reason;
  output.unavailable_reason = reason;
  return false;
}

struct Actor {
  std::int32_t id = -1;
  std::uint32_t type = 0;
  void *death = nullptr;
  void *living = nullptr;
  void *family = nullptr;
  friend bool operator==(const Actor &, const Actor &) = default;
};

bool ActorHeader(const void *actor, Actor &output) noexcept {
  return Read(actor, kCharacterFullIdOffset, output.id) &&
      Read(actor, kType, output.type) &&
      Read(actor, kCharacterDeathDataOffset, output.death) &&
      Read(actor, kLiving, output.living) && Read(actor, kFamily, output.family);
}

bool Valid(const Actor &actor, const CoreSnapshotPrefix &expected) noexcept {
  return actor.id == expected.played_character_id && actor.type == kCharacterType &&
      actor.death == nullptr && expected.played_character_alive;
}

struct Resources {
  std::int64_t gold = 0, prestige = 0, piety = 0;
  std::int32_t stress = 0;
  friend bool operator==(const Resources &, const Resources &) = default;
};

bool ResourceValues(const Actor &actor, Resources &values) noexcept {
  // Actual native getters return zero for null living. Read failure differs.
  return actor.living == nullptr ||
      (Read(actor.living, 0x100, values.gold) &&
       Read(actor.living, 0x130, values.prestige) &&
       Read(actor.living, 0x110, values.piety) &&
       Read(actor.living, 0x2F8, values.stress));
}

struct Family {
  std::int32_t betrothed = -1, primary = -1, capacity = 0, count = 0;
  const std::int32_t *ids = nullptr;
  void *betrothed_peer = nullptr, *primary_peer = nullptr;
  std::array<std::int32_t, kActorFoundationSpouseObservationLimitV1> spouses{};
  std::array<void *, kActorFoundationSpouseObservationLimitV1> peers{};
  friend bool operator==(const Family &, const Family &) = default;
};

bool Peer(const CoreBindings &core, std::int32_t id, void *&peer) noexcept {
  if (id == -1) return false;
  peer = Resolve(core, id);
  std::int32_t actual = -1;
  std::uint32_t type = 0;
  return peer != nullptr && Read(peer, kCharacterFullIdOffset, actual) &&
      actual == id && Read(peer, kType, type) && type == kCharacterType;
}

bool FamilyValues(const CoreBindings &core, const Actor &actor, Family &family,
    std::string_view &reason) noexcept {
  reason = "family_read_failed";
  if (actor.family == nullptr) { reason = {}; return true; }
  if (!Read(actor.family, 0x10, family.betrothed) ||
      !Read(actor.family, 0x14, family.primary) ||
      !Read(actor.family, 0x20, family.ids) ||
      !Read(actor.family, 0x28, family.capacity) ||
      !Read(actor.family, 0x2C, family.count)) return false;
  reason = "family_header_invalid";
  if (family.capacity < 0 || family.count < 0 || family.count > family.capacity ||
      (family.capacity > 0 && family.ids == nullptr)) return false;
  reason = "spouse_observation_scope_exceeded";
  if (static_cast<std::size_t>(family.count) >
      kActorFoundationSpouseObservationLimitV1) return false;
  reason = "family_peer_unavailable";
  if (family.betrothed != -1 && !Peer(core, family.betrothed, family.betrothed_peer))
    return false;
  if (family.primary != -1 && !Peer(core, family.primary, family.primary_peer))
    return false;
  for (std::int32_t i = 0; i < family.count; ++i) {
    const auto index = static_cast<std::size_t>(i);
    reason = "family_read_failed";
    if (!Read(family.ids, index * sizeof(std::int32_t), family.spouses[index]))
      return false;
    reason = "family_peer_unavailable";
    if (!Peer(core, family.spouses[index], family.peers[index])) return false;
  }
  // Do not filter dead peers, drop unresolved IDs, reorder or infer primary
  // membership. This internal result preserves the proven raw vector role.
  reason = {};
  return true;
}

bool ReadImpl(const ActorFoundationBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, ActorFoundationObservationV1 &output) {
  output = {};
  const auto &core = bindings.core;
  if (!bindings.exact_build_admitted || !core.enabled)
    return Fail(output, "unsupported_build");
  if (core.game_state_slot == nullptr || core.jomini_state_slot == nullptr ||
      core.character_storage_slot == nullptr || core.get_local_player == nullptr)
    return Fail(output, "core_binding_unavailable");
  if (!expected.clock.paused) return Fail(output, "requires_paused");
  if (!expected.map_ready) return Fail(output, "map_not_ready");
  if (expected.local_player_id < 0 || !expected.has_played_character ||
      expected.played_character_id == -1)
    return Fail(output, "player_identity_unavailable");
  if (!expected.played_character_alive) return Fail(output, "player_not_alive");
  CoreSnapshotPrefix before{}, after{};
  if (!Core(core, before)) return Fail(output, "core_read_failed");
  if (!SamePrefix(before, expected)) return Fail(output, "core_frame_changed");
  const auto actor = Resolve(core, expected.played_character_id);
  Actor first{}, second{};
  if (actor == nullptr || !ActorHeader(actor, first) || !Valid(first, expected))
    return Fail(output, "player_identity_unavailable");
  Resources resources_first{}, resources_second{};
  Family family_first{}, family_second{};
  std::string_view family_first_reason{}, family_second_reason{};
  const bool first_resources = ResourceValues(first, resources_first);
  const bool first_family = FamilyValues(core, first, family_first, family_first_reason);
  if (!Core(core, after)) return Fail(output, "core_read_failed");
  if (!SamePrefix(before, after) || !SamePrefix(after, expected))
    return Fail(output, "core_frame_changed");
  const auto confirmed = Resolve(core, expected.played_character_id);
  if (confirmed == nullptr || confirmed != actor || !ActorHeader(confirmed, second) ||
      !Valid(second, expected) || first != second)
    return Fail(output, "player_identity_changed");
  const bool second_resources = ResourceValues(second, resources_second);
  const bool second_family = FamilyValues(core, second, family_second, family_second_reason);
  output.frame = after;
  output.same_frame_ready = true;
  output.resources_ready = first_resources && second_resources &&
      resources_first == resources_second;
  output.relationships_ready = first_family && second_family &&
      family_first == family_second;
  if (output.resources_ready) {
    output.gold_raw = resources_first.gold;
    output.prestige_raw = resources_first.prestige;
    output.piety_raw = resources_first.piety;
    output.stress_points = resources_first.stress;
    output.resources_unavailable_reason = {};
  } else {
    output.resources_unavailable_reason = first_resources && second_resources ?
        "resources_changed" : "resource_read_failed";
  }
  if (output.relationships_ready) {
    ActorFoundationRelationshipsV1 relations{};
    relations.betrothed_character_id = family_first.betrothed;
    relations.primary_spouse_character_id = family_first.primary;
    for (std::int32_t i = 0; i < family_first.count; ++i)
      relations.spouse_character_ids.push_back(
          family_first.spouses[static_cast<std::size_t>(i)]);
    output.relationships = std::move(relations);
    output.relationships_unavailable_reason = {};
  } else {
    output.relationships_unavailable_reason = !first_family ? family_first_reason :
        !second_family ? family_second_reason : "relationships_changed";
  }
  output.available = output.resources_ready || output.relationships_ready;
  output.unavailable_reason = output.resources_ready && output.relationships_ready ?
      std::string_view{} : output.available ? "actor_foundation_partial" :
      "actor_foundation_unavailable";
  return output.available;
}
} // namespace

ActorFoundationBindingsV1 BindActorFoundationImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept {
  ActorFoundationBindingsV1 result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256 ||
      image_base > (std::numeric_limits<std::uintptr_t>::max)() -
          kJominiStateSlotRva - (sizeof(void *) - 1)) return result;
  result.core = BindCoreImage(image_base, executable_sha256);
  result.exact_build_admitted = result.core.enabled;
  return result;
}

bool ReadActorFoundationV1(const ActorFoundationBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, ActorFoundationObservationV1 &output) noexcept {
  try {
    return ReadImpl(bindings, expected, output);
  } catch (...) {
    return Fail(output, "allocation_or_internal_error");
  }
}

} // namespace xar::ck3_1210
