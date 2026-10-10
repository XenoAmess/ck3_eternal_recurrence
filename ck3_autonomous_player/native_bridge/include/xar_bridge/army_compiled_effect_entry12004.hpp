#pragma once

#include <cstddef>
#include <cstdint>
#include <type_traits>
#include <utility>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kArmyCompiledEffectWrapperRva12004 = 0x3765760;
inline constexpr std::uintptr_t kArmyCompiledEffectSeedRva12004 = 0x37652B0;
inline constexpr std::uintptr_t kArmyCompiledEffectFlagRva12004 = 0x5D1DADC;

enum class ArmyCompiledEffectRoute12004 : std::uint8_t {
  Unknown, Army1d8Plus40, EntrySavedArmy1d8Plus230
};

inline ArmyCompiledEffectRoute12004 ArmyCompiledEffectRouteForReturn12004(
    std::uintptr_t caller_return_rva) noexcept {
  if (caller_return_rva == 0x2639CA4)
    return ArmyCompiledEffectRoute12004::Army1d8Plus40;
  if (caller_return_rva == 0x24DD7B6)
    return ArmyCompiledEffectRoute12004::EntrySavedArmy1d8Plus230;
  return ArmyCompiledEffectRoute12004::Unknown;
}

// Source-derived arithmetic only. Callers must first establish seed >= 0.
inline std::uint32_t ArmyCompiledEffectSeedFromNonnegative12004(
    std::uint32_t seed) noexcept {
  std::uint32_t value = 0x5EA6BA9Fu - seed * 0x4AD685B3u;
  value = (value ^ (value >> 8)) + 0x68E31DA4u;
  value ^= value << 8;
  value *= 0x1B56C4E9u;
  value ^= value >> 8;
  value *= 0x92D68CA2u;
  return value ^ (value >> 8);
}

// Values are supplied by the actual owning-thread ingress. This leaf cannot
// mint a frame/revision, sequence or parent invocation from a query date.
struct ArmyCompiledEffectIngress12004 {
  bool bound = false;
  std::uint64_t native_sequence = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t frame_key = 0;
  std::uint64_t thread_key = 0;
  std::uint64_t parent_invocation_key = 0;
  std::uintptr_t caller_return_rva = 0;
};

inline bool ArmyCompiledEffectIngressBound12004(
    const ArmyCompiledEffectIngress12004& ingress) noexcept {
  return ingress.bound && ingress.native_sequence != 0
      && ingress.frame_key != 0 && ingress.thread_key != 0
      && ingress.parent_invocation_key != 0
      && ArmyCompiledEffectRouteForReturn12004(ingress.caller_return_rva)
         != ArmyCompiledEffectRoute12004::Unknown;
}

struct ArmyCompiledEffectEntry12004 {
  ArmyCompiledEffectIngress12004 ingress{};
  ArmyCompiledEffectRoute12004 route = ArmyCompiledEffectRoute12004::Unknown;
  std::uintptr_t receiver_token = 0;
  std::uintptr_t caller_context_token = 0;
  bool kind_read = false, payload_read = false, seed_read = false;
  bool flag_read = false, effect_key_read = false;
  std::uint16_t scope_kind = 0;
  std::uint64_t scope_payload = 0;
  std::int32_t scope_seed = 0;
  std::uint8_t evaluation_flag = 0;
  std::uint32_t effect_key = 0;
  bool conditional_rng_pair_known = false;
  std::uint32_t conditional_rng_seed = 0;
  std::uint32_t conditional_rng_counter = 0;
  bool original_returned = false;
  bool history_or_material_postimage_observed = false;
};

using ArmyCompiledEffectRead12004 = bool (*)(
    void*, std::uintptr_t, void*, std::size_t) noexcept;
using ArmyCompiledEffectPublish12004 = void (*)(
    void*, const ArmyCompiledEffectEntry12004&) noexcept;

inline ArmyCompiledEffectEntry12004 CaptureArmyCompiledEffectEntry12004(
    const ArmyCompiledEffectIngress12004& ingress,
    std::uintptr_t module_base, const void* receiver, const void* caller_context,
    ArmyCompiledEffectRead12004 read, void* reader_context) noexcept {
  ArmyCompiledEffectEntry12004 event{};
  event.ingress = ingress;
  event.route = ArmyCompiledEffectRouteForReturn12004(ingress.caller_return_rva);
  event.receiver_token = reinterpret_cast<std::uintptr_t>(receiver);
  event.caller_context_token = reinterpret_cast<std::uintptr_t>(caller_context);
  if (!ArmyCompiledEffectIngressBound12004(ingress)
      || !read || !receiver || !caller_context) return event;
  const auto scope = event.caller_context_token;
  event.kind_read = read(reader_context, scope, &event.scope_kind, sizeof(event.scope_kind));
  event.payload_read = read(reader_context, scope + 8, &event.scope_payload, sizeof(event.scope_payload));
  event.seed_read = read(reader_context, scope + 0x10, &event.scope_seed, sizeof(event.scope_seed));
  if (module_base)
    event.flag_read = read(reader_context, module_base + kArmyCompiledEffectFlagRva12004,
                          &event.evaluation_flag, sizeof(event.evaluation_flag));
  if (event.seed_read && event.scope_seed >= 0) {
    event.conditional_rng_pair_known = true;
    event.conditional_rng_seed = ArmyCompiledEffectSeedFromNonnegative12004(
        static_cast<std::uint32_t>(event.scope_seed));
  } else if (event.seed_read) {
    event.effect_key_read = read(reader_context, event.receiver_token + 0x2C,
                                &event.effect_key, sizeof(event.effect_key));
  }
  return event;
}

// Root must bind this to a naturally reached actual3765760 detour, preserving
// the original ABI/trampoline. No installer or native call binding is created
// here. The original runs exactly once even with disabled/failed observation.
// Publisher owns sequencing/storage and receives only completed invocations.
template <class Original>
decltype(auto) ObserveArmyCompiledEffectOriginalOnce12004(
    Original&& original, const ArmyCompiledEffectIngress12004& ingress,
    std::uintptr_t module_base, const void* receiver, const void* caller_context,
    ArmyCompiledEffectRead12004 read, void* reader_context,
    ArmyCompiledEffectPublish12004 publish, void* publisher_context) {
  auto event = CaptureArmyCompiledEffectEntry12004(
      ingress, module_base, receiver, caller_context, read, reader_context);
  using Result = std::invoke_result_t<Original, const void*, const void*>;
  if constexpr (std::is_void_v<Result>) {
    std::forward<Original>(original)(receiver, caller_context);
    event.original_returned = true;
    if (ArmyCompiledEffectIngressBound12004(ingress) && publish)
      publish(publisher_context, event);
  } else {
    Result result = std::forward<Original>(original)(receiver, caller_context);
    event.original_returned = true;
    if (ArmyCompiledEffectIngressBound12004(ingress) && publish)
      publish(publisher_context, event);
    return result;
  }
}

} // namespace xar::ck3_12004
