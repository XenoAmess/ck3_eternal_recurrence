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

constexpr std::int32_t kPendingId = 16'777'249;
constexpr std::int32_t kPlayedCharacterId = 2'001;
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
  xar::game::PendingCharacterInteractionFrameV1 frame{
      47, 53'175'816, true, true};
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
  std::array<std::byte, 0x2A60> definition{};
  std::vector<std::byte> rows = std::vector<std::byte>(2 * kRowStride);
  std::array<std::uint8_t, 2> selected{1, 0};
  std::array<std::byte, 0x20> target_registry{};
  std::vector<std::byte> target_registry_entries =
      std::vector<std::byte>(8 * 0x50);
  std::string definition_key = "fixture_request_support_interaction";
  std::string target_type_key = "fixture_generic_target_type";
  std::int32_t expiration_days = 60;
  bool on_main_thread = true;
  bool local_route = true;
  std::array<bool, 3> validator_results{true, true, true};
  std::array<bool, 2> shown_results{true, true};
  std::array<bool, 2> valid_results{true, true};
  bool change_frame_on_final_capture = false;
  bool change_selection_between_observations = false;
  std::int32_t capture_calls = 0;
  std::int32_t route_calls = 0;
  std::int32_t validator_calls = 0;
  std::int32_t selected_read_calls = 0;
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
    definition.fill(std::byte{});
    std::fill(rows.begin(), rows.end(), std::byte{});
    selected = {1, 0};
    target_registry.fill(std::byte{});
    std::fill(target_registry_entries.begin(),
              target_registry_entries.end(), std::byte{});
    expiration_days = 60;
    pending_storage_pointer = pending_storage.data();
    character_storage_pointer = character_storage.data();
    on_main_thread = true;
    local_route = true;
    validator_results = {true, true, true};
    shown_results = {true, true};
    valid_results = {true, true};
    change_frame_on_final_capture = false;
    change_selection_between_observations = false;
    capture_calls = 0;
    route_calls = 0;
    validator_calls = 0;
    selected_read_calls = 0;
    trigger_order.clear();

    Store(pending_storage, 0x20,
          static_cast<void *>(pending_slots.data()));
    Store(pending_storage, 0x2C,
          static_cast<std::int32_t>(kPendingSlotCount));
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
    Store(target_registry, 0x0C, std::int32_t{8});
    Store(target_registry_entries, 7 * 0x50, std::int32_t{77'007});
  }

  void SetPlayedCharacter(std::int32_t character_id) {
    std::fill(character_slots.begin(), character_slots.end(), std::byte{});
    const auto index = static_cast<std::uint32_t>(character_id) & 0x00FFFFFFU;
    if (index >= kCharacterSlotCount) {
      std::abort();
    }
    Store(character_storage, 0x20,
          static_cast<void *>(character_slots.data()));
    Store(character_storage, 0x2C,
          static_cast<std::int32_t>(kCharacterSlotCount));
    Store(character_slots, static_cast<std::size_t>(index) * 0x10 + 0x08,
          static_cast<void *>(played_character.data()));
    Store(played_character, 0x18, character_id);
  }
};

