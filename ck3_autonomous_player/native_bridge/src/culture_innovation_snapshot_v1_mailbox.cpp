#include "xar_bridge/culture_innovation_snapshot_v1_mailbox.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <charconv>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

template <std::size_t Size>
std::string_view Fixed(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  return end == value.end()
             ? std::string_view{}
             : std::string_view(value.data(),
                                static_cast<std::size_t>(end - value.begin()));
}

template <std::size_t Size>
bool AssignFixed(std::string_view value,
                 std::array<char, Size> &output) noexcept {
  output.fill('\0');
  if (value.empty() || value.size() >= Size) return false;
  std::copy(value.begin(), value.end(), output.begin());
  return true;
}

template <typename Value>
void AppendNumber(std::string &output, Value value) {
  std::array<char, 32> buffer{};
  const auto encoded =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (encoded.ec == std::errc{}) {
    output.append(buffer.data(), encoded.ptr);
  }
}

void AppendJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(character));
    } else if (character < 0x20U) {
      output += "\\u00";
      output.push_back(hex[(character >> 4U) & 0x0FU]);
      output.push_back(hex[character & 0x0FU]);
    } else {
      output.push_back(static_cast<char>(character));
    }
  }
  output.push_back('"');
}

bool MakeSnapshotId(std::uint64_t revision,
                    std::array<char,
                               game::kCultureInnovationSnapshotIdCapacityV1>
                        &output) noexcept {
  output.fill('\0');
  constexpr std::string_view prefix = "native:";
  std::copy(prefix.begin(), prefix.end(), output.begin());
  const auto encoded = std::to_chars(
      output.data() + prefix.size(), output.data() + output.size() - 1,
      revision);
  return revision != 0 && encoded.ec == std::errc{};
}

bool ReadBoundSnapshot(void *opaque, game::Snapshot &output) noexcept {
  const auto *query =
      static_cast<const CultureInnovationMailboxContextV1 *>(opaque);
  return query != nullptr && ReadSnapshot(query->bindings, output);
}

bool ResolveBoundPlayer(void *opaque, std::int32_t player_character_id,
                        std::uintptr_t &played_character) noexcept {
  auto *query = static_cast<CultureInnovationMailboxContextV1 *>(opaque);
  return query != nullptr &&
      ResolveExactBuildCultureInnovationPlayedCharacterV1(
          query->source, player_character_id, played_character);
}

bool IsExecutingExactMailboxSlot(
    const CultureInnovationMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.request.expected_public_revision == 0 ||
      query.request.expected_native_revision == 0 ||
      query.request.expected_snapshot_id.empty() || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0 ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0 ||
      stamp.game_state == 0 || GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *query.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
      !mailbox.stop_requested.load(std::memory_order_acquire) &&
      mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
      mailbox.published_sequence.load(std::memory_order_acquire) ==
          query.ticket.sequence &&
      mailbox.owner_thread_id.load(std::memory_order_acquire) ==
          stamp.thread_id &&
      mailbox.paused_owner_verified_pump_epochs.load(
          std::memory_order_acquire) >=
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
      mailbox.executor == &ExecuteCultureInnovationMailboxQueryV1 &&
      mailbox.executor_context ==
          const_cast<CultureInnovationMailboxContextV1 *>(&query);
}

struct AccessProxyV1 {
  CultureInnovationMailboxContextV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool ProxyIsMainThread(void *opaque) noexcept {
  const auto *proxy = static_cast<const AccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
      proxy->stamp != nullptr &&
      IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp);
}

