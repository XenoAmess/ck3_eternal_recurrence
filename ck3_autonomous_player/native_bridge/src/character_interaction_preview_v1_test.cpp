#include "xar_bridge/character_interaction_preview_v1.hpp"

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
  std::array<std::byte, 0x40> definition{};
  std::array<char, 32> definition_key{};
  std::array<std::byte, 0x40> storage{};
  std::array<std::byte, 8 * 0x10> slots{};
  std::array<std::byte, 0x200> actor{};
  std::array<std::byte, 0x200> recipient{};
  std::array<std::int64_t, game::kCharacterInteractionPreviewCostCountV1>
      costs{2'500'000, 0, 0, -100'000, 0, 0, 0, 0, 0, 0};
  game::CharacterInteractionPreviewAcceptanceV1 acceptance{};
  bool main_thread = true;
  bool can_send = true;
  bool fail_definition_lookup = false;
  bool fail_costs = false;
  bool fail_destroy = false;
  bool drift_second_sample = false;
  std::int32_t capture_calls = 0;
  std::int32_t hash_calls = 0;
  std::int32_t database_calls = 0;
  std::int32_t lookup_calls = 0;
  std::int32_t construct_calls = 0;
  std::int32_t refresh_calls = 0;
  std::int32_t finalize_calls = 0;
  std::int32_t can_send_calls = 0;
  std::int32_t cost_calls = 0;
  std::int32_t acceptance_calls = 0;
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
  Put(fixture.definition, 0x18,
      reinterpret_cast<std::uintptr_t>(fixture.definition_key.data()));
  Put(fixture.definition, 0x28, static_cast<std::size_t>(key.size()));
  Put(fixture.definition, 0x30, std::size_t{31});

  Put(fixture.storage, 0x20,
      reinterpret_cast<std::uintptr_t>(fixture.slots.data()));
  Put(fixture.storage, 0x2C, std::int32_t{8});
  Put(fixture.slots, 2 * 0x10 + 0x08,
      reinterpret_cast<std::uintptr_t>(fixture.actor.data()));
  Put(fixture.slots, 3 * 0x10 + 0x08,
      reinterpret_cast<std::uintptr_t>(fixture.recipient.data()));
  Put(fixture.actor, 0x18, kActorId);
  Put(fixture.actor, 0x1C8, std::uintptr_t{0});
  Put(fixture.recipient, 0x18, kRecipientId);
  Put(fixture.recipient, 0x1C8, std::uintptr_t{0});

  fixture.acceptance.kind =
      game::CharacterInteractionAcceptanceKindV1::ai_final;
  fixture.acceptance.recipient_is_ai = true;
  fixture.acceptance.recipient_raw_present = true;
  fixture.acceptance.recipient_raw = 12'500'000;
  fixture.acceptance.final_status_present = true;
  fixture.acceptance.final_status_raw = 0;
  fixture.acceptance.would_accept_now_present = true;
  fixture.acceptance.would_accept_now = true;
  return fixture;
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

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  if (address == 0 || output == nullptr || size == 0) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

bool StableHash(void *context, std::uintptr_t function, void *database,
                std::string_view key, std::int32_t &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.hash_calls;
  if (function !=
          kModuleBase + ck3::kCharacterInteractionPreviewStableKeyHashRvaV1 ||
      database != &fixture.storage || key != "gift_interaction") {
    return false;
  }
  output = static_cast<std::int32_t>(kGiftHash);
  return true;
}

bool Database(void *context, std::uintptr_t function, void *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.database_calls;
  if (function !=
      kModuleBase + ck3::kCharacterInteractionPreviewDatabaseGetterRvaV1) {
    return false;
  }
  output = &fixture.storage;
  return true;
}

bool Lookup(void *context, std::uintptr_t function, void *database,
            std::int32_t key_hash, void *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.lookup_calls;
  if (fixture.fail_definition_lookup ||
      function !=
          kModuleBase +
              ck3::kCharacterInteractionPreviewDefinitionLookupRvaV1 ||
      database != &fixture.storage ||
      static_cast<std::uint32_t>(key_hash) != kGiftHash) {
    output = nullptr;
    return false;
  }
  output = fixture.definition.data();
  return true;
}

bool Construct(void *context, std::uintptr_t function, void *context_storage,
               void *definition, std::int32_t actor_character_id,
               std::int32_t recipient_character_id, void *&output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.construct_calls;
  if (function !=
          kModuleBase +
              ck3::kCharacterInteractionPreviewConstructContextRvaV1 ||
      context_storage == nullptr || definition != fixture.definition.data() ||
      actor_character_id != kActorId ||
      recipient_character_id != kRecipientId ||
      fixture.active_context != nullptr) {
    output = nullptr;
    return false;
  }
  fixture.active_context = context_storage;
  output = context_storage;
  return true;
}

bool Refresh(void *context, std::uintptr_t function,
             void *interaction_context) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.refresh_calls;
  return function ==
             kModuleBase +
                 ck3::kCharacterInteractionPreviewRefreshContextRvaV1 &&
         interaction_context == fixture.active_context;
}

