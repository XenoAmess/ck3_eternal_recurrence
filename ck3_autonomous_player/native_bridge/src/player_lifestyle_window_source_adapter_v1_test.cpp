#include "xar_bridge/player_lifestyle_window_source_adapter_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <string_view>

namespace {

namespace game = xar::game;
namespace ck3 = xar::ck3_11906;

constexpr std::uintptr_t kModule = 0x140000000ULL;
constexpr std::uint32_t kPlayer = 0x8100002AU;

template <std::size_t Size>
struct Blob {
  std::array<std::uint8_t, Size> bytes{};

  std::uintptr_t address() noexcept {
    return reinterpret_cast<std::uintptr_t>(bytes.data());
  }
};

template <typename Value, std::size_t Size>
void Put(Blob<Size> &blob, std::size_t offset, Value value) {
  assert(offset + sizeof(value) <= blob.bytes.size());
  std::memcpy(blob.bytes.data() + offset, &value, sizeof(value));
}

template <typename Value, std::size_t Size>
void Put(std::array<std::uint8_t, Size> &bytes, std::size_t offset,
         Value value) {
  assert(offset + sizeof(value) <= bytes.size());
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

template <std::size_t ObjectBytes>
struct Definition {
  Blob<ObjectBytes> object{};
  std::array<char, game::kPlayerLifestyleWindowStableKeyCapacityV1>
      key_bytes{};
};

template <std::size_t ObjectBytes>
void SetKey(Definition<ObjectBytes> &definition, std::string_view key) {
  assert(!key.empty() &&
         key.size() < game::kPlayerLifestyleWindowStableKeyCapacityV1);
  const auto offset = ck3::kLifestyleWindowStableKeyOffsetV1;
  const auto size = static_cast<std::uint64_t>(key.size());
  Put(definition.object, offset + 0x10, size);
  if (key.size() <= 15) {
    std::memcpy(definition.object.bytes.data() + offset, key.data(),
                key.size());
    Put(definition.object, offset + 0x18, std::uint64_t{15});
  } else {
    std::copy(key.begin(), key.end(), definition.key_bytes.begin());
    const auto pointer = reinterpret_cast<std::uintptr_t>(
        definition.key_bytes.data());
    Put(definition.object, offset, pointer);
    Put(definition.object, offset + 0x18,
        static_cast<std::uint64_t>(definition.key_bytes.size() - 1));
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
  std::array<std::uint8_t, 64 * ck3::kLifestyleWindowStorageSlotStrideV1>
      character_slots{};
  Blob<0x40> character{};
  Blob<0x40> fallback_character{};

  Definition<0x180> stewardship_lifestyle{};
  Definition<0x180> learning_lifestyle{};
  Definition<0x900> wealth_focus{};
  Definition<0x900> medicine_focus{};
  Definition<0x490> tax_man_perk{};
  Definition<0x490> heregeld_perk{};

  std::array<std::uintptr_t, 2> lifestyle_rows{};
  std::array<std::uintptr_t, 2> focus_rows{};
  std::array<std::uint8_t, 2 * ck3::kLifestyleWindowPerkTreeRowBytesV1>
      perk_tree_rows{};
  std::array<std::uintptr_t, 2> perk_database_rows{};
  Blob<0x80> perk_database{};

  ck3::PlayerLifestyleWindowSourceAdapterStateV1 adapter_state{};
  ck3::PlayerLifestyleWindowFrameV1 before{};
  ck3::PlayerLifestyleWindowFrameV1 after{};
  std::uint32_t frame_calls = 0;
  std::uint32_t rtti_calls = 0;
  std::uint32_t focus_gate_calls = 0;
  std::uint32_t perk_gate_calls = 0;
  std::uint32_t ignore_cost_gate_calls = 0;
  bool main_thread = true;
  bool reject_rtti = false;
  bool bad_focus_evaluator_slot = false;
  bool drift_perk_gate_on_second_acquisition = false;
  std::uint32_t current_player_global = kPlayer;
};

Fixture *g_fixture = nullptr;

template <std::size_t Size>
void Fixed(std::array<char, Size> &output, std::string_view value) {
  assert(value.size() < Size);
  output.fill('\0');
  std::copy(value.begin(), value.end(), output.begin());
}

void InstallSpan(Blob<0x170> &window, std::size_t offset,
                 std::uintptr_t data, std::int32_t capacity,
                 std::int32_t count) {
  Put(window, offset, RawSpan{data, capacity, count});
}

void InstallDatabaseSpan(Fixture &fixture, std::int32_t count) {
  Put(fixture.perk_database, ck3::kLifestyleWindowDatabaseSpanOffsetV1,
      RawSpan{reinterpret_cast<std::uintptr_t>(
                  fixture.perk_database_rows.data()),
              static_cast<std::int32_t>(fixture.perk_database_rows.size()),
              count});
}

std::unique_ptr<Fixture> Base() {
  auto fixture = std::make_unique<Fixture>();

  SetKey(fixture->stewardship_lifestyle, "stewardship_lifestyle");
  SetKey(fixture->learning_lifestyle, "learning_lifestyle");
  SetKey(fixture->wealth_focus, "stewardship_wealth_focus");
  SetKey(fixture->medicine_focus, "learning_medicine_focus");
  SetKey(fixture->tax_man_perk, "tax_man_perk");
  SetKey(fixture->heregeld_perk, "heregeld_perk");

  Put(fixture->wealth_focus.object,
      ck3::kLifestyleWindowFocusLifestyleOffsetV1,
      fixture->stewardship_lifestyle.object.address());
  Put(fixture->medicine_focus.object,
      ck3::kLifestyleWindowFocusLifestyleOffsetV1,
      fixture->learning_lifestyle.object.address());
  Put(fixture->tax_man_perk.object,
      ck3::kLifestyleWindowPerkLifestyleOffsetV1,
      fixture->stewardship_lifestyle.object.address());
  Put(fixture->heregeld_perk.object,
      ck3::kLifestyleWindowPerkLifestyleOffsetV1,
      fixture->stewardship_lifestyle.object.address());

  fixture->lifestyle_rows = {
      fixture->stewardship_lifestyle.object.address(),
      fixture->learning_lifestyle.object.address()};
  fixture->focus_rows = {fixture->wealth_focus.object.address(),
                         fixture->medicine_focus.object.address()};
  fixture->perk_database_rows = {fixture->tax_man_perk.object.address(),
                                 fixture->heregeld_perk.object.address()};

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
  InstallSpan(fixture->window,
              ck3::kLifestyleWindowLifestylesSpanOffsetV1,
              reinterpret_cast<std::uintptr_t>(fixture->lifestyle_rows.data()),
              2, 2);
  InstallSpan(fixture->window, ck3::kLifestyleWindowPerkTreeSpanOffsetV1,
              reinterpret_cast<std::uintptr_t>(
                  fixture->perk_tree_rows.data()),
              2, 2);
  InstallSpan(fixture->window, ck3::kLifestyleWindowFocusSpanOffsetV1,
              reinterpret_cast<std::uintptr_t>(fixture->focus_rows.data()),
              2, 2);
  InstallDatabaseSpan(*fixture, 2);

  Put(fixture->character_storage, ck3::kLifestyleWindowStorageSlotsOffsetV1,
      reinterpret_cast<std::uintptr_t>(fixture->character_slots.data()));
  Put(fixture->character_storage,
      ck3::kLifestyleWindowStorageCapacityOffsetV1, std::int32_t{64});
  const auto slot_offset =
      static_cast<std::size_t>(kPlayer & 0x00FFFFFFU) *
          ck3::kLifestyleWindowStorageSlotStrideV1 +
      ck3::kLifestyleWindowStorageObjectOffsetV1;
  Put(fixture->character_slots, slot_offset,
      fixture->character.address());
  Put(fixture->character, ck3::kLifestyleWindowCharacterIdentityOffsetV1,
      kPlayer);

  Fixed(fixture->before.snapshot_id, "life5-adapter-fixture-001");
  fixture->before.public_revision = 711;
  fixture->before.native_revision = 9021;
  fixture->before.proof_epoch = 31;
  fixture->before.date_raw = 54'335'000;
  fixture->before.paused = true;
  fixture->before.map_ready = true;
  fixture->before.has_played_character = true;
  fixture->before.played_character_alive = true;
  fixture->before.played_character_id = kPlayer;
  fixture->before.played_character = fixture->character.address();
  fixture->before.played_character_identity_round_trip = true;
  fixture->after = fixture->before;
  return fixture;
}

bool ReadMemory(void *context, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  std::uintptr_t value = 0;
  if (address == kModule + ck3::kLifestyleWindowGlobalRootPointerRvaV1) {
    value = fixture.root.address();
  } else if (address ==
             kModule + ck3::kLifestyleWindowPlayedCharacterIdGlobalRvaV1) {
    if (output == nullptr || size != sizeof(fixture.current_player_global)) {
      return false;
    }
    std::memcpy(output, &fixture.current_player_global,
                sizeof(fixture.current_player_global));
    return true;
  } else if (address ==
             kModule + ck3::kLifestyleWindowCharacterStorageSlotRvaV1) {
    value = fixture.character_storage.address();
  } else if (address ==
             kModule + ck3::kLifestyleWindowCharacterFallbackSlotRvaV1) {
    value = fixture.fallback_character.address();
  } else if (address ==
             kModule +
                 ck3::kLifestyleWindowCanSelectFocusEvaluatorSlotRvaV1) {
    value = kModule +
        ck3::kLifestyleWindowCanSelectFocusEvaluatorTargetRvaV1 +
        (fixture.bad_focus_evaluator_slot ? 1 : 0);
  } else if (address ==
             kModule +
                 ck3::kLifestyleWindowCanSelectPerkEvaluatorSlotRvaV1) {
    value = kModule +
        ck3::kLifestyleWindowCanSelectPerkEvaluatorTargetRvaV1;
  } else {
    if (address == 0 || output == nullptr || size == 0) return false;
    std::memcpy(output, reinterpret_cast<const void *>(address), size);
    return true;
  }
  if (output == nullptr || size != sizeof(value)) return false;
  std::memcpy(output, &value, sizeof(value));
  return true;
}

void *FakeRtti(void *source, std::int32_t vf_delta, void *source_type,
               void *target_type, std::int32_t is_reference) {
  assert(g_fixture != nullptr);
  ++g_fixture->rtti_calls;
  if (g_fixture->reject_rtti ||
      source != reinterpret_cast<void *>(g_fixture->idler_base.address()) ||
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
  assert(window == reinterpret_cast<void *>(g_fixture->window.address()));
  ++g_fixture->focus_gate_calls;
  return definition ==
      reinterpret_cast<void *>(g_fixture->wealth_focus.object.address());
}

bool FakePerkGate(void *window, void *definition) {
  assert(g_fixture != nullptr);
  assert(window == reinterpret_cast<void *>(g_fixture->window.address()));
  ++g_fixture->perk_gate_calls;
  if (g_fixture->drift_perk_gate_on_second_acquisition &&
      g_fixture->rtti_calls >= 2 &&
      definition ==
          reinterpret_cast<void *>(
              g_fixture->tax_man_perk.object.address())) {
    return true;
  }
  return definition ==
      reinterpret_cast<void *>(g_fixture->heregeld_perk.object.address());
}

bool FakeIgnoreCostGate(void *window, void *) {
  assert(g_fixture != nullptr);
  assert(window == reinterpret_cast<void *>(g_fixture->window.address()));
  ++g_fixture->ignore_cost_gate_calls;
  return true;
}

ck3::PlayerLifestyleWindowSourceAdapterEnvironmentV1 Environment() {
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

ck3::PlayerLifestyleWindowSourceAdapterAccessV1 AdapterAccess(
    Fixture &fixture) {
  return {&fixture, &ReadMemory};
}

bool CaptureFrame(void *context,
                  ck3::PlayerLifestyleWindowFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.frame_calls;
  output = fixture.frame_calls == 1 ? fixture.before : fixture.after;
  return true;
}

bool IsMainThread(void *context) noexcept {
  return static_cast<Fixture *>(context)->main_thread;
}

ck3::PlayerLifestyleWindowSourceReadResultV1 ReadForCore(
    void *context, std::uintptr_t module_base,
    std::uint32_t played_character_id,
    ck3::PlayerLifestyleWindowSourceSampleV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  return ck3::ReadPlayerLifestyleWindowSourceAdapterV1(
      fixture.adapter_state, Environment(), AdapterAccess(fixture),
      module_base, played_character_id, output);
}

ck3::PlayerLifestyleWindowCandidatesRequestV1 Request() {
  return {"life5-adapter-fixture-001", 711, 9021, 54'335'000, kPlayer};
}

ck3::PlayerLifestyleWindowCandidatesAccessV1 CoreAccess(Fixture &fixture) {
  return {&fixture, &CaptureFrame, &IsMainThread, &ReadForCore};
}

ck3::PlayerLifestyleWindowCandidatesEnvironmentV1 CoreEnvironment() {
  return {true, ck3::kPlayerLifestyleWindowCandidatesExecutableSha256V1,
          kModule, true};
}

void Select(Fixture &fixture) { g_fixture = &fixture; }

void TestAdapterFeedsStableSemanticCore() {
  auto fixture = Base();
  Select(*fixture);
  game::PlayerLifestyleWindowCandidatesV1 output{};
  assert(ck3::ReadPlayerLifestyleWindowCandidatesV1(
             CoreEnvironment(), CoreAccess(*fixture), Request(), output) ==
         game::ReadPlayerLifestyleWindowCandidatesResultV1::available);
  assert(output.status ==
         game::PlayerLifestyleWindowCandidatesStatusV1::available);
  assert(output.player_character_id == kPlayer);
  assert(output.focus_count == 2 && output.perk_count == 2);
  assert(ck3::PlayerLifestyleWindowStableKeyViewV1(
             output.focuses[0].key) == "learning_medicine_focus");
  assert(!output.focuses[0].can_select && output.focuses[1].can_select);
  assert(ck3::PlayerLifestyleWindowStableKeyViewV1(
             output.perks[0].key) == "heregeld_perk");
  assert(output.perks[0].can_select &&
         output.perks[0].can_select_ignore_cost);
  assert(!output.perks[1].can_select &&
         output.perks[1].can_select_ignore_cost);
  assert(output.readiness.same_frame_ready);
  assert(fixture->adapter_state.root_acquisition_serial == 2);
  assert(fixture->rtti_calls == 2 && fixture->focus_gate_calls == 4 &&
         fixture->perk_gate_calls == 4 &&
         fixture->ignore_cost_gate_calls == 4);
}

void TestKnownEmptyContainersRemainKnownEmpty() {
  auto fixture = Base();
  Select(*fixture);
  InstallSpan(fixture->window, ck3::kLifestyleWindowFocusSpanOffsetV1, 0,
              2, 0);
  InstallDatabaseSpan(*fixture, 0);
  game::PlayerLifestyleWindowCandidatesV1 output{};
  assert(ck3::ReadPlayerLifestyleWindowCandidatesV1(
             CoreEnvironment(), CoreAccess(*fixture), Request(), output) ==
         game::ReadPlayerLifestyleWindowCandidatesResultV1::available);
  assert(output.focus_status ==
         game::PlayerLifestyleWindowCollectionStatusV1::known_empty);
  assert(output.perk_status ==
         game::PlayerLifestyleWindowCollectionStatusV1::known_empty);
  assert(fixture->focus_gate_calls == 0 && fixture->perk_gate_calls == 0 &&
         fixture->ignore_cost_gate_calls == 0);
}

void TestStaleAndWrongOwnerNeverReachEvaluators() {
  auto stale = Base();
  Select(*stale);
  Put(stale->window, ck3::kLifestyleWindowBoundCharacterIdOffsetV1,
      kPlayer + 1);
  game::PlayerLifestyleWindowCandidatesV1 output{};
  assert(ck3::ReadPlayerLifestyleWindowCandidatesV1(
             CoreEnvironment(), CoreAccess(*stale), Request(), output) ==
         game::ReadPlayerLifestyleWindowCandidatesResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::PlayerLifestyleWindowCandidatesFailureV1::
             lifestyle_window_unbound_or_stale);
  assert(stale->focus_gate_calls == 0 && stale->perk_gate_calls == 0);

  auto generation = Base();
  Select(*generation);
  Put(generation->character,
      ck3::kLifestyleWindowCharacterIdentityOffsetV1, kPlayer + 1);
  assert(ck3::ReadPlayerLifestyleWindowCandidatesV1(
             CoreEnvironment(), CoreAccess(*generation), Request(), output) ==
         game::ReadPlayerLifestyleWindowCandidatesResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::PlayerLifestyleWindowCandidatesFailureV1::
             lifestyle_window_unbound_or_stale);
  assert(generation->focus_gate_calls == 0 &&
         generation->perk_gate_calls == 0);

  auto current_global = Base();
  Select(*current_global);
  current_global->current_player_global = kPlayer + 1;
  assert(ck3::ReadPlayerLifestyleWindowCandidatesV1(
             CoreEnvironment(), CoreAccess(*current_global), Request(),
             output) ==
         game::ReadPlayerLifestyleWindowCandidatesResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::PlayerLifestyleWindowCandidatesFailureV1::
             lifestyle_window_unbound_or_stale);
  assert(current_global->focus_gate_calls == 0 &&
         current_global->perk_gate_calls == 0);

  auto owner = Base();
  Select(*owner);
  Put(owner->window, 0,
      kModule + ck3::kLifestyleWindowPrimaryVtableRvaV1 + 1);
  assert(ck3::ReadPlayerLifestyleWindowCandidatesV1(
             CoreEnvironment(), CoreAccess(*owner), Request(), output) ==
         game::ReadPlayerLifestyleWindowCandidatesResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::PlayerLifestyleWindowCandidatesFailureV1::owner_path_invalid);
  assert(owner->focus_gate_calls == 0 && owner->perk_gate_calls == 0);
}

void TestTypedAdapterFailures() {
  auto rtti = Base();
  Select(*rtti);
  rtti->reject_rtti = true;
  ck3::PlayerLifestyleWindowSourceSampleV1 sample{};
  assert(ck3::ReadPlayerLifestyleWindowSourceAdapterV1(
             rtti->adapter_state, Environment(), AdapterAccess(*rtti),
             kModule, kPlayer, sample) ==
         ck3::PlayerLifestyleWindowSourceReadResultV1::
             owner_path_unavailable);

  auto container = Base();
  Select(*container);
  InstallSpan(container->window, ck3::kLifestyleWindowFocusSpanOffsetV1,
              reinterpret_cast<std::uintptr_t>(container->focus_rows.data()),
              1, 2);
  assert(ck3::ReadPlayerLifestyleWindowSourceAdapterV1(
             container->adapter_state, Environment(),
             AdapterAccess(*container), kModule, kPlayer, sample) ==
         ck3::PlayerLifestyleWindowSourceReadResultV1::invalid_container);

  auto materialization = Base();
  Select(*materialization);
  materialization->tax_man_perk.object.bytes[
      ck3::kLifestyleWindowStableKeyOffsetV1] = 'X';
  assert(ck3::ReadPlayerLifestyleWindowSourceAdapterV1(
             materialization->adapter_state, Environment(),
             AdapterAccess(*materialization), kModule, kPlayer, sample) ==
         ck3::PlayerLifestyleWindowSourceReadResultV1::
             materialization_unavailable);

  auto evaluator = Base();
  Select(*evaluator);
  evaluator->bad_focus_evaluator_slot = true;
  assert(ck3::ReadPlayerLifestyleWindowSourceAdapterV1(
             evaluator->adapter_state, Environment(),
             AdapterAccess(*evaluator), kModule, kPlayer, sample) ==
         ck3::PlayerLifestyleWindowSourceReadResultV1::
             final_legality_evaluator_unavailable);
  assert(evaluator->focus_gate_calls == 0 && evaluator->perk_gate_calls == 0);
}

void TestGateDriftIsRejectedByLife4() {
  auto fixture = Base();
  Select(*fixture);
  fixture->drift_perk_gate_on_second_acquisition = true;
  game::PlayerLifestyleWindowCandidatesV1 output{};
  assert(ck3::ReadPlayerLifestyleWindowCandidatesV1(
             CoreEnvironment(), CoreAccess(*fixture), Request(), output) ==
         game::ReadPlayerLifestyleWindowCandidatesResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::PlayerLifestyleWindowCandidatesFailureV1::
             native_sample_drift);
  assert(fixture->adapter_state.root_acquisition_serial == 2);
}

void TestProductionBindingAndAdmission() {
  const auto bound = ck3::BindPlayerLifestyleWindowSourceAdapterEnvironmentV1(
      kModule, true,
      ck3::kPlayerLifestyleWindowCandidatesExecutableSha256V1);
  assert(!bound.offline_fixture);
  assert(ck3::PlayerLifestyleWindowSourceAdapterEnvironmentReadyV1(bound));
  assert(reinterpret_cast<std::uintptr_t>(bound.rtti_dynamic_cast) ==
         kModule + ck3::kLifestyleWindowRttiDynamicCastRvaV1);
  assert(reinterpret_cast<std::uintptr_t>(bound.character_perk_database) ==
         kModule + ck3::kLifestyleWindowCharacterPerkDatabaseRvaV1);
  assert(reinterpret_cast<std::uintptr_t>(bound.can_select_focus) ==
         kModule + ck3::kLifestyleWindowCanSelectFocusRvaV1);
  assert(reinterpret_cast<std::uintptr_t>(bound.can_select_perk) ==
         kModule + ck3::kLifestyleWindowCanSelectPerkRvaV1);
  assert(reinterpret_cast<std::uintptr_t>(
             bound.can_select_perk_ignore_cost) ==
         kModule + ck3::kLifestyleWindowCanSelectPerkIgnoreCostRvaV1);

  auto wrong_hash = bound;
  wrong_hash.admitted_executable_sha256 = "WRONG";
  assert(!ck3::PlayerLifestyleWindowSourceAdapterEnvironmentReadyV1(
      wrong_hash));

  auto fixture = Base();
  Select(*fixture);
  ck3::PlayerLifestyleWindowSourceSampleV1 sample{};
  assert(ck3::ReadPlayerLifestyleWindowSourceAdapterV1(
             fixture->adapter_state, Environment(), AdapterAccess(*fixture),
             kModule + 1, kPlayer, sample) ==
         ck3::PlayerLifestyleWindowSourceReadResultV1::source_read_failed);
  assert(fixture->rtti_calls == 0 && fixture->focus_gate_calls == 0);
}

} // namespace

int main() {
  TestAdapterFeedsStableSemanticCore();
  TestKnownEmptyContainersRemainKnownEmpty();
  TestStaleAndWrongOwnerNeverReachEvaluators();
  TestTypedAdapterFailures();
  TestGateDriftIsRejectedByLife4();
  TestProductionBindingAndAdmission();
  g_fixture = nullptr;
  std::cout << "player_lifestyle_window_source_adapter_v1_test: 6/6 GREEN\n";
  return 0;
}
