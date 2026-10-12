// Link this offline fixture with the actual Gathering Runtime producer TU.
// Only its external parent/clock and declared memory inputs are synthetic.
#include "xar_bridge/army_gathering_due_natural_stage_12004_serializer.hpp"

#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>

namespace gathering_sampling_fixture {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kBase = 0x10000000, kPrimary = 0x10000;
constexpr std::uintptr_t kState = 0x20000, kArmy = 0x30000;
constexpr std::uintptr_t kCombat = 0x40000, kQueue = 0x50000;
constexpr std::uint32_t kArmyId = 0xA1000001U;
constexpr std::uintptr_t kRawReturn = 0xFEDCBA9876543210ULL;
constexpr std::string_view kSyntheticSourcePin =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

std::map<std::uintptr_t, unsigned char> bytes;
ArmyNaturalPhaseScope12004 parent;
ArmyGatheringDueNaturalBindings12004 bindings;
ArmyGatheringResearchSamplingState12004 inside_before, inside_disabled;
ArmyGatheringResearchSamplingState12004 inside_repeat_enable, inside_enable_attempt, after_nested;
ArmyGatheringDueNaturalStage12004 nested_result;
unsigned assertions = 0, cases = 0, original_calls = 0;
unsigned reads = 0, copies = 0, masks = 0, events = 0, depth = 0;
std::uint64_t sequence = 1;
std::uintptr_t expected_primary = kPrimary;
bool permit_violation = false, arguments_changed = false;
bool denied_day_read = false, denied_subject_id = false, busy_sample_was_null = false;
enum class Action { ordinary, enable_at_original, disable_at_original, nested_disable };
Action action = Action::ordinary;

void Require(bool condition, std::string_view message) {
  ++assertions;
  if (!condition) throw std::runtime_error(std::string(message));
}

void CheckPermit() noexcept {
  const auto state = ReadArmyGatheringResearchSamplingState12004();
  if (!state.available || !state.busy || state.active_captures == 0)
    permit_violation = true;
}

template<class T> void Put(std::uintptr_t address, T value) {
  const auto *data = reinterpret_cast<const unsigned char *>(&value);
  for (std::size_t i = 0; i < sizeof(value); ++i) bytes[address + i] = data[i];
}
void Zero(std::uintptr_t address, std::size_t size) {
  for (std::size_t i = 0; i < size; ++i) bytes[address + i] = 0;
}
void List(std::uintptr_t address, std::uintptr_t data, std::int32_t count) {
  Put(address, data); Put(address + 8, count); Put(address + 12, count);
}

bool Read(void *, std::uintptr_t address, void *output, std::size_t size) noexcept {
  ++reads;
  CheckPermit();
  if ((denied_day_read && address == kState + 0x9C) ||
      (denied_subject_id && address == kArmy + 0x10)) return false;
  auto *data = static_cast<unsigned char *>(output);
  for (std::size_t i = 0; i < size; ++i) {
    const auto found = bytes.find(address + i);
    if (found == bytes.end()) return false;
    data[i] = found->second;
  }
  return true;
}

void SetupInputs() {
  bytes.clear();
  original_calls = reads = copies = masks = events = depth = 0;
  sequence = 1;
  expected_primary = kPrimary;
  permit_violation = arguments_changed = denied_day_read = denied_subject_id = busy_sample_was_null = false;
  action = Action::ordinary;
  inside_before = inside_disabled = inside_repeat_enable = inside_enable_attempt = after_nested = {};
  nested_result = {};
  Zero(kPrimary, 0x200); Zero(kState, 0xD0); Zero(kArmy, 0x200); Zero(kCombat, 0x20);
  Put(kState + 8, std::uint64_t{24});
  Put(kState + 0x9C, std::uint32_t{7}); Put(kState + 0xC0, std::uint8_t{0x80});
  List(kPrimary + 0x158, kQueue, 1); Put(kQueue, kArmyId);
  List(kPrimary + 0x30, 0, 0); List(kPrimary + 0x50, kQueue, 1);
  Put(kBase + 0x5D1DE48, std::uintptr_t{0}); Put(kBase + 0x5D1DE50, kArmy);
  Put(kBase + 0x5D1DE70, std::uintptr_t{0}); Put(kBase + 0x5D1DE18, kCombat);
  Put(kArmy + 0x10, kArmyId); Put(kArmy + 0x14, std::uint32_t{0x41726D79});
  Put(kArmy + 0x128, std::uint32_t{0xFFFFFFFFU});
  Put(kCombat + 8, std::uint32_t{0xFFFFFFFFU});
  parent = {};
  parent.observed = true; parent.phase = ArmyNaturalPhaseKind12004::post_date;
  parent.actual_entry_rva = kArmyNaturalPostDateRva12004;
  parent.primary_manager_identity = kPrimary; parent.secondary_manager_identity = kPrimary + 8;
  parent.game_state_identity = kState;
  parent.entry_event.clock_identity = 42; parent.entry_event.sequence = 1;
  parent.entry_event.thread_id = 7;
  bindings = BindArmyGatheringDueNaturalStage12004(kBase, kSyntheticSourcePin, nullptr, Read);
  Require(bindings.exact_build_enabled, "declared synthetic binding must be admitted");
}

std::uintptr_t __fastcall Original(void *actual_primary, const void *actual_date) {
  ++original_calls; ++depth;
  if (reinterpret_cast<std::uintptr_t>(actual_primary) != expected_primary ||
      reinterpret_cast<std::uintptr_t>(actual_date) != kState + 8)
    arguments_changed = true;
  if (action == Action::enable_at_original) {
    inside_before = ReadArmyGatheringResearchSamplingState12004();
    inside_enable_attempt = SetArmyGatheringResearchSampling12004(true);
  } else if (action == Action::disable_at_original) {
    inside_before = ReadArmyGatheringResearchSamplingState12004();
    inside_repeat_enable = SetArmyGatheringResearchSampling12004(true);
    busy_sample_was_null = !ReadSampledArmyGatheringDueNaturalForArmy12004(kArmyId);
    inside_disabled = SetArmyGatheringResearchSampling12004(false);
    inside_enable_attempt = SetArmyGatheringResearchSampling12004(true);
  } else if (action == Action::nested_disable) {
    action = Action::disable_at_original;
    nested_result = InvokeArmyGatheringDueNatural12004(
        bindings, Original, actual_primary, actual_date,
        kArmyGatheringDueNaturalReturnRva12004, std::uint8_t{0});
    after_nested = ReadArmyGatheringResearchSamplingState12004();
    action = Action::nested_disable;
  }
  --depth;
  return kRawReturn;
}

ArmyGatheringDueNaturalStage12004 Invoke(
    std::uintptr_t pc = kArmyGatheringDueNaturalReturnRva12004) {
  return InvokeArmyGatheringDueNatural12004(
      bindings, Original, reinterpret_cast<void *>(kPrimary),
      reinterpret_cast<const void *>(kState + 8), pc, std::uint8_t{0});
}

void ReturnedOnce(const ArmyGatheringDueNaturalStage12004 &result, unsigned calls = 1) {
  Require(original_calls == calls && result.original_called && result.original_returned,
          "intercepted original must run exactly once per invocation");
  Require(result.raw_return_bits == kRawReturn && !arguments_changed,
          "original arguments and full opaque return bits must survive");
  Require(!permit_violation, "capture touched metadata or declared memory before its permit");
}

void Begin() {
  const auto off = SetArmyGatheringResearchSampling12004(false);
  Require(off.available && !off.enabled && !off.busy && off.clear_completed,
          "case reset must be a completed idle disable");
  SetupInputs();
  const auto on = SetArmyGatheringResearchSampling12004(true);
  Require(on.available && on.enabled && !on.busy && !on.clear_completed &&
              on.retained_records == 0 && on.qualified_records == 0,
          "fresh enabled epoch must start without retained observations");
}

void DefaultOff() {
  ++cases;
  const auto initial = ReadArmyGatheringResearchSamplingState12004();
  Require(initial.available && !initial.enabled && !initial.busy && initial.clear_completed &&
              initial.epoch == 0 && initial.active_captures == 0 &&
              initial.retained_records == 0 && initial.qualified_records == 0,
          "fresh Runtime must start disabled with no evidence");
  SetupInputs();
  Require(!ReadSampledArmyGatheringDueNaturalForArmy12004(kArmyId),
          "off reader must report unavailable, not a fabricated empty observation");
  const auto result = Invoke();
  ReturnedOnce(result);
  Require(reads == 0 && copies == 0 && masks == 1 && events == 0 && !result.observed &&
              result.saved_mask_parent_observation_admitted == true,
          "off retains one qualified SavedMask observation and skips heavy capture");
  const auto after = ReadArmyGatheringResearchSamplingState12004();
  Require(!after.enabled && after.epoch == initial.epoch && after.retained_records == 0 &&
              !ReadSampledArmyGatheringDueNaturalForArmy12004(kArmyId),
          "query and off invocation must not enable sampling");
}

void OffSavedMaskInvalidInputs() {
  for (unsigned invalid = 0; invalid != 4; ++invalid) {
    ++cases; SetupInputs();
    auto b = bindings;
    auto pc = kArmyGatheringDueNaturalReturnRva12004;
    std::optional<std::uint8_t> mask = std::uint8_t{0};
    if (invalid == 0) b = BindArmyGatheringDueNaturalStage12004(kBase, "unsupported", nullptr, Read);
    if (invalid == 1) ++pc;
    if (invalid == 2) mask.reset();
    if (invalid == 3) expected_primary = (std::numeric_limits<std::uintptr_t>::max)() - 7;
    const auto result = InvokeArmyGatheringDueNatural12004(b, Original,
        reinterpret_cast<void *>(expected_primary), reinterpret_cast<const void *>(kState + 8), pc, mask);
    ReturnedOnce(result);
    Require(masks == 0 && !result.saved_mask_parent_observation_admitted &&
                reads == 0 && copies == 0 && events == 0 && !result.observed,
            "invalid off input must not qualify SavedMask or heavy capture");
    Require(!ReadSampledArmyGatheringDueNaturalForArmy12004(kArmyId) &&
                ReadArmyGatheringResearchSamplingState12004().retained_records == 0,
            "invalid off invocation must not manufacture a sampled history");
  }
}

void AdmissionIsFixedAtEntry() {
  ++cases;
  SetupInputs(); action = Action::enable_at_original;
  const auto result = Invoke();
  ReturnedOnce(result);
  Require(!inside_before.enabled && inside_before.active_captures == 0 &&
              inside_enable_attempt.enabled && !inside_enable_attempt.busy,
          "explicit original callback may enable only the next capture");
  Require(reads == 0 && copies == 0 && masks == 1 && events == 0 && !result.observed &&
              result.saved_mask_parent_observation_admitted == true,
          "off-entry enable keeps the light observation without admitting heavy capture");
  const auto after = ReadArmyGatheringResearchSamplingState12004();
  Require(after.enabled && after.retained_records == 0 && after.qualified_records == 0 &&
              !ReadSampledArmyGatheringDueNaturalForArmy12004(kArmyId),
          "a newly enabled epoch still has no qualified sample");
}

void UnqualifiedHistoryRemainsUnknown() {
  ++cases; Begin();
  const auto before = ReadArmyGatheringResearchSamplingState12004();
  Require(!ReadSampledArmyGatheringDueNaturalForArmy12004(kArmyId), "enabled without a sample is unknown");
  const auto result = Invoke(kArmyGatheringDueNaturalReturnRva12004 + 1);
  ReturnedOnce(result);
  Require(!result.observed && !result.actual_boundary_admitted && reads == 0,
          "wrong literal return PC must not qualify a stage");
  const auto after = ReadArmyGatheringResearchSamplingState12004();
  Require(after.retained_records == 1 && after.qualified_records == 0 &&
              !ReadSampledArmyGatheringDueNaturalForArmy12004(kArmyId),
          "retaining an unqualified attempt must not manufacture observed absence");
  const auto repeated = SetArmyGatheringResearchSampling12004(true);
  Require(repeated.epoch == before.epoch && repeated.retained_records == after.retained_records,
          "repeated enable must preserve the current epoch and retained records");
}

void QualifiedCaptureAndSubjectUnknowns() {
  ++cases; Begin();
  const auto before = ReadArmyGatheringResearchSamplingState12004();
  const auto result = Invoke();
  ReturnedOnce(result);
  Require(result.observed && result.actual_boundary_admitted && result.actual_poststage_observed &&
              result.entry.all_declared_reads_complete && result.returned.all_declared_reads_complete,
          "owned fixture must exercise a complete actual Runtime capture");
  Require(reads > 0 && copies > 0 && masks > 0 && events > 0,
          "enabled Runtime must execute its real capture path");
  const auto state = ReadArmyGatheringResearchSamplingState12004();
  Require(state.retained_records == 1 && state.qualified_records == 1 && !state.busy,
          "completed qualified capture must be recorded once");
  const auto sampled = ReadSampledArmyGatheringDueNaturalForArmy12004(kArmyId);
  Require(sampled && sampled->size() == 1 && sampled->front().raw_return_bits == kRawReturn,
          "sampled reader must return the actual retained capture");
  Require(!ReadSampledArmyGatheringDueNaturalForArmy12004(kArmyId + 1),
          "no observed full-ID match must remain unknown, not an empty subject history");
  Require(!ReadSampledArmyGatheringDueNaturalForArmy12004(0xFFFFFFFFU), "invalid Army identity remains unknown");
  const auto repeated = SetArmyGatheringResearchSampling12004(true);
  Require(repeated.epoch == before.epoch && repeated.qualified_records == 1,
          "repeated enable must not erase qualified evidence");
}

void PartialFieldsStayPartial() {
  ++cases; Begin(); denied_day_read = true;
  const auto result = Invoke();
  ReturnedOnce(result);
  Require(result.observed && !result.entry.all_declared_reads_complete &&
              !result.entry.absolute_day_raw && !result.entry.missing_fields.empty(),
          "denied declared reads must remain unavailable fields, never numeric zero");
  const auto sampled = ReadSampledArmyGatheringDueNaturalForArmy12004(kArmyId);
  Require(sampled && sampled->size() == 1 && !sampled->front().entry.absolute_day_raw,
          "a matched subject retains partial fields without upgrading complete-input readiness");
  Require(ReadArmyGatheringResearchSamplingState12004().qualified_records == 1,
          "qualified counter must use the same actual Runtime predicate");
}

void UnobservedSubjectIdentityRemainsUnknown() {
  ++cases; Begin(); denied_subject_id = true;
  const auto result = Invoke();
  ReturnedOnce(result);
  Require(result.observed && !result.entry.queued_armies.empty() &&
              !result.entry.queued_armies.front().receiver.selected_full_id,
          "unread subject identity must remain unavailable in the actual capture");
  Require(ReadArmyGatheringResearchSamplingState12004().qualified_records == 1 &&
              !ReadSampledArmyGatheringDueNaturalForArmy12004(kArmyId),
          "a qualified stage without subject identity must not fabricate empty subject history");
}

void DisableAnInflightCapture(bool nested) {
  ++cases; Begin();
  const auto seed = Invoke(); ReturnedOnce(seed);
  const auto old = ReadArmyGatheringResearchSamplingState12004();
  original_calls = 0;
  action = nested ? Action::nested_disable : Action::disable_at_original;
  const auto result = Invoke();
  ReturnedOnce(result, nested ? 2 : 1);
  Require(inside_before.enabled && inside_before.busy &&
              inside_before.active_captures == (nested ? 2U : 1U) && busy_sample_was_null,
          "inflight capture must be counted and unavailable to full sample reads");
  Require(inside_repeat_enable.available && inside_repeat_enable.enabled &&
              inside_repeat_enable.busy && inside_repeat_enable.epoch == old.epoch &&
              inside_repeat_enable.clear_completed == inside_before.clear_completed &&
              inside_repeat_enable.active_captures == inside_before.active_captures &&
              inside_repeat_enable.retained_records == old.retained_records,
          "already-enabled busy repeat must preserve epoch, captures and retained evidence");
  Require(!inside_disabled.enabled && inside_disabled.busy && !inside_disabled.clear_completed &&
              inside_disabled.epoch == old.epoch && inside_disabled.retained_records == old.retained_records,
          "disable inside original must return busy without self-waiting or claiming clear");
  Require(!inside_enable_attempt.enabled && inside_enable_attempt.busy &&
              inside_enable_attempt.epoch == old.epoch,
          "busy enable must not reopen a disabled epoch");
  if (nested) {
    Require(nested_result.original_called && nested_result.original_returned &&
                nested_result.raw_return_bits == kRawReturn &&
                after_nested.active_captures == 1 && !after_nested.enabled,
            "nested old capture must drain independently without changing native return");
  }
  const auto drained = ReadArmyGatheringResearchSamplingState12004();
  Require(!drained.enabled && !drained.busy && drained.active_captures == 0 &&
              !drained.clear_completed && drained.epoch == old.epoch &&
              drained.retained_records == old.retained_records &&
              drained.qualified_records == old.qualified_records,
          "old inflight return must not append after disable");
  Require(!ReadSampledArmyGatheringDueNaturalForArmy12004(kArmyId), "disabled retained history is unavailable");
  const auto cleared = SetArmyGatheringResearchSampling12004(false);
  Require(cleared.clear_completed && !cleared.busy && cleared.epoch == old.epoch + 1 &&
              cleared.retained_records == 0 && cleared.qualified_records == 0,
          "drained disable retry must clear and advance epoch exactly once");
  const auto again = SetArmyGatheringResearchSampling12004(false);
  Require(again.epoch == cleared.epoch && again.clear_completed, "repeated idle disable must be idempotent");
  ClearArmyGatheringDueNaturalJournal12004();
  Require(ReadArmyGatheringResearchSamplingState12004().epoch == cleared.epoch,
          "safe clear convenience must not advance a completed disable again");
}
} // namespace gathering_sampling_fixture

