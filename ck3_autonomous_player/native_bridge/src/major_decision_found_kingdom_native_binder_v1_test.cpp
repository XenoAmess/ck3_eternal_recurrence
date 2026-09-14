#include "xar_bridge/major_decision_found_kingdom_native_binder_v1.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <map>
#include <string_view>
#include <vector>

namespace bridge = xar::bridge;

namespace {

constexpr std::uintptr_t kModule = 0x10000000;
constexpr std::uintptr_t kDatabase = 0x71000000;
constexpr std::uintptr_t kDefinition = 0x72000000;
constexpr std::uintptr_t kPlayer = 0x73000000;
constexpr std::int32_t kPlayerId = 0x0100002A;
constexpr std::uint32_t kDecisionHash = 0xD15C1D01;

struct Fixture {
  std::map<std::uintptr_t, std::vector<std::byte>> memory{};
  std::array<bool, 3> eligibility{true, true, true};
  bridge::MajorDecisionFoundKingdomSourceCostV1 cost{
      30'000'000, 0, 50'000'000, 20'000'000};
  bool affordable = true;
  bool can_take = true;
  int frames = 0;
  int player_resolves = 0;
  int definition_lookups = 0;
  int trigger_evaluations = 0;
  int cost_evaluations = 0;
  int affordability_evaluations = 0;
  int can_take_evaluations = 0;
};

void StoreBytes(Fixture &fixture, std::uintptr_t address,
                const void *value, std::size_t size) {
  const auto *begin = static_cast<const std::byte *>(value);
  fixture.memory[address] = {begin, begin + size};
}

template <typename T>
void Store(Fixture &fixture, std::uintptr_t address, const T &value) {
  StoreBytes(fixture, address, &value, sizeof(value));
}

void PopulateExactImage(Fixture &fixture) {
  for (const auto &signature :
       bridge::kMajorDecisionFoundKingdomNativeSignaturesV1) {
    StoreBytes(fixture, kModule + signature.rva, signature.bytes.data(),
               signature.size);
  }
  for (const auto &slot : bridge::kMajorDecisionFoundKingdomNativeSlotsV1) {
    const auto function = kModule + slot.function_rva;
    Store(fixture, kModule + slot.slot_rva, function);
  }
  Store(fixture,
        kModule +
            bridge::kMajorDecisionFoundKingdomDecisionDatabaseSlotRvaV1,
        kDatabase);
  const auto database_vtable =
      kModule +
      bridge::kMajorDecisionFoundKingdomDecisionDatabaseVtableRvaV1;
  const auto definition_vtable =
      kModule +
      bridge::kMajorDecisionFoundKingdomDecisionDefinitionVtableRvaV1;
  Store(fixture, kDatabase, database_vtable);
  Store(fixture, kDefinition, definition_vtable);
  Store(fixture, kPlayer + 0x18, kPlayerId);
}

bool ReadMemory(void *context, const void *address, void *output,
                std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  const auto requested = reinterpret_cast<std::uintptr_t>(address);
  for (const auto &[start, bytes] : fixture.memory) {
    if (requested < start) continue;
    const auto offset = requested - start;
    if (offset <= bytes.size() && size <= bytes.size() - offset) {
      std::memcpy(output, bytes.data() + offset, size);
      return true;
    }
  }
  return false;
}

std::uintptr_t ResolvePlayer(void *context, std::uintptr_t module,
                             std::int32_t character_id) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.player_resolves;
  return module == kModule && character_id == kPlayerId ? kPlayer : 0;
}

bool HashName(void *, std::uintptr_t module, std::string_view name,
              std::uint32_t &output) noexcept {
  output = 0;
  if (module != kModule ||
      name != bridge::kMajorDecisionFoundKingdomDecisionIdV1) {
    return false;
  }
  output = kDecisionHash;
  return true;
}

std::uintptr_t LookupDefinition(void *context, std::uintptr_t module,
                                std::uintptr_t database,
                                std::uint32_t hash) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.definition_lookups;
  return module == kModule && database == kDatabase && hash == kDecisionHash
             ? kDefinition
             : 0;
}

bool EvaluateTrigger(void *context, std::uintptr_t module,
                     std::uintptr_t definition, std::size_t offset,
                     std::int32_t character_id, bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.trigger_evaluations;
  if (module != kModule || definition != kDefinition ||
      character_id != kPlayerId) {
    return false;
  }
  if (offset == bridge::kMajorDecisionFoundKingdomIsShownOffsetV1) {
    output = fixture.eligibility[0];
  } else if (offset ==
             bridge::kMajorDecisionFoundKingdomIsValidOffsetV1) {
    output = fixture.eligibility[1];
  } else if (
      offset == bridge::
                    kMajorDecisionFoundKingdomIsValidShowingFailuresOnlyOffsetV1) {
    output = fixture.eligibility[2];
  } else {
    return false;
  }
  return true;
}

