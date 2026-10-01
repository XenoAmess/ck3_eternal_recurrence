#include "xar_bridge/conversion_outcome12002_actor.hpp"

#include <cstring>

#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_12002::religion_conversion::outcome::actor {
namespace {
bool ReadLocalMemory(void *, std::uintptr_t address, void *out, std::size_t size) noexcept {
  if (!address || !out || !size) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(out, reinterpret_cast<const void *>(address), size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}
bool SamePlayerFrame(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return b.map_ready && b.clock.paused && b.has_played_character && b.played_character_alive &&
      a.played_character_id == b.played_character_id && a.clock.date_raw == b.clock.date_raw;
}
template <typename T> std::string Number(const std::optional<T> &v) {
  return v ? std::to_string(*v) : "null";
}
} // namespace

Bindings BindConversionOutcomeActorImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  b.current_religion = religion::BindReligionContextImage12002(base, sha);
  if (b.current_religion.enabled) b.read_memory = &ReadLocalMemory;
  return b;
}
bool ReadPlayedConversionOutcomeActor12002(const Bindings &b, std::uint64_t epoch,
                                         Context &out) noexcept {
  out = {}; out.capture_epoch = epoch;
  const auto &core = b.current_religion.core;
  if (!b.current_religion.enabled || !core.enabled || !b.read_memory) return false;
  CoreSnapshotPrefix before{};
  if (!ReadCoreSnapshot(core, before) || !before.map_ready ||
      !before.has_played_character || !before.played_character_alive) {
    out.failure = Failure::played_character_unavailable; return false;
  }
  if (!before.clock.paused) { out.failure = Failure::frame_not_paused; return false; }
  out.date_raw = before.clock.date_raw; out.played_character_id = before.played_character_id;
  if (!religion::ReadPlayedReligionContext12002(b.current_religion, epoch, out.current_religion)) {
    out.failure = Failure::current_religion_unavailable; return false;
  }
  if (out.current_religion.played_character_id != before.played_character_id ||
      out.current_religion.date_raw != before.clock.date_raw) {
    out.failure = Failure::state_changed; return false;
  }
  auto *character = ResolveCoreCharacter(core, before.played_character_id);
  if (!character) { out.failure = Failure::played_character_unavailable; return false; }
  ActorResourceBalances12002 sampled{};
  if (!ReadActorResourceBalances12002(b.read_memory, b.memory_context,
      reinterpret_cast<std::uintptr_t>(character), before.played_character_id, sampled)) {
    out.failure = Failure::resources_unavailable; return false;
  }
  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(core, after) || !SamePlayerFrame(before, after) ||
      ResolveCoreCharacter(core, before.played_character_id) != character) {
    out.failure = Failure::state_changed; return false;
  }
  out.piety_raw = sampled.piety_raw;
  out.gold_raw = sampled.gold_raw;
  out.prestige_raw = sampled.prestige_raw;
  out.available = true; out.failure = Failure::none;
  return true;
}
const char *ConversionOutcomeActorFailureKey(Failure f) noexcept {
  switch (f) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::current_religion_unavailable: return "current_religion_unavailable";
  case Failure::resources_unavailable: return "resources_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}
std::string SerializeConversionOutcomeActor12002(const Context &c) {
  return "{\"schema\":\"ck3_12002_conversion_outcome_actor_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":\"" + std::string(kExecutableSha256) + "\",\"read_only\":true,"
      "\"available\":" + (c.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (c.available ? std::string("null") :
          std::string("\"") + ConversionOutcomeActorFailureKey(c.failure) + '"') +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"current_religion\":" + religion::SerializePlayedReligionContext12002(c.current_religion) +
      ",\"piety_raw\":" + Number(c.piety_raw) + ",\"gold_raw\":" + Number(c.gold_raw) +
      ",\"prestige_raw\":" + Number(c.prestige_raw) + ",\"raw_scale\":100000,"
      "\"conversion_causality_inferred\":false}";
}
} // namespace xar::ck3_12002::religion_conversion::outcome::actor