bool ProxyCaptureFrame(void *opaque,
                       CultureInnovationSnapshotFrameV1 &output) noexcept {
  const auto *proxy = static_cast<const AccessProxyV1 *>(opaque);
  if (proxy == nullptr || proxy->query == nullptr || proxy->stamp == nullptr ||
      !IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp)) {
    return false;
  }
  auto &query = *proxy->query;
  game::Snapshot snapshot{};
  if (query.read_snapshot == nullptr ||
      !query.read_snapshot(query.snapshot_context, snapshot) ||
      snapshot != query.expected_snapshot || !snapshot.paused ||
      snapshot.date_raw != proxy->stamp->date_raw ||
      !snapshot.map_ready || !snapshot.has_played_character ||
      !snapshot.played_character_alive ||
      snapshot.played_character_id !=
          query.request.expected_player_character_id) {
    return false;
  }
  std::uintptr_t played_character = 0;
  if (query.resolve_player == nullptr ||
      !query.resolve_player(query.snapshot_context,
                            snapshot.played_character_id,
                            played_character) ||
      played_character == 0) {
    query.source_failure = query.source.last_failure;
    return false;
  }
  query.source_failure = CultureInnovationSourceAdapterFailureV1::none;
  output = {};
  if (!AssignFixed(query.request.expected_snapshot_id,
                   output.snapshot_id)) {
    return false;
  }
  output.public_revision = query.request.expected_public_revision;
  output.native_revision = query.request.expected_native_revision;
  output.proof_epoch = proxy->stamp->pump_epoch;
  output.date_raw = snapshot.date_raw;
  output.paused = snapshot.paused;
  output.map_ready = snapshot.map_ready;
  output.has_played_character = snapshot.has_played_character;
  output.played_character_alive = snapshot.played_character_alive;
  output.played_character_id = snapshot.played_character_id;
  output.played_character = played_character;
  output.played_character_identity_round_trip = true;
  return true;
}

bool ProxyReadSource(void *opaque, std::uintptr_t played_character,
                     CultureInnovationSourceSampleV1 &output) noexcept {
  auto *proxy = static_cast<AccessProxyV1 *>(opaque);
  if (proxy == nullptr || proxy->query == nullptr || proxy->stamp == nullptr ||
      proxy->query->read_source == nullptr ||
      !IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp)) {
    return false;
  }
  const bool read = proxy->query->read_source(
      &proxy->query->source, played_character, output);
  proxy->query->source_failure = proxy->query->source.last_failure;
  return read;
}

void BindTerminalIdentity(CultureInnovationMailboxContextV1 &query,
                          const MainThreadExecutionStampV1 &stamp) noexcept {
  auto &result = query.execution_result;
  if (Fixed(result.snapshot_id).empty()) {
    (void)AssignFixed(query.request.expected_snapshot_id,
                      result.snapshot_id);
  }
  (void)AssignFixed(kCultureInnovationSnapshotGameVersionV1,
                    result.game_build);
  (void)AssignFixed(kCultureInnovationSnapshotExecutableSha256V1,
                    result.executable_sha256);
  result.public_revision = query.request.expected_public_revision;
  result.native_revision = query.request.expected_native_revision;
  result.proof_epoch = stamp.pump_epoch;
  result.date_raw = query.request.expected_date_raw;
  result.player_character_id = query.request.expected_player_character_id;
}

void MakeInfrastructureUnavailable(
    CultureInnovationAsyncPrivateProbeV1 &probe,
    CultureInnovationAsyncFailureV1 failure) noexcept {
  auto &query = probe.query;
  query.execution_result = {};
  query.execution_result.status =
      game::CultureInnovationSnapshotStatusV1::unavailable;
  query.execution_result.unavailable_reason =
      game::CultureInnovationSnapshotFailureV1::native_bindings_unavailable;
  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = query.mailbox == nullptr
                         ? 0
                         : query.mailbox->pump_epochs.load(
                               std::memory_order_acquire);
  BindTerminalIdentity(query, stamp);
  probe.terminal_result = query.execution_result;
  probe.terminal_source_failure = query.source.last_failure;
  probe.async_failure = failure;
  probe.state = CultureInnovationAsyncStateV1::infrastructure_failed;
  probe.terminal_published = true;
}

bool IsTerminalMailboxState(MainThreadQueryMailboxStateV1 state) noexcept {
  return state == MainThreadQueryMailboxStateV1::completed ||
      state == MainThreadQueryMailboxStateV1::executor_failed ||
      state == MainThreadQueryMailboxStateV1::infrastructure_failed ||
      state == MainThreadQueryMailboxStateV1::cancelled;
}

MainThreadQueryWaitResultV1 ClassifyWait(
    MainThreadQueryMailboxStateV1 state) noexcept {
  switch (state) {
  case MainThreadQueryMailboxStateV1::completed:
    return MainThreadQueryWaitResultV1::completed;
  case MainThreadQueryMailboxStateV1::executor_failed:
    return MainThreadQueryWaitResultV1::executor_failed;
  case MainThreadQueryMailboxStateV1::infrastructure_failed:
    return MainThreadQueryWaitResultV1::infrastructure_failed;
  case MainThreadQueryMailboxStateV1::cancelled:
    return MainThreadQueryWaitResultV1::cancelled;
  default:
    return MainThreadQueryWaitResultV1::ticket_mismatch;
  }
}

