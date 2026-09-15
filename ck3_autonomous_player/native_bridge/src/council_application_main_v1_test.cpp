#include "xar_bridge/council_application_main_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

namespace bridge = xar::bridge;
namespace native = xar::ck3_11906;
namespace game = xar::game;

constexpr std::uintptr_t kModuleBase = 0x0000000140000000ULL;
constexpr std::int32_t kOwnerId = 29829;
constexpr std::int32_t kTaskId = 7159;
constexpr std::int32_t kIncumbentId = 33433;
constexpr std::int32_t kCandidateId = 30784;
constexpr std::uintptr_t kActiveTaskStorageSlotRva = 0x570C778;
constexpr std::uintptr_t kActiveTaskFallbackSlotRva = 0x570C6D8;

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

template <typename Value, std::size_t Size>
void Put(std::array<std::byte, Size> &storage, std::size_t offset,
         const Value &value) {
  Require(offset + sizeof(value) <= storage.size(), "fixture write overflow");
  std::memcpy(storage.data() + offset, &value, sizeof(value));
}

template <std::size_t Size>
void CopyToken(std::array<char, Size> &output, std::string_view value) {
  Require(value.size() < output.size(), "fixture token overflow");
  std::memcpy(output.data(), value.data(), value.size());
  output[value.size()] = '\0';
}

struct Fixture {
  native::CouncilCompositionStewardCandidatesFrameV1 frame{};
  std::array<std::byte, 0x300> owner{};
  std::array<std::byte, 0x280> land_state{};
  std::array<std::byte, 0x80> task{};
  std::array<std::byte, 0x80> task_type{};
  std::array<std::byte, 0x80> position_type{};
  std::array<std::byte, 0x40> task_storage{};
  std::array<std::byte, 0x20> fallback_task{};
  std::vector<std::byte> task_slots;
  std::array<std::int32_t, 1> active_task_ids{kTaskId};
  std::array<std::byte, 0x100> incumbent{};
  std::array<std::array<std::byte, 0x100>, 3> candidates{};
  std::array<std::int32_t, 3> candidate_ids{33888, kCandidateId, 33437};
  std::array<std::int32_t, 3> candidate_stewardship{14, 27, 19};
  std::array<std::uintptr_t, 3> candidate_pointers{};
  native::CouncilAssignCouncillorNativeSubmitAdapterV1 submit_adapter{};
  bool gate_available = true;
  bool candidate_already_councillor = false;
  bool candidate_is_guest = false;
  bool pending_character_interaction = false;
  bool incumbent_can_be_fired = true;
  std::uint32_t source_captures = 0;
  std::uint32_t initializes = 0;
  std::uint32_t producer_calls = 0;
  std::uint32_t releases = 0;
  std::uint32_t gate_calls = 0;
  std::uint32_t helper_calls = 0;

