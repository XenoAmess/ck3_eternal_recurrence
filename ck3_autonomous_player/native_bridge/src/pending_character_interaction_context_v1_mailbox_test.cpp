#include "xar_bridge/pending_character_interaction_context_v1_mailbox.hpp"

#include <windows.h>

#include <cstdint>
#include <iostream>
#include <string>

namespace {

#if defined(_MSC_VER)
#define XAR_TEST_PENDING_FASTCALL __fastcall
#else
#define XAR_TEST_PENDING_FASTCALL
#endif

xar::game::Snapshot g_snapshot{};
xar::game::ReadPendingCharacterInteractionContextResultV1 g_reader_result =
    xar::game::ReadPendingCharacterInteractionContextResultV1::available;
std::uint32_t g_reader_calls = 0;
std::uint32_t g_native_invocations = 0;

bool XAR_TEST_PENDING_FASTCALL FakeLocalRouting(void *, void *) { return true; }

bool XAR_TEST_PENDING_FASTCALL FakeReplyValidator(void *) { return true; }

bool XAR_TEST_PENDING_FASTCALL FakeTriggerEvaluator(void *, const void *) {
  return false;
}

void XAR_TEST_PENDING_FASTCALL FakeCostEvaluator(const void *, const void *,
                                                 std::int64_t *) {}

void *XAR_TEST_PENDING_FASTCALL FakeCommonWarRelation(void *, void *) {
  return reinterpret_cast<void *>(0x5678);
}

void *XAR_TEST_PENDING_FASTCALL FakeTargetTypeRegistry() {
  return reinterpret_cast<void *>(0x1234);
}

const std::string *XAR_TEST_PENDING_FASTCALL
FakeScriptIdentifierName(std::int32_t) {
  static const std::string value = "fixture_identifier";
  return &value;
}

bool InvokeLocalRouting(
    void *, xar::ck3_11906::NativePendingInteractionLocalRoutingV1 function,
    void *, void *, bool &output) noexcept {
  ++g_native_invocations;
  output = function == &FakeLocalRouting;
  return output;
}

bool InvokeReplyValidator(
    void *, xar::ck3_11906::NativePendingInteractionReplyValidatorV1 function,
    void *, bool &output) noexcept {
  ++g_native_invocations;
  output = function == &FakeReplyValidator;
  return output;
}

bool InvokeTriggerEvaluator(
    void *, xar::ck3_11906::NativePendingInteractionTriggerEvaluatorV1 function,
    void *, const void *, bool &output) noexcept {
  ++g_native_invocations;
  if (function != &FakeTriggerEvaluator) {
    return false;
  }
  output = false;
  return true;
}

bool InvokeCostEvaluator(
    void *, xar::ck3_11906::NativePendingInteractionCostEvaluatorV1 function,
    const void *, const void *,
    std::array<std::int64_t,
               xar::game::kPendingCharacterInteractionCostResourceCountV1>
        &output) noexcept {
  ++g_native_invocations;
  output.fill(0);
  return function == &FakeCostEvaluator;
}

bool InvokeCommonWarRelation(
    void *,
    xar::ck3_11906::NativePendingInteractionCommonWarRelationV1 function,
    void *, void *, void *&output) noexcept {
  ++g_native_invocations;
  output = function == &FakeCommonWarRelation ? reinterpret_cast<void *>(0x5678)
                                              : nullptr;
  return output != nullptr;
}

bool InvokeTargetTypeRegistry(
    void *,
    xar::ck3_11906::NativePendingInteractionTargetTypeRegistryGetterV1 function,
    void *&output) noexcept {
  ++g_native_invocations;
  output = function == &FakeTargetTypeRegistry
               ? reinterpret_cast<void *>(0x1234)
               : nullptr;
  return output != nullptr;
}

bool InvokeScriptIdentifierName(
    void *,
    xar::ck3_11906::NativePendingInteractionScriptIdentifierNameV1 function,
    std::int32_t identifier, const std::string *&output) noexcept {
  ++g_native_invocations;
  output = function == &FakeScriptIdentifierName && identifier == 41
               ? FakeScriptIdentifierName(identifier)
               : nullptr;
  return output != nullptr;
}

void PrimeMailbox(
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    xar::ck3_11906::PendingCharacterInteractionContextMailboxContextV1 &query,
    std::uint64_t sequence) {
  mailbox.state.store(xar::ck3_11906::MainThreadQueryMailboxStateV1::executing);
  mailbox.failure_flags.store(0);
  mailbox.stop_requested.store(false);
  mailbox.published_sequence.store(sequence);
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      xar::ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor =
      &xar::ck3_11906::ExecutePendingCharacterInteractionContextMailboxQueryV1;
  mailbox.executor_context = &query;
  query.mailbox = &mailbox;
  query.ticket.sequence = sequence;
  query.request.expected_snapshot_revision = 77;
  query.request.pending_interaction_id = 16'777'249;
  query.request.played_character_id = 2'001;
  query.expected_snapshot = g_snapshot;
  query.access.invoke_local_routing = &InvokeLocalRouting;
  query.access.invoke_reply_validator = &InvokeReplyValidator;
  query.access.invoke_trigger_evaluator = &InvokeTriggerEvaluator;
  query.access.invoke_cost_evaluator = &InvokeCostEvaluator;
  query.access.invoke_common_war_relation = &InvokeCommonWarRelation;
  query.access.invoke_target_type_registry = &InvokeTargetTypeRegistry;
  query.access.invoke_script_identifier_name = &InvokeScriptIdentifierName;
}

xar::ck3_11906::MainThreadExecutionStampV1 Stamp() {
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 9;
  stamp.thread_id = GetCurrentThreadId();
  stamp.paused = true;
  stamp.date_raw = g_snapshot.date_raw;
  stamp.tls_initialized_flag_address = 0x1000;
  stamp.tls_initialized = 1;
  stamp.tls_context = 0x2000;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = 0x3000;
  stamp.game_state = 0x4000;
  return stamp;
}

bool TestParsing() {
  using namespace xar::ck3_11906;
  std::uint64_t revision = 0;
  std::int32_t pending_id = -1;
  return ParsePendingCharacterInteractionContextV1Step(
             "query-pending-character-interaction-context-v1") &&
         !ParsePendingCharacterInteractionContextV1Step(
             "query-pending-character-interaction-context-v1-1") &&
         ParsePendingCharacterInteractionContextRequestV1(
             R"({"expected_revision":77,"pending_interaction_id":16777249})",
             revision, pending_id) &&
         revision == 77 && pending_id == 16'777'249 &&
         ParsePendingCharacterInteractionContextRequestV1(
             R"({"step":"query-pending-character-interaction-context-v1", "pending_interaction_id": 16777249, "expected_revision": 77})",
             revision, pending_id) &&
         revision == 77 && pending_id == 16'777'249 &&
         !ParsePendingCharacterInteractionContextRequestV1(
             R"({"expected_revision":0,"pending_interaction_id":16777249})",
             revision, pending_id) &&
         !ParsePendingCharacterInteractionContextRequestV1(
             R"({"expected_revision":77,"pending_interaction_id":016777249})",
             revision, pending_id) &&
         !ParsePendingCharacterInteractionContextRequestV1(
             R"({"expected_revision":77,"pending_interaction_id":-1})",
             revision, pending_id) &&
         !ParsePendingCharacterInteractionContextRequestV1(
             R"({"expected_revision":77,"pending_interaction_id":2147483648})",
             revision, pending_id) &&
         !ParsePendingCharacterInteractionContextRequestV1(
             R"({"expected_revision":77,"pending_interaction_id":16777249,"pending_interaction_id":16777250})",
             revision, pending_id) &&
         !ParsePendingCharacterInteractionContextRequestV1(
             R"({"expected_revision":77})", revision, pending_id);
}

bool TestDirectInvocationRejected() {
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::PendingCharacterInteractionContextMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.ticket.sequence = 1;
  query.request.expected_snapshot_revision = 77;
  query.request.pending_interaction_id = 16'777'249;
  query.request.played_character_id = 2'001;
  const auto stamp = Stamp();
  const auto calls_before = g_reader_calls;
  return !xar::ck3_11906::
             ExecutePendingCharacterInteractionContextMailboxQueryV1(&query,
                                                                     stamp) &&
         query.completion ==
             xar::ck3_11906::
                 PendingCharacterInteractionContextMailboxCompletionV1::
                     infrastructure_rejected &&
         g_reader_calls == calls_before;
}

bool TestTypedCompletion(
    xar::game::ReadPendingCharacterInteractionContextResultV1 read_result,
    std::uint64_t sequence) {
  g_reader_result = read_result;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::PendingCharacterInteractionContextMailboxContextV1 query{};
  PrimeMailbox(mailbox, query, sequence);
  const auto stamp = Stamp();
  const auto calls_before = g_reader_calls;
  const auto invokes_before = g_native_invocations;
  if (!xar::ck3_11906::ExecutePendingCharacterInteractionContextMailboxQueryV1(
          &query, stamp) ||
      g_reader_calls != calls_before + 1 ||
      g_native_invocations != invokes_before + 8 ||
      query.executor_invocations != 1 ||
      query.completion !=
          xar::ck3_11906::
              PendingCharacterInteractionContextMailboxCompletionV1::
                  completed ||
      query.result.snapshot_revision != 77 ||
      query.result.date_raw != g_snapshot.date_raw ||
      query.result.pending_interaction_id != 16'777'249 ||
      query.execution_stamp != stamp) {
    return false;
  }
  if (read_result ==
      xar::game::ReadPendingCharacterInteractionContextResultV1::available) {
    return query.result.status ==
               xar::game::PendingCharacterInteractionContextStatusV1::
                   available &&
           query.result.readiness.same_frame_ready &&
           query.result.legality.accept.allowed;
  }
  if (read_result ==
      xar::game::ReadPendingCharacterInteractionContextResultV1::invalid) {
    return query.result.status ==
               xar::game::PendingCharacterInteractionContextStatusV1::invalid &&
           query.result.reason == "send_option_count_mismatch" &&
           !query.result.legality.accept.allowed;
  }
  return query.result.status ==
             xar::game::PendingCharacterInteractionContextStatusV1::
                 unavailable &&
         query.result.reason == "pending_generation_mismatch" &&
         !query.result.legality.accept.allowed;
}

#undef XAR_TEST_PENDING_FASTCALL

} // namespace

