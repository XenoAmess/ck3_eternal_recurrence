#include "xar_bridge/character_interaction_proposal_native_binder_v1.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {

namespace ck3 = xar::ck3_11906;
namespace game = xar::game;

constexpr std::uintptr_t kModuleBase = 0x10000000U;
constexpr std::int32_t kActorId = 0x11000001;
constexpr std::int32_t kRecipientId = 0x22000002;
constexpr std::int32_t kGuardianId = 0x33000003;
constexpr std::int32_t kWardId = 0x44000004;
constexpr std::size_t kDefinitionSize = 0x2600;
constexpr std::size_t kContextSize =
    ck3::kCharacterInteractionProposalNativeContextSizeV1;
constexpr std::size_t kCommandSize =
    ck3::kCharacterInteractionProposalNativeCommandSizeV1;

void Require(bool condition, std::string_view message) {
  if (!condition) throw std::runtime_error(std::string(message));
}

template <typename T, std::size_t Size>
void Store(std::array<std::byte, Size> &target, std::size_t offset,
           const T &value) {
  Require(offset + sizeof(value) <= target.size(), "fixture store overflow");
  std::memcpy(target.data() + offset, &value, sizeof(value));
}

template <typename T>
void StoreRaw(void *target, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(target) + offset, &value,
              sizeof(value));
}

struct CharacterObject {
  std::array<std::byte, 0x30> bytes{};
};

struct Fixture {
  std::array<std::byte, kDefinitionSize> definition{};
  std::array<std::byte, 0x40> character_storage{};
  std::array<std::byte, 0x40> title_storage{};
  std::array<std::byte, 0x100> character_slots{};
  std::array<std::byte, 0x40> title_slots{};
  std::array<CharacterObject, 4> characters{};
  void *character_storage_pointer = character_storage.data();
  void *title_storage_pointer = title_storage.data();
  std::array<std::uint8_t, 4> selected_options{};
  ck3::CharacterInteractionProposalNativeCaptureV1 captures[2]{};
  int capture_index = 0;
  int construct_calls = 0;
  int materialize_calls = 0;
  int refresh_calls = 0;
  int finalize_calls = 0;
  int can_send_calls = 0;
  int command_calls = 0;
  int submit_calls = 0;
  int destroy_calls = 0;
  bool materialize_payload_drift = false;
  bool can_send = true;
  bool command_wrong_vtable = false;
  bool submit_result = true;

  static thread_local Fixture *active;

  Fixture() {
    void *slots = character_slots.data();
    Store(character_storage, 0x20, slots);
    const std::int32_t capacity = 16;
    Store(character_storage, 0x2C, capacity);
    void *title_slot_data = title_slots.data();
    Store(title_storage, 0x20, title_slot_data);
    Store(title_storage, 0x2C, capacity);
    const std::array<std::int32_t, 4> ids{
        kActorId, kRecipientId, kGuardianId, kWardId};
    for (std::size_t index = 0; index < ids.size(); ++index) {
      Store(characters[index].bytes, 0x18, ids[index]);
      void *object = characters[index].bytes.data();
      const auto slot = static_cast<std::size_t>(ids[index] & 0x00FFFFFF) *
                        0x10 + 0x08;
      Store(character_slots, slot, object);
    }
    const std::int32_t option_count = 0;
    Store(definition, 0x2554, option_count);
  }

  static void *GetDatabase() { return active; }

  static std::int32_t Hash(void *database, const char *data,
                           std::uint32_t size) {
    if (database != active || data == nullptr || size == 0) return 0;
    return 0x12345678;
  }

  static void *Lookup(void *database, std::int32_t hash) {
    return database == active && hash == 0x12345678
               ? active->definition.data()
               : nullptr;
  }

  static void *Construct(void *storage, void *definition,
                         std::int32_t actor_id, std::int32_t recipient_id,
                         void *, bool initialize_options) {
    ++active->construct_calls;
    if (storage == nullptr || definition != active->definition.data() ||
        !initialize_options) {
      return nullptr;
    }
    std::memset(storage, 0, kContextSize);
    StoreRaw(storage, 0x00, definition);
    StoreRaw(storage, 0x2D8, actor_id);
    StoreRaw(storage, 0x2DC, recipient_id);
    const std::int32_t invalid = -1;
    StoreRaw(storage, 0x2E0, invalid);
    StoreRaw(storage, 0x2E4, invalid);
    StoreRaw(storage, 0x2E8, invalid);
    return storage;
  }