  Fixture()
      : task_slots((static_cast<std::size_t>(kTaskId) + 1U) * 0x10) {
    SetSnapshot("council23:7", 7, 11, 53178264);
    frame.paused = true;
    frame.map_ready = true;
    frame.has_played_character = true;
    frame.played_character_alive = true;
    frame.played_character_id = kOwnerId;
    frame.played_character = reinterpret_cast<std::uintptr_t>(owner.data());

    Put(owner, 0x18, kOwnerId);
    void *land = land_state.data();
    Put(owner, 0x1B8, land);
    void *ids = active_task_ids.data();
    Put(land_state, 0x230, ids);
    Put(land_state, 0x23C, std::int32_t{1});

    Put(task, 0x10, kTaskId);
    void *type = task_type.data();
    Put(task, 0x18, type);
    Put(task, native::kCouncilCompositionActiveTaskIncumbentIdOffsetV1,
        kIncumbentId);
    Put(task, 0x3C, kOwnerId);
    void *position = position_type.data();
    Put(task_type, 0x38, position);

    void *slot_data = task_slots.data();
    Put(task_storage, 0x20, slot_data);
    Put(task_storage, 0x2C, kTaskId + 1);
    void *task_pointer = task.data();
    std::memcpy(task_slots.data() + static_cast<std::size_t>(kTaskId) * 0x10 +
                    0x08,
                &task_pointer, sizeof(task_pointer));

    Put(incumbent, native::kCouncilCompositionCharacterIdentityOffsetV1,
        kIncumbentId);
    Put(incumbent, native::kCouncilCompositionCharacterStewardshipOffsetV1,
        std::int32_t{12});
    for (std::size_t index = 0; index < candidates.size(); ++index) {
      Put(candidates[index], native::kCouncilCompositionCharacterIdentityOffsetV1,
          candidate_ids[index]);
      Put(candidates[index],
          native::kCouncilCompositionCharacterStewardshipOffsetV1,
          candidate_stewardship[index]);
      candidate_pointers[index] =
          reinterpret_cast<std::uintptr_t>(candidates[index].data());
    }

    submit_adapter.environment.exact_build_admitted = true;
    submit_adapter.environment.admitted_executable_sha256 =
        native::kCouncilAssignCouncillorExecutableSha256V1;
    submit_adapter.environment.native_command_abi_certified = true;
    submit_adapter.environment.private_candidate_admitted = true;
    submit_adapter.environment.offline_fixture = true;
    submit_adapter.override_context = this;
  }

  void SetSnapshot(std::string_view id, std::uint64_t public_revision,
                   std::uint64_t native_revision, std::int32_t date_raw) {
    frame.snapshot_id = {};
    CopyToken(frame.snapshot_id, id);
    frame.public_revision = public_revision;
    frame.native_revision = native_revision;
    frame.date_raw = date_raw;
  }

  void SetIncumbent(std::int32_t character_id) {
    Put(task, native::kCouncilCompositionActiveTaskIncumbentIdOffsetV1,
        character_id);
  }
};

bool CaptureSource(
    void *opaque,
    const native::CouncilCompositionStewardCandidatesRequestV1 &,
    const native::MainThreadExecutionStampV1 &,
    native::CouncilCompositionStewardCandidatesFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.source_captures;
  output = fixture.frame;
  return true;
}

bool ReadMemory(void *opaque, const void *address, void *output,
                std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  const auto numeric = reinterpret_cast<std::uintptr_t>(address);
  if (numeric == kModuleBase + kActiveTaskStorageSlotRva) {
    void *storage = fixture.task_storage.data();
    if (size != sizeof(storage)) return false;
    std::memcpy(output, &storage, size);
    return true;
  }
  if (numeric == kModuleBase + kActiveTaskFallbackSlotRva) {
    void *fallback = fixture.fallback_task.data();
    if (size != sizeof(fallback)) return false;
    std::memcpy(output, &fallback, size);
    return true;
  }
  if (address == nullptr || output == nullptr || size == 0) return false;
  std::memcpy(output, address, size);
  return true;
}

bool ReadStableKey(void *opaque, const void *native_string, char *output,
                   std::size_t output_capacity) noexcept {
  const auto &fixture = *static_cast<Fixture *>(opaque);
  const auto key = native::kCouncilCompositionStewardCandidatesReaderPositionKeyV1;
  if (native_string != fixture.position_type.data() + 0x18 ||
      output == nullptr || key.size() >= output_capacity) {
    return false;
  }
  std::memcpy(output, key.data(), key.size());
  output[key.size()] = '\0';
  return true;
}

bool ResolveCharacter(void *opaque, std::uintptr_t module_base,
                      std::int32_t full_id,
                      std::uintptr_t &character) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  character = 0;
  if (module_base != kModuleBase) return false;
  if (full_id == kOwnerId) {
    character = reinterpret_cast<std::uintptr_t>(fixture.owner.data());
    return true;
  }
  if (full_id == kIncumbentId) {
    character = reinterpret_cast<std::uintptr_t>(fixture.incumbent.data());
    return true;
  }
  for (std::size_t index = 0; index < fixture.candidate_ids.size(); ++index) {
    if (fixture.candidate_ids[index] == full_id) {
      character = fixture.candidate_pointers[index];
      return true;
    }
  }
  return false;
}

