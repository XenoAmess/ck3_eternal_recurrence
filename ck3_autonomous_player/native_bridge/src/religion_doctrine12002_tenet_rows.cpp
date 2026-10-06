#include "xar_bridge/religion_doctrine12002_tenet_rows.hpp"
#include "xar_bridge/tenet_definition_key_copy.hpp"

#include <algorithm>
#include <cstring>

namespace xar::ck3_12002::religion::doctrine12002 {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
bool Matches(const void *object, std::uint32_t id) noexcept {
  return object && Load<std::uint32_t>(object, religion::kReferenceIdentityOffset) == id;
}
bool Key(const void *definition, std::string &out) {
  return detail::CopyTenetDefinitionKeySource(definition, out);
}
std::string Entry(const TenetRowsBindings &b, void *current_rite, const void *definition,
                  TenetEntry &out) {
  if (!Key(definition, out.key)) return "tenet_definition_unavailable";
  if (current_rite) {
    const auto state = b.tenet_state(current_rite, definition);
    if (state > 4) return "tenet_state_unavailable";
    out.current_rite_status = state;
  }
  return {};
}
std::string Pointers(const void *collection, std::size_t stride, std::vector<const void *> &out) {
  const auto count = Load<std::int32_t>(collection, 0xC);
  const auto *data = Load<const std::byte *>(collection, 0);
  if (count < 0 || count > 8192 || (count && !data)) return "tenet_collection_unavailable";
  for (std::int32_t i = 0; i < count; ++i)
    out.push_back(Load<const void *>(data, static_cast<std::size_t>(i) * stride));
  if (Load<const std::byte *>(collection, 0) != data || Load<std::int32_t>(collection, 0xC) != count)
    return "state_changed";
  return {};
}
std::string Entries(const TenetRowsBindings &b, void *current_rite,
                    const std::vector<const void *> &definitions, std::vector<TenetEntry> &out) {
  for (const auto *definition : definitions) {
    TenetEntry entry{};
    auto failure = Entry(b, current_rite, definition, entry);
    if (!failure.empty()) return failure;
    out.push_back(std::move(entry));
  }
  return {};
}
void Union(std::vector<const void *> &all, const std::vector<const void *> &add) {
  for (const auto *p : add) if (std::find(all.begin(), all.end(), p) == all.end()) all.push_back(p);
}
std::string ReadOnce(const religion::Bindings &r, const TenetRowsBindings &b,
                     std::uint64_t epoch, TenetRowsContext &out) {
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(r.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive)
    return "played_character_unavailable";
  if (!frame.clock.paused) return "frame_not_paused";
  auto *character = ResolveCoreCharacter(r.core, frame.played_character_id);
  if (!character) return "played_character_unavailable";
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = static_cast<std::uint32_t>(frame.played_character_id);
  void *current_rite = nullptr;
  std::vector<const void *> all_definitions;
  const auto rite_id = Load<std::uint32_t>(character, religion::kCharacterRiteIdOffset);
  if (rite_id != religion::kAbsentReference) {
    current_rite = r.character_rite(character);
    if (!Matches(current_rite, rite_id)) return "rite_unavailable";
    std::vector<const void *> definitions;
    auto failure = Pointers(static_cast<const std::byte *>(current_rite) + kRiteCoreTenetsOffset, 8, definitions);
    if (!failure.empty()) return failure;
    RiteCoreTenets current{}; current.rite_id = rite_id;
    failure = Entries(b, current_rite, definitions, current.core_tenets);
    if (!failure.empty()) return failure;
    out.current_rite = std::move(current);
    Union(all_definitions, definitions);
    const auto faith_id = Load<std::uint32_t>(current_rite, religion::kRiteFaithIdOffset);
    if (faith_id != religion::kAbsentReference) {
      auto *faith = r.rite_faith(current_rite);
      if (!Matches(faith, faith_id) || r.character_faith(character) != faith)
        return "faith_unavailable";
      out.faith_id = faith_id;
      const auto main_id = Load<std::uint32_t>(faith, religion::kFaithMainRiteIdOffset);
      if (main_id != religion::kAbsentReference) {
        auto *main_rite = r.faith_main_rite(faith);
        if (!Matches(main_rite, main_id)) return "main_rite_unavailable";
        definitions.clear();
        failure = Pointers(static_cast<const std::byte *>(main_rite) + kRiteCoreTenetsOffset, 8, definitions);
        if (!failure.empty()) return failure;
        RiteCoreTenets main{}; main.rite_id = main_id;
        failure = Entries(b, current_rite, definitions, main.core_tenets);
        if (!failure.empty()) return failure;
        out.faith_main_rite = std::move(main);
        Union(all_definitions, definitions);
        definitions.clear();
        failure = Pointers(static_cast<const std::byte *>(main_rite) + kRiteTenetStatesOffset, 16, definitions);
        if (!failure.empty()) return failure;
        Union(all_definitions, definitions);
      }
    }
  }
  const auto *extension = Load<const void *>(character, kCharacterExtensionOffset);
  if (extension) {
    std::vector<const void *> personal;
    auto failure = Pointers(static_cast<const std::byte *>(extension) + kPersonalTenetsOffset, 8, personal);
    if (!failure.empty()) return failure;
    failure = Entries(b, current_rite, personal, out.personal_tenets);
    if (!failure.empty()) return failure;
    Union(all_definitions, personal);
  }
  auto failure = Entries(b, current_rite, all_definitions, out.effective_tenet_states);
  if (!failure.empty()) return failure;
  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(r.core, after) || !after.clock.paused ||
      after.clock.date_raw != frame.clock.date_raw || after.played_character_id != frame.played_character_id ||
      ResolveCoreCharacter(r.core, frame.played_character_id) != character)
    return "state_changed";
  return {};
}
bool Same(const TenetRowsContext &a, const TenetRowsContext &b) {
  return a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.faith_id == b.faith_id && a.current_rite == b.current_rite &&
      a.faith_main_rite == b.faith_main_rite && a.personal_tenets == b.personal_tenets &&
      a.effective_tenet_states == b.effective_tenet_states;
}
std::string Quote(std::string_view value) {
  std::string result = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const auto c : value) {
    const auto byte = static_cast<unsigned char>(c);
    if (c == '\\' || c == '"') { result += '\\'; result += c; }
    else if (byte < 32) { result += "\\u00"; result += hex[byte >> 4]; result += hex[byte & 15]; }
    else result += c;
  }
  return result + '"';
}
std::string EntriesJson(const std::vector<TenetEntry> &entries) {
  std::string result = "[";
  for (std::size_t i = 0; i < entries.size(); ++i) {
    if (i) result += ',';
    const auto state = entries[i].current_rite_status;
    result += "{\"key\":" + Quote(entries[i].key) + ",\"current_rite_status\":" +
        (state ? std::to_string(*state) : "null") + "}";
  }
  return result + ']';
}
std::string RiteJson(const std::optional<RiteCoreTenets> &rite) {
  return rite ? "{\"rite_id\":" + std::to_string(rite->rite_id) +
      ",\"core_tenets\":" + EntriesJson(rite->core_tenets) + "}" : "null";
}
} // namespace