void AppendStableKey(std::string &output,
                     const game::CultureInnovationStableKeyV1 &key) {
  AppendJsonString(output, CultureInnovationStableKeyViewV1(key));
}

void AppendTerminalSnapshot(
    std::string &output,
    const game::CultureInnovationSnapshotV1 &snapshot) {
  output += "{\"status\":";
  AppendJsonString(
      output,
      snapshot.status == game::CultureInnovationSnapshotStatusV1::available
          ? "available"
          : "unavailable");
  output += ",\"unavailable_reason\":";
  if (snapshot.unavailable_reason ==
      game::CultureInnovationSnapshotFailureV1::none) {
    output += "null";
  } else {
    AppendJsonString(output, CultureInnovationSnapshotFailureKeyV1(
                                 snapshot.unavailable_reason));
  }
  output += ",\"snapshot_id\":";
  AppendJsonString(output, Fixed(snapshot.snapshot_id));
  output += ",\"game_build\":";
  AppendJsonString(output, Fixed(snapshot.game_build));
  output += ",\"executable_sha256\":";
  AppendJsonString(output, Fixed(snapshot.executable_sha256));
  output += ",\"public_revision\":";
  AppendNumber(output, snapshot.public_revision);
  output += ",\"native_revision\":";
  AppendNumber(output, snapshot.native_revision);
  output += ",\"proof_epoch\":";
  AppendNumber(output, snapshot.proof_epoch);
  output += ",\"date_raw\":";
  AppendNumber(output, snapshot.date_raw);
  output += ",\"player_character_id\":";
  AppendNumber(output, snapshot.player_character_id);
  output += ",\"readiness\":{\"culture_identity\":";
  output += snapshot.readiness.culture_identity_ready ? "true" : "false";
  output += ",\"culture_head\":";
  output += snapshot.readiness.culture_head_ready ? "true" : "false";
  output += ",\"fascination\":";
  output += snapshot.readiness.fascination_ready ? "true" : "false";
  output += ",\"eras\":";
  output += snapshot.readiness.era_collection_ready ? "true" : "false";
  output += ",\"innovations\":";
  output += snapshot.readiness.innovation_collection_ready ? "true" : "false";
  output += ",\"same_frame\":";
  output += snapshot.readiness.same_frame_ready ? "true" : "false";
  output += "},\"state\":";
  if (snapshot.status !=
      game::CultureInnovationSnapshotStatusV1::available) {
    output += "null}";
    return;
  }
  const auto &state = snapshot.state;
  output += "{\"culture_id\":";
  AppendNumber(output, state.culture_id);
  output += ",\"culture_head_presence\":";
  AppendNumber(output, static_cast<std::uint32_t>(
                           state.culture_head_presence));
  output += ",\"culture_head_character_id\":";
  AppendNumber(output, state.culture_head_character_id);
  output += ",\"is_player_culture_head\":";
  output += state.is_player_culture_head ? "true" : "false";
  output += ",\"fascination_presence\":";
  AppendNumber(output, static_cast<std::uint32_t>(
                           state.fascination_presence));
  output += ",\"current_fascination\":";
  if (state.fascination_presence ==
      game::CultureInnovationPresenceV1::present) {
    AppendStableKey(output, state.current_fascination_key);
  } else {
    output += "null";
  }
  output += ",\"eras\":[";
  for (std::uint32_t index = 0; index < state.era_count; ++index) {
    if (index != 0) output.push_back(',');
    output += "{\"key\":";
    AppendStableKey(output, state.eras[index].key);
    output += ",\"progress_raw\":";
    AppendNumber(output, state.eras[index].progress_raw);
    output.push_back('}');
  }
  output += "],\"innovations\":[";
  for (std::uint32_t index = 0; index < state.innovation_count; ++index) {
    if (index != 0) output.push_back(',');
    const auto &row = state.innovations[index];
    output += "{\"key\":";
    AppendStableKey(output, row.key);
    output += ",\"era_key\":";
    AppendStableKey(output, row.era_key);
    output += ",\"group_key\":";
    AppendStableKey(output, row.group_key);
    output += ",\"skill_key\":";
    AppendStableKey(output, row.skill_key);
    output += ",\"progress_raw\":";
    AppendNumber(output, row.progress_raw);
    output += ",\"is_active\":";
    output += row.is_active ? "true" : "false";
    output += ",\"can_gain_progress\":";
    output += row.can_gain_progress ? "true" : "false";
    output += ",\"can_be_fascination\":";
    output += row.can_be_fascination ? "true" : "false";
    output += ",\"is_fascination\":";
    output += row.is_fascination ? "true" : "false";
    output += ",\"has_spread_marker\":";
    output += row.has_spread_marker ? "true" : "false";
    output.push_back('}');
  }
  output += "]}}";
}

} // namespace

