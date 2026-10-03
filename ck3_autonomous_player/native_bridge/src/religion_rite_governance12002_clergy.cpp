#include "xar_bridge/religion_rite_governance12002_clergy.hpp"

#include <array>
#include <cstring>
#include <sstream>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::ck3_12002::religion::clergy {
namespace {

bool Bytes(const Bindings &b, const void *address, void *out,
           std::size_t size) noexcept {
  if (address == nullptr || out == nullptr) return false;
  if (b.read_memory) return b.read_memory(b.read_context, address, out, size);
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(out, address, size);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
  return true;
}

template <typename T>
bool At(const Bindings &b, const void *object, std::size_t offset,
        T &out) noexcept {
  return object != nullptr && Bytes(b,
      static_cast<const std::byte *>(object) + offset, &out, sizeof(out));
}

bool Snapshot(const Bindings &b, CoreSnapshotPrefix &out) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return ReadCoreSnapshot(b.core, out);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

void *Character(const Bindings &b, std::int32_t id) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return ResolveCoreCharacter(b.core, id);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
#endif
}

bool Exact(const Bindings &b) noexcept {
  if (!b.enabled || b.executable_sha256 != kExecutableSha256 ||
      !b.core.enabled || !b.task_storage_slot || !b.valid_position ||
      !b.valid_character || !b.can_reassign || !b.can_fire || !b.court_owner) return false;
  if (b.offline_fixture) return b.module_base == 0;
  const auto base = b.module_base;
  return base != 0 &&
      reinterpret_cast<std::uintptr_t>(b.task_storage_slot) == base + kTaskStorageRva &&
      reinterpret_cast<std::uintptr_t>(b.valid_position) == base + kValidPositionRva &&
      reinterpret_cast<std::uintptr_t>(b.valid_character) == base + kValidCharacterRva &&
      reinterpret_cast<std::uintptr_t>(b.can_reassign) == base + kCanReassignRva &&
      reinterpret_cast<std::uintptr_t>(b.can_fire) == base + kCanFireRva &&
      reinterpret_cast<std::uintptr_t>(b.court_owner) == base + kCourtOwnerRva;
}

bool Key(const Bindings &b, const void *position,
         std::array<char, 128> &out) noexcept {
  out.fill('\0');
  const auto *key = static_cast<const std::byte *>(position) + kPositionKeyOffset;
  std::uint64_t size = 0, capacity = 0;
  if (!At(b, key, 0x10, size) || !At(b, key, 0x18, capacity) ||
      size == 0 || size >= out.size() || capacity < size) return false;
  const void *text = key;
  if (capacity > 15 && (!At(b, key, 0, text) || !text)) return false;
  if (!Bytes(b, text, out.data(), static_cast<std::size_t>(size))) return false;
  for (std::size_t i = 0; i < size; ++i)
    if (static_cast<unsigned char>(out[i]) < 0x20) return false;
  return true;
}

struct Seat {
  void *task = nullptr;
  void *position = nullptr;
  std::int32_t task_id = -1;
  std::int32_t incumbent = -1;
  bool operator==(const Seat &) const = default;
};

bool ResolveTask(const Bindings &b, std::int32_t id, void *&out) noexcept {
  out = nullptr;
  void *storage = nullptr, *slots = nullptr;
  std::int32_t capacity = 0, identity = -1;
  if (id == -1 || !At(b, b.task_storage_slot, 0, storage) || !storage ||
      !At(b, storage, 0x20, slots) || !slots ||
      !At(b, storage, 0x2C, capacity) || capacity <= 0) return false;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  return index < static_cast<std::uint32_t>(capacity) &&
      At(b, slots, static_cast<std::size_t>(index) * 0x10 + 8, out) && out &&
      At(b, out, kTaskIdentityOffset, identity) && identity == id;
}

bool ChaplainSeat(const Bindings &b, void *owner, std::int32_t owner_id,
                  Seat &out) noexcept {
  out = {};
  void *landed = nullptr, *ids = nullptr;
  std::int32_t count = 0;
  if (!At(b, owner, kLandedOffset, landed)) return false;
  if (!landed) return true;
  if (!At(b, landed, kTaskIdsOffset, ids) ||
      !At(b, landed, kTaskCountOffset, count) || count < 0 || count > 4096 ||
      (count > 0 && !ids)) return false;
  for (std::int32_t i = 0; i < count; ++i) {
    std::int32_t id = -1, task_owner = -1, incumbent = -1;
    void *task = nullptr, *type = nullptr, *position = nullptr;
    std::array<char, 128> key{};
    if (!At(b, ids, static_cast<std::size_t>(i) * 4, id) ||
        !ResolveTask(b, id, task) ||
        !At(b, task, kTaskTypeOffset, type) || !type ||
        !At(b, type, kTypePositionOffset, position) || !position ||
        !Key(b, position, key)) return false;
    if (std::string_view{key.data()} != kPositionKey) continue;
    if (out.task || !At(b, task, kTaskOwnerOffset, task_owner) ||
        task_owner != owner_id ||
        !At(b, task, kTaskIncumbentOffset, incumbent) ||
        (incumbent != -1 && !Character(b, incumbent))) return false;
    out = {task, position, id, incumbent};
  }
  return true;
}

