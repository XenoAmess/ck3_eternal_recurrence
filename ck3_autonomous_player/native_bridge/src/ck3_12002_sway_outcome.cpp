#include "xar_bridge/ck3_12002_sway_outcome.hpp"
#include "xar_bridge/ck3_12002_sway_state.hpp"

#include <cstring>
#include <limits>
#include <utility>

namespace xar::ck3_12002 {
namespace {

template <typename T> T LoadAt(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(T));
  return value;
}

bool Fail(SwayOutcomeEventV1 &output, const char *reason) {
  output.available = false;
  output.unavailable_reason = reason;
  return false;
}

const game::EventSavedScopeV1 *Named(
    const game::EventWindowContextV1 &context, std::string_view name) noexcept {
  const game::EventSavedScopeV1 *found = nullptr;
  for (const auto &row : context.saved_scopes) {
    if (row.name == name) {
      if (found != nullptr) return nullptr;
      found = &row;
    }
  }
  return found;
}

bool CharacterIs(const game::EventScopeV1 &scope, std::int32_t id) noexcept {
  return scope.type_key == "character" && scope.typed_identity.available &&
         scope.typed_identity.character_id == id;
}

bool ReadSavedScheme(const SwayOutcomeBindings &bindings,
                     const SwayOutcomeRequestV1 &request,
                     std::int32_t name_identifier,
                     void *&scheme_object) noexcept {
  scheme_object = nullptr;
  void *event = CurrentEvent(bindings.event_window.events);
  if (event == nullptr || LoadAt<std::int32_t>(event, 0x1BC) != request.event_instance_id)
    return false;
  const auto *rows = LoadAt<const std::byte *>(event, 0x18);
  const auto capacity = LoadAt<std::int32_t>(event, 0x20);
  const auto count = LoadAt<std::int32_t>(event, 0x24);
  if (count <= 0 || count > 4096 || capacity < count || rows == nullptr)
    return false;
  std::uint32_t id = 0xFFFFFFFFu;
  bool found = false;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *row = rows + static_cast<std::size_t>(index) * 0x18;
    if (LoadAt<std::int32_t>(row, 0) != name_identifier) continue;
    const auto payload = LoadAt<std::uint64_t>(row, 0x10);
    if (found || LoadAt<std::uint16_t>(row, 0x08) != kSwayOutcomeSchemeScopeType ||
        payload > std::numeric_limits<std::uint32_t>::max()) return false;
    id = static_cast<std::uint32_t>(payload);
    found = true;
  }
  if (!found || id != request.scheme_id || bindings.scheme_storage_slot == nullptr)
    return false;
  const void *storage = *bindings.scheme_storage_slot;
  if (storage == nullptr) return false;
  const auto *slots = LoadAt<const std::byte *>(storage, 0x20);
  const auto slot_count = LoadAt<std::int32_t>(storage, 0x2C);
  const auto index = id & 0x00FFFFFFu;
  if (slot_count <= 0 || index >= static_cast<std::uint32_t>(slot_count) || slots == nullptr)
    return false;
  void *object = LoadAt<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 0x08);
  if (object == nullptr || LoadAt<std::uint32_t>(object, 0x10) != id ||
      LoadAt<std::uintptr_t>(object, 0) != bindings.event_window.events.image_base + kSwayInstanceVtableRva12002 ||
      LoadAt<std::int32_t>(object, 0x2C) != request.actor_character_id ||
      LoadAt<std::uint32_t>(object, 0x30) != 0 ||
      LoadAt<std::int32_t>(object, 0x34) != request.target_character_id) return false;
  void *type = LoadAt<void *>(object, 0x20);
  if (type == nullptr || LoadAt<std::uintptr_t>(type, 0) != bindings.event_window.scheme_type_primary_vtable ||
      LoadAt<std::uint64_t>(type, 0x28) != 4 || LoadAt<std::uint32_t>(type, 0x38) != 0x4744624Fu) return false;
  const auto key_capacity = LoadAt<std::uint64_t>(type, 0x30);
  const char *type_key = key_capacity < 16 ? static_cast<const char *>(type) + 0x18 : LoadAt<const char *>(type, 0x18);
  if (key_capacity < 4 || type_key == nullptr || std::memcmp(type_key, "sway", 4) != 0) return false;
  scheme_object = object;
  return true;
}

