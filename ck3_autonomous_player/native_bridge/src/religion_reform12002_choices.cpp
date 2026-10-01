#include "xar_bridge/religion_reform12002_choices.hpp"
#include "xar_bridge/religion_doctrine12002_tenet_rows.hpp"
#include <cstring>

namespace xar::ck3_12002::religion_reform {
namespace {
template<class T> T Load(const void *p, std::size_t offset) {
  T out{}; std::memcpy(&out, static_cast<const std::byte *>(p) + offset, sizeof(out)); return out;
}
const std::byte *At(const void *p, std::size_t offset) {
  return static_cast<const std::byte *>(p) + offset;
}
struct ArrayView { const std::byte *data{}; std::int32_t count{}; };
bool Array(const void *p, ArrayView &out) {
  out = {Load<const std::byte *>(p, 0), Load<std::int32_t>(p, 0xC)};
  const auto capacity = Load<std::int32_t>(p, 8);
  return out.count >= 0 && out.count <= capacity && out.count <= 8192 && (!out.count || out.data);
}
bool SameArray(const void *p, const ArrayView &a) {
  return Load<const std::byte *>(p, 0) == a.data && Load<std::int32_t>(p, 0xC) == a.count;
}
bool Fail(DraftChoices &out, const char *reason) { out.failure = reason; return false; }
const void *Prophet(const DraftChoiceBindings &b) {
  const auto *database = b.perk_database_global ? *b.perk_database_global : nullptr;
  return database ? Load<const void *>(database, kProphetPerkCacheOffset) : nullptr;
}
bool ReadOnce(const DraftChoiceBindings &b, std::uint64_t epoch, DraftChoices &out) {
  DraftWindowView view{};
  if (!ReadCurrentRiteCreationWindow12002(b.window, epoch, view))
    return Fail(out, DraftWindowFailureKey(view.failure));
  out.capture_epoch = epoch; out.date_raw = view.date_raw;
  out.played_character_id = view.played_character_id; out.source_rite_id = view.source_rite_id;
  if (!view.window) { out.available = true; out.failure = "none"; return true; }
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(b.window.core, frame) || !frame.clock.paused ||
      frame.clock.date_raw != view.date_raw || !frame.has_played_character ||
      static_cast<std::uint32_t>(frame.played_character_id) != view.played_character_id)
    return Fail(out, "state_changed");
  auto *actor = ResolveCoreCharacter(b.window.core, frame.played_character_id);
  if (!actor || !frame.played_character_alive) return Fail(out, "played_character_unavailable");
  const auto *scope = At(view.window, kDraftTopScopeOffset);
  const auto *doctrine_array = At(view.window, kDraftDoctrineCategoryOffset + kCategoryDoctrineArrayOffset);
  const auto *group_array = At(view.window, kDraftTenetGroupArrayOffset);
  ArrayView doctrines{}, groups{};
  if (!Array(doctrine_array, doctrines) || !Array(group_array, groups))
    return Fail(out, "popup_collection_unavailable");
  for (std::int32_t i = 0; i < doctrines.count; ++i) {
    const auto *item = doctrines.data + static_cast<std::size_t>(i) * kDoctrineItemStride;
    const auto *definition = Load<const void *>(item, kChoiceDefinitionOffset);
    religion::doctrine12002::DoctrineRow keys{};
    if (!religion::doctrine12002::CopyDoctrineDefinition12002(definition, keys))
      return Fail(out, "doctrine_definition_unavailable");
    DraftDoctrineChoice row{};
    row.doctrine_key = std::move(keys.doctrine_key); row.group_key = std::move(keys.group_key);
    row.popup_index = static_cast<std::uint32_t>(i);
    row.native_can_pick = b.evaluate_trigger(At(definition, 0x1B8), scope) &&
                          b.evaluate_trigger(At(definition, 0xE8), scope);
    if (row.native_can_pick) {
      row.native_knows_doctrine = b.knows_doctrine(actor, definition);
      if (!*row.native_knows_doctrine) {
        const auto *prophet = Prophet(b);
        if (!prophet) return Fail(out, "prophet_definition_unavailable");
        row.native_has_prophet = b.has_perk(actor, prophet);
      }
      row.button_enabled = *row.native_knows_doctrine || row.native_has_prophet.value_or(false);
    }
    if (Load<const void *>(item, kChoiceDefinitionOffset) != definition)
      return Fail(out, "state_changed");
    out.doctrines.push_back(std::move(row));
  }
  for (std::int32_t group = 0; group < groups.count; ++group) {
    const auto *collection = groups.data + static_cast<std::size_t>(group) * kTenetGroupStride + kGroupTenetArrayOffset;
    ArrayView items{};
    if (!Array(collection, items)) return Fail(out, "popup_collection_unavailable");
    for (std::int32_t i = 0; i < items.count; ++i) {
      const auto *item = items.data + static_cast<std::size_t>(i) * kTenetItemStride;
      const auto *definition = Load<const void *>(item, kChoiceDefinitionOffset);
      DraftTenetChoice row{};
      if (!religion::doctrine12002::CopyTenetDefinitionKey12002(definition, row.tenet_key))
        return Fail(out, "tenet_definition_unavailable");
      row.popup_group_index = static_cast<std::uint32_t>(group); row.popup_item_index = static_cast<std::uint32_t>(i);
      row.native_pick_source = Load<std::uint8_t>(item, kTenetPickSourceOffset);
      // The source==0 native branch can use the lazy perk-database getter.
      // Read its initialized cache first; this producer never initializes it.
      if (row.native_pick_source == 0 && !Prophet(b)) return Fail(out, "prophet_definition_unavailable");
      row.native_can_pick = b.tenet_can_pick(item, actor, scope);
      if (Load<const void *>(item, kChoiceDefinitionOffset) != definition ||
          Load<std::uint8_t>(item, kTenetPickSourceOffset) != row.native_pick_source)
        return Fail(out, "state_changed");
      out.tenets.push_back(std::move(row));
    }
    if (!SameArray(collection, items)) return Fail(out, "state_changed");
  }
  DraftWindowView after{};
  if (!SameArray(doctrine_array, doctrines) || !SameArray(group_array, groups) ||
      !ReadCurrentRiteCreationWindow12002(b.window, epoch, after) || after.window != view.window ||
      after.date_raw != view.date_raw || after.played_character_id != view.played_character_id ||
      after.source_rite_id != view.source_rite_id ||
      ResolveCoreCharacter(b.window.core, frame.played_character_id) != actor)
    return Fail(out, "state_changed");
  out.available = true; out.draft_observed = true; out.failure = "none"; return true;
}
std::string Quote(std::string_view v) {
  std::string out = "\""; constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char c : v) {
    if (c == '\\' || c == '"') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 32) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += static_cast<char>(c);
  }
  return out + '"';
}
const char *Bool(bool value) { return value ? "true" : "false"; }
std::string OptionalBool(const std::optional<bool> &v) { return v ? Bool(*v) : "null"; }
} // namespace

