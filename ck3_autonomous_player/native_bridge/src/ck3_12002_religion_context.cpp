#include "xar_bridge/ck3_12002_religion_context.hpp"

#include <cstring>

namespace xar::ck3_12002::religion {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}

bool Matches(const void *object, std::uint32_t id) noexcept {
  return object && Load<std::uint32_t>(object, kReferenceIdentityOffset) == id;
}

bool CopyTag(const void *native_string, std::optional<std::string> &output) {
  if (!native_string) return false;
  const auto size = Load<std::uint64_t>(native_string, 0x10);
  const auto capacity = Load<std::uint64_t>(native_string, 0x18);
  if (size > capacity || size > 4096) return false;
  const auto *data = capacity < 16 ? static_cast<const char *>(native_string)
                                 : Load<const char *>(native_string, 0);
  if (!data && size) return false;
  output = size ? std::string(data, static_cast<std::size_t>(size)) : std::string{};
  return true;
}

const void *ReligionDefinitionTag(void *religion) noexcept {
  const auto *definition = Load<const void *>(religion, kReligionDefinitionPointerOffset);
  return definition ? static_cast<const std::byte *>(definition) + kReligionDefinitionTagOffset
                    : nullptr;
}

Failure ReadOnce(const Bindings &b, std::uint64_t epoch, Context &out) {
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

  const auto rite_id = Load<std::uint32_t>(character, kCharacterRiteIdOffset);
  if (rite_id != kAbsentReference) {
    auto *rite = b.character_rite(character);
    if (!Matches(rite, rite_id)) return Failure::rite_unavailable;
    out.rite_id = rite_id;
    const auto faith_id = Load<std::uint32_t>(rite, kRiteFaithIdOffset);
    if (faith_id != kAbsentReference) {
      auto *faith = b.rite_faith(rite);
      if (!Matches(faith, faith_id) || b.character_faith(character) != faith)
        return Failure::faith_unavailable;
      out.faith_id = faith_id;
      if (!CopyTag(b.faith_tag(faith), out.faith_key)) return Failure::tag_unavailable;
      const auto religion_id = Load<std::uint32_t>(faith, kFaithReligionIdOffset);
      if (religion_id != kAbsentReference) {
        auto *religion = b.faith_religion(faith);
        if (!Matches(religion, religion_id)) return Failure::religion_unavailable;
        out.religion_id = religion_id;
        if (!CopyTag(b.religion_tag(religion), out.religion_key))
          return Failure::tag_unavailable;
      }
      const auto main_rite_id = Load<std::uint32_t>(faith, kFaithMainRiteIdOffset);
      if (main_rite_id != kAbsentReference) {
        if (!Matches(b.faith_main_rite(faith), main_rite_id))
          return Failure::main_rite_unavailable;
        out.faith_main_rite_id = main_rite_id;
      }
      std::int64_t fervor{};
      if (b.faith_fervor(faith, &fervor) != &fervor)
        return Failure::fervor_unavailable;
      out.faith_fervor_raw = fervor;
    }
  }
  std::int64_t fulfillment{};
  if (b.character_spiritual_fulfillment(character, &fulfillment) != &fulfillment)
    return Failure::spiritual_fulfillment_unavailable;
  out.spiritual_fulfillment_raw = fulfillment;
  if (ResolveCoreCharacter(b.core, frame.played_character_id) != character)
    return Failure::state_changed;
  out.available = true;
  out.failure = Failure::none;
  return Failure::none;
}

bool Same(const Context &a, const Context &b) {
  return a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.rite_id == b.rite_id && a.faith_id == b.faith_id &&
      a.religion_id == b.religion_id && a.faith_main_rite_id == b.faith_main_rite_id &&
      a.faith_key == b.faith_key && a.religion_key == b.religion_key &&
      a.faith_fervor_raw == b.faith_fervor_raw &&
      a.spiritual_fulfillment_raw == b.spiritual_fulfillment_raw;
}

