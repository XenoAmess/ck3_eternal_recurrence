#include "xar_bridge/ck3_12003_player_holy_order_hire_mailbox.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_holy_order_bindings.hpp"

namespace xar::ck3_12003 {

bool BindPlayerHolyOrderHireMailboxImageV1(PlayerHolyOrderHireMailboxContextV1 &action,
    std::uintptr_t image_base, const game::AdapterDescriptor &descriptor) noexcept {
  const bool actual4 = game::IsCk3_12004Descriptor(descriptor);
  if (image_base == 0 || (!game::IsCk3_12003Descriptor(descriptor) && !actual4)) return false;
  if (actual4) {
    action.core = ck3_12004::BindCoreImage(image_base, descriptor.executable_sha256);
    action.bindings = ck3_12004::religion::holy_order::BindHolyOrderHireActionImage12004(
        image_base, descriptor.executable_sha256);
  } else {
    action.core = ck3_12002::BindCoreImage(image_base,
        game::ReviewedCrozierAbiSha256(descriptor));
    action.bindings = religion::holy_order::BindHolyOrderHireActionImage12003(
        image_base, descriptor.executable_sha256);
  }
  return action.core.enabled && action.bindings.enabled;
}

bool ExecutePlayerHolyOrderHireMailboxV1(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr) return false;
  auto &action = *static_cast<PlayerHolyOrderHireMailboxContextV1 *>(envelope->typed_context);
  try {
    if (envelope != &action.envelope || action.completed ||
        !ck3_12002::EnterQueryMailbox(*envelope, stamp,
            &ExecutePlayerHolyOrderHireMailboxV1) ||
        (!game::IsCk3_12003Descriptor(envelope->game->descriptor()) &&
         !game::IsCk3_12004Descriptor(envelope->game->descriptor()))) return false;
    const auto actor_id = static_cast<std::int32_t>(
        envelope->expected_snapshot.played_character_id);
    void *const actor = game::IsCk3_12004Descriptor(envelope->game->descriptor())
        ? ck3_12004::ResolveCoreCharacter(action.core, actor_id)
        : ck3_12002::ResolveCoreCharacter(action.core, actor_id);
    (void)religion::holy_order::ApplyHolyOrderHire12003(action.bindings, actor, actor_id,
        action.holy_order_id, envelope->expected_snapshot.date_raw,
        stamp.pump_epoch, action.observation);
    // The copied provider result records native rejection or owned queue
    // acceptance. A queued mutation can alter the admitted world frame;
    // independent current employer/army readback verifies its game outcome.
    action.completed = true;
    return true;
  } catch (...) {
    return false;
  }
}

} // namespace xar::ck3_12003