bool Finalize(void *context, std::uintptr_t function,
              void *interaction_context) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.finalize_calls;
  return function ==
             kModuleBase +
                 ck3::kCharacterInteractionPreviewFinalizeContextRvaV1 &&
         interaction_context == fixture.active_context;
}

bool CanSend(void *context, std::uintptr_t function, void *interaction_context,
             bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.can_send_calls;
  if (function !=
          kModuleBase + ck3::kCharacterInteractionPreviewCanSendRvaV1 ||
      interaction_context != fixture.active_context) {
    return false;
  }
  output = fixture.can_send;
  return true;
}

bool Costs(
    void *context, std::uintptr_t function, void *interaction_context,
    std::array<std::int64_t, game::kCharacterInteractionPreviewCostCountV1>
        &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.cost_calls;
  if (fixture.fail_costs ||
      function !=
          kModuleBase +
              ck3::kCharacterInteractionPreviewCostEvaluatorRvaV1 ||
      interaction_context != fixture.active_context) {
    return false;
  }
  output = fixture.costs;
  if (fixture.drift_second_sample && fixture.cost_calls == 2) ++output[0];
  return true;
}

bool Acceptance(
    void *context, std::uintptr_t auto_accept_function,
    std::uintptr_t intermediary_raw_function,
    std::uintptr_t recipient_raw_function, std::uintptr_t outer_final_function,
    void *interaction_context,
    game::CharacterInteractionPreviewAcceptanceV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.acceptance_calls;
  if (auto_accept_function !=
          kModuleBase +
              ck3::kCharacterInteractionPreviewAutoAcceptEvaluatorRvaV1 ||
      intermediary_raw_function !=
          kModuleBase +
              ck3::kCharacterInteractionPreviewIntermediaryRawRvaV1 ||
      recipient_raw_function !=
          kModuleBase +
              ck3::kCharacterInteractionPreviewRecipientRawRvaV1 ||
      outer_final_function !=
          kModuleBase +
              ck3::kCharacterInteractionPreviewOuterFinalRvaV1 ||
      interaction_context != fixture.active_context) {
    return false;
  }
  output = fixture.acceptance;
  return true;
}

bool Destroy(void *context, std::uintptr_t function,
             void *interaction_context) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.destroy_calls;
  const bool valid =
      function ==
          kModuleBase +
              ck3::kCharacterInteractionPreviewDestroyContextRvaV1 &&
      interaction_context == fixture.active_context;
  fixture.active_context = nullptr;
  return valid && !fixture.fail_destroy;
}

ck3::CharacterInteractionPreviewEnvironmentV1 Environment(Fixture &fixture) {
  Put(fixture.definition, 0x18,
      reinterpret_cast<std::uintptr_t>(fixture.definition_key.data()));
  Put(fixture.storage, 0x20,
      reinterpret_cast<std::uintptr_t>(fixture.slots.data()));
  Put(fixture.slots, 2 * 0x10 + 0x08,
      reinterpret_cast<std::uintptr_t>(fixture.actor.data()));
  Put(fixture.slots, 3 * 0x10 + 0x08,
      reinterpret_cast<std::uintptr_t>(fixture.recipient.data()));
  auto environment = ck3::BindCharacterInteractionPreviewEnvironmentV1(
      kModuleBase, true, ck3::kCharacterInteractionPreviewExecutableSha256V1);
  environment.offline_fixture = true;
  environment.character_storage_slot =
      reinterpret_cast<std::uintptr_t>(&fixture.storage) + 0x38;
  const auto storage = reinterpret_cast<std::uintptr_t>(fixture.storage.data());
  std::memcpy(reinterpret_cast<void *>(environment.character_storage_slot),
              &storage, sizeof(storage));
  return environment;
}

