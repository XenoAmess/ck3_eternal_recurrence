#include "xar_bridge/activity_planning_snapshot_v1_application_glue.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>
#include <utility>
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
constexpr std::uintptr_t kRoot = 0x730000000ULL;
constexpr std::uintptr_t kIdlerBase = 0x730001000ULL;
constexpr std::uintptr_t kIdlerGfx = 0x730002000ULL;
constexpr std::uintptr_t kHandler = 0x730003000ULL;
constexpr std::uintptr_t kHost = 0x730004000ULL;
constexpr std::uintptr_t kActivityType = 0x730005000ULL;
constexpr std::uintptr_t kStorage = 0x730006000ULL;
constexpr std::uintptr_t kSlots = 0x730007000ULL;
constexpr std::uintptr_t kCharacter = 0x730008000ULL;

template <std::size_t Capacity>
ActivityPlanningFixedTextV1<Capacity> Fixed(std::string_view value) {
  assert(!value.empty() && value.size() < Capacity);
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
  ActivityPlanningFrameIdentityV1 frame{91,   9021, 0x01000011, true,
                                        true, true, true};
  std::vector<MemoryEntry> memory{};
  std::uint32_t read_frame_calls = 0;
  std::uint32_t final_evaluator_calls = 0;
  std::uint32_t semantic_operation_calls = 0;
  bool can_plan = true;
  bool fail_semantics = false;

  Fixture() {
    g_fixture = this;
    BuildImage();
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
    Put(kIdlerGfx, kModuleBase + kActivityPlanningIdlerGfxVtableRvaV1);
    Put(kIdlerGfx + kActivityPlanningIdlerHandlerOffsetV1, kHandler);
    Put(kHandler, kModuleBase + kActivityPlanningHandlerVtableRvaV1);
    Put(kHandler + kActivityPlanningHandlerActivityHostOffsetV1, kHost);
    Put(kHost, kModuleBase + kActivityPlanningHostViewPrimaryVtableRvaV1);
    Put(kHost + kActivityPlanningHostSecondaryVtableOffsetV1,
        kModuleBase + kActivityPlanningHostSecondaryVtableRvaV1);
    Put(kHost + kActivityPlanningHostOwnerRoundTripOffsetV1, kHandler);
    Put(kHost + kActivityPlanningHostOwnerIdOffsetV1, frame.owner_character_id);
    Put(kHost + kActivityPlanningHostViewActivityTypeOffsetV1, kActivityType);
    Put(kActivityType, kModuleBase + kActivityPlanningActivityTypeVtableRvaV1);
    const auto activity_key = kActivityPlanningSnapshotP0ActivityKeyV1;
    PutBytes(kActivityType + kActivityPlanningActivityTypeStableKeyOffsetV1,
             activity_key.data(), activity_key.size());
    Put(kActivityType + kActivityPlanningActivityTypeStableKeyOffsetV1 + 0x10,
        static_cast<std::uint64_t>(activity_key.size()));
    Put(kActivityType + kActivityPlanningActivityTypeStableKeyOffsetV1 + 0x18,
        std::uint64_t{15});

    Put(kModuleBase + kActivityPlanningPlayedCharacterIdRvaV1,
        static_cast<std::uint32_t>(frame.owner_character_id));
    Put(kModuleBase + kActivityPlanningCharacterStorageSlotRvaV1, kStorage);
    Put(kModuleBase + kActivityPlanningCharacterFallbackSlotRvaV1,
        std::uintptr_t{0x7300F0000ULL});
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
  }

  ActivityPlanningSnapshotRequestV1 Request(std::string_view key) const {
    return {frame.snapshot_revision, frame.date_raw, frame.owner_character_id,
            key};
  }
};

