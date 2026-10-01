#include "xar_bridge/religion_doctrine12002_selection.hpp"
#include <cstring>

namespace xar::ck3_12002::religion::doctrine12002 {
namespace {
namespace reform = religion_reform;
template<class T> T Load(const void *pointer, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(pointer) + offset, sizeof(value));
  return value;
}
const std::byte *At(const void *pointer, std::size_t offset) {
  return static_cast<const std::byte *>(pointer) + offset;
}
bool Fail(CurrentDoctrineSelection &output, const char *reason) {
  output.failure = reason; return false;
}
bool Observe(const reform::DraftChoiceBindings &bindings, const reform::DraftChoices &popup,
    std::uint64_t epoch, CurrentDoctrineSelection &output) {
  output.date_raw = popup.date_raw; output.played_character_id = popup.played_character_id;
  output.source_rite_id = popup.source_rite_id;
  if (!popup.available) { output.failure = popup.failure; return false; }
  if (popup.capture_epoch != epoch) return Fail(output, "popup_epoch_changed");
  reform::DraftWindowView view{};
  if (!reform::ReadCurrentRiteCreationWindow12002(bindings.window, epoch, view))
    return Fail(output, reform::DraftWindowFailureKey(view.failure));
  if (!view.window || !popup.draft_observed) return Fail(output, "current_draft_not_visible");
  if (view.date_raw != popup.date_raw || view.played_character_id != popup.played_character_id ||
      view.source_rite_id != popup.source_rite_id) return Fail(output, "state_changed");
  const auto *collection = At(view.window,
      reform::kDraftDoctrineCategoryOffset + reform::kCategoryDoctrineArrayOffset);
  const auto *items = Load<const std::byte *>(collection, 0);
  const auto count = Load<std::int32_t>(collection, 0xC);
  const auto capacity = Load<std::int32_t>(collection, 8);
  if (count < 0 || count > capacity || count > 8192 || (count && !items))
    return Fail(output, "popup_collection_unavailable");
  if (static_cast<std::size_t>(count) != popup.doctrines.size()) return Fail(output, "state_changed");
  const auto *scope = At(view.window, reform::kDraftTopScopeOffset);
  for (std::int32_t index = 0; index < count; ++index) {
    const auto &raw = popup.doctrines[static_cast<std::size_t>(index)];
    if (raw.popup_index != static_cast<std::uint32_t>(index)) return Fail(output, "state_changed");
    const auto *item = items + static_cast<std::size_t>(index) * reform::kDoctrineItemStride;
    const auto *definition = Load<const void *>(item, reform::kChoiceDefinitionOffset);
    DoctrineRow identity{};
    if (!CopyDoctrineDefinition12002(definition, identity))
      return Fail(output, "doctrine_definition_unavailable");
    if (raw.doctrine_key != identity.doctrine_key || raw.group_key != identity.group_key)
      return Fail(output, "state_changed");
    DoctrineSelectionRow row{}; row.choice = raw;
    row.native_should_display = bindings.evaluate_trigger(At(definition, kDoctrineShownTriggerOffset), scope);
    row.selectable = row.native_should_display && raw.native_can_pick && raw.button_enabled;
    if (!row.native_should_display) row.selection_blocker = "hidden_by_native_should_display";
    else if (!raw.native_can_pick) row.selection_blocker = "blocked_by_native_can_pick";
    else if (!raw.button_enabled) row.selection_blocker = "doctrine_not_known_and_no_prophet";
    if (Load<const void *>(item, reform::kChoiceDefinitionOffset) != definition)
      return Fail(output, "state_changed");
    if (row.selectable) output.selectable_doctrine_keys.push_back(raw.doctrine_key);
    output.rows.push_back(std::move(row));
  }
  reform::DraftWindowView after{};
  if (Load<const std::byte *>(collection, 0) != items || Load<std::int32_t>(collection, 0xC) != count ||
      !reform::ReadCurrentRiteCreationWindow12002(bindings.window, epoch, after) ||
      after.window != view.window || after.date_raw != view.date_raw ||
      after.played_character_id != view.played_character_id || after.source_rite_id != view.source_rite_id)
    return Fail(output, "state_changed");
  output.available = true; output.popup_observed = true; output.selection_ready = true;
  output.failure = "none"; return true;
}
std::string Quote(std::string_view value) {
  std::string output = "\""; constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char byte : value) {
    if (byte == '\\' || byte == '"') { output += '\\'; output += static_cast<char>(byte); }
    else if (byte < 32) { output += "\\u00"; output += hex[byte >> 4]; output += hex[byte & 15]; }
    else output += static_cast<char>(byte);
  }
  return output + '"';
}
const char *Bool(bool value) { return value ? "true" : "false"; }
std::string OptionalBool(const std::optional<bool> &value) { return value ? Bool(*value) : "null"; }
} // namespace