namespace xar::ck3_12004 {
// External parent and event seams supply declared fixture inputs only. Sampling,
// permit, capture, publication and sampled-reader logic stay in the actual TU.
ArmyNaturalPhaseScope12004 CopyActiveArmyNaturalPhaseScope12004() noexcept {
  ++gathering_sampling_fixture::copies;
  gathering_sampling_fixture::CheckPermit();
  return gathering_sampling_fixture::parent;
}
bool ObserveArmyNaturalPhaseSavedMask12004(std::uintptr_t secondary,
    std::uintptr_t pc, std::uint8_t value) noexcept {
  ++gathering_sampling_fixture::masks;
  // SavedMask is permitted lightweight provenance even when sampling is off.
  return secondary == gathering_sampling_fixture::kPrimary + 8 &&
      pc == kArmyGatheringDueNaturalReturnRva12004 && value == 0;
}
ArmyNaturalPhaseEvent12004 NextArmyNaturalPhaseEvent12004(void *) noexcept {
  ++gathering_sampling_fixture::events;
  gathering_sampling_fixture::CheckPermit();
  ArmyNaturalPhaseEvent12004 out;
  out.clock_identity = 42; out.sequence = ++gathering_sampling_fixture::sequence;
  out.thread_id = 7;
  return out;
}
} // namespace xar::ck3_12004

