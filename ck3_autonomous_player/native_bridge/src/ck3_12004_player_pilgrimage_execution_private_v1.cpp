#include "ck3_12004_player_pilgrimage_execution_private_v1.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/activity_typed_cost_serializer_v1.hpp"
#include "xar_bridge/ck3_12002_event_window_context.hpp"
#include "xar_bridge/protocol.hpp"
#include <windows.h>
#include <memory>
#include <mutex>

namespace xar::ck3_12002 {
namespace {
using namespace ck3_11906;
using Op = PilgrimageExecutionOperation12004V1;
using PlannerOp = ActivityPilgrimagePlannerOperation12004V1;
std::atomic<PilgrimageExecutionAdmission12004V1> g_admission{nullptr};
std::atomic<bool> g_admission_configured{false};
void *g_admission_context = nullptr; // Published once by g_admission release.

bool ReadMemory(void *, std::uintptr_t address, void *out, std::size_t size) noexcept {
  SIZE_T got = 0;
  return address != 0 && out != nullptr && size != 0 &&
      ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<const void *>(address),
                        out, size, &got) && got == size;
}
bool ReadAdapter(void *opaque, game::Snapshot &out) noexcept {
  return opaque != nullptr && static_cast<const game::GameAdapter *>(opaque)->read_snapshot(out);
}
bool ResolveIdentifier(void *opaque, std::int32_t id, std::string_view &out) noexcept {
  out = {};
  const auto *adapter = static_cast<const game::GameAdapter *>(opaque);
  if (adapter == nullptr || !adapter->enabled() || id < 0 ||
      !game::IsCk3_12004Descriptor(adapter->descriptor())) return false;
  const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  if (base == 0) return false;
  const auto getter = reinterpret_cast<EventGetRegistry>(base +
      bridge::Activity12004RvaV1(adapter->descriptor().executable_sha256,
                                kEventScriptIdentifierTableGetterRva));
  const auto resolve = reinterpret_cast<EventResolveIdentifierName>(base +
      bridge::Activity12004RvaV1(adapter->descriptor().executable_sha256,
                                kEventScriptIdentifierNameResolverRva));
  __try {
    auto *table = getter();
    if (table == nullptr) return false;
    const auto *name = resolve(table, id);
    if (name == nullptr || name->empty() || name->size() > 96) return false;
    out = std::string_view(name->data(), name->size());
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}

struct Context {
  PlayerPilgrimageExecutionQuery12004V1 *query = nullptr;
  DWORD owner = 0;
  ActivityPlanner12002NativeV1 native{};
  bridge::ActivityPilgrimageStartCaptureSourcesV1 sources{};
  std::array<std::uint32_t, 4> reserve_mapping{10, 10, 10, 10};
};
bool Current(Context &context, game::Snapshot &out) noexcept {
  const auto &q = *context.query;
  return q.admission != nullptr && q.admission(q.admission_context, q.passive_cost) &&
      !q.mailbox->stop_requested.load(std::memory_order_acquire) &&
      GetCurrentThreadId() == context.owner && q.read_snapshot != nullptr &&
      q.read_snapshot(q.native_context, out) && out == q.expected_snapshot &&
      out.paused && out.map_ready && out.has_played_character &&
      out.played_character_alive && out.played_character_id > 0;
}
bool NativeSnapshot(void *opaque, game::Snapshot &out) noexcept {
  return opaque != nullptr && Current(*static_cast<Context *>(opaque), out);
}
bool NativeIdentifier(void *opaque, std::int32_t id, std::string_view &out) noexcept {
  if (opaque == nullptr) return false;
  auto &c = *static_cast<Context *>(opaque);
  game::Snapshot current{};
  return Current(c, current) && c.query->resolve_script_identifier != nullptr &&
         c.query->resolve_script_identifier(c.query->native_context, id, out);
}
bool HostedFrame(void *opaque, bridge::ActivityHostedIdentityFrameV1 &out) noexcept {
  auto &c = *static_cast<Context *>(opaque);
  game::Snapshot s{};
  if (!Current(c, s)) return false;
  out = {c.query->expected_revision, s.date_raw, s.played_character_id,
          true, true, true, true};
  return true;
}
bridge::ActivityPlannerDiagFrameV1 Frame(const PlayerPilgrimageExecutionQuery12004V1 &q) noexcept {
  return {q.expected_revision, q.expected_snapshot.date_raw,
          q.expected_snapshot.played_character_id, true, true, true, true};
}
bool CaptureMappedStart(void *opaque, const bridge::ActivityPlannerDiagFrameV1 &frame,
                        bridge::ActivityPilgrimageStage5SnapshotV1 &out) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  const auto &q = *context.query;
  return q.admission != nullptr && q.admission(q.admission_context, q.passive_cost) &&
         !q.mailbox->stop_requested.load(std::memory_order_acquire) &&
         bridge::CaptureActivityPilgrimageStage5V1(&context.sources, frame, out) &&
         out.quote.known_name_resource_indices == context.reserve_mapping &&
         out.quote == q.cost.quote &&
         q.admission(q.admission_context, q.passive_cost) &&
         !q.mailbox->stop_requested.load(std::memory_order_acquire);
}
bool CommitMappedStart(void *opaque, std::uintptr_t base,
                       std::uintptr_t planner) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  game::Snapshot current{};
  if (!Current(context, current) || base != context.query->module_base ||
      planner != context.query->cost.quote.planner) return false;
  return bridge::InvokeActivityPilgrimageNativeCommit12004V1(nullptr, base, planner);
}
bool IsWrite(Op op) noexcept {
  return op == Op::open || op == Op::confirm || op == Op::select || op == Op::start;
}
std::string_view OperationName(Op op) noexcept {
  switch (op) {
  case Op::read: return "read"; case Op::open: return "open";
  case Op::confirm: return "confirm"; case Op::can_select: return "can_select";
  case Op::select: return "select"; case Op::quote: return "quote";
  case Op::start: return "start"; case Op::post: return "post";
  }
  return {};
}
std::string_view LedgerName(bridge::ActivityPilgrimageStartStateV1 state) noexcept {
  using S = bridge::ActivityPilgrimageStartStateV1;
  switch (state) {
  case S::idle: return "idle"; case S::submitted_pending: return "submitted_pending";
  case S::submission_outcome_unknown: return "submission_outcome_unknown";
  case S::identity_observed: return "identity_observed";
  }
  return {};
}
void AppendString(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out += '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 0x20) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += static_cast<char>(c);
  }
  out += '"';
}
std::string Bool(bool b) { return b ? "true" : "false"; }

