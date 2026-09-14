#include "xar_bridge/character_interaction_preview_v1_source_adapter.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>

namespace {

namespace game = xar::game;
namespace ck3 = xar::ck3_11906;

constexpr std::uintptr_t kModuleBase = 0x140000000ULL;
constexpr std::int32_t kActorId = 0x01000002;
constexpr std::int32_t kRecipientId = 0x02000003;
constexpr std::int32_t kIntermediaryId = 0x03000004;
constexpr std::uint32_t kGiftHash = 0xD15EA5EDU;

template <typename Value, std::size_t Size>
void Put(std::array<std::byte, Size> &bytes, std::size_t offset,
         Value value) {
  assert(offset + sizeof(value) <= bytes.size());
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

struct Fixture {
  ck3::CharacterInteractionPreviewFrameV1 before{};
  ck3::CharacterInteractionPreviewFrameV1 after{};
  std::array<std::byte, 0x2A60> definition{};
  std::array<char, 32> definition_key{};
  std::array<std::byte, 0x40> storage{};
  std::array<std::byte, 8 * 0x10> slots{};
  std::array<std::byte, 0x200> actor{};
  std::array<std::byte, 0x200> recipient{};
  std::array<std::int64_t, game::kCharacterInteractionPreviewCostCountV1>
      costs{2'500'000, 0, 0, -100'000, 0, 0, 0, 0, 0, 0};
  bool main_thread = true;
  bool can_send = true;
  bool human_recipient = false;
  bool trigger_result = false;
  bool fail_destroy = false;
  bool drift_second_cost_sample = false;
  std::int64_t intermediary_raw = 700'000;
  std::int64_t recipient_raw = 12'500'000;
  std::int32_t outer_status = 0;
  std::int32_t intermediary_id = -1;
  std::int32_t capture_calls = 0;
  std::int32_t database_calls = 0;
  std::int32_t hash_calls = 0;
  std::int32_t lookup_calls = 0;
  std::int32_t construct_calls = 0;
  std::int32_t refresh_calls = 0;
  std::int32_t finalize_calls = 0;
  std::int32_t can_send_calls = 0;
  std::int32_t cost_calls = 0;
  std::int32_t trigger_calls = 0;
  std::int32_t human_calls = 0;
  std::int32_t intermediary_calls = 0;
  std::int32_t recipient_calls = 0;
  std::int32_t outer_calls = 0;
  std::int32_t destroy_calls = 0;
  void *active_context = nullptr;
};

void AssignSnapshotId(
    std::array<char, game::kCharacterInteractionPreviewSnapshotIdCapacityV1>
        &output,
    std::string_view value) {
  assert(value.size() < output.size());
  std::copy(value.begin(), value.end(), output.begin());
}

Fixture BaseFixture() {
  Fixture fixture{};
  AssignSnapshotId(fixture.before.snapshot_id, "diplomatic-frame-17");
  fixture.before.public_revision = 41;
  fixture.before.native_revision = 73;
  fixture.before.proof_epoch = 101;
  fixture.before.date_raw = 9001;
  fixture.before.paused = true;
  fixture.before.map_ready = true;
  fixture.before.has_played_character = true;
  fixture.before.played_character_alive = true;
  fixture.before.played_character_id = kActorId;
  fixture.after = fixture.before;

  constexpr std::string_view key = "gift_interaction";
  std::copy(key.begin(), key.end(), fixture.definition_key.begin());
  Put(fixture.definition, 0x10, std::int32_t{87});
  Put(fixture.definition, 0x14, kGiftHash);
  Put(fixture.definition, 0x28, static_cast<std::size_t>(key.size()));
  Put(fixture.definition, 0x30, std::size_t{31});
  Put(fixture.definition, 0x2580, static_cast<void *>(nullptr));
  Put(fixture.definition, 0x2A48, std::uint8_t{0});

  Put(fixture.storage, 0x2C, std::int32_t{8});
  Put(fixture.actor, 0x18, kActorId);
  Put(fixture.actor, 0x1C8, std::uintptr_t{0});
  Put(fixture.recipient, 0x18, kRecipientId);
  Put(fixture.recipient, 0x1C8, std::uintptr_t{0});
  return fixture;
}

void RepairPointers(Fixture &fixture) {
  Put(fixture.definition, 0x18,
      reinterpret_cast<std::uintptr_t>(fixture.definition_key.data()));
  Put(fixture.storage, 0x20,
      reinterpret_cast<std::uintptr_t>(fixture.slots.data()));
  Put(fixture.slots, 2 * 0x10 + 0x08,
      reinterpret_cast<std::uintptr_t>(fixture.actor.data()));
  Put(fixture.slots, 3 * 0x10 + 0x08,
      reinterpret_cast<std::uintptr_t>(fixture.recipient.data()));
}

bool Capture(void *context,
             ck3::CharacterInteractionPreviewFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.capture_calls++ == 0 ? fixture.before : fixture.after;
  return true;
}

bool MainThread(void *context) noexcept {
  return static_cast<Fixture *>(context)->main_thread;
}

bool GetDatabase(void *context, std::uintptr_t module,
                 void *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.database_calls;
  output = module == kModuleBase ? &fixture.storage : nullptr;
  return output != nullptr;
}

bool HashStableKey(void *context, std::uintptr_t module, void *database,
                   std::string_view key, std::int32_t &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.hash_calls;
  if (module != kModuleBase || database != &fixture.storage ||
      key != "gift_interaction") {
    return false;
  }
  output = static_cast<std::int32_t>(kGiftHash);
  return true;
}

bool LookupDefinition(void *context, std::uintptr_t module, void *database,
                      std::int32_t key_hash, void *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.lookup_calls;
  if (module != kModuleBase || database != &fixture.storage ||
      static_cast<std::uint32_t>(key_hash) != kGiftHash) {
    output = nullptr;
    return false;
  }
  output = fixture.definition.data();
  return true;
}

bool ConstructContext(void *context, std::uintptr_t module,
                      void *context_storage, void *definition,
                      std::int32_t actor_character_id,
                      std::int32_t recipient_character_id,
                      void *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.construct_calls;
  if (module != kModuleBase || context_storage == nullptr ||
      definition != fixture.definition.data() ||
      actor_character_id != kActorId ||
      recipient_character_id != kRecipientId ||
      fixture.active_context != nullptr) {
    output = nullptr;
    return false;
  }
  std::memset(context_storage, 0, 0x338);
  std::memcpy(static_cast<std::byte *>(context_storage) + 0x00, &definition,
              sizeof(definition));
  std::memcpy(static_cast<std::byte *>(context_storage) + 0x2D8,
              &actor_character_id, sizeof(actor_character_id));
  std::memcpy(static_cast<std::byte *>(context_storage) + 0x2DC,
              &recipient_character_id, sizeof(recipient_character_id));
  std::memcpy(static_cast<std::byte *>(context_storage) + 0x2E8,
              &fixture.intermediary_id, sizeof(fixture.intermediary_id));
  fixture.active_context = context_storage;
  output = context_storage;
  return true;
}

bool RefreshContext(void *context, std::uintptr_t module,
                    void *interaction_context, bool refresh) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.refresh_calls;
  return module == kModuleBase && refresh &&
         interaction_context == fixture.active_context;
}

bool FinalizeContext(void *context, std::uintptr_t module,
                     void *interaction_context) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.finalize_calls;
  return module == kModuleBase &&
         interaction_context == fixture.active_context;
}

bool CanSend(void *context, std::uintptr_t module, void *interaction_context,
             bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.can_send_calls;
  if (module != kModuleBase || interaction_context != fixture.active_context) {
    return false;
  }
  output = fixture.can_send;
  return true;
}

bool EvaluateCosts(
    void *context, std::uintptr_t module, void *interaction_context,
    std::array<std::int64_t, game::kCharacterInteractionPreviewCostCountV1>
        &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.cost_calls;
  if (module != kModuleBase || interaction_context != fixture.active_context) {
    return false;
  }
  output = fixture.costs;
  if (fixture.drift_second_cost_sample && fixture.cost_calls == 2) ++output[0];
  return true;
}

bool EvaluateTrigger(void *context, std::uintptr_t module, void *trigger,
                     const void *event_target_scope, bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.trigger_calls;
  if (module != kModuleBase || trigger != &fixture.definition ||
      event_target_scope !=
          static_cast<std::byte *>(fixture.active_context) + 0x08) {
    return false;
  }
  output = fixture.trigger_result;
  return true;
}

bool IntermediaryRaw(void *context, std::uintptr_t module,
                     void *interaction_context, std::int64_t &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.intermediary_calls;
  if (module != kModuleBase || interaction_context != fixture.active_context) {
    return false;
  }
  output = fixture.intermediary_raw;
  return true;
}

bool RecipientRaw(void *context, std::uintptr_t module,
                  void *interaction_context, std::int64_t &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.recipient_calls;
  if (module != kModuleBase || interaction_context != fixture.active_context) {
    return false;
  }
  output = fixture.recipient_raw;
  return true;
}

bool OuterFinal(void *context, std::uintptr_t module,
                void *interaction_context, std::int32_t &status) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.outer_calls;
  if (module != kModuleBase || interaction_context != fixture.active_context) {
    return false;
  }
  status = fixture.outer_status;
  return true;
}

