#include "xar_bridge/ck3_12003_player_mercenary_hire_mailbox.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

namespace xar::ck3_12003 {

bool BindPlayerMercenaryHireMailboxImageV1(PlayerMercenaryHireMailboxContextV1 &action,
    std::uintptr_t image_base, const game::AdapterDescriptor &descriptor) noexcept {
  if (image_base == 0 || !game::IsCk3_12003Descriptor(descriptor)) return false;
  action.core = ck3_12002::BindCoreImage(image_base,
      game::ReviewedCrozierAbiSha256(descriptor));
  action.bindings = mercenary::BindMercenaryHireActionImage12003(
      image_base, descriptor.executable_sha256);
  return action.core.enabled && action.bindings.enabled;
}

bool ExecutePlayerMercenaryHireMailboxV1(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr) return false;
  auto &action = *static_cast<PlayerMercenaryHireMailboxContextV1 *>(envelope->typed_context);
  try {
    if (envelope != &action.envelope || action.completed ||
        !ck3_12002::EnterQueryMailbox(*envelope, stamp,
            &ExecutePlayerMercenaryHireMailboxV1) ||
        !game::IsCk3_12003Descriptor(envelope->game->descriptor())) return false;
    const auto actor_id = static_cast<std::int32_t>(
        envelope->expected_snapshot.played_character_id);
    void *const actor = ck3_12002::ResolveCoreCharacter(action.core, actor_id);
    (void)mercenary::ApplyMercenaryHire12003(action.bindings, actor, actor_id,
        action.company_id, action.observation);
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
