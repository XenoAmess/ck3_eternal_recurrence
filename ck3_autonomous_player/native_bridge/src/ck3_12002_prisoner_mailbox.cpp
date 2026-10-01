#include "xar_bridge/ck3_12002_prisoner_mailbox.hpp"
#include "xar_bridge/ck3_12002_campaign.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/player_prisoner_collection_private_transport_v1.hpp"
#include "xar_bridge/protocol.hpp"

#include <cstring>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
struct CollectionQuery {
  QueryMailboxEnvelope envelope{};
  std::uintptr_t module = 0;
  PrisonerRansomBindings bindings{};
  std::uint32_t ordinal = 0;
  bridge::PlayerPrisonerCollectionSnapshotV1 collection{};
  std::array<PlayerPrisonerRansomQuoteV1, bridge::kPlayerPrisonerMaximumRowsV1> quotes{};
  bool completed = false;
};
struct RansomQuery {
  QueryMailboxEnvelope envelope{};
  std::uintptr_t module = 0;
  PrisonerRansomBindings bindings{};
  PlayerPrisonerRansomQuoteV1 quote{};
  PlayerPrisonerRansomSubmitV1 result = PlayerPrisonerRansomSubmitV1::unavailable;
};
bool CapturePrisonerFrame(void *opaque, bridge::PlayerPrisonerFrameV1 &frame) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  game::Snapshot snapshot{};
  if (!envelope || !CaptureQuerySnapshot(envelope, snapshot)) return false;
  frame = {};
  frame.public_revision = envelope->expected_snapshot_revision;
  frame.native_revision = envelope->expected_snapshot_revision;
  frame.proof_epoch = envelope->execution_stamp.pump_epoch;
  frame.date_raw = snapshot.date_raw;
  frame.paused = snapshot.paused;
  frame.map_ready = snapshot.map_ready;
  frame.played_character_id = snapshot.played_character_id;
  frame.played_character_alive = snapshot.played_character_alive;
  frame.played_character_identity_round_trip = snapshot.has_played_character &&
      snapshot.played_character_id > 0;
  return true;
}
bool ReadPrisonerMemory(void *, std::uintptr_t address, void *out, std::size_t size) noexcept {
  if (!address || !out || !size) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(out, reinterpret_cast<const void *>(address), size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
void AppendString(std::string &out, std::string_view value) {
  out += '"';
  for (const unsigned char ch : value) {
    if (ch == '"' || ch == '\\') { out += '\\'; out += static_cast<char>(ch); }
    else if (ch < 0x20) {
      constexpr char hex[] = "0123456789abcdef";
      out += "\\u00"; out += hex[ch >> 4]; out += hex[ch & 15];
    } else out += static_cast<char>(ch);
  }
  out += '"';
}
std::string ResultPrefix(std::string_view request_id, std::string_view step) {
  std::string out = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendString(out, request_id);
  out += ",\"ok\":true,\"result\":{\"step\":";
  AppendString(out, step);
  out += ",\"accepted\":true";
  return out;
}
bool RunMailbox(ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    QueryMailboxEnvelope &envelope, ck3_11906::MainThreadQueryExecutorV1 executor,
    std::string &failure) {
  const auto submitted = ck3_11906::TrySubmitMainThreadQueryV1(
      mailbox, executor, &envelope, envelope.ticket);
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
void PrepareEnvelope(QueryMailboxEnvelope &envelope, const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, void *typed) {
  envelope.game = &NativeAdapter12002(adapter);
  envelope.mailbox = &mailbox;
  envelope.expected_snapshot = published;
  envelope.expected_snapshot_revision = revision;
  envelope.typed_context = typed;
}
} // namespace

bool ExecutePlayerPrisonerCollection12002(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context ||
      !EnterQueryMailbox(*envelope, stamp, &ExecutePlayerPrisonerCollection12002)) return true;
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
  access.read_lineage = access.read_child_relation = access.read_title_tier = access.read_dread = true;
  access.get_primary_title = reinterpret_cast<bridge::GetPlayerPrisonerPrimaryTitleV1>(
      query.module + kCampaignRootPrimaryTitleRva);
  query.completed = ReadPlayerPrisonerCollectionV1(access, query.collection);
  if (query.completed) {
    for (std::uint32_t index = 0; index < query.collection.returned_count; ++index)
      query.quotes[index].failure = PlayerPrisonerRansomQuoteFailureV1::not_evaluated;
    if (query.ordinal < query.collection.returned_count) {
      query.quotes[query.ordinal] = ReadPlayerPrisonerRansomQuotePrivateV1(
          query.bindings, query.module, query.collection.frame.played_character_id,
          static_cast<std::int32_t>(query.collection.rows[query.ordinal].full_character_id));
    }
  }
  (void)FinishQueryMailbox(*envelope);
  return true;
}

bool ExecutePlayerPrisonerRansom12002(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context ||
      !EnterQueryMailbox(*envelope, stamp, &ExecutePlayerPrisonerRansom12002)) return true;
  auto &query = *static_cast<RansomQuery *>(envelope->typed_context);
  query.result = SubmitPlayerPrisonerRansomPrivateV1(query.bindings, query.module,
      query.quote, envelope->expected_snapshot_revision, stamp.date_raw);
  (void)FinishQueryMailbox(*envelope);
  return true;
}

bool HandlePlayerPrisonerPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, PrisonerPrivateWorkerState12002 &state,
    std::string &serialized, std::string &failure) {
  std::uint32_t ordinal = 0;
  const bool is_collection = ck3_11906::ParsePlayerPrisonerCollectionPrivateStepV1(step, ordinal);
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1)
  const bool is_submit = step == "submit-player-prisoner-ransom-private-v1";
#else
  const bool is_submit = false;
#endif
  if (!is_collection && !is_submit) return false;
  serialized.clear(); failure.clear();
  std::uint64_t expected = 0;
  if (!bridge::JsonUnsignedField(payload, "expected_revision", expected) ||
      expected == 0 || expected != revision || adapter.descriptor().game_version != "1.20.0.2" ||
      !published.paused || !published.map_ready || !published.has_played_character ||
      !published.played_character_alive || published.played_character_id <= 0) {
    failure = "prisoner request revision or paused player frame is stale";
    return true;
  }
  const auto module = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  const auto bindings = BindPrisonerRansomImage(module, adapter.descriptor().executable_sha256);
  if (is_collection) {
    CollectionQuery query{};
    PrepareEnvelope(query.envelope, adapter, mailbox, published, revision, &query);
    query.module = module; query.bindings = bindings; query.ordinal = ordinal;
    if (!RunMailbox(mailbox, query.envelope, &ExecutePlayerPrisonerCollection12002, failure)) return true;
    const auto value = xar::ck3_12002::SerializePlayerPrisonerCollectionPrivateV1(query.collection, revision,
        query.quotes, query.completed);
    if (value.empty()) { failure = "prisoner collection serialization unavailable"; return true; }
    ++state.query_sequence;
    state.current_quote.reset(); state.quote_revision = state.quote_query_sequence = 0;
    if (query.completed && ordinal < query.collection.returned_count && query.quotes[ordinal].available) {
      state.current_quote = query.quotes[ordinal];
      state.quote_revision = revision; state.quote_query_sequence = state.query_sequence;
    }
    serialized = ResultPrefix(request_id, step) + ",\"status\":\"" +
        (query.collection.available ? "available" : "unavailable") + "\",\"query_sequence\":" +
        std::to_string(state.query_sequence) + ",\"observation_revision\":" +
        std::to_string(query.envelope.execution_stamp.pump_epoch) + ",\"snapshot_revision\":" +
        std::to_string(revision) + ",\"player_prisoner_collection\":" + value +
        ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"backend_id\":\"native-headless\"}}";
    return true;
  }
  std::uint64_t sequence = 0, prisoner = 0, payer = 0, gold = 0;
  if (!state.current_quote || state.quote_revision != revision || state.may_have_submitted ||
      !bridge::JsonUnsignedField(payload, "quote_query_sequence", sequence) || sequence == 0 ||
      sequence != state.quote_query_sequence ||
      !bridge::JsonUnsignedField(payload, "prisoner_character_id", prisoner) ||
      !bridge::JsonUnsignedField(payload, "payer_character_id", payer) ||
      !bridge::JsonUnsignedField(payload, "quoted_gold_raw", gold) ||
      prisoner != static_cast<std::uint64_t>(state.current_quote->prisoner_character_id) ||
      payer != static_cast<std::uint64_t>(state.current_quote->payer_character_id) ||
      gold != static_cast<std::uint64_t>(state.current_quote->quoted_gold_raw) ||
      state.current_quote->jailer_character_id != published.played_character_id) {
    failure = "private ransom quote or request is stale";
    return true;
  }
  RansomQuery query{};
  PrepareEnvelope(query.envelope, adapter, mailbox, published, revision, &query);
  query.module = module; query.bindings = bindings; query.quote = *state.current_quote;
  state.may_have_submitted = true;
  if (!RunMailbox(mailbox, query.envelope, &ExecutePlayerPrisonerRansom12002, failure)) {
    if (query.envelope.ticket.sequence == 0) state.may_have_submitted = false;
    return true;
  }
  if (query.result != PlayerPrisonerRansomSubmitV1::submitted_verification_pending) {
    failure = "private ransom submit unresolved or rejected";
    return true;
  }
  serialized = ResultPrefix(request_id, step) + ",\"status\":\"submitted_verification_pending\"}}";
  return true;
}
} // namespace xar::ck3_12002