bool ReadSwayModifier(const SwayOutcomeBindings &bindings, void *recipient,
                      std::uint32_t actor_id, const char *key,
                      SwayOpinionModifierV1 &output) noexcept {
  output = {};
  const auto &b = bindings.opinion_modifiers;
  if (!b.enabled || b.modifier_database_slot == nullptr || b.lookup_modifier == nullptr ||
      b.find_group == nullptr || b.sum_modifier == nullptr ||
      bindings.event_window.hash_stable_key == nullptr) return false;
  void *database = *b.modifier_database_slot;
  if (database == nullptr) return false;
  const auto size = static_cast<std::uint32_t>(std::strlen(key));
  const auto hash = static_cast<std::uint32_t>(bindings.event_window.hash_stable_key(database, key, size));
  void *definition = b.lookup_modifier(database, hash);
  if (definition == nullptr || LoadAt<std::uintptr_t>(definition, 0) != b.modifier_primary_vtable ||
      LoadAt<std::uintptr_t>(definition, 0x88) != b.modifier_secondary_vtable ||
      LoadAt<std::uint32_t>(definition, 0x14) != hash ||
      LoadAt<std::uint32_t>(definition, 0x38) != 0x4744624Fu ||
      LoadAt<std::uint64_t>(definition, 0x28) != size) return false;
  const auto capacity = LoadAt<std::uint64_t>(definition, 0x30);
  const char *actual_key = capacity < 16 ? static_cast<const char *>(definition) + 0x18
                                      : LoadAt<const char *>(definition, 0x18);
  if (capacity < size || actual_key == nullptr || std::memcmp(actual_key, key, size) != 0) return false;
  void *extension = LoadAt<void *>(recipient, 0x1B0);
  void *group = extension == nullptr ? nullptr : b.find_group(extension, actor_id);
  if (group != nullptr) {
    void *rows = LoadAt<void *>(group, 8);
    const auto count = LoadAt<std::int32_t>(group, 0x14);
    if (count < 0 || count > (1 << 20) || (count != 0 && rows == nullptr)) return false;
    for (std::int32_t index = 0; index < count; ++index) {
      void *active = LoadAt<void *>(rows, static_cast<std::size_t>(index) * 8);
      if (active == nullptr) continue;
      const auto vtable = LoadAt<std::uintptr_t>(active, 0);
      if (vtable != b.active_opinion_vtable && vtable != b.temporary_opinion_vtable) return false;
      if (LoadAt<void *>(active, 8) == definition) output.present = true;
    }
    if (output.present) output.value = b.sum_modifier(group, definition);
  }
  if (*b.modifier_database_slot != database || b.lookup_modifier(database, hash) != definition) return false;
  output.observed = true;
  return true;
}

