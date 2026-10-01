#include "xar_bridge/ck3_12002_religion_conversion_faith.hpp"
#include <cstring>

namespace xar::ck3_12002::religion_conversion::faith {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T out{};
  std::memcpy(&out, static_cast<const std::byte *>(object) + offset, sizeof(out));
  return out;
}
void *ResolveFaith(const Bindings &b, std::uint32_t id) noexcept {
  const auto *storage = b.faith_storage_slot ? *b.faith_storage_slot : nullptr;
  if (!storage || id == kAbsentId) return nullptr;
  const auto index = id & 0xFFFFFFu;
  if (index >= Load<std::uint32_t>(storage, 0x2C)) return nullptr;
  const auto *slots = Load<const void *>(storage, 0x20);
  if (!slots) return nullptr;
  auto *faith = Load<void *>(slots, static_cast<std::size_t>(index) * 16 + 8);
  return faith && Load<std::uint32_t>(faith, kIdentityOffset) == id ? faith : nullptr;
}
bool Tag(const void *native, std::string &out) {
  if (!native) return false;
  const auto count = Load<std::uint64_t>(native, 0x10);
  const auto capacity = Load<std::uint64_t>(native, 0x18);
  if (count > capacity) return false;
  const auto *bytes = capacity < 16 ? static_cast<const char *>(native)
                                  : Load<const char *>(native, 0);
  if (count && !bytes) return false;
  out = count ? std::string(bytes, static_cast<std::size_t>(count)) : std::string{};
  return true;
}
std::string Quote(std::string_view value) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const char ch : value) {
    const auto byte = static_cast<unsigned char>(ch);
    if (ch == '\\' || ch == '"') { out += '\\'; out += ch; }
    else if (byte < 32) { out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15]; }
    else out += ch;
  }
  return out + '"';
}
bool SameFrame(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) {
  return a.clock.date_raw == b.clock.date_raw && b.clock.paused && b.map_ready &&
      b.has_played_character && b.played_character_alive &&
      a.played_character_id == b.played_character_id;
}
bool Read(const Bindings &b, Choices &out) {
  CoreSnapshotPrefix before{};
  if (!ReadCoreSnapshot(b.core, before) || !before.map_ready ||
      !before.has_played_character || !before.played_character_alive) {
    out.unavailable_reason = "played_character_unavailable"; return false;
  }
  out.date_raw = before.clock.date_raw;
  out.played_character_id = before.played_character_id;
  if (!before.clock.paused) { out.unavailable_reason = "frame_not_paused"; return false; }
  auto *actor = ResolveCoreCharacter(b.core, before.played_character_id);
  auto *current = actor ? b.character_faith(actor) : nullptr;
  if (!current) { out.unavailable_reason = "current_faith_unavailable"; return false; }
  const auto current_id = Load<std::uint32_t>(current, kIdentityOffset);
  if (ResolveFaith(b, current_id) != current) {
    out.unavailable_reason = "current_faith_unavailable"; return false;
  }
  out.current_faith_id = current_id;
  auto *state = b.core.game_state_slot ? *b.core.game_state_slot : nullptr;
  auto *world = state ? Load<void *>(state, kWorldDataOffset) : nullptr;
  if (!world) { out.unavailable_reason = "world_unavailable"; return false; }
  const auto count = Load<std::int32_t>(world, kWorldFaithCountOffset);
  const auto *items = Load<const void *>(world, kWorldFaithsOffset);
  if (count < 0 || (count && !items)) {
    out.unavailable_reason = "faith_registry_unavailable"; return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    auto *target = Load<void *>(items, static_cast<std::size_t>(index) * sizeof(void *));
    if (!target) { out.unavailable_reason = "faith_candidate_unavailable"; return false; }
    Choice row{};
    row.faith_id = Load<std::uint32_t>(target, kIdentityOffset);
    if (ResolveFaith(b, row.faith_id) != target) {
      out.unavailable_reason = "faith_candidate_unavailable"; return false;
    }
    if (!Tag(b.faith_tag(target), row.faith_key)) {
      out.unavailable_reason = "faith_tag_unavailable"; return false;
    }
    const auto main_id = Load<std::uint32_t>(target, kFaithMainRiteIdOffset);
    if (main_id != kAbsentId) {
      auto *main = b.faith_main_rite(target);
      if (!main || Load<std::uint32_t>(main, kIdentityOffset) != main_id ||
          b.rite_faith(main) != target) {
        out.unavailable_reason = "faith_main_rite_unavailable"; return false;
      }
      row.main_rite_id = main_id;
    }
    row.native_faith_rule_passes = b.conversion_rule(actor, row.faith_id, nullptr);
    out.choices.push_back(std::move(row));
  }
  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(b.core, after) || !SameFrame(before, after) ||
      ResolveCoreCharacter(b.core, before.played_character_id) != actor ||
      b.character_faith(actor) != current ||
      Load<std::int32_t>(world, kWorldFaithCountOffset) != count ||
      Load<const void *>(world, kWorldFaithsOffset) != items) {
    out.unavailable_reason = "state_changed"; return false;
  }
  out.available = true; out.unavailable_reason.clear(); return true;
}
} // namespace

