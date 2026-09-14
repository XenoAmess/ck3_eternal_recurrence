#include "xar_bridge/activity_planning_snapshot_v1_source_adapter.hpp"

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
#include <type_traits>

namespace {

using namespace xar::bridge;

constexpr std::uintptr_t kModuleBase = 0x140000000ULL;
constexpr std::array<std::uintptr_t, 2> kHostViews{0x71000000ULL,
                                                   0x71001000ULL};
constexpr std::array<std::uintptr_t, 2> kActivityTypes{0x72000000ULL,
                                                       0x72001000ULL};

ActivityPlanningSourceStringRefV1 Ref(std::string_view value) {
  return {reinterpret_cast<std::uintptr_t>(value.data()),
          static_cast<std::uint32_t>(value.size())};
}

struct Fixture {
  ActivityPlanningFrameIdentityV1 frame{91,   4567, 12345, true,
                                        true, true, true};
  std::string activity_key{"activity_feast"};
  std::array<std::string, 2> location_keys{"province_101", "province_202"};
  std::array<std::string, 2> resource_keys{"gold", "piety"};
  std::array<std::string, 2> option_keys{"activity_option_food_normal",
                                         "activity_option_drink_normal"};
  std::string host_intent{"reduce_stress_intent"};
  std::string guest_intent{"reduce_stress_intent"};
  std::string invite_rule{"activity_invite_rule_default"};
  std::string failure_key{"activity_feast_can_plan_failure"};
  std::string failure_text{"A feast is unavailable."};
  std::array<std::array<ActivityPlanningSourceLocationRowV1, 2>, 2> locations{};
  std::array<std::array<ActivityPlanningSourceCostRowV1, 2>, 2> costs{};
  std::array<std::array<ActivityPlanningSourceOptionRowV1, 2>, 2> options{};
  std::uintptr_t active_token = 0;
  ActivityPlanningSourceContainerViewV1 active_view{};
  std::uint32_t frame_reads = 0;
  std::uint32_t resolve_calls = 0;
  std::uint32_t definition_key_calls = 0;
  std::uint32_t can_plan_calls = 0;
  std::uint32_t open_calls = 0;
  std::uint32_t container_reads = 0;
  std::uint32_t release_calls = 0;
  bool can_plan = true;
  bool wrong_vtable = false;
  bool wrong_definition_key = false;
  bool fail_open = false;
  bool fail_release = false;
  bool drift_container_view = false;
  bool drift_second_sample = false;
  std::uint32_t drift_frame_at_read = 0;

  Fixture() { RefreshRows(); }

  void RefreshRows() {
    for (std::size_t set = 0; set < locations.size(); ++set) {
      locations[set][0] = {101, Ref(location_keys[0]), 150000, 1};
      locations[set][1] = {202, Ref(location_keys[1]), 50000, 0};
      costs[set][0] = {Ref(resource_keys[0]), 12500000};
      costs[set][1] = {Ref(resource_keys[1]), 250000};
      options[set][0] = {Ref(option_keys[0])};
      options[set][1] = {Ref(option_keys[1])};
    }
  }