  static bool Materialize(
      void *context, const game::CharacterInteractionProposalPayloadSourceV1 &source,
      void *storage, std::size_t storage_size, void *definition,
      void *&output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.materialize_calls;
    output = nullptr;
    if (storage == nullptr || storage_size != kContextSize ||
        definition != self.definition.data()) {
      return false;
    }
    std::memset(storage, 0, storage_size);
    StoreRaw(storage, 0x00, definition);
    StoreRaw(storage, 0x2D8, source.actor_character_id);
    StoreRaw(storage, 0x2DC, source.recipient_character_id);
    auto secondary_actor = source.secondary_actor_character_id;
    if (self.materialize_payload_drift) secondary_actor = kActorId;
    StoreRaw(storage, 0x2E0, secondary_actor);
    StoreRaw(storage, 0x2E4, source.secondary_recipient_character_id);
    StoreRaw(storage, 0x2E8, source.intermediary_character_id);
    void *options = nullptr;
    const std::int32_t zero = 0;
    StoreRaw(storage, 0x300, options);
    StoreRaw(storage, 0x308, zero);
    StoreRaw(storage, 0x30C, zero);
    output = storage;
    return true;
  }

  static void Refresh(void *context, bool refresh) {
    if (context != nullptr && refresh) ++active->refresh_calls;
  }

  static void Finalize(void *context) {
    if (context != nullptr) ++active->finalize_calls;
  }

  static bool CanSend(void *context, void *) {
    if (context == nullptr) return false;
    ++active->can_send_calls;
    return active->can_send;
  }

  static void Destroy(void *context) {
    if (context == nullptr) return;
    ++active->destroy_calls;
    void *empty = nullptr;
    StoreRaw(context, 0x00, empty);
  }

  static void *ConstructCommand(void *storage, const void *context) {
    ++active->command_calls;
    if (storage == nullptr || context == nullptr) return nullptr;
    std::memset(storage, 0, kCommandSize);
    const auto primary = active->command_wrong_vtable
                             ? std::uintptr_t{0xBAD}
                             : kModuleBase +
                                   ck3::kCharacterInteractionProposalCommandPrimaryVtableRvaV1;
    const auto secondary =
        kModuleBase +
        ck3::kCharacterInteractionProposalCommandSecondaryVtableRvaV1;
    StoreRaw(storage, 0x00, primary);
    StoreRaw(storage, 0x18, secondary);
    std::memcpy(static_cast<std::byte *>(storage) + 0x20, context,
                kContextSize);
    return storage;
  }

  static bool Submit(void *manager, void *command, std::uint32_t flags) {
    if (manager != active || command == nullptr ||
        flags != ck3::kCharacterInteractionProposalSubmitFlagsV1) {
      return false;
    }
    ++active->submit_calls;
    return active->submit_result;
  }

  static bool ReadMemory(void *, const void *address, void *output,
                         std::size_t size) noexcept {
    if (address == nullptr || output == nullptr || size == 0) return false;
    std::memcpy(output, address, size);
    return true;
  }

  static bool Capture(
      void *context,
      const game::CharacterInteractionProposalActionRequestV1 &,
      ck3::CharacterInteractionProposalNativeCaptureV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    const int index = self.capture_index < 2 ? self.capture_index : 1;
    output = self.captures[index];
    ++self.capture_index;
    return true;
  }

  ck3::CharacterInteractionProposalNativeBinderEnvironmentV1 Environment() {
    active = this;
    ck3::CharacterInteractionProposalNativeBinderEnvironmentV1 value{};
    value.module_base = kModuleBase;
    value.exact_build_admitted = true;
    value.admitted_executable_sha256 =
        ck3::kCharacterInteractionProposalNativeBinderExecutableSha256V1;
    value.offline_fixture = true;
    value.memory_context = this;
    value.read_memory = &ReadMemory;
    value.character_storage_slot = &character_storage_pointer;
    value.landed_title_storage_slot = &title_storage_pointer;
    value.get_database = &GetDatabase;
    value.hash_stable_key = &Hash;
    value.lookup_definition = &Lookup;
    value.construct_two_role_context = &Construct;
    value.refresh_context = &Refresh;
    value.finalize_context = &Finalize;
    value.complete_can_send = &CanSend;
    value.destroy_context = &Destroy;
    value.command_manager = this;
    value.construct_command = &ConstructCommand;
    value.submit_command = &Submit;
    value.command_primary_vtable =
        kModuleBase +
        ck3::kCharacterInteractionProposalCommandPrimaryVtableRvaV1;
    value.command_secondary_vtable =
        kModuleBase +
        ck3::kCharacterInteractionProposalCommandSecondaryVtableRvaV1;
    value.capture_context = this;
    value.capture = &Capture;
    value.special_materializer_context = this;
    value.materialize_special_context = &Materialize;
    return value;
  }
};

