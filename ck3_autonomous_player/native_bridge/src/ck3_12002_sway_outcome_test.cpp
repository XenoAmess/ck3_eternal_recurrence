#include "xar_bridge/ck3_12002_sway_outcome.hpp"

// Reuse the existing event producer's complete memory fixture and callbacks.
// The test links the actual core, events and event-window reader, not stubs.
#define main SwayReuseEventWindowFixtureMain
#include "ck3_12002_event_window_context_test.cpp"
#undef main

namespace {
constexpr std::int32_t kSwayTarget = 43;
constexpr std::uint32_t kSwayScheme = 0x01000002u;
std::int32_t g_opinion = 7;
std::int32_t g_opinion_calls = 0;
bool g_opinion_drift = false;
void *g_expected_recipient = nullptr;
void *g_expected_actor = nullptr;
void *g_sway_definition = nullptr;
void *g_blocker_definition = nullptr;
void *g_opinion_group = nullptr;
std::uint32_t g_sway_hash = 0, g_blocker_hash = 0;
std::int32_t g_sway_modifier_value = 40;

void *SwayLookupModifier(void *, std::uint32_t hash) {
  return hash == g_sway_hash ? g_sway_definition : hash == g_blocker_hash ? g_blocker_definition : nullptr;
}
void *SwayFindGroup(void *, std::uint32_t actor) {
  return actor == kCharacterId ? g_opinion_group : nullptr;
}
std::int32_t SwaySumModifier(void *group, void *definition) {
  return group == g_opinion_group && definition == g_sway_definition ? g_sway_modifier_value : -10;
}

std::int32_t SwayOpinion(void *recipient, void *actor) {
  if (recipient != g_expected_recipient || actor != g_expected_actor) return -999;
  ++g_opinion_calls;
  return g_opinion + (g_opinion_drift && g_opinion_calls > 1 ? 1 : 0);
}

struct SwayFixture : Fixture {
  std::array<std::byte, 10 * 0x50> types{};
  std::array<std::byte, 0x20> scheme_type_name{};
  std::array<std::byte, 0x20> owner_name{};
  std::array<std::byte, 0x20> target_name{};
  std::array<std::byte, 0x20> scheme_name{};
  std::array<std::byte, 3 * 0x18> scopes{};
  std::array<std::byte, 0x1C0> target_character{};
  std::array<std::byte, 0x20> opinion_extension{};
  std::array<std::byte, 0x20> opinion_group{};
  std::array<std::byte, 0x10> active_sway_opinion{};
  std::array<void *, 1> opinion_rows{};
  std::array<std::array<std::byte, 0x90>, 2> modifier_definitions{};
  std::array<std::array<char, 64>, 2> modifier_key_backing{};
  std::array<std::byte, 0x40> scheme_storage{};
  std::array<std::byte, 4 * 0x10> scheme_slots{};
  std::array<std::byte, 0x40> scheme_object{};
  std::array<std::byte, 0x40> sway_type_definition{};
  std::array<char, 64> definition_key{};
  void *scheme_storage_pointer = scheme_storage.data();
  xar::ck3_12002::SwayOutcomeBindings outcome_bindings{};
  xar::ck3_12002::SwayOutcomeRequestV1 request{
      kRevision, kEventId, kCharacterId, kSwayTarget, kSwayScheme};

