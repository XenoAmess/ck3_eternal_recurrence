#include "xar_bridge/religion_rite_governance12002_state_rite.hpp"

#include <cstring>
#include <utility>

namespace xar::ck3_12002::religion::state_rite {
namespace {
template <typename T> T Load(const void *object, std::size_t at) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value));
  return value;
}

bool Matches(const void *object, std::uint32_t id, std::size_t at) noexcept {
  return object && Load<std::uint32_t>(object, at) == id;
}

Failure ReadActor(const Bindings &b, void *actor, Context &out) {
  const auto rite_id = Load<std::uint32_t>(actor, kCharacterRiteIdOffset);
  if (rite_id == kAbsentReference) return Failure::none;
  auto *rite = b.context.character_rite(actor);
  if (!Matches(rite, rite_id, kReferenceIdentityOffset))
    return Failure::actor_rite_unavailable;
  out.actor_rite_id = rite_id;
  const auto faith_id = Load<std::uint32_t>(rite, kRiteFaithIdOffset);
  if (faith_id == kAbsentReference) return Failure::none;
  auto *faith = b.context.rite_faith(rite);
  if (!Matches(faith, faith_id, kReferenceIdentityOffset) ||
      b.context.character_faith(actor) != faith)
    return Failure::actor_faith_unavailable;
  out.actor_faith_id = faith_id;
  const auto main = Load<std::uint32_t>(faith, kFaithMainRiteIdOffset);
  if (main == kAbsentReference) return Failure::none;
  if (!Matches(b.context.faith_main_rite(faith), main, kReferenceIdentityOffset))
    return Failure::actor_main_rite_unavailable;
  out.actor_faith_main_rite_id = main;
  return Failure::none;
}

Failure ReadPrimaryTitle(const Bindings &b, void *character, TitleContext &out) {
  const auto *landed = Load<const void *>(character, kCharacterLandedDataOffset);
  const auto *death = Load<const void *>(character, kCharacterDeathDataOffset);
  const auto *holder = landed ? landed : death;
  if (!holder) return Failure::none;
  const auto count_offset = landed ? kLandedTitlesCountOffset : kDeathTitlesCountOffset;
  if (Load<std::int32_t>(holder, count_offset) == 0) return Failure::none;
  const auto titles_offset = landed ? kLandedTitlesOffset : kDeathTitlesOffset;
  const auto *titles = Load<const void *>(holder, titles_offset);
  if (!titles) return Failure::primary_title_unavailable;
  const auto id = Load<std::uint32_t>(titles, 0);
  if (id == kAbsentReference) return Failure::none;
  auto *title = b.character_primary_title(character);
  if (!Matches(title, id, kTitleIdentityOffset))
    return Failure::primary_title_unavailable;
  out.title_id = id;
  const auto state_rite = Load<std::uint32_t>(title, kTitleStateRiteIdOffset);
  if (state_rite == kAbsentReference) return Failure::none;
  auto *rite = b.title_state_rite(title);
  if (!Matches(rite, state_rite, kReferenceIdentityOffset))
    return Failure::title_state_rite_unavailable;
  out.state_rite_id = state_rite;
  const auto faith_id = Load<std::uint32_t>(rite, kRiteFaithIdOffset);
  if (faith_id == kAbsentReference) return Failure::none;
  if (!Matches(b.context.rite_faith(rite), faith_id, kReferenceIdentityOffset))
    return Failure::title_state_faith_unavailable;
  out.state_faith_id = faith_id;
  return Failure::none;
}

Failure ReadOnce(const Bindings &b, std::uint64_t epoch, Context &out) {
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(b.context.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive)
    return Failure::played_character_unavailable;
  if (!frame.clock.paused) return Failure::frame_not_paused;
  auto *actor = ResolveCoreCharacter(b.context.core, frame.played_character_id);
  if (!actor) return Failure::played_character_unavailable;
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = static_cast<std::uint32_t>(frame.played_character_id);
  auto failure = ReadActor(b, actor, out);
  if (failure != Failure::none) return failure;
  failure = ReadPrimaryTitle(b, actor, out.player_primary_title);
  if (failure != Failure::none) return failure;
  auto *liege = b.character_top_liege(actor);
  if (!liege) return Failure::top_liege_unavailable;
  const auto liege_id = Load<std::int32_t>(liege, kCharacterIdentityOffset);
  if (liege_id == -1 || ResolveCoreCharacter(b.context.core, liege_id) != liege)
    return Failure::top_liege_unavailable;
  out.top_liege_character_id = static_cast<std::uint32_t>(liege_id);
  failure = ReadPrimaryTitle(b, liege, out.realm_primary_title);
  if (failure != Failure::none) return failure;
  out.available = true;
  out.failure = Failure::none;
  return Failure::none;
}