bool EvaluateCost(
    void *context, std::uintptr_t module, std::uintptr_t definition,
    std::int32_t character_id,
    bridge::MajorDecisionFoundKingdomSourceCostV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.cost_evaluations;
  if (module != kModule || definition != kDefinition ||
      character_id != kPlayerId) {
    return false;
  }
  output = fixture.cost;
  return true;
}

bool EvaluateAffordability(void *context, std::uintptr_t module,
                           std::uintptr_t definition,
                           std::uintptr_t player,
                           std::int32_t character_id,
                           bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.affordability_evaluations;
  if (module != kModule || definition != kDefinition || player != kPlayer ||
      character_id != kPlayerId) {
    return false;
  }
  output = fixture.affordable;
  return true;
}

bool EvaluateCanTake(void *context, std::uintptr_t module,
                     std::uintptr_t definition, std::uintptr_t player,
                     std::int32_t character_id, bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.can_take_evaluations;
  if (module != kModule || definition != kDefinition || player != kPlayer ||
      character_id != kPlayerId) {
    return false;
  }
  output = fixture.can_take;
  return true;
}

bool CaptureFrame(void *context,
                  bridge::MajorDecisionFoundKingdomFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.frames;
  output = {};
  output.snapshot_revision = 81;
  output.native_revision = 34;
  output.proof_epoch = 21;
  output.date_raw = 1092;
  output.played_character_id = kPlayerId;
  output.application_main_thread = true;
  output.paused = true;
  output.map_ready = true;
  output.played_character_alive = true;
  output.played_character_identity_round_trip = true;
  return true;
}

bridge::MajorDecisionFoundKingdomNativeOperationsV1 Operations() {
  return {&ReadMemory,          &ResolvePlayer, &HashName,
          &LookupDefinition,   &EvaluateTrigger,
          &EvaluateCost,       &EvaluateAffordability,
          &EvaluateCanTake};
}

bridge::MajorDecisionFoundKingdomNativeEnvironmentV1 Environment(
    Fixture &fixture) {
  bridge::MajorDecisionFoundKingdomNativeEnvironmentV1 environment{};
  environment.binding_enabled = true;
  environment.exact_build_admitted = true;
  environment.admitted_game_version =
      bridge::kMajorDecisionFoundKingdomNativeBinderGameVersionV1;
  environment.admitted_executable_sha256 =
      bridge::kMajorDecisionFoundKingdomExecutableSha256V1;
  environment.offline_fixture = true;
  environment.module_base = kModule;
  environment.operation_context = &fixture;
  environment.operations = Operations();
  return environment;
}

bridge::MajorDecisionFoundKingdomSourceAccessV1 Access(Fixture &fixture) {
  bridge::MajorDecisionFoundKingdomSourceAccessV1 access{};
  access.current_thread_id = 7;
  access.application_main_thread_id = 7;
  access.context = &fixture;
  access.capture_frame = &CaptureFrame;
  return access;
}

void TestFullSourceTransaction() {
  Fixture fixture{};
  PopulateExactImage(fixture);
  auto environment = Environment(fixture);
  auto access = Access(fixture);
  bridge::MajorDecisionFoundKingdomNativeBindingStateV1 state{};
  assert(bridge::BindMajorDecisionFoundKingdomNativeV1(environment, state,
                                                       access));
  assert(state.attached);
  assert(access.context == &state);
  assert(access.exact_build_admitted);
  assert(access.admitted_executable_sha256 ==
         bridge::kMajorDecisionFoundKingdomExecutableSha256V1);

  bridge::MajorDecisionFoundKingdomSourceResultV1 result{};
  assert(bridge::ObserveMajorDecisionFoundKingdomSourceV1(access, result));
  assert(result.failure ==
         bridge::MajorDecisionFoundKingdomSourceAdapterFailureV1::none);
  assert(result.snapshot.status ==
         bridge::MajorDecisionFoundKingdomStatusV1::available);
  assert(result.snapshot.is_shown.value);
  assert(result.snapshot.is_valid.value);
  assert(result.snapshot.is_valid_showing_failures_only.value);
  assert(result.snapshot.evaluated_cost.gold_q100000 == 30'000'000);
  assert(result.snapshot.evaluated_cost.treasury_q100000 == 0);
  assert(result.snapshot.evaluated_cost.prestige_q100000 == 50'000'000);
  assert(result.snapshot.evaluated_cost.piety_q100000 == 20'000'000);
  assert(result.snapshot.is_affordable.value);
  assert(result.snapshot.can_take.value);
  assert(result.snapshot.readiness.semantic_observation_ready);
  assert(!result.snapshot.readiness.effect_preview_ready);
  assert(!result.snapshot.readiness.action_ready);
  assert(!result.snapshot.effect_preview.executable);
  assert(fixture.frames == 2);
  assert(fixture.player_resolves == 2);
  assert(fixture.definition_lookups == 2);
  assert(fixture.trigger_evaluations == 6);
  assert(fixture.cost_evaluations == 2);
  assert(fixture.affordability_evaluations == 2);
  assert(fixture.can_take_evaluations == 2);

  // A binding owns one source-access surface and cannot be stacked twice.
  assert(!bridge::BindMajorDecisionFoundKingdomNativeV1(environment, state,
                                                        access));
}