bool PrepareCultureInnovationMailboxQueryV1(
    CultureInnovationMailboxContextV1 &query, const Bindings &bindings,
    std::uintptr_t module_base, const game::Snapshot &snapshot,
    std::uint64_t public_revision,
    std::uint64_t native_revision) noexcept {
  if (!bindings.enabled || module_base == 0 || public_revision == 0 ||
      native_revision == 0 || !snapshot.paused || !snapshot.map_ready ||
      !snapshot.has_played_character || !snapshot.played_character_alive ||
      snapshot.played_character_id < 0 ||
      !MakeSnapshotId(public_revision, query.expected_snapshot_id)) {
    return false;
  }
  query.bindings = bindings;
  query.environment = {};
  query.environment.exact_build_admitted = true;
  query.environment.admitted_executable_sha256 =
      kCultureInnovationSnapshotExecutableSha256V1;
  query.environment.module_base = module_base;
  query.environment.offline_fixture = false;
  query.source = {};
  query.source.module_base = module_base;
  query.source.native = DirectCultureInnovationSourceNativeAccessV1();
  query.request = {};
  query.request.expected_snapshot_id = Fixed(query.expected_snapshot_id);
  query.request.expected_public_revision = public_revision;
  query.request.expected_native_revision = native_revision;
  query.request.expected_date_raw = snapshot.date_raw;
  query.request.expected_player_character_id = snapshot.played_character_id;
  query.expected_snapshot = snapshot;
  query.snapshot_context = &query;
  query.read_snapshot = &ReadBoundSnapshot;
  query.resolve_player = &ResolveBoundPlayer;
  query.read_source = &ReadExactBuildCultureInnovationNativeSourceV1;
  query.completion = CultureInnovationMailboxCompletionV1::not_executed;
  query.read_result = game::ReadCultureInnovationSnapshotResultV1::unavailable;
  query.execution_result = {};
  query.source_failure = CultureInnovationSourceAdapterFailureV1::none;
  query.execution_stamp = {};
  query.executor_invocations = 0;
  query.ticket = {};
  return true;
}

bool ExecuteCultureInnovationMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query =
      static_cast<CultureInnovationMailboxContextV1 *>(opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          CultureInnovationMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion =
          CultureInnovationMailboxCompletionV1::infrastructure_rejected;
    }
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    AccessProxyV1 proxy{query, &stamp};
    CultureInnovationSnapshotAccessV1 access{};
    access.context = &proxy;
    access.capture_frame = &ProxyCaptureFrame;
    access.is_main_thread = &ProxyIsMainThread;
    access.read_source = &ProxyReadSource;
    query->read_result = ReadCultureInnovationSnapshotV1(
        query->environment, access, query->request,
        query->execution_result);
    BindTerminalIdentity(*query, stamp);
    const bool available =
        query->read_result ==
            game::ReadCultureInnovationSnapshotResultV1::available &&
        query->execution_result.status ==
            game::CultureInnovationSnapshotStatusV1::available &&
        query->execution_result.unavailable_reason ==
            game::CultureInnovationSnapshotFailureV1::none &&
        query->execution_result.readiness.same_frame_ready;
    const bool unavailable =
        query->read_result ==
            game::ReadCultureInnovationSnapshotResultV1::unavailable &&
        query->execution_result.status ==
            game::CultureInnovationSnapshotStatusV1::unavailable &&
        query->execution_result.unavailable_reason !=
            game::CultureInnovationSnapshotFailureV1::none &&
        !query->execution_result.readiness.same_frame_ready;
    if (!available && !unavailable) {
      query->completion =
          CultureInnovationMailboxCompletionV1::infrastructure_rejected;
      return false;
    }
    query->completion = available
                            ? CultureInnovationMailboxCompletionV1::
                                  terminal_available
                            : CultureInnovationMailboxCompletionV1::
                                  terminal_unavailable;
    return true;
  } catch (...) {
    query->completion =
        CultureInnovationMailboxCompletionV1::infrastructure_rejected;
    return false;
  }
}

