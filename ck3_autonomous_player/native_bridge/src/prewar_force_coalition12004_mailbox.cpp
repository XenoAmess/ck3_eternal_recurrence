#include "xar_bridge/prewar_force_coalition12004_mailbox.hpp"

#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_army_support.hpp"
#include "xar_bridge/ck3_12004_commands.hpp"
#include "xar_bridge/ck3_12004_family_obligations_alliance.hpp"
#include "xar_bridge/ck3_12004_military.hpp"
#include "xar_bridge/ck3_12004_war.hpp"

#include <windows.h>

#include <algorithm>
#include <limits>
#include <utility>

namespace xar::ck3_12004 {
namespace {

using ck3_11906::MainThreadQueryReclaimResultV1;
using ck3_11906::MainThreadQuerySubmitResultV1;
using ck3_11906::MainThreadQueryWaitResultV1;

void SetFailure(std::string &failure, std::string_view reason) noexcept {
  try {
    if (failure.empty()) failure.assign(reason);
  } catch (...) {
    // Allocation failure still leaves completed=false or a non-completed wait;
    // it must never turn an unread observation into an accepted wire result.
  }
}

bool FrameValid(const game::Snapshot &frame, std::uint64_t revision) noexcept {
  return revision != 0 && frame.paused && frame.map_ready &&
      frame.has_played_character && frame.played_character_alive &&
      frame.played_character_id > 0 &&
      frame.played_character_id <= (std::numeric_limits<std::int32_t>::max)() &&
      frame.date_raw >= (std::numeric_limits<std::int32_t>::min)() &&
      frame.date_raw <= (std::numeric_limits<std::int32_t>::max)();
}

bool Space(unsigned char value) noexcept {
  return value == ' ' || value == '\t' || value == '\r' || value == '\n' ||
      value == '\f' || value == '\v';
}

bool RequestValid(const PrewarForceCoalitionRequest12004 &request) {
  const auto &selected = request.selected;
  if (!request.expected_native_revision || !request.expected_public_revision ||
      selected.target_character_id <= 0 || selected.casus_belli_index < 0 ||
      selected.configuration_index < -1 || selected.claimant_character_id < -1 ||
      selected.casus_belli_key.empty() ||
      Space(static_cast<unsigned char>(selected.casus_belli_key.front())) ||
      Space(static_cast<unsigned char>(selected.casus_belli_key.back())) ||
      !std::all_of(selected.target_title_ids.begin(), selected.target_title_ids.end(),
                   [](std::int32_t id) { return id >= 0; })) return false;
  return request.declaration_id ==
      std::to_string(selected.target_character_id) + '-' +
      std::to_string(selected.casus_belli_index) + '-' +
      std::to_string(selected.configuration_index);
}

PrewarForceCoalitionMailbox12004 *OwningQuery(void *opaque) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context ||
      !ck3_12002::IsQueryOwningThread(envelope)) return nullptr;
  auto *query = static_cast<PrewarForceCoalitionMailbox12004 *>(envelope->typed_context);
  return &query->envelope == envelope ? query : nullptr;
}

void *ResolveCharacter(void *opaque, std::int32_t id) noexcept {
  auto *query = OwningQuery(opaque);
  return query && id != -1 ? ck3_12004::ResolveCoreCharacter(query->bindings.core, id) : nullptr;
}

void *ResolveUnit(void *opaque, std::int32_t id) noexcept {
  auto *query = OwningQuery(opaque);
  return query && id != -1 ? ResolveArmyUnit12004(query->bindings.armies, id) : nullptr;
}

void *ResolveProvince(void *opaque, std::int32_t id) noexcept {
  auto *query = OwningQuery(opaque);
  return query && id != -1 ? ck3_12002::ResolveObjectiveProvince(query->provinces, id) : nullptr;
}

void BindWorld(PrewarForceCoalitionMailbox12004 &query) noexcept {
  query.world = {};
  query.world.context = &query.envelope;
  query.world.read_snapshot = &ck3_12002::CaptureQuerySnapshot;
  query.world.resolve_character = &ResolveCharacter;
  query.world.resolve_unit = &ResolveUnit;
  query.world.resolve_province = &ResolveProvince;
}

bool RejectObservation(PrewarForceCoalitionMailbox12004 &query,
                       std::string_view reason) noexcept {
  SetFailure(query.failure, reason);
  // A valid domain-unavailable result is not an executor exception. No DTO is
  // serialized, and the same envelope still records its final frame verdict.
  (void)ck3_12002::FinishQueryMailbox(query.envelope);
  return true;
}

bool SerializationReady(const PrewarForceCoalitionMailbox12004 &query) noexcept {
  return query.wait_result == MainThreadQueryWaitResultV1::completed &&
      query.reclaim_result == MainThreadQueryReclaimResultV1::reclaimed &&
      query.completed && query.envelope.frame_stable && query.failure.empty() &&
      query.observation.sampled && query.executor_invocations == 1 &&
      query.envelope.ticket.sequence != 0 && query.capture_epoch != 0 &&
      query.capture_epoch == query.envelope.execution_stamp.pump_epoch &&
      query.query_sequence == query.envelope.ticket.sequence;
}

