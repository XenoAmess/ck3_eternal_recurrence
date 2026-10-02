#pragma once

// External research recipe: CK3 1.20.0.3 build 25652598.
// EXE SHA-256: 94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6.
// Game main owner only. Compiles numeric math and executes no scripted effect.
// ABI-PROOF.json records the actual native load/eval/destructor callers.
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace xar::holy_order_amount_recipe {
template <typename T> inline T Read(const void* p, std::size_t off) noexcept {
  T v{};
  std::memcpy(&v, static_cast<const std::byte*>(p) + off, sizeof(v));
  return v;
}
template <typename T> inline void Write(void* p, std::size_t off, T v) noexcept {
  std::memcpy(static_cast<std::byte*>(p) + off, &v, sizeof(v));
}
struct NamedContext {
  void* node;
  std::uint16_t root_kind;
  std::byte padding[6];
};
static_assert(sizeof(NamedContext) == 0x10);

class NamedMath {
 public:
  bool Build(std::uintptr_t base, const void* definition) noexcept {
    if (ready_) return base_ == base && definition_ == definition;
    base_ = base;
    definition_ = definition;
    node_.fill(std::byte{});
    // This native constructor is inlined in 0x3760DBC..0x3760E72.
    Write(node_.data(), 0x00, base + 0x492E1B0);
    Write(node_.data(), 0x20, std::uint64_t{15}); // empty SSO at +0x08
    Write(node_.data(), 0x3C, std::uint8_t{1});
    Write(node_.data(), 0x48, definition);
    Write(node_.data(), 0x68, std::uint64_t{15}); // empty SSO at +0x50
    Write(node_.data(), 0x80, base + 0x54E2BB0); // argument allocator
    Write(node_.data(), 0x98, node_.data() + 0xA0); // child allocator
    Write(node_.data(), 0xA0, base + 0x492E288); // allocator vtable
    Write(node_.data(), 0xC8, base + 0x54E6448); // underlying allocator
    NamedContext context{node_.data(), 4, {}};
    using Compile = void (__fastcall*)(void*, const void*, const NamedContext*);
    reinterpret_cast<Compile>(base + 0x37D36D0)(node_.data(), definition, &context);
    ready_ = Read<void*>(node_.data(), 0x88) != nullptr &&
             Read<std::int32_t>(node_.data(), 0x94) > 0;
    if (!ready_) { Destroy(); return false; }
    math_.fill(std::byte{});
    nodes_[0] = node_.data();
    Write(math_.data(), 0x30, nodes_.data());
    Write(math_.data(), 0x38, std::int32_t{1});
    Write(math_.data(), 0x3C, std::int32_t{1});
    return true;
  }
  bool Evaluate(const void* scope, std::int64_t& raw) noexcept {
    if (!ready_ || !scope) return false;
    using EvaluateMath = std::int64_t* (__fastcall*)(const void*, std::int64_t*, const void*);
    return reinterpret_cast<EvaluateMath>(base_ + 0x37616A0)(math_.data(), &raw, scope) == &raw;
  }
  // Use before bridge/game cleanup; flags=0 retains the local 0xD0 storage.
  void Destroy() noexcept {
    if (!base_) return;
    using DestroyNode = void* (__fastcall*)(void*, std::uint32_t);
    reinterpret_cast<DestroyNode>(base_ + 0x3760C60)(node_.data(), 0);
    base_ = 0;
    ready_ = false;
    definition_ = nullptr;
  }
 private:
  alignas(16) std::array<std::byte, 0xD0> node_{};
  alignas(16) std::array<std::byte, 0x40> math_{};
  std::array<void*, 1> nodes_{};
  std::uintptr_t base_{};
  const void* definition_{};
  bool ready_{};
};

} // namespace xar::holy_order_amount_recipe
