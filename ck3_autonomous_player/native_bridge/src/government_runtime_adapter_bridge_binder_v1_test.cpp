#include "xar_bridge/government_runtime_adapter_bridge_binder_v1.hpp"

#include <windows.h>

#include <cstdint>
#include <iostream>
#include <limits>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace {

namespace observer = xar::bridge::private_observer;
namespace game = xar::game;
using BindingEnvironment =
    observer::GovernmentRuntimeAdapterBridgeBindingEnvironmentV1;
using BindingFailure = observer::GovernmentRuntimeAdapterBridgeBindingFailureV1;
using BindingState = observer::GovernmentRuntimeAdapterBridgeBindingStateV1;
using Operation = observer::GovernmentRuntimeAdapterPrivateOperationV1;
using Sample = observer::GovernmentRuntimeAdapterCollectorSampleV1;
using SourceAccess = observer::GovernmentRuntimeAdapterSourceAccessV1;
using SourceFailure = observer::GovernmentRuntimeAdapterSourceFailureV1;
using SourceResult = observer::GovernmentRuntimeAdapterSourceResultV1;
using SourceStatus = observer::GovernmentRuntimeAdapterSourceStatusV1;

constexpr std::uintptr_t kModuleBase = 0x0000000140000000ULL;
constexpr std::uint64_t kRevision = 701;
constexpr std::int32_t kDateRaw = 1'220'410;

struct FixtureContext {
  std::vector<Sample> samples;
  std::size_t next_sample = 0;
  std::optional<std::size_t> fail_capture;
};

bool CaptureFixture(void *opaque, Sample &output) noexcept {
  auto *context = static_cast<FixtureContext *>(opaque);
  if (context == nullptr ||
      (context->fail_capture.has_value() &&
       context->next_sample == context->fail_capture.value()) ||
      context->next_sample >= context->samples.size()) {
    output = {};
    return false;
  }
  try {
    output = context->samples[context->next_sample++];
    return true;
  } catch (...) {
    output = {};
    return false;
  }
}

bool DummyCampaignCapture(void *, game::CampaignRootFrameV1 &) noexcept {
  return false;
}

bool DummyFeatureCapture(void *,
                         game::LoadedFeatureManifestFrameV1 &) noexcept {
  return false;
}

bool DummyIsMainThread(void *) noexcept { return true; }

bool DummyReadMemory(void *, const void *, void *, std::size_t) noexcept {
  return false;
}

