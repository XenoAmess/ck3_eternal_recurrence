#include "xar_bridge/activity_planning_snapshot_v1_native_binder.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string_view>
#include <type_traits>
#include <vector>

#if defined(_MSC_VER)
#if !defined(NOMINMAX)
#define NOMINMAX
#endif
#include <Windows.h>
#endif

namespace {

using namespace xar::bridge;

constexpr std::uintptr_t kModuleBase = 0x140000000ULL;
constexpr std::uintptr_t kRoot = 0x720000000ULL;
constexpr std::uintptr_t kIdlerBase = 0x720001000ULL;
constexpr std::uintptr_t kStorage = 0x720002000ULL;
constexpr std::uintptr_t kSlots = 0x720003000ULL;
constexpr std::uintptr_t kCharacter = 0x720004000ULL;
constexpr std::array<std::uintptr_t, 2> kIdlerGfx{0x720010000ULL,
                                                  0x720011000ULL};
constexpr std::array<std::uintptr_t, 2> kHandler{0x720020000ULL,
                                                 0x720021000ULL};
constexpr std::array<std::uintptr_t, 2> kHost{0x720030000ULL, 0x720031000ULL};
constexpr std::array<std::uintptr_t, 2> kType{0x720040000ULL, 0x720041000ULL};
constexpr std::uintptr_t kHeapKey = 0x720050000ULL;

template <std::size_t Capacity>
ActivityPlanningFixedTextV1<Capacity> Fixed(std::string_view value) {
  assert(!value.empty());
  assert(value.size() < Capacity);
  ActivityPlanningFixedTextV1<Capacity> output{};
  std::memcpy(output.bytes.data(), value.data(), value.size());
  output.size = static_cast<std::uint16_t>(value.size());
  return output;
}

struct MemoryEntry {
  std::uintptr_t address = 0;
  std::vector<std::byte> bytes{};
};

struct Fixture;
Fixture *g_fixture = nullptr;

struct Fixture {
  ActivityPlanningFrameIdentityV1 frame{77,   8811, 0x01000011, true,
                                        true, true, true};
  std::vector<MemoryEntry> memory{};
  std::size_t identity_index = 0;
  std::uint32_t read_frame_calls = 0;
  std::uint32_t rtti_calls = 0;
  std::uint32_t can_plan_calls = 0;
  std::uint32_t semantic_calls = 0;
  bool can_plan = true;
  bool bad_owner = false;
  bool bad_semantic_provenance = false;
  bool semantic_drift = false;
  bool fail_semantics = false;
  std::uint32_t drift_frame_call = 0;

  Fixture() {
    g_fixture = this;
    BuildImage();
    SelectIdentity(0);
  }

  ~Fixture() {
    if (g_fixture == this)
      g_fixture = nullptr;
  }

  void Erase(std::uintptr_t address) {
    for (auto iterator = memory.begin(); iterator != memory.end(); ++iterator) {
      if (iterator->address == address) {
        memory.erase(iterator);
        return;
      }
    }
  }

  void PutBytes(std::uintptr_t address, const void *data, std::size_t size) {
    Erase(address);
    MemoryEntry entry{};
    entry.address = address;
    entry.bytes.resize(size);
    std::memcpy(entry.bytes.data(), data, size);
    memory.push_back(std::move(entry));
  }

  template <typename Value> void Put(std::uintptr_t address, Value value) {
    PutBytes(address, &value, sizeof(value));
  }

  template <std::size_t Size>
  void Put(std::uintptr_t address,
           const std::array<std::uint8_t, Size> &value) {
    PutBytes(address, value.data(), value.size());
  }

  bool Read(std::uintptr_t address, void *output, std::size_t size) const {
    for (const auto &entry : memory) {
      if (address >= entry.address &&
          address - entry.address <= entry.bytes.size() &&
          size <= entry.bytes.size() -
                      static_cast<std::size_t>(address - entry.address)) {
        std::memcpy(output,
                    entry.bytes.data() +
                        static_cast<std::size_t>(address - entry.address),
                    size);
        return true;
      }
    }
#if defined(_MSC_VER)
    __try {
      std::memcpy(output, reinterpret_cast<const void *>(address), size);
      return true;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
      return false;
    }
#else
    return false;
#endif
  }

