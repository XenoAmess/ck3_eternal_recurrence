#include "xar_bridge/ck3_12003_player_hof_gold_mailbox.hpp"

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/protocol.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"

#include <windows.h>

namespace xar::ck3_12003 {
namespace {
namespace hof = religion::hof_gold;
bool HasField(std::string_view payload, std::string_view name) {
  return payload.find('"' + std::string(name) + '"') != std::string_view::npos;
}
bool ValidFrame(const game::Snapshot &frame, std::uint64_t revision) noexcept {
  return revision != 0 && frame.paused && frame.map_ready &&
      frame.has_played_character && frame.played_character_alive &&
      frame.played_character_id > 0;
}
void *ResolvePlayed(const hof::Bindings &bindings, std::int32_t id) noexcept {
  return ck3_12002::ResolveCoreCharacter(bindings.interaction.core, id);
}
} // namespace

bool IsPlayerHeadOfFaithGoldPrivateStep12003(std::string_view step) noexcept {
  return step == kPlayerHeadOfFaithGoldPrivateStep12003;
}
bool ParsePlayerHeadOfFaithGoldRevision12003(
    std::string_view payload, std::uint64_t &revision) noexcept {
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

bool ExecutePlayerHeadOfFaithGoldMailbox12003(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<PlayerHeadOfFaithGoldMailboxContext12003 *>(envelope->typed_context);
  try {
    if (!ck3_12002::EnterQueryMailbox(*envelope, stamp, &ExecutePlayerHeadOfFaithGoldMailbox12003)) {
      query.failure = "player_head_of_faith_gold_published_frame_changed";
      return true;
    }
    const auto &frame = envelope->expected_snapshot;
    const auto actor = static_cast<std::int32_t>(frame.played_character_id);
    auto *character = ResolvePlayed(query.bindings, actor);
    (void)hof::ReadHeadOfFaithGoldContext12003(query.bindings, character, actor,
        static_cast<std::int32_t>(frame.date_raw), stamp.pump_epoch, query.observation);
    query.completed = true;
    (void)ck3_12002::FinishQueryMailbox(*envelope);
    return true;
  } catch (...) {
    query.failure = "player_head_of_faith_gold_native_capture_exception";
    return false;
  }
}

bool RunPlayerHeadOfFaithGoldMailbox12003(PlayerHeadOfFaithGoldMailboxContext12003 &query,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox ||
        !ValidFrame(envelope.expected_snapshot, envelope.expected_snapshot_revision)) {
      failure = "player_head_of_faith_gold_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox,
        &ExecutePlayerHeadOfFaithGoldMailbox12003, &envelope, envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "player_head_of_faith_gold_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "player_head_of_faith_gold_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = SerializePlayerHeadOfFaithGoldResult12003(query, request_id);
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "player_head_of_faith_gold_serialization_unavailable" : query.failure;
    return false;
  } catch (...) {
    serialized.clear(); failure = "player_head_of_faith_gold_mailbox_exception"; return false;
  }
}

bool HandlePlayerHeadOfFaithGoldPrivate12003(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerHeadOfFaithGoldPrivateStep12003(step)) {
    failure = "player_head_of_faith_gold_step_unavailable"; return false;
  }
  std::uint64_t expected = 0;
  if (!ParsePlayerHeadOfFaithGoldRevision12003(payload, expected)) {
    failure = "player_head_of_faith_gold_request_invalid"; return false;
  }
  if (!adapter.enabled() || adapter.descriptor().game_version != "1.20.0.3" ||
      adapter.descriptor().executable_sha256 != hof::kExecutableSha256 ||
      !ValidFrame(published, revision) || (expected != 0 && expected != revision)) {
    failure = "player_head_of_faith_gold_current_frame_unavailable"; return false;
  }
  try {
    PlayerHeadOfFaithGoldMailboxContext12003 query{};
    query.envelope.game = &ck3_12002::NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    const auto image_base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    const auto reviewed_sha = game::ReviewedCrozierAbiSha256(adapter.descriptor());
    const auto interaction = ck3_12002::BindContextImage(image_base, reviewed_sha);
    const auto heads = ck3_12002::religion::head::BindRiteHeadsImage12002(image_base, reviewed_sha);
    query.bindings = hof::BindHeadOfFaithGoldImage12003(
        image_base, adapter.descriptor().executable_sha256, interaction, heads,
        &ck3_12002::religion::head::ReadPlayedRiteHeads12002,
        &ck3_12002::ReadNamedInteractionFixedExact12002);
    return RunPlayerHeadOfFaithGoldMailbox12003(query, request_id, serialized, failure);
  } catch (...) { failure = "player_head_of_faith_gold_handler_exception"; return false; }
}
} // namespace xar::ck3_12003
#endif