bool IsHumanPlayer(void *context, std::uintptr_t module,
                   std::int32_t character_id, bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.human_calls;
  if (module != kModuleBase || character_id != kRecipientId) return false;
  output = fixture.human_recipient;
  return true;
}

bool DestroyContext(void *context, std::uintptr_t module,
                    void *interaction_context) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.destroy_calls;
  const bool valid = module == kModuleBase &&
                     interaction_context == fixture.active_context;
  fixture.active_context = nullptr;
  return valid && !fixture.fail_destroy;
}

bool ReadMemory(void *context, const void *address, void *output,
                std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (address == reinterpret_cast<const void *>(
                     kModuleBase +
                     ck3::kCharacterInteractionPreviewCharacterStorageSlotRvaV1)) {
    if (size != sizeof(std::uintptr_t)) return false;
    const auto storage =
        reinterpret_cast<std::uintptr_t>(fixture.storage.data());
    std::memcpy(output, &storage, sizeof(storage));
    return true;
  }
  if (address == nullptr || output == nullptr || size == 0) return false;
  std::memcpy(output, address, size);
  return true;
}

ck3::CharacterInteractionPreviewSourceOperationsV1 Operations() {
  return {&GetDatabase,       &HashStableKey, &LookupDefinition,
          &ConstructContext,  &RefreshContext,
          &FinalizeContext,   &CanSend,       &EvaluateCosts,
          &EvaluateTrigger,   &IntermediaryRaw,
          &RecipientRaw,      &OuterFinal,    &IsHumanPlayer,
          &DestroyContext,    &ReadMemory};
}

