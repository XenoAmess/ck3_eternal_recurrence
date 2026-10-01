#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_realm_law_action_mailbox.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <limits>
#include <memory>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
using namespace bridge;
enum class Mode { observe, enact, receipt };
struct Query {
  QueryMailboxEnvelope envelope{};
  RealmLawActionMailboxState12002 *state = nullptr;
  const RealmLawActionMailboxFixture12002 *fixture = nullptr;
  Mode mode = Mode::observe;
  RealmLawEnactActionRequestV1 request{};
  std::unique_ptr<RealmLawEnactActionObservationV1> observation;
  RealmLawEnactActionAckV1 ack{};
  RealmLawEnactActionReceiptV1 receipt{};
  std::string submitted_request_id;
  std::string status;
  std::string failure;
  bool complete = false;
};

std::string Quote(std::string_view input) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char c : input) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 0x20) {
      out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15];
    } else out += static_cast<char>(c);
  }
  return out + '"';
}
std::string Bool(bool value) { return value ? "true" : "false"; }
std::string Key(const RealmLawGovernanceKeyV1 &key) {
  return Quote(RealmLawGovernanceKeyViewV1(key));
}
std::string Titles(const RealmLawGovernanceTitleBaselineV1 &titles) {
  std::string out = "{\"primary_title_id\":" +
      std::to_string(titles.primary_title_id) + ",\"held_titles\":[";
  for (std::size_t i = 0; i < titles.held_title_count; ++i) {
    if (i != 0) out += ',';
    const auto &title = titles.held_titles[i];
    out += "{\"title_id\":" + std::to_string(title.title_id) +
        ",\"primary\":" + Bool(title.primary) + ",\"successor_character_ids\":[";
    for (std::size_t n = 0; n < title.successor_count; ++n) {
      if (n != 0) out += ',';
      out += std::to_string(title.successor_character_ids[n]);
    }
    out += "]}";
  }
  return out + "]}";
}
template <typename Charges>
std::string SerializeCharges(const Charges &charges, std::uint32_t count) {
  std::string out = "[";
  for (std::size_t i = 0; i < count; ++i) {
    if (i != 0) out += ',';
    const auto &charge = charges[i];
    out += "{\"currency_key\":" + Key(charge.currency_key) +
        ",\"cost_raw\":" + std::to_string(charge.cost_raw) +
        ",\"pre_balance_raw\":" + std::to_string(charge.pre_balance_raw) +
        ",\"post_balance_raw\":" + std::to_string(charge.post_balance_raw) + "}";
  }
  return out + ']';
}