bool Same(const Context &a, const Context &b) {
  return a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.actor_rite_id == b.actor_rite_id && a.actor_faith_id == b.actor_faith_id &&
      a.actor_faith_main_rite_id == b.actor_faith_main_rite_id &&
      a.top_liege_character_id == b.top_liege_character_id &&
      a.player_primary_title == b.player_primary_title &&
      a.realm_primary_title == b.realm_primary_title;
}

template <typename T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
std::string TitleJson(const TitleContext &t) {
  return "{\"title_id\":" + Number(t.title_id) +
      ",\"state_rite_id\":" + Number(t.state_rite_id) +
      ",\"state_faith_id\":" + Number(t.state_faith_id) + "}";
}
} // namespace

Bindings BindStateRiteImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.context = BindReligionContextImage12002(base, sha);
  b.character_top_liege = reinterpret_cast<ObjectGetter>(base + kCharacterTopLiegeRva);
  b.character_primary_title = reinterpret_cast<ObjectGetter>(base + kCharacterPrimaryTitleRva);
  b.title_state_rite = reinterpret_cast<ObjectGetter>(base + kTitleStateRiteRva);
  return b;
}

bool ReadPlayedStateRite12002(const Bindings &b, std::uint64_t epoch,
                             Context &output) noexcept {
  output = {};
  output.capture_epoch = epoch;
  if (!b.enabled || !b.context.enabled || !b.context.core.enabled ||
      !b.context.character_rite || !b.context.character_faith ||
      !b.context.rite_faith || !b.context.faith_main_rite ||
      !b.character_top_liege || !b.character_primary_title || !b.title_state_rite)
    return false;
  Context first{}, second{};
  auto failure = ReadOnce(b, epoch, first);
  if (failure == Failure::none) failure = ReadOnce(b, epoch, second);
  if (failure == Failure::none && !Same(first, second)) failure = Failure::state_changed;
  if (failure != Failure::none) { output.failure = failure; return false; }
  output = std::move(first);
  return true;
}

const char *StateRiteFailureKey(Failure f) noexcept {
  switch (f) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::actor_rite_unavailable: return "actor_rite_unavailable";
  case Failure::actor_faith_unavailable: return "actor_faith_unavailable";
  case Failure::actor_main_rite_unavailable: return "actor_main_rite_unavailable";
  case Failure::top_liege_unavailable: return "top_liege_unavailable";
  case Failure::primary_title_unavailable: return "primary_title_unavailable";
  case Failure::title_state_rite_unavailable: return "title_state_rite_unavailable";
  case Failure::title_state_faith_unavailable: return "title_state_faith_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}

std::string SerializePlayedStateRite12002(const Context &c) {
  return "{\"schema\":\"ck3_12002_religion_state_rite_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":\"" + std::string(kExecutableSha256) +
      "\",\"available\":" + (c.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (c.available ? "null" : '"' + std::string(StateRiteFailureKey(c.failure)) + '"') +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"actor_rite_id\":" + Number(c.actor_rite_id) +
      ",\"actor_faith_id\":" + Number(c.actor_faith_id) +
      ",\"actor_faith_main_rite_id\":" + Number(c.actor_faith_main_rite_id) +
      ",\"top_liege_character_id\":" + Number(c.top_liege_character_id) +
      ",\"player_primary_title\":" + TitleJson(c.player_primary_title) +
      ",\"realm_primary_title\":" + TitleJson(c.realm_primary_title) + "}";
}
} // namespace xar::ck3_12002::religion::state_rite