bool ReadFrame(void *context,
               ActivityPlanningFrameIdentityV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.read_frame_calls;
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
  if (reinterpret_cast<std::uintptr_t>(source) != kIdlerBase ||
      reinterpret_cast<std::uintptr_t>(source_type) !=
          kModuleBase + kActivityPlanningIdlerTypeDescriptorRvaV1 ||
      reinterpret_cast<std::uintptr_t>(target_type) !=
          kModuleBase + kActivityPlanningIdlerGfxTypeDescriptorRvaV1) {
    return nullptr;
  }
  return reinterpret_cast<void *>(kIdlerGfx);
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
  output.configured_cost_source = ActivityPlanningConfiguredCostSourceV1::
      native_authoritative_configured_cost;
  output.configuration_source =
      ActivityPlanningConfigurationSourceV1::native_selected_configuration;
  output.locations[0] = {
      101, Fixed<kActivityPlanningStableKeyCapacityV1>("province_101"), 175000,
      1};
  output.location_count = 1;
  output.configured_costs[0] = {
      Fixed<kActivityPlanningStableKeyCapacityV1>("gold"), 12000000};
  output.configured_cost_count = 1;
  output.selected_options[0] = Fixed<kActivityPlanningStableKeyCapacityV1>(
      "activity_option_food_normal");
  output.selected_option_count = 1;
  output.host_intent_key =
      Fixed<kActivityPlanningStableKeyCapacityV1>("reduce_stress_intent");
  output.guest_intent_key =
      Fixed<kActivityPlanningStableKeyCapacityV1>("reduce_stress_intent");
  output.invite_rule_key = Fixed<kActivityPlanningStableKeyCapacityV1>(
      "activity_invite_rule_default");
  output.shown = 1;
  output.can_start = 1;
  output.affordable = 1;
  return output;
}

bool InvokeFinalCanPlan(
    void *context, std::uintptr_t module_base, std::uintptr_t exact_entry_point,
    std::uintptr_t host_view, std::uintptr_t activity_type,
    const ActivityPlanningSnapshotRequestV1 &request,
    ActivityPlanningNativeCanPlanResultV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.final_evaluator_calls;
  if (module_base != kModuleBase ||
      exact_entry_point !=
          kModuleBase + kActivityPlanningHostViewCanPlanRvaV1 ||
      host_view != kHost || activity_type != kActivityType ||
      request.activity_key != kActivityPlanningSnapshotP0ActivityKeyV1) {
    return false;
  }
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
  ++fixture.semantic_operation_calls;
  if (fixture.fail_semantics || module_base != kModuleBase ||
      host_view != kHost || activity_type != kActivityType ||
      request.activity_key != kActivityPlanningSnapshotP0ActivityKeyV1) {
    return false;
  }
  output = SemanticSample(fixture);
  return true;
}

ActivityPlanningApplicationGlueEnvironmentV1 Environment(Fixture &fixture) {
  ActivityPlanningApplicationGlueEnvironmentV1 output{};
  output.glue_enabled = true;
  auto &native = output.native_environment;
  native.exact_build_admitted = true;
  native.admitted_executable_sha256 =
      kActivityPlanningSnapshotExecutableSha256V1;
  native.module_base = kModuleBase;
  native.offline_fixture = true;
  native.context = &fixture;
  native.read_frame = &ReadFrame;
  native.read_memory = &ReadMemory;
  native.rtti_dynamic_cast = &RttiCast;
  native.invoke_final_can_plan = &InvokeFinalCanPlan;
  native.read_semantics = &ReadSemantics;
  return output;
}

void TestConfigurationAndRequestGates() {
  Fixture fixture{};
  ActivityPlanningApplicationGlueStateV1 state{};
  auto environment = Environment(fixture);
  environment.glue_enabled = false;
  assert(!ConfigureActivityPlanningApplicationGlueV1(state, environment));
  assert(ReadActivityPlanningApplicationGlueDiagnosticsV1(state).failure ==
         ActivityPlanningApplicationGlueFailureV1::glue_disabled);

  ActivityPlanningApplicationGlueStateV1 missing{};
  environment = Environment(fixture);
  environment.native_environment.read_semantics = nullptr;
  assert(!ConfigureActivityPlanningApplicationGlueV1(missing, environment));
  assert(ReadActivityPlanningApplicationGlueDiagnosticsV1(missing).failure ==
         ActivityPlanningApplicationGlueFailureV1::callbacks_missing);

  ActivityPlanningApplicationGlueStateV1 configured{};
  assert(ConfigureActivityPlanningApplicationGlueV1(configured,
                                                    Environment(fixture)));
  assert(fixture.final_evaluator_calls == 0);
  assert(fixture.semantic_operation_calls == 0);
  assert(!PrepareActivityPlanningApplicationGlueV1(
      configured, fixture.Request("activity_hunt")));
  assert(PrepareActivityPlanningApplicationGlueV1(
      configured, fixture.Request(kActivityPlanningSnapshotP0ActivityKeyV1)));
  assert(!PrepareActivityPlanningApplicationGlueV1(
      configured, fixture.Request(kActivityPlanningSnapshotP0ActivityKeyV1)));
  assert(configured.prepared_request.activity_key ==
         kActivityPlanningSnapshotP0ActivityKeyV1);
}

