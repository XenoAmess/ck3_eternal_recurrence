#pragma once

#include "xar_bridge/ck3_1210.hpp"
#include <cstdint>
#include <optional>

namespace xar::ck3_1210 {

// Internal ABI decoder only. The caller retains paused application-main/TLS
// custody and independently brackets this call with current Core/Full checks.
// decoded grants no available wire DTO, same-frame witness, capability,
// government routing, budget, Full/Root role, or native-call permission.
using NonCashReadMemoryV1 = bool (*)(void *, std::uintptr_t, void *,
    std::size_t) noexcept;
inline constexpr std::int64_t kNonCashRawScaleV1 = 100'000;
enum class NonCashResourceV1 { prestige, piety, dynasty_renown, government_treasury };
enum class NonCashDecodeStatusV1 {
  not_read, decoded, unsupported_build, invalid_resource, invalid_actor,
  read_failed, source_unavailable, source_changed
};
struct NonCashDecodeBindingsV1 {
  bool exact_build_admitted = false;
  std::uintptr_t house_storage_slot = 0;
  std::uintptr_t dynasty_storage_slot = 0;
  std::uintptr_t title_storage_slot = 0;
};
struct NonCashRawDecodeV1 {
  NonCashDecodeStatusV1 status = NonCashDecodeStatusV1::not_read;
  std::optional<std::int64_t> raw;
  std::int64_t scale = kNonCashRawScaleV1;
  // actor for prestige/piety, dynasty for renown, primary title for treasury.
  // Empty on a proven native treasury zero branch with no primary title.
  std::optional<std::int32_t> source_full_id;
  bool native_zero_branch = false;
};

// Address calculation only; the supplied digest must be the exact Florin hash.
NonCashDecodeBindingsV1 BindNonCashDecodeImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

// Two independent pointer/ID/value samples must agree. Signed full32 zero and
// high-bit IDs are valid; only -1 is absent. Raw signed Q100000 is copied with
// no clamping or floating conversion. A failed/unresolved read clears raw;
// default/fallback objects never become observed zero.
// Scope is an independently resolved ALIVE actor. Renown is shared dynasty
// property, not personal prestige or proof that the actor may spend it.
// Treasury follows native GetTreasury: null living, null alive land, or empty
// primary-title vector yield lawful zero; stale/unreadable title does not.
bool DecodeNonCashRawV1(const NonCashDecodeBindingsV1 &bindings,
    NonCashReadMemoryV1 read, void *context, std::uintptr_t actor,
    std::int32_t expected_actor_full_id, NonCashResourceV1 resource,
    NonCashRawDecodeV1 &output) noexcept;

} // namespace xar::ck3_1210
