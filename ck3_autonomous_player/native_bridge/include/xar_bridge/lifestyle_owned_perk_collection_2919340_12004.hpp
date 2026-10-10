#pragma once

#include "xar_bridge/lifestyle_perk_predicate_inputs_12004.hpp"

namespace xar::ck3_12004::lifestyle {

inline constexpr std::uintptr_t kLifestyleOwnedPerkCollectionGetterRva12004 = 0x2919340;
inline constexpr std::uintptr_t kLifestyleOwnedPerkStaticCollectionRva12004 = 0x54E78B8;
inline constexpr std::uintptr_t kLifestyleOwnedPerkStaticGuardRva12004 = 0x5D67FDC;

enum class LifestyleOwnedPerkGetterBranch12004 : std::uint8_t {
  unavailable,
  character_extension,
  static_fast_return,
  static_epoch_slow_path,
};

// Owns copied operands and an optional source-equivalent return identity.
// An address is an identity, not a borrowed native object or copied collection.
// The caller passes the return to the existing A11CC0 readonly membership reader.
struct LifestyleOwnedPerkCollectionGetter12004 {
  std::uintptr_t character_identity = 0;
  std::optional<std::uintptr_t> extension_identity_raw{};
  std::optional<std::uintptr_t> current_thread_tls_array_identity_raw{};
  std::optional<std::uintptr_t> tls_slot_zero_identity_raw{};
  std::optional<std::int32_t> tls_epoch_raw_i32{};
  std::optional<std::int32_t> static_guard_raw_i32{};
  std::optional<std::uintptr_t> returned_collection_identity{};
  LifestyleOwnedPerkGetterBranch12004 branch = LifestyleOwnedPerkGetterBranch12004::unavailable;
  std::string unavailable_reason{};
};

// Nonnull Character+1B0 returns extension+220 without reading TLS or a header.
// Null uses the caller's same application-thread GS58 raw input and literal
// [TLS array]+10 epoch path. Only signed guard<=epoch closes the fast return.
// Missing inputs and the unmodeled epoch slow path retain unknown; no native
// getter, initializer, membership routine or complete CanSelect is executed.
// Every initial/prerequisite demand must call this reader independently.
LifestyleOwnedPerkCollectionGetter12004 ReadLifestyleOwnedPerkCollection291934012004(
    const LifestylePerkReadonlyAccess12004 &, std::uintptr_t character_identity) noexcept;

} // namespace xar::ck3_12004::lifestyle
