#include "xar_bridge/current_actor_stress_adjustment_v1_mailbox.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include <windows.h>

namespace xar::ck3_12003 {

bool ExecuteCurrentActorStressAdjustmentMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr ||
      !ck3_12002::EnterQueryMailbox(
          *envelope, stamp, &ExecuteCurrentActorStressAdjustmentMailboxV1))
    return false;
  auto &query = *static_cast<CurrentActorStressAdjustmentMailboxContextV1 *>(
      envelope->typed_context);
  if (envelope != &query.envelope || query.completed ||
      !game::IsCk3_12003Descriptor(envelope->game->descriptor()) ||
      query.request.expected_revision != envelope->expected_snapshot_revision ||
      query.request.expected_game_pid != GetCurrentProcessId() ||
      stamp.thread_id != GetCurrentThreadId() ||
      stamp.tls_initialized_flag_address == 0 ||
      stamp.tls_initialized != 1 || stamp.tls_main_thread_marker != 1 ||
      stamp.tls_context == 0 || stamp.pump_epoch == 0) return false;
  const auto bindings = BindCurrentActorStressAdjustmentImageV1(
      query.image_base, envelope->game->descriptor().executable_sha256);
  CurrentActorStressAdjustmentAccessV1 access{};
  access.context = envelope;
  access.capture_frame = &ck3_12002::CaptureQuerySnapshot;
  access.is_owning_thread = &ck3_12002::IsQueryOwningThread;
  query.observation.owner_thread_verified = true;
  query.observation.tls_verified = true;
  query.observation.owner_thread_id = stamp.thread_id;
  query.observation.owner_pump_epoch = stamp.pump_epoch;
  ReadCurrentActorStressAdjustmentV1(bindings, access, query.request,
      envelope->expected_snapshot, query.observation);
  query.completed = true;
  const bool finished = ck3_12002::FinishQueryMailbox(*envelope);
  if (!finished) MakeCurrentActorStressAdjustmentUnavailableV1(
      query.observation, "owner_completion_frame_changed");
  return finished;
}

} // namespace xar::ck3_12003