bool InitializeVector(
    void *opaque, std::uintptr_t module_base, void *allocator_storage,
    std::size_t allocator_storage_size,
    native::CouncilCompositionStewardCandidatesBindingNativeVectorV1
        &vector) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.initializes;
  if (module_base != kModuleBase || allocator_storage == nullptr ||
      allocator_storage_size !=
          native::kCouncilCompositionStewardInlineAllocatorSizeV1) {
    return false;
  }
  vector = {};
  vector.data_address = reinterpret_cast<std::uintptr_t>(allocator_storage) + 8;
  vector.capacity = native::kCouncilCompositionStewardInlineCandidateCapacityV1;
  vector.allocator = allocator_storage;
  return true;
}

bool InvokeProducer(
    void *opaque, std::uintptr_t module_base, std::uintptr_t owner_character,
    std::uintptr_t active_task, bool gui_eligibility_mode,
    native::CouncilCompositionStewardCandidatesBindingNativeVectorV1
        &vector) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.producer_calls;
  if (module_base != kModuleBase ||
      owner_character != reinterpret_cast<std::uintptr_t>(fixture.owner.data()) ||
      active_task != reinterpret_cast<std::uintptr_t>(fixture.task.data()) ||
      !gui_eligibility_mode || vector.allocator == nullptr) {
    return false;
  }
  vector.data_address =
      reinterpret_cast<std::uintptr_t>(fixture.candidate_pointers.data());
  vector.count = static_cast<std::int32_t>(fixture.candidate_pointers.size());
  return true;
}

bool ReleaseAllocation(void *opaque, std::uintptr_t module_base,
                       void *allocator, std::uintptr_t data_address,
                       std::size_t element_size) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.releases;
  return module_base == kModuleBase && allocator != nullptr &&
      data_address != 0 && element_size == sizeof(std::uintptr_t);
}

bool EvaluateGates(
    void *opaque, const game::CouncilAssignCouncillorFrameV1 &frame,
    std::int32_t candidate_character_id,
    game::CouncilAssignCouncillorFinalLegalityV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.gate_calls;
  if (!fixture.gate_available || candidate_character_id != kCandidateId) {
    return false;
  }
  output = {};
  output.available = true;
  output.candidate_already_councillor = fixture.candidate_already_councillor;
  output.candidate_is_guest = fixture.candidate_is_guest;
  output.pending_character_interaction =
      fixture.pending_character_interaction;
  output.incumbent_fireability_evaluated = frame.has_incumbent;
  output.incumbent_can_be_fired = fixture.incumbent_can_be_fired;
  output.native_reason_key = fixture.incumbent_can_be_fired
      ? ""
      : "incumbent_cannot_be_fired";
  return true;
}

bool EvaluateReadOnlyGateRows(
    void *opaque, const game::CouncilAssignCouncillorFrameV1 &frame,
    std::int32_t candidate_character_id,
    game::CouncilAssignCouncillorFinalLegalityV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.gate_calls;
  if (!fixture.gate_available && candidate_character_id == 33437)
    return false;
  if (std::find(fixture.candidate_ids.begin(), fixture.candidate_ids.end(),
                candidate_character_id) == fixture.candidate_ids.end())
    return false;
  output = {};
  output.available = true;
  output.candidate_already_councillor = candidate_character_id == 33888;
  output.candidate_is_guest = candidate_character_id == 33437;
  output.pending_character_interaction = false;
  output.incumbent_fireability_evaluated = frame.has_incumbent;
  output.incumbent_can_be_fired = true;
  return true;
}

void InvokeHelper(void *opaque, std::int32_t candidate_character_id,
                  std::int32_t active_task_id) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (candidate_character_id == kCandidateId && active_task_id == kTaskId) {
    ++fixture.helper_calls;
  }
}