bool ProjectOption(std::string_view event_key, const game::EventWindowOptionV1 &source,
                   SwayOutcomeOptionV1 &output) {
  output.rendered_index = source.rendered_index;
  output.native_option_index = source.native_option_index;
  output.shown = source.shown;
  output.enabled = source.enabled;
  output.resolved_name = source.resolved_name;
  const auto index = source.native_option_index;
  if (event_key == "sway_outcome.1001" || event_key == "sway_outcome.1002") {
    if (index != 0 && index != 1) return false;
    output.sway_end_effect = true;
    output.deterministic = index == 1;
    output.authored_sway_points_on_success = index == 1 ? 30 : 50;
    output.authored_sway_points_on_failure = index == 1 ? 30 : 0;
    output.authored_sway_modifier_selection = index == 1 ? "scheme_sway_opinion" : "conditional_sway_or_compelled";
  } else if (event_key == "sway_outcome.1003") {
    if (index < 0 || index > 2) return false;
    output.sway_end_effect = true;
    output.deterministic = index == 2;
    output.authored_sway_points_on_success = index == 0 ? 20 : index == 1 ? 15 : 0;
    output.authored_sway_points_on_failure = index == 2 ? 0 : -10;
    output.authored_sway_modifier_selection = index == 2 ? "none" : "conditional_sway_or_compelled";
  } else if (event_key == "sway_outcome.1004") {
    if (index != 0 && index != 1) return false;
    output.deterministic = true;
    output.end_scheme_effect = true;
  } else if (event_key == "sway_outcome.2001" || event_key == "sway_outcome.2002") {
    if (index != 0) return false;
    output.deterministic = true;
    output.end_scheme_effect = true;
    output.authored_blocker_points = -10;
  } else return false;
  return true;
}

std::string Quote(std::string_view value) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char ch : value) {
    if (ch == '"' || ch == '\\') { out.push_back('\\'); out.push_back(static_cast<char>(ch)); }
    else if (ch < 0x20) { out += "\\u00"; out.push_back(hex[ch >> 4]); out.push_back(hex[ch & 15]); }
    else out.push_back(static_cast<char>(ch));
  }
  return out + '"';
}
const char *Boolean(bool value) noexcept { return value ? "true" : "false"; }

std::string SerializeModifier(const SwayOpinionModifierV1 &value) {
  std::string wire = "{\"observed\":";
  wire += Boolean(value.observed);
  wire += ",\"present\":";
  wire += Boolean(value.present);
  wire += ",\"value\":";
  wire += value.value ? std::to_string(*value.value) : "null";
  return wire + '}';
}

} // namespace

SwayOutcomeBindings BindSwayOutcomeImage(std::uintptr_t image_base,
                                        std::string_view sha256) noexcept {
  SwayOutcomeBindings bindings{};
  bindings.event_window = BindEventWindowImage(image_base, sha256);
  if (!bindings.event_window.events.core.enabled) return bindings;
  bindings.scheme_storage_slot = reinterpret_cast<void **>(image_base + kSwayOutcomeSchemeStorageSlotRva);
  bindings.target_opinion = reinterpret_cast<SwayOutcomeTargetOpinion>(image_base + kSwayOutcomeTargetOpinionRva);
  bindings.opinion_modifiers = BindGiftOpinionImage12002(image_base, sha256);
  return bindings;
}

bool ReadSwayOutcomeOpinionV1(const SwayOutcomeBindings &bindings,
                             std::int32_t actor_id, std::int32_t target_id,
                             SwayOutcomeOpinionV1 &output) noexcept {
  output = {};
  output.actor_character_id = actor_id;
  output.target_character_id = target_id;
  try {
    if (!bindings.event_window.events.core.enabled || bindings.target_opinion == nullptr ||
        actor_id <= 0 || target_id <= 0 || actor_id == target_id) {
      output.unavailable_reason = "sway_opinion_bindings_or_pair_invalid";
      return false;
    }
    void *actor = ResolveCoreCharacter(bindings.event_window.events.core, actor_id);
    void *recipient = ResolveCoreCharacter(bindings.event_window.events.core, target_id);
    if (actor == nullptr || recipient == nullptr) {
      output.unavailable_reason = "sway_opinion_character_unavailable";
      return false;
    }
    const auto opinion = bindings.target_opinion(recipient, actor);
    SwayOpinionModifierV1 sway{}, blocker{}, sway_after{}, blocker_after{};
    if (!ReadSwayModifier(bindings, recipient, static_cast<std::uint32_t>(actor_id), "scheme_sway_opinion", sway) ||
        !ReadSwayModifier(bindings, recipient, static_cast<std::uint32_t>(actor_id), "sway_blocker_opinion", blocker) ||
        !ReadSwayModifier(bindings, recipient, static_cast<std::uint32_t>(actor_id), "scheme_sway_opinion", sway_after) ||
        !ReadSwayModifier(bindings, recipient, static_cast<std::uint32_t>(actor_id), "sway_blocker_opinion", blocker_after) ||
        sway != sway_after || blocker != blocker_after ||
        bindings.target_opinion(recipient, actor) != opinion ||
        ResolveCoreCharacter(bindings.event_window.events.core, actor_id) != actor ||
        ResolveCoreCharacter(bindings.event_window.events.core, target_id) != recipient) {
      output.unavailable_reason = "sway_opinion_source_unavailable_or_changed";
      return false;
    }
    output.available = true;
    output.target_opinion_of_actor = opinion;
    output.scheme_sway_opinion = sway;
    output.sway_blocker_opinion = blocker;
    return true;
  } catch (...) {
    output.unavailable_reason = "sway_opinion_internal_error";
    return false;
  }
}