std::string Quoted(std::string_view value) {
  std::string result = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const auto c : value) {
    const auto byte = static_cast<unsigned char>(c);
    if (c == '\\' || c == '"') { result += '\\'; result += c; }
    else if (byte < 32) {
      result += "\\u00"; result += hex[byte >> 4]; result += hex[byte & 15];
    } else result += c;
  }
  return result + '"';
}
template <typename T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
std::string Text(const std::optional<std::string> &value) {
  return value ? Quoted(*value) : "null";
}
} // namespace

Bindings BindReligionContextImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.core = BindCoreImage(base, sha);
  b.character_rite = reinterpret_cast<ObjectGetter>(base + kCharacterRiteRva);
  b.character_faith = reinterpret_cast<ObjectGetter>(base + kCharacterFaithRva);
  b.rite_faith = reinterpret_cast<ObjectGetter>(base + kRiteFaithRva);
  b.faith_religion = reinterpret_cast<ObjectGetter>(base + kFaithReligionRva);
  b.faith_main_rite = reinterpret_cast<ObjectGetter>(base + kFaithMainRiteRva);
  b.faith_fervor = reinterpret_cast<FixedPointGetter>(base + kFaithFervorRva);
  b.character_spiritual_fulfillment = reinterpret_cast<FixedPointGetter>(base + kCharacterSpiritualFulfillmentRva);
  b.faith_tag = reinterpret_cast<TagGetter>(base + kFaithTagRva);
  // The old 0x247CA20 reflection branch points into string metadata on this
  // build. Read the observed CReligion definition's authored CString instead.
  b.religion_tag = &ReligionDefinitionTag;
  return b;
}

bool ReadPlayedReligionContext12002(const Bindings &b, std::uint64_t epoch,
                                   Context &output) noexcept {
  output = {};
  output.capture_epoch = epoch;
  if (!b.enabled || !b.core.enabled || !b.character_rite || !b.character_faith ||
      !b.rite_faith || !b.faith_religion || !b.faith_main_rite ||
      !b.faith_fervor || !b.character_spiritual_fulfillment ||
      !b.faith_tag || !b.religion_tag) return false;
  Context first{}, second{};
  auto failure = ReadOnce(b, epoch, first);
  if (failure == Failure::none) failure = ReadOnce(b, epoch, second);
  if (failure == Failure::none && !Same(first, second)) failure = Failure::state_changed;
  if (failure != Failure::none) { output.failure = failure; return false; }
  output = std::move(first);
  return true;
}

const char *ReligionContextFailureKey(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::rite_unavailable: return "rite_unavailable";
  case Failure::faith_unavailable: return "faith_unavailable";
  case Failure::religion_unavailable: return "religion_unavailable";
  case Failure::main_rite_unavailable: return "main_rite_unavailable";
  case Failure::tag_unavailable: return "tag_unavailable";
  case Failure::fervor_unavailable: return "fervor_unavailable";
  case Failure::spiritual_fulfillment_unavailable: return "spiritual_fulfillment_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}

std::string SerializePlayedReligionContext12002(const Context &c) {
  return "{\"schema\":\"ck3_12002_religion_context_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quoted(kExecutableSha256) +
      ",\"available\":" + (c.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (c.available ? "null" : Quoted(ReligionContextFailureKey(c.failure))) +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"rite_id\":" + Number(c.rite_id) + ",\"faith_id\":" + Number(c.faith_id) +
      ",\"religion_id\":" + Number(c.religion_id) +
      ",\"faith_main_rite_id\":" + Number(c.faith_main_rite_id) +
      ",\"faith_key\":" + Text(c.faith_key) + ",\"religion_key\":" + Text(c.religion_key) +
      ",\"faith_fervor_raw\":" + Number(c.faith_fervor_raw) +
      ",\"spiritual_fulfillment_raw\":" + Number(c.spiritual_fulfillment_raw) +
      ",\"raw_scale\":100000}";
}
} // namespace xar::ck3_12002::religion