  ActivityPlanningSnapshotRequestV1 Request() const {
    return {frame.snapshot_revision, frame.date_raw, frame.owner_character_id,
            kActivityPlanningSnapshotP0ActivityKeyV1};
  }
};

bool ReadFrame(void *context,
               ActivityPlanningFrameIdentityV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.frame_reads;
  if (fixture.drift_frame_at_read != 0 &&
      fixture.frame_reads == fixture.drift_frame_at_read) {
    ++fixture.frame.snapshot_revision;
  }
  output = fixture.frame;
  return true;
}

bool ReadMemory(void *context, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  const auto expected_vtable =
      kModuleBase + kActivityPlanningHostViewPrimaryVtableRvaV1;
  const auto expected_can_plan =
      kModuleBase + kActivityPlanningHostViewCanPlanRvaV1;
  for (std::size_t index = 0; index < kHostViews.size(); ++index) {
    if (address == kHostViews[index] && size == sizeof(std::uintptr_t)) {
      const std::uintptr_t value =
          fixture.wrong_vtable ? expected_vtable + 8 : expected_vtable;
      std::memcpy(output, &value, size);
      return true;
    }
    if (address ==
            kHostViews[index] + kActivityPlanningHostViewActivityTypeOffsetV1 &&
        size == sizeof(std::uintptr_t)) {
      std::memcpy(output, &kActivityTypes[index], size);
      return true;
    }
  }
  if (address ==
          expected_vtable + kActivityPlanningHostViewCanPlanVtableSlotV1 *
                                sizeof(std::uintptr_t) &&
      size == sizeof(std::uintptr_t)) {
    std::memcpy(output, &expected_can_plan, size);
    return true;
  }
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

bool ResolveHostView(void *context, std::int32_t owner_character_id,
                     std::string_view activity_key,
                     std::uintptr_t &host_view) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (owner_character_id != fixture.frame.owner_character_id ||
      activity_key != fixture.activity_key) {
    host_view = 0;
    return false;
  }
  host_view = kHostViews[fixture.resolve_calls % kHostViews.size()];
  ++fixture.resolve_calls;
  return true;
}

bool ReadDefinitionKey(void *context, std::uintptr_t activity_type,
                       ActivityPlanningSourceStringRefV1 &key) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  const auto expected =
      kActivityTypes[fixture.definition_key_calls % kActivityTypes.size()];
  ++fixture.definition_key_calls;
  if (activity_type != expected)
    return false;
  key = fixture.wrong_definition_key ? Ref("activity_tournament")
                                     : Ref(fixture.activity_key);
  return true;
}

bool InvokeFinalCanPlan(
    void *context, std::uintptr_t exact_entry_point, std::uintptr_t host_view,
    const ActivityPlanningSnapshotRequestV1 &request,
    ActivityPlanningSourceCanPlanResultV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  const auto expected_host =
      kHostViews[fixture.can_plan_calls % kHostViews.size()];
  ++fixture.can_plan_calls;
  if (exact_entry_point !=
          kModuleBase + kActivityPlanningHostViewCanPlanRvaV1 ||
      host_view != expected_host ||
      request.activity_key != fixture.activity_key) {
    return false;
  }
  output.value = fixture.can_plan ? 1 : 0;
  if (!fixture.can_plan) {
    output.failure_display_key = Ref(fixture.failure_key);
    output.failure_display_text = Ref(fixture.failure_text);
  }
  return true;
}

bool OpenSourceContainer(void *context, std::uintptr_t host_view,
                         std::uintptr_t activity_type,
                         const ActivityPlanningSnapshotRequestV1 &request,
                         std::uintptr_t &token) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (fixture.fail_open)
    return false;
  const auto set = fixture.open_calls % 2;
  if (host_view != kHostViews[set] || activity_type != kActivityTypes[set] ||
      request.activity_key != fixture.activity_key ||
      fixture.active_token != 0) {
    return false;
  }
  if (fixture.drift_second_sample && fixture.open_calls == 1) {
    fixture.locations[set][0].native_weight_q100000 += 1;
  }
  ++fixture.open_calls;
  token = 0x73000000ULL + fixture.open_calls;
  fixture.active_token = token;
  fixture.active_view = {};
  fixture.active_view.location_rows =
      reinterpret_cast<std::uintptr_t>(fixture.locations[set].data());
  fixture.active_view.location_count = 2;
  fixture.active_view.configured_cost_rows =
      reinterpret_cast<std::uintptr_t>(fixture.costs[set].data());
  fixture.active_view.configured_cost_count = 2;
  fixture.active_view.selected_option_rows =
      reinterpret_cast<std::uintptr_t>(fixture.options[set].data());
  fixture.active_view.selected_option_count = 2;
  fixture.active_view.host_intent_key = Ref(fixture.host_intent);
  fixture.active_view.guest_intent_key = Ref(fixture.guest_intent);
  fixture.active_view.invite_rule_key = Ref(fixture.invite_rule);
  fixture.active_view.shown = 1;
  fixture.active_view.can_start = 1;
  fixture.active_view.affordable = 1;
  fixture.active_view.cooldown_active = 0;
  fixture.active_view.cooldown_days_remaining = 0;
  return true;
}