native::CouncilCompositionStewardCandidatesBindingEnvironmentV1 Binding(
    Fixture &fixture) {
  native::CouncilCompositionStewardCandidatesBindingEnvironmentV1 output{};
  output.binding_enabled = true;
  output.exact_build_admitted = true;
  output.admitted_executable_sha256 =
      native::kCouncilCompositionStewardCandidatesReaderExecutableSha256V1;
  output.offline_fixture = true;
  output.module_base = kModuleBase;
  output.operation_context = &fixture;
  output.operations = {&ReadMemory, &ReadStableKey, &ResolveCharacter,
                       &InitializeVector, &InvokeProducer,
                       &ReleaseAllocation};
  return output;
}

bridge::CouncilApplicationMainConfigurationV1 Configuration(
    Fixture &fixture, bool action_runtime = true,
    bool include_gates = true, bool gate_query = false) {
  fixture.submit_adapter.helper_override = &InvokeHelper;
  bridge::CouncilApplicationMainConfigurationV1 output{};
  output.enabled = true;
  output.query_runtime_enabled = true;
  output.final_gate_query_runtime_enabled = gate_query;
  output.action_runtime_enabled = action_runtime;
  output.exact_build_admitted = true;
  output.private_candidate_admitted = true;
  output.native_command_abi_certified = true;
  output.offline_fixture = true;
  output.module_base = kModuleBase;
  output.admitted_executable_sha256 =
      native::kCouncilCompositionStewardCandidatesReaderExecutableSha256V1;
  output.binding = Binding(fixture);
  output.source_context = &fixture;
  output.capture_source_frame = &CaptureSource;
  output.action_gate_context = &fixture;
  output.evaluate_action_gates = include_gates
      ? (gate_query ? &EvaluateReadOnlyGateRows : &EvaluateGates)
      : nullptr;
  output.submit_adapter = &fixture.submit_adapter;
  return output;
}

native::CouncilCompositionStewardCandidatesRequestV1 QueryRequest(
    const Fixture &fixture) {
  native::CouncilCompositionStewardCandidatesRequestV1 output{};
  const auto end = std::find(fixture.frame.snapshot_id.begin(),
                             fixture.frame.snapshot_id.end(), '\0');
  output.expected_snapshot_id = {fixture.frame.snapshot_id.data(),
                                 static_cast<std::size_t>(
                                     end - fixture.frame.snapshot_id.begin())};
  output.expected_public_revision = fixture.frame.public_revision;
  output.expected_native_revision = fixture.frame.native_revision;
  output.expected_date_raw = fixture.frame.date_raw;
  output.expected_owner_character_id = kOwnerId;
  return output;
}

native::MainThreadExecutionStampV1 Stamp(const Fixture &fixture) {
  native::MainThreadExecutionStampV1 output{};
  output.pump_epoch = 10;
  output.thread_id = GetCurrentThreadId();
  output.tls_initialized_flag_address = 0x1000;
  output.tls_initialized = 1;
  output.tls_context = 0x2000;
  output.tls_main_thread_marker = 1;
  output.jomini_state = 0x3000;
  output.game_state = 0x4000;
  output.date_raw = fixture.frame.date_raw;
  output.paused = true;
  return output;
}

void PrepareMailbox(native::MainThreadQueryMailboxV1 &mailbox) {
  mailbox.state.store(native::MainThreadQueryMailboxStateV1::idle);
  mailbox.failure_flags.store(0);
  mailbox.stop_requested.store(false);
  mailbox.executor_submission_enabled = true;
  mailbox.module_base = kModuleBase;
  mailbox.permitted_executor_unquadragintary =
      &bridge::ExecuteCouncilApplicationMainV1;
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      native::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
}

struct Harness {
  explicit Harness(Fixture &fixture, bool action_runtime = true,
                   bool include_gates = true,
                   bool gate_query = false) {
    PrepareMailbox(mailbox);
    Require(bridge::ConfigureCouncilApplicationMainV1(
                mailbox,
                Configuration(fixture, action_runtime, include_gates,
                              gate_query), state,
                context),
            "Council application-main configuration failed");
  }

  native::MainThreadQueryMailboxV1 mailbox{};
  bridge::CouncilApplicationMainStateV1 state{};
  bridge::CouncilApplicationMainContextV1 context{};
};

