#pragma once

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::game {

// Private exact-build observation; no public capability or action is added here.
enum class H2743StockPredicateStateV1 : std::uint8_t {
  unavailable = 0,
  observed_native_false = 1,
  observed_native_true = 2,
};

enum class H2743StockPredicateFailureV1 : std::uint8_t {
  none = 0,
  disabled,
  wrong_session,
  read_failed,
  stale_identity,
  cache_unavailable,
  bounded_extent_exceeded,
  identifier_unavailable,
  phase_unavailable,
  definition_unavailable,
  unstable_sample,
};

struct H2743StockPredicateValueV1 {
  H2743StockPredicateStateV1 state =
      H2743StockPredicateStateV1::unavailable;
  H2743StockPredicateFailureV1 failure =
      H2743StockPredicateFailureV1::disabled;
  friend bool operator==(const H2743StockPredicateValueV1 &,
                         const H2743StockPredicateValueV1 &) = default;
};

struct H2743StockPredicateStampV1 {
  std::uint32_t actor_id = 0;
  std::uint32_t war_id = 0;
  std::int64_t date_raw = 0;
  std::uint64_t revision = 0;
  std::uint64_t native_revision = 0;
  bool paused = false;
  bool living_map = false;
  friend bool operator==(const H2743StockPredicateStampV1 &,
                         const H2743StockPredicateStampV1 &) = default;
};

using H2743StockReadBytesV1 = bool (*)(void *, std::uintptr_t, void *,
                                     std::size_t) noexcept;
using H2743StockLookupIdentifierV1 = bool (*)(void *, std::string_view,
                                             std::int32_t &) noexcept;
using H2743StockHashNameV1 = bool (*)(void *, std::string_view,
                                    std::uint32_t &) noexcept;
using H2743StockReadStampV1 = bool (*)(void *,
                                     H2743StockPredicateStampV1 &) noexcept;

struct H2743StockPredicateBindingsV1 {
  void *opaque = nullptr;
  std::uintptr_t module_base = 0;
  bool enabled = false;
  bool exact_build_verified = false;
  bool application_main_verified = false;
  H2743StockReadBytesV1 read_bytes = nullptr;
  // Must use lookup-only 0x3B588E0 and 0x3B58970 full-name roundtrip.
  // Missing identifier 12 is unavailable. The interner is not an input API.
  H2743StockLookupIdentifierV1 lookup_identifier = nullptr;
  H2743StockHashNameV1 hash_name = nullptr;
  H2743StockReadStampV1 read_stamp = nullptr;
};

struct H2743StockPredicateResultV1 {
  H2743StockPredicateStampV1 stamp{};
  std::uint32_t attacker_id = 0;
  std::uint32_t defender_id = 0;
  H2743StockPredicateValueV1 short_truce{};
  H2743StockPredicateValueV1 long_truce{};
  H2743StockPredicateValueV1 border_raid_pair{};
  bool double_sample_stable = false;
  bool material_complete = false;
};

// Bounded raw reads of the stock caches and phase parameters. The caller must
// dispatch this synchronously through a registered application-main executor.
H2743StockPredicateResultV1 ReadH2743StockPredicatesV1(
    const H2743StockPredicateBindingsV1 &bindings,
    const H2743StockPredicateStampV1 &expected);

// Windows binding owner must survive one synchronous callback. The stamp
// observer is supplied by the actual bridge, never by a profile or sidecar.
struct H2743StockNativeContextV1 {
  std::uintptr_t module_base = 0;
  std::uint32_t application_main_thread_id = 0;
  bool exact_build_verified = false;
  void *stamp_opaque = nullptr;
  H2743StockReadStampV1 observe_stamp = nullptr;
};

// Default-off native adapter. It calls only read-only identifier lookup/name
// resolution and the stable hash; it never calls a DB lazy getter or evaluator.
H2743StockPredicateBindingsV1 BindH2743StockNativeSourcesV1(
    H2743StockNativeContextV1 &context) noexcept;

} // namespace xar::game