namespace xar::ck3_11906 {

bool ResolvePendingCharacterInteractionActiveWarV1(const Bindings &,
                                                   void *game_state,
                                                   std::int32_t war_id,
                                                   void *&output) noexcept {
  ++g_native_invocations;
  output = game_state == reinterpret_cast<void *>(0x4000) && war_id == 17
               ? reinterpret_cast<void *>(0x9ABC)
               : nullptr;
  return output != nullptr;
}

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  output = g_snapshot;
  return true;
}

game::ReadPendingCharacterInteractionContextResultV1
ReadPendingCharacterInteractionContextV1(
    const PendingCharacterInteractionNativeEnvironmentV1 &,
    const PendingCharacterInteractionAccessV1 &access,
    const PendingCharacterInteractionContextRequestV1 &request,
    game::PendingCharacterInteractionContextV1 &output) noexcept {
  ++g_reader_calls;
  game::PendingCharacterInteractionFrameV1 frame{};
  bool routed = false;
  bool valid = false;
  bool evaluated = true;
  std::array<std::int64_t,
             game::kPendingCharacterInteractionCostResourceCountV1>
      costs{};
  void *registry = nullptr;
  void *relation = nullptr;
  void *war = nullptr;
  const std::string *identifier_name = nullptr;
  if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
      access.invoke_local_routing == nullptr ||
      access.invoke_reply_validator == nullptr ||
      access.invoke_trigger_evaluator == nullptr ||
      access.invoke_cost_evaluator == nullptr ||
      access.invoke_common_war_relation == nullptr ||
      access.resolve_active_war == nullptr ||
      access.invoke_target_type_registry == nullptr ||
      access.invoke_script_identifier_name == nullptr ||
      !access.is_main_thread(access.context) ||
      !access.capture_frame(access.context, frame) ||
      !access.invoke_local_routing(access.context, &FakeLocalRouting,
                                   reinterpret_cast<void *>(0x10),
                                   reinterpret_cast<void *>(0x20), routed) ||
      !access.invoke_reply_validator(access.context, &FakeReplyValidator,
                                     reinterpret_cast<void *>(0x30), valid) ||
      !access.invoke_trigger_evaluator(
          access.context, &FakeTriggerEvaluator, reinterpret_cast<void *>(0x40),
          reinterpret_cast<void *>(0x50), evaluated) ||
      !access.invoke_cost_evaluator(access.context, &FakeCostEvaluator,
                                    reinterpret_cast<void *>(0x60),
                                    reinterpret_cast<void *>(0x70), costs) ||
      !access.invoke_common_war_relation(access.context, &FakeCommonWarRelation,
                                         reinterpret_cast<void *>(0x80),
                                         reinterpret_cast<void *>(0x90),
                                         relation) ||
      !access.resolve_active_war(access.context, 17, war) ||
      !access.invoke_target_type_registry(access.context,
                                          &FakeTargetTypeRegistry, registry) ||
      !access.invoke_script_identifier_name(
          access.context, &FakeScriptIdentifierName, 41, identifier_name) ||
      !routed || !valid || evaluated || costs[0] != 0 ||
      relation != reinterpret_cast<void *>(0x5678) ||
      war != reinterpret_cast<void *>(0x9ABC) || registry == nullptr ||
      identifier_name == nullptr || *identifier_name != "fixture_identifier") {
    return game::ReadPendingCharacterInteractionContextResultV1::unavailable;
  }

  output = {};
  output.snapshot_revision = request.expected_snapshot_revision;
  output.date_raw = frame.date_raw;
  output.pending_interaction_id = request.pending_interaction_id;
  const auto mark_unavailable = [](auto &legality, std::string_view reason) {
    legality.status =
        game::PendingCharacterInteractionSemanticStatusV1::unavailable;
    legality.allowed = false;
    legality.reason = reason;
  };
  if (g_reader_result ==
      game::ReadPendingCharacterInteractionContextResultV1::available) {
    output.status = game::PendingCharacterInteractionContextStatusV1::available;
    output.readiness.same_frame_ready = true;
    output.legality.accept.status =
        game::PendingCharacterInteractionSemanticStatusV1::available;
    output.legality.accept.allowed = true;
    return g_reader_result;
  }
  const std::string_view reason =
      g_reader_result ==
              game::ReadPendingCharacterInteractionContextResultV1::invalid
          ? "send_option_count_mismatch"
          : "pending_generation_mismatch";
  output.status =
      g_reader_result ==
              game::ReadPendingCharacterInteractionContextResultV1::invalid
          ? game::PendingCharacterInteractionContextStatusV1::invalid
          : game::PendingCharacterInteractionContextStatusV1::unavailable;
  output.reason = reason;
  mark_unavailable(output.legality.accept, reason);
  mark_unavailable(output.legality.reject, reason);
  mark_unavailable(output.legality.block, reason);
  mark_unavailable(output.legality.acknowledge, reason);
  return g_reader_result;
}

} // namespace xar::ck3_11906

int main() {
  g_snapshot.date_raw = 54'321;
  g_snapshot.paused = true;
  g_snapshot.map_ready = true;
  g_snapshot.has_played_character = true;
  g_snapshot.played_character_alive = true;
  g_snapshot.played_character_id = 2'001;
  g_snapshot.has_pending_character_interaction = true;
  g_snapshot.pending_character_interaction_id = 16'777'249;
  if (!TestParsing()) {
    std::cerr << "pending-interaction mailbox parser fixture failed\n";
    return 1;
  }
  if (!TestDirectInvocationRejected()) {
    std::cerr << "pending-interaction direct invocation fixture failed\n";
    return 1;
  }
  if (!TestTypedCompletion(
          xar::game::ReadPendingCharacterInteractionContextResultV1::available,
          10) ||
      !TestTypedCompletion(
          xar::game::ReadPendingCharacterInteractionContextResultV1::
              unavailable,
          11) ||
      !TestTypedCompletion(
          xar::game::ReadPendingCharacterInteractionContextResultV1::invalid,
          12)) {
    std::cerr << "pending-interaction typed completion fixture failed\n";
    return 1;
  }
  std::cout
      << "pending-character-interaction-context-v1 mailbox fixture passed\n";
  return 0;
}