bool ReadMemory(void *opaque, std::uintptr_t address,
                void *output, std::size_t size) noexcept {
  auto &query = *static_cast<Query *>(opaque);
  if (query.fixture != nullptr) return query.fixture->read_memory != nullptr &&
      query.fixture->read_memory(query.fixture->context, address, output, size);
  SIZE_T read = 0;
  return address != 0 && output != nullptr && ReadProcessMemory(
      GetCurrentProcess(), reinterpret_cast<const void *>(address), output,
      size, &read) != 0 && read == size;
}
bool ReadMutation(void *opaque, std::uintptr_t rva,
                  void *output, std::size_t size) noexcept {
  auto &query = *static_cast<Query *>(opaque);
  return ReadMemory(opaque, query.state->source.module_base + rva, output, size);
}
bool Proof(void *opaque, RealmLawNativeRuntimeProofV1 &out) noexcept {
  auto &query = *static_cast<Query *>(opaque);
  out = {};
  const auto &envelope = query.envelope;
  if (!IsQueryOwningThread(&query.envelope) ||
      !query.state->source.command_access.mutation_abi_proof.verified) return false;
  out.exact_build_admitted = true;
  if (!AssignRealmLawNativeDigestV1(kExecutableSha256, out.executable_sha256) ||
      !AssignRealmLawNativeDigestV1(
          private_law::kRealmLawEnactMutationManifestSha256V1,
          out.signature_manifest_sha256)) return false;
  out.module_base = query.state->source.module_base;
  out.signatures_complete = true;
  out.signature_generation = 1;
  out.connection_generation = 1;
  // The source revision is the public paused frame. Pump epochs prove owner
  // execution separately and do not manufacture a second observation clock.
  out.proof_epoch = envelope.expected_snapshot_revision;
  out.current_thread_id = GetCurrentThreadId();
  out.application_main_thread_id = envelope.execution_stamp.thread_id;
  out.paused = envelope.execution_stamp.paused;
  return true;
}
bool Frame(void *opaque, RealmLawGovernanceFrameV1 &out) noexcept {
  auto &query = *static_cast<Query *>(opaque);
  game::Snapshot snapshot{};
  out = {};
  if (!CaptureQuerySnapshot(&query.envelope, snapshot)) return false;
  out.public_revision = query.envelope.expected_snapshot_revision;
  out.native_revision = out.public_revision;
  out.proof_epoch = out.public_revision;
  out.date_raw = snapshot.date_raw;
  out.paused = snapshot.paused;
  out.map_ready = snapshot.map_ready;
  out.played_character_id = snapshot.played_character_id;
  out.played_character_alive = snapshot.played_character_alive;
  out.played_character_identity_round_trip = snapshot.has_played_character;
  return true;
}
bool Bind(Query &query) noexcept {
  auto &state = *query.state;
  auto &source = state.source;
  source.callback_context = &query;
  source.read_runtime_proof = &Proof;
  source.capture_frame = &Frame;
  source.read_memory = &ReadMemory;
  source.failure.clear();
  if (!state.binder.attached) {
    source.admitted_executable_sha256 = kExecutableSha256;
    source.module_base = query.fixture != nullptr ? query.fixture->module_base :
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (source.module_base == 0) return false;
    if (query.fixture != nullptr) {
      source.final_operations = query.fixture->final_operations;
      source.component_operations = query.fixture->component_operations;
      source.primary_title = query.fixture->primary_title;
      source.command_access = query.fixture->command_access;
    } else {
      source.final_operations = private_law::BindRealmLawFinalTermsImage12002(
          source.module_base, kExecutableSha256);
      source.command_access.module_base = source.module_base;
      source.command_access.mutation_abi_proof =
          private_law::VerifyRealmLawEnactMutationAbiV1(
              {&query, &ReadMutation}, source.module_base);
      source.command_access.submit_enabled =
          source.command_access.mutation_abi_proof.verified;
    }
    if (!source.command_access.mutation_abi_proof.verified ||
        !BindRealmLawCrownSource12002(source,
            private_law::kRealmLawEnactMutationManifestSha256V1,
            state.binder, query.fixture != nullptr)) return false;
  }
  return !state.binder.integrity_failed;
}
bool ReadFrameRequest(std::string_view payload, const game::Snapshot &frame,
                      std::uint64_t revision) noexcept {
  std::uint64_t requested = 0, date = 0, actor = 0;
  return JsonUnsignedField(payload, "expected_revision", requested) &&
      JsonUnsignedField(payload, "expected_date_raw", date) &&
      JsonUnsignedField(payload, "expected_player_character_id", actor) &&
      requested == revision && revision != 0 && frame.date_raw > 0 &&
      date == static_cast<std::uint64_t>(frame.date_raw) && actor > 0 &&
      actor == static_cast<std::uint64_t>(frame.played_character_id);
}
bool ReadEnact(std::string_view payload, Query &query,
               const game::Snapshot &frame, std::uint64_t revision) {
  auto &request = query.request;
  std::string group, law;
  if (!JsonStringField(payload, "submitted_request_id", request.request_id, 63) ||
      request.request_id.empty() ||
      !JsonStringField(payload, "group_key", group, 95) ||
      !JsonStringField(payload, "law_key", law, 95) || group != "crown_authority" ||
      !law.starts_with("crown_authority_") ||
      !AssignRealmLawGovernanceKeyV1(group, request.group_key) ||
      !AssignRealmLawGovernanceKeyV1(law, request.law_key) ||
      !JsonUnsignedField(payload, "expected_native_revision", request.expected_native_revision) ||
      !JsonUnsignedField(payload, "expected_proof_epoch", request.expected_proof_epoch)) return false;
  request.expected_public_revision = revision;
  request.expected_date_raw = frame.date_raw;
  request.expected_player_character_id = frame.played_character_id;
  constexpr std::array<std::string_view, 5> currencies{
      "gold", "prestige", "piety", "influence", "merit"};
  for (const auto currency : currencies) {
    std::uint64_t amount = 0;
    const std::string field = "budget_" + std::string(currency) + "_raw";
    if (!JsonUnsignedField(payload, field, amount)) continue;
    if (amount > static_cast<std::uint64_t>((std::numeric_limits<std::int64_t>::max)())) return false;
    auto &budget = request.budgets[request.budget_count++];
    if (!AssignRealmLawGovernanceKeyV1(currency, budget.currency_key)) return false;
    budget.maximum_spend_raw = static_cast<std::int64_t>(amount);
  }
  return true;
}
std::string SerializeResult(const Query &query, std::string_view step,
                            std::string_view request_id) {
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
      Quote(request_id) + ",\"ok\":true,\"result\":{\"step\":" + Quote(step) +
      ",\"accepted\":true,\"private_build\":true,\"advertised\":false,"
      "\"backend_id\":\"native-headless\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"read_only\":" + Bool(query.mode != Mode::enact) +
      ",\"status\":" + Quote(query.status) + ",\"observation\":" +
      (query.observation ? SerializeRealmLawCrownActionObservation12002(*query.observation) : "null") +
      ",\"ack\":" + (query.mode == Mode::enact ? SerializeRealmLawCrownActionAck12002(query.ack) : "null") +
      ",\"receipt\":" + (query.mode == Mode::receipt ? SerializeRealmLawCrownActionReceipt12002(query.receipt) : "null") + "}}";
}
} // namespace