ck3::CharacterInteractionPreviewSourceEnvironmentV1 Environment(
    Fixture &fixture) {
  RepairPointers(fixture);
  ck3::CharacterInteractionPreviewSourceEnvironmentV1 environment{};
  environment.adapter_enabled = true;
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      ck3::kCharacterInteractionPreviewExecutableSha256V1;
  environment.offline_fixture = true;
  environment.module_base = kModuleBase;
  environment.operation_context = &fixture;
  environment.operations = Operations();
  environment.upstream_context = &fixture;
  environment.capture_frame = &Capture;
  environment.is_main_thread = &MainThread;
  return environment;
}

ck3::CharacterInteractionPreviewRequestV1 Request() {
  ck3::CharacterInteractionPreviewRequestV1 request{};
  request.expected_snapshot_id = "diplomatic-frame-17";
  request.expected_public_revision = 41;
  request.expected_native_revision = 73;
  request.expected_date_raw = 9001;
  request.actor_character_id = kActorId;
  request.recipient_character_id = kRecipientId;
  request.interaction_key = "gift_interaction";
  return request;
}

std::string ReadFixture(const char *path) {
  std::ifstream stream(path, std::ios::binary);
  assert(stream.good());
  std::string result{std::istreambuf_iterator<char>(stream),
                     std::istreambuf_iterator<char>()};
  while (!result.empty() &&
         (result.back() == '\n' || result.back() == '\r')) {
    result.pop_back();
  }
  return result;
}

