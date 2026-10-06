#include "xar_bridge/ck3_12004_prisoner_mailbox.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_core_frame_v1.hpp"
#include "xar_bridge/ck3_12004_thread_runtime.hpp"
#include "xar_bridge/player_prisoner_collection_private_transport_v1.hpp"
#include "xar_bridge/protocol.hpp"

#include <cstring>
#include <windows.h>

namespace xar::ck3_12004 {
namespace {
using ck3_12002::QueryMailboxEnvelope;

struct CollectionQuery {
  QueryMailboxEnvelope envelope{};
  std::uintptr_t module = 0;
  PrisonerRansomBindings12004 bindings{};
  std::uint32_t ordinal = 0;
  PrisonerReleasePreviewBindings12004 release_bindings{};
  std::array<PrisonerReleasePreview12004,
      bridge::kPlayerPrisonerMaximumRowsV1> release_previews{};
  bridge::PlayerPrisonerCollectionSnapshotV1 collection{};
  std::array<PlayerPrisonerRansomQuoteV1,
      bridge::kPlayerPrisonerMaximumRowsV1> quotes{};
  bool completed = false;
};

bool CapturePrisonerFrame(void *opaque,
    bridge::PlayerPrisonerFrameV1 &frame) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  game::Snapshot prefix{};
  if (!envelope || !ck3_12002::CaptureQuerySnapshot(envelope, prefix)) return false;
  frame = {};
  frame.public_revision = envelope->expected_snapshot_revision;
  frame.native_revision = envelope->expected_snapshot_revision;
  frame.proof_epoch = envelope->execution_stamp.pump_epoch;
  frame.date_raw = prefix.date_raw;
  frame.paused = prefix.paused;
  frame.map_ready = prefix.map_ready;
  frame.played_character_id = prefix.played_character_id;
  frame.played_character_alive = prefix.played_character_alive;
  frame.played_character_identity_round_trip = prefix.has_played_character &&
      prefix.played_character_id > 0;
  return true;
}

bool ReadPrisonerMemory(void *, std::uintptr_t address,
    void *output, std::size_t size) noexcept {
  if (!address || !output || !size) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(output, reinterpret_cast<const void *>(address), size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

void AppendString(std::string &output, std::string_view value) {
  output += '"';
  for (const unsigned char ch : value) {
    if (ch == '"' || ch == '\\') { output += '\\'; output += static_cast<char>(ch); }
    else if (ch < 0x20) {
      constexpr char hex[] = "0123456789abcdef";
      output += "\\u00"; output += hex[ch >> 4]; output += hex[ch & 15];
    } else output += static_cast<char>(ch);
  }
  output += '"';
}

std::string ResultPrefix(std::string_view request_id, std::string_view step) {
  std::string output = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendString(output, request_id);
  output += ",\"ok\":true,\"result\":{\"step\":";
  AppendString(output, step);
  output += ",\"accepted\":true";
  return output;
}

bool RunMailbox(ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    QueryMailboxEnvelope &envelope, std::string &failure) {
  const auto submitted = ck3_11906::TrySubmitMainThreadQueryV1(mailbox,
      &ExecutePlayerPrisonerCollection12004, &envelope, envelope.ticket);
  if (submitted != ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
    failure = "prisoner application-main executor unavailable";
    return false;
  }
  auto wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, envelope.ticket,
      ck3_11906::kPlayerPrisonerCollectionQueuedWaitMsV1);
  while (wait == ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)
    wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, envelope.ticket,
        ck3_11906::kPlayerPrisonerCollectionExecutingWaitMsV1);
  const auto reclaimed = ck3_11906::ReclaimMainThreadQueryV1(mailbox, envelope.ticket);
  if (wait != ck3_11906::MainThreadQueryWaitResultV1::completed ||
      reclaimed != ck3_11906::MainThreadQueryReclaimResultV1::reclaimed ||
      !envelope.entered || !envelope.frame_stable) {
    failure = "prisoner application-main result or frame unavailable";
    return false;
  }
  return true;
}
} // namespace