// One process owns one ledger. No request ID, MCP reconnect, actor switch or
// supplied case name can reset a submitted/unknown ledger. No reset API exists.
struct ProcessState {
  std::mutex worker_lock;
  bridge::ActivityPilgrimageStartLedgerV1 ledger{};
  std::unique_ptr<PlayerPilgrimageExecutionQuery12004V1> active;
};
ProcessState &State() { static ProcessState state; return state; }

bool ReclaimCompleted(ProcessState &state) noexcept {
  if (!state.active) return true;
  auto &q = *state.active;
  const auto reclaimed = ReclaimMainThreadQueryV1(*q.mailbox, q.ticket);
  if (reclaimed != MainThreadQueryReclaimResultV1::reclaimed) return false;
  state.active.reset();
  return true;
}

bool ParseRequest(std::string_view payload, bool write,
                  PlayerPilgrimageExecutionQuery12004V1 &q) {
  std::uint64_t actor = 0, date = 0, revision = 0, province = 0, stage = 0;
  std::string activity, option, operation;
  if (!bridge::JsonUnsignedField(payload, "expected_actor_character_id", actor) ||
      actor != static_cast<std::uint64_t>(q.expected_snapshot.played_character_id) ||
      !bridge::JsonUnsignedField(payload, "expected_date_raw", date) ||
      date != static_cast<std::uint64_t>(q.expected_snapshot.date_raw) ||
      !bridge::JsonUnsignedField(payload, "expected_revision", revision) || revision != q.expected_revision ||
      !bridge::JsonStringField(payload, "expected_activity_key", activity, 96) || activity != "activity_pilgrimage" ||
      !bridge::JsonStringField(payload, "expected_option_key", option, 96) ||
      bridge::PilgrimageContractForKeyV1(option) == nullptr ||
      !bridge::JsonStringField(payload, "operation", operation, 24) ||
      !bridge::JsonUnsignedField(payload, "province_id", province) || province >= UINT32_MAX ||
      !bridge::JsonUnsignedField(payload, "read_stage", stage) || stage > 5) return false;
  bool found = false;
  for (auto op : {Op::read, Op::open, Op::confirm, Op::can_select, Op::select, Op::quote, Op::start, Op::post})
    if (OperationName(op) == operation) { q.operation = op; found = true; }
  if (!found || IsWrite(q.operation) != write) return false;
  q.province_id = static_cast<std::uint32_t>(province);
  q.option_key = option;
  q.read_stage = static_cast<std::int32_t>(stage);
  const bool destination = q.operation == Op::can_select || q.operation == Op::select || q.operation == Op::start;
  if ((destination && province == 0) || (!destination && province != 0) ||
      (q.operation != Op::read && stage != 0)) return false;
  if (write) {
    if (!bridge::JsonBooleanField(payload, "policy_positive", q.policy_positive) ||
        !q.policy_positive) return false;
    constexpr std::array<std::string_view, 4> keys{
        "reserve_gold_raw", "reserve_treasury_raw", "reserve_piety_raw", "reserve_barter_goods_raw"};
    for (std::size_t i = 0; i < keys.size(); ++i) {
      std::uint64_t reserve = 0;
      if (!bridge::JsonUnsignedField(payload, keys[i], reserve) ||
          reserve > static_cast<std::uint64_t>((std::numeric_limits<std::int64_t>::max)()) ||
          (q.operation != Op::start && reserve != 0)) return false;
      q.reserve_by_name_raw[i] = static_cast<std::int64_t>(reserve);
    }
  }
  return true;
}
} // namespace

