#include "xar_bridge/ck3_12003_war_cash_current_mailbox.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

namespace xar::ck3_12003::war_cash_current {

bool ExecuteCurrentResourcesMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr ||
      !ck3_12002::EnterQueryMailbox(*envelope, stamp,
                                 &ExecuteCurrentResourcesMailboxV1)) return false;
  auto &query = *static_cast<CurrentResourcesMailboxContextV1 *>(envelope->typed_context);
  if (envelope != &query.envelope || query.completed ||
      !game::IsCk3_12003Descriptor(envelope->game->descriptor())) return false;
  // Even an unavailable or partial field read is a completed observation.
  // FinishQueryMailbox supplies the same-frame result separately.
  (void)game::ReadCk3_12003WarCashCurrentResourcesV1(
      *envelope->game, envelope->expected_snapshot, query.observation);
  query.completed = true;
  return ck3_12002::FinishQueryMailbox(*envelope);
}

} // namespace xar::ck3_12003::war_cash_current
