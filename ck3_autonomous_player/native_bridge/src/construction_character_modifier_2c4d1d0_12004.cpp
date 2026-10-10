#include "xar_bridge/construction_character_modifier_2c4d1d0_12004.hpp"

#include <limits>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {
constexpr std::uintptr_t kCharacterFallbackSlot = 0x5C67570;
constexpr const char *kExactSha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

bool ReadCopiedMemory(void *opaque, const void *address,
                      void *output, std::size_t size) noexcept {
  const auto &access = *static_cast<const RawReceiverAccessV1 *>(opaque);
  try {
    return access.read_memory != nullptr &&
        access.read_memory(access.context, address, output, size);
  } catch (...) {
    return false;
  }
}

bool ReadContextMemory(void *opaque, std::uintptr_t address,
                       void *output, std::size_t size) noexcept {
  return ReadCopiedMemory(opaque, reinterpret_cast<const void *>(address),
                          output, size);
}

template<class T>
bool ReadRaw(const RawReceiverAccessV1 &access, std::uintptr_t base,
             std::size_t offset, T &output) noexcept {
  if (base == 0 || offset > std::numeric_limits<std::uintptr_t>::max() - base)
    return false;
  return ReadCopiedMemory(const_cast<RawReceiverAccessV1 *>(&access),
      reinterpret_cast<const void *>(base + offset), &output, sizeof(output));
}
} // namespace

CharacterModifier2C4D1D012004 ReadCharacterModifier2C4D1D012004(
    const RawReceiverAccessV1 &access, std::uintptr_t character,
    std::uint16_t key, std::uintptr_t detail, std::int64_t scale) noexcept {
  CharacterModifier2C4D1D012004 result;
  result.character_identity = character;
  result.key_raw_u16 = key;
  result.detail_identity = detail;
  result.scale_raw_q64 = scale;
  try {
    const auto fail = [&](CharacterModifierFailure2C4D1D012004 failure,
                          const char *reason) {
      result.ready = false;
      result.failure = failure;
      result.reason = reason;
      result.value_raw_q64.reset();
      return result;
    };
    if (!access.exact_12004_bound || access.module_base == 0)
      return fail(CharacterModifierFailure2C4D1D012004::exact_build,
                   "exact_12004_modifier_access_unavailable");
    if (access.read_memory == nullptr)
      return fail(CharacterModifierFailure2C4D1D012004::read_callback,
                   "modifier_read_callback_unavailable");
    if (detail != 0)
      return fail(CharacterModifierFailure2C4D1D012004::detail_branch_not_supplied,
                   "actual_modifier_detail_sideeffects_not_supplied");

    std::uint32_t physical_id = 0;
    if (!ReadRaw(access, character, 0x18, physical_id))
      return fail(CharacterModifierFailure2C4D1D012004::character_identity_read,
                   "modifier_physical_character_identity_unavailable");
    result.physical_character_id_raw_u32 = physical_id;
    if (physical_id == 0xFFFFFFFFu) {
      std::uintptr_t fallback = 0;
      if (!ReadRaw(access, access.module_base, kCharacterFallbackSlot, fallback) ||
          fallback != character)
        return fail(CharacterModifierFailure2C4D1D012004::fallback_receiver_unqualified,
                     "modifier_source_fallback_receiver_unqualified");
      result.fallback_character_identity = fallback;
      result.source_qualified_fallback = true;
    }

    // RawReceiverAccessV1's exact-build token belongs to the real parent.
    // These two adapters forward every copy to that same access/context.
    const auto context_bindings = BindConceptionModifierContext12004(
        access.module_base, "1.20.0.4", kExactSha, &ReadContextMemory,
        const_cast<RawReceiverAccessV1 *>(&access));
    result.context = ResolveRawCharacterModifierContext12004(
        context_bindings, character, physical_id,
        result.source_qualified_fallback);
    if (!result.context.ready)
      return fail(CharacterModifierFailure2C4D1D012004::modifier_context,
                   result.context.reason.c_str());

    // Getter selection precedes the actual scalar call, including factor0.
    // A factor0 cannot make an unobserved/lazy default getter ready.
    const LoadedInputAccessV1 scalar_access{
        const_cast<RawReceiverAccessV1 *>(&access), &ReadCopiedMemory,
        access.exact_12004_bound};
    result.scalar = ReadScaledCollectionKey12004(
        scalar_access, result.context.context_address, key, scale, 0, 0);
    if (!result.scalar.ready || !result.scalar.scaled_value_raw_q64.has_value())
      return fail(CharacterModifierFailure2C4D1D012004::scaled_key,
                   "modifier_scaled_key_unavailable");

    std::string changed_reason;
    if (!CheckRawCharacterModifierContextStillCurrent12004(
            context_bindings, result.context, physical_id,
            result.source_qualified_fallback, changed_reason))
      return fail(CharacterModifierFailure2C4D1D012004::modifier_context_changed,
                   changed_reason.c_str());
    if (result.source_qualified_fallback) {
      std::uintptr_t after_fallback = 0;
      if (!ReadRaw(access, access.module_base, kCharacterFallbackSlot, after_fallback) ||
          after_fallback != *result.fallback_character_identity)
        return fail(CharacterModifierFailure2C4D1D012004::fallback_receiver_changed,
                     "modifier_source_fallback_receiver_changed");
    }
    result.value_raw_q64 = result.scalar.scaled_value_raw_q64;
    result.ready = true;
    return result;
  } catch (...) {
    result.ready = false;
    result.failure = CharacterModifierFailure2C4D1D012004::copy_exception;
    result.reason.clear();
    result.value_raw_q64.reset();
    return result;
  }
}
} // namespace xar::ck3_12004::construction_owner_mode3