void TestFalseIsObserved() {
  Fixture fixture{};
  PopulateExactImage(fixture);
  fixture.eligibility = {true, false, true};
  fixture.affordable = false;
  fixture.can_take = false;
  auto environment = Environment(fixture);
  auto access = Access(fixture);
  bridge::MajorDecisionFoundKingdomNativeBindingStateV1 state{};
  assert(bridge::BindMajorDecisionFoundKingdomNativeV1(environment, state,
                                                       access));
  bridge::MajorDecisionFoundKingdomSourceResultV1 result{};
  assert(bridge::ObserveMajorDecisionFoundKingdomSourceV1(access, result));
  assert(!result.snapshot.is_valid.value);
  assert(!result.snapshot.is_affordable.value);
  assert(!result.snapshot.can_take.value);
  assert(result.snapshot.readiness.semantic_observation_ready);
}

void TestExactImageGates() {
  Fixture fixture{};
  PopulateExactImage(fixture);

  {
    auto environment = Environment(fixture);
    environment.admitted_executable_sha256 = "wrong";
    auto access = Access(fixture);
    bridge::MajorDecisionFoundKingdomNativeBindingStateV1 state{};
    assert(!bridge::BindMajorDecisionFoundKingdomNativeV1(environment, state,
                                                          access));
    assert(access.context == &fixture);
    assert(access.resolve_player == nullptr);
  }

  {
    auto corrupted = fixture;
    const auto rva =
        bridge::kMajorDecisionFoundKingdomNativeSignaturesV1.front().rva;
    corrupted.memory[kModule + rva][0] ^= std::byte{0x01};
    auto environment = Environment(corrupted);
    auto access = Access(corrupted);
    bridge::MajorDecisionFoundKingdomNativeBindingStateV1 state{};
    assert(!bridge::BindMajorDecisionFoundKingdomNativeV1(environment, state,
                                                          access));
    assert(!state.attached);
  }

  {
    auto corrupted = fixture;
    const auto slot =
        bridge::kMajorDecisionFoundKingdomNativeSlotsV1.front().slot_rva;
    std::uintptr_t wrong = 1;
    Store(corrupted, kModule + slot, wrong);
    auto environment = Environment(corrupted);
    auto access = Access(corrupted);
    bridge::MajorDecisionFoundKingdomNativeBindingStateV1 state{};
    assert(!bridge::BindMajorDecisionFoundKingdomNativeV1(environment, state,
                                                          access));
  }
}

void TestDefinitionVtableGate() {
  Fixture fixture{};
  PopulateExactImage(fixture);
  const std::uintptr_t wrong_vtable = kModule + 0x1234;
  Store(fixture, kDefinition, wrong_vtable);
  auto environment = Environment(fixture);
  auto access = Access(fixture);
  bridge::MajorDecisionFoundKingdomNativeBindingStateV1 state{};
  assert(bridge::BindMajorDecisionFoundKingdomNativeV1(environment, state,
                                                       access));
  bridge::MajorDecisionFoundKingdomSourceResultV1 result{};
  assert(!bridge::ObserveMajorDecisionFoundKingdomSourceV1(access, result));
  assert(result.failure == bridge::
                               MajorDecisionFoundKingdomSourceAdapterFailureV1::
                                   decision_definition_missing);
}

} // namespace

int main() {
  TestFullSourceTransaction();
  TestFalseIsObserved();
  TestExactImageGates();
  TestDefinitionVtableGate();
  return 0;
}