thread_local Fixture *Fixture::active = nullptr;

void SetSnapshot(std::array<char, game::kCharacterInteractionPreviewSnapshotIdCapacityV1> &target,
                 std::string_view value) {
  Require(value.size() < target.size(), "snapshot too long");
  std::copy(value.begin(), value.end(), target.begin());
}

ck3::CharacterInteractionProposalNativeCaptureV1 GoodCapture(
    std::string_view key, bool special) {
  ck3::CharacterInteractionProposalNativeCaptureV1 value{};
  auto &preview = value.envelope.preview;
  preview.status = game::CharacterInteractionPreviewStatusV1::available;
  preview.unavailable_reason = game::CharacterInteractionPreviewFailureV1::none;
  SetSnapshot(preview.snapshot_id, "diplo6-snapshot");
  preview.public_revision = 101;
  preview.native_revision = 201;
  preview.proof_epoch = 301;
  preview.date_raw = 401;
  preview.definition.canonical_key.assign(key);
  preview.definition.deterministic_key_hash = 0x12345678U;
  preview.definition.runtime_ordinal = 17;
  preview.roles.actor_character_id = kActorId;
  preview.roles.recipient_character_id = kRecipientId;
  preview.can_send = true;
  preview.costs.raw_scale = game::kCharacterInteractionPreviewRawScaleV1;
  preview.costs.raw.fill(0);
  preview.acceptance.kind = game::CharacterInteractionAcceptanceKindV1::auto_accept;
  preview.acceptance.auto_accept = true;
  preview.acceptance.would_accept_now_present = true;
  preview.acceptance.would_accept_now = true;
  preview.readiness = {true, true, true, true, true, true, true, true};
  auto &payload = value.envelope.payload;
  payload.complete = true;
  payload.semantic_subject_character_id = special ? kWardId : kRecipientId;
  payload.semantic_object_character_id = special ? kGuardianId : kActorId;
  payload.selected_title_count = 0;
  payload.fingerprint = special
                            ? "cipps:v1:educate_child_interaction:a=285212673:r=570425346:sa=855638019:sr=1140850692:i=-1:o=0:t="
                            : "two-role-fingerprint";
  value.typed_payload_source_present = special;
  if (special) {
    auto &source = value.typed_payload_source;
    source.available = true;
    source.failure =
        game::CharacterInteractionProposalPayloadSourceFailureV1::none;
    source.reason = "available";
    source.snapshot_id = preview.snapshot_id;
    source.public_revision = preview.public_revision;
    source.native_revision = preview.native_revision;
    source.proof_epoch = preview.proof_epoch;
    source.date_raw = preview.date_raw;
    source.interaction_key.assign(key);
    source.actor_character_id = kActorId;
    source.recipient_character_id = kRecipientId;
    source.secondary_actor_character_id = kGuardianId;
    source.secondary_recipient_character_id = kWardId;
    source.intermediary_character_id = -1;
    source.selected_option_mask = 0;
    source.payload = payload;
  }
  return value;
}

game::CharacterInteractionProposalActionRequestV1 GoodRequest(
    const ck3::CharacterInteractionProposalNativeCaptureV1 &capture) {
  const auto &preview = capture.envelope.preview;
  const auto &payload = capture.envelope.payload;
  game::CharacterInteractionProposalActionRequestV1 request{};
  request.request_id = "g2-m5-diplo6-request";
  request.expected_snapshot_id = "diplo6-snapshot";
  request.expected_public_revision = preview.public_revision;
  request.expected_native_revision = preview.native_revision;
  request.expected_proof_epoch = preview.proof_epoch;
  request.expected_date_raw = preview.date_raw;
  request.interaction_key = preview.definition.canonical_key;
  request.actor_character_id = preview.roles.actor_character_id;
  request.recipient_character_id = preview.roles.recipient_character_id;
  request.semantic_subject_character_id =
      payload.semantic_subject_character_id;
  request.semantic_object_character_id = payload.semantic_object_character_id;
  request.selected_title_count = payload.selected_title_count;
  request.payload_fingerprint = payload.fingerprint;
  request.budget.maximum_actor_spend_raw.fill(0);
  return request;
}