void ExecuteAndComplete(Harness &harness, const Fixture &fixture,
                        bool expected = true) {
  Require(harness.mailbox.state.load() ==
              native::MainThreadQueryMailboxStateV1::queued,
          "mailbox request not queued");
  harness.mailbox.state.store(native::MainThreadQueryMailboxStateV1::executing);
  const bool actual = bridge::ExecuteCouncilApplicationMainV1(
      &harness.context, Stamp(fixture));
  Require(actual == expected, "executor returned unexpected result");
  harness.mailbox.executor_succeeded = actual;
  harness.mailbox.completed_sequence.store(harness.context.ticket.sequence);
  harness.mailbox.state.store(
      actual ? native::MainThreadQueryMailboxStateV1::completed
             : native::MainThreadQueryMailboxStateV1::executor_failed);
}

void Reclaim(Harness &harness) {
  Require(bridge::ReclaimCouncilApplicationMainV1(harness.context) ==
              native::MainThreadQueryReclaimResultV1::reclaimed,
          "mailbox request not reclaimed");
}

void Queue(Harness &harness, const Fixture &fixture) {
  Require(bridge::TryQueueCouncilApplicationMainV1(harness.context) ==
              native::MainThreadQuerySubmitResultV1::submitted,
          "mailbox request not submitted");
  ExecuteAndComplete(harness, fixture);
}

void TestQueryTransactionAndSerializer() {
  Fixture fixture;
  Harness harness(fixture);
  Require(bridge::PrepareCouncilApplicationMainQueryV1(
              harness.context, QueryRequest(fixture)),
          "query preparation failed");
  Queue(harness, fixture);
  Require(harness.context.completion ==
              bridge::CouncilApplicationMainCompletionV1::query_available &&
              harness.context.query_result.readiness.ready &&
              harness.context.query_result.candidate_count == 3 &&
              harness.context.query_result.incumbent_character_id ==
                  kIncumbentId &&
              fixture.initializes == 1 && fixture.producer_calls == 1 &&
              fixture.releases == 1,
          "private-read/release/enrichment/public query chain failed");
  const auto wire = bridge::SerializeCouncilApplicationMainResultEnvelopeV1(
      harness.context, "pipe-query-1");
  Require(wire.find("\"request_id\":\"pipe-query-1\"") !=
                  std::string::npos &&
              wire.find("\"step\":\"query-council-composition-candidates-v1\"") !=
                  std::string::npos &&
              wire.find("\"council_composition_candidates\":") !=
                  std::string::npos &&
              wire.find("\"backend_id\":\"native-headless\"") !=
                  std::string::npos,
          "query serializer omitted the production normalizer envelope");
  Reclaim(harness);
}

void TestIncompleteNativeGatesStayUnadvertised() {
  Fixture fixture;
  Harness harness(fixture, true, false);
  Require(bridge::CouncilApplicationMainQueryRuntimeReadyV1(harness.state) &&
              !bridge::CouncilApplicationMainActionRuntimeReadyV1(
                  harness.state) &&
              !bridge::kCouncilApplicationMainAdvertisedByDefaultV1,
          "incomplete action gates became runtime-ready or advertised");
  game::CouncilAssignCouncillorActionRequestV1 request{};
  Require(!bridge::PrepareCouncilApplicationMainSubmitV1(harness.context,
                                                          request) &&
              fixture.helper_calls == 0,
          "incomplete action gates reached native submit");
}