std::string SerializeRealmLawCrownActionObservation12002(
    const RealmLawEnactActionObservationV1 &observation) {
  const auto &snapshot = observation.law_snapshot;
  std::string out = "{\"available\":" + Bool(observation.available) +
      ",\"paused\":" + Bool(observation.paused) +
      ",\"snapshot_revision\":" + std::to_string(snapshot.public_revision) +
      ",\"native_snapshot_revision\":" + std::to_string(snapshot.native_revision) +
      ",\"proof_epoch\":" + std::to_string(snapshot.proof_epoch) +
      ",\"date_raw\":" + std::to_string(snapshot.date_raw) +
      ",\"player_character_id\":" + std::to_string(snapshot.played_character_id);
  if (snapshot.group_count != 1) return out + ",\"group_key\":null,\"active_law_key\":null,\"candidates\":[],\"resources\":[],\"title_successors\":null}";
  const auto &group = snapshot.groups[0];
  out += ",\"group_key\":" + Key(group.group_key) +
      ",\"active_law_key\":" + Key(group.active_law_key) + ",\"candidates\":[";
  for (std::size_t i = 0; i < group.candidate_count; ++i) {
    if (i != 0) out += ',';
    const auto &candidate = group.candidates[i];
    out += "{\"law_key\":" + Key(candidate.law_key) +
        ",\"is_active\":" + Bool(candidate.is_active) +
        ",\"engine_final_only\":" + Bool(candidate.engine_final_only) +
        ",\"can_enact\":" + Bool(candidate.can_enact) +
        ",\"blocked_reason\":" + Quote(RealmLawGovernanceReasonViewV1(candidate.blocked_reason)) +
        ",\"costs\":[";
    for (std::size_t n = 0; n < candidate.cost_count; ++n) {
      if (n != 0) out += ',';
      out += "{\"currency_key\":" + Key(candidate.costs[n].currency_key) +
          ",\"cost_raw\":" + std::to_string(candidate.costs[n].amount_raw) + "}";
    }
    out += "]}";
  }
  out += "],\"resources\":[";
  for (std::size_t i = 0; i < observation.resource_count; ++i) {
    if (i != 0) out += ',';
    out += "{\"currency_key\":" + Key(observation.resources[i].currency_key) +
        ",\"amount_raw\":" + std::to_string(observation.resources[i].amount_raw) + "}";
  }
  return out + "],\"title_successors\":" + Titles(snapshot.title_baseline) + '}';
}
std::string SerializeRealmLawCrownActionAck12002(const RealmLawEnactActionAckV1 &ack) {
  return "{\"submitted_request_id\":" + Quote(ack.request_id) +
      ",\"verification_pending\":" + Bool(ack.verification_pending) +
      ",\"failure\":" + Quote(RealmLawEnactActionFailureNameV1(ack.failure)) +
      ",\"player_character_id\":" + std::to_string(ack.player_character_id) +
      ",\"group_key\":" + Key(ack.group_key) +
      ",\"previous_effective_law_key\":" + Key(ack.previous_effective_law_key) +
      ",\"requested_law_key\":" + Key(ack.requested_law_key) +
      ",\"pre_public_revision\":" + std::to_string(ack.pre_public_revision) +
      ",\"pre_native_revision\":" + std::to_string(ack.pre_native_revision) +
      ",\"pre_proof_epoch\":" + std::to_string(ack.pre_proof_epoch) +
      ",\"pre_date_raw\":" + std::to_string(ack.pre_date_raw) +
      ",\"charges\":" + SerializeCharges(ack.charges, ack.charge_count) +
      ",\"title_successors\":" + Titles(ack.pre_title_successors) + '}';
}
std::string SerializeRealmLawCrownActionReceipt12002(const RealmLawEnactActionReceiptV1 &receipt) {
  return "{\"submitted_request_id\":" + Quote(receipt.request_id) +
      ",\"failure\":" + Quote(RealmLawEnactActionReceiptFailureNameV1(receipt.failure)) +
      ",\"post_public_revision\":" + std::to_string(receipt.post_public_revision) +
      ",\"post_native_revision\":" + std::to_string(receipt.post_native_revision) +
      ",\"post_proof_epoch\":" + std::to_string(receipt.post_proof_epoch) +
      ",\"post_date_raw\":" + std::to_string(receipt.post_date_raw) +
      ",\"effective_law_key\":" + Key(receipt.effective_law_key) +
      ",\"effective_law_verified\":" + Bool(receipt.effective_law_verified) +
      ",\"resources_verified\":" + Bool(receipt.resources_verified) +
      ",\"succession_verified\":" + Bool(receipt.succession_verified) +
      ",\"charges\":" + SerializeCharges(receipt.charges, receipt.charge_count) +
      ",\"title_successors\":" + Titles(receipt.post_title_successors) + '}';
}

