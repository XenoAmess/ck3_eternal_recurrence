#include "xar_bridge/religion_doctrine12002_rite.hpp"

#include <cstring>

namespace xar::ck3_12002::religion::doctrine12002 {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
bool Matches(const void *object, std::uint32_t reference) noexcept {
  return object && Load<std::uint32_t>(object, religion::kReferenceIdentityOffset) == reference;
}
const char *ReadOnce(const religion::Bindings &b, std::uint64_t epoch,
                     RiteDoctrineSnapshot &out) {
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(b.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive)
    return "played_character_unavailable";
  if (!frame.clock.paused) return "frame_not_paused";
  auto *character = ResolveCoreCharacter(b.core, frame.played_character_id);
  if (!character) return "played_character_unavailable";
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = frame.played_character_id;
  const auto rite_id = Load<std::uint32_t>(character, religion::kCharacterRiteIdOffset);
  if (rite_id != religion::kAbsentReference) {
    auto *rite = b.character_rite(character);
    if (!Matches(rite, rite_id)) return "rite_unavailable";
    out.rite_id = rite_id;
    const auto faith_id = Load<std::uint32_t>(rite, religion::kRiteFaithIdOffset);
    if (faith_id != religion::kAbsentReference) {
      auto *faith = b.rite_faith(rite);
      if (!Matches(faith, faith_id) || b.character_faith(character) != faith)
        return "faith_unavailable";
      out.faith_id = faith_id;
    }
    const auto count = Load<std::int32_t>(rite, kRiteEffectiveDoctrineCountOffset);
    const auto capacity = Load<std::int32_t>(rite, kRiteEffectiveDoctrineCapacityOffset);
    const auto *definitions = Load<const void *const *>(rite, kRiteEffectiveDoctrineDataOffset);
    if (count < 0 || capacity < count || (count && !definitions))
      return "doctrine_collection_unavailable";
    out.rows.reserve(static_cast<std::size_t>(count));
    for (std::int32_t i = 0; i < count; ++i) {
      DoctrineRow row{};
      if (!CopyDoctrineDefinition12002(definitions[i], row))
        return "doctrine_definition_unavailable";
      row.source = "rite_effective";
      out.rows.push_back(std::move(row));
    }
  }
  if (ResolveCoreCharacter(b.core, frame.played_character_id) != character)
    return "state_changed";
  out.available = true;
  out.unavailable_reason.clear();
  return nullptr;
}
bool Same(const RiteDoctrineSnapshot &a, const RiteDoctrineSnapshot &b) noexcept {
  return a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.rite_id == b.rite_id && a.faith_id == b.faith_id && a.rows == b.rows;
}
std::string Quoted(std::string_view value) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const auto c : value) {
    const auto byte = static_cast<unsigned char>(c);
    if (c == '\\' || c == '"') { out += '\\'; out += c; }
    else if (byte < 32) {
      out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15];
    } else out += c;
  }
  return out + '"';
}
std::string Id(const std::optional<std::uint32_t> &value) {
  return value ? std::to_string(*value) : "null";
}
} // namespace

bool ReadPlayedRiteDoctrines12002(const religion::Bindings &b, std::uint64_t epoch,
                                RiteDoctrineSnapshot &out) noexcept {
  out = {};
  if (!b.enabled || !b.core.enabled || !b.character_rite || !b.character_faith ||
      !b.rite_faith) return false;
  try {
    RiteDoctrineSnapshot first{}, second{};
    const char *failure = ReadOnce(b, epoch, first);
    if (!failure) failure = ReadOnce(b, epoch, second);
    if (failure) { out.unavailable_reason = failure; return false; }
    if (!Same(first, second)) { out.unavailable_reason = "state_changed"; return false; }
    out = std::move(second);
    return true;
  } catch (...) {
    out.unavailable_reason = "doctrine_read_failed";
    return false;
  }
}

bool HasRiteDoctrineByStableKey12002(const RiteDoctrineSnapshot &snapshot,
                                   std::string_view key) noexcept {
  if (!snapshot.available) return false;
  for (const auto &row : snapshot.rows)
    if (row.doctrine_key == key) return true;
  return false;
}

std::string SerializeRiteDoctrines12002(const RiteDoctrineSnapshot &value) {
  std::string out = "{\"schema\":\"ck3_12002_player_rite_doctrines_v1\",\"available\":";
  out += value.available ? "true" : "false";
  out += ",\"unavailable_reason\":" + (value.available ? std::string("null") : Quoted(value.unavailable_reason));
  out += ",\"capture_epoch\":" + std::to_string(value.capture_epoch);
  out += ",\"date_raw\":" + std::to_string(value.date_raw);
  out += ",\"played_character_id\":" + std::to_string(value.played_character_id);
  out += ",\"rite_id\":" + Id(value.rite_id) + ",\"faith_id\":" + Id(value.faith_id);
  out += ",\"rows\":[";
  bool comma = false;
  for (const auto &row : value.rows) {
    if (comma) out += ',';
    comma = true;
    out += "{\"doctrine_key\":" + Quoted(row.doctrine_key) +
        ",\"group_key\":" + Quoted(row.group_key) + ",\"source\":" + Quoted(row.source) + '}';
  }
  return out + "]}";
}
} // namespace xar::ck3_12002::religion::doctrine12002