void TestReadOnlyFinalGatesCannotSubmitOrPublishPartialRows() {
  Fixture fixture;
  Harness harness(fixture, false, true, true);
  Require(harness.state.final_gate_query_runtime_ready &&
              !bridge::CouncilApplicationMainActionRuntimeReadyV1(
                  harness.state) &&
              !bridge::kCouncilApplicationMainAdvertisedByDefaultV1,
          "read-only gate candidate admitted an action or public capability");
  Require(bridge::PrepareCouncilApplicationMainFinalGateQueryV1(
              harness.context, QueryRequest(fixture)),
          "read-only final-gate query preparation failed");
  Queue(harness, fixture);
  const auto rows_begin = harness.context.final_gate_rows.begin();
  const auto rows_end = rows_begin + harness.context.final_gate_row_count;
  const bool saw_councillor = std::any_of(
      rows_begin, rows_end, [](const auto &row) {
        return row.candidate_character_id == 33888 &&
               row.already_councillor;
      });
  const bool saw_guest = std::any_of(
      rows_begin, rows_end, [](const auto &row) {
        return row.candidate_character_id == 33437 && row.guest;
      });
  Require(harness.context.completion ==
              bridge::CouncilApplicationMainCompletionV1::query_available &&
              harness.context.final_gate_row_count == 3 &&
              saw_councillor && saw_guest &&
              fixture.gate_calls == 3 && fixture.helper_calls == 0 &&
              fixture.submit_adapter.invocation_count == 0 &&
              !harness.state.has_pending_ack,
          "gate-only executor did not evaluate all rows without a helper");
  const auto wire = bridge::SerializeCouncilApplicationMainResultEnvelopeV1(
      harness.context, "pipe-gates-1");
  Require(wire.find("\"private\":true,\"advertised\":false") !=
                  std::string::npos &&
              wire.find("\"candidate_is_guest\":true") !=
                  std::string::npos &&
              wire.find("\"native_helper_invocations_delta\":0") !=
                  std::string::npos,
          "read-only gate envelope omitted evaluated status or no-submit proof");
  Reclaim(harness);

  fixture.gate_available = false;
  Require(bridge::PrepareCouncilApplicationMainFinalGateQueryV1(
              harness.context, QueryRequest(fixture)),
          "unavailable gate query preparation failed");
  Queue(harness, fixture);
  Require(harness.context.completion ==
              bridge::CouncilApplicationMainCompletionV1::query_unavailable &&
              harness.context.final_gate_row_count == 0 &&
              fixture.helper_calls == 0 && !harness.state.has_pending_ack,
          "unavailable final native row published partial gates or submitted");
  Reclaim(harness);
}

game::CouncilAssignCouncillorActionRequestV1 ActionRequest(
    const Fixture &fixture, std::string_view request_id) {
  game::CouncilAssignCouncillorActionRequestV1 output{};
  const auto candidates_request = QueryRequest(fixture);
  output.request_id.assign(request_id);
  output.position_key.assign(native::kCouncilAssignCouncillorPositionKeyV1);
  output.expected_snapshot_id.assign(candidates_request.expected_snapshot_id);
  output.expected_public_revision = candidates_request.expected_public_revision;
  output.expected_native_revision = candidates_request.expected_native_revision;
  output.expected_date_raw = candidates_request.expected_date_raw;
  output.expected_owner_character_id = kOwnerId;
  output.candidate_character_id = kCandidateId;
  output.expected_has_incumbent = true;
  output.expected_incumbent_character_id = kIncumbentId;
  return output;
}

