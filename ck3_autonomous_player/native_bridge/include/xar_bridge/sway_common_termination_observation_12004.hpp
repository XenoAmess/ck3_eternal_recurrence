#pragma once

#include "xar_bridge/ck3_12004.hpp"

#include <cstdint>
#include <type_traits>

namespace xar::ck3_12004 {

// Relocated unchanged from sway_end_invocation_12004.hpp. The existing
// observer owns session lifecycle, thread admission and invocation allocation.
struct SwayEndInvocationStamp12004 {
  std::uint64_t observer_session_identity = 0;
  std::uint32_t owner_thread_id = 0;
  std::uint64_t invocation_id = 0;
  bool incoming_return_address_observed = false;
  std::uintptr_t caller_return_rva = 0;
};

inline constexpr std::uintptr_t kSwayCommonTerminationCallsiteRva12004 =
    0x2A48877;
inline constexpr std::uintptr_t kSwayCommonTerminationOriginalRva12004 =
    0x2A4ADF0;
inline constexpr std::uintptr_t kSwayCommonTerminationCallerReturnRva12004 =
    0x2A4887C;

// Owned copies from the actual Scheme operand at one native boundary.
// No native Scheme, definition, storage or current-frame pointer is retained.
// Every raw field has its own read flag; a default value is never a read.
struct SwayCommonTerminationFrame12004 {
  // Actual instance vptr, Schm marker and sway definition checks succeeded.
  // This does not assert that a storage slot contains the instance.
  bool scheme_header_observed = false;
  bool scheme_full_id_observed = false;
  std::uint32_t scheme_full_id_raw_u32 = 0xFFFFFFFFu; // Scheme+0x10.
  std::uint8_t scheme_instance_generation_u8 = 0; // Full ID >> 24 only.
  bool status_observed = false;
  std::int32_t status_raw_i32 = 0; // Scheme+0x28; no cause classification.
  bool owner_observed = false;
  std::uint32_t owner_character_full_id_raw_u32 = 0xFFFFFFFFu; // +0x2C.
  bool other_kind_observed = false;
  std::uint32_t other_kind_raw_u32 = 0; // +0x30; independent of status.
  // A character target is copied from +0x34 only when the observed kind is 0.
  bool target_observed = false;
  std::uint32_t target_character_full_id_raw_u32 = 0xFFFFFFFFu;
  // Copy only an already supplied current native observer frame. Missing
  // provenance stays false; no later query or native clock getter fills it.
  bool core_frame_observed = false;
  CoreSnapshotPrefix core_frame{};
};

// Neutral observation of the fixed current call above. It neither extends
// the three existing source classes nor assigns a terminal reason or Toast
// relationship. The actor for a query is the observed entry owner; the
// returned owner remains its independently copied raw value, including FF.
struct SwayCommonTerminationObservation12004 {
  SwayEndInvocationStamp12004 stamp{};
  bool incoming_dl_observed = false;
  std::uint8_t incoming_dl_raw_u8 = 0; // Preserve every value 0..255.
  SwayCommonTerminationFrame12004 entry{};
  bool original_forwarded_once = false;
  bool original_returned = false;
  SwayCommonTerminationFrame12004 returned{};
  // Reader-derived diagnostic: both actual header/full-ID reads succeeded
  // and compare all 32 bits. False/unknown does not mean an absent instance;
  // even true does not assert current storage membership or a terminal cause.
  bool return_same_scheme_full_id_observed = false;
  bool return_same_scheme_full_id = false;
};

static_assert(std::is_trivially_copyable_v<SwayEndInvocationStamp12004>);
static_assert(std::is_trivially_copyable_v<SwayCommonTerminationFrame12004>);
static_assert(std::is_trivially_copyable_v<SwayCommonTerminationObservation12004>);

} // namespace xar::ck3_12004