std::string SerializeSwayOutcomeOpinionV1(const SwayOutcomeOpinionV1 &row,
                                        std::uint64_t revision, std::int32_t date_raw) {
  std::string out = "{\"schema\":\"xar.ck3.sway-outcome-opinion-v1\",\"build\":\"1.20.0.2\",\"available\":";
  out += Boolean(row.available);
  out += ",\"unavailable_reason\":" + Quote(row.unavailable_reason);
  out += ",\"snapshot_revision\":" + std::to_string(revision);
  out += ",\"date_raw\":" + std::to_string(date_raw);
  out += ",\"actor_character_id\":" + std::to_string(row.actor_character_id);
  out += ",\"target_character_id\":" + std::to_string(row.target_character_id);
  out += ",\"target_opinion_of_actor\":";
  out += row.available ? std::to_string(row.target_opinion_of_actor) : "null";
  out += ",\"scheme_sway_opinion\":" + SerializeModifier(row.scheme_sway_opinion);
  out += ",\"sway_blocker_opinion\":" + SerializeModifier(row.sway_blocker_opinion);
  return out + ",\"instance_terminal_outcome_observed\":false,\"cancel_outcome_observed\":false}";
}

std::string SerializeSwayOutcomeOpinionResponseV1(
    const SwayOutcomeOpinionV1 &row, std::uint64_t revision,
    std::int32_t date_raw, std::string_view request_id) {
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
      Quote(request_id) + ",\"ok\":true,\"result\":{\"step\":" +
      Quote(kSwayOutcomeOpinionStepV1) +
      ",\"accepted\":true,\"status\":" +
      Quote(row.available ? "available" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,"
      "\"sway_outcome_opinion\":" +
      SerializeSwayOutcomeOpinionV1(row, revision, date_raw) +
      ",\"backend_id\":\"native-headless\"}}";
}

bool ReadSwayOutcomeEventV1(const SwayOutcomeBindings &bindings,
                           const SwayOutcomeRequestV1 &request,
                           SwayOutcomeEventV1 &output) noexcept {
  output = {};
  output.request = request;
  try {
    if (!bindings.event_window.events.core.enabled || bindings.scheme_storage_slot == nullptr ||
        bindings.target_opinion == nullptr) return Fail(output, "sway_outcome_bindings_unavailable");
    if (request.expected_revision == 0 || request.event_instance_id < 0 ||
        request.actor_character_id < 0 || request.target_character_id < 0 ||
        request.scheme_id == 0xFFFFFFFFu) return Fail(output, "sway_outcome_request_invalid");
    game::EventWindowContextV1 before{};
    if (ReadEventWindowContextV1(bindings.event_window, request.expected_revision,
                                request.event_instance_id, before) != game::ReadEventWindowContextResultV1::available)
      return Fail(output, "sway_outcome_current_event_unavailable");
    const auto &key = before.event_definition_key;
    const bool success = key == "sway_outcome.1001" || key == "sway_outcome.1002" ||
                         key == "sway_outcome.1003" || key == "sway_outcome.1004";
    const bool failure = key == "sway_outcome.2001" || key == "sway_outcome.2002";
    if (!success && !failure) return Fail(output, "sway_outcome_event_not_supported");
    const auto *owner = Named(before, "owner");
    const auto *target = Named(before, "target");
    const auto *scheme = Named(before, "scheme");
    if (!before.event_definition_identity_ready || !before.root_scope_ready ||
        !before.saved_scopes_ready || !before.option_presentation_ready ||
        !before.root_scope || !CharacterIs(*before.root_scope, request.actor_character_id) ||
        owner == nullptr || !CharacterIs(owner->scope, request.actor_character_id) ||
        target == nullptr || !CharacterIs(target->scope, request.target_character_id) ||
        scheme == nullptr || scheme->scope.type_key != "scheme" ||
        scheme->scope.raw_type_index != kSwayOutcomeSchemeScopeType)
      return Fail(output, "sway_outcome_scope_join_mismatch");
    void *scheme_before = nullptr;
    if (!ReadSavedScheme(bindings, request, scheme->name_identifier, scheme_before))
      return Fail(output, "sway_outcome_scheme_join_mismatch");
    void *actor = ResolveCoreCharacter(bindings.event_window.events.core, request.actor_character_id);
    void *recipient = ResolveCoreCharacter(bindings.event_window.events.core, request.target_character_id);
    if (actor == nullptr || recipient == nullptr) return Fail(output, "sway_outcome_character_unavailable");
    const auto opinion = bindings.target_opinion(recipient, actor);
    SwayOutcomeEventV1 candidate{};
    candidate.request = request;
    candidate.date_raw = before.date_raw;
    candidate.event_definition_key = key;
    if (!ReadSwayModifier(bindings, recipient, static_cast<std::uint32_t>(request.actor_character_id),
                          "scheme_sway_opinion", candidate.scheme_sway_opinion) ||
        !ReadSwayModifier(bindings, recipient, static_cast<std::uint32_t>(request.actor_character_id),
                          "sway_blocker_opinion", candidate.sway_blocker_opinion))
      return Fail(output, "sway_outcome_modifier_unavailable");
    candidate.authored_immediate_sway_points = key == "sway_outcome.1003" ? 30 :
                                              key == "sway_outcome.1004" ? 20 : 0;
    candidate.authored_immediate_modifier_selection = key == "sway_outcome.1003" ? "conditional_sway_or_compelled" :
                                                      key == "sway_outcome.1004" ? "scheme_sway_opinion" : "none";
    for (const auto &source : before.options) {
      SwayOutcomeOptionV1 option{};
      if (!ProjectOption(key, source, option)) return Fail(output, "sway_outcome_native_option_unknown");
      candidate.options.push_back(std::move(option));
    }
    if (candidate.options.empty()) return Fail(output, "sway_outcome_options_unavailable");
    game::EventWindowContextV1 after{};
    void *scheme_after = nullptr;
    SwayOpinionModifierV1 sway_after{}, blocker_after{};
    if (ReadEventWindowContextV1(bindings.event_window, request.expected_revision,
                                request.event_instance_id, after) != game::ReadEventWindowContextResultV1::available ||
        after != before || !ReadSavedScheme(bindings, request, scheme->name_identifier, scheme_after) ||
        scheme_after != scheme_before ||
        bindings.target_opinion(recipient, actor) != opinion ||
        !ReadSwayModifier(bindings, recipient, static_cast<std::uint32_t>(request.actor_character_id),
                          "scheme_sway_opinion", sway_after) ||
        !ReadSwayModifier(bindings, recipient, static_cast<std::uint32_t>(request.actor_character_id),
                          "sway_blocker_opinion", blocker_after) ||
        sway_after != candidate.scheme_sway_opinion || blocker_after != candidate.sway_blocker_opinion)
      return Fail(output, "sway_outcome_source_changed");
    candidate.available = true;
    candidate.exact_scope_join_ready = true;
    candidate.phase_result_observed = true;
    candidate.phase_result = success ? SwayPhaseResultV1::success : SwayPhaseResultV1::failure;
    candidate.target_opinion_observed = true;
    candidate.target_opinion_of_actor = opinion;
    output = std::move(candidate);
    return true;
  } catch (...) { return Fail(output, "sway_outcome_internal_error"); }
}

std::string SerializeSwayOutcomeEventV1(const SwayOutcomeEventV1 &row) {
  std::string out = "{\"schema\":\"xar.ck3.sway-outcome-event-v1\",\"build\":\"1.20.0.2\",\"available\":";
  out += Boolean(row.available);
  out += ",\"unavailable_reason\":" + Quote(row.unavailable_reason);
  out += ",\"snapshot_revision\":" + std::to_string(row.request.expected_revision);
  out += ",\"event_instance_id\":" + std::to_string(row.request.event_instance_id);
  out += ",\"actor_character_id\":" + std::to_string(row.request.actor_character_id);
  out += ",\"target_character_id\":" + std::to_string(row.request.target_character_id);
  out += ",\"scheme_instance_id\":" + std::to_string(row.request.scheme_id);
  out += ",\"date_raw\":" + std::to_string(row.date_raw);
  out += ",\"event_definition_key\":" + Quote(row.event_definition_key);
  out += ",\"exact_scope_join_ready\":"; out += Boolean(row.exact_scope_join_ready);
  out += ",\"phase_result_observed\":"; out += Boolean(row.phase_result_observed);
  out += ",\"phase_result\":" + Quote(row.phase_result == SwayPhaseResultV1::success ? "success" :
                                       row.phase_result == SwayPhaseResultV1::failure ? "failure" : "unknown");
  out += ",\"target_opinion_observed\":"; out += Boolean(row.target_opinion_observed);
  out += ",\"target_opinion_of_actor\":";
  out += row.target_opinion_observed ? std::to_string(row.target_opinion_of_actor) : "null";
  out += ",\"scheme_sway_opinion\":" + SerializeModifier(row.scheme_sway_opinion);
  out += ",\"sway_blocker_opinion\":" + SerializeModifier(row.sway_blocker_opinion);
  out += ",\"authored_immediate_sway_points\":" + std::to_string(row.authored_immediate_sway_points);
  out += ",\"authored_immediate_modifier_selection\":" + Quote(row.authored_immediate_modifier_selection);
  out += ",\"instance_terminal_outcome_observed\":"; out += Boolean(row.instance_terminal_outcome_observed);
  out += ",\"cancel_outcome_observed\":"; out += Boolean(row.cancel_outcome_observed);
  out += ",\"option_effects_are_projection\":true,\"options\":[";
  bool first = true;
  for (const auto &option : row.options) {
    if (!first) out += ',';
    first = false;
    out += "{\"rendered_index\":" + std::to_string(option.rendered_index);
    out += ",\"native_option_index\":" + std::to_string(option.native_option_index);
    out += ",\"shown\":"; out += Boolean(option.shown);
    out += ",\"enabled\":"; out += Boolean(option.enabled);
    out += ",\"deterministic\":"; out += Boolean(option.deterministic);
    out += ",\"end_scheme_effect\":"; out += Boolean(option.end_scheme_effect);
    out += ",\"sway_end_effect\":"; out += Boolean(option.sway_end_effect);
    out += ",\"authored_sway_points_on_success\":" + std::to_string(option.authored_sway_points_on_success);
    out += ",\"authored_sway_points_on_failure\":" + std::to_string(option.authored_sway_points_on_failure);
    out += ",\"authored_sway_modifier_selection\":" + Quote(option.authored_sway_modifier_selection);
    out += ",\"authored_blocker_points\":" + std::to_string(option.authored_blocker_points);
    out += ",\"resolved_name\":" + Quote(option.resolved_name) + '}';
  }
  return out + "]}";
}

} // namespace xar::ck3_12002
