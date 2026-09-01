#include "xar_bridge/pending_character_interaction_context_v1.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

namespace {

constexpr std::int32_t kPendingId = -2'130'706'399;
constexpr std::int32_t kPlayedCharacterId = 2'001;
constexpr std::int32_t kActorCharacterId = 1'001;
constexpr std::int32_t kWarId = 16'777'250;
constexpr std::int32_t kCallAllyWarId = 67'108'946;
constexpr std::size_t kPendingSlotIndex = 33;
constexpr std::size_t kPendingSlotCount = 34;
constexpr std::size_t kCharacterSlotCount = 3'002;
constexpr std::size_t kRowStride = 0x7D0;

template <std::size_t Size, typename Value>
void Store(std::array<std::byte, Size> &storage, std::size_t offset,
           const Value &value) {
  if (offset + sizeof(value) > storage.size()) {
    std::abort();
  }
  std::memcpy(storage.data() + offset, &value, sizeof(value));
}

template <typename Value>
void Store(std::vector<std::byte> &storage, std::size_t offset,
           const Value &value) {
  if (offset + sizeof(value) > storage.size()) {
    std::abort();
  }
  std::memcpy(storage.data() + offset, &value, sizeof(value));
}

struct Fixture {
  xar::game::PendingCharacterInteractionFrameV1 frame{47, 53'175'816, true,
                                                      true};
  std::array<std::byte, 0x40> pending_storage{};
  void *pending_storage_pointer = nullptr;
  std::vector<std::byte> pending_slots =
      std::vector<std::byte>(kPendingSlotCount * 0x10);
  std::array<std::byte, 0x5C8> pending{};
  std::array<std::byte, 0x40> character_storage{};
  void *character_storage_pointer = nullptr;
  std::vector<std::byte> character_slots =
      std::vector<std::byte>(kCharacterSlotCount * 0x10);
  std::array<std::byte, 0x220> played_character{};
  std::array<std::byte, 0x220> actor_character{};
  std::array<std::byte, 0x2A60> definition{};
  std::array<std::byte, 0x08> special_data{};
  std::array<std::byte, 0x28> common_war_relation{};
  std::array<std::byte, 0x28> second_common_war_relation{};
  std::array<std::byte, 0x360> active_war{};
  std::vector<std::byte> rows = std::vector<std::byte>(2 * kRowStride);
  std::array<std::uint8_t, 2> selected{1, 0};
  std::array<std::byte, 0x20> target_registry{};
  std::vector<std::byte> target_registry_entries =
      std::vector<std::byte>(17 * 0x50);
  std::string definition_key = "fixture_request_support_interaction";
  std::string target_type_key = "fixture_generic_target_type";
  std::string war_target_type_key = "war";
  std::int32_t expiration_days = 60;
  bool on_main_thread = true;
  bool local_route = true;
  std::array<bool, 3> validator_results{true, true, true};
  std::array<bool, 2> shown_results{true, true};
  std::array<bool, 2> valid_results{true, true};
  std::array<std::int64_t, 10> cost_raw{0, 100'000, -50'000, 250'000, 0,
                                        0, 300'000, 50'000,  0,       400'000};
  bool change_frame_on_final_capture = false;
  bool change_selection_between_observations = false;
  bool change_cost_between_observations = false;
  bool change_relation_between_observations = false;
  bool change_special_vptr_between_observations = false;
  bool call_ally_war_resolver_available = true;
  std::int32_t capture_calls = 0;
  std::int32_t route_calls = 0;
  std::int32_t validator_calls = 0;
  std::int32_t selected_read_calls = 0;
  std::int32_t cost_calls = 0;
  std::int32_t common_war_relation_calls = 0;
  std::int32_t resolve_active_war_calls = 0;
  std::int32_t special_vptr_read_calls = 0;
  std::vector<std::int32_t> trigger_order;

  Fixture() { Reset(); }

  void Reset() {
    frame = {47, 53'175'816, true, true};
    pending_storage.fill(std::byte{});
    std::fill(pending_slots.begin(), pending_slots.end(), std::byte{});
    pending.fill(std::byte{});
    character_storage.fill(std::byte{});
    std::fill(character_slots.begin(), character_slots.end(), std::byte{});
    played_character.fill(std::byte{});
    actor_character.fill(std::byte{});
    definition.fill(std::byte{});
    special_data.fill(std::byte{});
    common_war_relation.fill(std::byte{});
    second_common_war_relation.fill(std::byte{});
    active_war.fill(std::byte{});
    std::fill(rows.begin(), rows.end(), std::byte{});
    selected = {1, 0};
    target_registry.fill(std::byte{});
    std::fill(target_registry_entries.begin(), target_registry_entries.end(),
              std::byte{});
    expiration_days = 60;
    definition_key = "fixture_request_support_interaction";
    target_type_key = "fixture_generic_target_type";
    war_target_type_key = "war";
    pending_storage_pointer = pending_storage.data();
    character_storage_pointer = character_storage.data();
    on_main_thread = true;
    local_route = true;
    validator_results = {true, true, true};
    shown_results = {true, true};
    valid_results = {true, true};
    cost_raw = {0, 100'000, -50'000, 250'000, 0,
                0, 300'000, 50'000,  0,       400'000};
    change_frame_on_final_capture = false;
    change_selection_between_observations = false;
    change_cost_between_observations = false;
    change_relation_between_observations = false;
    change_special_vptr_between_observations = false;
    call_ally_war_resolver_available = true;
    capture_calls = 0;
    route_calls = 0;
    validator_calls = 0;
    selected_read_calls = 0;
    cost_calls = 0;
    common_war_relation_calls = 0;
    resolve_active_war_calls = 0;
    special_vptr_read_calls = 0;
    trigger_order.clear();

    Store(pending_storage, 0x20, static_cast<void *>(pending_slots.data()));
    Store(pending_storage, 0x2C, static_cast<std::int32_t>(kPendingSlotCount));
    Store(pending_slots, kPendingSlotIndex * 0x10 + 0x08,
          static_cast<void *>(pending.data()));
    Store(pending, 0x10, kPendingId);
    Store(pending, 0x18, static_cast<void *>(definition.data()));
    Store(pending, 0x2F0, std::int32_t{1'001});
    Store(pending, 0x2F4, kPlayedCharacterId);
    Store(pending, 0x2F8, std::int32_t{-1});
    Store(pending, 0x2FC, std::int32_t{-1});
    Store(pending, 0x300, std::int32_t{-1});
    Store(pending, 0x318, static_cast<void *>(selected.data()));
    Store(pending, 0x320, std::int32_t{2});
    Store(pending, 0x324, std::int32_t{2});
    Store(pending, 0x348, static_cast<void *>(nullptr));
    Store(pending, 0x5B8, std::int32_t{17});
    Store(pending, 0x5C0, std::int32_t{0});
    Store(pending, 0x5C6, std::uint8_t{0});

    SetPlayedCharacter(kPlayedCharacterId);

    Store(definition, 0x10, std::int32_t{42});
    Store(definition, 0x14, std::uint32_t{0x12345678});
    Store(definition, 0x2548, static_cast<void *>(rows.data()));
    Store(definition, 0x2554, std::int32_t{2});
    Store(definition, 0x2580, static_cast<void *>(nullptr));
    Store(definition, 0x2A48, std::uint8_t{0});
    Store(definition, 0x2A4E, std::uint8_t{0});
    Store(rows, 0x3A8, std::int32_t{31'001});
    Store(rows, kRowStride + 0x3A8, std::int32_t{31'002});

    Store(target_registry, 0x00,
          static_cast<void *>(target_registry_entries.data()));
    Store(target_registry, 0x0C, std::int32_t{17});
    Store(target_registry_entries, 7 * 0x50, std::int32_t{77'007});
    Store(target_registry_entries, 16 * 0x50, std::int32_t{77'016});
  }

  void SetPlayedCharacter(std::int32_t character_id) {
    std::fill(character_slots.begin(), character_slots.end(), std::byte{});
    const auto index = static_cast<std::uint32_t>(character_id) & 0x00FFFFFFU;
    if (index >= kCharacterSlotCount) {
      std::abort();
    }
    Store(character_storage, 0x20, static_cast<void *>(character_slots.data()));
    Store(character_storage, 0x2C,
          static_cast<std::int32_t>(kCharacterSlotCount));
    Store(character_slots, static_cast<std::size_t>(index) * 0x10 + 0x08,
          static_cast<void *>(played_character.data()));
    Store(played_character, 0x18, character_id);
  }

  void InstallActorCharacter() {
    const auto index =
        static_cast<std::uint32_t>(kActorCharacterId) & 0x00FFFFFFU;
    Store(character_slots, static_cast<std::size_t>(index) * 0x10 + 0x08,
          static_cast<void *>(actor_character.data()));
    Store(actor_character, 0x18, kActorCharacterId);
  }

  void SetSpecialWar(std::string key, std::uintptr_t vtable,
                     bool actor_is_attacker = true) {
    definition_key = std::move(key);
    InstallActorCharacter();
    Store(special_data, 0, vtable);
    Store(pending, 0x348, static_cast<void *>(special_data.data()));
    Store(common_war_relation, 0x20, kWarId);
    Store(second_common_war_relation, 0x20, kWarId);
    Store(active_war, 0x08, kWarId);
    Store(active_war, 0x288,
          actor_is_attacker ? kActorCharacterId : kPlayedCharacterId);
    Store(active_war, 0x28C,
          actor_is_attacker ? kPlayedCharacterId : kActorCharacterId);
    Store(active_war, 0x358, static_cast<void *>(nullptr));
  }

  void SetCallAllyWarTarget() {
    definition_key = "call_ally_interaction";
    const std::uint16_t type_index = 16;
    Store(pending, 0x308, type_index);
    Store(pending, 0x310, kCallAllyWarId);
    Store(active_war, 0x08, kCallAllyWarId);
    call_ally_war_resolver_available = true;
  }
};

bool DummyRoute(void *, void *) { return false; }
bool DummyValidator(void *) { return false; }
bool DummyTrigger(void *, const void *) { return false; }
void DummyCost(const void *, const void *, std::int64_t *) {}
void *DummyCommonWarRelation(void *, void *) { return nullptr; }
void *DummyRegistry() { return nullptr; }
const std::string *DummyIdentifier(std::int32_t) { return nullptr; }

bool Capture(void *context,
             xar::game::PendingCharacterInteractionFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.capture_calls;
  output = fixture.frame;
  if (fixture.change_frame_on_final_capture && fixture.capture_calls >= 2) {
    ++output.snapshot_revision;
  }
  return true;
}

bool IsMainThread(void *context) noexcept {
  return static_cast<Fixture *>(context)->on_main_thread;
}

bool ReadMemory(void *context, const void *address, void *output,
                std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (address == fixture.special_data.data() &&
      size == sizeof(std::uintptr_t)) {
    ++fixture.special_vptr_read_calls;
    if (fixture.change_special_vptr_between_observations &&
        fixture.special_vptr_read_calls >= 2) {
      const std::uintptr_t changed = 0x33333331U;
      std::memcpy(output, &changed, sizeof(changed));
      return true;
    }
  }
  if (address >= fixture.selected.data() &&
      address < fixture.selected.data() + fixture.selected.size() &&
      size == 1) {
    ++fixture.selected_read_calls;
    if (fixture.change_selection_between_observations &&
        fixture.selected_read_calls > 2 && address == fixture.selected.data()) {
      const std::uint8_t changed = 0;
      std::memcpy(output, &changed, 1);
      return true;
    }
  }
  std::memcpy(output, address, size);
  return true;
}

bool ReadString(void *context, const void *native_string,
                std::string &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (native_string == fixture.definition.data() + 0x18) {
    output = fixture.definition_key;
    return true;
  }
  if (native_string == &fixture.target_type_key) {
    output = fixture.target_type_key;
    return true;
  }
  if (native_string == &fixture.war_target_type_key) {
    output = fixture.war_target_type_key;
    return true;
  }
  return false;
}

bool InvokeRoute(void *context,
                 xar::ck3_11906::NativePendingInteractionLocalRoutingV1,
                 void *pending, void *character, bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.route_calls;
  output = fixture.local_route && pending == fixture.pending.data() &&
           character == fixture.played_character.data();
  return true;
}

bool InvokeValidator(void *context,
                     xar::ck3_11906::NativePendingInteractionReplyValidatorV1,
                     void *command, bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.validator_calls;
  std::uintptr_t primary = 0;
  std::uintptr_t secondary = 0;
  std::int32_t pending_id = -1;
  std::int32_t reply = -1;
  const auto *bytes = static_cast<const std::byte *>(command);
  std::memcpy(&primary, bytes, sizeof(primary));
  std::memcpy(&secondary, bytes + 0x18, sizeof(secondary));
  std::memcpy(&pending_id, bytes + 0x20, sizeof(pending_id));
  std::memcpy(&reply, bytes + 0x24, sizeof(reply));
  if (primary != 0x11111111U || secondary != 0x22222222U ||
      pending_id != kPendingId || reply < 0 || reply > 2) {
    return false;
  }
  output = fixture.validator_results[static_cast<std::size_t>(reply)];
  return true;
}

bool InvokeTrigger(void *context,
                   xar::ck3_11906::NativePendingInteractionTriggerEvaluatorV1,
                   void *trigger, const void *scope, bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (scope != fixture.pending.data() + 0x20) {
    return false;
  }
  for (std::int32_t index = 0; index < 2; ++index) {
    auto *row =
        fixture.rows.data() + static_cast<std::size_t>(index) * kRowStride;
    if (trigger == row + 0xE0) {
      fixture.trigger_order.push_back(index * 2);
      output = fixture.valid_results[static_cast<std::size_t>(index)];
      return true;
    }
    if (trigger == row) {
      fixture.trigger_order.push_back(index * 2 + 1);
      output = fixture.shown_results[static_cast<std::size_t>(index)];
      return true;
    }
  }
  if (trigger == fixture.definition.data() + 0x100) {
    fixture.trigger_order.push_back(99);
    output = true;
    return true;
  }
  return false;
}

bool InvokeCost(
    void *context, xar::ck3_11906::NativePendingInteractionCostEvaluatorV1,
    const void *compiled_cost_block, const void *scope,
    std::array<std::int64_t,
               xar::game::kPendingCharacterInteractionCostResourceCountV1>
        &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (compiled_cost_block != fixture.definition.data() + 0x38 ||
      scope != fixture.pending.data() + 0x20) {
    return false;
  }
  ++fixture.cost_calls;
  output = fixture.cost_raw;
  if (fixture.change_cost_between_observations && fixture.cost_calls >= 2) {
    ++output[0];
  }
  return true;
}

bool InvokeCommonWarRelation(
    void *context,
    xar::ck3_11906::NativePendingInteractionCommonWarRelationV1 function,
    void *actor_character, void *recipient_character, void *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.common_war_relation_calls;
  if (function != DummyCommonWarRelation ||
      actor_character != fixture.actor_character.data() ||
      recipient_character != fixture.played_character.data()) {
    output = nullptr;
    return false;
  }
  output = fixture.change_relation_between_observations &&
                   fixture.common_war_relation_calls >= 2
               ? static_cast<void *>(fixture.second_common_war_relation.data())
               : static_cast<void *>(fixture.common_war_relation.data());
  return true;
}

bool ResolveActiveWar(void *context, std::int32_t war_id,
                      void *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.resolve_active_war_calls;
  output = war_id == kWarId ||
                   (war_id == kCallAllyWarId &&
                    fixture.call_ally_war_resolver_available)
               ? static_cast<void *>(fixture.active_war.data())
               : nullptr;
  return output != nullptr;
}

bool InvokeRegistry(
    void *context,
    xar::ck3_11906::NativePendingInteractionTargetTypeRegistryGetterV1,
    void *&output) noexcept {
  output = static_cast<Fixture *>(context)->target_registry.data();
  return true;
}

bool InvokeIdentifier(
    void *context,
    xar::ck3_11906::NativePendingInteractionScriptIdentifierNameV1,
    std::int32_t identifier, const std::string *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = identifier == 77'007
               ? &fixture.target_type_key
               : identifier == 77'016 ? &fixture.war_target_type_key : nullptr;
  return output != nullptr;
}

xar::ck3_11906::PendingCharacterInteractionNativeEnvironmentV1
Environment(Fixture &fixture) {
  xar::ck3_11906::PendingCharacterInteractionNativeEnvironmentV1 output{};
  output.exact_build_admitted = true;
  output.offline_fixture_function_overrides = true;
  output.pending_storage_slot = &fixture.pending_storage_pointer;
  output.character_storage_slot = &fixture.character_storage_pointer;
  output.expiration_days = &fixture.expiration_days;
  output.local_routing = DummyRoute;
  output.reply_validator = DummyValidator;
  output.trigger_evaluator = DummyTrigger;
  output.cost_evaluator = DummyCost;
  output.common_war_relation = DummyCommonWarRelation;
  output.target_type_registry = DummyRegistry;
  output.script_identifier_name = DummyIdentifier;
  output.reply_primary_vtable = 0x11111111U;
  output.reply_secondary_vtable = 0x22222222U;
  output.war_victory_special_vtable = 0x33333331U;
  output.war_white_peace_special_vtable = 0x33333332U;
  output.war_defeat_special_vtable = 0x33333333U;
  return output;
}

xar::ck3_11906::PendingCharacterInteractionAccessV1 Access(Fixture &fixture) {
  xar::ck3_11906::PendingCharacterInteractionAccessV1 output{};
  output.context = &fixture;
  output.capture_frame = Capture;
  output.is_main_thread = IsMainThread;
  output.read_memory = ReadMemory;
  output.read_string = ReadString;
  output.invoke_local_routing = InvokeRoute;
  output.invoke_reply_validator = InvokeValidator;
  output.invoke_trigger_evaluator = InvokeTrigger;
  output.invoke_cost_evaluator = InvokeCost;
  output.invoke_common_war_relation = InvokeCommonWarRelation;
  output.resolve_active_war = ResolveActiveWar;
  output.invoke_target_type_registry = InvokeRegistry;
  output.invoke_script_identifier_name = InvokeIdentifier;
  return output;
}

xar::ck3_11906::PendingCharacterInteractionContextRequestV1
Request(std::int32_t played_character_id = kPlayedCharacterId) {
  return {47, kPendingId, played_character_id};
}

bool Contains(std::string_view value, std::string_view token) {
  return value.find(token) != std::string_view::npos;
}

int Fail(std::string_view message) {
  std::cerr << message << '\n';
  return 1;
}

bool Read(Fixture &fixture,
          xar::game::PendingCharacterInteractionContextV1 &output,
          std::int32_t played_character_id = kPlayedCharacterId) {
  const auto result = xar::ck3_11906::ReadPendingCharacterInteractionContextV1(
      Environment(fixture), Access(fixture), Request(played_character_id),
      output);
  return result ==
         xar::game::ReadPendingCharacterInteractionContextResultV1::available;
}

} // namespace

int main() {
  using xar::game::PendingCharacterInteractionContextStatusV1;
  using xar::game::ReadPendingCharacterInteractionContextResultV1;

  Fixture fixture;
  xar::game::PendingCharacterInteractionContextV1 output{};
  if (!Read(fixture, output) ||
      output.status != PendingCharacterInteractionContextStatusV1::available ||
      !output.definition.has_value() ||
      output.definition->canonical_key != fixture.definition_key ||
      output.definition->deterministic_key_hash != 0x12345678U ||
      !output.roles.has_value() || output.roles->actor_character_id != 1'001 ||
      !output.routing.has_value() ||
      output.routing->current_responder_role != "recipient" ||
      output.routing->reply_execution_channel != "recipient" ||
      !output.routing->local_route || !output.deadline.has_value() ||
      output.deadline->remaining_days != 43 ||
      !output.send_options.has_value() ||
      output.send_options->rows.size() != 2 ||
      !output.send_options->rows[0].selected ||
      output.send_options->rows[1].selected ||
      !output.legality.accept.allowed || !output.legality.reject.allowed ||
      !output.legality.block.allowed || output.legality.acknowledge.allowed ||
      !output.terms.has_value() ||
      output.terms->structured_costs.status !=
          xar::game::PendingCharacterInteractionSemanticStatusV1::available ||
      output.terms->structured_costs.entries[1].resource_key != "prestige" ||
      output.terms->structured_costs.entries[1].raw != 100'000 ||
      output.terms->structured_costs.entries[2].resource_key != "piety" ||
      output.terms->structured_costs.entries[2].raw != -50'000 ||
      output.terms->structured_costs.payer_role != "actor" ||
      output.terms->structured_costs.application_timing != "on_send" ||
      output.terms->structured_costs.pending_payment_state !=
          "already_applied" ||
      output.terms->structured_costs.entries[7].resource_key !=
          "treasury_or_gold" ||
      output.terms->structured_costs.entries[7].raw != 50'000 ||
      !output.readiness.generic_costs_ready ||
      output.terms->special_war_binding.status !=
          xar::game::PendingCharacterInteractionSemanticStatusV1::unavailable ||
      output.terms->special_war_binding.reason !=
          "special_war_binding_not_applicable" ||
      output.readiness.special_war_binding_ready ||
      output.readiness.special_outcome_terms_ready ||
      output.readiness.interaction_semantic_decision_ready ||
      fixture.route_calls != 2 || fixture.validator_calls != 6 ||
      fixture.cost_calls != 2 ||
      fixture.trigger_order !=
          std::vector<std::int32_t>({0, 1, 2, 3, 0, 1, 2, 3})) {
    return Fail("ordinary recipient projection or trigger order failed");
  }
  const auto serialized =
      xar::ck3_11906::SerializePendingCharacterInteractionContextV1(output);
  if (!Contains(serialized,
                "\"schema\":\"pending-character-interaction-context-v1\"") ||
      !Contains(serialized, "\"remaining_days\":43") ||
      !Contains(serialized, "\"interaction_semantic_decision_ready\":false") ||
      !Contains(serialized, "\"terms\":{") ||
      !Contains(serialized, "\"raw_scale\":100000") ||
      !Contains(serialized,
                "\"payer_role\":\"actor\",\"application_timing\":\"on_send\","
                "\"pending_payment_state\":\"already_applied\"") ||
      !Contains(serialized,
                "\"resource_key\":\"treasury_or_gold\",\"raw\":50000") ||
      !Contains(serialized,
                "\"special_war_binding\":{\"status\":\"unavailable\","
                "\"value\":null,\"reason\":"
                "\"special_war_binding_not_applicable\"") ||
      !Contains(serialized, "\"value\":null")) {
    return Fail("available serializer contract failed");
  }

  fixture.Reset();
  fixture.definition_key = "end_war_attacker_white_peace_interaction";
  if (!Read(fixture, output) || output.terms->special_data_present ||
      output.terms->special_war_binding.reason !=
          "special_interaction_identity_mismatch" ||
      fixture.common_war_relation_calls != 0 ||
      fixture.resolve_active_war_calls != 0 ||
      xar::ck3_11906::SerializePendingCharacterInteractionContextV1(output)
          .empty()) {
    return Fail("known war-exit definition accepted missing special data");
  }
  auto inconsistent_absent_special = output;
  inconsistent_absent_special.terms->special_war_binding.reason =
      "special_war_binding_not_applicable";
  inconsistent_absent_special.readiness.not_ready_reasons[0] =
      "special_war_binding_not_applicable";
  if (!xar::ck3_11906::SerializePendingCharacterInteractionContextV1(
           inconsistent_absent_special)
           .empty()) {
    return Fail("serializer accepted known war-exit as not applicable");
  }

  struct SpecialCase {
    std::string_view definition_key;
    std::uintptr_t vtable;
    std::string_view special_interaction_kind;
    std::string_view absolute_outcome;
    bool actor_is_attacker;
  };
  constexpr std::array<SpecialCase, 3> special_cases{{
      {"end_war_attacker_victory_interaction", 0x33333331U,
       "end_war_attacker_victory_interaction", "attacker_victory", true},
      {"end_war_attacker_white_peace_interaction", 0x33333332U,
       "end_war_white_peace_interaction", "white_peace", false},
      {"end_war_attacker_defeat_interaction", 0x33333333U,
       "end_war_attacker_defeat_interaction", "attacker_defeat", true},
  }};
  for (const auto &test_case : special_cases) {
    fixture.Reset();
    fixture.SetSpecialWar(std::string(test_case.definition_key),
                          test_case.vtable, test_case.actor_is_attacker);
    if (!Read(fixture, output) || !output.terms->special_data_present ||
        output.terms->special_war_binding.status !=
            xar::game::PendingCharacterInteractionSemanticStatusV1::available ||
        output.terms->special_war_binding.special_interaction_kind !=
            test_case.special_interaction_kind ||
        output.terms->special_war_binding.absolute_outcome !=
            test_case.absolute_outcome ||
        output.terms->special_war_binding.war_id != kWarId ||
        output.terms->special_war_binding.actor_war_role !=
            (test_case.actor_is_attacker ? "primary_attacker"
                                         : "primary_defender") ||
        output.terms->special_war_binding.recipient_war_role !=
            (test_case.actor_is_attacker ? "primary_defender"
                                         : "primary_attacker") ||
        output.terms->special_war_binding.binding_source !=
            "native_common_war_relation" ||
        !output.readiness.special_war_binding_ready ||
        output.readiness.special_outcome_terms_ready ||
        output.readiness.structured_terms_ready ||
        output.readiness.interaction_semantic_decision_ready ||
        output.readiness.not_ready_reasons !=
            std::vector<std::string>(
                {"special_outcome_terms_unavailable",
                 "structured_exchanges_unavailable",
                 "structured_effect_preview_unavailable"}) ||
        fixture.common_war_relation_calls != 2 ||
        fixture.resolve_active_war_calls != 2) {
      return Fail("exact special-war identity or active-War binding failed");
    }
  }
  const auto special_serialized =
      xar::ck3_11906::SerializePendingCharacterInteractionContextV1(output);
  if (!Contains(special_serialized,
                "\"special_interaction_kind\":"
                "\"end_war_attacker_defeat_interaction\"") ||
      !Contains(special_serialized,
                "\"absolute_outcome\":\"attacker_defeat\"") ||
      !Contains(special_serialized, "\"war_id\":16777250") ||
      !Contains(special_serialized,
                "\"binding_source\":\"native_common_war_relation\"") ||
      !Contains(special_serialized, "\"special_war_binding_ready\":true") ||
      !Contains(special_serialized, "\"special_outcome_terms_ready\":false")) {
    return Fail("special-war serializer contract failed");
  }
  auto malformed_special = output;
  malformed_special.terms->special_war_binding.absolute_outcome = "white_peace";
  if (!xar::ck3_11906::SerializePendingCharacterInteractionContextV1(
           malformed_special)
           .empty()) {
    return Fail("serializer accepted an inconsistent special-war outcome");
  }
  malformed_special = output;
  malformed_special.terms->special_war_binding.special_interaction_kind =
      "end_war_white_peace_interaction";
  if (!xar::ck3_11906::SerializePendingCharacterInteractionContextV1(
           malformed_special)
           .empty()) {
    return Fail("serializer accepted an inconsistent special-war kind");
  }
  malformed_special = output;
  malformed_special.terms->special_war_binding.actor_war_role =
      "primary_defender";
  if (!xar::ck3_11906::SerializePendingCharacterInteractionContextV1(
           malformed_special)
           .empty()) {
    return Fail("serializer accepted inconsistent special-war roles");
  }
  malformed_special = output;
  malformed_special.terms->special_war_binding.binding_source = "tooltip";
  if (!xar::ck3_11906::SerializePendingCharacterInteractionContextV1(
           malformed_special)
           .empty()) {
    return Fail("serializer accepted an invented special-war source");
  }
  malformed_special = output;
  malformed_special.terms->special_data_present = false;
  if (!xar::ck3_11906::SerializePendingCharacterInteractionContextV1(
           malformed_special)
           .empty()) {
    return Fail("serializer accepted available binding without special data");
  }

  fixture.Reset();
  fixture.SetSpecialWar("fixture_request_support_interaction", 0x44444444U);
  if (!Read(fixture, output) ||
      output.terms->special_war_binding.reason !=
          "special_interaction_subtype_opaque" ||
      fixture.common_war_relation_calls != 0 ||
      fixture.resolve_active_war_calls != 0) {
    return Fail("opaque special subtype crossed the exact allowlist");
  }

  fixture.Reset();
  fixture.SetSpecialWar("owner_deferred_religious_special_fixture",
                        0x55555555U);
  if (!Read(fixture, output) ||
      output.terms->special_war_binding.reason !=
          "special_interaction_subtype_opaque" ||
      fixture.common_war_relation_calls != 0 ||
      fixture.resolve_active_war_calls != 0) {
    return Fail("owner-deferred subtype crossed the exact allowlist");
  }

  fixture.Reset();
  fixture.SetSpecialWar("end_war_attacker_victory_interaction", 0x33333332U);
  if (!Read(fixture, output) ||
      output.terms->special_war_binding.reason !=
          "special_interaction_identity_mismatch" ||
      fixture.common_war_relation_calls != 0) {
    return Fail("definition/vptr mismatch was not typed unavailable");
  }

  fixture.Reset();
  fixture.SetSpecialWar("end_war_attacker_white_peace_interaction",
                        0x33333332U);
  Store(fixture.active_war, 0x28C, std::int32_t{9'001});
  if (!Read(fixture, output) ||
      output.terms->special_war_binding.reason !=
          "special_war_roles_mismatch" ||
      output.readiness.special_war_binding_ready) {
    return Fail("special-war primary-side mismatch was not rejected");
  }

  fixture.Reset();
  fixture.SetSpecialWar("end_war_attacker_white_peace_interaction",
                        0x33333332U);
  Store(fixture.actor_character, 0x18, std::int32_t{33'555'433});
  if (!Read(fixture, output) ||
      output.terms->special_war_binding.reason !=
          "special_war_binding_unavailable" ||
      fixture.common_war_relation_calls != 0) {
    return Fail("special-war actor generation mismatch leaked a binding");
  }

  fixture.Reset();
  fixture.SetSpecialWar("end_war_attacker_white_peace_interaction",
                        0x33333332U);
  Store(fixture.played_character, 0x18, std::int32_t{33'556'433});
  if (xar::ck3_11906::ReadPendingCharacterInteractionContextV1(
          Environment(fixture), Access(fixture), Request(), output) !=
          ReadPendingCharacterInteractionContextResultV1::unavailable ||
      output.reason != "played_character_generation_mismatch" ||
      fixture.common_war_relation_calls != 0) {
    return Fail("special-war recipient generation mismatch was not rejected");
  }

  fixture.Reset();
  fixture.SetSpecialWar("end_war_attacker_white_peace_interaction",
                        0x33333332U);
  Store(fixture.active_war, 0x08, std::int32_t{33'554'466});
  if (!Read(fixture, output) || output.terms->special_war_binding.reason !=
                                    "special_war_binding_unavailable") {
    return Fail("active CWar full identity mismatch leaked a binding");
  }

  fixture.Reset();
  fixture.SetSpecialWar("end_war_attacker_white_peace_interaction",
                        0x33333332U);
  Store(fixture.active_war, 0x358,
        static_cast<void *>(fixture.definition.data()));
  if (!Read(fixture, output) || output.terms->special_war_binding.reason !=
                                    "special_war_binding_unavailable") {
    return Fail("ended CWar leaked a special-war binding");
  }

  fixture.Reset();
  fixture.SetSpecialWar("end_war_attacker_white_peace_interaction",
                        0x33333332U);
  fixture.change_relation_between_observations = true;
  if (xar::ck3_11906::ReadPendingCharacterInteractionContextV1(
          Environment(fixture), Access(fixture), Request(), output) !=
          ReadPendingCharacterInteractionContextResultV1::unavailable ||
      output.reason != "state_changed") {
    return Fail("special-war relation pointer drift was not rejected");
  }

  fixture.Reset();
  fixture.SetSpecialWar("end_war_attacker_white_peace_interaction",
                        0x33333332U);
  fixture.change_special_vptr_between_observations = true;
  if (xar::ck3_11906::ReadPendingCharacterInteractionContextV1(
          Environment(fixture), Access(fixture), Request(), output) !=
          ReadPendingCharacterInteractionContextResultV1::unavailable ||
      output.reason != "state_changed") {
    return Fail("special-war vptr drift was not rejected");
  }

  fixture.Reset();
  fixture.valid_results[0] = false;
  if (!Read(fixture, output) || output.send_options->rows[0].is_valid ||
      output.send_options->rows[0].is_shown ||
      std::count(fixture.trigger_order.begin(), fixture.trigger_order.end(),
                 1) != 0) {
    return Fail("send-option is_valid did not short-circuit is_shown");
  }

  fixture.Reset();
  Store(fixture.pending, 0x10, std::int32_t{33'554'465});
  if (xar::ck3_11906::ReadPendingCharacterInteractionContextV1(
          Environment(fixture), Access(fixture), Request(), output) !=
          ReadPendingCharacterInteractionContextResultV1::unavailable ||
      output.reason != "pending_generation_mismatch" ||
      output.legality.accept.allowed ||
      output.readiness.not_ready_reasons !=
          std::vector<std::string>({"pending_generation_mismatch"}) ||
      !Contains(
          xar::ck3_11906::SerializePendingCharacterInteractionContextV1(output),
          "\"status\":\"unavailable\"")) {
    return Fail("generation mismatch did not fail closed");
  }

  fixture.Reset();
  Store(fixture.pending, 0x2F4, std::int32_t{9'001});
  if (xar::ck3_11906::ReadPendingCharacterInteractionContextV1(
          Environment(fixture), Access(fixture), Request(), output) !=
          ReadPendingCharacterInteractionContextResultV1::unavailable ||
      output.reason != "pending_not_routed_to_played_character" ||
      fixture.route_calls != 0) {
    return Fail("non-local responder was not rejected before native route");
  }

  fixture.Reset();
  constexpr std::int32_t intermediary_id = 3'001;
  fixture.SetPlayedCharacter(intermediary_id);
  Store(fixture.pending, 0x300, intermediary_id);
  Store(fixture.pending, 0x5C0, std::int32_t{1});
  fixture.validator_results[2] = false;
  if (!Read(fixture, output, intermediary_id) ||
      output.routing->current_responder_role != "intermediary" ||
      output.routing->reply_execution_channel != "intermediary" ||
      output.legality.block.allowed) {
    return Fail("intermediary route projection failed");
  }

  fixture.Reset();
  Store(fixture.pending, 0x5C0, std::int32_t{2});
  Store(fixture.pending, 0x5C6, std::uint8_t{1});
  Store(fixture.definition, 0x2A48, std::uint8_t{1});
  if (!Read(fixture, output) || output.legality.accept.allowed ||
      output.legality.reject.allowed || output.legality.block.allowed ||
      !output.legality.acknowledge.allowed || fixture.validator_calls != 0 ||
      !output.auto_accept->value) {
    return Fail(
        "ack channel consulted the enum-4 false seam or normal channel");
  }

  fixture.Reset();
  Store(fixture.definition, 0x2A48, std::uint8_t{1});
  fixture.validator_results = {true, false, false};
  if (!Read(fixture, output) || !output.legality.accept.allowed ||
      output.legality.reject.allowed || output.legality.block.allowed ||
      !output.auto_accept->value) {
    return Fail("exact auto-accept legality projection failed");
  }

  fixture.Reset();
  Store(fixture.definition, 0x2580,
        static_cast<void *>(fixture.definition.data() + 0x100));
  fixture.validator_results = {true, false, false};
  if (!Read(fixture, output) || !output.auto_accept->value ||
      output.legality.reject.allowed || output.legality.block.allowed ||
      std::count(fixture.trigger_order.begin(), fixture.trigger_order.end(),
                 99) != 2) {
    return Fail("auto-accept trigger was not evaluated in both observations");
  }

  fixture.Reset();
  Store(fixture.pending, 0x2F0, kPlayedCharacterId);
  fixture.validator_results = {true, false, false};
  if (!Read(fixture, output) || output.legality.reject.allowed ||
      output.legality.block.allowed) {
    return Fail("self-interaction reject/block boundary failed");
  }

  fixture.Reset();
  Store(fixture.pending, 0x324, std::int32_t{1});
  if (xar::ck3_11906::ReadPendingCharacterInteractionContextV1(
          Environment(fixture), Access(fixture), Request(), output) !=
          ReadPendingCharacterInteractionContextResultV1::invalid ||
      output.reason != "send_option_count_mismatch" ||
      output.legality.accept.allowed) {
    return Fail("send-option count mismatch did not become typed invalid");
  }

  fixture.Reset();
  Store(fixture.definition, 0x2554,
        xar::ck3_11906::kPendingInteractionMaximumSendOptionsV1 + 1);
  Store(fixture.pending, 0x324,
        xar::ck3_11906::kPendingInteractionMaximumSendOptionsV1 + 1);
  Store(fixture.pending, 0x320,
        xar::ck3_11906::kPendingInteractionMaximumSendOptionsV1 + 1);
  if (xar::ck3_11906::ReadPendingCharacterInteractionContextV1(
          Environment(fixture), Access(fixture), Request(), output) !=
          ReadPendingCharacterInteractionContextResultV1::invalid ||
      output.reason != "send_option_count_invalid") {
    return Fail("send-option implementation bound was not enforced");
  }

  fixture.Reset();
  fixture.pending[0x30A] = std::byte{0xAA};
  if (!Read(fixture, output) || output.target->present ||
      output.target->raw_envelope[2] != 0xAA ||
      output.target->type_key_status !=
          xar::game::PendingCharacterInteractionSemanticStatusV1::absent) {
    return Fail("absent target incorrectly required an all-zero opaque tail");
  }
  const auto valid_absent_target = output;
  if (xar::ck3_11906::SerializePendingCharacterInteractionContextV1(
          valid_absent_target)
          .empty()) {
    return Fail("serializer rejected an absent target opaque tail");
  }
  auto malformed_absent_target = valid_absent_target;
  malformed_absent_target.target->raw_envelope[0] = 1;
  if (!xar::ck3_11906::SerializePendingCharacterInteractionContextV1(
           malformed_absent_target)
           .empty()) {
    return Fail("serializer accepted an absent target envelope/index mismatch");
  }

  fixture.Reset();
  Store(fixture.pending, 0x5B8, std::int32_t{60});
  if (!Read(fixture, output) || output.deadline->remaining_days != 0 ||
      output.deadline->expiry_boundary_status !=
          "at_or_past_daily_expiry_queue_threshold") {
    return Fail("deadline expiry boundary was not projected exactly");
  }

  fixture.Reset();
  const std::array<std::uint8_t, 16> opaque_target{
      7, 0, 1, 0, 0x78, 0x56, 0x34, 0x12, 0, 0, 0, 0, 0, 0, 0, 0};
  std::memcpy(fixture.pending.data() + 0x308, opaque_target.data(),
              opaque_target.size());
  if (!Read(fixture, output) || !output.target->present ||
      output.target->raw_type_index != 7 ||
      output.target->type_key != fixture.target_type_key ||
      output.target->typed_identity_status !=
          xar::game::PendingCharacterInteractionSemanticStatusV1::unavailable ||
      output.readiness.target_typed_identity_ready ||
      output.readiness.not_ready_reasons.front() !=
          "target_generic_scope_payload_identity_not_closed" ||
      !Contains(
          xar::ck3_11906::SerializePendingCharacterInteractionContextV1(output),
          "\"raw_16_bytes_hex\":\"07000100785634120000000000000000\"")) {
    return Fail(
        "opaque target/type-key projection crossed typed identity seam");
  }
  auto malformed_generic_target = output;
  malformed_generic_target.target->raw_envelope[0] = 6;
  if (!xar::ck3_11906::SerializePendingCharacterInteractionContextV1(
           malformed_generic_target)
           .empty()) {
    return Fail("serializer accepted a generic target envelope/index mismatch");
  }

  fixture.Reset();
  fixture.SetCallAllyWarTarget();
  if (!Read(fixture, output) || !output.target->present ||
      output.target->raw_type_index != 16 ||
      output.target->type_key != "war" ||
      output.target->typed_identity_status !=
          xar::game::PendingCharacterInteractionSemanticStatusV1::available ||
      !output.target->typed_identity.has_value() ||
      *output.target->typed_identity != "war:67108946" ||
      !output.target->typed_identity_reason.empty() ||
      !output.readiness.target_typed_identity_ready ||
      std::find(output.readiness.not_ready_reasons.begin(),
                output.readiness.not_ready_reasons.end(),
                "target_generic_scope_payload_identity_not_closed") !=
          output.readiness.not_ready_reasons.end() ||
      fixture.resolve_active_war_calls != 2 ||
      !Contains(
          xar::ck3_11906::SerializePendingCharacterInteractionContextV1(output),
          "\"typed_identity\":\"war:67108946\"") ||
      !Contains(
          xar::ck3_11906::SerializePendingCharacterInteractionContextV1(output),
          "\"target_typed_identity_ready\":true")) {
    return Fail("exact call-ally war target identity was not published");
  }
  auto malformed_typed_target = output;
  malformed_typed_target.target->raw_envelope[0] = 15;
  if (!xar::ck3_11906::SerializePendingCharacterInteractionContextV1(
           malformed_typed_target)
           .empty()) {
    return Fail("serializer accepted a typed target envelope/index mismatch");
  }

  fixture.Reset();
  fixture.SetCallAllyWarTarget();
  fixture.call_ally_war_resolver_available = false;
  if (!Read(fixture, output) ||
      output.target->typed_identity_status !=
          xar::game::PendingCharacterInteractionSemanticStatusV1::unavailable ||
      output.target->typed_identity.has_value() ||
      output.target->typed_identity_reason !=
          "war_target_identity_unavailable" ||
      output.readiness.target_typed_identity_ready ||
      output.readiness.not_ready_reasons.empty() ||
      output.readiness.not_ready_reasons.front() !=
          "war_target_identity_unavailable" ||
      fixture.resolve_active_war_calls != 2 ||
      xar::ck3_11906::SerializePendingCharacterInteractionContextV1(output)
          .empty()) {
    return Fail("call-ally war resolver failure did not fail closed");
  }

  fixture.Reset();
  fixture.SetCallAllyWarTarget();
  Store(fixture.active_war, 0x08, std::int32_t{kCallAllyWarId + 1});
  if (!Read(fixture, output) ||
      output.target->typed_identity_status !=
          xar::game::PendingCharacterInteractionSemanticStatusV1::unavailable ||
      output.target->typed_identity.has_value() ||
      output.target->typed_identity_reason !=
          "war_target_identity_unavailable" ||
      output.readiness.target_typed_identity_ready ||
      fixture.resolve_active_war_calls != 2) {
    return Fail("call-ally war full-ID mismatch was not rejected");
  }

  fixture.Reset();
  // A different definition can carry the same generic type-16/war envelope;
  // without the canonical definition binding it must remain opaque and must
  // not invoke the active-war resolver.
  const std::uint16_t non_call_ally_type_index = 16;
  Store(fixture.pending, 0x308, non_call_ally_type_index);
  Store(fixture.pending, 0x310, kCallAllyWarId);
  fixture.definition_key = "request_contract_assistance_interaction";
  if (!Read(fixture, output) || !output.target->present ||
      output.target->raw_type_index != 16 || output.target->type_key != "war" ||
      output.target->typed_identity_status !=
          xar::game::PendingCharacterInteractionSemanticStatusV1::unavailable ||
      output.target->typed_identity.has_value() ||
      output.target->typed_identity_reason !=
          "generic_scope_payload_identity_not_closed" ||
      output.readiness.target_typed_identity_ready ||
      output.readiness.not_ready_reasons.empty() ||
      output.readiness.not_ready_reasons.front() !=
          "target_generic_scope_payload_identity_not_closed" ||
      fixture.resolve_active_war_calls != 0) {
    return Fail("non-call-ally type-16 war target crossed typed identity seam");
  }

  fixture.Reset();
  fixture.change_frame_on_final_capture = true;
  if (xar::ck3_11906::ReadPendingCharacterInteractionContextV1(
          Environment(fixture), Access(fixture), Request(), output) !=
          ReadPendingCharacterInteractionContextResultV1::unavailable ||
      output.reason != "state_changed") {
    return Fail("outer frame drift was not rejected");
  }

  fixture.Reset();
  fixture.change_selection_between_observations = true;
  if (xar::ck3_11906::ReadPendingCharacterInteractionContextV1(
          Environment(fixture), Access(fixture), Request(), output) !=
          ReadPendingCharacterInteractionContextResultV1::unavailable ||
      output.reason != "state_changed") {
    return Fail("same-frame inner observation drift was not rejected");
  }

  fixture.Reset();
  fixture.change_cost_between_observations = true;
  if (xar::ck3_11906::ReadPendingCharacterInteractionContextV1(
          Environment(fixture), Access(fixture), Request(), output) !=
          ReadPendingCharacterInteractionContextResultV1::unavailable ||
      output.reason != "state_changed") {
    return Fail("same-frame structured-cost drift was not rejected");
  }

  fixture.Reset();
  fixture.on_main_thread = false;
  if (xar::ck3_11906::ReadPendingCharacterInteractionContextV1(
          Environment(fixture), Access(fixture), Request(), output) !=
          ReadPendingCharacterInteractionContextResultV1::unavailable ||
      output.reason != "requires_application_main") {
    return Fail("application-main gate failed");
  }

  constexpr std::uintptr_t module = 0x140000000ULL;
  const auto bound =
      xar::ck3_11906::BindPendingCharacterInteractionNativeEnvironmentV1(module,
                                                                         true);
  if (reinterpret_cast<std::uintptr_t>(bound.pending_storage_slot) !=
          module + xar::ck3_11906::kPendingInteractionStorageSlotV1Rva ||
      reinterpret_cast<std::uintptr_t>(bound.target_type_registry) !=
          module + xar::ck3_11906::
                       kPendingInteractionTargetTypeRegistryGetterV1Rva ||
      reinterpret_cast<std::uintptr_t>(bound.cost_evaluator) !=
          module + xar::ck3_11906::kPendingInteractionCostEvaluatorV1Rva ||
      reinterpret_cast<std::uintptr_t>(bound.common_war_relation) !=
          module + xar::ck3_11906::kPendingInteractionCommonWarRelationV1Rva ||
      bound.reply_primary_vtable !=
          module + xar::ck3_11906::kPendingInteractionReplyPrimaryVtableV1Rva ||
      bound.war_white_peace_special_vtable !=
          module + xar::ck3_11906::
                       kPendingInteractionWarWhitePeaceSpecialVtableV1Rva) {
    return Fail("exact-build environment binding drifted");
  }

  std::cout << "pending-character-interaction-context-v1 reader passed\n";
  return 0;
}
