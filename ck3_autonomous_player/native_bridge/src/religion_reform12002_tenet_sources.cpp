#include "xar_bridge/religion_reform12002_tenet_sources.hpp"
#include "xar_bridge/religion_doctrine12002_tenet_rows.hpp"
#include <cstring>

namespace xar::ck3_12002::religion_reform {
namespace {
template<class T> T Load(const void *p, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(value));
  return value;
}
const std::byte *At(const void *p, std::size_t offset) {
  return static_cast<const std::byte *>(p) + offset;
}
struct ArrayView { const std::byte *data{}; std::int32_t count{}; };
bool Array(const void *p, ArrayView &value) {
  value = {Load<const std::byte *>(p, 0), Load<std::int32_t>(p, 0xC)};
  return value.count >= 0 && value.count <= 8192 &&
    value.count <= Load<std::int32_t>(p, 8) && (!value.count || value.data);
}
bool SameArray(const void *p, const ArrayView &value) {
  return Load<const std::byte *>(p, 0) == value.data &&
    Load<std::int32_t>(p, 0xC) == value.count;
}
void *Resolve(void *const *global, std::uint32_t id) {
  if (!global || !*global || id == 0xFFFFFFFFU) return nullptr;
  const auto *storage = *global;
  const auto index = id & 0xFFFFFFU;
  if (index >= Load<std::uint32_t>(storage, 0x2C)) return nullptr;
  const auto *entries = Load<const void *>(storage, 0x20);
  if (!entries) return nullptr;
  auto *object = Load<void *>(entries, static_cast<std::size_t>(index) * 16 + 8);
  return object && Load<std::uint32_t>(object, 8) == id ? object : nullptr;
}
bool Fail(DraftTenetSources &out, const char *reason) {
  out.failure = reason;
  return false;
}
bool ReadOnce(const TenetSourcesBindings &b, std::uint64_t epoch, DraftTenetSources &out) {
  DraftWindowView window{};
  if (!ReadCurrentRiteCreationWindow12002(b.window, epoch, window))
    return Fail(out, DraftWindowFailureKey(window.failure));
  out.capture_epoch = epoch;
  out.date_raw = window.date_raw;
  out.played_character_id = window.played_character_id;
  out.source_rite_id = window.source_rite_id;
  if (!window.window) { out.available = true; out.failure = "none"; return true; }
  auto *actor = ResolveCoreCharacter(b.window.core, static_cast<std::int32_t>(window.played_character_id));
  if (!actor) return Fail(out, "played_character_unavailable");
  const auto *category = At(window.window, 0x888);
  if (Load<const void *>(category, 0) != window.window)
    return Fail(out, "actual_category_owner_unavailable");
  const auto *exemption = Load<const void *>(category, 0x18);
  out.raw_category_exemption_present = exemption != nullptr;
  if (exemption) {
    std::string key;
    if (!religion::doctrine12002::CopyTenetDefinitionKey12002(exemption, key))
      return Fail(out, "category_exemption_definition_unavailable");
    out.raw_category_exemption_key = std::move(key);
  }
  const auto *database = b.tenet_database_global ? *b.tenet_database_global : nullptr;
  if (!database) return Fail(out, "tenet_source_database_unavailable");
  const auto *sources_array = At(database, 0xEF0);
  const auto *slots_array = At(window.window, 0x778);
  ArrayView sources{}, slots{};
  if (!Array(sources_array, sources)) return Fail(out, "tenet_source_collection_unavailable");
  if (!Array(slots_array, slots)) return Fail(out, "actual_tenet_slots_unavailable");
  const auto *native_default = b.default_tenet_definition_global ? *b.default_tenet_definition_global : nullptr;
  std::vector<const void *> selected;
  for (std::int32_t i = 0; i < slots.count; ++i) {
    const auto *item = At(slots.data, static_cast<std::size_t>(i) * 0x70);
    const auto *definition = Load<const void *>(item, 0x28);
    DraftTenetSourceSlot slot{};
    slot.slot_index = Load<std::uint32_t>(item, 0x20);
    if ((!native_default || definition != native_default) &&
        !religion::doctrine12002::CopyTenetDefinitionKey12002(definition, slot.selected_tenet_key))
      return Fail(out, "selected_tenet_definition_unavailable");
    selected.push_back(definition);
    out.slots.push_back(std::move(slot));
  }
  auto *source_rite = window.source_rite_id ? Resolve(b.rite_storage_global, *window.source_rite_id) : nullptr;
  if (!source_rite) return Fail(out, "source_rite_unavailable");
  const auto source_faith_id = Load<std::uint32_t>(source_rite, 0x4B8);
  auto *source_faith = Resolve(b.faith_storage_global, source_faith_id);
  if (!source_faith) return Fail(out, "source_faith_unavailable");
  const auto main_id = Load<std::uint32_t>(source_faith, 0x98);
  auto *main_rite = Resolve(b.rite_storage_global, main_id);
  if (!main_rite) return Fail(out, "source_main_rite_unavailable");
  out.source_faith_id = source_faith_id;
  out.source_main_rite_id = main_id;
  const auto actor_rite_id = Load<std::uint32_t>(actor, 0xB4);
  auto *actor_rite = Resolve(b.rite_storage_global, actor_rite_id);
  if (!actor_rite) return Fail(out, "actor_rite_unavailable");
  const auto actor_faith_id = Load<std::uint32_t>(actor_rite, 0x4B8);
  auto *actor_faith = Resolve(b.faith_storage_global, actor_faith_id);
  if (!actor_faith) return Fail(out, "actor_faith_unavailable");
  // The native filter uses the existing perk database; a missing database is
  // unavailable rather than an invitation to initialize game registries.
  const auto *perk_database = b.perk_database_global ? *b.perk_database_global : nullptr;
  const auto *prophet = perk_database ? Load<const void *>(perk_database, 0xEF0) : nullptr;
  if (sources.count && !prophet) return Fail(out, "prophet_definition_unavailable");
  const auto *scope = At(window.window, 0xD0);
  const auto *extra = sources.count ? b.actor_extra_collection(actor) : nullptr;
  const auto *perks = sources.count ? b.actor_perks_collection(actor) : nullptr;
  if (sources.count && (!extra || !perks)) return Fail(out, "actor_native_knowledge_collection_unavailable");
  const bool has_prophet = sources.count && b.contains(perks, &prophet);
  for (std::int32_t i = 0; i < sources.count; ++i) {
    const auto *definition = Load<const void *>(sources.data, static_cast<std::size_t>(i) * sizeof(void *));
    DraftTenetSource row{};
    row.source_index = static_cast<std::uint32_t>(i);
    if (!religion::doctrine12002::CopyTenetDefinitionKey12002(definition, row.tenet_key))
      return Fail(out, "tenet_source_definition_unavailable");
    for (const auto *current : selected)
      if (current == definition) { row.already_selected = true; break; }
    row.duplicate_excluded = row.already_selected && definition != exemption;
    row.source_can_materialize = b.source_filter(category, definition);
    row.filtered_out = !row.source_can_materialize;
    row.native_status_raw = b.source_main_rite_status(main_rite, definition);
    row.actor_faith_status_raw = b.actor_faith_status(actor_faith, definition);
    row.native_extra_knowledge = b.contains(extra, &definition);
    row.native_has_prophet = has_prophet;
    row.knowledge = row.native_extra_knowledge || has_prophet;
    row.passed_shown = b.evaluate_trigger(At(definition, 0x658), scope);
    row.passed_selectable_trigger = b.evaluate_trigger(At(definition, 0x4B8), scope);
    row.native_can_pick = row.native_status_raw != 5 &&
      (row.native_status_raw != 0 || row.knowledge) &&
      row.passed_shown && row.passed_selectable_trigger;
    row.final_selectable = row.source_can_materialize && row.native_can_pick;
    out.sources.push_back(std::move(row));
  }
  if (!SameArray(sources_array, sources) || !SameArray(slots_array, slots) ||
      Load<const void *>(category, 0x18) != exemption)
    return Fail(out, "state_changed");
  for (std::int32_t i = 0; i < slots.count; ++i) {
    const auto *item = At(slots.data, static_cast<std::size_t>(i) * 0x70);
    if (Load<const void *>(item, 0x28) != selected[static_cast<std::size_t>(i)] ||
        Load<std::uint32_t>(item, 0x20) != out.slots[static_cast<std::size_t>(i)].slot_index)
      return Fail(out, "state_changed");
  }
  DraftWindowView after{};
  if (!ReadCurrentRiteCreationWindow12002(b.window, epoch, after) || after.window != window.window ||
      after.played_character_id != window.played_character_id || after.date_raw != window.date_raw ||
      after.source_rite_id != window.source_rite_id ||
      *b.tenet_database_global != database ||
      Resolve(b.rite_storage_global, *window.source_rite_id) != source_rite ||
      Load<std::uint32_t>(source_rite, 0x4B8) != source_faith_id ||
      Resolve(b.faith_storage_global, source_faith_id) != source_faith ||
      Load<std::uint32_t>(source_faith, 0x98) != main_id ||
      Resolve(b.rite_storage_global, main_id) != main_rite ||
      Load<std::uint32_t>(actor, 0xB4) != actor_rite_id ||
      Load<std::uint32_t>(actor_rite, 0x4B8) != actor_faith_id)
    return Fail(out, "state_changed");
  out.available = true; out.draft_observed = true;
  out.tenet_gates_complete = true; out.failure = "none";
  return true;
}
std::string Quote(std::string_view value) {
  std::string result = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char c : value) {
    if (c == '\\' || c == '"') { result += '\\'; result += static_cast<char>(c); }
    else if (c < 32) { result += "\\u00"; result += hex[c >> 4]; result += hex[c & 15]; }
    else result += static_cast<char>(c);
  }
  return result + '"';
}
const char *Bool(bool value) { return value ? "true" : "false"; }
std::string ID(const std::optional<std::uint32_t> &value) {
  return value ? std::to_string(*value) : "null";
}
} // namespace

