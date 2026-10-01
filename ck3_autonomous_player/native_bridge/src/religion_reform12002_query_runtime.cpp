#include "xar_bridge/religion_reform12002_query_runtime.hpp"

#include <utility>

namespace xar::ck3_12002::religion_reform::query {
namespace {
bool Fail(Observation &out, const char *reason) {
  out.failure = reason;
  return false;
}

bool MatchesFrame(std::int32_t date, std::int32_t actor,
                  const CoreSnapshotPrefix &frame) noexcept {
  return date == frame.clock.date_raw && actor == frame.played_character_id;
}

bool ReadOnce(const Bindings &b, std::uint64_t epoch, Observation &out) {
  CoreSnapshotPrefix before{};
  if (!ReadCoreSnapshot(b.core, before) || !before.map_ready ||
      !before.has_played_character || !before.played_character_alive)
    return Fail(out, "played_character_unavailable");
  out.capture_epoch = epoch;
  out.date_raw = before.clock.date_raw;
  out.played_character_id = before.played_character_id;
  if (!before.clock.paused) return Fail(out, "frame_not_paused");

  auto context_bindings = b.context;
  context_bindings.core = b.core;
  ReadPlayedReligionContext12002(context_bindings, epoch, out.context);

  auto rite_bindings = b.rite_model;
  rite_bindings.core = b.core;
  ReadPlayedRiteModel12002(rite_bindings, epoch, out.rite_model);

  // Reuse the exact current-character Faith getter. Character+0xB4 is a Rite
  // reference, so it must never be substituted for this Faith identity.
  const auto expected_faith = out.context.available ? out.context.faith_id
      : (out.rite_model.available ? out.rite_model.faith_id : std::nullopt);
  if (expected_faith && context_bindings.character_faith) {
    auto *actor = ResolveCoreCharacter(b.core, before.played_character_id);
    auto *faith = actor ? context_bindings.character_faith(actor) : nullptr;
    out.main_rite = ReadFaithMainRiteUnreformed12002(
        b.main_rite, faith, *expected_faith);
  } else {
    out.main_rite.status = MainRiteStatus::faith_unavailable;
  }

  auto window_bindings = b.window;
  window_bindings.core = b.core;
  ReadCurrentRiteCreationWindow12002(window_bindings, epoch, out.current_window);
  if (out.current_window.available && out.current_window.window) {
    const auto &window = out.current_window;
    if (!MatchesFrame(window.date_raw,
                      static_cast<std::int32_t>(window.played_character_id), before))
      return Fail(out, "state_changed");
    CurrentDraftView draft{};
    draft.window = const_cast<void *>(window.window);
    draft.played_character_id = before.played_character_id;
    draft.capture_epoch = epoch;
    draft.date_raw = before.clock.date_raw;
    ReadCurrentRiteCreationCosts12002(b.costs, draft, out.draft_costs);
    ReadCurrentDraftEligibility12002(
        b.eligibility, window.window, window.played_character_id,
        out.draft_eligibility);
    auto choices_bindings = b.choices;
    choices_bindings.window = window_bindings;
    ReadCurrentDraftChoices12002(choices_bindings, epoch, out.popup_choices);
    religion::doctrine12002::ObserveCurrentDraftDoctrineSelection12002(
        choices_bindings, out.popup_choices, epoch, out.current_doctrine_selection);

    // Cost and final-gate readers consume the actual pointer returned by the
    // window observer; confirm that the popup reader saw that same draft.
    DraftWindowView after_window{};
    if (!ReadCurrentRiteCreationWindow12002(window_bindings, epoch, after_window) ||
        after_window.window != window.window ||
        after_window.played_character_id != window.played_character_id ||
        after_window.source_rite_id != window.source_rite_id ||
        after_window.date_raw != window.date_raw)
      return Fail(out, "state_changed");
  } else {
    out.draft_costs.capture_epoch = epoch;
    out.draft_costs.date_raw = before.clock.date_raw;
    out.draft_costs.played_character_id = before.played_character_id;
    out.draft_costs.failure = CostFailure::draft_unavailable;
    out.draft_eligibility.failure = EligibilityFailure::current_window_unavailable;
    out.popup_choices.capture_epoch = epoch;
    out.popup_choices.date_raw = before.clock.date_raw;
    out.popup_choices.played_character_id =
        static_cast<std::uint32_t>(before.played_character_id);
    out.popup_choices.failure = !out.current_window.available
        ? DraftWindowFailureKey(out.current_window.failure)
        : (out.current_window.present ? "current_window_hidden"
                                      : "current_window_absent");
    out.current_doctrine_selection.capture_epoch = epoch;
    out.current_doctrine_selection.date_raw = before.clock.date_raw;
    out.current_doctrine_selection.played_character_id =
        static_cast<std::uint32_t>(before.played_character_id);
    out.current_doctrine_selection.failure = out.popup_choices.failure;
  }

  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(b.core, after) || !after.map_ready ||
      !after.has_played_character || !after.played_character_alive ||
      !after.clock.paused ||
      !MatchesFrame(after.clock.date_raw, after.played_character_id, before) ||
      (out.context.available &&
       !MatchesFrame(out.context.date_raw, out.context.played_character_id, before)) ||
      (out.rite_model.available &&
       !MatchesFrame(out.rite_model.date_raw, out.rite_model.played_character_id, before)))
    return Fail(out, "state_changed");