void DriveCultureInnovationAsyncPrivateProbeV1(
    CultureInnovationAsyncPrivateProbeV1 &probe,
    MainThreadQueryMailboxV1 &mailbox, const Bindings &bindings,
    std::uintptr_t module_base, const game::Snapshot *snapshot,
    std::uint64_t public_revision,
    std::uint64_t native_revision) noexcept {
  if (probe.terminal_published) return;
  auto &query = probe.query;
  query.mailbox = &mailbox;

  if (!probe.query_in_flight) {
    if (snapshot == nullptr || !snapshot->paused || !snapshot->map_ready ||
        !snapshot->has_played_character ||
        !snapshot->played_character_alive || public_revision == 0 ||
        native_revision == 0) {
      probe.state = CultureInnovationAsyncStateV1::waiting_snapshot;
      return;
    }
    if (!bindings.enabled || module_base == 0) {
      MakeInfrastructureUnavailable(
          probe, CultureInnovationAsyncFailureV1::bindings_unavailable);
      return;
    }
    if (!PrepareCultureInnovationMailboxQueryV1(
            query, bindings, module_base, *snapshot, public_revision,
            native_revision)) {
      MakeInfrastructureUnavailable(
          probe,
          CultureInnovationAsyncFailureV1::request_preparation_failed);
      return;
    }
    query.mailbox = &mailbox;
    const auto submitted = TrySubmitMainThreadQueryV1(
        mailbox, &ExecuteCultureInnovationMailboxQueryV1, &query,
        query.ticket);
    probe.last_submit_result = static_cast<std::uint32_t>(submitted);
    if (submitted == MainThreadQuerySubmitResultV1::submitted) {
      probe.query_in_flight = true;
      probe.state = CultureInnovationAsyncStateV1::queued;
    } else if (submitted ==
                   MainThreadQuerySubmitResultV1::mailbox_not_installed ||
               submitted == MainThreadQuerySubmitResultV1::
                                paused_main_thread_not_observed ||
               submitted == MainThreadQuerySubmitResultV1::mailbox_busy ||
               submitted == MainThreadQuerySubmitResultV1::
                                application_main_not_observed) {
      probe.state = CultureInnovationAsyncStateV1::waiting_snapshot;
    } else {
      MakeInfrastructureUnavailable(
          probe, CultureInnovationAsyncFailureV1::submission_rejected);
    }
    return;
  }

  if (mailbox.published_sequence.load(std::memory_order_acquire) !=
      query.ticket.sequence) {
    MakeInfrastructureUnavailable(
        probe, CultureInnovationAsyncFailureV1::mailbox_ticket_mismatch);
    return;
  }
  const auto mailbox_state = mailbox.state.load(std::memory_order_acquire);
  if (!IsTerminalMailboxState(mailbox_state)) {
    probe.state = mailbox_state == MainThreadQueryMailboxStateV1::executing
                      ? CultureInnovationAsyncStateV1::executing
                      : CultureInnovationAsyncStateV1::queued;
    return;
  }
  const auto wait = ClassifyWait(mailbox_state);
  probe.last_wait_result = static_cast<std::uint32_t>(wait);
  if (wait == MainThreadQueryWaitResultV1::completed &&
      (query.completion ==
           CultureInnovationMailboxCompletionV1::terminal_available ||
       query.completion ==
           CultureInnovationMailboxCompletionV1::terminal_unavailable)) {
    probe.terminal_result = query.execution_result;
    probe.terminal_source_failure = query.source_failure;
    probe.state = query.completion ==
                          CultureInnovationMailboxCompletionV1::
                              terminal_available
                      ? CultureInnovationAsyncStateV1::terminal_available
                      : CultureInnovationAsyncStateV1::terminal_unavailable;
    probe.terminal_published = true;
  } else {
    CultureInnovationAsyncFailureV1 failure =
        CultureInnovationAsyncFailureV1::mailbox_executor_failed;
    if (wait == MainThreadQueryWaitResultV1::infrastructure_failed) {
      failure = CultureInnovationAsyncFailureV1::
          mailbox_infrastructure_failed;
    } else if (wait == MainThreadQueryWaitResultV1::cancelled) {
      failure = CultureInnovationAsyncFailureV1::mailbox_cancelled;
    }
    MakeInfrastructureUnavailable(probe, failure);
  }
  const auto reclaimed = ReclaimMainThreadQueryV1(mailbox, query.ticket);
  probe.last_reclaim_result = static_cast<std::uint32_t>(reclaimed);
  probe.query_in_flight = false;
  if (reclaimed != MainThreadQueryReclaimResultV1::reclaimed) {
    probe.async_failure =
        CultureInnovationAsyncFailureV1::mailbox_reclaim_failed;
    probe.state = CultureInnovationAsyncStateV1::infrastructure_failed;
  }
}

