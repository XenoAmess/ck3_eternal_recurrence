#include "xar_bridge/ck3_12003_holy_order_loan_mailbox.hpp"

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_religion_mailbox.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"

#include <cstring>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
namespace loan = ck3_12003::religion::loan;
template <typename T> T Load(const void *p, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(value));
  return value;
}
bool ValidFrame(const game::Snapshot &frame, std::uint64_t revision) noexcept {
  return revision != 0 && frame.paused && frame.map_ready &&
      frame.has_played_character && frame.played_character_alive &&
      frame.played_character_id > 0;
}
void *ResolvePlayed(const loan::Bindings &bindings, std::int32_t id) noexcept {
  if (!bindings.character_store || !*bindings.character_store) return nullptr;
  const auto *store = *bindings.character_store;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  if (index >= Load<std::uint32_t>(store, 0x2C)) return nullptr;
  const auto *rows = Load<const std::byte *>(store, 0x20);
  if (!rows) return nullptr;
  auto *character = Load<void *>(rows, static_cast<std::size_t>(index) * 0x10 + 8);
  if (!character || Load<std::int32_t>(character, 0x18) != id) return nullptr;
  return character;
}
} // namespace

bool IsPlayerHolyOrderLoanPrivateStep12003(std::string_view step) noexcept {
  return step == kPlayerHolyOrderLoanPrivateStep12003;
}
bool ParsePlayerHolyOrderLoanRevision12003(
    std::string_view payload, std::uint64_t &revision) noexcept {
  return ParsePlayerReligionRevision12002(payload, revision);
}

bool ExecutePlayerHolyOrderLoanMailbox12003(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<PlayerHolyOrderLoanMailboxContext12003 *>(envelope->typed_context);
  try {
    if (!EnterQueryMailbox(*envelope, stamp, &ExecutePlayerHolyOrderLoanMailbox12003)) {
      query.failure = "player_holy_order_loan_published_frame_changed";
      return true;
    }
    const auto &frame = envelope->expected_snapshot;
    const auto actor = static_cast<std::int32_t>(frame.played_character_id);
    auto *character = ResolvePlayed(query.bindings, actor);
    (void)loan::ReadHolyOrderLoanContext12003(query.bindings, character, actor,
        static_cast<std::int32_t>(frame.date_raw), stamp.pump_epoch, query.observation);
    query.completed = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) {
    query.failure = "player_holy_order_loan_native_capture_exception";
    return false;
  }
}

bool RunPlayerHolyOrderLoanMailbox12003(PlayerHolyOrderLoanMailboxContext12003 &query,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox ||
        !ValidFrame(envelope.expected_snapshot, envelope.expected_snapshot_revision)) {
      failure = "player_holy_order_loan_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox,
        &ExecutePlayerHolyOrderLoanMailbox12003, &envelope, envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "player_holy_order_loan_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "player_holy_order_loan_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = SerializePlayerHolyOrderLoanResult12003(query, request_id);
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "player_holy_order_loan_serialization_unavailable" : query.failure;
    return false;
  } catch (...) {
    serialized.clear(); failure = "player_holy_order_loan_mailbox_exception"; return false;
  }
}

bool HandlePlayerHolyOrderLoanPrivate12003(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerHolyOrderLoanPrivateStep12003(step)) {
    failure = "player_holy_order_loan_step_unavailable"; return false;
  }
  std::uint64_t expected = 0;
  if (!ParsePlayerHolyOrderLoanRevision12003(payload, expected)) {
    failure = "player_holy_order_loan_request_invalid"; return false;
  }
  if (!adapter.enabled() || adapter.descriptor().game_version != "1.20.0.3" ||
      adapter.descriptor().executable_sha256 != loan::kExecutableSha256 ||
      !ValidFrame(published, revision) || (expected != 0 && expected != revision)) {
    failure = "player_holy_order_loan_current_frame_unavailable"; return false;
  }
  try {
    PlayerHolyOrderLoanMailboxContext12003 query{};
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.bindings = loan::BindHolyOrderLoanImage12003(
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
        adapter.descriptor().executable_sha256);
    return RunPlayerHolyOrderLoanMailbox12003(query, request_id, serialized, failure);
  } catch (...) { failure = "player_holy_order_loan_handler_exception"; return false; }
}
} // namespace xar::ck3_12002
#endif
