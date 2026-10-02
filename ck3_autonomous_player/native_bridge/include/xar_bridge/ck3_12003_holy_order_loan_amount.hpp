#pragma once

// CK3 1.20.0.3 build 25652598: borrow a loaded fixed-point script value.
// EXE SHA-256: 94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6.
// Native scalar route A13180 -> A07970 / A07830, not scripted modifiers.
// Game main owner only; database entries remain owned by the game.
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string_view>

namespace xar::holy_order_amount_recipe {
template <typename T> inline T Read(const void* p, std::size_t off) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte*>(p) + off, sizeof(value));
  return value;
}

inline const void* FindFixedPointScriptValue(std::uintptr_t base,
                                            std::string_view key) noexcept {
  using DatabaseGetter = void* (__fastcall*)();
  using Hash = std::uint32_t (__fastcall*)(const void*, const char*, std::uint32_t);
  using Lookup = const void* (__fastcall*)(void*, std::uint32_t);
  auto* database = reinterpret_cast<DatabaseGetter>(base + 0xA07970)();
  if (!database) return nullptr;
  auto hash = reinterpret_cast<Hash>(base + 0x3F7E240)(
      database, key.data(), static_cast<std::uint32_t>(key.size()));
  auto* entry = reinterpret_cast<Lookup>(base + 0xA07830)(database, hash);
  auto* fallback = Read<const void*>(reinterpret_cast<const void*>(base + 0x5D1DD48), 0);
  return entry && entry != fallback && Read<std::uint32_t>(entry, 0x38) == 0x4744624FU
             ? entry : nullptr;
}

// Context is the native fixed-point cost caller's 0x28-byte input.
struct FixedPointEvaluationContext {
  const void* root;
  const void* previous;
  const void* current;
  void* scratch;
  std::uint8_t mode;
  std::byte padding[7];
};
static_assert(sizeof(FixedPointEvaluationContext) == 0x28);

inline void ReleaseEvaluationVector(void* scratch, std::size_t vector_offset,
                                    bool clear_values, std::uintptr_t base) noexcept {
  auto* data = Read<void*>(scratch, vector_offset);
  if (!data) return;
  auto* vector = static_cast<std::byte*>(scratch) + vector_offset;
  if (clear_values) {
    using ClearValues = void (__fastcall*)(void*);
    reinterpret_cast<ClearValues>(base + 0x9D7340)(vector);
  } else {
    const std::int32_t zero = 0;
    std::memcpy(vector + 0x0C, &zero, sizeof(zero));
  }
  auto* allocator = Read<void*>(vector, 0x10);
  auto* vtable = Read<const void*>(allocator, 0);
  using Release = void (__fastcall*)(void*, void*, std::uint64_t);
  auto release = Read<Release>(vtable, 0x10);
  release(allocator, data, 8);
}

inline bool EvaluateFixedPointScriptValue(std::uintptr_t base, const void* entry,
                                          const void* root_scope,
                                          std::int64_t& raw) noexcept {
  if (!entry || !root_scope) return false;
  // Native A13180 gives the compiled expression precedence over the constant.
  if (!Read<std::uint8_t>(entry, 0x7C)) {
    if (!Read<std::uint8_t>(entry, 0x7B)) return false;
    raw = Read<std::int64_t>(entry, 0x68);
    return true;
  }
  alignas(16) std::array<std::byte, 0x3D8> scratch{};
  using Construct = void (__fastcall*)(void*);
  reinterpret_cast<Construct>(base + 0x3736060)(scratch.data());
  reinterpret_cast<Construct>(base + 0x3735FB0)(scratch.data() + 0x128);
  std::memcpy(scratch.data() + 0x3D0, &root_scope, sizeof(root_scope));
  FixedPointEvaluationContext context{
      root_scope, root_scope, root_scope, scratch.data(),
      Read<std::uint8_t>(reinterpret_cast<const void*>(base + 0x5D1DADC), 0), {}};
  using EvaluateEntry = std::int64_t* (__fastcall*)(
      const void*, std::int64_t*, const FixedPointEvaluationContext*, void*, const void*);
  auto* result = reinterpret_cast<EvaluateEntry>(base + 0x37542F0)(
      entry, &raw, &context, nullptr, static_cast<const std::byte*>(entry) + 0x40);
  // Native 37616A0 cleanup order; only temporary vectors are owned locally.
  ReleaseEvaluationVector(scratch.data(), 0x128, true, base);
  ReleaseEvaluationVector(scratch.data(), 0, false, base);
  return result == &raw;
}

} // namespace xar::holy_order_amount_recipe