std::string SerializeCultureInnovationAsyncPrivateProbeV1(
    const CultureInnovationAsyncPrivateProbeV1 &probe) {
  std::string output =
      "{\"private_build\":true,\"read_only\":true,"
      "\"advertised\":false,\"default_enabled\":false,"
      "\"terminal_only_publication\":true,\"raw_pointers_persisted\":false,"
      "\"async_state\":";
  AppendJsonString(output, CultureInnovationAsyncStateKeyV1(probe.state));
  output += ",\"query_in_flight\":";
  output += probe.query_in_flight ? "true" : "false";
  output += ",\"terminal_published\":";
  output += probe.terminal_published ? "true" : "false";
  output += ",\"async_failure\":";
  if (probe.async_failure == CultureInnovationAsyncFailureV1::none) {
    output += "null";
  } else {
    AppendJsonString(output,
                     CultureInnovationAsyncFailureKeyV1(
                         probe.async_failure));
  }
  output += ",\"source_failure\":";
  if (probe.terminal_source_failure ==
      CultureInnovationSourceAdapterFailureV1::none) {
    output += "null";
  } else {
    AppendJsonString(
        output, CultureInnovationSourceAdapterFailureKeyV1(
                    probe.terminal_source_failure));
  }
  output += ",\"last_submit_result\":";
  AppendNumber(output, probe.last_submit_result);
  output += ",\"last_wait_result\":";
  AppendNumber(output, probe.last_wait_result);
  output += ",\"last_reclaim_result\":";
  AppendNumber(output, probe.last_reclaim_result);
  output += ",\"terminal_result\":";
  if (probe.terminal_published) {
    AppendTerminalSnapshot(output, probe.terminal_result);
  } else {
    output += "null";
  }
  output.push_back('}');
  return output;
}

std::string_view CultureInnovationAsyncStateKeyV1(
    CultureInnovationAsyncStateV1 state) noexcept {
  switch (state) {
  case CultureInnovationAsyncStateV1::waiting_snapshot:
    return "waiting-snapshot";
  case CultureInnovationAsyncStateV1::queued:
    return "queued";
  case CultureInnovationAsyncStateV1::executing:
    return "executing";
  case CultureInnovationAsyncStateV1::terminal_available:
    return "terminal-available";
  case CultureInnovationAsyncStateV1::terminal_unavailable:
    return "terminal-unavailable";
  case CultureInnovationAsyncStateV1::infrastructure_failed:
    return "infrastructure-failed";
  }
  return "infrastructure-failed";
}

std::string_view CultureInnovationAsyncFailureKeyV1(
    CultureInnovationAsyncFailureV1 failure) noexcept {
  switch (failure) {
  case CultureInnovationAsyncFailureV1::none:
    return "none";
  case CultureInnovationAsyncFailureV1::bindings_unavailable:
    return "bindings_unavailable";
  case CultureInnovationAsyncFailureV1::request_preparation_failed:
    return "request_preparation_failed";
  case CultureInnovationAsyncFailureV1::submission_rejected:
    return "submission_rejected";
  case CultureInnovationAsyncFailureV1::mailbox_executor_failed:
    return "mailbox_executor_failed";
  case CultureInnovationAsyncFailureV1::mailbox_infrastructure_failed:
    return "mailbox_infrastructure_failed";
  case CultureInnovationAsyncFailureV1::mailbox_cancelled:
    return "mailbox_cancelled";
  case CultureInnovationAsyncFailureV1::mailbox_ticket_mismatch:
    return "mailbox_ticket_mismatch";
  case CultureInnovationAsyncFailureV1::mailbox_reclaim_failed:
    return "mailbox_reclaim_failed";
  }
  return "unknown";
}

} // namespace xar::ck3_11906