TenetSourcesBindings BindCurrentDraftTenetSources12002(std::uintptr_t base,
    std::string_view sha) noexcept {
  TenetSourcesBindings b{};
  b.window = BindCurrentRiteCreationWindow12002(base, sha);
  if (!b.window.enabled) return b;
  b.tenet_database_global = reinterpret_cast<void *const *>(base + kTenetSourcesDatabaseGlobalRva);
  b.default_tenet_definition_global = reinterpret_cast<void *const *>(base + kTenetSourcesDefaultDefinitionGlobalRva);
  b.rite_storage_global = reinterpret_cast<void *const *>(base + kTenetSourcesRiteStorageGlobalRva);
  b.faith_storage_global = reinterpret_cast<void *const *>(base + kTenetSourcesFaithStorageGlobalRva);
  b.perk_database_global = reinterpret_cast<void *const *>(base + kTenetSourcesPerkDatabaseGlobalRva);
  b.source_filter = reinterpret_cast<TenetSourcesFilter>(base + kTenetSourceNativeFilterRva);
  b.source_main_rite_status = reinterpret_cast<TenetSourcesStatus>(base + kTenetSourceRawStatusRva);
  b.actor_faith_status = reinterpret_cast<TenetSourcesStatus>(base + kTenetSourceActorFaithRawStatusRva);
  b.actor_extra_collection = reinterpret_cast<TenetSourcesCollection>(base + kTenetSourceActorExtraCollectionRva);
  b.actor_perks_collection = reinterpret_cast<TenetSourcesCollection>(base + kTenetSourceActorPerksCollectionRva);
  b.contains = reinterpret_cast<TenetSourcesContains>(base + kTenetSourceContainsRva);
  b.evaluate_trigger = reinterpret_cast<TenetSourcesTrigger>(base + kTenetSourceTriggerRva);
  b.enabled = true;
  return b;
}
bool ReadCurrentDraftTenetSources12002(const TenetSourcesBindings &b,
    std::uint64_t epoch, DraftTenetSources &out) noexcept {
  out = {}; out.capture_epoch = epoch;
  if (!b.enabled || !b.window.enabled || !b.tenet_database_global ||
      !b.rite_storage_global || !b.faith_storage_global || !b.source_filter ||
      !b.source_main_rite_status || !b.actor_faith_status || !b.actor_extra_collection ||
      !b.actor_perks_collection || !b.contains || !b.evaluate_trigger) return false;
  DraftTenetSources value{}; value.capture_epoch = epoch;
  bool ok = false;
#if defined(_WIN32) && defined(_MSC_VER)
  auto guarded = [](const TenetSourcesBindings &binding, std::uint64_t e,
      DraftTenetSources &v) -> bool {
    __try { return ReadOnce(binding, e, v); }
    __except(1) { v.failure = "tenet_sources_native_unavailable"; return false; }
  };
  ok = guarded(b, epoch, value);
#else
  ok = ReadOnce(b, epoch, value);
#endif
  if (ok) out = std::move(value);
  else { out.failure = std::move(value.failure); out.date_raw = value.date_raw;
    out.played_character_id = value.played_character_id; }
  return ok;
}
std::string SerializeCurrentDraftTenetSources12002(const DraftTenetSources &v) {
  std::string slots = "[", sources = "[";
  for (const auto &slot : v.slots) {
    if (slots.size() > 1) slots += ',';
    slots += "{\"slot_index\":" + std::to_string(slot.slot_index) +
      ",\"selected_tenet_key\":" + (slot.selected_tenet_key.empty() ? "null" : Quote(slot.selected_tenet_key)) + '}';
  }
  for (const auto &row : v.sources) {
    if (sources.size() > 1) sources += ',';
    sources += "{\"source_index\":" + std::to_string(row.source_index) +
      ",\"tenet_key\":" + Quote(row.tenet_key) +
      ",\"already_selected\":" + Bool(row.already_selected) +
      ",\"duplicate_excluded\":" + Bool(row.duplicate_excluded) +
      ",\"source_can_materialize\":" + Bool(row.source_can_materialize) +
      ",\"filtered_out\":" + Bool(row.filtered_out) +
      ",\"native_status_raw\":" + std::to_string(row.native_status_raw) +
      ",\"actor_faith_status_raw\":" + std::to_string(row.actor_faith_status_raw) +
      ",\"native_extra_knowledge\":" + Bool(row.native_extra_knowledge) +
      ",\"native_has_prophet\":" + Bool(row.native_has_prophet) +
      ",\"knowledge\":" + Bool(row.knowledge) +
      ",\"passed_shown\":" + Bool(row.passed_shown) +
      ",\"passed_selectable_trigger\":" + Bool(row.passed_selectable_trigger) +
      ",\"native_can_pick\":" + Bool(row.native_can_pick) +
      ",\"final_selectable\":" + Bool(row.final_selectable) + '}';
  }
  return "{\"schema\":\"ck3_12002_current_draft_tenet_sources_v1\",\"game_version\":\"1.20.0.2\",\"executable_sha256\":" +
    Quote(kExecutableSha256) + ",\"scope\":\"actual_current_draft_all_tenet_sources_shared_slot_predicate\",\"available\":" + Bool(v.available) +
    ",\"unavailable_reason\":" + (v.available ? "null" : Quote(v.failure)) +
    ",\"capture_epoch\":" + std::to_string(v.capture_epoch) +
    ",\"date_raw\":" + std::to_string(v.date_raw) +
    ",\"played_character_id\":" + std::to_string(v.played_character_id) +
    ",\"source_rite_id\":" + ID(v.source_rite_id) +
    ",\"source_faith_id\":" + ID(v.source_faith_id) +
    ",\"source_main_rite_id\":" + ID(v.source_main_rite_id) +
    ",\"draft_observed\":" + Bool(v.draft_observed) +
    ",\"tenet_gates_complete\":" + Bool(v.tenet_gates_complete) +
    ",\"raw_category_exemption_present\":" + Bool(v.raw_category_exemption_present) +
    ",\"raw_category_exemption_key\":" + (v.raw_category_exemption_key ? Quote(*v.raw_category_exemption_key) : "null") +
    ",\"slots_share_source_predicate\":true,\"slots\":" + slots +
    "],\"sources\":" + sources + "]}";
}
} // namespace xar::ck3_12002::religion_reform
