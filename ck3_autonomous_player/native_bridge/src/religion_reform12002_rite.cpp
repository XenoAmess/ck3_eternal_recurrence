#include "xar_bridge/religion_reform12002_rite.hpp"

#include <cstring>

namespace xar::ck3_12002::religion_reform::rite {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
bool Matches(const void *object, std::uint32_t id) noexcept {
  return object && Load<std::uint32_t>(object, religion::kReferenceIdentityOffset) == id;
}
std::optional<std::uint32_t> Reference(std::uint32_t id) noexcept {
  return id == religion::kAbsentReference ? std::nullopt : std::optional{id};
}
Failure ReadOnce(const Bindings &b, std::uint64_t epoch, Model &out) {
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(b.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive)
    return Failure::played_character_unavailable;
  if (!frame.clock.paused) return Failure::frame_not_paused;
  auto *character = ResolveCoreCharacter(b.core, frame.played_character_id);
  if (!character) return Failure::played_character_unavailable;
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = frame.played_character_id;
  const auto rite_id = Load<std::uint32_t>(character, religion::kCharacterRiteIdOffset);
  if (rite_id != religion::kAbsentReference) {
    auto *current = b.character_rite(character);
    if (!Matches(current, rite_id)) return Failure::rite_unavailable;
    out.rite_id = rite_id;
    const auto faith_id = Load<std::uint32_t>(current, religion::kRiteFaithIdOffset);
    auto *faith = b.rite_faith(current);
    if (faith_id == religion::kAbsentReference || !Matches(faith, faith_id))
      return Failure::faith_unavailable;
    out.faith_id = faith_id;
    const auto main_id = Load<std::uint32_t>(faith, religion::kFaithMainRiteIdOffset);
    if (main_id == religion::kAbsentReference || !Matches(b.faith_main_rite(faith), main_id))
      return Failure::main_rite_unavailable;
    out.faith_main_rite_id = main_id;
    out.founder_character_id = Reference(Load<std::uint32_t>(current, kRiteFounderCharacterIdOffset));
    out.head_character_id = Reference(Load<std::uint32_t>(current, kRiteHeadCharacterIdOffset));
    out.current_is_main = b.rite_is_main(current);
    std::int64_t divergence{}, threshold{};
    if (b.divergence_to_main(&divergence, current, nullptr) != &divergence)
      return Failure::divergence_unavailable;
    if (b.faith_heresy_threshold(faith, &threshold) != &threshold)
      return Failure::threshold_unavailable;
    out.divergence_to_main_raw = divergence;
    out.faith_heresy_threshold_raw = threshold;
  }
  if (ResolveCoreCharacter(b.core, frame.played_character_id) != character)
    return Failure::state_changed;
  out.available = true;
  out.failure = Failure::none;
  return Failure::none;
}
bool Same(const Model &a, const Model &b) noexcept {
  return a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.rite_id == b.rite_id && a.faith_id == b.faith_id &&
      a.faith_main_rite_id == b.faith_main_rite_id &&
      a.founder_character_id == b.founder_character_id &&
      a.head_character_id == b.head_character_id && a.current_is_main == b.current_is_main &&
      a.divergence_to_main_raw == b.divergence_to_main_raw &&
      a.faith_heresy_threshold_raw == b.faith_heresy_threshold_raw;
}
template <typename T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
std::string Boolean(const std::optional<bool> &value) {
  return value ? (*value ? "true" : "false") : "null";
}
} // namespace

Bindings BindRiteModelImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.core = BindCoreImage(base, sha);
  b.character_rite = reinterpret_cast<religion::ObjectGetter>(base + religion::kCharacterRiteRva);
  b.rite_faith = reinterpret_cast<religion::ObjectGetter>(base + religion::kRiteFaithRva);
  b.faith_main_rite = reinterpret_cast<religion::ObjectGetter>(base + religion::kFaithMainRiteRva);
  b.rite_is_main = reinterpret_cast<IsMainGetter>(base + kRiteIsMainRva);
  b.divergence_to_main = reinterpret_cast<DivergenceGetter>(base + kRiteDivergenceToMainRva);
  b.faith_heresy_threshold = reinterpret_cast<religion::FixedPointGetter>(base + kFaithHeresyThresholdRva);
  return b;
}

bool ReadPlayedRiteModel12002(const Bindings &b, std::uint64_t epoch, Model &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  if (!b.enabled || !b.core.enabled || !b.character_rite || !b.rite_faith ||
      !b.faith_main_rite || !b.rite_is_main || !b.divergence_to_main ||
      !b.faith_heresy_threshold) return false;
  Model first{}, second{};
  auto failure = ReadOnce(b, epoch, first);
  if (failure == Failure::none) failure = ReadOnce(b, epoch, second);
  if (failure == Failure::none && !Same(first, second)) failure = Failure::state_changed;
  if (failure != Failure::none) { out.failure = failure; return false; }
  out = std::move(first);
  return true;
}

const char *RiteModelFailureKey(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::rite_unavailable: return "rite_unavailable";
  case Failure::faith_unavailable: return "faith_unavailable";
  case Failure::main_rite_unavailable: return "main_rite_unavailable";
  case Failure::divergence_unavailable: return "divergence_unavailable";
  case Failure::threshold_unavailable: return "threshold_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}

std::string SerializePlayedRiteModel12002(const Model &m) {
  return "{\"schema\":\"religion_reform12002_rite_model_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":\"" + std::string(kExecutableSha256) + "\",\"available\":" +
      (m.available ? "true" : "false") + ",\"unavailable_reason\":" +
      (m.available ? "null" : "\"" + std::string(RiteModelFailureKey(m.failure)) + "\"") +
      ",\"capture_epoch\":" + std::to_string(m.capture_epoch) +
      ",\"date_raw\":" + std::to_string(m.date_raw) +
      ",\"played_character_id\":" + std::to_string(m.played_character_id) +
      ",\"rite_id\":" + Number(m.rite_id) + ",\"faith_id\":" + Number(m.faith_id) +
      ",\"faith_main_rite_id\":" + Number(m.faith_main_rite_id) +
      ",\"founder_character_id\":" + Number(m.founder_character_id) +
      ",\"head_character_id\":" + Number(m.head_character_id) +
      ",\"current_is_main\":" + Boolean(m.current_is_main) +
      ",\"divergence_to_main_raw\":" + Number(m.divergence_to_main_raw) +
      ",\"faith_heresy_threshold_raw\":" + Number(m.faith_heresy_threshold_raw) +
      ",\"raw_scale\":100000}";
}
} // namespace xar::ck3_12002::religion_reform::rite
