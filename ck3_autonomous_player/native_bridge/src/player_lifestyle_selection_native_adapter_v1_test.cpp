#include "xar_bridge/player_lifestyle_selection_native_adapter_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <string_view>

namespace {

namespace ck3 = xar::ck3_11906;
namespace game = xar::game;

using Dispatch = ck3::PlayerLifestyleSelectionNativeDispatchResultV1;
using Kind = game::PlayerLifestyleSelectionKindV1;
using StableKey = game::PlayerLifestyleWindowStableKeyV1;

constexpr std::uintptr_t kModule = 0x0000000140000000ULL;
constexpr std::uint32_t kPlayer = 0x81000002U;

template <std::size_t Size>
struct Blob {
  std::array<std::uint8_t, Size> bytes{};
  std::uintptr_t address() noexcept {
    return reinterpret_cast<std::uintptr_t>(bytes.data());
  }
};

template <typename Value, std::size_t Size>
void Put(Blob<Size> &blob, std::size_t offset, Value value) {
  assert(offset + sizeof(value) <= Size);
  std::memcpy(blob.bytes.data() + offset, &value, sizeof(value));
}

template <typename Value, std::size_t Size>
void Put(std::array<std::uint8_t, Size> &bytes, std::size_t offset,
         Value value) {
  assert(offset + sizeof(value) <= Size);
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

template <std::size_t ObjectBytes>
struct Definition {
  Blob<ObjectBytes> object{};
  std::array<char, game::kPlayerLifestyleWindowStableKeyCapacityV1>
      external_key{};
};

template <std::size_t ObjectBytes>
void SetKey(Definition<ObjectBytes> &definition, std::string_view key) {
  assert(!key.empty() && key.size() < definition.external_key.size());
  const auto offset = ck3::kLifestyleWindowStableKeyOffsetV1;
  Put(definition.object, offset + 0x10,
      static_cast<std::uint64_t>(key.size()));
  if (key.size() <= 15) {
    std::memcpy(definition.object.bytes.data() + offset, key.data(),
                key.size());
    Put(definition.object, offset + 0x18, std::uint64_t{15});
  } else {
    std::copy(key.begin(), key.end(), definition.external_key.begin());
    Put(definition.object, offset,
        reinterpret_cast<std::uintptr_t>(definition.external_key.data()));
    Put(definition.object, offset + 0x18,
        static_cast<std::uint64_t>(definition.external_key.size() - 1));
  }
}

struct RawSpan {
  std::uintptr_t data = 0;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};

static_assert(sizeof(RawSpan) == 0x10);

struct Fixture {
  Blob<0x20> root{};
  Blob<0x20> idler_base{};
  Blob<0x100> idler_gfx{};
  Blob<0x1C0> handler{};
  Blob<0x170> window{};
  Blob<0x40> character_storage{};
  std::array<std::uint8_t, 8 * ck3::kLifestyleWindowStorageSlotStrideV1>
      character_slots{};
  Blob<0x40> character{};
  Blob<0x40> fallback_character{};
  Definition<0x180> lifestyle{};
  Definition<0x900> focus{};
  Definition<0x490> perk{};
  std::array<std::uintptr_t, 1> lifestyle_rows{};
  std::array<std::uintptr_t, 1> focus_rows{};
  std::array<std::uintptr_t, 1> perk_rows{};
  Blob<0x80> perk_database{};
  ck3::PlayerLifestyleWindowSourceAdapterStateV1 source_state{};

  bool main_thread = true;
  bool paused = true;
  bool focus_gate = true;
  bool perk_gate = true;
  bool focus_validator = true;
  bool perk_validator = true;
  bool submit_result = true;
  std::uint32_t current_player = kPlayer;
  std::uint32_t rtti_calls = 0;
  std::uint32_t focus_gate_calls = 0;
  std::uint32_t perk_gate_calls = 0;
  std::uint32_t ignore_cost_gate_calls = 0;
  std::uint32_t focus_validator_calls = 0;
  std::uint32_t perk_validator_calls = 0;
  std::uint32_t submit_calls = 0;
  std::uint32_t submitted_flags = 0;
  std::array<std::uint8_t,
             ck3::kPlayerLifestyleSelectionFocusCommandBytesV1>
      submitted_command{};
};

Fixture *g_fixture = nullptr;

StableKey Key(std::string_view value) {
  StableKey output{};
  assert(ck3::AssignPlayerLifestyleWindowStableKeyV1(value, output));
  return output;
}

template <std::size_t Size>
void Fixed(std::array<char, Size> &output, std::string_view value) {
  assert(value.size() < Size);
  output.fill('\0');
  std::copy(value.begin(), value.end(), output.begin());
}

template <std::size_t Size>
std::uintptr_t LoadPointer(const std::array<std::uint8_t, Size> &bytes,
                           std::size_t offset) {
  std::uintptr_t output = 0;
  assert(offset + sizeof(output) <= Size);
  std::memcpy(&output, bytes.data() + offset, sizeof(output));
  return output;
}

template <std::size_t Size>
std::uint32_t LoadU32(const std::array<std::uint8_t, Size> &bytes,
                      std::size_t offset) {
  std::uint32_t output = 0;
  assert(offset + sizeof(output) <= Size);
  std::memcpy(&output, bytes.data() + offset, sizeof(output));
  return output;
}

std::unique_ptr<Fixture> Base() {
  auto fixture = std::make_unique<Fixture>();
  SetKey(fixture->lifestyle, "stewardship_lifestyle");
  SetKey(fixture->focus, "stewardship_wealth_focus");
  SetKey(fixture->perk, "tax_man_perk");
  Put(fixture->focus.object, ck3::kLifestyleWindowFocusLifestyleOffsetV1,
      fixture->lifestyle.object.address());
  Put(fixture->perk.object, ck3::kLifestyleWindowPerkLifestyleOffsetV1,
      fixture->lifestyle.object.address());
  fixture->lifestyle_rows = {fixture->lifestyle.object.address()};
  fixture->focus_rows = {fixture->focus.object.address()};
  fixture->perk_rows = {fixture->perk.object.address()};

  Put(fixture->root, ck3::kLifestyleWindowRootIdlerOffsetV1,
      fixture->idler_base.address());
  Put(fixture->idler_gfx, ck3::kLifestyleWindowIdlerHandlerOffsetV1,
      fixture->handler.address());
  Put(fixture->handler, 0,
      kModule + ck3::kLifestyleWindowHandlerVtableRvaV1);
  Put(fixture->handler, ck3::kLifestyleWindowHandlerOwnerSlotOffsetV1,
      fixture->window.address());
  Put(fixture->window, 0,
      kModule + ck3::kLifestyleWindowPrimaryVtableRvaV1);
  Put(fixture->window, ck3::kLifestyleWindowSecondaryVtableOffsetV1,
      kModule + ck3::kLifestyleWindowSecondaryVtableRvaV1);
  Put(fixture->window, ck3::kLifestyleWindowOwnerRoundTripOffsetV1,
      fixture->handler.address());
  Put(fixture->window, ck3::kLifestyleWindowBoundCharacterIdOffsetV1,
      kPlayer);
  Put(fixture->window, ck3::kLifestyleWindowLifestylesSpanOffsetV1,
      RawSpan{reinterpret_cast<std::uintptr_t>(fixture->lifestyle_rows.data()),
              1, 1});
  Put(fixture->window, ck3::kLifestyleWindowPerkTreeSpanOffsetV1,
      RawSpan{});
  Put(fixture->window, ck3::kLifestyleWindowFocusSpanOffsetV1,
      RawSpan{reinterpret_cast<std::uintptr_t>(fixture->focus_rows.data()),
              1, 1});
  Put(fixture->perk_database, ck3::kLifestyleWindowDatabaseSpanOffsetV1,
      RawSpan{reinterpret_cast<std::uintptr_t>(fixture->perk_rows.data()),
              1, 1});

  Put(fixture->character_storage,
      ck3::kLifestyleWindowStorageSlotsOffsetV1,
      reinterpret_cast<std::uintptr_t>(fixture->character_slots.data()));
  Put(fixture->character_storage,
      ck3::kLifestyleWindowStorageCapacityOffsetV1, std::int32_t{8});
  const auto slot = static_cast<std::size_t>(kPlayer & 0x00FFFFFFU) *
          ck3::kLifestyleWindowStorageSlotStrideV1 +
      ck3::kLifestyleWindowStorageObjectOffsetV1;
  Put(fixture->character_slots, slot, fixture->character.address());
  Put(fixture->character, ck3::kLifestyleWindowCharacterIdentityOffsetV1,
      kPlayer);
  return fixture;
}

bool ReadMemory(void *context, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  std::uintptr_t pointer = 0;
  if (address == kModule + ck3::kLifestyleWindowGlobalRootPointerRvaV1) {
    pointer = fixture.root.address();
  } else if (address ==
             kModule + ck3::kLifestyleWindowPlayedCharacterIdGlobalRvaV1) {
    if (output == nullptr || size != sizeof(fixture.current_player)) {
      return false;
    }
    std::memcpy(output, &fixture.current_player,
                sizeof(fixture.current_player));
    return true;
  } else if (address ==
             kModule + ck3::kLifestyleWindowCharacterStorageSlotRvaV1) {
    pointer = fixture.character_storage.address();
  } else if (address ==
             kModule + ck3::kLifestyleWindowCharacterFallbackSlotRvaV1) {
    pointer = fixture.fallback_character.address();
  } else if (address ==
             kModule +
                 ck3::kLifestyleWindowCanSelectFocusEvaluatorSlotRvaV1) {
    pointer = kModule +
        ck3::kLifestyleWindowCanSelectFocusEvaluatorTargetRvaV1;
  } else if (address ==
             kModule +
                 ck3::kLifestyleWindowCanSelectPerkEvaluatorSlotRvaV1) {
    pointer = kModule +
        ck3::kLifestyleWindowCanSelectPerkEvaluatorTargetRvaV1;
  } else {
    if (address == 0 || output == nullptr || size == 0) return false;
    std::memcpy(output, reinterpret_cast<const void *>(address), size);
    return true;
  }
  if (output == nullptr || size != sizeof(pointer)) return false;
  std::memcpy(output, &pointer, sizeof(pointer));
  return true;
}

void *FakeRtti(void *source, std::int32_t vf_delta, void *source_type,
               void *target_type, std::int32_t is_reference) {
  assert(g_fixture != nullptr);
  ++g_fixture->rtti_calls;
  if (source != reinterpret_cast<void *>(g_fixture->idler_base.address()) ||
      vf_delta != 0 || is_reference != 0 ||
      source_type != reinterpret_cast<void *>(
                         kModule +
                         ck3::kLifestyleWindowIdlerTypeDescriptorRvaV1) ||
      target_type != reinterpret_cast<void *>(
                         kModule +
                         ck3::kLifestyleWindowIdlerGfxTypeDescriptorRvaV1)) {
    return nullptr;
  }
  return reinterpret_cast<void *>(g_fixture->idler_gfx.address());
}

void *FakePerkDatabase() {
  assert(g_fixture != nullptr);
  return reinterpret_cast<void *>(g_fixture->perk_database.address());
}

bool FakeFocusGate(void *window, void *definition) {
  assert(g_fixture != nullptr);
  ++g_fixture->focus_gate_calls;
  return g_fixture->focus_gate &&
      window == reinterpret_cast<void *>(g_fixture->window.address()) &&
      definition ==
          reinterpret_cast<void *>(g_fixture->focus.object.address());
}

bool FakePerkGate(void *window, void *definition) {
  assert(g_fixture != nullptr);
  ++g_fixture->perk_gate_calls;
  return g_fixture->perk_gate &&
      window == reinterpret_cast<void *>(g_fixture->window.address()) &&
      definition ==
          reinterpret_cast<void *>(g_fixture->perk.object.address());
}

bool FakeIgnoreCostGate(void *window, void *definition) {
  assert(g_fixture != nullptr);
  ++g_fixture->ignore_cost_gate_calls;
  return window == reinterpret_cast<void *>(g_fixture->window.address()) &&
      definition ==
          reinterpret_cast<void *>(g_fixture->perk.object.address());
}

bool IsMain(void *context) noexcept {
  return static_cast<Fixture *>(context)->main_thread;
}

bool IsPaused(void *context) noexcept {
  return static_cast<Fixture *>(context)->paused;
}

bool FakeFocusValidator(void *command, void *validation_context) {
  assert(g_fixture != nullptr && command != nullptr);
  assert(validation_context == nullptr);
  ++g_fixture->focus_validator_calls;
  const auto *bytes = static_cast<const std::uint8_t *>(command);
  std::array<std::uint8_t,
             ck3::kPlayerLifestyleSelectionFocusCommandBytesV1>
      copy{};
  std::memcpy(copy.data(), bytes, copy.size());
  assert(LoadPointer(copy, 0x00) ==
         kModule + ck3::kPlayerLifestyleSelectionFocusPrimaryVtableRvaV1);
  assert(LoadPointer(copy, 0x18) ==
         kModule + ck3::kPlayerLifestyleSelectionFocusSecondaryVtableRvaV1);
  assert(LoadU32(copy, 0x20) == kPlayer);
  assert(LoadPointer(copy, 0x28) == g_fixture->focus.object.address());
  assert(LoadU32(copy, 0x30) == kPlayer);
  return g_fixture->focus_validator;
}

bool FakePerkValidator(void *command, void *validation_context) {
  assert(g_fixture != nullptr && command != nullptr);
  assert(validation_context == nullptr);
  ++g_fixture->perk_validator_calls;
  const auto *bytes = static_cast<const std::uint8_t *>(command);
  std::array<std::uint8_t,
             ck3::kPlayerLifestyleSelectionPerkCommandBytesV1>
      copy{};
  std::memcpy(copy.data(), bytes, copy.size());
  assert(LoadPointer(copy, 0x00) ==
         kModule + ck3::kPlayerLifestyleSelectionPerkPrimaryVtableRvaV1);
  assert(LoadPointer(copy, 0x18) ==
         kModule + ck3::kPlayerLifestyleSelectionPerkSecondaryVtableRvaV1);
  assert(LoadU32(copy, 0x20) == kPlayer);
  assert(LoadPointer(copy, 0x28) == g_fixture->perk.object.address());
  return g_fixture->perk_validator;
}

bool FakeSubmit(void *manager, void *command, std::uint32_t flags) {
  assert(g_fixture != nullptr && command != nullptr);
  assert(manager == g_fixture);
  ++g_fixture->submit_calls;
  g_fixture->submitted_flags = flags;
  const auto primary = *static_cast<const std::uintptr_t *>(command);
  const std::size_t bytes =
      primary ==
              kModule +
                  ck3::kPlayerLifestyleSelectionFocusPrimaryVtableRvaV1
          ? ck3::kPlayerLifestyleSelectionFocusCommandBytesV1
          : ck3::kPlayerLifestyleSelectionPerkCommandBytesV1;
  std::memcpy(g_fixture->submitted_command.data(), command, bytes);
  return g_fixture->submit_result;
}

ck3::PlayerLifestyleWindowSourceAdapterEnvironmentV1 SourceEnvironment() {
  ck3::PlayerLifestyleWindowSourceAdapterEnvironmentV1 output{};
  output.exact_build_admitted = true;
  output.admitted_executable_sha256 =
      ck3::kPlayerLifestyleWindowCandidatesExecutableSha256V1;
  output.module_base = kModule;
  output.offline_fixture = true;
  output.rtti_dynamic_cast = &FakeRtti;
  output.character_perk_database = &FakePerkDatabase;
  output.can_select_focus = &FakeFocusGate;
  output.can_select_perk = &FakePerkGate;
  output.can_select_perk_ignore_cost = &FakeIgnoreCostGate;
  return output;
}

ck3::PlayerLifestyleSelectionNativeAdapterEnvironmentV1
NativeEnvironment(Fixture &fixture) {
  auto output = ck3::BindPlayerLifestyleSelectionNativeAdapterEnvironmentV1(
      kModule, true,
      ck3::kPlayerLifestyleSelectionNativeAdapterExecutableSha256V1);
  output.offline_fixture_command = true;
  output.command_manager = &fixture;
  output.submit_command = &FakeSubmit;
  output.validate_focus_command = &FakeFocusValidator;
  output.validate_perk_command = &FakePerkValidator;
  return output;
}

ck3::PlayerLifestyleSelectionNativeAdapterAccessV1 Access(Fixture &fixture) {
  return {&fixture, &IsMain, &IsPaused, &fixture.source_state,
          SourceEnvironment(), {&fixture, &ReadMemory}};
}

Dispatch DispatchTarget(Fixture &fixture, Kind kind,
                        std::string_view key) {
  g_fixture = &fixture;
  return ck3::DispatchPlayerLifestyleSelectionNativeAdapterV1(
      NativeEnvironment(fixture), Access(fixture), kModule, kPlayer, kind,
      Key(key));
}

void TestExactProductionBindingAndCertification() {
  auto production =
      ck3::BindPlayerLifestyleSelectionNativeAdapterEnvironmentV1(
          kModule, true,
          ck3::kPlayerLifestyleSelectionNativeAdapterExecutableSha256V1);
  assert(ck3::PlayerLifestyleSelectionNativeAdapterEnvironmentReadyV1(
      production));
  assert(production.command_manager == reinterpret_cast<void *>(
             kModule + ck3::kPlayerLifestyleSelectionCommandManagerRvaV1));
  assert(reinterpret_cast<std::uintptr_t>(production.submit_command) ==
         kModule + ck3::kPlayerLifestyleSelectionSubmitCommandRvaV1);
  const auto action =
      ck3::BindPlayerLifestyleSelectionActionEnvironmentFromNativeAdapterV1(
          production);
  assert(action.command_abi_certified);
  assert(!action.offline_fixture_command);

  auto bad = ck3::BindPlayerLifestyleSelectionNativeAdapterEnvironmentV1(
      kModule, true, "WRONG");
  assert(!ck3::PlayerLifestyleSelectionNativeAdapterEnvironmentReadyV1(bad));
  production.focus_primary_vtable += 8;
  assert(!ck3::PlayerLifestyleSelectionNativeAdapterEnvironmentReadyV1(
      production));
}

void TestFocusUsesExactLayoutAndOneSubmit() {
  auto fixture = Base();
  assert(DispatchTarget(*fixture, Kind::focus,
                        "stewardship_wealth_focus") ==
         Dispatch::submitted_verification_pending);
  assert(fixture->rtti_calls == 1);
  assert(fixture->focus_gate_calls == 1);
  assert(fixture->focus_validator_calls == 1);
  assert(fixture->perk_validator_calls == 0);
  assert(fixture->submit_calls == 1);
  assert(fixture->submitted_flags ==
         ck3::kPlayerLifestyleSelectionCommandChannelFlagsV1);
  assert(LoadU32(fixture->submitted_command, 0x30) == kPlayer);
  assert(ck3::PlayerLifestyleSelectionNativeDispatchResultKeyV1(
             Dispatch::submitted_verification_pending) ==
         "submitted_verification_pending");
}

void TestPerkUsesExactLayoutAndOneSubmit() {
  auto fixture = Base();
  assert(DispatchTarget(*fixture, Kind::perk, "tax_man_perk") ==
         Dispatch::submitted_verification_pending);
  assert(fixture->perk_gate_calls == 1);
  assert(fixture->perk_validator_calls == 1);
  assert(fixture->focus_validator_calls == 0);
  assert(fixture->submit_calls == 1);
  assert(LoadPointer(fixture->submitted_command, 0x28) ==
         fixture->perk.object.address());
}

void TestResolvedPerkAvoidsWindowAndRevalidatesOnce() {
  auto fixture = Base();
  g_fixture = fixture.get();
  Put(fixture->window, ck3::kLifestyleWindowBoundCharacterIdOffsetV1,
      kPlayer + 1);
  const auto result =
      ck3::DispatchResolvedPlayerLifestylePerkNativeAdapterV1(
          NativeEnvironment(*fixture), Access(*fixture), kPlayer,
          fixture->perk.object.address());
  assert(result == Dispatch::submitted_verification_pending);
  assert(fixture->rtti_calls == 0 && fixture->perk_gate_calls == 0);
  assert(fixture->perk_validator_calls == 1 && fixture->submit_calls == 1);
  assert(LoadPointer(fixture->submitted_command, 0x28) ==
         fixture->perk.object.address());
}

void TestResolvedFocusAvoidsWindowAndRevalidatesOnce() {
  auto fixture = Base();
  g_fixture = fixture.get();
  Put(fixture->window, ck3::kLifestyleWindowBoundCharacterIdOffsetV1,
      kPlayer + 1);
  const auto result =
      ck3::DispatchResolvedPlayerLifestyleFocusNativeAdapterV1(
          NativeEnvironment(*fixture), Access(*fixture), kPlayer,
          fixture->focus.object.address());
  assert(result == Dispatch::submitted_verification_pending);
  assert(fixture->rtti_calls == 0 && fixture->focus_gate_calls == 0);
  assert(fixture->focus_validator_calls == 1 && fixture->submit_calls == 1);
  assert(LoadPointer(fixture->submitted_command, 0x28) ==
         fixture->focus.object.address());
  assert(LoadU32(fixture->submitted_command, 0x30) == kPlayer);
}

void TestEveryPreSubmitFailureAvoidsNativeSubmit() {
  {
    auto fixture = Base();
    fixture->paused = false;
    assert(DispatchTarget(*fixture, Kind::focus,
                          "stewardship_wealth_focus") ==
           Dispatch::application_main_paused_required);
    assert(fixture->rtti_calls == 0 && fixture->submit_calls == 0);
  }
  {
    auto fixture = Base();
    Put(fixture->window, ck3::kLifestyleWindowBoundCharacterIdOffsetV1,
        kPlayer + 1);
    assert(DispatchTarget(*fixture, Kind::perk, "tax_man_perk") ==
           Dispatch::source_read_rejected);
    assert(fixture->perk_validator_calls == 0 && fixture->submit_calls == 0);
  }
  {
    auto fixture = Base();
    fixture->focus_gate = false;
    assert(DispatchTarget(*fixture, Kind::focus,
                          "stewardship_wealth_focus") ==
           Dispatch::final_legality_rejected);
    assert(fixture->focus_validator_calls == 0 && fixture->submit_calls == 0);
  }
  {
    auto fixture = Base();
    fixture->perk_validator = false;
    assert(DispatchTarget(*fixture, Kind::perk, "tax_man_perk") ==
           Dispatch::command_validator_rejected);
    assert(fixture->perk_validator_calls == 1 && fixture->submit_calls == 0);
  }
  {
    auto fixture = Base();
    assert(DispatchTarget(*fixture, Kind::perk, "missing_perk") ==
           Dispatch::target_not_stably_resolved);
    assert(fixture->submit_calls == 0);
  }
}

void TestSubmitRejectionIsNeverRetriedOrReportedApplied() {
  auto fixture = Base();
  fixture->submit_result = false;
  auto environment = NativeEnvironment(*fixture);
  auto access = Access(*fixture);
  ck3::PlayerLifestyleSelectionNativeAdapterContextV1 context{
      environment, access, kModule, kPlayer, Dispatch::unavailable};
  g_fixture = fixture.get();
  assert(!ck3::SubmitPlayerLifestyleSelectionNativeAdapterV1(
      &context, Kind::focus, Key("stewardship_wealth_focus")));
  assert(context.last_result == Dispatch::submit_rejected);
  assert(fixture->submit_calls == 1);

  fixture = Base();
  environment = NativeEnvironment(*fixture);
  access = Access(*fixture);
  context = {environment, access, kModule, kPlayer, Dispatch::unavailable};
  g_fixture = fixture.get();
  assert(ck3::SubmitPlayerLifestyleSelectionNativeAdapterV1(
      &context, Kind::perk, Key("tax_man_perk")));
  assert(context.last_result == Dispatch::submitted_verification_pending);
  assert(fixture->submit_calls == 1);
  const auto action =
      ck3::BindPlayerLifestyleSelectionActionEnvironmentFromNativeAdapterV1(
          environment);
  assert(!action.command_abi_certified);
  assert(action.offline_fixture_command);
}

struct IntegratedActionContext {
  ck3::PlayerLifestyleSelectionNativeAdapterContextV1 adapter{};
  Fixture *fixture = nullptr;
  std::uint32_t precondition_captures = 0;
};

static_assert(offsetof(IntegratedActionContext, adapter) == 0);

bool CaptureIntegratedPrecondition(
    void *context,
    game::PlayerLifestyleSelectionPreconditionV1 &output) noexcept {
  auto &integrated = *static_cast<IntegratedActionContext *>(context);
  ++integrated.precondition_captures;
  output = {};
  auto &candidates = output.candidates;
  candidates.status = game::PlayerLifestyleWindowCandidatesStatusV1::available;
  Fixed(candidates.snapshot_id, "life7-native-action-fixture");
  candidates.public_revision = 71;
  candidates.native_revision = 7001;
  candidates.proof_epoch = 17;
  candidates.date_raw = 54'336'000;
  candidates.player_character_id = kPlayer;
  candidates.focus_status =
      game::PlayerLifestyleWindowCollectionStatusV1::available;
  candidates.focus_count = 1;
  candidates.focuses[0] = {Key("stewardship_wealth_focus"),
                           Key("stewardship_lifestyle"), true};
  candidates.perk_status =
      game::PlayerLifestyleWindowCollectionStatusV1::available;
  candidates.perk_count = 1;
  candidates.perks[0] = {Key("tax_man_perk"),
                         Key("stewardship_lifestyle"), true, true};
  candidates.readiness = {true, true, true, true, true, true, true};

  auto &state = output.state;
  state.available = true;
  state.paused = true;
  state.snapshot_id = candidates.snapshot_id;
  Fixed(state.episode_run_id, "native-29829-ee172aa720db");
  state.public_revision = candidates.public_revision;
  state.native_revision = candidates.native_revision;
  state.proof_epoch = candidates.proof_epoch;
  state.date_raw = candidates.date_raw;
  state.player_character_id = kPlayer;
  state.current_focus_known = true;
  state.has_current_focus = false;
  state.owned_perks_fully_materialized = true;
  state.lifestyle_progress_fully_materialized = true;
  state.lifestyle_progress_count = 1;
  state.lifestyle_progress[0] =
      {Key("stewardship_lifestyle"), 25'000, 1};
  return true;
}

bool IntegratedActionMainThread(void *) noexcept { return true; }

void TestLife6IntegrationKeepsSubmitPending() {
  auto fixture = Base();
  auto native_environment = NativeEnvironment(*fixture);
  IntegratedActionContext context{};
  context.fixture = fixture.get();
  context.adapter = {native_environment, Access(*fixture), kModule, kPlayer,
                     Dispatch::unavailable};
  g_fixture = fixture.get();

  const auto action_environment =
      ck3::BindPlayerLifestyleSelectionActionEnvironmentFromNativeAdapterV1(
          native_environment);
  ck3::PlayerLifestyleSelectionActionAccessV1 action_access{
      &context, &CaptureIntegratedPrecondition, nullptr,
      &IntegratedActionMainThread,
      &ck3::SubmitPlayerLifestyleSelectionNativeAdapterV1};
  const game::PlayerLifestyleSelectionActionRequestV1 request{
      "life7-native-action-1", Kind::focus,
      "stewardship_wealth_focus", "life7-native-action-fixture",
      "native-29829-ee172aa720db", 71, 7001, 17, 54'336'000, kPlayer};
  game::PlayerLifestyleSelectionActionAckV1 ack{};
  assert(ck3::ExecutePlayerLifestyleSelectionActionV1(
             action_environment, action_access, request, ack) ==
         game::PlayerLifestyleSelectionActionAckStatusV1::
             submitted_verification_pending);
  assert(ack.verification_pending);
  assert(context.precondition_captures == 2);
  assert(context.adapter.last_result ==
         Dispatch::submitted_verification_pending);
  assert(fixture->submit_calls == 1);

  game::PlayerLifestyleSelectionActionReceiptV1 receipt{};
  assert(ck3::VerifyPlayerLifestyleSelectionActionReceiptV1(
             action_access, ack, receipt) ==
         game::PlayerLifestyleSelectionActionReceiptStatusV1::
             postcondition_failed);
  assert(!receipt.postcondition_verified);
}

void TestBindingMismatchFailsClosed() {
  auto fixture = Base();
  g_fixture = fixture.get();
  auto environment = NativeEnvironment(*fixture);
  auto access = Access(*fixture);
  access.source_environment.admitted_executable_sha256 = "WRONG";
  assert(ck3::DispatchPlayerLifestyleSelectionNativeAdapterV1(
             environment, access, kModule, kPlayer, Kind::perk,
             Key("tax_man_perk")) ==
         Dispatch::exact_source_binding_mismatch);
  assert(fixture->rtti_calls == 0 && fixture->submit_calls == 0);
  assert(ck3::DispatchPlayerLifestyleSelectionNativeAdapterV1(
             environment, Access(*fixture), kModule + 1, kPlayer,
             Kind::perk, Key("tax_man_perk")) ==
         Dispatch::exact_source_binding_mismatch);
  assert(fixture->submit_calls == 0);
}

} // namespace

int main() {
  TestExactProductionBindingAndCertification();
  TestFocusUsesExactLayoutAndOneSubmit();
  TestPerkUsesExactLayoutAndOneSubmit();
  TestResolvedPerkAvoidsWindowAndRevalidatesOnce();
  TestResolvedFocusAvoidsWindowAndRevalidatesOnce();
  TestEveryPreSubmitFailureAvoidsNativeSubmit();
  TestSubmitRejectionIsNeverRetriedOrReportedApplied();
  TestLife6IntegrationKeepsSubmitPending();
  TestBindingMismatchFailsClosed();
  std::cout << "player lifestyle selection native adapter v1: 9/9 green\n";
  return 0;
}