  out.available = out.context.available || out.rite_model.available ||
      out.main_rite.status == MainRiteStatus::observed || out.current_window.available;
  out.failure = out.available ? "none" : "current_observations_unavailable";
  return out.available;
}

bool ReadGuarded(const Bindings &b, std::uint64_t epoch, Observation &out) {
#if defined(_WIN32) && defined(_MSC_VER)
  __try { return ReadOnce(b, epoch, out); }
  __except (1) { out.failure = "native_observation_unavailable"; return false; }
#else
  return ReadOnce(b, epoch, out);
#endif
}

std::string Quote(std::string_view value) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char c : value) {
    if (c == '\\' || c == '"') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 32) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += static_cast<char>(c);
  }
  return out + '"';
}

const char *Boolean(bool value) noexcept { return value ? "true" : "false"; }
std::string OptionalBoolean(const std::optional<bool> &value) {
  return value ? Boolean(*value) : "null";
}
const char *MainRiteReason(MainRiteStatus status) noexcept {
  switch (status) {
  case MainRiteStatus::observed: return "none";
  case MainRiteStatus::bindings_unavailable: return "bindings_unavailable";
  case MainRiteStatus::faith_unavailable: return "faith_unavailable";
  case MainRiteStatus::main_rite_unavailable: return "main_rite_unavailable";
  case MainRiteStatus::state_changed: return "state_changed";
  }
  return "unknown";
}

std::string SerializeMainRite(const MainRiteUnreformed &value) {
  const bool observed = value.status == MainRiteStatus::observed;
  return "{\"available\":" + std::string(Boolean(observed)) +
      ",\"unavailable_reason\":" + (observed ? "null" : Quote(MainRiteReason(value.status))) +
      ",\"faith_id\":" + (value.faith_id == kAbsentFullReference
          ? "null" : std::to_string(value.faith_id)) +
      ",\"main_rite_id\":" + (value.main_rite_id == kAbsentFullReference
          ? "null" : std::to_string(value.main_rite_id)) +
      ",\"is_unreformed\":" + (observed ? Boolean(value.is_unreformed) : "null") +
      ",\"final_reform_legality_observed\":false}";
}

std::string SerializePopup(const DraftChoices &value) {
  const bool observed = value.available && value.draft_observed;
  std::string doctrines = observed ? "[" : "null";
  std::string tenets = observed ? "[" : "null";
  if (observed) {
    for (const auto &row : value.doctrines) {
      if (doctrines.size() > 1) doctrines += ',';
      doctrines += "{\"doctrine_key\":" + Quote(row.doctrine_key) +
          ",\"group_key\":" + Quote(row.group_key) +
          ",\"popup_index\":" + std::to_string(row.popup_index) +
          ",\"native_raw_trigger_gates_pass\":" + Boolean(row.native_can_pick) +
          ",\"native_knows_doctrine\":" + OptionalBoolean(row.native_knows_doctrine) +
          ",\"native_has_prophet\":" + OptionalBoolean(row.native_has_prophet) +
          ",\"native_observed_knowledge_button_gate\":" + Boolean(row.button_enabled) +
          ",\"final_can_pick\":null,\"final_choice_legality_readiness\":false}";
    }
    for (const auto &row : value.tenets) {
      if (tenets.size() > 1) tenets += ',';
      tenets += "{\"tenet_key\":" + Quote(row.tenet_key) +
          ",\"popup_group_index\":" + std::to_string(row.popup_group_index) +
          ",\"popup_item_index\":" + std::to_string(row.popup_item_index) +
          ",\"native_pick_source\":" + std::to_string(row.native_pick_source) +
          ",\"native_item_helper_can_pick\":" + Boolean(row.native_can_pick) +
          ",\"final_can_pick\":null,\"final_choice_legality_readiness\":false}";
    }
    doctrines += ']';
    tenets += ']';
  }
  return "{\"available\":" + std::string(Boolean(observed)) +
      ",\"unavailable_reason\":" + (observed ? "null" : Quote(value.failure)) +
      ",\"scope\":\"already_materialized_current_popup_candidates\""
      ",\"collection_readiness\":" + Boolean(observed) +
      ",\"final_choice_legality_readiness\":false,\"doctrines\":" + doctrines +
      ",\"tenets\":" + tenets + '}';
}
} // namespace

