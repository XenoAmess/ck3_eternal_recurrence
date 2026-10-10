#pragma once

#include "xar_bridge/lifestyle_perk_predicate_inputs_12004.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::lifestyle {

inline constexpr std::uintptr_t kLifestyleCharacterScopeConstructorRva12004 = 0x9D78D0;
inline constexpr std::size_t kLifestyleCharacterScopeStorageBytes12004 = 0x170;
inline constexpr std::size_t kLifestyleCharacterScopeDefinedBytes12004 = 155;

struct LifestyleCharacterScope12004 {
  std::uintptr_t resolved_character = 0;
  std::optional<std::uint32_t> fresh_full_character_id;
  bool source_projection_ready = false;
  std::string_view unavailable_reason{};
  // Explicit software padding preserves raw alignment without implicit padding.
  std::array<std::byte,8> raw_alignment_padding{};
  // Source-equivalent software storage; never an observed native stack scope.
  // The source's explicit extent is0x167. Padding/untouched bytes have mask0.
  alignas(16) std::array<std::byte,kLifestyleCharacterScopeStorageBytes12004> raw{};
  std::array<std::uint8_t,kLifestyleCharacterScopeStorageBytes12004> defined_bytes{};

  LifestyleCharacterScope12004() = default;
  LifestyleCharacterScope12004(const LifestyleCharacterScope12004 &) = delete;
  LifestyleCharacterScope12004 &operator=(const LifestyleCharacterScope12004 &) = delete;
  LifestyleCharacterScope12004(LifestyleCharacterScope12004 &&) = delete;
  LifestyleCharacterScope12004 &operator=(LifestyleCharacterScope12004 &&) = delete;
};

// Access16/62 already binds the exact actual4 module and resolved Character.
// The only guarded source read is the ctor's fresh Character+18 DWORD. The
// source-closed48 child projection supplies only8895D0's byte/self-pointer ops.
// This boolean means projection available, not native constructor/truth success.
// No frame/actor tag/source label is invented as a native predicate input.
bool ProjectLifestyleCharacterScope9D78D012004(
    const LifestylePerkReadonlyAccess12004 &access,
    std::uintptr_t resolved_character, LifestyleCharacterScope12004 &output) noexcept;

// Consumers must request source-defined fields through this mask-aware copy.
// Unknown raw holes are unavailable, even if physical owned bytes are zero.
bool CopyDefinedLifestyleCharacterScopeBytes12004(
    const LifestyleCharacterScope12004 &scope, std::size_t offset,
    void *output, std::size_t size) noexcept;

// New18c fragment, invoked once by the sole16/62/10 connected M5 compound.
int RunLifestyleCharacterScope9D78D0NewCases12004() noexcept;

} // namespace xar::ck3_12004::lifestyle