void Prepare(Fixture &fixture, std::string_view key, bool special) {
  fixture.captures[0] = GoodCapture(key, special);
  fixture.captures[1] = fixture.captures[0];
}

game::CharacterInteractionProposalActionAckV1 Execute(
    Fixture &fixture, ck3::CharacterInteractionProposalNativeBinderStateV1 &state,
    std::string_view key, bool special) {
  Prepare(fixture, key, special);
  state.environment = fixture.Environment();
  auto request = GoodRequest(fixture.captures[0]);
  game::CharacterInteractionProposalActionAckV1 ack{};
  ck3::ExecuteCharacterInteractionProposalFromNativeBinderV1(state, request,
                                                              ack);
  return ack;
}

void TestExactEnvironmentAndConfigurationGates() {
  const auto bound =
      ck3::BindCharacterInteractionProposalNativeBinderEnvironmentV1(
          kModuleBase, true,
          ck3::kCharacterInteractionProposalNativeBinderExecutableSha256V1);
  Require(reinterpret_cast<std::uintptr_t>(bound.get_database) ==
              kModuleBase +
                  ck3::kCharacterInteractionProposalDatabaseGetterRvaV1 &&
              reinterpret_cast<std::uintptr_t>(bound.construct_command) ==
                  kModuleBase +
                      ck3::kCharacterInteractionProposalConstructCommandRvaV1 &&
              bound.command_primary_vtable ==
                  kModuleBase +
                      ck3::kCharacterInteractionProposalCommandPrimaryVtableRvaV1,
          "exact environment did not bind frozen addresses");

  Fixture fixture;
  ck3::CharacterInteractionProposalNativeBinderStateV1 state{};
  state.environment = fixture.Environment();
  state.environment.admitted_executable_sha256 = "wrong";
  Require(ck3::ConfigureCharacterInteractionProposalNativeBinderV1(state) ==
              ck3::CharacterInteractionProposalNativeBindResultV1::blocked &&
              ck3::ReadCharacterInteractionProposalNativeBinderFailureV1(
                  state) == ck3::CharacterInteractionProposalNativeBinderFailureV1::
                                exact_build_not_admitted,
          "wrong executable hash must stay blocked");
  state.environment = fixture.Environment();
  state.environment.capture = nullptr;
  Require(ck3::ConfigureCharacterInteractionProposalNativeBinderV1(state) ==
              ck3::CharacterInteractionProposalNativeBindResultV1::blocked,
          "missing capture must stay blocked");
  state.environment = fixture.Environment();
  state.environment.materialize_special_context = nullptr;
  Require(ck3::ConfigureCharacterInteractionProposalNativeBinderV1(state) ==
              ck3::CharacterInteractionProposalNativeBindResultV1::blocked,
          "missing typed materializer must stay blocked");
}

void TestTwoRoleSubmitOnceAndCleanup() {
  Fixture fixture;
  ck3::CharacterInteractionProposalNativeBinderStateV1 state{};
  const auto ack = Execute(fixture, state, "gift_interaction", false);
  Require(ack.status == game::CharacterInteractionProposalActionAckStatusV1::
                            submitted_verification_pending &&
              ack.verification_pending && fixture.capture_index == 2 &&
              fixture.construct_calls == 1 && fixture.materialize_calls == 0 &&
              fixture.refresh_calls == 1 && fixture.finalize_calls == 1 &&
              fixture.can_send_calls == 1 && fixture.command_calls == 1 &&
              fixture.submit_calls == 1 && fixture.destroy_calls == 2,
          "two-role binder did not submit and clean both owned contexts once");
  Require(ck3::ReadCharacterInteractionProposalNativeBinderFailureV1(state) ==
              ck3::CharacterInteractionProposalNativeBinderFailureV1::none,
          "successful submit retained a binder failure");
}