  void PutSlot(std::uintptr_t vtable_rva, std::size_t slot,
               std::uintptr_t target_rva) {
    Put(kModuleBase + vtable_rva + slot * sizeof(std::uintptr_t),
        kModuleBase + target_rva);
  }

  void BuildImage() {
    Put(kModuleBase + kActivityPlanningHandlerInstallSignatureRvaV1,
        kActivityPlanningHandlerInstallSignatureV1);
    Put(kModuleBase + kActivityPlanningIdlerGfxSlotOneTargetRvaV1,
        kActivityPlanningIdlerOwnerSignatureV1);
    Put(kModuleBase + kActivityPlanningHostConstructorSignatureRvaV1,
        kActivityPlanningHostConstructorSignatureV1);
    Put(kModuleBase + kActivityPlanningTypeSetterSignatureRvaV1,
        kActivityPlanningTypeSetterSignatureV1);
    Put(kModuleBase + kActivityPlanningOwnerSetterSignatureRvaV1,
        kActivityPlanningOwnerSetterSignatureV1);
    Put(kModuleBase + kActivityPlanningHostViewCanPlanRvaV1,
        kActivityPlanningCanPlanSignatureV1);
    Put(kModuleBase + kActivityPlanningRttiDynamicCastRvaV1,
        kActivityPlanningRttiCastSignatureV1);
    PutSlot(kActivityPlanningIdlerGfxVtableRvaV1, 0,
            kActivityPlanningIdlerGfxSlotZeroTargetRvaV1);
    PutSlot(kActivityPlanningIdlerGfxVtableRvaV1, 1,
            kActivityPlanningIdlerGfxSlotOneTargetRvaV1);
    PutSlot(kActivityPlanningHandlerVtableRvaV1, 0,
            kActivityPlanningHandlerSlotZeroTargetRvaV1);
    PutSlot(kActivityPlanningHostViewPrimaryVtableRvaV1, 0,
            kActivityPlanningHostSlotZeroTargetRvaV1);
    PutSlot(kActivityPlanningHostViewPrimaryVtableRvaV1,
            kActivityPlanningHostViewCanPlanVtableSlotV1,
            kActivityPlanningHostViewCanPlanRvaV1);
    PutSlot(kActivityPlanningHostSecondaryVtableRvaV1, 0,
            kActivityPlanningHostSecondarySlotZeroTargetRvaV1);
    PutSlot(kActivityPlanningActivityTypeVtableRvaV1, 0,
            kActivityPlanningActivityTypeSlotZeroTargetRvaV1);

    Put(kModuleBase + kActivityPlanningGlobalRootPointerRvaV1, kRoot);
    Put(kRoot + kActivityPlanningRootIdlerOffsetV1, kIdlerBase);
    Put(kModuleBase + kActivityPlanningCharacterStorageSlotRvaV1, kStorage);
    Put(kModuleBase + kActivityPlanningCharacterFallbackSlotRvaV1,
        std::uintptr_t{0x7200F0000ULL});
    Put(kStorage + kActivityPlanningCharacterStorageSlotsOffsetV1, kSlots);
    Put(kStorage + kActivityPlanningCharacterStorageCapacityOffsetV1,
        std::int32_t{64});
    const auto index =
        static_cast<std::uint32_t>(frame.owner_character_id) & 0x00FFFFFFU;
    Put(kSlots + index * kActivityPlanningCharacterStorageSlotStrideV1 +
            kActivityPlanningCharacterStorageObjectOffsetV1,
        kCharacter);
    Put(kCharacter + kActivityPlanningCharacterIdentityOffsetV1,
        static_cast<std::uint32_t>(frame.owner_character_id));
    for (std::size_t index_value = 0; index_value < kType.size();
         ++index_value) {
      Put(kIdlerGfx[index_value],
          kModuleBase + kActivityPlanningIdlerGfxVtableRvaV1);
      Put(kIdlerGfx[index_value] + kActivityPlanningIdlerHandlerOffsetV1,
          kHandler[index_value]);
      Put(kHandler[index_value],
          kModuleBase + kActivityPlanningHandlerVtableRvaV1);
      Put(kHandler[index_value] + kActivityPlanningHandlerActivityHostOffsetV1,
          kHost[index_value]);
      Put(kHost[index_value],
          kModuleBase + kActivityPlanningHostViewPrimaryVtableRvaV1);
      Put(kHost[index_value] + kActivityPlanningHostSecondaryVtableOffsetV1,
          kModuleBase + kActivityPlanningHostSecondaryVtableRvaV1);
      Put(kHost[index_value] + kActivityPlanningHostOwnerRoundTripOffsetV1,
          kHandler[index_value]);
      Put(kHost[index_value] + kActivityPlanningHostOwnerIdOffsetV1,
          frame.owner_character_id);
      Put(kHost[index_value] + kActivityPlanningHostViewActivityTypeOffsetV1,
          kType[index_value]);
      Put(kType[index_value],
          kModuleBase + kActivityPlanningActivityTypeVtableRvaV1);
    }
    const std::string_view activity_key =
        kActivityPlanningSnapshotP0ActivityKeyV1;
    PutBytes(kType[0] + kActivityPlanningActivityTypeStableKeyOffsetV1,
             activity_key.data(), activity_key.size());
    Put(kType[0] + kActivityPlanningActivityTypeStableKeyOffsetV1 + 0x10,
        static_cast<std::uint64_t>(activity_key.size()));
    Put(kType[0] + kActivityPlanningActivityTypeStableKeyOffsetV1 + 0x18,
        std::uint64_t{15});
    Put(kType[1] + kActivityPlanningActivityTypeStableKeyOffsetV1, kHeapKey);
    PutBytes(kHeapKey, activity_key.data(), activity_key.size());
    Put(kType[1] + kActivityPlanningActivityTypeStableKeyOffsetV1 + 0x10,
        static_cast<std::uint64_t>(activity_key.size()));
    Put(kType[1] + kActivityPlanningActivityTypeStableKeyOffsetV1 + 0x18,
        std::uint64_t{31});
  }