  SwayFixture() {
    std::memcpy(types.data(), generic_value_type_entries.data(), generic_value_type_entries.size());
    Store<void *>(generic_value_type_registry.data(), 0, types.data());
    Store<std::int32_t>(generic_value_type_registry.data(), 0x0C, 10);
    Store<std::int32_t>(types.data() + 9 * 0x50, 0, 109);
    StoreInlineString(scheme_type_name.data(), "scheme");
    g_generic_value_type_names[109] = reinterpret_cast<const std::string *>(scheme_type_name.data());
    StoreInlineString(owner_name.data(), "owner");
    StoreInlineString(target_name.data(), "target");
    StoreInlineString(scheme_name.data(), "scheme");
    const std::array<const char *, 3> names{"owner", "target", "scheme"};
    const std::array<const std::byte *, 3> name_objects{owner_name.data(), target_name.data(), scheme_name.data()};
    for (std::size_t index = 0; index < 3; ++index) {
      const auto identifier = static_cast<std::int32_t>(301 + index);
      g_script_identifier_names[identifier] = reinterpret_cast<const std::string *>(name_objects[index]);
      g_script_identifier_text[identifier] = names[index];
      auto *row = scopes.data() + index * 0x18;
      Store<std::int32_t>(row, 0, identifier);
      Store<std::uint16_t>(row, 8, index == 2 ? 9 : 4);
      Store<std::uint64_t>(row, 0x10, index == 0 ? kCharacterId : index == 1 ? kSwayTarget : kSwayScheme);
    }
    Store<void *>(active_event.data(), 0x18, scopes.data());
    Store<std::int32_t>(active_event.data(), 0x20, 3);
    Store<std::int32_t>(active_event.data(), 0x24, 3);
    Store<void *>(character_slots.data() + kSwayTarget * 0x10, 8, target_character.data());
    Store<std::int32_t>(target_character.data(), 0x18, kSwayTarget);
    Store<void *>(scheme_storage.data(), 0x20, scheme_slots.data());
    Store<std::int32_t>(scheme_storage.data(), 0x2C, 4);
    Store<void *>(scheme_slots.data() + 2 * 0x10, 8, scheme_object.data());
    Store<std::uint32_t>(scheme_object.data(), 0x10, kSwayScheme);
    Store<std::uintptr_t>(scheme_object.data(), 0, 0x1847794E8);
    Store<void *>(scheme_object.data(), 0x20, sway_type_definition.data());
    Store<std::int32_t>(scheme_object.data(), 0x2C, kCharacterId);
    Store<std::int32_t>(scheme_object.data(), 0x34, kSwayTarget);
    Store<std::uintptr_t>(sway_type_definition.data(), 0, bindings.scheme_type_primary_vtable);
    StoreInlineString(sway_type_definition.data() + 0x18, "sway");
    Store<std::uint32_t>(sway_type_definition.data(), 0x38, 0x4744624Fu);
    bindings.events.image_base = 0x180000000;
    outcome_bindings.event_window = bindings;
    outcome_bindings.scheme_storage_slot = &scheme_storage_pointer;
    outcome_bindings.target_opinion = &SwayOpinion;
    auto &modifiers = outcome_bindings.opinion_modifiers;
    modifiers.enabled = true;
    modifiers.modifier_database_slot = &scheme_type_database_pointer;
    modifiers.lookup_modifier = &SwayLookupModifier;
    modifiers.find_group = &SwayFindGroup;
    modifiers.sum_modifier = &SwaySumModifier;
    modifiers.modifier_primary_vtable = 0x1848C5370;
    modifiers.modifier_secondary_vtable = 0x1848C5338;
    modifiers.active_opinion_vtable = 0x18473DE08;
    modifiers.temporary_opinion_vtable = 0x18473DDD0;
    const std::array<const char *, 2> modifier_keys{"scheme_sway_opinion", "sway_blocker_opinion"};
    for (std::size_t index = 0; index < 2; ++index) {
      auto *definition = modifier_definitions[index].data();
      const auto hash = static_cast<std::uint32_t>(HashStableKey(scheme_type_database.data(), modifier_keys[index],
                                                                static_cast<std::uint32_t>(std::strlen(modifier_keys[index]))));
      Store<std::uintptr_t>(definition, 0, modifiers.modifier_primary_vtable);
      Store<std::uintptr_t>(definition, 0x88, modifiers.modifier_secondary_vtable);
      Store<std::uint32_t>(definition, 0x14, hash);
      StoreHeapString(definition + 0x18, modifier_key_backing[index], modifier_keys[index]);
      Store<std::uint32_t>(definition, 0x38, 0x4744624Fu);
      if (index == 0) g_sway_hash = hash;
      else g_blocker_hash = hash;
    }
    g_sway_definition = modifier_definitions[0].data();
    g_blocker_definition = modifier_definitions[1].data();
    g_opinion_group = opinion_group.data();
    g_sway_modifier_value = 40;
    Store<void *>(target_character.data(), 0x1B0, opinion_extension.data());
    opinion_rows[0] = active_sway_opinion.data();
    Store<void *>(opinion_group.data(), 8, opinion_rows.data());
    Store<std::int32_t>(opinion_group.data(), 0x14, 1);
    Store<std::uintptr_t>(active_sway_opinion.data(), 0, modifiers.active_opinion_vtable);
    Store<void *>(active_sway_opinion.data(), 8, g_sway_definition);
    g_expected_recipient = target_character.data();
    g_expected_actor = character.data();
    g_opinion = 7;
    g_opinion_drift = false;
    SetEvent("sway_outcome.1001", 1);
  }