bool ConfigurePilgrimageExecutionAdmission12004V1(
    PilgrimageExecutionAdmission12004V1 admission, void *context) noexcept {
  if (admission == nullptr ||
      g_admission_configured.exchange(true, std::memory_order_acq_rel))
    return false;
  g_admission_context = context;
  g_admission.store(admission, std::memory_order_release);
  return true;
}

bool IsPlayerPilgrimageExecutionPrivate12004V1(std::string_view step) noexcept {
#if defined(XAR_CK3_ENABLE_G2_PLAYER_PILGRIMAGE_EXECUTION_PRIVATE_V1)
  return step == kPilgrimagePlannerQuery12004V1 || step == kPilgrimagePlannerSubmit12004V1;
#else
  (void)step; return false;
#endif
}

bool ExecutePlayerPilgrimageExecutionPrivate12004V1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *q = static_cast<PlayerPilgrimageExecutionQuery12004V1 *>(opaque);
  if (q == nullptr || q->mailbox == nullptr || q->ledger == nullptr ||
      q->ticket.sequence == 0 || q->expected_revision == 0 || q->invocations != 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 || GetCurrentThreadId() != stamp.thread_id)
    return false;
  auto &m = *q->mailbox;
  if (m.state.load(std::memory_order_acquire) != MainThreadQueryMailboxStateV1::executing ||
      m.stop_requested.load(std::memory_order_acquire) || m.failure_flags.load(std::memory_order_acquire) != 0 ||
      m.published_sequence.load(std::memory_order_acquire) != q->ticket.sequence ||
      m.owner_thread_id.load(std::memory_order_acquire) != stamp.thread_id ||
      m.paused_owner_verified_pump_epochs.load(std::memory_order_acquire) <
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      m.executor != &ExecutePlayerPilgrimageExecutionPrivate12004V1 || m.executor_context != q)
    return false;
  try {
    ++q->invocations;
    Context context{q, stamp.thread_id};
    game::Snapshot current{};
    if (!Current(context, current) || current.date_raw != stamp.date_raw) {
      q->frame_changed = true; q->failure = "published_frame_changed";
    } else if (!q->enabled || q->module_base == 0 ||
               !bridge::IsActivity12004BuildV1(q->executable_sha256) ||
                bridge::PilgrimageContractForKeyV1(q->option_key) == nullptr ||
               (IsWrite(q->operation) && !q->policy_positive)) {
      q->failure = "exact4_or_private_policy_rejected";
    } else if (!BindActivityPlanner12002V1(context.native, q->module_base,
        q->executable_sha256, &context, &NativeSnapshot, &ReadMemory,
        &NativeIdentifier, q->expected_revision, stamp.thread_id, stamp.game_state)) {
      q->failure = "native_planner_bind_rejected";
    } else {
      const auto frame = Frame(*q);
      context.sources.cost.enabled = true;
      context.sources.cost.diagnostic = BuildActivityPlanner12002DiagEnvironmentV1(context.native);
      context.sources.cost.passive_cost = q->passive_cost;
      context.sources.cost.read_selection = &ReadActivityPlanner12004PilgrimageSelectedOptionV1;
      context.sources.cost.selection_context = &context.native;
      context.sources.hosted = {true, q->executable_sha256, q->module_base,
          &context, &ReadMemory, &HostedFrame};
      context.sources.read_destination = &ReadActivityPlanner12004PilgrimageDestinationStateV1;
      context.sources.destination_context = &context.native;
      ActivityPilgrimagePlannerRequest12004V1 request{};
      request.expected_frame = frame; request.province_id = q->province_id;
      request.read_stage = q->read_stage;
      request.option_key = q->option_key;
      bool planner_operation = true;
      switch (q->operation) {
      case Op::read: request.operation = PlannerOp::read; break;
      case Op::open: request.operation = PlannerOp::open; break;
      case Op::confirm: request.operation = PlannerOp::confirm; break;
      case Op::can_select: request.operation = PlannerOp::can_select; break;
      case Op::select: request.operation = PlannerOp::select; break;
      default: planner_operation = false; request.operation = PlannerOp::read; request.province_id = 0; break;
      }
      if (q->operation != Op::post) {
        ExecuteActivityPilgrimagePlannerOperation12004V1(context.native, stamp,
            current, request, q->planner);
      }
      if (planner_operation) {
        using S = ActivityPilgrimagePlannerStatus12004V1;
        switch (q->planner.status) {
        case S::observed: case S::opened: case S::already_open: case S::confirmed:
        case S::can_select_observed: case S::selected: q->operation_status = "observed"; break;
        default: q->operation_status = q->planner.needs_recovery ? "needs_recovery" : "rejected"; break;
        }
      } else if (q->operation == Op::quote || q->operation == Op::start) {
        if (q->operation == Op::start && q->ledger->state != bridge::ActivityPilgrimageStartStateV1::idle) {
          q->operation_status = "rejected"; q->failure = "process_start_ledger_not_idle";
        } else {
          q->cost = bridge::ReadActivityTypedPlannerFullCostV1(
              context.sources.cost, frame, *bridge::PilgrimageContractForKeyV1(q->option_key));
          if (q->cost.status != bridge::ActivityTypedFullCostStatusV1::observed ||
              bridge::SerializeActivityTypedPlannerFullCostV1(q->cost).empty()) {
            q->operation_status = "unavailable";
            q->failure = "typed_full10_quote_unavailable;cost_status=";
            q->failure += bridge::ActivityTypedFullCostStatusKeyV1(q->cost.status);
            if (q->cost.status == bridge::ActivityTypedFullCostStatusV1::observed)
              q->failure += ";serializer_rejected=true";
            q->failure += ";diag=";
            q->failure += bridge::ActivityPlannerDiagStatusKeyV1(q->planner.diagnostic.status);
            q->failure += q->planner.diagnostic.value.host_view_activity_key_known
                ? ";host_key_known=true" : ";host_key_known=false";
          } else if (q->operation == Op::quote) q->operation_status = "observed";
          else {
            context.reserve_mapping = q->cost.quote.known_name_resource_indices;
            bridge::ActivityPilgrimageStage5StartRequestV1 start_request{};
            start_request.expected = frame; start_request.policy_approved = q->policy_positive;
            start_request.destination_province_id = q->province_id;
            for (std::size_t i = 0; i < context.reserve_mapping.size(); ++i)
              start_request.reserve_raw[context.reserve_mapping[i]] = q->reserve_by_name_raw[i];
            const bridge::ActivityPilgrimageStage5StartEnvironmentV1 start_environment{
                true, q->executable_sha256, q->module_base, &context,
                &ReadMemory, &CaptureMappedStart, &CommitMappedStart};
            q->start = bridge::StartActivityPilgrimageStage5V1(start_environment, start_request, *q->ledger);
            q->operation_status = !q->start.invoked ? "rejected" :
                q->start.state == bridge::ActivityPilgrimageStartStateV1::submitted_pending
                  ? "submitted_pending" : "submission_outcome_unknown";
          }
        }
      } else {
        const auto &prior = q->ledger->before.quote.selection;
        if (q->ledger->state != bridge::ActivityPilgrimageStartStateV1::idle &&
            (prior.option_key_size >= prior.option_key.size() ||
             std::string_view(prior.option_key.data(), prior.option_key_size) != q->option_key)) {
          q->failure = "post_requested_option_differs_from_original_start";
          q->operation_status = "rejected";
          q->ledger_state = q->ledger->state;
          q->completed = true;
          return true;
        }
        bridge::ActivityHostedIdentityFrameV1 hosted_frame{};
        if (!HostedFrame(&context, hosted_frame)) q->failure = "post_frame_unavailable";
        else {
          const auto after = bridge::ReadActivityHostedIdentityV1(context.sources.hosted, hosted_frame);
          q->post = bridge::ReconcileActivityPilgrimageStartV1(*q->ledger, after);
          using P = bridge::ActivityPilgrimageReconcileStatusV1;
          switch (q->post.status) {
          case P::pending: q->operation_status = "post_pending"; break;
          case P::identity_observed: q->operation_status = "identity_observed"; break;
          case P::ambiguous_new_identities: q->operation_status = "ambiguous"; break;
          default: q->operation_status = "unavailable"; q->failure = "post_observation_rejected"; break;
          }
        }
      }
    }
    q->ledger_state = q->ledger->state;
    q->completed = true;
    return true;
  } catch (...) {
    q->failure = "native_execution_exception";
    q->operation_status = q->start.invoked ? "submission_outcome_unknown" : "unavailable";
    q->ledger_state = q->ledger->state;
    q->completed = true; return true;
  }
}

