#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::size_t kM4FactorActorContextSize12004 = 0x168;
inline constexpr std::size_t kM4FactorActorInnerOffset12004 = 0x18;
inline constexpr std::size_t kM4FactorActorInnerCapacity12004 = 0x150;
inline constexpr std::uint32_t kM4FactorActorTag12004 = 4;
inline constexpr std::uintptr_t kM4FactorActorContextConstructorRva12004 = 0xB17C70;

using M4FactorActorReadMemory12004 =
    bool (*)(void *, std::uintptr_t, void *, std::size_t) noexcept;

struct M4FactorActorContextAccess12004 {
  void *context = nullptr;
  M4FactorActorReadMemory12004 read_memory = nullptr;
};

struct M4FactorActorContextRequest12004 {
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  // Saved factor entry RDX, not a replacement played-character pointer.
  std::uintptr_t context_receiver = 0;
  std::uint64_t frame_key = 0;
};

struct M4FactorActorSelfPointerPatch12004 {
  // Relative to child receiver = final owned outer storage+18.
  std::uint16_t offset = 0;
  std::uint16_t target = 0;
};

// Child48 supplies only actual ctor/virtual-slot source writes. Bytes not
// written by that source stay undefined. Self pointers are source operations,
// rebased at the final owned parent address; no native initializer is invoked.
struct M4FactorActorInnerInit12004 {
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  std::uint64_t frame_key = 0;
  bool complete_source = false;
  std::array<std::byte, kM4FactorActorInnerCapacity12004> raw{};
  std::array<std::uint8_t, kM4FactorActorInnerCapacity12004> defined_bytes{};
  std::array<M4FactorActorSelfPointerPatch12004, 8> self_pointer_patches{};
  std::size_t self_pointer_patch_count = 0;
};

// Exact source-equivalent storage requires16-byte alignment; MSVC reports
// the resulting intentional padding under/W4. Keep ABI/layout unchanged.
#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4324)
#endif
struct M4FactorActorContext12004 {
  std::uintptr_t context_receiver = 0;
  std::uint64_t frame_key = 0;
  std::uint32_t actor_full_id = 0xFFFFFFFFU;
  std::uint32_t native_scope_tag = 0;
  bool actor_identity_qualified = false;
  bool complete_source = false;
  // Stable software storage equivalence, never an observed native stack scope.
  alignas(16) std::array<std::byte, kM4FactorActorContextSize12004> raw{};
  std::array<std::uint8_t, kM4FactorActorContextSize12004> defined_bytes{};

  M4FactorActorContext12004() = default;
  M4FactorActorContext12004(const M4FactorActorContext12004 &) = delete;
  M4FactorActorContext12004 &operator=(const M4FactorActorContext12004 &) = delete;
  M4FactorActorContext12004(M4FactorActorContext12004 &&) = delete;
  M4FactorActorContext12004 &operator=(M4FactorActorContext12004 &&) = delete;
};
#if defined(_MSC_VER)
#pragma warning(pop)
#endif

// Exact4 read-only Character storage identity round-trip for the saved factor
// receiver, then source-only stores into stable owned context. Native +18u32 is
// zero-extended to the root scope+8qword without masking its generation bits.
// Return value admits the actual actor/root prefix only. complete_source stays
// false when the child is missing; a consumer requiring inner state must check
// it separately. Constant consumers may use their proved unused-inner branch.
// No native constructor, allocator, evaluator, action or listener invocation.
bool ReadM4FactorActorContext12004(
    const M4FactorActorContextAccess12004 &access,
    const M4FactorActorContextRequest12004 &request,
    const M4FactorActorInnerInit12004 &inner,
    M4FactorActorContext12004 &output) noexcept;

// Production entry: obtains the source-closed inner projection from child48
// directly. The explicit-inner overload is the focused join/partial-read API.
bool ReadM4FactorActorContext12004(
    const M4FactorActorContextAccess12004 &access,
    const M4FactorActorContextRequest12004 &request,
    M4FactorActorContext12004 &output) noexcept;

} // namespace xar::ck3_12004