bool IsRealmLawPrivateActionStep12002(std::string_view step) noexcept {
  return step == kRealmLawCrownActionQueryStep12002 ||
      step == kRealmLawCrownEnactStep12002 || step == kRealmLawCrownReceiptStep12002;
}
bool ExecuteRealmLawPrivateAction12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr ||
      !EnterQueryMailbox(*envelope, stamp, &ExecuteRealmLawPrivateAction12002)) return true;
  auto &query = *static_cast<Query *>(envelope->typed_context);
  try {
    auto &state = *query.state;
    if (!Bind(query)) query.failure = "native_law_crown_action_binding_unavailable";
    else if (query.mode == Mode::observe) {
      query.observation = std::make_unique<RealmLawEnactActionObservationV1>();
      const auto access = MakeRealmLawNativeActionAccessV1(state.binder);
      if (access.capture_observation == nullptr ||
          !access.capture_observation(access.context, *query.observation))
        query.failure = "native_law_crown_action_observation_unavailable";
      else { query.status = "available"; query.complete = true; }
    } else if (query.mode == Mode::enact) {
      if (state.has_pending_ack || state.binder.submit_pending)
        query.failure = "previous_law_submission_verification_pending";
      else {
        const auto status = ExecuteBoundRealmLawNativeEnactV1(state.binder, query.request, query.ack);
        query.status = status == RealmLawEnactActionAckStatusV1::submitted_verification_pending
            ? "submitted_verification_pending" : "rejected_before_submit";
        if (query.ack.verification_pending) {
          state.pending_ack = query.ack;
          state.pending_sequence = envelope->ticket.sequence;
          state.has_pending_ack = true;
        }
        query.complete = true;
      }
    } else if (!state.has_pending_ack || !state.binder.submit_pending ||
               state.pending_ack.request_id != query.submitted_request_id ||
               envelope->ticket.sequence <= state.pending_sequence)
      query.failure = "independent_pending_law_submission_unavailable";
    else {
      const auto status = VerifyBoundRealmLawNativeReceiptV1(state.binder, state.pending_ack, query.receipt);
      query.status = status == RealmLawEnactActionReceiptStatusV1::enacted ? "enacted" : "failed";
      if (status == RealmLawEnactActionReceiptStatusV1::enacted) {
        state.has_pending_ack = false;
        state.pending_sequence = 0;
      }
      query.complete = true;
    }
    (void)FinishQueryMailbox(*envelope);
    state.source.callback_context = nullptr;
    return true;
  } catch (...) { query.failure = "native_law_crown_action_executor_exception"; return true; }
}