std::string SerializePlayerPilgrimageExecutionPrivate12004V1(
    const PlayerPilgrimageExecutionQuery12004V1 &q) {
  if (!q.completed || q.frame_changed || !bridge::IsActivity12004BuildV1(q.executable_sha256) ||
      bridge::PilgrimageContractForKeyV1(q.option_key) == nullptr ||
      q.expected_revision == 0 || q.expected_snapshot.played_character_id <= 0) return {};
  std::string out = "{\"schema\":\"ck3_12004_player_pilgrimage_planner_v1\",\"read_only\":" + Bool(!IsWrite(q.operation));
  out += ",\"snapshot_revision\":" + std::to_string(q.expected_revision) +
      ",\"date_raw\":" + std::to_string(q.expected_snapshot.date_raw) +
      ",\"played_character_id\":" + std::to_string(q.expected_snapshot.played_character_id) +
      ",\"activity_type_key\":\"activity_pilgrimage\",\"special_option_key\":";
  AppendString(out, q.option_key); out += ",\"operation\":";
  AppendString(out, OperationName(q.operation)); out += ",\"operation_status\":"; AppendString(out, q.operation_status);
  out += ",\"invoked\":" + Bool(q.start.invoked || q.planner.invoked) +
      ",\"needs_recovery\":" + Bool(q.planner.needs_recovery ||
          q.start.state == bridge::ActivityPilgrimageStartStateV1::submission_outcome_unknown ||
          q.ledger_state == bridge::ActivityPilgrimageStartStateV1::submission_outcome_unknown);
  out += ",\"ledger_state\":"; AppendString(out, LedgerName(q.ledger_state));
  const auto &p = q.planner;
  if (p.selection_observed &&
      (p.selection.option_key_size >= p.selection.option_key.size() ||
       bridge::PilgrimageContractForKeyV1(std::string_view(
           p.selection.option_key.data(), p.selection.option_key_size)) == nullptr)) return {};
  auto failure = q.failure;
  // Preserve the strict public DTO schema. Describe observed reader state in
  // the existing failure string; never promote UI appearance into selection.
  if (failure.empty() && !p.selection_observed &&
      (q.operation == Op::read || q.operation == Op::open)) {
    failure = "typed_selection_unobserved;diag=";
    failure += bridge::ActivityPlannerDiagStatusKeyV1(p.diagnostic.status);
    failure += ";host_key_known=";
    failure += p.diagnostic.value.host_view_activity_key_known ? "true" : "false";
    if (p.diagnostic.value.host_view_activity_key_known &&
        p.diagnostic.value.host_view_activity_key_size <
            p.diagnostic.value.host_view_activity_key.size()) {
      failure += ";host_key=";
      failure.append(p.diagnostic.value.host_view_activity_key.data(),
                     p.diagnostic.value.host_view_activity_key_size);
    }
    if (p.diagnostic.value.stage == 1) {
      failure += ";stage1=";
      failure += bridge::ActivityPilgrimageStage1OptionReadStatusKeyV1(p.stage1.status);
      if (p.stage1.status == bridge::ActivityPilgrimageStage1OptionReadStatusV1::observed &&
          p.stage1.option_key_size < p.stage1.option_key.size()) {
        failure += ";stage1_option=";
        failure.append(p.stage1.option_key.data(), p.stage1.option_key_size);
        failure += ";stage1_confirm_ready=";
        failure += p.stage1.pilgrimage_confirm_ready ? "true" : "false";
      }
    }
  }
  out += ",\"failure\":"; AppendString(out, failure); out += ",\"planner\":";
  if (p.diagnostic.status != bridge::ActivityPlannerDiagStatusV1::observed ||
      p.diagnostic.value.stage < 0 || p.diagnostic.value.stage > 5) out += "null";
  else {
    out += "{\"stage\":" + std::to_string(p.diagnostic.value.stage) + ",\"selected_option_key\":";
    if (p.selection_observed) AppendString(out, std::string_view(
        p.selection.option_key.data(), p.selection.option_key_size));
    else out += "null";
    out += ",\"destination_province_id\":";
    out += p.destination_observed && p.destination.province_id != 0 ? std::to_string(p.destination.province_id) : "null";
    out += ",\"can_select\":";
    out += p.destination_operation.can_select_observed ? Bool(p.destination_operation.can_select) : "null";
    out += ",\"can_progress\":";
    out += p.stage1.status == bridge::ActivityPilgrimageStage1OptionReadStatusV1::observed ? Bool(p.stage1.can_progress) : "null";
    out += '}';
  }
  out += ",\"quote\":";
  const auto quote = bridge::SerializeActivityTypedPlannerFullCostV1(q.cost);
  if (q.cost.status == bridge::ActivityTypedFullCostStatusV1::observed && quote.empty()) return {};
  out += quote.empty() ? "null" : quote;
  out += ",\"new_identity\":";
  if (q.post.status != bridge::ActivityPilgrimageReconcileStatusV1::identity_observed) out += "null";
  else {
    const auto &id = q.post.identity;
    if (id.type_key_size >= id.type_key.size() ||
        id.host_character_id != q.expected_snapshot.played_character_id || !id.terminal_flags_observed ||
        std::string_view(id.type_key.data(), id.type_key_size) != "activity_pilgrimage") return {};
    out += "{\"activity_id\":" + std::to_string(id.activity_id) +
        ",\"host_character_id\":" + std::to_string(id.host_character_id) +
        ",\"type_key\":\"activity_pilgrimage\",\"terminal_flags_observed\":true,\"native_completed\":" +
        Bool(id.native_completed) + ",\"native_invalidated\":" + Bool(id.native_invalidated) +
        ",\"native_completion_stamp_observed\":" + Bool(id.native_completion_stamp_observed) +
        ",\"native_completion_stamp_raw\":" + (id.native_completion_stamp_observed ? std::to_string(id.native_completion_stamp_raw) : "null") + '}';
  }
  out += ",\"absence_is_completion\":false,\"raw_pointer_fields_persisted\":false}";
  return out;
}

