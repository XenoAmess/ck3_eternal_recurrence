#include "xar_bridge/root_scope_initializer_889f60_12004.hpp"

#include <limits>

namespace xar::ck3_12004 {
namespace {
static_assert(sizeof(std::uintptr_t) == 8);

constexpr std::string_view kActualSha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

bool ExactSha(std::string_view supplied) noexcept {
  if (supplied.size() != kActualSha.size()) return false;
  for (std::size_t i = 0; i < kActualSha.size(); ++i) {
    char c = supplied[i];
    if (c >= 'a' && c <= 'f') c = static_cast<char>(c - 'a' + 'A');
    if (c != kActualSha[i]) return false;
  }
  return true;
}

void Put(std::span<std::byte> raw, std::span<std::uint8_t> mask,
          std::size_t offset, std::size_t width, std::uint64_t value) noexcept {
  for (std::size_t i = 0; i < width; ++i) {
    raw[offset + i] = static_cast<std::byte>((value >> (i * 8)) & 0xFFu);
    mask[offset + i] = 1;
  }
}
} // namespace

RootScopeInitializer889F60Projection12004 ProjectOwnedRootScopeInitializer889F6012004(
    const RootScopeInitializer889F60Source12004 &source,
    std::span<std::byte> owned_scope,
    std::span<std::uint8_t> defined_bytes) noexcept {
  RootScopeInitializer889F60Projection12004 result{};
  if (owned_scope.size() < kRootScopeInitializer889F60Extent12004 ||
      defined_bytes.size() != owned_scope.size()) {
    result.failure = RootScopeInitializer889F60Failure12004::owned_storage_shape;
    return result;
  }
  for (auto &defined : defined_bytes) defined = 0;
  if (!source.actual_12004_source_closed || !ExactSha(source.executable_sha256)) {
    result.failure = RootScopeInitializer889F60Failure12004::source_binding;
    return result;
  }
  if (source.module_base == 0 ||
      source.module_base > std::numeric_limits<std::uintptr_t>::max() - 0x54DE2E0) {
    result.failure = RootScopeInitializer889F60Failure12004::module_address;
    return result;
  }
  const auto self = reinterpret_cast<std::uintptr_t>(owned_scope.data());
  const auto module = source.module_base;
  // Actual889F60 own pre-child stores.
  Put(owned_scope, defined_bytes, 0x00, 4, 0);
  Put(owned_scope, defined_bytes, 0x08, 8, 0);
  Put(owned_scope, defined_bytes, 0x10, 4, 0xFFFFFFFFu);

  // Only proper actual8895D0 final effects, translated by literalRCX=root+18.
  // Source48c closed both mandatory actual virtual slots before this packet.
  Put(owned_scope, defined_bytes, 0x18, 8, self + 0x38);
  Put(owned_scope, defined_bytes, 0x20, 4, 8);
  Put(owned_scope, defined_bytes, 0x24, 4, 0);
  Put(owned_scope, defined_bytes, 0x28, 8, self + 0x30);
  Put(owned_scope, defined_bytes, 0x30, 8, module + 0x448D2A0);
  Put(owned_scope, defined_bytes, 0xF8, 8, module + 0x54DE2E0);

  // Actual889F60 own normal-return stores, without other outer layouts.
  Put(owned_scope, defined_bytes, 0x100, 8, 0);
  Put(owned_scope, defined_bytes, 0x108, 8, 0);
  Put(owned_scope, defined_bytes, 0x110, 8, module + 0x54DE270);
  Put(owned_scope, defined_bytes, 0x118, 8, module + 0x448D1F8);
  Put(owned_scope, defined_bytes, 0x120, 8, module + 0x448D268);
  Put(owned_scope, defined_bytes, 0x128, 8, 0);
  Put(owned_scope, defined_bytes, 0x130, 8, 0);
  Put(owned_scope, defined_bytes, 0x138, 8, module + 0x54DE278);
  Put(owned_scope, defined_bytes, 0x140, 4, 0);
  Put(owned_scope, defined_bytes, 0x148, 8, 0);
  Put(owned_scope, defined_bytes, 0x150, 8, 0);
  Put(owned_scope, defined_bytes, 0x158, 8, module + 0x54DE270);
  Put(owned_scope, defined_bytes, 0x160, 4, 0xFFFFFFFFu);
  Put(owned_scope, defined_bytes, 0x164, 2, 0);
  Put(owned_scope, defined_bytes, 0x166, 1, 0);
  result.available = true;
  result.defined_byte_count = kRootScopeInitializer889F60DefinedBytes12004;
  return result;
}

} // namespace xar::ck3_12004