bool ReadSourceContainer(
    void *context, std::uintptr_t token,
    ActivityPlanningSourceContainerViewV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (token != fixture.active_token)
    return false;
  ++fixture.container_reads;
  output = fixture.active_view;
  if (fixture.drift_container_view && (fixture.container_reads % 2) == 0) {
    output.selected_option_count = 1;
  }
  return true;
}

bool ReleaseSourceContainer(void *context, std::uintptr_t token) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.release_calls;
  if (token != fixture.active_token)
    return false;
  fixture.active_token = 0;
  fixture.active_view = {};
  return !fixture.fail_release;
}

ActivityPlanningSourceAdapterEnvironmentV1 SourceEnvironment(Fixture &fixture) {
  ActivityPlanningSourceAdapterEnvironmentV1 output{};
  output.exact_build_admitted = true;
  output.admitted_executable_sha256 =
      kActivityPlanningSourceAdapterExecutableSha256V1;
  output.module_base = kModuleBase;
  output.context = &fixture;
  output.read_frame = &ReadFrame;
  output.read_memory = &ReadMemory;
  output.resolve_host_view = &ResolveHostView;
  output.read_definition_key = &ReadDefinitionKey;
  output.invoke_final_can_plan = &InvokeFinalCanPlan;
  output.open_source_container = &OpenSourceContainer;
  output.read_source_container = &ReadSourceContainer;
  output.release_source_container = &ReleaseSourceContainer;
  return output;
}

struct Harness {
  Fixture fixture{};
  ActivityPlanningSourceAdapterStateV1 state{};
  ActivityPlanningSnapshotPrivateEnvironmentV1 observer{};

  Harness() {
    assert(ConfigureActivityPlanningSourceAdapterV1(
        state, SourceEnvironment(fixture), observer));
  }

  bool Read(ActivityPlanningSnapshotPrivateV1 &output) {
    return ReadActivityPlanningSnapshotPrivateObserverV1(
        observer, fixture.Request(), output);
  }
};

std::string_view View(const ActivityPlanningStableKeyV1 &value) {
  return ActivityPlanningFixedTextViewV1(value);
}

