#include "xar_bridge/religion_reform12002_ai_inputs_mailbox.hpp"

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <windows.h>
#include <utility>

namespace xar::ck3_12002 {
namespace {
std::string Quote(std::string_view text) {
  static constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : text) {
    if (byte == '"' || byte == '\\') { out += '\\'; out += static_cast<char>(byte); }
    else if (byte < 0x20) { out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15]; }
    else out += static_cast<char>(byte);
  }
  return out + '"';
}
bool HasField(std::string_view payload, std::string_view name) {
  return payload.find('"' + std::string(name) + '"') != std::string_view::npos;
}
bool ValidFrame(const game::Snapshot &frame, std::uint64_t revision) noexcept {
  return revision != 0 && frame.paused && frame.map_ready &&
      frame.has_played_character && frame.played_character_alive &&
      frame.played_character_id > 0;
}

bool ContextObserved(religion_reform::AIContextStatus status) noexcept {
  return status == religion_reform::AIContextStatus::observed_no_ai ||
      status == religion_reform::AIContextStatus::observed_controllers;
}
const char *ContextStatusKey(religion_reform::AIContextStatus status) noexcept {
  using Status = religion_reform::AIContextStatus;
  switch (status) {
  case Status::bindings_unavailable: return "bindings_unavailable";
  case Status::actor_unavailable: return "actor_unavailable";
  case Status::container_unavailable: return "container_unavailable";
  case Status::observed_no_ai: return "observed_no_ai";
  case Status::observed_controllers: return "observed_controllers";
  }
  return "bindings_unavailable";
}
const char *ScheduleStatusKey(religion_reform::ScheduleStatus status) noexcept {
  using Status = religion_reform::ScheduleStatus;
  switch (status) {
  case Status::bindings_unavailable: return "bindings_unavailable";
  case Status::actor_unavailable: return "actor_unavailable";
  case Status::configuration_unavailable: return "configuration_unavailable";
  case Status::observed: return "observed";
  }
  return "bindings_unavailable";
}
const char *ScheduleAIStatusKey(religion_reform::ScheduleAIStatus status) noexcept {
  using Status = religion_reform::ScheduleAIStatus;
  switch (status) {
  case Status::not_supplied: return "not_supplied";
  case Status::actor_mismatch: return "actor_mismatch";
  case Status::invalid_state: return "invalid_state";
  case Status::gates_only: return "gates_only";
  case Status::observed: return "observed";
  }
  return "not_supplied";
}
bool ScheduleCacheObserved(const religion_reform::ScheduleInputs &value) noexcept {
  return value.status == religion_reform::ScheduleStatus::observed &&
      (value.ai_status == religion_reform::ScheduleAIStatus::gates_only ||
       value.ai_status == religion_reform::ScheduleAIStatus::observed);
}
bool ReadAIInputsOnce(const PlayerReligionAIReformInputsBindings12002 &bindings,
    std::uint64_t epoch, PlayerReligionAIReformInputsObservation12002 &out) {
  CoreSnapshotPrefix before{};
  if (!bindings.core.enabled) return false;
  if (!ReadCoreSnapshot(bindings.core, before) || !before.map_ready ||
      !before.has_played_character || !before.played_character_alive) {
    out.failure = "played_character_unavailable"; return false;
  }
  out.capture_epoch = epoch;
  out.date_raw = before.clock.date_raw;
  out.played_character_id = before.played_character_id;
  if (!before.clock.paused) { out.failure = "frame_not_paused"; return false; }
  auto *actor = ResolveCoreCharacter(bindings.core, before.played_character_id);
  if (!actor) { out.failure = "played_character_unavailable"; return false; }
  const auto id = static_cast<std::uint32_t>(before.played_character_id);
  out.context = religion_reform::ReadActorReformAIContext12002(bindings.context, actor, id);
  // This real actor/global read deliberately supplies no AI. The original
  // not_supplied status describes a base observation, not a missing controller.
  out.schedule_base = religion_reform::ReadReformScheduleInputs12002(
      bindings.schedule, actor, id, nullptr);
  for (std::size_t index = 0; index < out.context.controllers.size(); ++index) {
    const auto &controller = out.context.controllers[index];
    PlayerReligionAIReformControllerInputs12002 row{};
    row.context_index = static_cast<std::uint32_t>(index);
    row.schedule = religion_reform::ReadReformScheduleInputs12002(
        bindings.schedule, actor, id, controller.actual_ai);
    out.controller_inputs.push_back(row);
  }
  if (out.context.status == religion_reform::AIContextStatus::observed_no_ai) {
    out.gate_inputs_observation_complete = true;
  } else if (out.context.status == religion_reform::AIContextStatus::observed_controllers) {
    out.gate_inputs_observation_complete = !out.controller_inputs.empty();
    for (const auto &row : out.controller_inputs)
      out.gate_inputs_observation_complete =
          out.gate_inputs_observation_complete && ScheduleCacheObserved(row.schedule);
  }
  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(bindings.core, after) || !after.map_ready ||
      !after.has_played_character || !after.played_character_alive || !after.clock.paused ||
      after.clock.date_raw != before.clock.date_raw ||
      after.played_character_id != before.played_character_id ||
      ResolveCoreCharacter(bindings.core, before.played_character_id) != actor) {
    out.failure = "state_changed"; return false;
  }
  out.available = ContextObserved(out.context.status) ||
      out.schedule_base.status == religion_reform::ScheduleStatus::observed;
  out.failure = out.available ? "none" : "actual_ai_inputs_unavailable";
  return out.available;
}
bool ReadAIInputsGuarded(const PlayerReligionAIReformInputsBindings12002 &bindings,
    std::uint64_t epoch, PlayerReligionAIReformInputsObservation12002 &out) {
#if defined(_WIN32) && defined(_MSC_VER)
  __try { return ReadAIInputsOnce(bindings, epoch, out); }
  __except (1) { out.failure = "native_observation_unavailable"; return false; }
#else
  return ReadAIInputsOnce(bindings, epoch, out);
#endif
}
bool ReadAIInputs(const PlayerReligionAIReformInputsBindings12002 &bindings,
    std::uint64_t epoch, PlayerReligionAIReformInputsObservation12002 &out) {
  out = {};
  out.capture_epoch = epoch;
  PlayerReligionAIReformInputsObservation12002 candidate{};
  candidate.capture_epoch = epoch;
  if (!ReadAIInputsGuarded(bindings, epoch, candidate)) {
    out.failure = std::move(candidate.failure);
    out.date_raw = candidate.date_raw;
    out.played_character_id = candidate.played_character_id;
    return false;
  }
  out = std::move(candidate);
  return true;
}
std::string Boolean(bool value) { return value ? "true" : "false"; }
std::string KnownBoolean(bool known, bool value) { return known ? Boolean(value) : "null"; }
std::string KnownNumber(bool known, std::int64_t value) {
  return known ? std::to_string(value) : "null";
}
std::string SerializeSchedule(const religion_reform::ScheduleInputs &value) {
  const bool actor_read = value.status == religion_reform::ScheduleStatus::observed ||
      value.status == religion_reform::ScheduleStatus::configuration_unavailable;
  const bool configuration_read = value.status == religion_reform::ScheduleStatus::observed;
  const bool cache_read = ScheduleCacheObserved(value);
  const bool timer_read = configuration_read &&
      value.ai_status == religion_reform::ScheduleAIStatus::observed;
  return "{\"status\":" + Quote(ScheduleStatusKey(value.status)) +
      ",\"ai_status\":" + Quote(ScheduleAIStatusKey(value.ai_status)) +
      ",\"current_actor\":{\"actor_id\":" +
      KnownNumber(value.actor_id != 0xFFFFFFFFU, value.actor_id) +
      ",\"highest_tier\":" + KnownNumber(actor_read, value.highest_tier) +
      ",\"current_independent_ruler\":" + KnownBoolean(actor_read, value.current_independent_ruler) +
      "},\"native_globals\":{\"reformation_enabled\":" + KnownBoolean(actor_read, value.reformation_enabled) +
      ",\"rare_period_prepare_ticks\":" + KnownNumber(configuration_read, value.rare_period) +
      "},\"actual_ai_cache\":{\"available\":" + Boolean(cache_read) +
      ",\"ai_government_flags\":" + KnownNumber(cache_read, value.ai_government_flags) +
      ",\"ai_independent_flags\":" + KnownNumber(cache_read, value.ai_independent_flags) +
      ",\"ai_active_raw\":" + KnownNumber(cache_read, value.ai_active) +
      ",\"ai_special_raw\":" + KnownNumber(cache_read, value.ai_special) +
      ",\"cached_independent_ruler\":" + KnownBoolean(cache_read, value.cached_independent_ruler) +
      ",\"cached_government_bit6\":" + KnownBoolean(cache_read, value.cached_government_bit6) +
      ",\"handler_cache_gates_pass\":" + KnownBoolean(cache_read, value.handler_cache_gates_pass) +
      "},\"actual_ai_timer\":{\"available\":" + Boolean(timer_read) +
      ",\"rare_countdown_prepare_ticks\":" + KnownNumber(timer_read, value.rare_countdown_prepare_ticks) +
      ",\"rare_selected_raw\":" + KnownNumber(timer_read, value.rare_selected_raw) +
      ",\"units\":\"prepare_invocations\"}}";
}
std::string SerializeAIInputs(const PlayerReligionAIReformInputsObservation12002 &value) {
  const bool context_read = ContextObserved(value.context.status);
  std::string rows = context_read ? "[" : "null";
  if (context_read) {
    for (const auto &row : value.controller_inputs) {
      if (rows.size() > 1) rows += ',';
      const auto &controller = value.context.controllers[row.context_index];
      rows += "{\"context_index\":" + std::to_string(row.context_index) +
          ",\"kind\":" + Quote(controller.kind == religion_reform::AIControllerKind::ordinary
              ? "ordinary" : "player_special") +
          ",\"active_raw\":" + std::to_string(controller.active_raw) +
          ",\"special_raw\":" + std::to_string(controller.special_raw) +
          ",\"schedule\":" + SerializeSchedule(row.schedule) + '}';
    }
    rows += ']';
  }
  return "{\"schema\":\"ck3_12002_player_religion_ai_reform_inputs_v1\",\"available\":" +
      Boolean(value.available) + ",\"unavailable_reason\":" +
      (value.available ? "null" : Quote(value.failure)) +
      ",\"capture_epoch\":" + std::to_string(value.capture_epoch) +
      ",\"date_raw\":" + std::to_string(value.date_raw) +
      ",\"played_character_id\":" + std::to_string(value.played_character_id) +
      ",\"context_status\":" + Quote(ContextStatusKey(value.context.status)) +
      ",\"controller_count\":" + KnownNumber(context_read,
          static_cast<std::int64_t>(value.context.controllers.size())) +
      ",\"gate_inputs_observation_complete\":" + Boolean(value.gate_inputs_observation_complete) +
      ",\"controller_absence\":" + (value.context.status == religion_reform::AIContextStatus::observed_no_ai
          ? Quote("no_actual_controller") : "null") +
      ",\"context\":" + religion_reform::SerializeActorReformAIContext12002(value.context) +
      ",\"schedule_base\":" + SerializeSchedule(value.schedule_base) +
      ",\"controllers\":" + rows + '}';
}
} // namespace