ck3::CharacterInteractionPreviewAccessV1 Access(Fixture &fixture) {
  ck3::CharacterInteractionPreviewAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &MainThread;
  access.read_memory = &ReadMemory;
  access.invoke_stable_hash = &StableHash;
  access.invoke_database_getter = &Database;
  access.invoke_definition_lookup = &Lookup;
  access.invoke_construct = &Construct;
  access.invoke_refresh = &Refresh;
  access.invoke_finalize = &Finalize;
  access.invoke_can_send = &CanSend;
  access.invoke_costs = &Costs;
  access.invoke_acceptance = &Acceptance;
  access.invoke_destroy = &Destroy;
  return access;
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
  if (!result.empty() && result.back() == '\n') result.pop_back();
  if (!result.empty() && result.back() == '\r') result.pop_back();
  return result;
}

game::CharacterInteractionPreviewV1 ReadAvailable(Fixture &fixture) {
  game::CharacterInteractionPreviewV1 output{};
  assert(ck3::ReadCharacterInteractionPreviewV1(
             Environment(fixture), Access(fixture), Request(), output) ==
         game::ReadCharacterInteractionPreviewResultV1::available);
  assert(output.status == game::CharacterInteractionPreviewStatusV1::available);
  assert(output.readiness.same_frame_ready);
  assert(fixture.capture_calls == 2);
  assert(fixture.hash_calls == 2 && fixture.database_calls == 2 &&
         fixture.lookup_calls == 2 && fixture.construct_calls == 2 &&
         fixture.refresh_calls == 2 && fixture.finalize_calls == 2 &&
         fixture.can_send_calls == 2 && fixture.cost_calls == 2 &&
         fixture.acceptance_calls == 2 && fixture.destroy_calls == 2);
  assert(fixture.active_context == nullptr);
  return output;
}

