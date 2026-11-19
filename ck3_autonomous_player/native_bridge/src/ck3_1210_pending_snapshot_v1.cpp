#include "xar_bridge/ck3_1210_pending_snapshot_v1.hpp"
#include <array>
#include <cstring>
#include <limits>
#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_1210 {
namespace {
template <class T>
bool Load(const void *object, std::size_t offset, T &value) noexcept {
  if (object == nullptr) return false;
  const auto address = reinterpret_cast<std::uintptr_t>(object);
  constexpr auto max = (std::numeric_limits<std::uintptr_t>::max)();
  if (offset > max - address || sizeof(T) - 1 > max - (address + offset))
    return false;
  std::memcpy(&value, reinterpret_cast<const void *>(address + offset), sizeof(T));
  return true;
}
bool SameCore(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
bool Fail(PendingSnapshotObservationV1 &output, std::string_view reason) noexcept {
  output = {};
  output.unavailable_reason = reason;
  return false;
}
struct Roots {
  void *state = nullptr, *jomini = nullptr, *characters = nullptr;
  void *data = nullptr, *players = nullptr;
  bool operator==(const Roots &) const = default;
};
bool ReadRoots(const CoreBindings &core, Roots &r) noexcept {
  return Load(core.game_state_slot, 0, r.state) && r.state != nullptr &&
      Load(core.jomini_state_slot, 0, r.jomini) && r.jomini != nullptr &&
      Load(core.character_storage_slot, 0, r.characters) && r.characters != nullptr &&
      Load(r.state, kGameStateDataOffset, r.data) && r.data != nullptr &&
      Load(r.jomini, kJominiPlayersOffset, r.players) && r.players != nullptr;
}
bool ClockMatches(const Roots &r, const CoreSnapshotPrefix &frame) noexcept {
  std::int32_t date = 0, speed = 0;
  std::uint8_t paused = 0;
  return Load(r.state, kGameStateDateOffset, date) &&
      Load(r.state, kGameStateSpeedOffset, speed) &&
      Load(r.jomini, kJominiPausedOffset, paused) &&
      date == frame.clock.date_raw && speed >= 0 && speed <= 4 &&
      speed + 1 == frame.clock.speed && (paused != 0) == frame.clock.paused;
}
struct Actor {
  void *storage = nullptr, *slots = nullptr, *object = nullptr, *death = nullptr;
  std::int32_t capacity = 0, id = -1;
  std::uint32_t type = 0;
  bool operator==(const Actor &) const = default;
};
bool ReadActor(const CoreBindings &core, const CoreSnapshotPrefix &frame,
    Actor &a) noexcept {
  if (!Load(core.character_storage_slot, 0, a.storage) || a.storage == nullptr ||
      !Load(a.storage, kCharacterStorageSlotsOffset, a.slots) || a.slots == nullptr ||
      !Load(a.storage, kCharacterStorageCapacityOffset, a.capacity) || a.capacity <= 0)
    return false;
  const auto index = static_cast<std::uint32_t>(frame.played_character_id) & 0xFFFFFFU;
  if (index >= static_cast<std::uint32_t>(a.capacity) ||
      !Load(a.slots, std::size_t{index} * 0x10 + 8, a.object) || a.object == nullptr)
    return false;
  return Load(a.object, kCharacterFullIdOffset, a.id) &&
      Load(a.object, 0x1C, a.type) && Load(a.object, kCharacterDeathDataOffset, a.death) &&
      a.id != -1 && a.id == frame.played_character_id && a.type == 0x43686172U &&
      a.death == nullptr && frame.played_character_alive;
}
struct Header {
  void *object = nullptr, *slots = nullptr;
  std::uintptr_t vtable = 0;
  std::int32_t capacity = 0;
  std::uintptr_t manager_vtable = 0;
  void *manager_database = nullptr;
  bool operator==(const Header &) const = default;
};
bool ReadHeader(const PendingSnapshotBindingsV1 &b, const Roots &roots, Header &h,
    std::string_view &reason) noexcept {
  reason = "pending_header_unreadable";
  if (!Load(b.pending_storage_slot, 0, h.object) || h.object == nullptr) return false;
  if (!Load(h.object, 0, h.vtable) || !Load(h.object, 0x20, h.slots) ||
      !Load(h.object, 0x2C, h.capacity)) return false;
  if (h.vtable != b.database_vtable) { reason = "pending_database_type_mismatch"; return false; }
  if (b.owner_manager_vtable) {
    const auto offset = b.owner_manager_data_offset;
    if (offset > (std::numeric_limits<std::size_t>::max)() - 0x50 ||
        !Load(roots.data, offset, h.manager_vtable) ||
        h.manager_vtable != b.owner_manager_vtable) {
      reason = "pending_manager_type_mismatch"; return false;
    }
    if (!Load(roots.data, offset + 0x50, h.manager_database) ||
        h.manager_database != h.object) {
      reason = "pending_manager_registry_mismatch"; return false;
    }
  }
  if (h.capacity < 0) { reason = "pending_capacity_invalid"; return false; }
  if (static_cast<std::size_t>(h.capacity) > kPendingSnapshotMaxSlotsV1) {
    reason = "pending_capacity_bound"; return false;
  }
  if (h.capacity > 0 && h.slots == nullptr) { reason = "pending_slots_unavailable"; return false; }
  return true;
}
struct Sample {
  void *object = nullptr;
  std::uintptr_t vtable = 0;
  std::int32_t id = -1, kind = 0, actor = -1, recipient = -1, alternate = -1;
  std::uint32_t type = 0;
  std::uint8_t notification = 0;
  bool operator==(const Sample &) const = default;
};
bool ReadSample(const Header &h, std::size_t index, Sample &s) noexcept {
  if (!Load(h.slots, index * 0x10 + 8, s.object)) return false;
  if (s.object == nullptr) return true;
  return Load(s.object, 0, s.vtable) && Load(s.object, 0x10, s.id) &&
      Load(s.object, 0x14, s.type) && Load(s.object, 0x300, s.actor) &&
      Load(s.object, 0x304, s.recipient) && Load(s.object, 0x310, s.alternate) &&
      Load(s.object, 0x5D0, s.kind) && Load(s.object, 0x5D6, s.notification);
}
bool ReadImpl(const PendingSnapshotBindingsV1 &b, const CoreSnapshotPrefix &expected,
    PendingSnapshotObservationV1 &output) noexcept {
  output = {};
  if (!b.exact_build_admitted || !b.core.enabled) return Fail(output, "unsupported_build");
  if (!b.core.game_state_slot || !b.core.jomini_state_slot ||
      !b.core.character_storage_slot || !b.core.get_local_player)
    return Fail(output, "core_binding_unavailable");
  if (!b.pending_storage_slot || !b.is_pending_for_character || !b.validate_reply ||
      !b.database_vtable || !b.pending_vtable || !b.reply_primary_vtable ||
      !b.reply_secondary_vtable) return Fail(output, "pending_binding_unavailable");
  if ((b.owner_manager_vtable == 0) != (b.owner_manager_data_offset == 0))
    return Fail(output, "pending_binding_unavailable");
  if (!expected.clock.paused) return Fail(output, "requires_paused");
  if (!expected.map_ready) return Fail(output, "map_not_ready");
  if (expected.local_player_id < 0 || !expected.has_played_character ||
      expected.played_character_id == -1) return Fail(output, "player_identity_unavailable");
  if (!expected.played_character_alive) return Fail(output, "player_not_alive");

  Roots roots{};
  if (!ReadRoots(b.core, roots)) return Fail(output, "core_root_unavailable");
  CoreSnapshotPrefix before{};
  if (!ReadCoreSnapshot(b.core, before)) return Fail(output, "core_read_failed");
  if (!SameCore(before, expected) || !ClockMatches(roots, expected))
    return Fail(output, "core_frame_changed");
  Actor actor{};
  if (!ReadActor(b.core, expected, actor)) return Fail(output, "player_identity_unavailable");
  Header header{};
  std::string_view reason;
  if (!ReadHeader(b, roots, header, reason)) return Fail(output, reason);

  // Trivial, bounded stack storage: no allocation or SEH-unwind heap ownership.
  std::array<Sample, kPendingSnapshotMaxSlotsV1> first{};
  std::uint32_t occupied = 0;
  bool found = false;
  Sample selected{};
  for (std::size_t i = 0; i < static_cast<std::size_t>(header.capacity); ++i) {
    auto &sample = first[i];
    if (!ReadSample(header, i, sample)) return Fail(output, "pending_read_failed");
    if (sample.object == nullptr) continue;
    ++occupied;
    if (sample.vtable != b.pending_vtable || sample.type != kPendingSnapshotTypeV1 ||
        sample.id == -1 || (static_cast<std::uint32_t>(sample.id) & 0xFFFFFFU) != i)
      return Fail(output, "pending_identity_invalid");
    if (sample.kind < 0 || sample.kind > 3) return Fail(output, "pending_kind_unsupported");
    // Native kind3 exists, but its IsPendingForCharacter branch returns false.
    if (sample.kind == 3) continue;
    const auto recipient = sample.kind == 1 ? sample.alternate : sample.recipient;
    if (recipient != expected.played_character_id ||
        !b.is_pending_for_character(sample.object, actor.object)) continue;
    bool eligible = sample.notification != 0;
    if (!eligible) {
      PendingReplyValidationCommandV1 command{};
      command.primary_vtable = b.reply_primary_vtable;
      command.secondary_vtable = b.reply_secondary_vtable;
      command.instance_id = sample.id;
      command.choice = 0;
      eligible = b.validate_reply(&command);
    }
    if (eligible && !found) { selected = sample; found = true; }
  }

  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(b.core, after)) return Fail(output, "core_read_failed");
  if (!SameCore(before, after) || !SameCore(after, expected))
    return Fail(output, "core_frame_changed");
  Roots confirmed_roots{};
  if (!ReadRoots(b.core, confirmed_roots) || !(confirmed_roots == roots))
    return Fail(output, "core_root_changed");
  Actor confirmed_actor{};
  if (!ReadActor(b.core, expected, confirmed_actor) || !(confirmed_actor == actor))
    return Fail(output, "player_identity_changed");
  Header confirmed_header{};
  if (!ReadHeader(b, confirmed_roots, confirmed_header, reason) || !(confirmed_header == header))
    return Fail(output, "pending_header_changed");
  // Includes every null/occupied row, not just the selected interaction. No
  // native callback is invoked during confirmation, so a late callback cannot
  // mutate an already-confirmed row in this pass.
  for (std::size_t i = 0; i < static_cast<std::size_t>(header.capacity); ++i) {
    Sample second{};
    if (!ReadSample(header, i, second)) return Fail(output, "pending_read_failed");
    if (!(second == first[i])) return Fail(output, "pending_changed");
  }
  Header tail_header{};
  Actor tail_actor{};
  Roots tail_roots{};
  if (!ReadHeader(b, roots, tail_header, reason) || !(tail_header == header))
    return Fail(output, "pending_header_changed");
  if (!ReadActor(b.core, expected, tail_actor) || !(tail_actor == actor))
    return Fail(output, "player_identity_changed");
  if (!ReadRoots(b.core, tail_roots) || !(tail_roots == roots))
    return Fail(output, "core_root_changed");
  std::int32_t local_player = -1;
  if (!ClockMatches(tail_roots, expected) ||
      !Load(tail_roots.players, kPlayersLocalPlayerIdOffset, local_player) ||
      local_player != expected.local_player_id) return Fail(output, "core_frame_changed");

  output.available = true;
  output.found = found;
  output.same_frame_ready = true;
  output.frame = after;
  output.slots_scanned = static_cast<std::uint32_t>(header.capacity);
  output.occupied_slots = occupied;
  if (found) {
    output.pending_character_interaction_id = selected.id;
    output.pending_sender_character_id = selected.actor;
    output.pending_auto_accept_notification = selected.notification != 0;
  }
  output.unavailable_reason = {};
  return true;
}
} // namespace