bool DummyRoute(void *, void *) { return false; }
bool DummyValidator(void *) { return false; }
bool DummyTrigger(void *, const void *) { return false; }
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
  if (address >= fixture.selected.data() &&
      address < fixture.selected.data() + fixture.selected.size() &&
      size == 1) {
    ++fixture.selected_read_calls;
    if (fixture.change_selection_between_observations &&
        fixture.selected_read_calls > 2 &&
        address == fixture.selected.data()) {
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
  return false;
}

bool InvokeRoute(
    void *context, xar::ck3_11906::NativePendingInteractionLocalRoutingV1,
    void *pending, void *character, bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.route_calls;
  output = fixture.local_route && pending == fixture.pending.data() &&
           character == fixture.played_character.data();
  return true;
}

bool InvokeValidator(
    void *context, xar::ck3_11906::NativePendingInteractionReplyValidatorV1,
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

bool InvokeTrigger(
    void *context, xar::ck3_11906::NativePendingInteractionTriggerEvaluatorV1,
    void *trigger, const void *scope, bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (scope != fixture.pending.data() + 0x20) {
    return false;
  }
  for (std::int32_t index = 0; index < 2; ++index) {
    auto *row = fixture.rows.data() +
                static_cast<std::size_t>(index) * kRowStride;
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
  output = identifier == 77'007 ? &fixture.target_type_key : nullptr;
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
  output.target_type_registry = DummyRegistry;
  output.script_identifier_name = DummyIdentifier;
  output.reply_primary_vtable = 0x11111111U;
  output.reply_secondary_vtable = 0x22222222U;
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
  output.invoke_target_type_registry = InvokeRegistry;
  output.invoke_script_identifier_name = InvokeIdentifier;
  return output;
}

xar::ck3_11906::PendingCharacterInteractionContextRequestV1 Request(
    std::int32_t played_character_id = kPlayedCharacterId) {
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
      !output.roles.has_value() ||
      output.roles->actor_character_id != 1'001 ||
      !output.routing.has_value() ||
      output.routing->current_responder_role != "recipient" ||
      output.routing->reply_execution_channel != "recipient" ||
      !output.routing->local_route ||
      !output.deadline.has_value() || output.deadline->remaining_days != 43 ||
      !output.send_options.has_value() ||
      output.send_options->rows.size() != 2 ||
      !output.send_options->rows[0].selected ||
      output.send_options->rows[1].selected ||
      !output.legality.accept.allowed || !output.legality.reject.allowed ||
      !output.legality.block.allowed || output.legality.acknowledge.allowed ||
      output.readiness.interaction_semantic_decision_ready ||
      fixture.route_calls != 2 || fixture.validator_calls != 6 ||
      fixture.trigger_order !=
          std::vector<std::int32_t>({0, 1, 2, 3, 0, 1, 2, 3})) {
    return Fail("ordinary recipient projection or trigger order failed");
  }
  const auto serialized =
      xar::ck3_11906::SerializePendingCharacterInteractionContextV1(output);
  if (!Contains(serialized,
                "\"schema\":\"pending-character-interaction-context-v1\"") ||
      !Contains(serialized, "\"remaining_days\":43") ||
      !Contains(serialized,
                "\"interaction_semantic_decision_ready\":false") ||
      !Contains(serialized, "\"terms\":{") ||
      !Contains(serialized, "\"value\":null")) {
    return Fail("available serializer contract failed");
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
    return Fail("ack channel consulted the enum-4 false seam or normal channel");
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

  fixture.Reset();
  Store(fixture.pending, 0x5B8, std::int32_t{60});
  if (!Read(fixture, output) || output.deadline->remaining_days != 0 ||
      output.deadline->expiry_boundary_status !=
          "at_or_past_daily_expiry_queue_threshold") {
    return Fail("deadline expiry boundary was not projected exactly");
  }

  fixture.Reset();
  const std::array<std::uint8_t, 16> opaque_target{
      7, 0, 1, 0, 0x78, 0x56, 0x34, 0x12,
      0, 0, 0, 0, 0, 0, 0, 0};
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
    return Fail("opaque target/type-key projection crossed typed identity seam");
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
  fixture.on_main_thread = false;
  if (xar::ck3_11906::ReadPendingCharacterInteractionContextV1(
          Environment(fixture), Access(fixture), Request(), output) !=
          ReadPendingCharacterInteractionContextResultV1::unavailable ||
      output.reason != "requires_application_main") {
    return Fail("application-main gate failed");
  }

  constexpr std::uintptr_t module = 0x140000000ULL;
  const auto bound =
      xar::ck3_11906::BindPendingCharacterInteractionNativeEnvironmentV1(
          module, true);
  if (reinterpret_cast<std::uintptr_t>(bound.pending_storage_slot) !=
          module + xar::ck3_11906::kPendingInteractionStorageSlotV1Rva ||
      reinterpret_cast<std::uintptr_t>(bound.target_type_registry) !=
          module +
              xar::ck3_11906::kPendingInteractionTargetTypeRegistryGetterV1Rva ||
      bound.reply_primary_vtable !=
          module +
              xar::ck3_11906::kPendingInteractionReplyPrimaryVtableV1Rva) {
    return Fail("exact-build environment binding drifted");
  }

  std::cout << "pending-character-interaction-context-v1 reader passed\n";
  return 0;
}