int main(int argc, char **argv) {
  try {
    using namespace gathering_sampling_fixture;
    const bool off67d = argc == 2 && std::string_view(argv[1]) == "--gathering-off-67d";
    Require(argc == 1 || off67d, "unknown focused fixture selection");
    if (off67d) {
      DefaultOff(); OffSavedMaskInvalidInputs(); AdmissionIsFixedAtEntry();
      SetArmyGatheringResearchSampling12004(false);
    } else {
      DefaultOff(); AdmissionIsFixedAtEntry(); UnqualifiedHistoryRemainsUnknown();
      QualifiedCaptureAndSubjectUnknowns(); PartialFieldsStayPartial();
      UnobservedSubjectIdentityRemainsUnknown();
      DisableAnInflightCapture(false); DisableAnInflightCapture(true);
    }
    const auto final = ReadArmyGatheringResearchSamplingState12004();
    Require(!final.enabled && !final.busy && final.clear_completed && final.retained_records == 0,
            "fixture must finish with drained disabled sampling");
    std::cout << "{\"status\":\"passed\",\"cases\":" << cases
              << ",\"assertions\":" << assertions
              << ",\"actual_runtime_tu\":true,\"synthetic_inputs\":true,\"live_ck3\":false}\n";
    return EXIT_SUCCESS;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return EXIT_FAILURE;
  }
}