bool ObserveCurrentDraftDoctrineSelection12002(const reform::DraftChoiceBindings &bindings,
    const reform::DraftChoices &popup, std::uint64_t epoch, CurrentDoctrineSelection &output) noexcept {
  output = {}; output.capture_epoch = epoch;
  if (!bindings.window.enabled || !bindings.evaluate_trigger) return false;
  CurrentDoctrineSelection candidate{}; candidate.capture_epoch = epoch;
  bool ok = false;
#if defined(_WIN32) && defined(_MSC_VER)
  auto guarded = [](const reform::DraftChoiceBindings &binding, const reform::DraftChoices &input,
      std::uint64_t capture, CurrentDoctrineSelection &value) -> bool {
    __try { return Observe(binding, input, capture, value); }
    __except (1) { value.failure = "popup_layout_unavailable"; return false; }
  };
  ok = guarded(bindings, popup, epoch, candidate);
#else
  ok = Observe(bindings, popup, epoch, candidate);
#endif
  if (ok) output = std::move(candidate);
  else {
    output.failure = std::move(candidate.failure); output.date_raw = candidate.date_raw;
    output.played_character_id = candidate.played_character_id; output.source_rite_id = candidate.source_rite_id;
  }
  return ok;
}
bool ReadCurrentDraftDoctrineSelection12002(const reform::DraftChoiceBindings &bindings,
    std::uint64_t epoch, CurrentDoctrineSelection &output) noexcept {
  reform::DraftChoices popup{};
  reform::ReadCurrentDraftChoices12002(bindings, epoch, popup);
  return ObserveCurrentDraftDoctrineSelection12002(bindings, popup, epoch, output);
}
std::string SerializeCurrentDraftDoctrineSelection12002(const CurrentDoctrineSelection &value) {
  std::string rows = "[", keys = "[";
  for (const auto &row : value.rows) {
    if (rows.size() > 1) rows += ',';
    const auto &choice = row.choice;
    rows += "{\"doctrine_key\":" + Quote(choice.doctrine_key) + ",\"group_key\":" + Quote(choice.group_key) +
        ",\"popup_index\":" + std::to_string(choice.popup_index) +
        ",\"native_should_display\":" + Bool(row.native_should_display) +
        ",\"native_can_pick\":" + Bool(choice.native_can_pick) +
        ",\"native_knows_doctrine\":" + OptionalBool(choice.native_knows_doctrine) +
        ",\"native_has_prophet\":" + OptionalBool(choice.native_has_prophet) +
        ",\"button_enabled\":" + Bool(choice.button_enabled) +
        ",\"selectable\":" + Bool(row.selectable) +
        ",\"selection_blocker\":" + Quote(row.selection_blocker) + '}';
  }
  for (const auto &key : value.selectable_doctrine_keys) {
    if (keys.size() > 1) keys += ',';
    keys += Quote(key);
  }
  return "{\"schema\":\"ck3_12002_current_draft_doctrine_selection_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"scope\":\"already_materialized_current_popup_candidates\",\"available\":" + Bool(value.available) +
      ",\"unavailable_reason\":" + (value.available ? "null" : Quote(value.failure)) +
      ",\"popup_observed\":" + Bool(value.popup_observed) +
      ",\"selection_ready\":" + Bool(value.selection_ready) +
      ",\"capture_epoch\":" + std::to_string(value.capture_epoch) +
      ",\"date_raw\":" + std::to_string(value.date_raw) +
      ",\"played_character_id\":" + std::to_string(value.played_character_id) +
      ",\"source_rite_id\":" + (value.source_rite_id ? std::to_string(*value.source_rite_id) : "null") +
      ",\"rows\":" + rows + "],\"selectable_doctrine_keys\":" + keys + "]}";
}
} // namespace xar::ck3_12002::religion::doctrine12002
