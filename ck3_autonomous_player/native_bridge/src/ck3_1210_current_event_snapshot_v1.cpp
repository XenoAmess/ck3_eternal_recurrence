#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include "xar_bridge/ck3_1210_current_event_snapshot_v1.hpp"
#include "xar_bridge/ck3_1210_current_event_hotfix26757580_v1.hpp"
#include <cstring>
#include <limits>
#if defined(_MSC_VER)
#include <windows.h>
#endif
namespace xar::ck3_1210 {
namespace {
template <class T> bool Load(const void *object, std::size_t offset, T &value) noexcept {
  if (!object) return false;
  const auto address = reinterpret_cast<std::uintptr_t>(object);
  constexpr auto max = (std::numeric_limits<std::uintptr_t>::max)();
  if (offset > max - address || sizeof(T) - 1 > max - (address + offset)) return false;
  std::memcpy(&value, reinterpret_cast<const void *>(address + offset), sizeof(T)); return true;
}
bool SameCore(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id && a.played_character_alive == b.played_character_alive;
}
bool Fail(CurrentEventSnapshotObservationV1 &out, std::string_view reason) noexcept {
  out = {}; out.unavailable_reason = reason; return false;
}
struct Roots {
  void *state = nullptr, *jomini = nullptr, *characters = nullptr, *data = nullptr, *players = nullptr;
  void *manager = nullptr, *queue = nullptr;
  std::int32_t queued = 0, character_id = -1;
  bool operator==(const Roots &) const = default;
};
bool ReadRoots(const CurrentEventSnapshotBindingsV1 &b, Roots &r,
    std::string_view &reason) noexcept {
  reason = "event_root_unavailable";
  if (!Load(b.core.game_state_slot, 0, r.state) || !r.state ||
      !Load(b.core.jomini_state_slot, 0, r.jomini) || !r.jomini ||
      !Load(b.core.character_storage_slot, 0, r.characters) || !r.characters ||
      !Load(r.state, 0xA0, r.data) || !r.data ||
      !Load(r.jomini, 0x18, r.players) || !r.players ||
      !Load(b.selector_character_id_slot, 0, r.character_id)) return false;
  const auto address = reinterpret_cast<std::uintptr_t>(r.data);
  if (address > (std::numeric_limits<std::uintptr_t>::max)() - kCurrentEventManagerOffsetV1) return false;
  r.manager = reinterpret_cast<void *>(address + kCurrentEventManagerOffsetV1);
  if (!Load(r.manager, kCurrentEventQueuePointerOffsetV1, r.queue) ||
      !Load(r.manager, kCurrentEventQueueCountOffsetV1, r.queued)) return false;
  if (r.queued < 0) { reason = "event_queue_header_invalid"; return false; }
  if (static_cast<std::size_t>(r.queued) > kCurrentEventMaxQueuedV1) {
    reason = "event_queue_bound"; return false;
  }
  if (r.queued > 0 && !r.queue) { reason = "event_queue_header_invalid"; return false; }
  return true;
}
bool ClockMatches(const Roots &r, const CoreSnapshotPrefix &f) noexcept {
  std::int32_t date = 0, speed = 0, local = -1; std::uint8_t paused = 0;
  return Load(r.state, 8, date) && Load(r.state, 0x70, speed) && Load(r.jomini, 0x20, paused) &&
      Load(r.players, kPlayersLocalPlayerIdOffset, local) && local == f.local_player_id &&
      date == f.clock.date_raw && speed >= 0 && speed <= 4 && speed + 1 == f.clock.speed &&
      (paused != 0) == f.clock.paused;
}
struct Actor {
  void *storage = nullptr, *slots = nullptr, *object = nullptr, *death = nullptr;
  std::int32_t capacity = 0, id = -1; std::uint32_t type = 0;
  bool operator==(const Actor &) const = default;
};
bool ReadActor(const CoreBindings &core, const CoreSnapshotPrefix &f, Actor &a) noexcept {
  if (!Load(core.character_storage_slot, 0, a.storage) || !a.storage ||
      !Load(a.storage, 0x20, a.slots) || !a.slots || !Load(a.storage, 0x2C, a.capacity) || a.capacity <= 0)
    return false;
  const auto index = static_cast<std::uint32_t>(f.played_character_id) & 0xFFFFFFU;
  return index < static_cast<std::uint32_t>(a.capacity) &&
      Load(a.slots, std::size_t{index} * 0x10 + 8, a.object) && a.object &&
      Load(a.object, 0x18, a.id) && Load(a.object, 0x1C, a.type) && Load(a.object, 0x1D0, a.death) &&
      a.id == f.played_character_id && a.id != -1 && a.type == 0x43686172U && !a.death;
}
using Queue = std::array<void *, kCurrentEventMaxQueuedV1>;
bool ReadQueue(const Roots &r, Queue &queue) noexcept {
  for (std::size_t i = 0; i < static_cast<std::size_t>(r.queued); ++i)
    if (!Load(r.queue, i * sizeof(void *), queue[i]) || !queue[i]) return false;
  return true;
}
bool Owned(const Roots &r, const Queue &queue, void *event) noexcept {
  if (!event) return true;
  for (std::size_t i = 0; i < static_cast<std::size_t>(r.queued); ++i)
    if (queue[i] == event) return true;
  return false;
}
struct Event {
  void *object = nullptr, *definition = nullptr, *options = nullptr;
  std::uintptr_t definition_vtable = 0;
  std::int32_t character_id = -1, instance_id = -1, capacity = 0, count = 0;
  std::array<void *, kCurrentEventMaxAuthoredV1> authored{};
  bool operator==(const Event &) const = default;
};
bool ReadEvent(const CurrentEventSnapshotBindingsV1 &b, const CoreSnapshotPrefix &f,
    void *object, Event &e, std::string_view &reason) noexcept {
  e.object = object; if (!object) return true;
  reason = "event_prefix_unreadable";
  if (!Load(object, 0x1B8, e.definition) || !Load(object, 0x1C0, e.character_id) ||
      !Load(object, 0x1C4, e.instance_id)) return false;
  if (e.character_id != f.played_character_id) { reason = "event_character_mismatch"; return false; }
  if (e.instance_id <= 0) { reason = "event_instance_invalid"; return false; }
  if (!e.definition) { reason = "event_definition_unavailable"; return false; }
  reason = "event_definition_unreadable";
  if (!Load(e.definition, 0, e.definition_vtable) || !Load(e.definition, 0x138, e.options) ||
      !Load(e.definition, 0x140, e.capacity) || !Load(e.definition, 0x144, e.count)) return false;
  if (e.definition_vtable != b.definition_vtable) { reason = "event_definition_type_mismatch"; return false; }
  if (e.capacity < 0 || e.count < 0 || e.count > e.capacity || (e.capacity > 0 && !e.options)) {
    reason = "event_options_header_invalid"; return false;
  }
  if (static_cast<std::size_t>(e.capacity) > kCurrentEventMaxAuthoredV1) {
    reason = "event_options_bound"; return false;
  }
  for (std::size_t i = 0; i < static_cast<std::size_t>(e.count); ++i)
    if (!Load(e.options, i * sizeof(void *), e.authored[i]) || !e.authored[i]) {
      reason = "event_authored_pointer_invalid"; return false;
    }
  return true;
}
bool ReadImpl(const CurrentEventSnapshotBindingsV1 &b, const CoreSnapshotPrefix &expected,
    CurrentEventSnapshotObservationV1 &out) noexcept {
  out = {};
  if (!b.exact_build_admitted || !b.core.enabled) return Fail(out, "unsupported_build");
  if (!b.core.game_state_slot || !b.core.jomini_state_slot || !b.core.character_storage_slot ||
      !b.core.get_local_player) return Fail(out, "core_binding_unavailable");
  if (!b.get_current_event || !b.selector_character_id_slot || !b.definition_vtable)
    return Fail(out, "event_binding_unavailable");
  if (!expected.clock.paused) return Fail(out, "requires_paused");
  if (!expected.map_ready) return Fail(out, "map_not_ready");
  if (expected.local_player_id < 0 || !expected.has_played_character || expected.played_character_id == -1)
    return Fail(out, "player_identity_unavailable");
  if (!expected.played_character_alive) return Fail(out, "player_not_alive");
  Roots roots{}; std::string_view reason;
  if (!ReadRoots(b, roots, reason)) return Fail(out, reason);
  if (roots.character_id != expected.played_character_id) return Fail(out, "selector_character_mismatch");
  CoreSnapshotPrefix before{};
  if (!ReadCoreSnapshot(b.core, before)) return Fail(out, "core_read_failed");
  if (!SameCore(before, expected) || !ClockMatches(roots, expected)) return Fail(out, "core_frame_changed");
  Actor actor{};
  if (!ReadActor(b.core, expected, actor)) return Fail(out, "player_identity_unavailable");
  Queue queue{};
  if (!ReadQueue(roots, queue)) return Fail(out, "event_queue_read_failed");
  // This first hotfix lane admits the actual empty queue only; selector
  // type2/Jomini virtual transitive branches remain separately unqualified.
  if (IsHotfix(b.core.image_build) && roots.queued!=0)
    return Fail(out,"hotfix_nonempty_event_selector_unqualified");
  Event first{};
  const auto first_pointer = b.get_current_event(roots.manager);
  if (!Owned(roots, queue, first_pointer)) return Fail(out, "current_event_not_owned");
  if (!ReadEvent(b, expected, first_pointer, first, reason)) return Fail(out, reason);

  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(b.core, after)) return Fail(out, "core_read_failed");
  if (!SameCore(before, after) || !SameCore(after, expected)) return Fail(out, "core_frame_changed");
  Roots confirmed_roots{};
  if (!ReadRoots(b, confirmed_roots, reason) || !(confirmed_roots == roots))
    return Fail(out, "event_root_changed");
  Actor confirmed_actor{};
  if (!ReadActor(b.core, expected, confirmed_actor) || !(confirmed_actor == actor))
    return Fail(out, "player_identity_changed");
  Queue confirmed_queue{};
  if (!ReadQueue(confirmed_roots, confirmed_queue) || confirmed_queue != queue)
    return Fail(out, "event_queue_changed");
  Event second{};
  const auto second_pointer = b.get_current_event(roots.manager);
  if (!Owned(roots, queue, second_pointer)) return Fail(out, "current_event_not_owned");
  if (!ReadEvent(b, expected, second_pointer, second, reason)) return Fail(out, reason);
  if (!(first == second)) return Fail(out, "current_event_changed");
  CoreSnapshotPrefix final{};
  if (!ReadCoreSnapshot(b.core, final)) return Fail(out, "core_read_failed");
  if (!SameCore(final, after) || !SameCore(final, expected)) return Fail(out, "core_frame_changed");
  Event tail_event{};
  if (!ReadEvent(b, expected, second.object, tail_event, reason)) return Fail(out, reason);
  if (!(first == tail_event)) return Fail(out, "current_event_changed");
  Roots tail_roots{}; Actor tail_actor{}; Queue tail_queue{};
  if (!ReadRoots(b, tail_roots, reason) || !(tail_roots == roots)) return Fail(out, "event_root_changed");
  if (!ReadActor(b.core, expected, tail_actor) || !(tail_actor == actor))
    return Fail(out, "player_identity_changed");
  if (!ReadQueue(tail_roots, tail_queue) || tail_queue != queue) return Fail(out, "event_queue_changed");
  if (!ClockMatches(tail_roots, expected)) return Fail(out, "core_frame_changed");
  out.available = true; out.found = first.object != nullptr; out.same_frame_ready = true;
  out.frame = final;
  if (out.found) { out.active_event_instance_id = first.instance_id; out.active_event_option_count = first.count; }
  out.unavailable_reason = {};
  return true;
}
} // namespace

