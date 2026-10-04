#include "xar_bridge/ck3_12003_player_mercenary_mailbox.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

#include <cstring>
#include <windows.h>

namespace xar::ck3_12003 {
namespace {

bool ReadMercenaryWorldMemory(void *, const void *source, void *destination,
                             std::size_t size) noexcept {
  if (source == nullptr || destination == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(destination, source, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

const void *ResolveMercenaryWorldTitle(void *opaque,
                                      std::int32_t full_id) noexcept {
  const auto *world = static_cast<const ck3_12002::ProvinceBindings *>(opaque);
  if (world == nullptr) return nullptr;
  return ck3_12002::ResolveObjectiveTitle(*world, full_id);
}

const void *ResolveMercenaryWorldProvince(void *opaque,
                                         std::int32_t province_id) noexcept {
  const auto *world = static_cast<const ck3_12002::ProvinceBindings *>(opaque);
  if (world == nullptr) return nullptr;
  return ck3_12002::ResolveObjectiveProvince(*world, province_id);
}

} // namespace

bool BindPlayerMercenaryMailboxImageV1(PlayerMercenaryMailboxContextV1 &query,
    std::uintptr_t image_base, const game::AdapterDescriptor &descriptor) noexcept {
  if (image_base == 0 || !game::IsCk3_12003Descriptor(descriptor)) return false;
  const auto reviewed_sha = game::ReviewedCrozierAbiSha256(descriptor);
  query.core = ck3_12002::BindCoreImage(image_base, reviewed_sha);
  // The exact .3 title-holder and military-world paths reuse these reviewed
  // full-reference storage and current Province array bindings.
  query.provinces = ck3_12002::BindProvinceImage(image_base, reviewed_sha);
  query.bindings.candidates = mercenary::BindMercenaryCandidatesImage12003(
      image_base, descriptor.executable_sha256);
  query.bindings.final_terms = mercenary::BindMercenaryFinalTermsImage12003(
      image_base, descriptor.executable_sha256);
  query.bindings.composition = mercenary::BindMercenaryCompositionImage12003(
      image_base, descriptor.executable_sha256);
  query.bindings.position.get_title_province =
      reinterpret_cast<decltype(query.bindings.position.get_title_province)>(
          image_base + kMercenaryTitleProvinceRvaV1);
  query.bindings.position.select_hire_raise_province =
      reinterpret_cast<decltype(query.bindings.position.select_hire_raise_province)>(
          image_base + kMercenaryHireRaiseSelectorRvaV1);
  query.bindings.world.context = &query.provinces;
  query.bindings.world.read_memory = &ReadMercenaryWorldMemory;
  query.bindings.world.resolve_title = &ResolveMercenaryWorldTitle;
  query.bindings.world.resolve_province = &ResolveMercenaryWorldProvince;
  return query.core.enabled && query.provinces.enabled &&
      query.bindings.candidates.enabled && query.bindings.final_terms.enabled &&
      query.bindings.composition.enabled;
}

bool ExecutePlayerMercenaryMailboxV1(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr) return false;
  auto &query = *static_cast<PlayerMercenaryMailboxContextV1 *>(envelope->typed_context);
  try {
    if (envelope != &query.envelope || query.completed ||
        !ck3_12002::EnterQueryMailbox(*envelope, stamp,
            &ExecutePlayerMercenaryMailboxV1) ||
        !game::IsCk3_12003Descriptor(envelope->game->descriptor())) return false;
    const auto &frame = envelope->expected_snapshot;
    const auto actor_id = static_cast<std::int32_t>(frame.played_character_id);
    void *const actor = ck3_12002::ResolveCoreCharacter(query.core, actor_id);
    (void)mercenary::ReadPlayerMercenaryContext12003(query.bindings, actor,
        actor_id, static_cast<std::int32_t>(frame.date_raw), stamp.pump_epoch,
        query.observation);
    query.completed = true;
    return ck3_12002::FinishQueryMailbox(*envelope);
  } catch (...) {
    return false;
  }
}

} // namespace xar::ck3_12003
