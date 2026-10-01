#include "xar_bridge/religion_rite_governance12002_head.hpp"

#include <bit>
#include <cstring>

namespace xar::ck3_12002::religion::head {
namespace {
template <typename T> T Load(const void *object, std::size_t at) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value));
  return value;
}
bool ReferenceMatches(const void *object, std::uint32_t id) noexcept {
  return object && Load<std::uint32_t>(object, kReferenceIdentityOffset) == id;
}
bool ReadHead(const Bindings &b, void *rite,
              std::optional<std::uint32_t> &head_id) noexcept {
  const auto stored_id = Load<std::uint32_t>(rite, kRiteHeadCharacterIdOffset);
  std::uint32_t getter_id = kAbsentReference;
  if (b.rite_head_id(rite, &getter_id) != &getter_id || getter_id != stored_id)
    return false;
  if (stored_id == kAbsentReference) return true;
  auto *resolved = ResolveCoreCharacter(b.context.core, std::bit_cast<std::int32_t>(stored_id));
  if (!resolved || b.rite_head(rite) != resolved) return false;
  head_id = stored_id;
  return true;
}
Failure ReadOnce(const Bindings &b, std::uint64_t epoch, Context &out) noexcept {
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(b.context.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive)
    return Failure::played_character_unavailable;
  if (!frame.clock.paused) return Failure::frame_not_paused;
  auto *actor = ResolveCoreCharacter(b.context.core, frame.played_character_id);
  if (!actor) return Failure::played_character_unavailable;
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = frame.played_character_id;
  const auto rite_id = Load<std::uint32_t>(actor, kCharacterRiteIdOffset);
  if (rite_id != kAbsentReference) {
    auto *rite = b.context.character_rite(actor);
    if (!ReferenceMatches(rite, rite_id)) return Failure::rite_unavailable;
    out.actor_rite_id = rite_id;
    if (!ReadHead(b, rite, out.actor_rite_head_character_id))
      return Failure::rite_head_unavailable;
    const auto faith_id = Load<std::uint32_t>(rite, kRiteFaithIdOffset);
    if (faith_id != kAbsentReference) {
      auto *faith = b.context.rite_faith(rite);
      if (!ReferenceMatches(faith, faith_id) || b.context.character_faith(actor) != faith)
        return Failure::faith_unavailable;
      out.faith_id = faith_id;
      const auto main_id = Load<std::uint32_t>(faith, kFaithMainRiteIdOffset);
      if (main_id != kAbsentReference) {
        auto *main_rite = b.context.faith_main_rite(faith);
        if (!ReferenceMatches(main_rite, main_id)) return Failure::main_rite_unavailable;
        out.faith_main_rite_id = main_id;
        if (!ReadHead(b, main_rite, out.faith_main_rite_head_character_id))
          return Failure::main_rite_head_unavailable;
      }
      const auto title_id = Load<std::uint32_t>(faith, kFaithReligiousHeadTitleIdOffset);
      if (title_id != kAbsentReference) {
        auto *title = b.faith_religious_head_title(faith);
        if (!title || Load<std::uint32_t>(title, kTitleReferenceIdOffset) != title_id)
          return Failure::faith_head_title_unavailable;
        out.faith_religious_head_title_id = title_id;
        const auto holder_id = Load<std::uint32_t>(title, kTitleHolderCharacterIdOffset);
        if (holder_id != kAbsentReference) {
          auto *holder = ResolveCoreCharacter(b.context.core, std::bit_cast<std::int32_t>(holder_id));
          if (!holder || b.faith_religious_head(faith) != holder)
            return Failure::faith_head_holder_unavailable;
          out.faith_religious_head_holder_character_id = holder_id;
        }
      }
    }
  }
  out.available = true;
  out.failure = Failure::none;
  return Failure::none;
}
bool Same(const Context &a, const Context &b) noexcept {
  return a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.actor_rite_id == b.actor_rite_id && a.faith_id == b.faith_id &&
      a.faith_main_rite_id == b.faith_main_rite_id &&
      a.actor_rite_head_character_id == b.actor_rite_head_character_id &&
      a.faith_main_rite_head_character_id == b.faith_main_rite_head_character_id &&
      a.faith_religious_head_title_id == b.faith_religious_head_title_id &&
      a.faith_religious_head_holder_character_id == b.faith_religious_head_holder_character_id;
}
std::string Number(const std::optional<std::uint32_t> &id) {
  return id ? std::to_string(*id) : "null";
}
} // namespace

Bindings BindRiteHeadsImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  b.context = BindReligionContextImage12002(base, sha);
  if (!b.context.enabled) return b;
  b.enabled = true;
  b.rite_head_id = reinterpret_cast<HeadIdGetter>(base + kRiteHeadIdGetterRva);
  b.rite_head = reinterpret_cast<ObjectGetter>(base + kRiteHeadObjectGetterRva);
  b.faith_religious_head = reinterpret_cast<ObjectGetter>(base + kFaithReligiousHeadGetterRva);
  b.faith_religious_head_title = reinterpret_cast<ObjectGetter>(base + kFaithReligiousHeadTitleGetterRva);
  return b;
}
bool ReadPlayedRiteHeads12002(const Bindings &b, std::uint64_t epoch, Context &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  if (!b.enabled || !b.context.enabled || !b.context.core.enabled ||
      !b.context.character_rite || !b.context.character_faith || !b.context.rite_faith ||
      !b.context.faith_main_rite || !b.rite_head_id || !b.rite_head ||
      !b.faith_religious_head || !b.faith_religious_head_title) return false;
  Context first{}, second{};
  auto failure = ReadOnce(b, epoch, first);
  if (failure == Failure::none) failure = ReadOnce(b, epoch, second);
  if (failure == Failure::none && !Same(first, second)) failure = Failure::state_changed;
  if (failure != Failure::none) { out.failure = failure; return false; }
  out = first;
  return true;
}
const char *RiteHeadsFailureKey(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::rite_unavailable: return "rite_unavailable";
  case Failure::faith_unavailable: return "faith_unavailable";
  case Failure::main_rite_unavailable: return "main_rite_unavailable";
  case Failure::rite_head_unavailable: return "rite_head_unavailable";
  case Failure::main_rite_head_unavailable: return "main_rite_head_unavailable";
  case Failure::faith_head_title_unavailable: return "faith_head_title_unavailable";
  case Failure::faith_head_holder_unavailable: return "faith_head_holder_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}
std::string SerializePlayedRiteHeads12002(const Context &c) {
  return "{\"schema\":\"ck3_12002_religion_rite_heads_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":\"" + std::string(kExecutableSha256) + "\","
      "\"available\":" + (c.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (c.available ? "null" : "\"" + std::string(RiteHeadsFailureKey(c.failure)) + "\"") +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"actor_rite_id\":" + Number(c.actor_rite_id) +
      ",\"faith_id\":" + Number(c.faith_id) +
      ",\"faith_main_rite_id\":" + Number(c.faith_main_rite_id) +
      ",\"actor_rite_head_character_id\":" + Number(c.actor_rite_head_character_id) +
      ",\"faith_main_rite_head_character_id\":" + Number(c.faith_main_rite_head_character_id) +
      ",\"faith_religious_head_title_id\":" + Number(c.faith_religious_head_title_id) +
      ",\"faith_religious_head_holder_character_id\":" + Number(c.faith_religious_head_holder_character_id) + "}";
}
} // namespace xar::ck3_12002::religion::head