TenetRowsBindings BindTenetRows12002(std::uintptr_t base, std::string_view sha) noexcept {
  return base && sha == kExecutableSha256 ?
      TenetRowsBindings{true, reinterpret_cast<NativeTenetState>(base + kNativeTenetStateRva)} : TenetRowsBindings{};
}
bool CopyTenetDefinitionKey12002(const void *definition, std::string &output) {
  return Key(definition, output);
}
bool ReadPlayedTenetRows12002(const religion::Bindings &r, const TenetRowsBindings &b,
                             std::uint64_t epoch, TenetRowsContext &out) noexcept {
  out = {}; out.capture_epoch = epoch;
  if (!b.enabled || !b.tenet_state || !r.enabled || !r.core.enabled || !r.character_rite ||
      !r.character_faith || !r.rite_faith || !r.faith_main_rite) return false;
  TenetRowsContext first{}, second{};
  auto failure = ReadOnce(r, b, epoch, first);
  if (failure.empty()) failure = ReadOnce(r, b, epoch, second);
  if (failure.empty() && !Same(first, second)) failure = "state_changed";
  if (!failure.empty()) { out.failure = std::move(failure); return false; }
  out = std::move(first); out.available = true; out.failure = "none"; return true;
}
std::string SerializeTenetRows12002(const TenetRowsContext &c) {
  return "{\"schema\":\"ck3_12002_tenet_rows_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"available\":" + (c.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (c.available ? "null" : Quote(c.failure)) +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"faith_id\":" + (c.faith_id ? std::to_string(*c.faith_id) : "null") +
      ",\"current_rite\":" + RiteJson(c.current_rite) +
      ",\"faith_main_rite\":" + RiteJson(c.faith_main_rite) +
      ",\"personal_tenets_complete\":" + (c.available ? "true" : "false") +
      ",\"personal_tenets\":" + EntriesJson(c.personal_tenets) +
      ",\"effective_tenet_states\":" + EntriesJson(c.effective_tenet_states) +
      ",\"status_values\":{\"unknown\":0,\"known\":1,\"prohibited\":2,\"permitted\":3,\"core\":4}}";
}
} // namespace xar::ck3_12002::religion::doctrine12002