Sample AvailableSample() {
  Sample sample{};
  sample.paused = true;
  sample.campaign_lifecycle_identity = 0xCA'11;
  sample.feature_lifecycle_identity = 0xFE'A7;
  sample.government_object_identity_available = true;
  sample.government_object_identity = 0x60'01;
  sample.script_dlc_layout_identity_available = true;
  sample.script_dlc_bucket_base_identity = 0xD1'C0;
  sample.script_dlc_bucket_mask_identity = 7;
  sample.script_dlc_maximum_spill_identity = 2;

  auto &campaign = sample.campaign_root;
  campaign.status = game::CampaignRootContextStatusV1::available;
  campaign.snapshot_revision = kRevision;
  campaign.date_raw = kDateRaw;
  campaign.player_character_id = 29'829;
  campaign.government = game::CampaignRootGovernmentV1{
      "feudal_government",
      {"government_uses_domain_limit", "government_is_feudal"},
      2};
  campaign.readiness.player_identity_ready = true;
  campaign.readiness.government_ready = true;
  campaign.readiness.same_frame_ready = true;

  auto &manifest = sample.loaded_features;
  manifest.status = game::LoadedFeatureManifestStatusV1::available;
  manifest.snapshot_revision = kRevision;
  manifest.date_raw = kDateRaw;
  const auto keys = observer::GovernmentRuntimeAdapterExpectedFeatureKeysV1();
  manifest.effective_feature_flags.status =
      game::LoadedFeatureComponentStatusV1::available;
  manifest.effective_feature_flags.native_count =
      static_cast<std::int32_t>(keys.size());
  manifest.effective_feature_flags.items.reserve(keys.size());
  for (std::size_t index = 0; index < keys.size(); ++index) {
    const auto key = keys[index];
    const bool enabled = key == "roads_to_power" || key == "admin_gov";
    manifest.effective_feature_flags.items.push_back(
        {static_cast<std::int32_t>(index),
         static_cast<std::uint32_t>(1'000 + index), std::string(key), enabled});
  }
  manifest.script_dlc_keys.status =
      game::LoadedFeatureComponentStatusV1::available;
  manifest.script_dlc_keys.enumerated_count = 2;
  manifest.script_dlc_keys.keys = {"A Royal Court", "Roads to Power"};
  manifest.readiness.effective_feature_flags_ready = true;
  manifest.readiness.script_dlc_keys_ready = true;
  manifest.readiness.entitlements_ready = false;
  manifest.readiness.same_frame_ready = true;
  manifest.readiness.actionable_ready = true;
  return sample;
}

BindingEnvironment FixtureBinding(FixtureContext &fixture) {
  BindingEnvironment environment{};
  environment.binding_enabled = true;
  environment.exact_build_admitted = true;
  environment.admitted_game_version =
      observer::kGovernmentRuntimeAdapterBridgeBinderV1GameVersion;
  environment.admitted_executable_sha256 =
      observer::kGovernmentRuntimeAdapterBridgeBinderV1ExecutableSha256;
  environment.module_base = kModuleBase;
  environment.offline_fixture = true;
  environment.fixture_context = &fixture;
  environment.fixture_capture = &CaptureFixture;
  return environment;
}

xar::ck3_11906::MainThreadExecutionStampV1 ValidStamp() {
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 37;
  stamp.thread_id = GetCurrentThreadId();
  stamp.tls_initialized_flag_address = 0x1000;
  stamp.tls_initialized = 1;
  stamp.tls_context = 0x2000;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = 0x3000;
  stamp.game_state = 0xCA'11;
  stamp.date_raw = kDateRaw;
  stamp.paused = true;
  return stamp;
}

struct BoundFixture {
  FixtureContext fixture;
  BindingState binding;
  SourceAccess source_access;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox;

  BoundFixture() : fixture{{AvailableSample(), AvailableSample()}} {
    if (!observer::BindGovernmentRuntimeAdapterBridgeV1(
            FixtureBinding(fixture), binding, source_access)) {
      binding.attached = false;
    }
  }
};

void ArmExactMailboxSlot(
    BoundFixture &bound, Operation &operation,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp,
    std::uint64_t sequence = 41) {
  operation.ticket.sequence = sequence;
  bound.mailbox.state.store(
      xar::ck3_11906::MainThreadQueryMailboxStateV1::executing,
      std::memory_order_release);
  bound.mailbox.stop_requested.store(false, std::memory_order_release);
  bound.mailbox.failure_flags.store(0, std::memory_order_release);
  bound.mailbox.published_sequence.store(sequence, std::memory_order_release);
  bound.mailbox.owner_thread_id.store(stamp.thread_id,
                                      std::memory_order_release);
  bound.mailbox.paused_owner_verified_pump_epochs.store(
      xar::ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs,
      std::memory_order_release);
  bound.mailbox.executor =
      &observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1;
  bound.mailbox.executor_context = &operation;
}

bool TestBindingAdmission() {
  FixtureContext fixture{{AvailableSample(), AvailableSample()}};
  auto environment = FixtureBinding(fixture);
  BindingState state{};
  SourceAccess access{};

  environment.binding_enabled = false;
  if (observer::BindGovernmentRuntimeAdapterBridgeV1(environment, state,
                                                     access) ||
      state.last_failure != BindingFailure::binding_disabled) {
    return false;
  }
  environment = FixtureBinding(fixture);
  environment.admitted_executable_sha256 = "wrong";
  if (observer::BindGovernmentRuntimeAdapterBridgeV1(environment, state,
                                                     access) ||
      state.last_failure != BindingFailure::unsupported_build) {
    return false;
  }
  environment = FixtureBinding(fixture);
  environment.module_base = 0;
  if (observer::BindGovernmentRuntimeAdapterBridgeV1(environment, state,
                                                     access) ||
      state.last_failure != BindingFailure::module_unavailable) {
    return false;
  }
  environment = FixtureBinding(fixture);
  environment.fixture_capture = nullptr;
  if (observer::BindGovernmentRuntimeAdapterBridgeV1(environment, state,
                                                     access) ||
      state.last_failure != BindingFailure::fixture_override_incomplete) {
    return false;
  }
  environment = FixtureBinding(fixture);
  environment.offline_fixture = false;
  if (observer::BindGovernmentRuntimeAdapterBridgeV1(environment, state,
                                                     access) ||
      state.last_failure != BindingFailure::fixture_override_forbidden) {
    return false;
  }

  environment = FixtureBinding(fixture);
  environment.offline_fixture = false;
  environment.fixture_context = nullptr;
  environment.fixture_capture = nullptr;
  if (observer::BindGovernmentRuntimeAdapterBridgeV1(environment, state,
                                                     access) ||
      state.last_failure != BindingFailure::campaign_access_incomplete) {
    return false;
  }
  environment.campaign_access.capture_frame = &DummyCampaignCapture;
  environment.campaign_access.is_main_thread = &DummyIsMainThread;
  environment.campaign_access.read_memory = &DummyReadMemory;
  if (observer::BindGovernmentRuntimeAdapterBridgeV1(environment, state,
                                                     access) ||
      state.last_failure != BindingFailure::feature_access_incomplete) {
    return false;
  }
  environment.feature_access.capture_frame = &DummyFeatureCapture;
  environment.feature_access.is_main_thread = &DummyIsMainThread;
  environment.feature_access.read_memory = &DummyReadMemory;
  if (!observer::BindGovernmentRuntimeAdapterBridgeV1(environment, state,
                                                      access) ||
      !state.attached || !access.exact_build_admitted) {
    return false;
  }
  SourceAccess untouched{};
  if (observer::BindGovernmentRuntimeAdapterBridgeV1(environment, state,
                                                     untouched) ||
      state.last_failure != BindingFailure::binding_already_attached ||
      !state.attached || untouched.context != nullptr) {
    return false;
  }
  return true;
}

bool TestAvailablePrivateOperation() {
  BoundFixture bound;
  if (!bound.binding.attached) {
    return false;
  }
  SourceResult direct{};
  observer::ReadGovernmentRuntimeAdapterSourceV1(bound.source_access, direct);
  if (direct.failure != SourceFailure::requires_application_main) {
    return false;
  }

  Operation operation{};
  if (!observer::PrepareGovernmentRuntimeAdapterPrivateOperationV1(
          bound.binding, bound.mailbox, kRevision, operation) ||
      observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1(
          &operation, ValidStamp())) {
    return false;
  }
  const auto stamp = ValidStamp();
  ArmExactMailboxSlot(bound, operation, stamp);
  if (!observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1(&operation,
                                                                   stamp)) {
    return false;
  }
  const bool available =
      operation.completed && operation.executed && operation.prepared &&
      operation.executor_invocations == 1 &&
      operation.result.status == SourceStatus::available &&
      operation.result.failure == SourceFailure::none &&
      operation.result.first_snapshot_revision == kRevision &&
      operation.result.second_snapshot_revision == kRevision &&
      operation.result.input.effective_government_stable_key ==
          "feudal_government" &&
      operation.result.semantic_result.adapter.requirements_met &&
      !bound.binding.execution_active && bound.binding.expected_revision == 0 &&
      bound.fixture.next_sample == 2 &&
      bound.binding.last_failure == BindingFailure::none;
  if (!available ||
      observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1(
          &operation, ValidStamp()) ||
      operation.executor_invocations != 1 ||
      bound.binding.last_failure != BindingFailure::execution_stamp_invalid) {
    return false;
  }
  return true;
}

bool TestTypedSourceFailures() {
  {
    BoundFixture bound;
    ++bound.fixture.samples[1].feature_lifecycle_identity;
    Operation operation{};
    if (!observer::PrepareGovernmentRuntimeAdapterPrivateOperationV1(
            bound.binding, bound.mailbox, kRevision, operation)) {
      return false;
    }
    const auto stamp = ValidStamp();
    ArmExactMailboxSlot(bound, operation, stamp);
    if (!observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1(&operation,
                                                                     stamp) ||
        operation.result.failure != SourceFailure::collector_lifecycle_drift) {
      return false;
    }
  }
  {
    BoundFixture bound;
    ++bound.fixture.samples[1].government_object_identity;
    Operation operation{};
    if (!observer::PrepareGovernmentRuntimeAdapterPrivateOperationV1(
            bound.binding, bound.mailbox, kRevision, operation)) {
      return false;
    }
    const auto stamp = ValidStamp();
    ArmExactMailboxSlot(bound, operation, stamp);
    if (!observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1(&operation,
                                                                     stamp) ||
        operation.result.failure !=
            SourceFailure::government_object_identity_drift) {
      return false;
    }
  }
  {
    BoundFixture bound;
    ++bound.fixture.samples[1].script_dlc_bucket_mask_identity;
    Operation operation{};
    if (!observer::PrepareGovernmentRuntimeAdapterPrivateOperationV1(
            bound.binding, bound.mailbox, kRevision, operation)) {
      return false;
    }
    const auto stamp = ValidStamp();
    ArmExactMailboxSlot(bound, operation, stamp);
    if (!observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1(&operation,
                                                                     stamp) ||
        operation.result.failure !=
            SourceFailure::script_dlc_layout_identity_drift) {
      return false;
    }
  }
  {
    BoundFixture bound;
    ++bound.fixture.samples[0].campaign_root.snapshot_revision;
    Operation operation{};
    if (!observer::PrepareGovernmentRuntimeAdapterPrivateOperationV1(
            bound.binding, bound.mailbox, kRevision, operation)) {
      return false;
    }
    const auto stamp = ValidStamp();
    ArmExactMailboxSlot(bound, operation, stamp);
    if (!observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1(&operation,
                                                                     stamp) ||
        operation.result.failure != SourceFailure::first_capture_failed ||
        bound.fixture.next_sample != 1) {
      return false;
    }
  }
  {
    BoundFixture bound;
    bound.fixture.fail_capture = 1;
    Operation operation{};
    if (!observer::PrepareGovernmentRuntimeAdapterPrivateOperationV1(
            bound.binding, bound.mailbox, kRevision, operation)) {
      return false;
    }
    const auto stamp = ValidStamp();
    ArmExactMailboxSlot(bound, operation, stamp);
    if (!observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1(&operation,
                                                                     stamp) ||
        operation.result.failure != SourceFailure::second_capture_failed) {
      return false;
    }
  }
  return true;
}

bool TestStampAndOperationGuards() {
  {
    BoundFixture bound;
    Operation operation{};
    auto stamp = ValidStamp();
    stamp.paused = false;
    if (!observer::PrepareGovernmentRuntimeAdapterPrivateOperationV1(
            bound.binding, bound.mailbox, kRevision, operation)) {
      return false;
    }
    ArmExactMailboxSlot(bound, operation, ValidStamp());
    if (observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1(&operation,
                                                                    stamp) ||
        operation.executed || operation.completed ||
        bound.binding.last_failure != BindingFailure::execution_stamp_invalid) {
      return false;
    }
  }
  {
    BoundFixture bound;
    Operation operation{};
    auto stamp = ValidStamp();
    stamp.thread_id =
        stamp.thread_id == std::numeric_limits<std::uint32_t>::max()
            ? stamp.thread_id - 1
            : stamp.thread_id + 1;
    if (!observer::PrepareGovernmentRuntimeAdapterPrivateOperationV1(
            bound.binding, bound.mailbox, kRevision, operation)) {
      return false;
    }
    ArmExactMailboxSlot(bound, operation, ValidStamp());
    if (observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1(&operation,
                                                                    stamp) ||
        operation.executed || operation.completed ||
        bound.binding.last_failure != BindingFailure::execution_stamp_invalid) {
      return false;
    }
  }
  {
    BoundFixture bound;
    Operation operation{};
    if (observer::PrepareGovernmentRuntimeAdapterPrivateOperationV1(
            bound.binding, bound.mailbox, 0, operation) ||
        operation.prepared ||
        bound.binding.last_failure != BindingFailure::operation_not_prepared) {
      return false;
    }
  }
  {
    BoundFixture bound;
    Operation operation{};
    if (!observer::PrepareGovernmentRuntimeAdapterPrivateOperationV1(
            bound.binding, bound.mailbox, kRevision, operation) ||
        observer::PrepareGovernmentRuntimeAdapterPrivateOperationV1(
            bound.binding, bound.mailbox, kRevision, operation) ||
        !operation.prepared || operation.binding != &bound.binding ||
        operation.mailbox != &bound.mailbox ||
        bound.binding.last_failure != BindingFailure::operation_not_prepared) {
      return false;
    }
  }
  return !observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1(
      nullptr, ValidStamp());
}

template <typename Mutate> bool MailboxMutationRejected(Mutate mutate) {
  BoundFixture bound;
  Operation operation{};
  const auto stamp = ValidStamp();
  if (!observer::PrepareGovernmentRuntimeAdapterPrivateOperationV1(
          bound.binding, bound.mailbox, kRevision, operation)) {
    return false;
  }
  ArmExactMailboxSlot(bound, operation, stamp);
  mutate(bound, operation, stamp);
  return !observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1(
             &operation, stamp) &&
         !operation.executed && !operation.completed &&
         operation.executor_invocations == 0 &&
         bound.fixture.next_sample == 0 &&
         bound.binding.last_failure == BindingFailure::execution_stamp_invalid;
}

bool TestExactMailboxIdentityGuards() {
  return MailboxMutationRejected(
             [](BoundFixture &bound, Operation &, const auto &) {
               bound.mailbox.state.store(
                   xar::ck3_11906::MainThreadQueryMailboxStateV1::queued,
                   std::memory_order_release);
             }) &&
         MailboxMutationRejected(
             [](BoundFixture &bound, Operation &, const auto &) {
               bound.mailbox.published_sequence.fetch_add(
                   1, std::memory_order_acq_rel);
             }) &&
         MailboxMutationRejected([](BoundFixture &bound, Operation &,
                                    const auto &) {
           bound.mailbox.owner_thread_id.fetch_add(1,
                                                   std::memory_order_acq_rel);
         }) &&
         MailboxMutationRejected([](BoundFixture &bound, Operation &,
                                    const auto &) {
           bound.mailbox.paused_owner_verified_pump_epochs.store(
               xar::ck3_11906::
                       kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs -
                   1,
               std::memory_order_release);
         }) &&
         MailboxMutationRejected(
             [](BoundFixture &bound, Operation &, const auto &) {
               bound.mailbox.executor = nullptr;
             }) &&
         MailboxMutationRejected(
             [](BoundFixture &bound, Operation &, const auto &) {
               bound.mailbox.executor_context = nullptr;
             }) &&
         MailboxMutationRejected(
             [](BoundFixture &bound, Operation &, const auto &) {
               bound.mailbox.failure_flags.store(1, std::memory_order_release);
             }) &&
         MailboxMutationRejected([](BoundFixture &bound, Operation &,
                                    const auto &) {
           bound.mailbox.stop_requested.store(true, std::memory_order_release);
         });
}

bool TestFailureKeys() {
  return observer::GovernmentRuntimeAdapterBridgeBindingFailureKeyV1(
             BindingFailure::none) == "none" &&
         observer::GovernmentRuntimeAdapterBridgeBindingFailureKeyV1(
             BindingFailure::binding_already_attached) ==
             "binding_already_attached" &&
         observer::GovernmentRuntimeAdapterBridgeBindingFailureKeyV1(
             BindingFailure::execution_stamp_invalid) ==
             "execution_stamp_invalid" &&
         observer::GovernmentRuntimeAdapterBridgeBindingFailureKeyV1(
             static_cast<BindingFailure>(999)) == "unknown";
}

} // namespace

int main() {
  const bool green =
      TestBindingAdmission() && TestAvailablePrivateOperation() &&
      TestTypedSourceFailures() && TestStampAndOperationGuards() &&
      TestExactMailboxIdentityGuards() && TestFailureKeys();
  if (!green) {
    std::cerr << "government-runtime-adapter-bridge-binder-v1: RED\n";
    return 1;
  }
  std::cout << "government-runtime-adapter-bridge-binder-v1: GREEN\n";
  return 0;
}