  void SetEvent(const char *key, std::int32_t native_option) {
    StoreHeapString(event_definition.data() + 0x10, definition_key, key);
    InitializeOption(0, native_option, true, false);
    Store<std::int32_t>(option_items.data(), 0x94, 0);
    g_current_event_calls = 0;
    g_opinion_calls = 0;
  }
};

bool TestSwayReader() {
  using namespace xar::ck3_12002;
  SwayFixture fixture;
  SwayOutcomeEventV1 row{};
  const auto read = [&]() { g_opinion_calls = 0; return ReadSwayOutcomeEventV1(fixture.outcome_bindings, fixture.request, row); };
  if (!read() || !row.exact_scope_join_ready || !row.phase_result_observed ||
      row.phase_result != SwayPhaseResultV1::success || !row.target_opinion_observed ||
      row.target_opinion_of_actor != 7 || row.options.size() != 1 ||
      !row.scheme_sway_opinion.observed || !row.scheme_sway_opinion.present ||
      row.scheme_sway_opinion.value != 40 || !row.sway_blocker_opinion.observed ||
      row.sway_blocker_opinion.present || row.sway_blocker_opinion.value ||
      row.options[0].rendered_index != 0 || row.options[0].native_option_index != 1 ||
      !row.options[0].deterministic || row.options[0].authored_sway_points_on_success != 30 ||
      row.options[0].authored_sway_modifier_selection != "scheme_sway_opinion" ||
      row.instance_terminal_outcome_observed || row.cancel_outcome_observed) return false;
  // The rendered first option is native option 2: friend-gated option filtering
  // must never shift the effect mapping to native option 0.
  fixture.SetEvent("sway_outcome.1003", 2);
  if (!read() || row.authored_immediate_sway_points != 30 ||
      row.authored_immediate_modifier_selection != "conditional_sway_or_compelled" ||
      row.options[0].native_option_index != 2 || !row.options[0].deterministic ||
      row.options[0].authored_sway_points_on_success != 0) return false;
  fixture.SetEvent("sway_outcome.1004", 1);
  if (!read() || row.authored_immediate_sway_points != 20 ||
      !row.options[0].end_scheme_effect || row.instance_terminal_outcome_observed) return false;
  fixture.SetEvent("sway_outcome.2002", 0);
  if (!read() || row.phase_result != SwayPhaseResultV1::failure ||
      row.options[0].authored_blocker_points != -10 ||
      !row.options[0].end_scheme_effect || row.instance_terminal_outcome_observed) return false;
  std::cout << SerializeSwayOutcomeEventV1(row) << '\n';
  fixture.SetEvent("sway_outcome.1002", 0);
  g_opinion = 100;
  g_sway_modifier_value = 0;
  if (!read() || row.options[0].deterministic ||
      !row.scheme_sway_opinion.present || row.scheme_sway_opinion.value != 0 ||
      row.options[0].authored_sway_points_on_success != 50 ||
      row.options[0].authored_sway_points_on_failure != 0 ||
      row.instance_terminal_outcome_observed) return false;
  fixture.SetEvent("sway_outcome.0001", 0);
  if (read() || row.unavailable_reason != "sway_outcome_event_not_supported") return false;
  fixture.SetEvent("sway_outcome.1001", 1);
  Store<std::uint32_t>(fixture.scheme_object.data(), 0x10, 0x02000002u);
  if (read() || row.unavailable_reason != "sway_outcome_scheme_join_mismatch") return false;
  Store<std::uint32_t>(fixture.scheme_object.data(), 0x10, kSwayScheme);
  Store<std::int32_t>(fixture.scheme_object.data(), 0x34, kCharacterId);
  if (read() || row.unavailable_reason != "sway_outcome_scheme_join_mismatch") return false;
  Store<std::int32_t>(fixture.scheme_object.data(), 0x34, kSwayTarget);
  fixture.request.target_character_id = kCharacterId;
  if (read() || row.unavailable_reason != "sway_outcome_scope_join_mismatch") return false;
  fixture.request.target_character_id = kSwayTarget;
  g_opinion_drift = true;
  if (read() || row.unavailable_reason != "sway_outcome_source_changed") return false;
  g_opinion_drift = false;
  g_active_event = nullptr;
  if (read() || row.instance_terminal_outcome_observed || row.cancel_outcome_observed) return false;
  // Material opinion remains observable after consuming the current event.
  SwayOutcomeOpinionV1 opinion_row{};
  g_opinion_calls = 0;
  g_opinion = 37;
  g_sway_modifier_value = 30;
  if (!ReadSwayOutcomeOpinionV1(fixture.outcome_bindings, kCharacterId, kSwayTarget, opinion_row) ||
      opinion_row.target_opinion_of_actor != 37 || opinion_row.scheme_sway_opinion.value != 30) return false;
  Store<void *>(fixture.active_sway_opinion.data(), 8, g_blocker_definition);
  g_opinion_calls = 0;
  if (!ReadSwayOutcomeOpinionV1(fixture.outcome_bindings, kCharacterId, kSwayTarget, opinion_row) ||
      opinion_row.scheme_sway_opinion.present || opinion_row.scheme_sway_opinion.value ||
      !opinion_row.sway_blocker_opinion.present || opinion_row.sway_blocker_opinion.value != -10) return false;
  std::cout << SerializeSwayOutcomeOpinionV1(opinion_row, kRevision, 741221) << '\n';
  g_active_event = fixture.active_event.data();
  const auto bound = BindSwayOutcomeImage(0x180000000, kExecutableSha256);
  const auto old = BindSwayOutcomeImage(0x180000000, "old");
  return bound.event_window.events.core.enabled && !old.event_window.events.core.enabled &&
         reinterpret_cast<std::uintptr_t>(bound.scheme_storage_slot) == 0x185D1FC58 &&
         reinterpret_cast<std::uintptr_t>(bound.target_opinion) == 0x1828BC490 &&
         old.target_opinion == nullptr;
}
} // namespace

int main() {
  if (!TestSwayReader()) { std::cerr << "Sway outcome fixture failed\n"; return 1; }
  std::cout << "Sway outcome exact event/actor/target/SchemeID and opinion fixture passed\n";
  return 0;
}