void TestTypedSpecialRereadAndDrift() {
  {
    Fixture fixture;
    ck3::CharacterInteractionProposalNativeBinderStateV1 state{};
    const auto ack =
        Execute(fixture, state, "educate_child_interaction", true);
    if (!(ack.status == game::CharacterInteractionProposalActionAckStatusV1::
                           submitted_verification_pending &&
          fixture.materialize_calls == 1 && fixture.submit_calls == 1 &&
          fixture.destroy_calls == 2)) {
      throw std::runtime_error(
          "typed special did not survive DIPLO5 reconstruction reread: " +
          ack.reason);
    }
  }
  {
    Fixture fixture;
    Prepare(fixture, "educate_child_interaction", true);
    fixture.captures[1].typed_payload_source.secondary_actor_character_id =
        kActorId;
    ck3::CharacterInteractionProposalNativeBinderStateV1 state{};
    state.environment = fixture.Environment();
    auto request = GoodRequest(fixture.captures[0]);
    game::CharacterInteractionProposalActionAckV1 ack{};
    ck3::ExecuteCharacterInteractionProposalFromNativeBinderV1(state, request,
                                                                ack);
    Require(ack.status == game::CharacterInteractionProposalActionAckStatusV1::
                              rejected_before_submit &&
                ack.reason == "capture_drift" && fixture.submit_calls == 0,
            "typed source drift reached submit");
  }
  {
    Fixture fixture;
    fixture.materialize_payload_drift = true;
    ck3::CharacterInteractionProposalNativeBinderStateV1 state{};
    const auto ack =
        Execute(fixture, state, "educate_child_interaction", true);
    Require(ack.status == game::CharacterInteractionProposalActionAckStatusV1::
                              rejected_before_submit &&
                ack.reason == "typed_payload_source_mismatch" &&
                fixture.submit_calls == 0 && fixture.destroy_calls == 1,
            "materialized typed payload drift reached command queue");
  }
}

void TestIdentityCanSendCommandAndQueueFailures() {
  {
    Fixture fixture;
    std::int32_t stale = kRecipientId + 0x01000000;
    Store(fixture.characters[1].bytes, 0x18, stale);
    ck3::CharacterInteractionProposalNativeBinderStateV1 state{};
    const auto ack = Execute(fixture, state, "gift_interaction", false);
    Require(ack.reason == "character_identity_unavailable" &&
                fixture.construct_calls == 0 && fixture.submit_calls == 0,
            "generation mismatch was not rejected before construction");
  }
  {
    Fixture fixture;
    fixture.can_send = false;
    ck3::CharacterInteractionProposalNativeBinderStateV1 state{};
    const auto ack = Execute(fixture, state, "gift_interaction", false);
    Require(ack.reason == "complete_can_send_rejected" &&
                fixture.command_calls == 0 && fixture.destroy_calls == 1,
            "fresh complete Can Send false reached command construction");
  }
  {
    Fixture fixture;
    fixture.command_wrong_vtable = true;
    ck3::CharacterInteractionProposalNativeBinderStateV1 state{};
    const auto ack = Execute(fixture, state, "gift_interaction", false);
    Require(ack.reason == "command_identity_mismatch" &&
                fixture.submit_calls == 0 && fixture.destroy_calls == 2,
            "wrong command vtable reached queue");
  }
  {
    Fixture fixture;
    fixture.submit_result = false;
    ck3::CharacterInteractionProposalNativeBinderStateV1 state{};
    const auto ack = Execute(fixture, state, "gift_interaction", false);
    Require(ack.reason == "command_queue_rejected" &&
                fixture.submit_calls == 1 && fixture.destroy_calls == 2 &&
                !state.action_state.submission_in_flight,
            "queue rejection was promoted to pending action state");
  }
}

} // namespace

int main() {
  struct Case {
    const char *name;
    void (*run)();
  };
  constexpr Case cases[] = {
      {"exact_environment_configuration",
       &TestExactEnvironmentAndConfigurationGates},
      {"two_role_submit_once_cleanup", &TestTwoRoleSubmitOnceAndCleanup},
      {"typed_special_reread_drift", &TestTypedSpecialRereadAndDrift},
      {"identity_can_send_command_queue_failures",
       &TestIdentityCanSendCommandAndQueueFailures},
  };
  int failures = 0;
  for (const auto &test : cases) {
    try {
      test.run();
      std::cout << "PASS " << test.name << '\n';
    } catch (const std::exception &error) {
      ++failures;
      std::cerr << "FAIL " << test.name << ": " << error.what() << '\n';
    }
  }
  std::cout << (std::size(cases) - static_cast<std::size_t>(failures)) << '/'
            << std::size(cases) << " passed\n";
  return failures == 0 ? 0 : 1;
}