std::string SerializePlayerPilgrimageExecutionCommandResult12004V1(
    const PlayerPilgrimageExecutionQuery12004V1 &q,
    std::string_view request_id, std::string_view step) {
  if (step != (IsWrite(q.operation) ? kPilgrimagePlannerSubmit12004V1 : kPilgrimagePlannerQuery12004V1)) return {};
  const auto body = SerializePlayerPilgrimageExecutionPrivate12004V1(q);
  if (body.empty()) return {};
  std::string out = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendString(out, request_id); out += ",\"ok\":true,\"result\":{\"step\":"; AppendString(out, step);
  out += ",\"accepted\":true,\"status\":\"available\",\"private_build\":true,\"advertised\":false,\"read_only\":" +
      Bool(!IsWrite(q.operation)) + ",\"player_pilgrimage_planner\":" + body + ",\"backend_id\":\"native-headless\"}}";
  return out;
}

bool HandlePlayerPilgrimageExecutionPrivate12004V1(
    const game::GameAdapter &adapter, MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision, std::string_view step,
    std::string_view payload, std::string_view request_id,
    bridge::ActivityCostSlot12ObserverV1 *cost, std::string &serialized,
    std::string &failure) noexcept {
  if (!IsPlayerPilgrimageExecutionPrivate12004V1(step)) return false;
  serialized.clear(); failure.clear();
  try {
    if (!adapter.enabled() || !game::IsCk3_12004Descriptor(adapter.descriptor()) || revision == 0) {
      failure = "exact4_execution_unavailable"; return false;
    }
    auto &state = State(); std::lock_guard lock(state.worker_lock);
    if (!ReclaimCompleted(state)) { failure = "previous_native_execution_still_owned"; return false; }
    auto query = std::make_unique<PlayerPilgrimageExecutionQuery12004V1>();
    auto &q = *query;
    q.mailbox = &mailbox; q.enabled = true;
    q.module_base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    q.executable_sha256 = adapter.descriptor().executable_sha256;
    q.native_context = const_cast<game::GameAdapter *>(&adapter);
    q.read_snapshot = &ReadAdapter; q.resolve_script_identifier = &ResolveIdentifier;
    q.expected_snapshot = published; q.expected_revision = revision;
    q.passive_cost = cost; q.ledger = &state.ledger;
    q.admission = g_admission.load(std::memory_order_acquire);
    q.admission_context = q.admission != nullptr ? g_admission_context : nullptr;
    if (q.admission == nullptr || !q.admission(q.admission_context, q.passive_cost)) {
      failure = "cold_execution_admission_revoked_or_unconfigured"; return false;
    }
    if (!ParseRequest(payload, step == kPilgrimagePlannerSubmit12004V1, q)) {
      failure = "typed_pilgrimage_request_invalid"; return false;
    }
    state.active = std::move(query);
    if (TrySubmitMainThreadQueryV1(mailbox, &ExecutePlayerPilgrimageExecutionPrivate12004V1,
          &q, q.ticket) != MainThreadQuerySubmitResultV1::submitted) {
      state.active.reset(); failure = "execution_permission_or_mailbox_unavailable"; return false;
    }
    const auto wait = WaitForMainThreadQueryV1(mailbox, q.ticket, 8'000);
    if (wait != MainThreadQueryWaitResultV1::completed) {
      // Request/backing/ledger remain process-owned until exact reclaim succeeds.
      const auto reclaim = ReclaimMainThreadQueryV1(mailbox, q.ticket);
      if (reclaim == MainThreadQueryReclaimResultV1::reclaimed) state.active.reset();
      failure = "execution_pending_or_unknown_do_not_retry_submit"; return false;
    }
    if (!q.completed) { failure = "executor_guard_rejected"; ReclaimCompleted(state); return false; }
    if (!q.start.invoked) {
      game::Snapshot after{};
      if (!adapter.read_snapshot(after) || after != published) q.frame_changed = true;
    }
    serialized = SerializePlayerPilgrimageExecutionCommandResult12004V1(q, request_id, step);
    const bool good = !serialized.empty();
    if (!ReclaimCompleted(state)) { serialized.clear(); failure = "execution_reclaim_unknown"; return false; }
    if (!good) failure = "execution_typed_serializer_rejected";
    return good;
  } catch (...) { failure = "private_execution_transport_exception"; return false; }
}

} // namespace xar::ck3_12002
