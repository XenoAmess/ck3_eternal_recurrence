#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <string_view>

namespace xar::ck3_12004 {

// This is the extent through the last literal write at+166. It is not a
// native sizeof claim; any later bytes remain outside this source contract.
inline constexpr std::size_t kRootScopeInitializer889F60Extent12004 = 0x167;
inline constexpr std::size_t kRootScopeInitializer889F60DefinedBytes12004 = 155;

struct RootScopeInitializer889F60Source12004 {
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256;
  bool actual_12004_source_closed = false;
};

enum class RootScopeInitializer889F60Failure12004 : std::uint8_t {
  none,
  owned_storage_shape,
  source_binding,
  module_address,
};

struct RootScopeInitializer889F60Projection12004 {
  bool available = false;
  RootScopeInitializer889F60Failure12004 failure =
      RootScopeInitializer889F60Failure12004::none;
  std::size_t defined_byte_count = 0;
};

// Project only source-defined final fields into caller-owned storage. Mask
// entries are0/1; untouched raw bytes are not read, copied or zero-filled.
// Root+18 and+28 self pointers refer to this owned storage, so reapply after
// relocating storage. No native initializer, frame/epoch or stack identity
// is supplied. Callers own the later wordkind4 and qwordOwnerFullID stores.
RootScopeInitializer889F60Projection12004 ProjectOwnedRootScopeInitializer889F6012004(
    const RootScopeInitializer889F60Source12004 &source,
    std::span<std::byte> owned_scope,
    std::span<std::uint8_t> defined_bytes) noexcept;

} // namespace xar::ck3_12004