void TestOnePausedFeastExecutesThroughScopedOperations() {
  Fixture fixture{};
  ActivityPlanningApplicationGlueStateV1 state{};
  assert(
      ConfigureActivityPlanningApplicationGlueV1(state, Environment(fixture)));
  std::string mutable_key{kActivityPlanningSnapshotP0ActivityKeyV1};
  assert(PrepareActivityPlanningApplicationGlueV1(
      state, fixture.Request(mutable_key)));
  mutable_key.assign("activity_hunt");
  ActivityPlanningSnapshotPrivateV1 result{};
  bool available = false;
  assert(
      !ReadActivityPlanningApplicationGlueResultV1(state, result, available));
  assert(ExecuteActivityPlanningApplicationGlueV1(state));
  assert(ReadActivityPlanningApplicationGlueResultV1(state, result, available));
  assert(available);
  assert(result.status == ActivityPlanningSnapshotStatusV1::available);
  assert(ActivityPlanningFixedTextViewV1(result.activity_key) ==
         kActivityPlanningSnapshotP0ActivityKeyV1);
  assert(result.owner_character_id == fixture.frame.owner_character_id);
  assert(result.can_plan_final.state == ActivityPlanningFieldStateV1::known &&
         result.can_plan_final.value);
  assert(result.candidates.count == 1);
  assert(result.configured_cost.count == 1);
  assert(result.readiness.action_inputs_ready);
  assert(!result.readiness.raw_pointer_fields_persisted);
  assert(fixture.final_evaluator_calls == 2);
  assert(fixture.semantic_operation_calls == 6);
  const auto diagnostics =
      ReadActivityPlanningApplicationGlueDiagnosticsV1(state);
  assert(diagnostics.installed && diagnostics.request_prepared &&
         diagnostics.result_ready && diagnostics.result_available &&
         !diagnostics.execution_active &&
         diagnostics.failure == ActivityPlanningApplicationGlueFailureV1::none);
  assert(!state.binder.container_active.load());
  assert(state.binder.active_token == 0);
  assert(!ExecuteActivityPlanningApplicationGlueV1(state));
}

void TestApplicationMainAndPauseAreRequiredBeforeOperations() {
  Fixture wrong_thread{};
  wrong_thread.frame.application_main_thread = false;
  ActivityPlanningApplicationGlueStateV1 thread_state{};
  assert(ConfigureActivityPlanningApplicationGlueV1(thread_state,
                                                    Environment(wrong_thread)));
  assert(PrepareActivityPlanningApplicationGlueV1(
      thread_state,
      wrong_thread.Request(kActivityPlanningSnapshotP0ActivityKeyV1)));
  assert(!ExecuteActivityPlanningApplicationGlueV1(thread_state));
  assert(wrong_thread.final_evaluator_calls == 0);
  assert(wrong_thread.semantic_operation_calls == 0);
  assert(
      ReadActivityPlanningApplicationGlueDiagnosticsV1(thread_state).failure ==
      ActivityPlanningApplicationGlueFailureV1::requires_application_main);

  Fixture running{};
  running.frame.paused = false;
  ActivityPlanningApplicationGlueStateV1 pause_state{};
  assert(ConfigureActivityPlanningApplicationGlueV1(pause_state,
                                                    Environment(running)));
  assert(PrepareActivityPlanningApplicationGlueV1(
      pause_state, running.Request(kActivityPlanningSnapshotP0ActivityKeyV1)));
  assert(!ExecuteActivityPlanningApplicationGlueV1(pause_state));
  assert(running.final_evaluator_calls == 0);
  assert(running.semantic_operation_calls == 0);
  assert(
      ReadActivityPlanningApplicationGlueDiagnosticsV1(pause_state).failure ==
      ActivityPlanningApplicationGlueFailureV1::requires_paused);
}