void TestAvailableCaptureUsesTwoFreshNativeSamples() {
  Harness harness{};
  ActivityPlanningSnapshotPrivateV1 output{};
  assert(harness.Read(output));
  assert(output.status == ActivityPlanningSnapshotStatusV1::available);
  assert(output.can_plan_source ==
         ActivityPlanningCanPlanSourceV1::host_view_final_can_plan);
  assert(output.can_plan_final.state == ActivityPlanningFieldStateV1::known);
  assert(output.can_plan_final.value);
  assert(output.failure_display_key.state ==
         ActivityPlanningFieldStateV1::unknown);
  assert(output.failure_display_key.unknown_reason ==
         ActivityPlanningUnknownReasonV1::not_applicable);
  assert(output.candidates.count == 2);
  assert(output.candidates.source ==
         ActivityPlanningCandidateSourceV1::native_legal_location_collection);
  assert(output.candidates.rows[0].location_id == 101);
  assert(View(output.candidates.rows[0].location_key) == "province_101");
  assert(output.candidates.rows[0].native_weight_q100000 == 150000);
  assert(output.selected_options.count == 2);
  assert(View(output.selected_options.keys[0]) ==
         "activity_option_food_normal");
  assert(View(output.host_intent_key.value) == "reduce_stress_intent");
  assert(View(output.guest_intent_key.value) == "reduce_stress_intent");
  assert(View(output.invite_rule_key.value) == "activity_invite_rule_default");
  assert(output.configured_cost.count == 2);
  assert(output.configured_cost.source ==
         ActivityPlanningConfiguredCostSourceV1::
             native_authoritative_configured_cost);
  assert(View(output.configured_cost.rows[0].resource_key) == "gold");
  assert(output.configured_cost.rows[0].amount_q100000 == 12500000);
  assert(output.readiness.action_inputs_ready);
  assert(!output.readiness.raw_pointer_fields_persisted);
  assert(harness.fixture.resolve_calls == 2);
  assert(harness.fixture.definition_key_calls == 2);
  assert(harness.fixture.can_plan_calls == 2);
  assert(harness.fixture.open_calls == 2);
  assert(harness.fixture.container_reads == 4);
  assert(harness.fixture.release_calls == 2);
  assert(harness.fixture.active_token == 0);
  assert(harness.state.captured.candidate_count == 0);
  assert(harness.state.projected_options[0].data() == nullptr);

  harness.fixture.location_keys[0].assign("destroyed___");
  harness.fixture.resource_keys[0].assign("dust");
  harness.fixture.option_keys[0].assign("destroyed_option____________");
  harness.fixture.host_intent.assign("destroyed_intent___");
  assert(View(output.candidates.rows[0].location_key) == "province_101");
  assert(View(output.configured_cost.rows[0].resource_key) == "gold");
  assert(View(output.selected_options.keys[0]) ==
         "activity_option_food_normal");
  assert(View(output.host_intent_key.value) == "reduce_stress_intent");
}

void TestBlockedCapturePreservesTypedFailure() {
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
  assert(output.readiness.final_can_plan_ready);
  assert(output.readiness.candidate_inputs_ready);
  assert(output.readiness.configured_cost_ready);
  assert(output.readiness.configuration_keys_ready);
  assert(!output.readiness.action_inputs_ready);
}

void TestRepeatedQueryNeverCachesNativeIdentity() {
  Harness harness{};
  ActivityPlanningSnapshotPrivateV1 first{};
  ActivityPlanningSnapshotPrivateV1 second{};
  assert(harness.Read(first));
  assert(harness.Read(second));
  assert(harness.fixture.resolve_calls == 4);
  assert(harness.fixture.definition_key_calls == 4);
  assert(harness.fixture.can_plan_calls == 4);
  assert(harness.fixture.open_calls == 4);
  assert(harness.fixture.release_calls == 4);
  assert(harness.fixture.active_token == 0);
  assert(View(first.activity_key) == View(second.activity_key));
}

void TestExactBuildAndHostViewAdmissionFailClosed() {
  Harness bad_hash{};
  bad_hash.state.environment.admitted_executable_sha256 = "bad";
  ActivityPlanningSnapshotPrivateV1 output{};
  assert(!bad_hash.Read(output));
  assert(output.unavailable_reason ==
         ActivityPlanningSnapshotFailureV1::provider_failed);
  assert(ReadActivityPlanningSourceAdapterFailureV1(bad_hash.state) ==
         ActivityPlanningSourceAdapterFailureV1::exact_build_not_admitted);

  Harness bad_vtable{};
  bad_vtable.fixture.wrong_vtable = true;
  assert(!bad_vtable.Read(output));
  assert(ReadActivityPlanningSourceAdapterFailureV1(bad_vtable.state) ==
         ActivityPlanningSourceAdapterFailureV1::host_view_identity_mismatch);

  Harness bad_key{};
  bad_key.fixture.wrong_definition_key = true;
  assert(!bad_key.Read(output));
  assert(ReadActivityPlanningSourceAdapterFailureV1(bad_key.state) ==
         ActivityPlanningSourceAdapterFailureV1::activity_key_mismatch);
}