void TestAvailableFixture(const char *fixture_path) {
  auto fixture = BaseFixture();
  const auto output = ReadAvailable(fixture);
  assert(output.definition.canonical_key == "gift_interaction");
  assert(output.definition.deterministic_key_hash == kGiftHash);
  assert(output.definition.runtime_ordinal == 87);
  assert(output.roles.actor_character_id == kActorId);
  assert(output.roles.recipient_character_id == kRecipientId);
  assert(output.can_send);
  assert(output.costs.raw[0] == 2'500'000 &&
         output.costs.raw[3] == -100'000);
  assert(output.acceptance.kind ==
         game::CharacterInteractionAcceptanceKindV1::ai_final);
  const auto json = ck3::SerializeCharacterInteractionPreviewV1(output);
  const auto expected = ReadFixture(fixture_path);
  if (json != expected) {
    std::cerr << "fixture mismatch\nactual: " << json
              << "\nexpected: " << expected << '\n';
    std::abort();
  }
}

void TestFinalRejectionRemainsAvailable() {
  auto fixture = BaseFixture();
  fixture.can_send = false;
  fixture.acceptance.recipient_raw = -3'000'000;
  fixture.acceptance.final_status_raw = 2;
  fixture.acceptance.would_accept_now = false;
  const auto output = ReadAvailable(fixture);
  assert(!output.can_send);
  assert(output.acceptance.final_status_raw == 2);
  assert(!output.acceptance.would_accept_now);
}

void TestKnownNonAiAcceptanceBranches() {
  auto automatic = BaseFixture();
  automatic.acceptance = {};
  automatic.acceptance.kind =
      game::CharacterInteractionAcceptanceKindV1::auto_accept;
  automatic.acceptance.recipient_is_ai = true;
  automatic.acceptance.auto_accept = true;
  automatic.acceptance.would_accept_now_present = true;
  automatic.acceptance.would_accept_now = true;
  auto output = ReadAvailable(automatic);
  assert(output.acceptance.kind ==
         game::CharacterInteractionAcceptanceKindV1::auto_accept);

  auto human = BaseFixture();
  human.acceptance = {};
  human.acceptance.kind =
      game::CharacterInteractionAcceptanceKindV1::human_pending;
  output = ReadAvailable(human);
  assert(output.acceptance.kind ==
         game::CharacterInteractionAcceptanceKindV1::human_pending);
}

void TestDefinitionAndRecipientLookupFailuresAreAtomic() {
  auto missing_definition = BaseFixture();
  missing_definition.fail_definition_lookup = true;
  game::CharacterInteractionPreviewV1 output{};
  assert(ck3::ReadCharacterInteractionPreviewV1(
             Environment(missing_definition), Access(missing_definition),
             Request(), output) ==
         game::ReadCharacterInteractionPreviewResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CharacterInteractionPreviewFailureV1::definition_lookup_failed);
  assert(output.definition.canonical_key.empty() &&
         !output.readiness.definition_ready);
  assert(missing_definition.construct_calls == 0);

  auto generation_mismatch = BaseFixture();
  Put(generation_mismatch.recipient, 0x18, std::int32_t{3});
  assert(ck3::ReadCharacterInteractionPreviewV1(
             Environment(generation_mismatch), Access(generation_mismatch),
             Request(), output) ==
         game::ReadCharacterInteractionPreviewResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CharacterInteractionPreviewFailureV1::
             character_identity_mismatch);
  assert(output.definition.canonical_key.empty() &&
         !output.readiness.recipient_ready);
  assert(generation_mismatch.construct_calls == 0);
}

void TestDriftAndCleanupFailuresStayRed() {
  auto sample_drift = BaseFixture();
  sample_drift.drift_second_sample = true;
  game::CharacterInteractionPreviewV1 output{};
  assert(ck3::ReadCharacterInteractionPreviewV1(
             Environment(sample_drift), Access(sample_drift), Request(),
             output) ==
         game::ReadCharacterInteractionPreviewResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CharacterInteractionPreviewFailureV1::native_sample_drift);

  auto frame_drift = BaseFixture();
  ++frame_drift.after.proof_epoch;
  assert(ck3::ReadCharacterInteractionPreviewV1(
             Environment(frame_drift), Access(frame_drift), Request(),
             output) ==
         game::ReadCharacterInteractionPreviewResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CharacterInteractionPreviewFailureV1::revision_drift);

  auto cleanup_failure = BaseFixture();
  cleanup_failure.fail_destroy = true;
  assert(ck3::ReadCharacterInteractionPreviewV1(
             Environment(cleanup_failure), Access(cleanup_failure), Request(),
             output) ==
         game::ReadCharacterInteractionPreviewResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CharacterInteractionPreviewFailureV1::context_cleanup_failed);
  assert(output.definition.canonical_key.empty());
}

void TestInvalidAcceptanceAndAllowlistStayRed() {
  auto invalid_acceptance = BaseFixture();
  invalid_acceptance.acceptance.final_status_raw = 2;
  invalid_acceptance.acceptance.would_accept_now = true;
  game::CharacterInteractionPreviewV1 output{};
  assert(ck3::ReadCharacterInteractionPreviewV1(
             Environment(invalid_acceptance), Access(invalid_acceptance),
             Request(), output) ==
         game::ReadCharacterInteractionPreviewResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CharacterInteractionPreviewFailureV1::
             acceptance_invariant_failed);

  auto not_allowlisted = BaseFixture();
  auto request = Request();
  request.interaction_key = "imprison_interaction";
  assert(ck3::ReadCharacterInteractionPreviewV1(
             Environment(not_allowlisted), Access(not_allowlisted), request,
             output) ==
         game::ReadCharacterInteractionPreviewResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CharacterInteractionPreviewFailureV1::
             interaction_not_allowlisted);
  assert(not_allowlisted.hash_calls == 0);
}

void TestBoundEnvironment() {
  const auto environment = ck3::BindCharacterInteractionPreviewEnvironmentV1(
      kModuleBase, true, ck3::kCharacterInteractionPreviewExecutableSha256V1);
  assert(environment.character_storage_slot ==
         kModuleBase +
             ck3::kCharacterInteractionPreviewCharacterStorageSlotRvaV1);
  assert(environment.definition_lookup ==
         kModuleBase +
             ck3::kCharacterInteractionPreviewDefinitionLookupRvaV1);
  assert(environment.can_send ==
         kModuleBase + ck3::kCharacterInteractionPreviewCanSendRvaV1);
  assert(environment.cost_evaluator ==
         kModuleBase +
             ck3::kCharacterInteractionPreviewCostEvaluatorRvaV1);
  assert(environment.outer_final ==
         kModuleBase + ck3::kCharacterInteractionPreviewOuterFinalRvaV1);
}

} // namespace

int main(int argc, char **argv) {
  assert(argc == 2);
  TestAvailableFixture(argv[1]);
  TestFinalRejectionRemainsAvailable();
  TestKnownNonAiAcceptanceBranches();
  TestDefinitionAndRecipientLookupFailuresAreAtomic();
  TestDriftAndCleanupFailuresStayRed();
  TestInvalidAcceptanceAndAllowlistStayRed();
  TestBoundEnvironment();
  std::cout << "character-interaction-preview-v1 fixture passed\n";
  return 0;
}