bool Predicates(const Bindings &b, const Seat &seat, std::int32_t owner,
                std::int32_t candidate, bool &position, bool &character,
                bool &reassign) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    position = b.valid_position(seat.position, owner);
    character = b.valid_character(seat.position, candidate);
    reassign = b.can_reassign(seat.task, nullptr);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
  return true;
}

bool CanFire(const Bindings &b, void *owner, const Seat &seat,
             bool &result) noexcept {
  void *incumbent = Character(b, seat.incumbent);
  if (!incumbent) return false;
#if defined(_MSC_VER)
  __try {
#endif
    result = b.can_fire(owner, incumbent, seat.task, 0U, nullptr);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
  return true;
}

bool Context(const Bindings &b, void *owner, void *candidate,
             std::uint32_t &owner_rite, std::uint32_t &candidate_rite,
             std::int32_t &court_owner_id) noexcept {
  void *court_owner = nullptr;
#if defined(_MSC_VER)
  __try {
#endif
    court_owner = b.court_owner(candidate);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
  return At(b, owner, kCharacterRiteOffset, owner_rite) &&
      At(b, candidate, kCharacterRiteOffset, candidate_rite) && court_owner &&
      At(b, court_owner, 0x18, court_owner_id) &&
      Character(b, court_owner_id) == court_owner;
}

bool SameFrame(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}

bool Failed(Observation &out, Failure failure) noexcept {
  out.available = false;
  out.failure = failure;
  out.native_valid_position.reset(); out.native_valid_character.reset();
  out.native_can_reassign.reset(); out.native_can_fire.reset();
  return false;
}

template <typename T>
void Optional(std::ostringstream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}
} // namespace


bool ResolveCurrentClergySeat12002(const Bindings &b, std::int32_t owner_id,
                                 CurrentClergySeat &out) noexcept {
  out = {};
  if (!Exact(b)) return false;
  void *owner = Character(b, owner_id);
  Seat seat{};
  if (!owner || !ChaplainSeat(b, owner, owner_id, seat)) return false;
  out.owner = owner;
  if (!seat.task) return true;
  void *type = nullptr;
  if (!At(b, seat.task, kTaskTypeOffset, type) || !type) return false;
  void *incumbent = seat.incumbent == -1 ? nullptr : Character(b, seat.incumbent);
  if (seat.incumbent != -1 && !incumbent) return false;
  out.task = seat.task; out.type = type; out.position = seat.position;
  out.incumbent = incumbent; out.task_id = seat.task_id;
  out.incumbent_character_id = seat.incumbent;
  return true;
}

Bindings BindClergyAppointmentImage12002(
    std::uintptr_t module_base, std::string_view sha) noexcept {
  Bindings b{};
  if (!module_base || sha != kExecutableSha256) return b;
  b.enabled = true; b.module_base = module_base;
  b.executable_sha256 = kExecutableSha256;
  b.core = BindCoreImage(module_base, sha);
  b.task_storage_slot = reinterpret_cast<void **>(module_base + kTaskStorageRva);
  b.valid_position = reinterpret_cast<PositionPredicate>(module_base + kValidPositionRva);
  b.valid_character = reinterpret_cast<PositionPredicate>(module_base + kValidCharacterRva);
  b.can_reassign = reinterpret_cast<TaskPredicate>(module_base + kCanReassignRva);
  b.can_fire = reinterpret_cast<CanFirePredicate>(module_base + kCanFireRva);
  b.court_owner = reinterpret_cast<CourtOwnerGetter>(module_base + kCourtOwnerRva);
  return b;
}

bool ReadClergyAppointment12002(const Bindings &b, std::uint64_t epoch,
                              std::int32_t candidate_id,
                              Observation &out) noexcept {
  out = {}; out.capture_epoch = epoch; out.candidate_character_id = candidate_id;
  if (!Exact(b)) return Failed(out, Failure::bindings_unavailable);
  if (!b.offline_fixture) {
#if defined(_WIN32)
    if (!b.application_main_thread_id ||
        GetCurrentThreadId() != b.application_main_thread_id)
#endif
      return Failed(out, Failure::owner_thread_required);
  }
  CoreSnapshotPrefix before{}, after{};
  if (!Snapshot(b, before)) return Failed(out, Failure::frame_unavailable);
  if (!before.clock.paused) return Failed(out, Failure::not_paused);
  if (!before.map_ready || !before.has_played_character || !before.played_character_alive)
    return Failed(out, Failure::player_unavailable);
  out.date_raw = before.clock.date_raw; out.owner_character_id = before.played_character_id;
  void *owner = Character(b, out.owner_character_id);
  void *candidate = candidate_id == -1 ? nullptr : Character(b, candidate_id);
  if (!owner) return Failed(out, Failure::player_unavailable);
  if (!candidate) return Failed(out, Failure::candidate_unavailable);
  Seat seat{};
  if (!ChaplainSeat(b, owner, out.owner_character_id, seat))
    return Failed(out, Failure::task_unavailable);
  std::uint32_t owner_rite = 0, candidate_rite = 0;
  std::int32_t court_owner = -1;
  if (!Context(b, owner, candidate, owner_rite, candidate_rite, court_owner))
    return Failed(out, Failure::candidate_context_unavailable);
  out.candidate_court_owner_id = court_owner;
  out.candidate_matches_owner_context = court_owner == out.owner_character_id;
  if (owner_rite != 0xFFFFFFFFU) out.owner_rite_id = owner_rite;
  if (candidate_rite != 0xFFFFFFFFU) out.candidate_rite_id = candidate_rite;
  if (seat.task) {
    out.position_present = true; out.active_task_id = seat.task_id;
    if (seat.incumbent != -1) out.incumbent_character_id = seat.incumbent;
    out.candidate_is_incumbent = seat.incumbent == candidate_id;
    bool position = false, character = false, reassign = false;
    if (!Predicates(b, seat, out.owner_character_id, candidate_id, position, character, reassign))
      return Failed(out, Failure::native_predicate_unavailable);
    out.native_valid_position = position; out.native_valid_character = character;
    out.native_can_reassign = reassign;
    if (seat.incumbent != -1) {
      bool fire = false;
      if (!CanFire(b, owner, seat, fire))
        return Failed(out, Failure::native_predicate_unavailable);
      out.native_can_fire = fire;
    }
  }
  Seat last{};
  std::uint32_t last_owner_rite = 0, last_candidate_rite = 0;
  std::int32_t last_court_owner = -1;
  if (!Snapshot(b, after) || !SameFrame(before, after) ||
      Character(b, out.owner_character_id) != owner || Character(b, candidate_id) != candidate ||
      !ChaplainSeat(b, owner, out.owner_character_id, last) || seat != last ||
      !Context(b, owner, candidate, last_owner_rite, last_candidate_rite, last_court_owner) ||
      owner_rite != last_owner_rite || candidate_rite != last_candidate_rite || court_owner != last_court_owner)
    return Failed(out, Failure::state_changed);
  out.available = true; out.failure = Failure::none;
  return true;
}

const char *ClergyAppointmentFailureKey(Failure v) noexcept {
  switch (v) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::owner_thread_required: return "owner_thread_required";
  case Failure::frame_unavailable: return "frame_unavailable";
  case Failure::not_paused: return "not_paused";
  case Failure::player_unavailable: return "player_unavailable";
  case Failure::candidate_unavailable: return "candidate_unavailable";
  case Failure::task_unavailable: return "task_unavailable";
  case Failure::candidate_context_unavailable: return "candidate_context_unavailable";
  case Failure::native_predicate_unavailable: return "native_predicate_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "unknown";
}

std::string SerializeClergyAppointment12002(const Observation &v) {
  std::ostringstream o; o << std::boolalpha;
  o << "{\"schema\":\"xar.ck3.religion-clergy-appointment/v1\",\"schema_version\":1,"
    << "\"exact_build\":{\"game_version\":\"1.20.0.2\",\"executable_sha256\":\""
    << kExecutableSha256 << "\"},\"status\":\"" << (v.available ? "available" : "unavailable")
    << "\",\"failure\":\"" << ClergyAppointmentFailureKey(v.failure)
    << "\",\"capture_epoch\":" << v.capture_epoch << ",\"date_raw\":" << v.date_raw
    << ",\"owner_character_id\":" << v.owner_character_id
    << ",\"candidate_character_id\":" << v.candidate_character_id
    << ",\"position_key\":\"" << kPositionKey << "\",\"position_present\":" << v.position_present
    << ",\"active_task_id\":"; Optional(o,v.active_task_id);
  o << ",\"incumbent_character_id\":"; Optional(o,v.incumbent_character_id);
  o << ",\"candidate_court_owner_id\":"; Optional(o,v.candidate_court_owner_id);
  o << ",\"owner_rite_id\":"; Optional(o,v.owner_rite_id);
  o << ",\"candidate_rite_id\":"; Optional(o,v.candidate_rite_id);
  o << ",\"candidate_is_incumbent\":" << v.candidate_is_incumbent;
  o << ",\"candidate_matches_owner_context\":"; Optional(o,v.candidate_matches_owner_context);
  o << ",\"native_valid_position\":"; Optional(o,v.native_valid_position);
  o << ",\"native_valid_character\":"; Optional(o,v.native_valid_character);
  o << ",\"native_can_reassign\":"; Optional(o,v.native_can_reassign);
  o << ",\"native_can_fire\":"; Optional(o,v.native_can_fire);
  o << ",\"action_eligibility_complete\":false}";
  return o.str();
}

} // namespace xar::ck3_12002::religion::clergy