bool HandleRealmLawPrivateWithState12002(
    RealmLawActionMailboxState12002 &state, const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure,
    const RealmLawActionMailboxFixture12002 *fixture) noexcept {
  serialized.clear(); failure.clear();
  if (!IsRealmLawPrivateActionStep12002(step) ||
      xar::game::ReviewedCrozierAbiVersion(adapter.descriptor()) != "1.20.0.2" ||
      xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256 ||
      request_id.empty() || !published.paused || !published.map_ready ||
      !published.has_played_character || !published.played_character_alive ||
      !ReadFrameRequest(payload, published, revision)) {
    failure = "native_law_crown_action_request_contract_invalid"; return false;
  }
  try {
    auto query = std::make_unique<Query>();
    query->state = &state;
    query->fixture = fixture;
    query->mode = step == kRealmLawCrownEnactStep12002 ? Mode::enact :
        step == kRealmLawCrownReceiptStep12002 ? Mode::receipt : Mode::observe;
    if (query->mode == Mode::enact && !ReadEnact(payload, *query, published, revision)) {
      failure = "native_law_crown_enact_request_invalid"; return false;
    }
    if (query->mode == Mode::receipt &&
        (!JsonStringField(payload, "submitted_request_id", query->submitted_request_id, 63) ||
         query->submitted_request_id.empty())) {
      failure = "native_law_crown_receipt_request_invalid"; return false;
    }
    query->envelope.game = fixture != nullptr ? &adapter : &NativeAdapter12002(adapter);
    query->envelope.mailbox = &mailbox;
    query->envelope.expected_snapshot = published;
    query->envelope.expected_snapshot_revision = revision;
    query->envelope.typed_context = query.get();
    if (ck3_11906::TrySubmitMainThreadQueryV1(mailbox, &ExecuteRealmLawPrivateAction12002,
        &query->envelope, query->envelope.ticket) !=
        ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
      failure = "native_law_crown_action_mailbox_submit_unavailable"; return false;
    }
    auto wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query->envelope.ticket, 5000);
    while (wait == ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query->envelope.ticket, 100);
    const auto reclaim = ck3_11906::ReclaimMainThreadQueryV1(mailbox, query->envelope.ticket);
    if (wait != ck3_11906::MainThreadQueryWaitResultV1::completed ||
        reclaim != ck3_11906::MainThreadQueryReclaimResultV1::reclaimed ||
        !query->envelope.frame_stable || !query->complete) {
      failure = query->failure.empty() ? "native_law_crown_action_frame_unavailable" : query->failure;
      return false;
    }
    serialized = SerializeResult(*query, step, request_id);
    return true;
  } catch (...) { failure = "native_law_crown_action_router_exception"; return false; }
}
bool HandleRealmLawPrivate12002(
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  static const auto state = std::make_unique<RealmLawActionMailboxState12002>();
  return HandleRealmLawPrivateWithState12002(*state, adapter, mailbox, published,
      revision, step, payload, request_id, serialized, failure);
}
} // namespace xar::ck3_12002