  void SelectIdentity(std::size_t index) {
    assert(index < kHost.size());
    identity_index = index;
    Put(kModuleBase + kActivityPlanningPlayedCharacterIdRvaV1,
        bad_owner ? static_cast<std::uint32_t>(frame.owner_character_id + 1)
                  : static_cast<std::uint32_t>(frame.owner_character_id));
  }

  ActivityPlanningSnapshotRequestV1 Request() const {
    return {frame.snapshot_revision, frame.date_raw, frame.owner_character_id,
            kActivityPlanningSnapshotP0ActivityKeyV1};
  }
};

bool ReadFrame(void *context,
               ActivityPlanningFrameIdentityV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.read_frame_calls;
  if (fixture.drift_frame_call != 0 &&
      fixture.read_frame_calls == fixture.drift_frame_call)
    ++fixture.frame.snapshot_revision;
  output = fixture.frame;
  return true;
}

bool ReadMemory(void *context, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  return static_cast<Fixture *>(context)->Read(address, output, size);
}

void *RttiCast(void *source, std::int32_t, void *source_type, void *target_type,
               std::int32_t) {
  assert(g_fixture != nullptr);
  ++g_fixture->rtti_calls;
  if (reinterpret_cast<std::uintptr_t>(source) != kIdlerBase ||
      reinterpret_cast<std::uintptr_t>(source_type) !=
          kModuleBase + kActivityPlanningIdlerTypeDescriptorRvaV1 ||
      reinterpret_cast<std::uintptr_t>(target_type) !=
          kModuleBase + kActivityPlanningIdlerGfxTypeDescriptorRvaV1)
    return nullptr;
  return reinterpret_cast<void *>(kIdlerGfx[g_fixture->identity_index]);
}

ActivityPlanningNativeSemanticSampleV1 SemanticSample(Fixture &fixture) {
  ActivityPlanningNativeSemanticSampleV1 output{};
  output.frame = fixture.frame;
  output.owner_character_id = fixture.frame.owner_character_id;
  output.activity_key = Fixed<kActivityPlanningStableKeyCapacityV1>(
      kActivityPlanningSnapshotP0ActivityKeyV1);
  output.complete = true;
  output.candidate_source =
      ActivityPlanningCandidateSourceV1::native_legal_location_collection;
  output.configured_cost_source =
      fixture.bad_semantic_provenance
          ? ActivityPlanningConfiguredCostSourceV1::ui_predicted_cost
          : ActivityPlanningConfiguredCostSourceV1::
                native_authoritative_configured_cost;
  output.configuration_source =
      ActivityPlanningConfigurationSourceV1::native_selected_configuration;
  output.locations[0] = {
      101, Fixed<kActivityPlanningStableKeyCapacityV1>("province_101"), 175000,
      1};
  output.locations[1] = {
      202, Fixed<kActivityPlanningStableKeyCapacityV1>("province_202"), 50000,
      0};
  output.location_count = 2;
  output.configured_costs[0] = {
      Fixed<kActivityPlanningStableKeyCapacityV1>("gold"), 12000000};
  output.configured_costs[1] = {
      Fixed<kActivityPlanningStableKeyCapacityV1>("prestige"), 250000};
  output.configured_cost_count = 2;
  output.selected_options[0] = Fixed<kActivityPlanningStableKeyCapacityV1>(
      "activity_option_food_normal");
  output.selected_options[1] = Fixed<kActivityPlanningStableKeyCapacityV1>(
      "activity_option_drink_normal");
  output.selected_option_count = 2;
  output.host_intent_key =
      Fixed<kActivityPlanningStableKeyCapacityV1>("reduce_stress_intent");
  output.guest_intent_key =
      Fixed<kActivityPlanningStableKeyCapacityV1>("reduce_stress_intent");
  output.invite_rule_key = Fixed<kActivityPlanningStableKeyCapacityV1>(
      "activity_invite_rule_default");
  output.shown = 1;
  output.can_start = 1;
  output.affordable = 1;
  output.cooldown_active = 0;
  output.cooldown_days_remaining = 0;
  return output;
}

bool InvokeCanPlan(void *context, std::uintptr_t module_base,
                   std::uintptr_t exact_entry_point, std::uintptr_t host_view,
                   std::uintptr_t activity_type,
                   const ActivityPlanningSnapshotRequestV1 &request,
                   ActivityPlanningNativeCanPlanResultV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.can_plan_calls;
  if (module_base != kModuleBase ||
      exact_entry_point !=
          kModuleBase + kActivityPlanningHostViewCanPlanRvaV1 ||
      host_view != kHost[fixture.identity_index] ||
      activity_type != kType[fixture.identity_index] ||
      request.activity_key != kActivityPlanningSnapshotP0ActivityKeyV1)
    return false;
  output = {};
  output.complete = true;
  output.used_host_view_final_can_plan = true;
  output.value = fixture.can_plan ? 1 : 0;
  if (!fixture.can_plan) {
    output.failure_display_key = Fixed<kActivityPlanningStableKeyCapacityV1>(
        "activity_feast_can_plan_failure");
    output.failure_display_text = Fixed<kActivityPlanningDisplayTextCapacityV1>(
        "A feast is unavailable.");
  }
  return true;
}

bool ReadSemantics(void *context, std::uintptr_t module_base,
                   std::uintptr_t host_view, std::uintptr_t activity_type,
                   const ActivityPlanningSnapshotRequestV1 &request,
                   ActivityPlanningNativeSemanticSampleV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.semantic_calls;
  if (fixture.fail_semantics || module_base != kModuleBase ||
      host_view != kHost[fixture.identity_index] ||
      activity_type != kType[fixture.identity_index] ||
      request.activity_key != kActivityPlanningSnapshotP0ActivityKeyV1)
    return false;
  output = SemanticSample(fixture);
  if (fixture.semantic_drift && fixture.semantic_calls == 2)
    ++output.locations[0].native_weight_q100000;
  return true;
}

ActivityPlanningNativeBinderEnvironmentV1 Environment(Fixture &fixture) {
  ActivityPlanningNativeBinderEnvironmentV1 output{};
  output.exact_build_admitted = true;
  output.admitted_executable_sha256 =
      kActivityPlanningSourceAdapterExecutableSha256V1;
  output.module_base = kModuleBase;
  output.offline_fixture = true;
  output.context = &fixture;
  output.read_frame = &ReadFrame;
  output.read_memory = &ReadMemory;
  output.rtti_dynamic_cast = &RttiCast;
  output.invoke_final_can_plan = &InvokeCanPlan;
  output.read_semantics = &ReadSemantics;
  return output;
}

struct Harness {
  Fixture fixture{};
  ActivityPlanningNativeBinderStateV1 binder{};
  ActivityPlanningSourceAdapterStateV1 adapter{};
  ActivityPlanningSnapshotPrivateEnvironmentV1 observer{};