std::string_view WaitFailure(MainThreadQueryWaitResultV1 wait) noexcept {
  switch (wait) {
  case MainThreadQueryWaitResultV1::completed:
    return "prewar_force_coalition_observation_unavailable";
  case MainThreadQueryWaitResultV1::executor_failed:
    return "prewar_force_coalition_executor_failed";
  case MainThreadQueryWaitResultV1::infrastructure_failed:
    return "prewar_force_coalition_execution_boundary_drift";
  case MainThreadQueryWaitResultV1::cancelled:
    return "prewar_force_coalition_cancelled";
  case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
    return "prewar_force_coalition_timeout_before_execution";
  case MainThreadQueryWaitResultV1::timeout_executor_already_running:
    return "prewar_force_coalition_executor_still_running";
  case MainThreadQueryWaitResultV1::ticket_mismatch:
    return "prewar_force_coalition_ticket_mismatch";
  }
  return "prewar_force_coalition_wait_unavailable";
}

std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 0x20) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += static_cast<char>(c);
  }
  return out + '"';
}

} // namespace

bool IsPrewarForceCoalitionPrivateStep12004(std::string_view step) noexcept {
  return step == kPrewarForceCoalitionPrivateStep12004;
}

bool ExecutePrewarForceCoalitionMailbox12004(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<PrewarForceCoalitionMailbox12004 *>(envelope->typed_context);
  if (&query.envelope != envelope || query.executor_invocations != 0 ||
      query.completed || envelope->entered) return false;
  try {
    if (!ck3_12002::EnterQueryMailbox(*envelope, stamp,
                                    &ExecutePrewarForceCoalitionMailbox12004)) {
      SetFailure(query.failure, "prewar_force_coalition_published_frame_changed");
      return true;
    }
    ++query.executor_invocations;
    query.capture_epoch = stamp.pump_epoch;
    query.query_sequence = envelope->ticket.sequence;
    if (!query.capture_epoch || !query.query_sequence ||
        query.request.expected_native_revision != envelope->expected_snapshot_revision ||
        !RequestValid(query.request))
      return RejectObservation(query, "prewar_force_coalition_request_binding_invalid");

    PrewarForceCoalitionSample12004 first{}, second{};
    if (!ReadPrewarForceCoalitionSample12004(query.bindings, query.request,
                                            *envelope, query.world, first, query.failure))
      return RejectObservation(query, "prewar_force_coalition_first_sample_unavailable");
    game::Snapshot middle{};
    if (envelope->execution_stamp != stamp ||
        !ck3_12002::CaptureQuerySnapshot(envelope, middle))
      return RejectObservation(query, "prewar_force_coalition_middle_frame_changed");

    if (!ReadPrewarForceCoalitionSample12004(query.bindings, query.request,
                                            *envelope, query.world, second, query.failure))
      return RejectObservation(query, "prewar_force_coalition_second_sample_unavailable");
    if (!first.sampled || !second.sampled || first.selected != query.request.selected ||
        second.selected != query.request.selected || first != second)
      return RejectObservation(query, "prewar_force_coalition_complete_sample_drift");
    game::Snapshot after{};
    if (envelope->execution_stamp != stamp ||
        !ck3_12002::CaptureQuerySnapshot(envelope, after) || after != middle)
      return RejectObservation(query, "prewar_force_coalition_final_frame_changed");
    if (!ck3_12002::FinishQueryMailbox(*envelope))
      return RejectObservation(query, "prewar_force_coalition_finish_frame_changed");

    query.observation = std::move(first);
    query.completed = true;
    // The mailbox drain independently re-reads the actual execution stamp at
    // this same pump_epoch after returning; Run also requires completed wait.
    return true;
  } catch (...) {
    SetFailure(query.failure, "prewar_force_coalition_capture_exception");
    (void)ck3_12002::FinishQueryMailbox(*envelope);
    return false;
  }
}