game::CharacterInteractionPreviewV1 ReadAvailable(
    Fixture &fixture, ck3::CharacterInteractionPreviewSourceStateV1 &state) {
  assert(ck3::BindCharacterInteractionPreviewSourceAdapterV1(
      Environment(fixture), state));
  game::CharacterInteractionPreviewV1 output{};
  assert(ck3::ReadCharacterInteractionPreviewFromSourceAdapterV1(
             state, Request(), output) ==
         game::ReadCharacterInteractionPreviewResultV1::available);
  assert(output.status == game::CharacterInteractionPreviewStatusV1::available);
  assert(output.readiness.same_frame_ready);
  assert(state.completed_context_count == 2 && !state.context_active &&
         state.active_owned_context == nullptr &&
         !state.terminal_cleanup_failure);
  assert(fixture.capture_calls == 2 && fixture.database_calls == 2 &&
         fixture.hash_calls == 2 && fixture.lookup_calls == 2 &&
         fixture.construct_calls == 2 && fixture.refresh_calls == 2 &&
         fixture.finalize_calls == 2 && fixture.can_send_calls == 2 &&
         fixture.cost_calls == 2 && fixture.human_calls == 2 &&
         fixture.destroy_calls == 2 && fixture.active_context == nullptr);
  return output;
}

