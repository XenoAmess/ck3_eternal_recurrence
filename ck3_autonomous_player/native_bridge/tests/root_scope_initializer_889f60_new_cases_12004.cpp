#include "xar_bridge/root_scope_initializer_889f60_12004.hpp"

#include <array>
#include <source_location>
#include <stdexcept>
#include <string>
#include <limits>

namespace {
using namespace xar::ck3_12004;
void Require(bool condition,
             const std::source_location &location = std::source_location::current()) {
  if (!condition) throw std::runtime_error(
      "root scope initializer889F60 case failed at line " + std::to_string(location.line()));
}
constexpr std::string_view kSha =
    "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";

std::uint64_t Qword(const std::array<std::byte, 0x170> &raw,
                    std::size_t offset) {
  std::uint64_t value = 0;
  for (std::size_t i = 0; i < 8; ++i)
    value |= static_cast<std::uint64_t>(std::to_integer<std::uint8_t>(raw[offset+i])) << (8*i);
  return value;
}
} // namespace

// Only new15f projection/owned-relocation cases; 26's sole fresh clergy compound after10 admission
// imports this fragment. No main or standalone execution is provided.
void RunRootScopeInitializer889F6012004NewCases() {
  {
    std::array<std::byte, 0x170> raw;
    raw.fill(std::byte{0xA5});
    std::array<std::uint8_t, 0x170> mask;
    mask.fill(1);
    const auto result = ProjectOwnedRootScopeInitializer889F6012004(
        {0x10000000, kSha, true}, raw, mask);
    Require(result.available && result.defined_byte_count == 155);
    std::size_t actual_count = 0;
    for (std::size_t i = 0; i < raw.size(); ++i) {
      const bool expected = i < 4 || (i >= 8 && i < 0x14) ||
          (i >= 0x18 && i < 0x38) || (i >= 0xF8 && i < 0x144) ||
          (i >= 0x148 && i < 0x167);
      Require((mask[i] != 0) == expected);
      if (!expected) Require(raw[i] == std::byte{0xA5});
      else ++actual_count;
    }
    Require(actual_count == 155);
    Require(raw[0] == std::byte{0}); // kind4 is the caller's later store.
    Require(Qword(raw, 8) == 0); // no Owner payload invented by initializer.
    Require(Qword(raw, 0x18) == reinterpret_cast<std::uintptr_t>(raw.data()) + 0x38);
    Require(Qword(raw, 0x28) == reinterpret_cast<std::uintptr_t>(raw.data()) + 0x30);
    Require(Qword(raw, 0x30) == 0x1448D2A0);
    Require(Qword(raw, 0x110) == 0x154DE270);
    Require(Qword(raw, 0x118) == 0x1448D1F8);
    Require(Qword(raw, 0x120) == 0x1448D268);
    Require(Qword(raw, 0x138) == 0x154DE278);
    Require(Qword(raw, 0xF8) == 0x154DE2E0);
  }
  {
    std::array<std::byte, 0x170> first{};
    std::array<std::byte, 0x170> second{};
    std::array<std::uint8_t, 0x170> first_mask{};
    std::array<std::uint8_t, 0x170> second_mask{};
    const RootScopeInitializer889F60Source12004 source{0x20000000, kSha, true};
    Require(ProjectOwnedRootScopeInitializer889F6012004(source, first, first_mask).available);
    second = first; // copied pointer bytes alone do not rebase owned storage.
    Require(ProjectOwnedRootScopeInitializer889F6012004(source, second, second_mask).available);
    Require(Qword(first, 0x18) != Qword(second, 0x18));
    Require(Qword(second, 0x18) == reinterpret_cast<std::uintptr_t>(second.data()) + 0x38);
    Require(Qword(first, 0x30) == Qword(second, 0x30));
  }
  {
    std::array<std::byte, 0x170> raw;
    raw.fill(std::byte{0xA5});
    std::array<std::uint8_t, 0x170> mask;
    mask.fill(1);
    auto result = ProjectOwnedRootScopeInitializer889F6012004(
        {0x10000000, "wrong-build", true}, raw, mask);
    Require(!result.available && result.failure == RootScopeInitializer889F60Failure12004::source_binding);
    for (const auto byte : raw) Require(byte == std::byte{0xA5});
    for (const auto defined : mask) Require(defined == 0);
    result = ProjectOwnedRootScopeInitializer889F6012004(
        {0x10000000, kSha, false}, raw, mask);
    Require(!result.available && result.failure == RootScopeInitializer889F60Failure12004::source_binding);
  }
  {
    std::array<std::byte, 0x170> raw{};
    std::array<std::uint8_t, 0x170> mask{};
    auto result = ProjectOwnedRootScopeInitializer889F6012004(
        {std::numeric_limits<std::uintptr_t>::max(), kSha, true}, raw, mask);
    Require(!result.available && result.failure == RootScopeInitializer889F60Failure12004::module_address);
    result = ProjectOwnedRootScopeInitializer889F6012004(
        {0x10000000, kSha, true}, std::span(raw).first(0x166), std::span(mask).first(0x166));
    Require(!result.available && result.failure == RootScopeInitializer889F60Failure12004::owned_storage_shape);
  }
}