void TestScopedOperationsRejectObserverBypass() {
  Fixture fixture{};
  ActivityPlanningApplicationGlueStateV1 state{};
  assert(
      ConfigureActivityPlanningApplicationGlueV1(state, Environment(fixture)));
  assert(PrepareActivityPlanningApplicationGlueV1(
      state, fixture.Request(kActivityPlanningSnapshotP0ActivityKeyV1)));
  ActivityPlanningSnapshotPrivateV1 bypass_result{};
  assert(!ReadActivityPlanningSnapshotPrivateObserverV1(
      state.observer_environment, state.prepared_request, bypass_result));
  assert(fixture.final_evaluator_calls == 0);
  assert(fixture.semantic_operation_calls == 0);
  assert(ReadActivityPlanningApplicationGlueDiagnosticsV1(state).failure ==
         ActivityPlanningApplicationGlueFailureV1::operation_outside_scope);
  assert(ExecuteActivityPlanningApplicationGlueV1(state));
}

void TestTypedNativeFailuresRemainResults() {
  Fixture fixture{};
  fixture.fail_semantics = true;
  ActivityPlanningApplicationGlueStateV1 state{};
  assert(
      ConfigureActivityPlanningApplicationGlueV1(state, Environment(fixture)));
  assert(PrepareActivityPlanningApplicationGlueV1(
      state, fixture.Request(kActivityPlanningSnapshotP0ActivityKeyV1)));
  assert(ExecuteActivityPlanningApplicationGlueV1(state));
  ActivityPlanningSnapshotPrivateV1 result{};
  bool available = true;
  assert(ReadActivityPlanningApplicationGlueResultV1(state, result, available));
  assert(!available);
  assert(result.status == ActivityPlanningSnapshotStatusV1::unavailable);
  assert(result.unavailable_reason ==
         ActivityPlanningSnapshotFailureV1::provider_failed);
  const auto diagnostics =
      ReadActivityPlanningApplicationGlueDiagnosticsV1(state);
  assert(diagnostics.failure ==
         ActivityPlanningApplicationGlueFailureV1::observer_unavailable);
  assert(diagnostics.binder_failure ==
         ActivityPlanningNativeBinderFailureV1::semantic_read_failed);
}

void TestKnownFalseFinalEvaluatorIsPreserved() {
  Fixture fixture{};
  fixture.can_plan = false;
  ActivityPlanningApplicationGlueStateV1 state{};
  assert(
      ConfigureActivityPlanningApplicationGlueV1(state, Environment(fixture)));
  assert(PrepareActivityPlanningApplicationGlueV1(
      state, fixture.Request(kActivityPlanningSnapshotP0ActivityKeyV1)));
  assert(ExecuteActivityPlanningApplicationGlueV1(state));
  ActivityPlanningSnapshotPrivateV1 result{};
  bool available = false;
  assert(ReadActivityPlanningApplicationGlueResultV1(state, result, available));
  assert(available && !result.can_plan_final.value);
  assert(ActivityPlanningFixedTextViewV1(result.failure_display_key.value) ==
         "activity_feast_can_plan_failure");
}

void TestFailureVocabulary() {
  assert(
      ActivityPlanningApplicationGlueFailureKeyV1(
          ActivityPlanningApplicationGlueFailureV1::operation_outside_scope) ==
      "operation_outside_scope");
}

} // namespace

int main() {
  TestConfigurationAndRequestGates();
  TestOnePausedFeastExecutesThroughScopedOperations();
  TestApplicationMainAndPauseAreRequiredBeforeOperations();
  TestScopedOperationsRejectObserverBypass();
  TestTypedNativeFailuresRemainResults();
  TestKnownFalseFinalEvaluatorIsPreserved();
  TestFailureVocabulary();
  return 0;
}