DraftChoiceBindings BindCurrentDraftChoices12002(std::uintptr_t base, std::string_view sha) noexcept {
  DraftChoiceBindings b{}; b.window = BindCurrentRiteCreationWindow12002(base, sha);
  if (!b.window.enabled) return b;
  b.knows_doctrine = religion::doctrine12002::BindDoctrineKnowledgeImage12002(base, sha).knows_doctrine;
  b.evaluate_trigger = reinterpret_cast<ChoiceTriggerEval>(base + kChoiceTriggerEvalRva);
  b.tenet_can_pick = reinterpret_cast<TenetItemCanPick>(base + kTenetItemCanPickRva);
  b.has_perk = reinterpret_cast<ChoiceHasPerk>(base + kChoiceHasPerkRva);
  b.perk_database_global = reinterpret_cast<void *const *>(base + kChoicePerkDatabaseGlobalRva);
  return b;
}
bool ReadCurrentDraftChoices12002(const DraftChoiceBindings &b, std::uint64_t epoch, DraftChoices &out) noexcept {
  out = {}; out.capture_epoch = epoch;
  if (!b.window.enabled || !b.knows_doctrine || !b.evaluate_trigger || !b.tenet_can_pick || !b.has_perk) return false;
  DraftChoices candidate{}; candidate.capture_epoch = epoch;
  bool ok = false;
#if defined(_WIN32) && defined(_MSC_VER)
  // Put SEH in the trivial wrapper below; STL destruction stays in this scope.
  auto guarded = [](const DraftChoiceBindings &binding, std::uint64_t e, DraftChoices &value) -> bool {
    __try { return ReadOnce(binding, e, value); }
    __except (1) { value.failure = "popup_layout_unavailable"; return false; }
  };
  ok = guarded(b, epoch, candidate);
#else
  ok = ReadOnce(b, epoch, candidate);
#endif
  if (ok) out = std::move(candidate);
  else { out.failure = std::move(candidate.failure); out.date_raw = candidate.date_raw;
    out.played_character_id = candidate.played_character_id; }
  return ok;
}
std::string SerializeCurrentDraftChoices12002(const DraftChoices &v) {
  std::string doctrines = "[", tenets = "[";
  for (const auto &row : v.doctrines) {
    if (doctrines.size() > 1) doctrines += ',';
    doctrines += "{\"doctrine_key\":" + Quote(row.doctrine_key) + ",\"group_key\":" + Quote(row.group_key) +
      ",\"popup_index\":" + std::to_string(row.popup_index) + ",\"native_can_pick\":" + Bool(row.native_can_pick) +
      ",\"native_knows_doctrine\":" + OptionalBool(row.native_knows_doctrine) +
      ",\"native_has_prophet\":" + OptionalBool(row.native_has_prophet) + ",\"button_enabled\":" + Bool(row.button_enabled) + '}';
  }
  for (const auto &row : v.tenets) {
    if (tenets.size() > 1) tenets += ',';
    tenets += "{\"tenet_key\":" + Quote(row.tenet_key) + ",\"popup_group_index\":" + std::to_string(row.popup_group_index) +
      ",\"popup_item_index\":" + std::to_string(row.popup_item_index) + ",\"native_pick_source\":" +
      std::to_string(row.native_pick_source) + ",\"native_can_pick\":" + Bool(row.native_can_pick) + '}';
  }
  return "{\"schema\":\"ck3_12002_current_draft_popup_choices_v1\",\"game_version\":\"1.20.0.2\","
    "\"executable_sha256\":" + Quote(kExecutableSha256) + ",\"available\":" + Bool(v.available) +
    ",\"unavailable_reason\":" + (v.available ? "null" : Quote(v.failure)) +
    ",\"scope\":\"already_materialized_current_popup_candidates\",\"draft_observed\":" + Bool(v.draft_observed) +
    ",\"capture_epoch\":" + std::to_string(v.capture_epoch) + ",\"date_raw\":" + std::to_string(v.date_raw) +
    ",\"played_character_id\":" + std::to_string(v.played_character_id) + ",\"source_rite_id\":" +
    (v.source_rite_id ? std::to_string(*v.source_rite_id) : "null") + ",\"doctrines\":" + doctrines +
    "],\"tenets\":" + tenets + "]}";
}
} // namespace xar::ck3_12002::religion_reform