Bindings BindFaithConversionImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true; b.core = BindCoreImage(base, sha);
  b.faith_storage_slot = reinterpret_cast<void **>(base + kFaithStorageSlotRva);
  b.character_faith = reinterpret_cast<ObjectGetter>(base + kCharacterFaithRva);
  b.faith_main_rite = reinterpret_cast<ObjectGetter>(base + kFaithMainRiteRva);
  b.rite_faith = reinterpret_cast<ObjectGetter>(base + kRiteFaithRva);
  b.faith_tag = reinterpret_cast<TagGetter>(base + kFaithTagRva);
  b.conversion_rule = reinterpret_cast<ConversionRule>(base + kFaithConversionRuleRva);
  return b;
}
bool ReadPlayedFaithConversionChoices12002(const Bindings &b, std::uint64_t epoch,
                                         Choices &out) noexcept {
  out = {}; out.capture_epoch = epoch;
  if (!b.enabled || !b.core.enabled || !b.faith_storage_slot || !b.character_faith ||
      !b.faith_main_rite || !b.rite_faith || !b.faith_tag || !b.conversion_rule) return false;
  const bool ok = Read(b, out);
  if (!ok) out.choices.clear();
  return ok;
}
std::string SerializePlayedFaithConversionChoices12002(const Choices &out) {
  std::string wire = "{\"schema\":\"ck3_12002_faith_conversion_choices_v1\","
      "\"game_version\":\"1.20.0.2\",\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"available\":" + (out.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (out.available ? "null" : Quote(out.unavailable_reason)) +
      ",\"capture_epoch\":" + std::to_string(out.capture_epoch) +
      ",\"date_raw\":" + std::to_string(out.date_raw) +
      ",\"played_character_id\":" + std::to_string(out.played_character_id) +
      ",\"current_faith_id\":" + (out.current_faith_id ? std::to_string(*out.current_faith_id) : "null") +
      ",\"candidate_source\":\"native_world_faith_registry\",\"rule_only\":true,\"choices\":[";
  bool comma = false;
  for (const auto &row : out.choices) {
    if (comma) wire += ',';
    comma = true;
    wire += "{\"faith_id\":" + std::to_string(row.faith_id) + ",\"faith_key\":" + Quote(row.faith_key) +
        ",\"main_rite_id\":" + (row.main_rite_id ? std::to_string(*row.main_rite_id) : "null") +
        ",\"native_faith_rule_passes\":" + (row.native_faith_rule_passes ? "true" : "false") + '}';
  }
  return wire + "]}";
}
} // namespace xar::ck3_12002::religion_conversion::faith