bool IsPlayerReligionAIReformInputsPrivateStep12002(std::string_view step) noexcept {
  return step == kPlayerReligionAIReformInputsPrivateStep12002;
}

bool ParsePlayerReligionAIReformInputsRevision12002(std::string_view payload,
                                               std::uint64_t &revision) noexcept {
  revision = 0;
  try {
    std::uint64_t alias = 0;
    const bool canonical_present = HasField(payload, "expected_snapshot_revision");
    const bool alias_present = HasField(payload, "expected_revision");
    if (canonical_present && (!bridge::JsonUnsignedField(payload,
        "expected_snapshot_revision", revision) || revision == 0)) return false;
    if (alias_present && (!bridge::JsonUnsignedField(payload,
        "expected_revision", alias) || alias == 0)) return false;
    if (canonical_present && alias_present && revision != alias) return false;
    if (!canonical_present) revision = alias;
    return true;
  } catch (...) { revision = 0; return false; }
}

bool ExecutePlayerReligionAIReformInputsMailbox12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<PlayerReligionAIReformInputsMailboxContext12002 *>(envelope->typed_context);
  try {
    if (!EnterQueryMailbox(*envelope, stamp, &ExecutePlayerReligionAIReformInputsMailbox12002)) {
      query.failure = "player_religion_ai_reform_inputs_published_frame_changed";
      return true;
    }
    (void)ReadAIInputs(
        query.bindings, stamp.pump_epoch, query.observation);
    auto &out = query.observation;
    const auto &frame = envelope->expected_snapshot;
    if (out.available &&
        (out.played_character_id != static_cast<std::int32_t>(frame.played_character_id) ||
         out.date_raw != frame.date_raw)) {
      out = {};
      out.failure = "published_frame_changed";
      out.capture_epoch = stamp.pump_epoch;
    }
    if (!out.available) {
      // These are the actual published-frame identifiers whose read failed;
      // missing selected slots, draft groups and native gates are not filled.
      out.date_raw = static_cast<std::int32_t>(frame.date_raw);
      out.played_character_id = static_cast<std::int32_t>(frame.played_character_id);
    }
    query.completed = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) {
    query.failure = "player_religion_ai_reform_inputs_native_capture_exception";
    return false;
  }
}

