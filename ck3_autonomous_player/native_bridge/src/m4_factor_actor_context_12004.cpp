#include "xar_bridge/m4_factor_actor_context_12004.hpp"
#include "xar_bridge/m4_factor_actor_inner_init_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstring>
#include <limits>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t kCharacterFallbackSlot = 0x5C67570;
constexpr std::uintptr_t kScopeTailVtable0 = 0x448D1F8;
constexpr std::uintptr_t kScopeTailVtable1 = 0x448D268;
constexpr std::uintptr_t kScopeAllocator = 0x54DE270;
constexpr std::uintptr_t kScopeTailBacking = 0x54DE278;

bool Add(std::uintptr_t base, std::size_t offset, std::uintptr_t &out) noexcept {
  if (!base || offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  out = base + offset;
  return true;
}

template <typename T>
bool Read(const M4FactorActorContextAccess12004 &access,
          std::uintptr_t base, std::size_t offset, T &out) noexcept {
  std::uintptr_t address = 0;
  return access.read_memory && Add(base, offset, address) &&
      access.read_memory(access.context, address, &out, sizeof(out));
}

template <typename T>
void Store(M4FactorActorContext12004 &out, std::size_t offset, T value) noexcept {
  std::memcpy(out.raw.data() + offset, &value, sizeof(value));
  for (std::size_t i = 0; i < sizeof(value); ++i) out.defined_bytes[offset+i] = 1;
}

void Reset(M4FactorActorContext12004 &out) noexcept {
  out.context_receiver = 0;
  out.frame_key = 0;
  out.actor_full_id = 0xFFFFFFFFU;
  out.native_scope_tag = 0;
  out.actor_identity_qualified = false;
  out.complete_source = false;
  out.raw.fill(std::byte{});
  out.defined_bytes.fill(0);
}

// Existing exact4 Core storage/identity layout, reused as a read algorithm.
// The generation-bearing fullID must resolve back to the actual factor receiver.
bool Actor(const M4FactorActorContextAccess12004 &access,
           const M4FactorActorContextRequest12004 &request,
           std::uint32_t &raw_id) noexcept {
  std::uintptr_t storage = 0, fallback = 0, slots = 0, object = 0;
  std::int32_t capacity = 0;
  std::uint32_t observed_id = 0xFFFFFFFFU;
  if (!Read(access, request.context_receiver, kCharacterFullIdOffset, raw_id) ||
      raw_id == 0xFFFFFFFFU ||
      !Read(access, request.module_base, kCharacterStorageSlotRva, storage) ||
      !Read(access, request.module_base, kCharacterFallbackSlot, fallback) ||
      !Read(access, storage, kCharacterStorageSlotsOffset, slots) ||
      !Read(access, storage, kCharacterStorageCapacityOffset, capacity) || capacity <= 0)
    return false;
  const auto index = raw_id & 0x00FFFFFFU;
  return index < static_cast<std::uint32_t>(capacity) &&
      Read(access, slots, static_cast<std::size_t>(index) * kCharacterStorageSlotStride +
           kCharacterStorageObjectOffset, object) &&
      object == request.context_receiver && object != fallback &&
      Read(access, object, kCharacterFullIdOffset, observed_id) && observed_id == raw_id;
}

bool CopyInner(const M4FactorActorContextRequest12004 &request,
               const M4FactorActorInnerInit12004 &inner,
               M4FactorActorContext12004 &out) noexcept {
  if (!inner.complete_source || inner.module_base != request.module_base ||
      inner.executable_sha256 != kExecutableSha256 || inner.frame_key != request.frame_key ||
      inner.self_pointer_patch_count > inner.self_pointer_patches.size()) return false;
  for (std::size_t i = 0; i < inner.raw.size(); ++i) {
    if (inner.defined_bytes[i] > 1) return false;
    if (inner.defined_bytes[i]) {
      out.raw[kM4FactorActorInnerOffset12004+i] = inner.raw[i];
      out.defined_bytes[kM4FactorActorInnerOffset12004+i] = 1;
    }
  }
  const auto child = reinterpret_cast<std::uintptr_t>(out.raw.data()) +
      kM4FactorActorInnerOffset12004;
  for (std::size_t i = 0; i < inner.self_pointer_patch_count; ++i) {
    const auto patch = inner.self_pointer_patches[i];
    if (patch.offset > inner.raw.size() - sizeof(std::uintptr_t) ||
        patch.target > inner.raw.size()) return false;
    // The operation is rebound into final stable software-owned storage.
    Store(out, kM4FactorActorInnerOffset12004 + patch.offset,
          child + patch.target);
  }
  return true;
}

bool OuterStores(const M4FactorActorContextRequest12004 &request,
                 M4FactorActorContext12004 &out) noexcept {
  std::uintptr_t tail0 = 0, tail1 = 0, allocator = 0, backing = 0;
  if (!Add(request.module_base, kScopeTailVtable0, tail0) ||
      !Add(request.module_base, kScopeTailVtable1, tail1) ||
      !Add(request.module_base, kScopeAllocator, allocator) ||
      !Add(request.module_base, kScopeTailBacking, backing)) return false;
  // Source zeros DWORD0 then writes WORD4: upper WORD stays zero.
  Store(out, 0, std::uint32_t{kM4FactorActorTag12004});
  Store(out, 8, static_cast<std::uint64_t>(out.actor_full_id));
  Store(out, 0x10, std::uint32_t{0xFFFFFFFFU});
  Store(out, 0x100, std::uint64_t{0});
  Store(out, 0x108, std::uint64_t{0});
  Store(out, 0x110, allocator);
  Store(out, 0x118, tail0);
  Store(out, 0x120, tail1);
  Store(out, 0x128, std::uint64_t{0});
  Store(out, 0x130, std::uint64_t{0});
  Store(out, 0x138, backing);
  Store(out, 0x140, std::uint32_t{0});
  Store(out, 0x148, std::uint64_t{0});
  Store(out, 0x150, std::uint64_t{0});
  Store(out, 0x158, allocator);
  Store(out, 0x160, std::uint32_t{0xFFFFFFFFU});
  Store(out, 0x164, std::uint16_t{0});
  Store(out, 0x166, std::uint8_t{0});
  out.native_scope_tag = kM4FactorActorTag12004;
  return true;
}
} // namespace

bool ReadM4FactorActorContext12004(
    const M4FactorActorContextAccess12004 &access,
    const M4FactorActorContextRequest12004 &request,
    const M4FactorActorInnerInit12004 &inner,
    M4FactorActorContext12004 &out) noexcept {
  Reset(out);
  if (!request.module_base || request.executable_sha256 != kExecutableSha256 ||
      !Actor(access, request, out.actor_full_id)) return false;
  out.context_receiver = request.context_receiver;
  out.frame_key = request.frame_key;
  out.actor_identity_qualified = true;
  const bool inner_ready = CopyInner(request, inner, out);
  // Native outer writes after its child have priority over overlapping stores.
  if (!OuterStores(request, out)) return false;
  out.complete_source = inner_ready;
  return true;
}

bool ReadM4FactorActorContext12004(
    const M4FactorActorContextAccess12004 &access,
    const M4FactorActorContextRequest12004 &request,
    M4FactorActorContext12004 &out) noexcept {
  M4FactorActorInnerInit12004 inner;
  ProjectM4FactorActorInnerInit12004(request.module_base, request.executable_sha256,
                                   request.frame_key, inner);
  return ReadM4FactorActorContext12004(access, request, inner, out);
}
} // namespace xar::ck3_12004
