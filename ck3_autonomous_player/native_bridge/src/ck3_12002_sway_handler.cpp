#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_sway_mailbox.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"
#include <charconv>
#include <windows.h>
namespace xar::ck3_12002 {
namespace {
using namespace bridge;
bool Simple(std::string_view s) noexcept {
  if (s.empty() || s.size() > 64) return false;
  for (const char c : s) if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
      (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.')) return false;
  return true;
}
bool Target(std::string_view step, std::string_view prefix, std::uint32_t &out) noexcept {
  if (!step.starts_with(prefix)) return false;
  const auto s = step.substr(prefix.size());
  if (s.empty() || s.front() == '0') return false;
  const auto [end, error] = std::from_chars(s.data(), s.data() + s.size(), out);
  return error == std::errc{} && end == s.data() + s.size() && out != 0;
}
} // namespace
bool HandleActiveSwayPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, ActiveSwayState12002 &state,
    std::string &serialized, std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    ActiveSwayMailboxContext12002 q{};
    if (!Target(step, "query-active-scheme-sway-target-v1-private-", q.target)) {
      q.formal = true;
      if (!Target(step, "submit-active-scheme-sway-v1-private-", q.target)) {
        q.receipt_mode = true;
        if (!Target(step, "receipt-active-scheme-sway-v1-private-", q.target)) {
          failure = "sway step invalid"; return false;
        }
      }
    }
    std::uint64_t expected_revision{};
    if (xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256 || !adapter.enabled() ||
        !JsonUnsignedField(payload, "expected_revision", expected_revision) || expected_revision != revision ||
        !revision || !published.paused || !published.map_ready || !published.has_played_character ||
        !published.played_character_alive || published.played_character_id <= 0 ||
        published.played_character_id == static_cast<std::int64_t>(q.target)) { failure = "sway frame or request invalid"; return false; }
    if (q.formal) {
      if (!JsonStringField(payload, "action_id", q.action_id, 64) || !Simple(q.action_id)) {
        failure = "sway action_id invalid"; return false;
      }
      if (q.receipt_mode) {
        if (!state.pending_ack || state.pending_ack->request_id != q.action_id ||
            state.pending_ack->target_id != q.target ||
            state.pending_ack->actor_character_id != published.played_character_id) {
          failure = "sway receipt ledger invalid"; return false;
        }
        q.prior_ack = *state.pending_ack;
      } else {
        std::string opinion;
        if (state.may_have_submitted ||
            !JsonUnsignedField(payload, "expected_capture_epoch", q.expected_capture_epoch) ||
            !JsonUnsignedField(payload, "expected_container_generation", q.expected_container_generation) ||
            !q.expected_capture_epoch || !q.expected_container_generation ||
            !JsonStringField(payload, "expected_target_opinion_of_actor", opinion, 16) || opinion.empty()) {
          failure = "sway submit ledger or source invalid"; return false;
        }
        const auto [end, error] = std::from_chars(opinion.data(), opinion.data() + opinion.size(), q.expected_opinion);
        if (error != std::errc{} || end != opinion.data() + opinion.size() ||
            q.expected_opinion < -100 || q.expected_opinion > 100) { failure = "sway opinion invalid"; return false; }
      }
    }
    q.envelope.game = &NativeAdapter12002(adapter); q.envelope.mailbox = &mailbox;
    q.envelope.expected_snapshot = published; q.envelope.expected_snapshot_revision = revision;
    q.envelope.typed_context = &q;
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    q.source = BindSwayStateImage12002(base, xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
    q.commands = BindSwayCommandImage(base, xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
    const bool submitting = q.formal && !q.receipt_mode;
    if (submitting) state.may_have_submitted = true;
    const auto submit = TrySubmitMainThreadQueryV1(mailbox, &ExecuteActiveSwayMailbox12002,
        &q.envelope, q.envelope.ticket);
    if (submit != MainThreadQuerySubmitResultV1::submitted) {
      if (submitting) state.may_have_submitted = false;
      failure = "sway executor unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(mailbox, q.envelope.ticket, 8000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(mailbox, q.envelope.ticket, 2000);
    const auto reclaim = ReclaimMainThreadQueryV1(mailbox, q.envelope.ticket);
    const auto native = wait == MainThreadQueryWaitResultV1::completed &&
        reclaim == MainThreadQueryReclaimResultV1::reclaimed && q.envelope.frame_stable
        ? (q.formal ? SerializeActiveSwayFormal12002(q) : SerializeActiveSwayRead12002(q)) : std::string{};
    if (native.empty()) {
      if (submitting && q.envelope.entered && q.completed && !q.ack.submit_attempted && !q.failure.empty())
        state.may_have_submitted = false;
      failure = q.failure.empty() ? "sway native result unavailable" : q.failure; return false;
    }
    if (submitting) state.pending_ack = q.ack;
    if (q.receipt_mode) { state.pending_ack.reset(); state.may_have_submitted = false; }
    serialized = SerializeActiveSwayEnvelope12002(q, step, request_id);
    return true;
  } catch (...) { failure = "sway handler exception"; return false; }
}
} // namespace xar::ck3_12002