void TestSubmitAndFreshReceipt() {
  Fixture fixture;
  Harness harness(fixture);
  Require(bridge::CouncilApplicationMainActionRuntimeReadyV1(harness.state),
          "complete offline action fixture was not ready");
  Require(bridge::PrepareCouncilApplicationMainSubmitV1(
              harness.context, ActionRequest(fixture, "action-23-1")),
          "submit preparation failed");
  Queue(harness, fixture);
  const auto submit_sequence = harness.context.ticket.sequence;
  Require(harness.context.completion ==
              bridge::CouncilApplicationMainCompletionV1::
                  submitted_verification_pending &&
              harness.context.action_ack.native_helper_invoked &&
              !harness.context.action_ack.queue_acceptance_observed &&
              harness.context.action_ack.verification_pending &&
              harness.state.has_pending_ack && fixture.gate_calls == 1 &&
              fixture.helper_calls == 1 &&
              fixture.submit_adapter.invocation_count == 1,
          "submit did not preserve helper-only ACK semantics");
  const auto ack_wire = bridge::SerializeCouncilApplicationMainResultEnvelopeV1(
      harness.context, "pipe-submit-1");
  Require(ack_wire.find("\"request_id\":\"pipe-submit-1\"") !=
                  std::string::npos &&
              ack_wire.find("\"action_request_id\":\"action-23-1\"") !=
                  std::string::npos &&
              ack_wire.find("\"queue_acceptance_observed\":false") !=
                  std::string::npos,
          "ACK serializer conflated protocol and semantic request IDs");
  Reclaim(harness);

  fixture.SetSnapshot("council23:8", 8, 12, 53178265);
  fixture.SetIncumbent(kCandidateId);
  Require(bridge::PrepareCouncilApplicationMainReceiptV1(
              harness.context, QueryRequest(fixture)),
          "receipt preparation failed");
  Queue(harness, fixture);
  Require(harness.context.ticket.sequence > submit_sequence &&
              harness.context.completion ==
                  bridge::CouncilApplicationMainCompletionV1::receipt_applied &&
              harness.context.action_receipt.postcondition_verified &&
              harness.context.action_receipt.incumbent_character_id ==
                  kCandidateId &&
              !harness.state.has_pending_ack && fixture.helper_calls == 1,
          "fresh paused receipt did not confirm candidate as incumbent");
  const auto receipt_wire =
      bridge::SerializeCouncilApplicationMainResultEnvelopeV1(
          harness.context, "pipe-receipt-1");
  Require(receipt_wire.find("\"request_id\":\"pipe-receipt-1\"") !=
                  std::string::npos &&
              receipt_wire.find("\"action_request_id\":\"action-23-1\"") !=
                  std::string::npos &&
              receipt_wire.find("\"status\":\"applied\"") !=
                  std::string::npos,
          "receipt serializer omitted correlation or applied status");
  Reclaim(harness);
}

void TestReplacementFireabilityBlocksHelper() {
  Fixture fixture;
  fixture.incumbent_can_be_fired = false;
  Harness harness(fixture);
  Require(bridge::PrepareCouncilApplicationMainSubmitV1(
              harness.context, ActionRequest(fixture, "action-23-denied")),
          "denied replacement preparation failed");
  Queue(harness, fixture);
  Require(harness.context.completion ==
              bridge::CouncilApplicationMainCompletionV1::action_rejected &&
              harness.context.action_ack.failure ==
                  game::CouncilAssignCouncillorFailureV1::
                      incumbent_cannot_be_replaced &&
              fixture.gate_calls == 1 && fixture.helper_calls == 0,
          "replacement fireability denial reached native helper");
  Reclaim(harness);
}

void TestMailboxIdentityMismatchIsInfrastructureRed() {
  Fixture fixture;
  Harness harness(fixture);
  Require(bridge::PrepareCouncilApplicationMainQueryV1(
              harness.context, QueryRequest(fixture)),
          "identity query preparation failed");
  Require(bridge::TryQueueCouncilApplicationMainV1(harness.context) ==
              native::MainThreadQuerySubmitResultV1::submitted,
          "identity query did not queue");
  harness.mailbox.executor_context = nullptr;
  ExecuteAndComplete(harness, fixture, false);
  Require(harness.context.completion ==
              bridge::CouncilApplicationMainCompletionV1::
                  infrastructure_red &&
              harness.context.failure ==
                  bridge::CouncilApplicationMainFailureV1::mailbox_identity &&
              fixture.producer_calls == 0,
          "wrong mailbox identity reached Council native reads");
  Reclaim(harness);
}

} // namespace

int main() {
  try {
    TestQueryTransactionAndSerializer();
    TestIncompleteNativeGatesStayUnadvertised();
    TestReadOnlyFinalGatesCannotSubmitOrPublishPartialRows();
    TestSubmitAndFreshReceipt();
    TestReplacementFireabilityBlocksHelper();
    TestMailboxIdentityMismatchIsInfrastructureRed();
    std::cout << "council_application_main_v1_test: 6/6 GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "council_application_main_v1 RED: " << error.what() << '\n';
    return 1;
  }
}