void TestAvailableFixture(const char *fixture_path) {
  auto fixture = BaseFixture();
  ck3::CharacterInteractionPreviewSourceStateV1 state{};
  const auto output = ReadAvailable(fixture, state);
  assert(output.definition.canonical_key == "gift_interaction");
  assert(output.roles.actor_character_id == kActorId &&
         output.roles.recipient_character_id == kRecipientId);
  assert(output.can_send && output.costs.raw[0] == 2'500'000 &&
         output.costs.raw[3] == -100'000);
  assert(output.acceptance.kind ==
             game::CharacterInteractionAcceptanceKindV1::ai_final &&
         output.acceptance.recipient_raw == 12'500'000 &&
         output.acceptance.final_status_raw == 0 &&
         output.acceptance.would_accept_now);
  assert(fixture.intermediary_calls == 0 && fixture.recipient_calls == 2 &&
         fixture.outer_calls == 2 && fixture.trigger_calls == 0);
  const auto actual = ck3::SerializeCharacterInteractionPreviewV1(output);
  const auto expected = ReadFixture(fixture_path);
  if (actual != expected) {
    std::cerr << "source-adapter fixture mismatch\nactual: " << actual
              << "\nexpected: " << expected << '\n';
    std::abort();
  }
}

void TestAcceptanceBranchesAreNativeFinal() {
  auto rejected = BaseFixture();
  rejected.can_send = false;
  rejected.recipient_raw = -3'000'000;
  rejected.outer_status = 2;
  ck3::CharacterInteractionPreviewSourceStateV1 state{};
  auto output = ReadAvailable(rejected, state);
  assert(!output.can_send && output.acceptance.final_status_raw == 2 &&
         !output.acceptance.would_accept_now);
  assert(rejected.recipient_calls == 2 && rejected.outer_calls == 2);

  auto automatic = BaseFixture();
  automatic.trigger_result = true;
  Put(automatic.definition, 0x2580,
      static_cast<void *>(&automatic.definition));
  state = {};
  output = ReadAvailable(automatic, state);
  assert(output.acceptance.kind ==
             game::CharacterInteractionAcceptanceKindV1::auto_accept &&
         output.acceptance.auto_accept && output.acceptance.would_accept_now);
  assert(automatic.trigger_calls == 2 && automatic.recipient_calls == 0 &&
         automatic.outer_calls == 0);

  auto human = BaseFixture();
  human.human_recipient = true;
  state = {};
  output = ReadAvailable(human, state);
  assert(output.acceptance.kind ==
             game::CharacterInteractionAcceptanceKindV1::human_pending &&
         !output.acceptance.recipient_is_ai &&
         !output.acceptance.would_accept_now_present);
  assert(human.recipient_calls == 0 && human.outer_calls == 0);

  auto intermediary = BaseFixture();
  intermediary.intermediary_id = kIntermediaryId;
  state = {};
  output = ReadAvailable(intermediary, state);
  assert(output.acceptance.intermediary_present &&
         output.acceptance.intermediary_raw_present &&
         output.acceptance.intermediary_raw == 700'000);
  assert(intermediary.intermediary_calls == 2);
}

void TestGenerationAndSampleDriftStayRed() {
  auto generation_mismatch = BaseFixture();
  Put(generation_mismatch.recipient, 0x18, std::int32_t{3});
  ck3::CharacterInteractionPreviewSourceStateV1 state{};
  assert(ck3::BindCharacterInteractionPreviewSourceAdapterV1(
      Environment(generation_mismatch), state));
  game::CharacterInteractionPreviewV1 output{};
  assert(ck3::ReadCharacterInteractionPreviewFromSourceAdapterV1(
             state, Request(), output) ==
         game::ReadCharacterInteractionPreviewResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CharacterInteractionPreviewFailureV1::
             character_identity_mismatch);
  assert(generation_mismatch.construct_calls == 0 &&
         output.definition.canonical_key.empty());

  auto drift = BaseFixture();
  drift.drift_second_cost_sample = true;
  state = {};
  assert(ck3::BindCharacterInteractionPreviewSourceAdapterV1(
      Environment(drift), state));
  assert(ck3::ReadCharacterInteractionPreviewFromSourceAdapterV1(
             state, Request(), output) ==
         game::ReadCharacterInteractionPreviewResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CharacterInteractionPreviewFailureV1::native_sample_drift);
  assert(drift.destroy_calls == 2 && state.completed_context_count == 2);
}

void TestCleanupFailureIsTerminal() {
  auto fixture = BaseFixture();
  fixture.fail_destroy = true;
  ck3::CharacterInteractionPreviewSourceStateV1 state{};
  assert(ck3::BindCharacterInteractionPreviewSourceAdapterV1(
      Environment(fixture), state));
  game::CharacterInteractionPreviewV1 output{};
  assert(ck3::ReadCharacterInteractionPreviewFromSourceAdapterV1(
             state, Request(), output) ==
         game::ReadCharacterInteractionPreviewResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CharacterInteractionPreviewFailureV1::context_cleanup_failed);
  assert(state.terminal_cleanup_failure && !state.context_active &&
         state.active_owned_context == nullptr &&
         state.completed_context_count == 0);
  assert(ck3::ReadCharacterInteractionPreviewFromSourceAdapterV1(
             state, Request(), output) ==
         game::ReadCharacterInteractionPreviewResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CharacterInteractionPreviewFailureV1::
             native_bindings_unavailable);
  assert(fixture.destroy_calls == 1);
}

void TestBindingGateAndExactAddresses() {
  auto fixture = BaseFixture();
  ck3::CharacterInteractionPreviewSourceStateV1 state{};
  auto environment = Environment(fixture);
  environment.operations.outer_final = nullptr;
  assert(!ck3::BindCharacterInteractionPreviewSourceAdapterV1(environment,
                                                              state));
  assert(!state.attached);

  environment = Environment(fixture);
  environment.admitted_executable_sha256 = "WRONG";
  assert(!ck3::BindCharacterInteractionPreviewSourceAdapterV1(environment,
                                                              state));
  assert(!state.attached);

  environment = Environment(fixture);
  assert(ck3::BindCharacterInteractionPreviewSourceAdapterV1(environment,
                                                             state));
  assert(state.core_environment.database_getter ==
         kModuleBase +
             ck3::kCharacterInteractionPreviewDatabaseGetterRvaV1);
  assert(state.core_environment.construct_context ==
         kModuleBase +
             ck3::kCharacterInteractionPreviewConstructContextRvaV1);
  assert(state.core_environment.destroy_context ==
         kModuleBase +
             ck3::kCharacterInteractionPreviewDestroyContextRvaV1);
  assert(state.core_environment.offline_fixture);
}

} // namespace

int main(int argc, char **argv) {
  assert(argc == 2);
  TestAvailableFixture(argv[1]);
  TestAcceptanceBranchesAreNativeFinal();
  TestGenerationAndSampleDriftStayRed();
  TestCleanupFailureIsTerminal();
  TestBindingGateAndExactAddresses();
  std::cout << "character-interaction-preview-v1 source adapter passed\n";
  return 0;
}