void TestContainerAndSampleDriftRemainRed() {
  Harness container_drift{};
  container_drift.fixture.drift_container_view = true;
  ActivityPlanningSnapshotPrivateV1 output{};
  assert(!container_drift.Read(output));
  assert(ReadActivityPlanningSourceAdapterFailureV1(container_drift.state) ==
         ActivityPlanningSourceAdapterFailureV1::source_container_drift);
  assert(container_drift.fixture.release_calls == 1);
  assert(container_drift.fixture.active_token == 0);

  Harness sample_drift{};
  sample_drift.fixture.drift_second_sample = true;
  assert(!sample_drift.Read(output));
  assert(ReadActivityPlanningSourceAdapterFailureV1(sample_drift.state) ==
         ActivityPlanningSourceAdapterFailureV1::source_sample_drift);
  assert(sample_drift.fixture.release_calls == 2);
  assert(sample_drift.fixture.active_token == 0);

  Harness frame_drift{};
  frame_drift.fixture.drift_frame_at_read = 5;
  assert(!frame_drift.Read(output));
  assert(ReadActivityPlanningSourceAdapterFailureV1(frame_drift.state) ==
         ActivityPlanningSourceAdapterFailureV1::frame_mismatch);
  assert(frame_drift.fixture.active_token == 0);
}

void TestContainerFailuresReleaseAndRecoverSession() {
  Harness open_failure{};
  open_failure.fixture.fail_open = true;
  ActivityPlanningSnapshotPrivateV1 output{};
  assert(!open_failure.Read(output));
  assert(ReadActivityPlanningSourceAdapterFailureV1(open_failure.state) ==
         ActivityPlanningSourceAdapterFailureV1::source_container_unavailable);
  assert(!open_failure.state.session_active.load());

  Harness row_failure{};
  row_failure.fixture.locations[0][0].location_key = {};
  assert(!row_failure.Read(output));
  assert(ReadActivityPlanningSourceAdapterFailureV1(row_failure.state) ==
         ActivityPlanningSourceAdapterFailureV1::source_text_unavailable);
  assert(row_failure.fixture.release_calls == 1);
  assert(row_failure.fixture.active_token == 0);
  assert(!row_failure.state.session_active.load());

  Harness release_failure{};
  release_failure.fixture.fail_release = true;
  assert(!release_failure.Read(output));
  assert(
      ReadActivityPlanningSourceAdapterFailureV1(release_failure.state) ==
      ActivityPlanningSourceAdapterFailureV1::source_container_release_failed);
  assert(release_failure.fixture.release_calls == 1);
  assert(release_failure.fixture.active_token == 0);
  assert(!release_failure.state.session_active.load());
}

void TestFailureKeysAreStable() {
  assert(ActivityPlanningSourceAdapterFailureKeyV1(
             ActivityPlanningSourceAdapterFailureV1::source_sample_drift) ==
         "source_sample_drift");
  assert(ActivityPlanningSourceAdapterFailureKeyV1(
             ActivityPlanningSourceAdapterFailureV1::
                 source_container_release_failed) ==
         "source_container_release_failed");
}

} // namespace

int main() {
  static_assert(
      std::is_trivially_copyable_v<ActivityPlanningSourceLocationRowV1>);
  static_assert(
      std::is_trivially_copyable_v<ActivityPlanningSourceContainerViewV1>);
  TestAvailableCaptureUsesTwoFreshNativeSamples();
  TestBlockedCapturePreservesTypedFailure();
  TestRepeatedQueryNeverCachesNativeIdentity();
  TestExactBuildAndHostViewAdmissionFailClosed();
  TestContainerAndSampleDriftRemainRed();
  TestContainerFailuresReleaseAndRecoverSession();
  TestFailureKeysAreStable();
  return 0;
}
