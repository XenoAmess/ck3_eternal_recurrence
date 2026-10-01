#include "xar_bridge/religion_rite_governance12002_organization_members.hpp"
#include <algorithm>
#include <cstring>

namespace xar::ck3_12002::religion::organization::members {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value)); return value;
}
bool Matches(const void *object, std::uint32_t id) noexcept {
  return object && Load<std::uint32_t>(object, kReferenceIdentityOffset) == id;
}
bool Collect(Collector collector, std::uint16_t kind, std::uint32_t id,
             std::int32_t capacity, std::vector<ScopeValue> &rows) {
  if (capacity < 0) return false;
  rows.resize(static_cast<std::size_t>(capacity));
  ScopeArray native{rows.data(), capacity, 0, nullptr};
  const ScopeValue root{kind, 0, 0, id}; const ScopeRoot context{&root};
  // Each proven native collector emits at most one row per actual source item.
  // Thus this buffer is caller-owned and the native append never grows it.
  collector(nullptr, &native, &context);
  if (native.data != rows.data() || native.capacity != capacity || native.size < 0 || native.size > capacity)
    return false;
  rows.resize(static_cast<std::size_t>(native.size)); return true;
}
void *ResolveTitle(const Bindings &b, std::uint32_t id) {
  auto *storage = *b.title_storage_slot;
  if (!storage || id == kAbsentReference) return nullptr;
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto *slots = Load<const void *>(storage, 0x20);
  const auto index = id & 0x00FFFFFFU;
  if (!slots || capacity <= 0 || index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  auto *title = Load<void *>(slots, static_cast<std::size_t>(index) * 16 + 8);
  return title && Load<std::uint32_t>(title, kTitleIdentityOffset) == id ? title : nullptr;
}
void Normalize(std::vector<std::uint32_t> &ids) {
  std::sort(ids.begin(), ids.end()); ids.erase(std::unique(ids.begin(), ids.end()), ids.end());
}
Failure Read(const Bindings &b, std::uint64_t epoch, Snapshot &out) {
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(b.core, frame) || !frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive) return Failure::frame_unavailable;
  if (!frame.clock.paused) return Failure::frame_not_paused;
  auto *character = ResolveCoreCharacter(b.core, frame.played_character_id);
  if (!character) return Failure::frame_unavailable;
  out.capture_epoch = epoch; out.date_raw = frame.clock.date_raw;
  out.played_character_id = frame.played_character_id;
  const auto rite_id = Load<std::uint32_t>(character, kCharacterRiteIdOffset);
  if (rite_id == kAbsentReference) { out.available = true; out.failure = Failure::none; return Failure::none; }
  auto *rite = b.character_rite(character);
  if (!Matches(rite, rite_id)) return Failure::religion_context_unavailable;
  const auto faith_id = Load<std::uint32_t>(rite, kRiteFaithIdOffset);
  auto *faith = b.rite_faith(rite);
  if (faith_id == kAbsentReference || !Matches(faith, faith_id)) return Failure::religion_context_unavailable;
  const auto religion_id = Load<std::uint32_t>(faith, kFaithReligionIdOffset);
  auto *religion = b.faith_religion(faith);
  if (religion_id == kAbsentReference || !Matches(religion, religion_id))
    return Failure::religion_context_unavailable;
  out.rite_id = rite_id; out.faith_id = faith_id; out.religion_id = religion_id;
  auto *state = *b.core.game_state_slot;
  auto *data = state ? Load<void *>(state, 0xA0) : nullptr;
  if (!data) return Failure::source_pool_unavailable;
  const auto characters = Load<std::int32_t>(data, kAlivePoolSizeOffset);
  const auto counties = Load<std::int32_t>(religion, kReligionCountyPoolSizeOffset);
  if (characters < 0 || counties < 0 ||
      (characters && !Load<void *>(data, kAlivePoolOffset)) ||
      (counties && !Load<void *>(religion, kReligionCountyPoolOffset))) return Failure::source_pool_unavailable;
  std::vector<ScopeValue> character_rows, county_rows;
  if (!Collect(b.faith_characters, kFaithScope, faith_id, characters, character_rows) ||
      !Collect(b.rite_counties, kRiteScope, rite_id, counties, county_rows))
    return Failure::native_output_unavailable;
  for (const auto &row : character_rows) {
    if (row.kind != kCharacterScope || row.identity > UINT32_MAX) return Failure::native_output_unavailable;
    const auto id = static_cast<std::uint32_t>(row.identity);
    auto *member = ResolveCoreCharacter(b.core, static_cast<std::int32_t>(id));
    if (!member) return Failure::character_unavailable;
    const auto member_rite_id = Load<std::uint32_t>(member, kCharacterRiteIdOffset);
    auto *member_rite = b.character_rite(member);
    if (!Matches(member_rite, member_rite_id) ||
        Load<std::uint32_t>(member_rite, kRiteFaithIdOffset) != faith_id)
      return Failure::character_unavailable;
    out.faith_character_ids.push_back(id);
    if (member_rite_id == rite_id) out.rite_character_ids.push_back(id);
  }
  for (const auto &row : county_rows) {
    if (row.kind != kTitleScope || row.identity > UINT32_MAX) return Failure::native_output_unavailable;
    const auto id = static_cast<std::uint32_t>(row.identity);
    auto *title = ResolveTitle(b, id);
    auto *definition = title ? Load<void *>(title, kTitleTemplateOffset) : nullptr;
    if (!definition || Load<std::int32_t>(definition, kTitleTemplateRankOffset) != 2)
      return Failure::county_title_unavailable;
    out.county_title_ids.push_back(id);
  }
  Normalize(out.faith_character_ids); Normalize(out.rite_character_ids); Normalize(out.county_title_ids);
  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(b.core, after) || !after.clock.paused || after.clock.date_raw != frame.clock.date_raw ||
      after.played_character_id != frame.played_character_id ||
      Load<std::uint32_t>(character, kCharacterRiteIdOffset) != rite_id) return Failure::state_changed;
  out.available = true; out.failure = Failure::none; return Failure::none;
}
std::string Number(const std::optional<std::uint32_t> &value) { return value ? std::to_string(*value) : "null"; }
std::string Ids(const std::vector<std::uint32_t> &values) {
  std::string result = "[";
  for (const auto id : values) { if (result.size() > 1) result += ','; result += std::to_string(id); }
  return result + ']';
}
} // namespace
Bindings BindOrganizationMembersImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{}; if (!base || sha != kExecutableSha256) return b;
  b.enabled = true; b.core = BindCoreImage(base, sha);
  b.character_rite = reinterpret_cast<ObjectGetter>(base + kCharacterRiteRva);
  b.rite_faith = reinterpret_cast<ObjectGetter>(base + kRiteFaithRva);
  b.faith_religion = reinterpret_cast<ObjectGetter>(base + kFaithReligionRva);
  b.title_storage_slot = reinterpret_cast<void **>(base + kTitleStorageSlotRva);
  b.faith_characters = reinterpret_cast<Collector>(base + kFaithCharacterCollectorRva);
  b.rite_counties = reinterpret_cast<Collector>(base + kRiteCountyCollectorRva);
  return b;
}
bool ReadPlayedOrganizationMembers12002(const Bindings &b, std::uint64_t epoch, Snapshot &output) noexcept {
  output = {}; output.capture_epoch = epoch;
  if (!b.enabled || !b.core.enabled || !b.character_rite || !b.rite_faith || !b.faith_religion ||
      !b.title_storage_slot || !b.faith_characters || !b.rite_counties) return false;
  Snapshot current{}; const auto failure = Read(b, epoch, current);
  if (failure != Failure::none) { output.failure = failure; return false; }
  output = std::move(current); return true;
}
const char *MembersFailureKey(Failure f) noexcept {
  switch (f) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::frame_unavailable: return "frame_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::religion_context_unavailable: return "religion_context_unavailable";
  case Failure::source_pool_unavailable: return "source_pool_unavailable";
  case Failure::native_output_unavailable: return "native_output_unavailable";
  case Failure::character_unavailable: return "character_unavailable";
  case Failure::county_title_unavailable: return "county_title_unavailable";
  case Failure::state_changed: return "state_changed";
  } return "bindings_unavailable";
}
std::string SerializePlayedOrganizationMembers12002(const Snapshot &s) {
  return "{\"schema\":\"ck3_12002_rite_organization_members_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":\"" + std::string(kExecutableSha256) + "\","
      "\"scope\":\"current_player_rite_and_its_faith\",\"available\":" + (s.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (s.available ? std::string("null") :
          "\"" + std::string(MembersFailureKey(s.failure)) + "\"") +
      ",\"capture_epoch\":" + std::to_string(s.capture_epoch) +
      ",\"date_raw\":" + std::to_string(s.date_raw) +
      ",\"played_character_id\":" + std::to_string(s.played_character_id) +
      ",\"rite_id\":" + Number(s.rite_id) + ",\"faith_id\":" + Number(s.faith_id) +
      ",\"religion_id\":" + Number(s.religion_id) +
      ",\"faith_character_ids\":" + Ids(s.faith_character_ids) +
      ",\"rite_character_ids\":" + Ids(s.rite_character_ids) +
      ",\"county_title_ids\":" + Ids(s.county_title_ids) + "}";
}
} // namespace xar::ck3_12002::religion::organization::members