PendingSnapshotBindingsV1 BindPendingSnapshotImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept {
  PendingSnapshotBindingsV1 b{};
  const bool hotfix = executable_sha256 == pending_hotfix26757580::kExecutableSha256;
  const bool historical = executable_sha256 ==
      "2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC";
  const auto slot = hotfix ? pending_hotfix26757580::kStorageSlotRva : kPendingSnapshotStorageSlotRvaV1;
  constexpr auto max = (std::numeric_limits<std::uintptr_t>::max)();
  if (image_base == 0 || (!hotfix && !historical) || image_base > max - slot - (sizeof(void *) - 1))
    return b;
  // Central exact Core selection remains the unique Native owner's dependency.
  b.core = BindCoreImage(image_base, executable_sha256);
  if (!b.core.enabled) return {};
  b.exact_build_admitted = true;
  b.pending_storage_slot = reinterpret_cast<void **>(image_base + slot);
  b.is_pending_for_character = reinterpret_cast<PendingForCharacterV1>(image_base +
      (hotfix ? pending_hotfix26757580::kPredicateRva : kPendingSnapshotPredicateRvaV1));
  b.validate_reply = reinterpret_cast<PendingReplyValidatorV1>(image_base +
      (hotfix ? pending_hotfix26757580::kValidatorRva : kPendingSnapshotValidatorRvaV1));
  b.database_vtable = image_base + (hotfix ? pending_hotfix26757580::kDatabaseVtableRva : kPendingSnapshotDatabaseVtableRvaV1);
  b.pending_vtable = image_base + (hotfix ? pending_hotfix26757580::kObjectVtableRva : kPendingSnapshotObjectVtableRvaV1);
  b.reply_primary_vtable = image_base + (hotfix ? pending_hotfix26757580::kReplyPrimaryRva : kPendingSnapshotReplyPrimaryRvaV1);
  b.reply_secondary_vtable = image_base + (hotfix ? pending_hotfix26757580::kReplySecondaryRva : kPendingSnapshotReplySecondaryRvaV1);
  if (hotfix) {
    b.owner_manager_vtable = image_base + pending_hotfix26757580::kOwnerManagerVtableRva;
    b.owner_manager_data_offset = pending_hotfix26757580::kOwnerManagerDataOffset;
  }
  return b;
}
bool ReadPendingSnapshotV1(const PendingSnapshotBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, PendingSnapshotObservationV1 &output) noexcept {
#if defined(_MSC_VER)
  __try {
    return ReadImpl(bindings, expected, output);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return Fail(output, "memory_read_failed");
  }
#else
  return ReadImpl(bindings, expected, output);
#endif
}
} // namespace xar::ck3_1210
