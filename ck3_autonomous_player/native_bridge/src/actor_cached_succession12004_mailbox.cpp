#include "xar_bridge/actor_cached_succession12004_mailbox.hpp"

#if defined(XAR_CK3_ENABLE_CONFUCIAN_ASSEMBLY_PREDICATES_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/ck3_12003_readonly_revision.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"

#include <windows.h>

namespace xar::ck3_12004 {
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
bool ValidFrame(const game::Snapshot &frame, std::uint64_t revision) noexcept {
  return revision != 0 && frame.paused && frame.map_ready &&
      frame.has_played_character && frame.played_character_alive &&
      frame.played_character_id != -1;
}
bool ReadMemory(void *context, std::uintptr_t address, void *out,
                std::size_t bytes) noexcept {
  if (!context || !address || !out || !bytes) return false;
  SIZE_T copied = 0;
  return ReadProcessMemory(GetCurrentProcess(),
      reinterpret_cast<const void *>(address), out, bytes, &copied) &&
      copied == bytes;
}
std::uintptr_t ResolveCharacter(void *context, std::uint32_t full_id) noexcept {
  if (!context) return 0;
  return reinterpret_cast<std::uintptr_t>(ck3_12004::ResolveCoreCharacter(
      *static_cast<CoreBindings *>(context), static_cast<std::int32_t>(full_id)));
}
} // namespace

bool IsActorCachedSuccessionPrivateStepV1(std::string_view step) noexcept {
  return step == kActorCachedSuccessionPrivateStepV1;
}
bool ParseActorCachedSuccessionRevisionV1(std::string_view payload,
                                         std::uint64_t &revision) noexcept {
  return ck3_12003::readonly_query::ParseUniqueTopLevelRevision(payload, revision);
}
bool ExecuteActorCachedSuccessionMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<ActorCachedSuccessionMailboxContextV1 *>(envelope->typed_context);
  try {
    if (!ck3_12002::EnterQueryMailbox(*envelope, stamp,
                                    &ExecuteActorCachedSuccessionMailboxV1)) {
      query.failure = "actor_cached_succession_published_frame_changed";
      return true;
    }
    const auto &frame = envelope->expected_snapshot;
    (void)actor_cached_succession::Read(query.bindings, stamp.pump_epoch,
        static_cast<std::uint32_t>(frame.played_character_id),
        static_cast<std::uint32_t>(frame.date_raw), query.observation);
    query.completed = true;
    (void)ck3_12002::FinishQueryMailbox(*envelope);
    return true;
  } catch (...) {
    query.failure = "actor_cached_succession_native_capture_exception";
    return false;
  }
}
std::string SerializeActorCachedSuccessionResultV1(
    const ActorCachedSuccessionMailboxContextV1 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kActorCachedSuccessionPrivateStepV1) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":" + Quote(kGameVersion) +
      ",\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"domain_key\":" + Quote(kActorCachedSuccessionDomainKeyV1) +
      ",\"backend_id\":" + Quote(kActorCachedSuccessionBackendV1) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"actor_cached_succession\":" + actor_cached_succession::Serialize(query.observation) + "}}";
}
bool RunActorCachedSuccessionMailboxV1(ActorCachedSuccessionMailboxContextV1 &query,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox ||
        !ValidFrame(envelope.expected_snapshot, envelope.expected_snapshot_revision)) {
      failure = "actor_cached_succession_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox,
        &ExecuteActorCachedSuccessionMailboxV1, &envelope, envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "actor_cached_succession_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "actor_cached_succession_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = SerializeActorCachedSuccessionResultV1(query, request_id);
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "actor_cached_succession_serialization_unavailable" : query.failure;
    return false;
  } catch (...) {
    serialized.clear(); failure = "actor_cached_succession_mailbox_exception"; return false;
  }
}
bool HandleActorCachedSuccessionPrivateV1(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsActorCachedSuccessionPrivateStepV1(step)) {
    failure = "actor_cached_succession_step_unavailable"; return false;
  }
  std::uint64_t expected = 0;
  if (!ParseActorCachedSuccessionRevisionV1(payload, expected)) {
    failure = "actor_cached_succession_request_invalid"; return false;
  }
  const auto &descriptor = adapter.descriptor();
  if (!adapter.enabled() || !game::IsCk3_12004Descriptor(descriptor) ||
      !ValidFrame(published, revision) || (expected != 0 && expected != revision)) {
    failure = "actor_cached_succession_current_frame_unavailable"; return false;
  }
  try {
    ActorCachedSuccessionMailboxContextV1 query{};
    query.envelope.game = &ck3_12002::NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    query.core = BindCoreImage(base, descriptor.executable_sha256);
    query.bindings = actor_cached_succession::BindImage(base,
        descriptor.executable_sha256, &ReadMemory, &ResolveCharacter, &query.core);
    return RunActorCachedSuccessionMailboxV1(query, request_id, serialized, failure);
  } catch (...) { failure = "actor_cached_succession_handler_exception"; return false; }
}
} // namespace xar::ck3_12004
#endif