ck3_11906::MainThreadQueryInstallEnvironmentV1
BindPrisonerCollectionMailboxEnvironment12004(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept {
  const std::array<ck3_11906::MainThreadQueryExecutorV1, 2> executors{
      &ExecuteCoreFrameMailboxV1, &ExecutePlayerPrisonerCollection12004};
  return xar::ck3_12004::BindThreadRuntimeImage(
      module_base, executable_sha256, executors);
}

bool ExecutePlayerPrisonerCollection12004(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context ||
      !ck3_12002::EnterQueryMailbox(*envelope, stamp,
          &ExecutePlayerPrisonerCollection12004)) return true;
  auto &query = *static_cast<CollectionQuery *>(envelope->typed_context);
  bridge::PlayerPrisonerCollectionAccessV1 access{};
  access.exact_build_admitted = query.bindings.enabled;
  access.admitted_executable_sha256 = kExecutableSha256;
  access.module_base = query.module;
  access.current_thread_id = GetCurrentThreadId();
  access.application_main_thread_id = stamp.thread_id;
  access.context = envelope;
  access.capture_frame = &CapturePrisonerFrame;
  access.read_memory = &ReadPrisonerMemory;
  access.read_lineage = access.read_child_relation =
      access.read_title_tier = access.read_dread = true;
  access.get_primary_title = reinterpret_cast<bridge::GetPlayerPrisonerPrimaryTitleV1>(
      query.module + kPrisonerPrimaryTitleRva12004);
  query.completed = ReadPlayerPrisonerCollectionV1(access, query.collection);
  if (query.completed) {
    for (std::uint32_t index = 0; index < query.collection.returned_count; ++index)
      query.quotes[index].failure = PlayerPrisonerRansomQuoteFailureV1::not_evaluated;
    if (query.ordinal < query.collection.returned_count) {
      const auto prisoner = query.collection.rows[query.ordinal].full_character_id;
      query.quotes[query.ordinal] = ReadPlayerPrisonerRansomQuotePrivateV1(
          query.bindings, query.module, query.collection.frame.played_character_id,
          static_cast<std::int32_t>(prisoner));
      const PrisonerReleasePreviewAccess12004 release_access{
          access.current_thread_id, stamp.thread_id, envelope,
          &CapturePrisonerFrame, &ReadPrisonerMemory};
      (void)ReadPrisonerReleasePreview12004(query.release_bindings, release_access,
          static_cast<std::uint32_t>(query.collection.frame.played_character_id),
          prisoner, query.release_previews[query.ordinal]);
    }
  }
  (void)ck3_12002::FinishQueryMailbox(*envelope);
  return true;
}

bool HandlePlayerPrisonerCollection12004(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published_core, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    PrisonerPrivateWorkerState12004 &state, std::string &serialized,
    std::string &failure) {
  std::uint32_t ordinal = 0;
  if (!ck3_11906::ParsePlayerPrisonerCollectionPrivateStepV1(step, ordinal)) return false;
  serialized.clear(); failure.clear();
  std::uint64_t expected = 0;
  if (!bridge::JsonUnsignedField(payload, "expected_revision", expected) ||
      expected == 0 || expected != revision ||
      !game::IsCk3_12004Descriptor(adapter.descriptor()) ||
      !published_core.paused || !published_core.map_ready ||
      !published_core.has_played_character || !published_core.played_character_alive ||
      published_core.played_character_id <= 0) {
    failure = "prisoner request revision or paused player frame is stale";
    return true;
  }
  std::uint64_t requested_mask = 0;
  if (bridge::JsonUnsignedField(payload, "release_option_mask_bits", requested_mask) &&
      requested_mask != 0) {
    failure = "negotiated release preview is not admitted for 1.20.0.4";
    return true;
  }
  CollectionQuery query{};
  query.module = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  query.bindings = BindPrisonerRansomImage12004(query.module,
      adapter.descriptor().executable_sha256);
  query.release_bindings = BindPrisonerReleasePreview12004(query.module,
      adapter.descriptor().executable_sha256);
  query.ordinal = ordinal;
  query.envelope.game = &adapter;
  query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = published_core;
  query.envelope.expected_snapshot_revision = revision;
  query.envelope.typed_context = &query;
  query.envelope.snapshot_comparison = ck3_12002::QuerySnapshotComparison12002::core_frame;
  if (!RunMailbox(mailbox, query.envelope, failure)) return true;
  const auto value = SerializePlayerPrisonerCollectionPrivateV1(query.collection,
      revision, query.quotes, query.completed, &query.release_previews);
  if (value.empty()) { failure = "prisoner collection serialization unavailable"; return true; }
  ++state.query_sequence;
  serialized = ResultPrefix(request_id, step) + ",\"status\":\"" +
      (query.collection.available ? "available" : "unavailable") +
      "\",\"query_sequence\":" + std::to_string(state.query_sequence) +
      ",\"observation_revision\":" +
      std::to_string(query.envelope.execution_stamp.pump_epoch) +
      ",\"snapshot_revision\":" + std::to_string(revision) +
      ",\"player_prisoner_collection\":" + value +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,"
      "\"backend_id\":\"native-headless\"}}";
  return true;
}

} // namespace xar::ck3_12004