CurrentEventSnapshotBindingsV1 BindCurrentEventSnapshotImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept {
  CurrentEventSnapshotBindingsV1 b{};
  if (!image_base || ImageBuildForSha(executable_sha256)==ImageBuildV1::unknown ||
      image_base > (std::numeric_limits<std::uintptr_t>::max)() - kJominiStateSlotRva - (sizeof(void *) - 1))
    return b;
  b.core = BindCoreImage(image_base, executable_sha256);
  if (!b.core.enabled) return {};
  b.exact_build_admitted = true;
  b.get_current_event = reinterpret_cast<CurrentEventSelectorV1>(image_base + ImageRva(b.core.image_build,kCurrentEventSelectorRvaV1,bb3_current_event_profile36::kCurrentEventSelectorRvaV1));
  b.selector_character_id_slot = reinterpret_cast<std::int32_t *>(image_base + ImageRva(b.core.image_build,kCurrentEventCharacterSlotRvaV1,bb3_current_event_profile36::kCurrentEventCharacterSlotRvaV1));
  b.definition_vtable = image_base + ImageRva(b.core.image_build,kCurrentEventDefinitionVtableRvaV1,bb3_current_event_profile36::kCurrentEventDefinitionVtableRvaV1);
  return b;
}
bool ReadCurrentEventSnapshotV1(const CurrentEventSnapshotBindingsV1 &b,
    const CoreSnapshotPrefix &expected, CurrentEventSnapshotObservationV1 &out) noexcept {
#if defined(_MSC_VER)
  __try { return ReadImpl(b, expected, out); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return Fail(out, "memory_read_failed"); }
#else
  return ReadImpl(b, expected, out);
#endif
}
} // namespace xar::ck3_1210