Bindings BindReformQueryImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  b.core = BindCoreImage(base, sha);
  if (!b.core.enabled) return b;
  b.enabled = true;
  b.context = religion::BindReligionContextImage12002(base, sha);
  b.rite_model = rite::BindRiteModelImage12002(base, sha);
  b.main_rite = BindFaithMainRiteUnreformedImage12002(base, sha);
  b.window = BindCurrentRiteCreationWindow12002(base, sha);
  b.costs = BindRiteCreationCostsImage12002(base, sha);
  b.eligibility = BindEligibilityImage12002(base, sha);
  b.choices = BindCurrentDraftChoices12002(base, sha);
  return b;
}

bool ReadPlayedReformQuery12002(const Bindings &b, std::uint64_t epoch,
                              Observation &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  if (!b.enabled || !b.core.enabled) return false;
  Observation candidate{};
  candidate.capture_epoch = epoch;
  if (!ReadGuarded(b, epoch, candidate)) {
    // Preserve only frame metadata on an incomplete composed capture. Partial
    // native values must not appear to be an available composed observation.
    out.failure = std::move(candidate.failure);
    out.date_raw = candidate.date_raw;
    out.played_character_id = candidate.played_character_id;
    return false;
  }
  out = std::move(candidate);
  return true;
}

std::string SerializePlayedReformQuery12002(const Observation &value) {
  return "{\"schema\":\"ck3_12002_player_religion_reform_query_v1\""
      ",\"game_version\":\"1.20.0.2\",\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"available\":" + Boolean(value.available) +
      ",\"unavailable_reason\":" + (value.available ? "null" : Quote(value.failure)) +
      ",\"scope\":\"played_character_current_model_and_already_open_draft\""
      ",\"capture_epoch\":" + std::to_string(value.capture_epoch) +
      ",\"date_raw\":" + std::to_string(value.date_raw) +
      ",\"played_character_id\":" + std::to_string(value.played_character_id) +
      ",\"readiness\":{\"current_context_ready\":" + Boolean(value.context.available) +
      ",\"current_rite_model_ready\":" + Boolean(value.rite_model.available) +
      ",\"main_rite_status_ready\":" + Boolean(value.main_rite.status == MainRiteStatus::observed) +
      ",\"current_window_observation_ready\":" + Boolean(value.current_window.available) +
      ",\"current_draft_cost_ready\":" + Boolean(value.draft_costs.available) +
      ",\"current_draft_final_eligibility_ready\":" + Boolean(value.draft_eligibility.available) +
      ",\"current_popup_collection_ready\":" + Boolean(value.popup_choices.available && value.popup_choices.draft_observed) +
      ",\"doctrine_final_selection_ready\":" + Boolean(value.current_doctrine_selection.available && value.current_doctrine_selection.selection_ready) +
      ",\"final_choice_legality_readiness\":false}"
      ",\"current_context\":" + religion::SerializePlayedReligionContext12002(value.context) +
      ",\"current_rite_model\":" + rite::SerializePlayedRiteModel12002(value.rite_model) +
      ",\"main_rite_unreformed\":" + SerializeMainRite(value.main_rite) +
      ",\"current_creation_window\":" + SerializeCurrentRiteCreationWindow12002(value.current_window) +
      ",\"current_draft_costs\":" + SerializeCurrentRiteCreationCosts12002(value.draft_costs) +
      ",\"current_draft_eligibility\":" + SerializeDraftEligibility12002(value.draft_eligibility) +
      ",\"current_popup_choices\":" + SerializePopup(value.popup_choices) +
      ",\"current_doctrine_selection\":" + religion::doctrine12002::SerializeCurrentDraftDoctrineSelection12002(value.current_doctrine_selection) + '}';
}

} // namespace xar::ck3_12002::religion_reform::query