bool RunPrewarForceCoalitionMailbox12004(
    PrewarForceCoalitionMailbox12004 &query,
    std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox || !envelope.game->enabled() ||
        !game::IsCk3_12004Descriptor(envelope.game->descriptor()) ||
        envelope.snapshot_comparison != ck3_12002::QuerySnapshotComparison12002::full_snapshot ||
        !FrameValid(envelope.expected_snapshot, envelope.expected_snapshot_revision) ||
        query.request.expected_native_revision != envelope.expected_snapshot_revision ||
        !RequestValid(query.request) || envelope.ticket.sequence != 0 ||
        envelope.entered || query.executor_invocations != 0 || query.completed) {
      SetFailure(failure, "prewar_force_coalition_current_request_invalid"); return false;
    }
    envelope.typed_context = &query;
    BindWorld(query);
    if (ck3_11906::TrySubmitMainThreadQueryV1(*envelope.mailbox,
        &ExecutePrewarForceCoalitionMailbox12004, &envelope, envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      SetFailure(failure, "prewar_force_coalition_mailbox_submit_unavailable"); return false;
    }
    // No allocating or throwing worker operation intervenes between submit
    // and terminal reclaim. An executing callback owns all query storage.
    query.wait_result = ck3_11906::WaitForMainThreadQueryV1(
        *envelope.mailbox, envelope.ticket, 8000);
    while (query.wait_result == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      query.wait_result = ck3_11906::WaitForMainThreadQueryV1(
          *envelope.mailbox, envelope.ticket, 100);
    query.reclaim_result = ck3_11906::ReclaimMainThreadQueryV1(
        *envelope.mailbox, envelope.ticket);
    if (!SerializationReady(query)) {
      failure = query.failure;
      SetFailure(failure, query.reclaim_result != MainThreadQueryReclaimResultV1::reclaimed
          ? "prewar_force_coalition_terminal_ticket_not_reclaimed" : WaitFailure(query.wait_result));
      return false;
    }
    serialized = SerializePrewarForceCoalition12004(
        query.observation, query.request, query.capture_epoch,
        envelope.ticket.sequence, query.query_sequence,
        static_cast<std::int32_t>(envelope.expected_snapshot.date_raw),
        static_cast<std::int32_t>(envelope.expected_snapshot.played_character_id));
    if (!serialized.empty()) return true;
    SetFailure(failure, "prewar_force_coalition_serialization_unavailable"); return false;
  } catch (...) {
    serialized.clear();
    SetFailure(failure, "prewar_force_coalition_mailbox_exception"); return false;
  }
}

bool HandlePrewarForceCoalitionPrivate12004(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t native_revision,
    const PrewarForceCoalitionRequest12004 &request,
    std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  try {
    if (!adapter.enabled() || !game::IsCk3_12004Descriptor(adapter.descriptor()) ||
        !FrameValid(published, native_revision) || request_id.empty() ||
        request.expected_native_revision != native_revision || !RequestValid(request)) {
      SetFailure(failure, "prewar_force_coalition_current_frame_unavailable"); return false;
    }
    PrewarForceCoalitionMailbox12004 query{};
    query.request = request;
    query.envelope.game = &ck3_12002::NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = native_revision;
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    const auto sha = adapter.descriptor().executable_sha256;
    query.commands = BindCommandImage12004(base, sha);
    query.bindings.core = BindCoreImage(base, sha);
    query.bindings.armies = BindArmyImage12004(base, sha);
    query.provinces = BindProvinceImage12004(base, sha, query.bindings.armies);
    query.bindings.military = BindMilitaryImage12004(base, sha, query.commands);
    query.bindings.reserve = BindPlayerArmyReserveImage12004V1(base, sha);
    query.bindings.alliance = BindFamilyObligationsAllianceImage(base, sha);
    query.bindings.war_entry = BindWarEntryNativeEnvironment12004(base, sha);
    if (!base || !query.commands.enabled || !query.bindings.core.enabled ||
        !query.bindings.armies.enabled || !query.provinces.enabled ||
        !query.bindings.military.enabled || !query.bindings.reserve.enabled ||
        !query.bindings.alliance.enabled ||
        !IsWarEntryNativeEnvironment12004(query.bindings.war_entry)) {
      SetFailure(failure, "prewar_force_coalition_actual4_bindings_unavailable"); return false;
    }
    std::string domain;
    if (!RunPrewarForceCoalitionMailbox12004(query, domain, failure)) return false;
    // This independent receipt is built from actual native query fields. The
    // domain string is opaque here; no identity is parsed or copied from it.
    const auto ticket = query.envelope.ticket.sequence;
    const auto epoch = query.envelope.execution_stamp.pump_epoch;
    const auto sequence = ticket;
    serialized = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
        ",\"ok\":true,\"execution_receipt\":{\"ticket\":" + std::to_string(ticket) +
        ",\"query_sequence\":" + std::to_string(sequence) +
        ",\"capture_epoch\":" + std::to_string(epoch) + "},\"result\":{\"step\":" +
        Quote(kPrewarForceCoalitionPrivateStep12004) +
        ",\"accepted\":true,\"status\":\"available_partial\",\"private_build\":true," +
        "\"read_only\":true,\"advertised\":false,\"domain_key\":" +
        Quote(kPrewarForceCoalitionDomainKey12004) +
        ",\"prewar_force_coalition_coverage\":" + domain + "}}";
    return true;
  } catch (...) {
    serialized.clear();
    SetFailure(failure, "prewar_force_coalition_handler_exception"); return false;
  }
}

} // namespace xar::ck3_12004
