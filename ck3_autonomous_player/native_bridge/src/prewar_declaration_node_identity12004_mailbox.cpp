#include "xar_bridge/prewar_declaration_node_identity12004_mailbox.hpp"

#if defined(XAR_ENABLE_PREWAR_DECLARATION_NODE_IDENTITY_V1)

#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_holy_war.hpp"

#include <windows.h>

#include <algorithm>
#include <cstring>
#include <limits>
#include <sstream>
#include <utility>

namespace xar::ck3_12004 {
namespace {
using ck3_11906::MainThreadQueryReclaimResultV1;
using ck3_11906::MainThreadQuerySubmitResultV1;
using ck3_11906::MainThreadQueryWaitResultV1;
using Query = PrewarDeclarationNodeIdentityMailbox12004;
using Request = PrewarForceCoalitionRequest12004;
using Round = PrewarDeclarationNodeRound12004;
using NodeBindings = PrewarDeclarationNodeIdentityBindings12004;
using DatabaseWitness = PrewarDeclarationNodeDatabaseWitness12004;

// Actual4 8FC320 [8FC320,8FC377), 87B, SHA
// 65297dcd2a4daf03aa0b25737c943d19474f203b2278ba338dcba0f84231d46f.
// Its nonnull fast path returns this slot directly. The null slow path calls
// unqualified 3F8B640: this query never invokes the getter or that path.
constexpr std::uintptr_t kCurrentCbDatabaseSlotRva = 0x5C671F0;
constexpr std::size_t kMaximumSelectedTitles = 4096;
constexpr std::size_t kMaximumKeyBytes = 128;
constexpr std::size_t kMaximumRequestIdBytes = 128;

void SetFailure(std::string &failure, std::string_view reason) noexcept {
  try { if (failure.empty()) failure.assign(reason); } catch (...) {}
}
bool Copy(const void *source, void *target, std::size_t size) noexcept {
  if (!source || !target) return false;
  const auto address = reinterpret_cast<std::uintptr_t>(source);
  if (size > (std::numeric_limits<std::uintptr_t>::max)() - address) return false;
  __try { std::memcpy(target, source, size); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
template <class T> bool Read(const void *source, std::size_t offset, T &out) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(source);
  return source && offset <= (std::numeric_limits<std::uintptr_t>::max)() - address &&
      Copy(reinterpret_cast<const void *>(address + offset), &out, sizeof(out));
}
bool ModuleContains(const NodeBindings &b,
                    std::uintptr_t address, std::size_t bytes) noexcept {
  return address >= b.image_base && bytes <= b.runtime_image_size &&
      address - b.image_base <= b.runtime_image_size - bytes;
}
bool LoadedImageSize(std::uintptr_t base, std::size_t &size) noexcept {
  size = 0;
  __try {
    if (!base) return false;
    const auto *dos = reinterpret_cast<const IMAGE_DOS_HEADER *>(base);
    if (dos->e_magic != IMAGE_DOS_SIGNATURE || dos->e_lfanew < 0 ||
        dos->e_lfanew > 0x100000) return false;
    const auto offset = static_cast<std::size_t>(dos->e_lfanew);
    if (offset > (std::numeric_limits<std::uintptr_t>::max)() - base ||
        sizeof(IMAGE_NT_HEADERS64) > (std::numeric_limits<std::uintptr_t>::max)() - base - offset)
      return false;
    const auto *nt = reinterpret_cast<const IMAGE_NT_HEADERS64 *>(base + offset);
    if (nt->Signature != IMAGE_NT_SIGNATURE ||
        nt->FileHeader.Machine != IMAGE_FILE_MACHINE_AMD64 ||
        nt->FileHeader.SizeOfOptionalHeader < sizeof(IMAGE_OPTIONAL_HEADER64) ||
        nt->OptionalHeader.Magic != IMAGE_NT_OPTIONAL_HDR64_MAGIC) return false;
    const auto span = static_cast<std::size_t>(nt->OptionalHeader.SizeOfImage);
    const auto headers = static_cast<std::size_t>(nt->OptionalHeader.SizeOfHeaders);
    if (!span || headers > span || offset > span ||
        sizeof(IMAGE_NT_HEADERS64) > span - offset ||
        sizeof(IMAGE_NT_HEADERS64) > headers || offset > headers - sizeof(IMAGE_NT_HEADERS64) ||
        span > (std::numeric_limits<std::uintptr_t>::max)() - base) return false;
    size = span;
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool ReadCore(const CoreBindings &core, CoreSnapshotPrefix &frame) noexcept {
  __try { return xar::ck3_12004::ReadCoreSnapshot(core, frame); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
void *ResolveCore(const CoreBindings &core, std::int32_t id) noexcept {
  __try { return xar::ck3_12004::ResolveCoreCharacter(core, id); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
}
bool FrameValid(const game::Snapshot &frame, std::uint64_t revision) noexcept {
  return revision && frame.paused && frame.map_ready && frame.has_played_character &&
      frame.played_character_alive && frame.played_character_id > 0 &&
      frame.played_character_id <= (std::numeric_limits<std::int32_t>::max)() &&
      frame.date_raw >= (std::numeric_limits<std::int32_t>::min)() &&
      frame.date_raw <= (std::numeric_limits<std::int32_t>::max)();
}
bool RequestValid(const Request &r) {
  const auto &s = r.selected;
  return r.expected_native_revision && r.expected_public_revision &&
      s.target_character_id > 0 && s.casus_belli_index >= 0 &&
      s.configuration_index >= -1 && s.claimant_character_id >= -1 &&
      !s.casus_belli_key.empty() && s.casus_belli_key.size() <= kMaximumKeyBytes &&
      std::all_of(s.casus_belli_key.begin(), s.casus_belli_key.end(),
          [](unsigned char c) { return c >= 0x21 && c <= 0x7E; }) &&
      s.target_title_ids.size() <= kMaximumSelectedTitles &&
      std::all_of(s.target_title_ids.begin(), s.target_title_ids.end(),
          [](std::int32_t id) { return id >= 0; }) &&
      r.declaration_id == std::to_string(s.target_character_id) + '-' +
          std::to_string(s.casus_belli_index) + '-' + std::to_string(s.configuration_index);
}
bool ExactDeclarations(const Query &q) noexcept {
  const auto &b = q.declarations;
  const auto exact = BindOrdinaryHolyWarDeclarationsImage12004(q.bindings.image_base, kExecutableSha256);
  return b.enabled && b.core.enabled && exact.enabled &&
      b.get_cb_database == exact.get_cb_database &&
      b.core.game_state_slot == q.bindings.core.game_state_slot &&
      b.core.jomini_state_slot == q.bindings.core.jomini_state_slot &&
      b.core.character_storage_slot == q.bindings.core.character_storage_slot;
}

bool ReadDatabase(Query &q,
                  DatabaseWitness &out) {
  const auto slot = q.bindings.image_base + kCurrentCbDatabaseSlotRva;
  if (!ModuleContains(q.bindings, slot, sizeof(void *)) ||
      !Read(reinterpret_cast<const void *>(slot), 0, out.database) || !out.database)
    return false;
  const auto *database = reinterpret_cast<const void *>(out.database);
  if (!Read(database, 0x50, out.types) || !Read(database, 0x5C, out.count) ||
      out.count < 0 || out.count > 10000 || !out.types ||
      q.request.selected.casus_belli_index >= out.count) return false;
  const auto index = static_cast<std::size_t>(q.request.selected.casus_belli_index);
  if (index > (std::numeric_limits<std::size_t>::max)() / sizeof(void *) ||
      !Read(reinterpret_cast<const void *>(out.types), index * sizeof(void *), out.descriptor) ||
      !out.descriptor) return false;
  const auto *descriptor = reinterpret_cast<const void *>(out.descriptor);
  if (!Read(descriptor, 0x18, out.key_storage)) return false;
  std::size_t length = 0, capacity = 0;
  std::memcpy(&length, out.key_storage.data() + 0x10, sizeof(length));
  std::memcpy(&capacity, out.key_storage.data() + 0x18, sizeof(capacity));
  if (!length || length > capacity || length > kMaximumKeyBytes) return false;
  if (capacity <= 15) {
    if (0x18 > (std::numeric_limits<std::uintptr_t>::max)() - out.descriptor) return false;
    out.key_data = out.descriptor + 0x18;
  } else std::memcpy(&out.key_data, out.key_storage.data(), sizeof(out.key_data));
  if (!out.key_data) return false;
  out.key.resize(length);
  return Copy(reinterpret_cast<const void *>(out.key_data), out.key.data(), length) &&
      out.key == q.request.selected.casus_belli_key;
}

bool ReadRound(Query &q,
               Round &out) {
  auto &envelope = q.envelope;
  if (!ck3_12002::IsQueryOwningThread(&envelope) || !ExactDeclarations(q)) return false;
  void *state = nullptr;
  CoreSnapshotPrefix frame{};
  if (!Read(q.bindings.core.game_state_slot, 0, state) ||
      reinterpret_cast<std::uintptr_t>(state) != envelope.execution_stamp.game_state ||
      !ReadCore(q.bindings.core, frame) || !frame.clock.paused || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive ||
      frame.clock.date_raw != envelope.expected_snapshot.date_raw ||
      frame.played_character_id != envelope.expected_snapshot.played_character_id ||
      !ReadDatabase(q, out.database)) return false;
  auto *actor = ResolveCore(q.bindings.core, frame.played_character_id);
  auto *target = ResolveCore(q.bindings.core, q.request.selected.target_character_id);
  if (!actor || !target) return false;
  PrewarDeclarationNodeSelectionObservation12004 observed{};
  observed.frame = frame;
  observed.query_ticket = envelope.ticket.sequence;
  observed.epoch = envelope.execution_stamp.pump_epoch;
  observed.native_revision = q.request.expected_native_revision;
  observed.public_revision = q.request.expected_public_revision;
  // The requested configuration/claimant/titles are preserved as a binding.
  // A database index/key lookup does not finalize those choices or CB roles.
  observed.finalized_selection_ready = false;
  observed.named_roles_ready = false;
  auto &selection = observed.selection;
  selection.actor_character_id = frame.played_character_id;
  selection.target_character_id = q.request.selected.target_character_id;
  selection.casus_belli_index = q.request.selected.casus_belli_index;
  selection.cb_key = q.request.selected.casus_belli_key;
  selection.cb_config_index = q.request.selected.configuration_index;
  selection.claimant_character_id = q.request.selected.claimant_character_id;
  selection.selected_title_ids = q.request.selected.target_title_ids;
  PrewarDeclarationNodeIdentityNativeScope12004 scope{};
  scope.actual_cb = reinterpret_cast<const void *>(out.database.descriptor);
  scope.actual_actor = actor;
  scope.actual_target = target;
  std::string_view reason;
  return ReadPrewarDeclarationNodeIdentity12004(q.bindings, scope, observed,
      out.directory, &reason) && out.directory.sampled;
}

std::string Quote(std::string_view text) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char c : text) {
    if (c == '\\' || c == '"') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 0x20) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += static_cast<char>(c);
  }
  return out + '"';
}
void Selected(std::ostream &out, const Request &r) {
  const auto &s = r.selected;
  out << "{\"target_character_id\":" << s.target_character_id
      << ",\"casus_belli_index\":" << s.casus_belli_index
      << ",\"casus_belli_key\":" << Quote(s.casus_belli_key)
      << ",\"configuration_index\":" << s.configuration_index
      << ",\"claimant_character_id\":" << s.claimant_character_id
      << ",\"target_title_ids\":[";
  for (std::size_t i = 0; i < s.target_title_ids.size(); ++i) {
    if (i) out << ',';
    out << s.target_title_ids[i];
  }
  out << "]}";
}
std::string Outer(const std::string &domain, std::string_view request_id,
                  std::uint64_t ticket, std::uint64_t epoch, bool complete) {
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"execution_receipt\":{\"ticket\":" + std::to_string(ticket) +
      ",\"query_sequence\":" + std::to_string(ticket) +
      ",\"capture_epoch\":" + std::to_string(epoch) + "},\"result\":{\"step\":" +
      Quote(kPrewarDeclarationNodeIdentityStep12004) + ",\"accepted\":true,\"status\":" +
      Quote(complete ? "observed" : "partial") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"domain_key\":" +
      Quote(kPrewarDeclarationNodeIdentityDomain12004) +
      ",\"prewar_declaration_node_identity_v1\":" + domain + "}}";
}
void Rva(std::ostream &out, const PrewarNodeRva12004 &rva) {
  if (rva.observed && rva.in_module) out << rva.value;
  else out << "null";
}
void Index(std::ostream &out, std::uint16_t index) {
  if (index == kPrewarNodeNoIndex12004) out << "null";
  else out << index;
}
std::string Serialize(const Query &q) {
  const auto &d = q.observation.directory;
  std::ostringstream out;
  out << "{\"schema_version\":1,\"read_only\":true,\"structural_capture_complete\":"
      << (d.structural_capture_complete ? "true" : "false")
      << ",\"participant_coverage_complete\":false,\"war_permission\":false"
      << ",\"game_version\":\"1.20.0.4\",\"game_executable_sha256\":" << Quote(kExecutableSha256)
      << ",\"native_revision\":" << q.request.expected_native_revision
      << ",\"public_revision\":" << q.request.expected_public_revision
      << ",\"date_raw\":" << d.frame.date_raw
      << ",\"actor_character_id\":" << d.selection.actor_character_id
      << ",\"selected_target_character_id\":" << d.selection.target_character_id
      << ",\"primary_attacker_character_id\":null,\"primary_defender_character_id\":null"
      << ",\"finalized_selection_ready\":false,\"named_roles_ready\":false"
      << ",\"binding_kind\":\"current_cb_database_index_key\",\"declaration_id\":"
      << Quote(q.request.declaration_id) << ",\"selected_declaration\":";
  Selected(out, q.request);
  out << ",\"request_binding\":{\"ticket\":" << q.envelope.ticket.sequence
      << ",\"query_sequence\":" << q.query_sequence << ",\"capture_epoch\":" << q.capture_epoch
      << "},\"two_round_observation\":{\"round_count\":2,\"complete_dto_equal\":true,\"frame_binding_equal\":true}"
      << ",\"status_code\":" << static_cast<unsigned>(d.status)
      << ",\"root_indices\":[";
  Index(out, d.cb_root_index); out << ','; Index(out, d.on_action_root_index);
  out << "],\"on_action_definition_observed\":" << (d.on_action_definition_observed ? "true" : "false")
      << ",\"on_action_definition_known_null\":" << (d.on_action_definition_known_null ? "true" : "false")
      << ",\"callback_source_rvas\":[" << d.callback_source_rvas[0] << ',' << d.callback_source_rvas[1]
      << "],\"unresolved_helper_source_rvas\":[" << d.unresolved_helper_source_rvas[0] << ','
      << d.unresolved_helper_source_rvas[1] << ',' << d.unresolved_helper_source_rvas[2]
      << "],\"callbacks_runtime_observed\":false,\"real_war_context_observed\":false"
      << ",\"node_columns\":[\"layout\",\"status\",\"read_flags\",\"rva_flags\",\"vptr\",\"scope_kind\",\"scope_mask\",\"invoke\",\"count\",\"edge_begin\",\"edge_count\"]"
      << ",\"node_rows\":[";
  for (std::size_t i = 0; i < d.rows.size(); ++i) {
    if (i) out << ',';
    const auto &r = d.rows[i];
    std::uint32_t read_flags = 0, rva_flags = 0;
    const PrewarNodeRva12004 *rvas[]{&r.vptr, &r.scope_kind_callee, &r.scope_mask_callee, &r.invoke_callee};
    for (std::uint32_t j = 0; j < 4; ++j) {
      read_flags |= static_cast<std::uint32_t>(r.identity_read_status[j]) << (j * 3);
      if (rvas[j]->observed) rva_flags |= 1U << (j * 2);
      if (rvas[j]->in_module) rva_flags |= 1U << (j * 2 + 1);
    }
    out << '[' << static_cast<unsigned>(r.layout) << ',' << static_cast<unsigned>(r.status)
        << ',' << read_flags << ',' << rva_flags << ',';
    Rva(out, r.vptr); out << ','; Rva(out, r.scope_kind_callee); out << ',';
    Rva(out, r.scope_mask_callee); out << ','; Rva(out, r.invoke_callee); out << ',';
    if (r.child_count_observed) out << r.child_count_raw; else out << "null";
    out << ',' << r.edge_begin << ',' << r.edge_count << ']';
  }
  out << "],\"edge_columns\":[\"target_index\",\"status\"],\"ordered_edges\":[";
  for (std::size_t i = 0; i < d.ordered_edges.size(); ++i) {
    if (i) out << ',';
    out << '['; Index(out, d.ordered_edges[i].target_index);
    out << ',' << static_cast<unsigned>(d.ordered_edges[i].status) << ']';
  }
  out << "],\"limits\":{\"nodes\":128,\"edges\":128,\"depth\":16,\"read_bytes\":32768,\"read_attempts\":2048,\"wire_bytes\":8192}}";
  return out.str();
}

bool Reject(Query &q, std::string_view reason) noexcept {
  SetFailure(q.failure, reason);
  (void)ck3_12002::FinishQueryMailbox(q.envelope);
  return true;
}
bool Ready(const Query &q) noexcept {
  return q.wait_result == MainThreadQueryWaitResultV1::completed &&
      q.reclaim_result == MainThreadQueryReclaimResultV1::reclaimed && q.completed &&
      q.failure.empty() && q.envelope.frame_stable && q.observation.directory.sampled &&
      q.executor_invocations == 1 && q.capture_epoch && q.envelope.ticket.sequence &&
      q.capture_epoch == q.envelope.execution_stamp.pump_epoch &&
      q.query_sequence == q.envelope.ticket.sequence;
}
} // namespace

bool IsPrewarDeclarationNodeIdentityStep12004(std::string_view step) noexcept {
  return step == kPrewarDeclarationNodeIdentityStep12004;
}
bool ExecutePrewarDeclarationNodeIdentityMailbox12004(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &q = *static_cast<Query *>(envelope->typed_context);
  if (&q.envelope != envelope || q.executor_invocations || q.completed || envelope->entered) return false;
  try {
    if (!ck3_12002::EnterQueryMailbox(*envelope, stamp, &ExecutePrewarDeclarationNodeIdentityMailbox12004)) {
      SetFailure(q.failure, "prewar_node_identity_published_frame_changed"); return true;
    }
    ++q.executor_invocations;
    q.capture_epoch = stamp.pump_epoch;
    q.query_sequence = envelope->ticket.sequence;
    if (!q.capture_epoch || !q.query_sequence || !RequestValid(q.request) ||
        q.request.expected_native_revision != envelope->expected_snapshot_revision)
      return Reject(q, "prewar_node_identity_request_binding_invalid");
    Round first{}, second{};
    if (!ReadRound(q, first)) return Reject(q, "prewar_node_identity_first_database_or_frame_unavailable");
    game::Snapshot middle{};
    if (envelope->execution_stamp != stamp || !ck3_12002::CaptureQuerySnapshot(envelope, middle))
      return Reject(q, "prewar_node_identity_middle_frame_changed");
    if (!ReadRound(q, second)) return Reject(q, "prewar_node_identity_second_database_or_frame_unavailable");
    const auto &d = first.directory;
    if (first != second || !d.sampled || d.query_ticket != q.query_sequence ||
        d.epoch != q.capture_epoch || d.native_revision != q.request.expected_native_revision ||
        d.public_revision != q.request.expected_public_revision ||
        d.frame.date_raw != envelope->expected_snapshot.date_raw ||
        d.selection.actor_character_id != envelope->expected_snapshot.played_character_id ||
        d.selection.target_character_id != q.request.selected.target_character_id ||
        d.selection.casus_belli_index != q.request.selected.casus_belli_index ||
        d.selection.cb_key != q.request.selected.casus_belli_key ||
        d.selection.cb_config_index != q.request.selected.configuration_index ||
        d.selection.claimant_character_id != q.request.selected.claimant_character_id ||
        d.selection.selected_title_ids != q.request.selected.target_title_ids ||
        d.named_roles_ready || d.finalized_selection_ready ||
        d.participant_coverage_complete || d.war_permission)
      return Reject(q, "prewar_node_identity_complete_sample_drift");
    game::Snapshot after{};
    if (envelope->execution_stamp != stamp || !ck3_12002::CaptureQuerySnapshot(envelope, after) || after != middle)
      return Reject(q, "prewar_node_identity_final_frame_changed");
    if (!ck3_12002::FinishQueryMailbox(*envelope))
      return Reject(q, "prewar_node_identity_finish_frame_changed");
    q.observation = std::move(first);
    q.completed = true;
    return true;
  } catch (...) {
    SetFailure(q.failure, "prewar_node_identity_capture_exception");
    (void)ck3_12002::FinishQueryMailbox(*envelope);
    return false;
  }
}
bool RunPrewarDeclarationNodeIdentityMailbox12004(
    Query &q,
    std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  try {
    auto &e = q.envelope;
    if (!e.game || !e.mailbox || !e.game->enabled() || !game::IsCk3_12004Descriptor(e.game->descriptor()) ||
        e.snapshot_comparison != ck3_12002::QuerySnapshotComparison12002::full_snapshot ||
        !FrameValid(e.expected_snapshot, e.expected_snapshot_revision) ||
        q.request.expected_native_revision != e.expected_snapshot_revision || !RequestValid(q.request) ||
        !q.bindings.enabled || !ExactDeclarations(q) || e.ticket.sequence || e.entered ||
        q.executor_invocations || q.completed) {
      SetFailure(failure, "prewar_node_identity_current_request_invalid"); return false;
    }
    e.typed_context = &q;
    if (ck3_11906::TrySubmitMainThreadQueryV1(*e.mailbox, &ExecutePrewarDeclarationNodeIdentityMailbox12004,
        &e, e.ticket) != MainThreadQuerySubmitResultV1::submitted) {
      SetFailure(failure, "prewar_node_identity_mailbox_submit_unavailable"); return false;
    }
    // No throwing/allocating worker operation before terminal wait/reclaim.
    q.wait_result = ck3_11906::WaitForMainThreadQueryV1(*e.mailbox, e.ticket, 8000);
    while (q.wait_result == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      q.wait_result = ck3_11906::WaitForMainThreadQueryV1(*e.mailbox, e.ticket, 100);
    q.reclaim_result = ck3_11906::ReclaimMainThreadQueryV1(*e.mailbox, e.ticket);
    if (!Ready(q)) {
      failure = q.failure;
      SetFailure(failure, q.reclaim_result != MainThreadQueryReclaimResultV1::reclaimed
          ? "prewar_node_identity_terminal_ticket_not_reclaimed" : "prewar_node_identity_observation_unavailable");
      return false;
    }
    serialized = Serialize(q);
    return !serialized.empty();
  } catch (...) {
    serialized.clear(); SetFailure(failure, "prewar_node_identity_mailbox_exception"); return false;
  }
}
bool HandlePrewarDeclarationNodeIdentity12004(
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t native_revision,
    const Request &request, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  try {
    if (!adapter.enabled() || !game::IsCk3_12004Descriptor(adapter.descriptor()) ||
        !FrameValid(published, native_revision) || request_id.empty() ||
        request_id.size() > kMaximumRequestIdBytes || !RequestValid(request) ||
        request.expected_native_revision != native_revision) {
      SetFailure(failure, "prewar_node_identity_current_frame_or_request_unavailable"); return false;
    }
    std::ostringstream binding;
    binding << "{\"declaration_id\":" << Quote(request.declaration_id) << ",\"selected_declaration\":";
    Selected(binding, request); binding << '}';
    if (Outer(binding.str(), request_id, (std::numeric_limits<std::uint64_t>::max)(),
        (std::numeric_limits<std::uint64_t>::max)(), false).size() > kPrewarDeclarationNodeWireLimit12004) {
      SetFailure(failure, "prewar_node_identity_full_binding_exceeds_wire_budget"); return false;
    }
    Query q{};
    q.request = request;
    q.envelope.game = &ck3_12002::NativeAdapter12002(adapter);
    q.envelope.mailbox = &mailbox;
    q.envelope.expected_snapshot = published;
    q.envelope.expected_snapshot_revision = native_revision;
    q.envelope.snapshot_comparison = ck3_12002::QuerySnapshotComparison12002::full_snapshot;
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    std::size_t span = 0;
    const auto *declarations = game::BorrowOrdinaryHolyWarDeclarations12004(adapter);
    if (!declarations || !LoadedImageSize(base, span)) {
      SetFailure(failure, "prewar_node_identity_actual4_profile_or_pe_unavailable"); return false;
    }
    q.declarations = *declarations;
    const auto core = xar::ck3_12004::BindCoreImage(base, adapter.descriptor().executable_sha256);
    q.bindings = BindPrewarDeclarationNodeIdentityImage12004(
        core, base, span, adapter.descriptor().executable_sha256);
    if (!q.bindings.enabled || !ExactDeclarations(q)) {
      SetFailure(failure, "prewar_node_identity_actual4_bindings_unavailable"); return false;
    }
    std::string domain;
    if (!RunPrewarDeclarationNodeIdentityMailbox12004(q, domain, failure)) return false;
    serialized = Outer(domain, request_id, q.envelope.ticket.sequence,
        q.envelope.execution_stamp.pump_epoch, q.observation.directory.structural_capture_complete);
    // Count final escaped bytes, including request ID, receipt and full tuple.
    if (serialized.size() > kPrewarDeclarationNodeWireLimit12004) {
      serialized.clear(); SetFailure(failure, "prewar_node_identity_full_result_exceeds_wire_budget"); return false;
    }
    return true;
  } catch (...) {
    serialized.clear(); SetFailure(failure, "prewar_node_identity_handler_exception"); return false;
  }
}
} // namespace xar::ck3_12004

#endif // XAR_ENABLE_PREWAR_DECLARATION_NODE_IDENTITY_V1