std::string SerializePlayerReligionAIReformInputsResult12002(
    const PlayerReligionAIReformInputsMailboxContext12002 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kPlayerReligionAIReformInputsPrivateStep12002) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"domain_key\":" + Quote(kPlayerReligionAIReformInputsDomainKey12002) +
      ",\"backend_id\":" + Quote(kPlayerReligionAIReformInputsBackend12002) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"player_religion_ai_reform_inputs\":" +
      SerializeAIInputs(query.observation) + "}}";
}

bool RunPlayerReligionAIReformInputsMailbox12002(PlayerReligionAIReformInputsMailboxContext12002 &query,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox ||
        !ValidFrame(envelope.expected_snapshot, envelope.expected_snapshot_revision)) {
      failure = "player_religion_ai_reform_inputs_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox,
        &ExecutePlayerReligionAIReformInputsMailbox12002, &envelope, envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "player_religion_ai_reform_inputs_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "player_religion_ai_reform_inputs_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = SerializePlayerReligionAIReformInputsResult12002(query, request_id);
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "player_religion_ai_reform_inputs_serialization_unavailable" : query.failure;
    return false;
  } catch (...) {
    serialized.clear(); failure = "player_religion_ai_reform_inputs_mailbox_exception"; return false;
  }
}

bool HandlePlayerReligionAIReformInputsPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerReligionAIReformInputsPrivateStep12002(step)) {
    failure = "player_religion_ai_reform_inputs_step_unavailable"; return false;
  }
  std::uint64_t expected = 0;
  if (!ParsePlayerReligionAIReformInputsRevision12002(payload, expected)) {
    failure = "player_religion_ai_reform_inputs_request_invalid"; return false;
  }
  if (!adapter.enabled() || adapter.descriptor().game_version != "1.20.0.2" ||
      adapter.descriptor().executable_sha256 != kExecutableSha256 ||
      !ValidFrame(published, revision) || (expected != 0 && expected != revision)) {
    failure = "player_religion_ai_reform_inputs_current_frame_unavailable"; return false;
  }
  try {
    PlayerReligionAIReformInputsMailboxContext12002 query{};
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    const auto sha = adapter.descriptor().executable_sha256;
    query.bindings.core = BindCoreImage(base, sha);
    query.bindings.context = religion_reform::BindReformAIContextImage12002(base, sha);
    query.bindings.schedule = religion_reform::BindReformScheduleImage12002(base, sha);
    return RunPlayerReligionAIReformInputsMailbox12002(query, request_id, serialized, failure);
  } catch (...) { failure = "player_religion_ai_reform_inputs_handler_exception"; return false; }
}
} // namespace xar::ck3_12002
#endif