  Harness() { Configure(); }

  void Configure() {
    ActivityPlanningSourceAdapterEnvironmentV1 source{};
    assert(ConfigureActivityPlanningNativeBinderV1(binder, Environment(fixture),
                                                   source));
    assert(ConfigureActivityPlanningSourceAdapterV1(adapter, source, observer));
  }

  bool Read(ActivityPlanningSnapshotPrivateV1 &output) {
    return ReadActivityPlanningSnapshotPrivateObserverV1(
        observer, fixture.Request(), output);
  }
};

std::string_view View(const ActivityPlanningStableKeyV1 &value) {
  return ActivityPlanningFixedTextViewV1(value);
}

void TestFullP0CaptureAndFreshResolution() {
  Harness harness{};
  ActivityPlanningSnapshotPrivateV1 output{};
  assert(harness.Read(output));
  assert(output.status == ActivityPlanningSnapshotStatusV1::available);
  assert(output.can_plan_final.value);
  assert(output.failure_display_key.state ==
         ActivityPlanningFieldStateV1::unknown);
  assert(output.failure_display_key.unknown_reason ==
         ActivityPlanningUnknownReasonV1::not_applicable);
  assert(output.candidates.count == 2);
  assert(View(output.candidates.rows[0].location_key) == "province_101");
  assert(output.candidates.rows[0].native_weight_q100000 == 175000);
  assert(output.configured_cost.source ==
         ActivityPlanningConfiguredCostSourceV1::
             native_authoritative_configured_cost);
  assert(View(output.configured_cost.rows[0].resource_key) == "gold");
  assert(View(output.selected_options.keys[0]) ==
         "activity_option_food_normal");
  assert(View(output.host_intent_key.value) == "reduce_stress_intent");
  assert(View(output.invite_rule_key.value) == "activity_invite_rule_default");
  assert(output.readiness.action_inputs_ready);
  assert(!output.readiness.raw_pointer_fields_persisted);
  assert(harness.fixture.can_plan_calls == 2);
  assert(harness.fixture.semantic_calls == 6);
  assert(harness.fixture.rtti_calls == 10);
  assert(!harness.binder.container_active.load());
  assert(harness.binder.active_token == 0);
  assert(harness.binder.active_sample.location_count == 0);
}

void TestHeapDefinitionAndIdentityReplacement() {
  Harness harness{};
  ActivityPlanningSnapshotPrivateV1 first{};
  ActivityPlanningSnapshotPrivateV1 second{};
  assert(harness.Read(first));
  harness.fixture.SelectIdentity(1);
  assert(harness.Read(second));
  assert(View(first.activity_key) == View(second.activity_key));
  assert(harness.fixture.rtti_calls == 20);
  assert(harness.fixture.semantic_calls == 12);
}

void TestFinalCanPlanFailureIsTypedAndCopied() {
  Harness harness{};
  harness.fixture.can_plan = false;
  ActivityPlanningSnapshotPrivateV1 output{};
  assert(harness.Read(output));
  assert(!output.can_plan_final.value);
  assert(output.failure_display_key.state ==
         ActivityPlanningFieldStateV1::known);
  assert(View(output.failure_display_key.value) ==
         "activity_feast_can_plan_failure");
  assert(ActivityPlanningFixedTextViewV1(output.failure_display_text.value) ==
         "A feast is unavailable.");
  harness.binder.can_plan_scratch.failure_display_key = {};
  assert(View(output.failure_display_key.value) ==
         "activity_feast_can_plan_failure");
}

void TestExactBuildImageAndSlotGate() {
  Fixture fixture{};
  ActivityPlanningNativeBinderStateV1 state{};
  ActivityPlanningSourceAdapterEnvironmentV1 source{};
  auto environment = Environment(fixture);
  environment.admitted_executable_sha256 = "wrong";
  assert(!ConfigureActivityPlanningNativeBinderV1(state, environment, source));
  assert(ReadActivityPlanningNativeBinderFailureV1(state) ==
         ActivityPlanningNativeBinderFailureV1::exact_build_not_admitted);

  environment = Environment(fixture);
  const std::uint8_t bad = 0;
  fixture.PutBytes(kModuleBase + kActivityPlanningHandlerInstallSignatureRvaV1,
                   &bad, 1);
  assert(!ConfigureActivityPlanningNativeBinderV1(state, environment, source));
  assert(ReadActivityPlanningNativeBinderFailureV1(state) ==
         ActivityPlanningNativeBinderFailureV1::image_signature_mismatch);

  fixture.BuildImage();
  fixture.PutSlot(kActivityPlanningHostViewPrimaryVtableRvaV1,
                  kActivityPlanningHostViewCanPlanVtableSlotV1,
                  kActivityPlanningHostViewCanPlanRvaV1 + 1);
  assert(!ConfigureActivityPlanningNativeBinderV1(state, environment, source));
  assert(ReadActivityPlanningNativeBinderFailureV1(state) ==
         ActivityPlanningNativeBinderFailureV1::vtable_slot_mismatch);

  fixture.BuildImage();
  environment = Environment(fixture);
  environment.read_semantics = nullptr;
  assert(!ConfigureActivityPlanningNativeBinderV1(state, environment, source));
  assert(ReadActivityPlanningNativeBinderFailureV1(state) ==
         ActivityPlanningNativeBinderFailureV1::callbacks_missing);
}

void TestOwnerAndSemanticRedRemainVisible() {
  Harness owner{};
  owner.fixture.bad_owner = true;
  owner.fixture.SelectIdentity(0);
  ActivityPlanningSnapshotPrivateV1 output{};
  assert(!owner.Read(output));
  assert(ReadActivityPlanningNativeBinderFailureV1(owner.binder) ==
         ActivityPlanningNativeBinderFailureV1::owner_identity_mismatch);

  Harness provenance{};
  provenance.fixture.bad_semantic_provenance = true;
  assert(!provenance.Read(output));
  assert(ReadActivityPlanningNativeBinderFailureV1(provenance.binder) ==
         ActivityPlanningNativeBinderFailureV1::semantic_sample_invalid);

  Harness drift{};
  drift.fixture.semantic_drift = true;
  assert(!drift.Read(output));
  assert(ReadActivityPlanningNativeBinderFailureV1(drift.binder) ==
         ActivityPlanningNativeBinderFailureV1::semantic_sample_drift);
  assert(!drift.binder.container_active.load());
}

void TestContainerLifecycleAndFrameDriftFailClosed() {
  Harness harness{};
  ActivityPlanningSourceAdapterEnvironmentV1 source{};
  assert(ConfigureActivityPlanningNativeBinderV1(
      harness.binder, Environment(harness.fixture), source));
  std::uintptr_t host = 0;
  assert(source.resolve_host_view(
      source.context, harness.fixture.frame.owner_character_id,
      kActivityPlanningSnapshotP0ActivityKeyV1, host));
  std::uintptr_t type = 0;
  assert(source.read_memory(
      source.context, host + kActivityPlanningHostViewActivityTypeOffsetV1,
      &type, sizeof(type)));
  std::uintptr_t token = 0;
  assert(source.open_source_container(source.context, host, type,
                                      harness.fixture.Request(), token));
  std::uintptr_t second_token = 0;
  assert(!source.open_source_container(
      source.context, host, type, harness.fixture.Request(), second_token));
  assert(ReadActivityPlanningNativeBinderFailureV1(harness.binder) ==
         ActivityPlanningNativeBinderFailureV1::container_busy);
  assert(!source.release_source_container(source.context, token + 1));
  assert(source.release_source_container(source.context, token));
  ActivityPlanningSourceContainerViewV1 view{};
  assert(!source.read_source_container(source.context, token, view));

  Harness frame_drift{};
  frame_drift.fixture.drift_frame_call = 5;
  ActivityPlanningSnapshotPrivateV1 output{};
  assert(!frame_drift.Read(output));
  assert(ReadActivityPlanningNativeBinderFailureV1(frame_drift.binder) ==
         ActivityPlanningNativeBinderFailureV1::frame_mismatch);
  assert(!frame_drift.binder.container_active.load());
}

void TestFailureKey() {
  assert(ActivityPlanningNativeBinderFailureKeyV1(
             ActivityPlanningNativeBinderFailureV1::semantic_sample_drift) ==
         "semantic_sample_drift");
}

} // namespace

int main() {
  static_assert(
      std::is_trivially_copyable_v<ActivityPlanningNativeSemanticSampleV1>);
  TestFullP0CaptureAndFreshResolution();
  TestHeapDefinitionAndIdentityReplacement();
  TestFinalCanPlanFailureIsTypedAndCopied();
  TestExactBuildImageAndSlotGate();
  TestOwnerAndSemanticRedRemainVisible();
  TestContainerLifecycleAndFrameDriftFailClosed();
  TestFailureKey();
  return 0;
}
