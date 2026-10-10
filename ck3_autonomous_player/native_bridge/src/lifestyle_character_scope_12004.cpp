#include "xar_bridge/lifestyle_character_scope_12004.hpp"
#include "xar_bridge/m4_factor_actor_inner_init_12004.hpp"
#include <cstring>
#include <limits>

namespace xar::ck3_12004::lifestyle {
namespace {
constexpr std::string_view kActualSourcePin =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
constexpr std::size_t kActualChildOffset = 0x18;

template <class T>
void Store(LifestyleCharacterScope12004 &out, std::size_t offset, T value) noexcept {
  std::memcpy(out.raw.data()+offset,&value,sizeof(value));
  for (std::size_t i=offset; i<offset+sizeof(value); ++i) out.defined_bytes[i]=1;
}
bool ReadFreshFullId(const LifestylePerkReadonlyAccess12004 &access,
                    std::uintptr_t character, std::uint32_t &out) noexcept {
  if (!access.read_memory || !character ||
      character > std::numeric_limits<std::uintptr_t>::max()-0x18) return false;
  try {
    return access.read_memory(access.read_context,character+0x18,&out,sizeof(out));
  } catch (...) { return false; }
}
bool ProjectChild(const LifestylePerkReadonlyAccess12004 &access,
                  LifestyleCharacterScope12004 &out) noexcept {
  // Reuse only actual8895D0 source. The08 parent actor construction/layout is
  // not called or copied. Frame0 is unused software audit metadata, not native.
  M4FactorActorInnerInit12004 inner{};
  if (!ProjectM4FactorActorInnerInit12004(access.module_base,kActualSourcePin,0,inner) ||
      !inner.complete_source) return false;
  for (std::size_t i=0; i<inner.defined_bytes.size(); ++i) {
    if (!inner.defined_bytes[i]) continue;
    if (kActualChildOffset+i >= out.raw.size()) return false;
    out.raw[kActualChildOffset+i]=inner.raw[i];
    out.defined_bytes[kActualChildOffset+i]=1;
  }
  if (inner.self_pointer_patch_count > inner.self_pointer_patches.size()) return false;
  for (std::size_t i=0; i<inner.self_pointer_patch_count; ++i) {
    const auto patch=inner.self_pointer_patches[i];
    const auto offset=kActualChildOffset+patch.offset;
    const auto target=kActualChildOffset+patch.target;
    if (offset > out.raw.size()-sizeof(std::uint64_t) || target >= out.raw.size()) return false;
    Store(out,offset,static_cast<std::uint64_t>(
        reinterpret_cast<std::uintptr_t>(out.raw.data()+target)));
  }
  return true;
}
} // namespace

bool ProjectLifestyleCharacterScope9D78D012004(
    const LifestylePerkReadonlyAccess12004 &access,
    std::uintptr_t resolved_character, LifestyleCharacterScope12004 &out) noexcept {
  out.resolved_character=resolved_character;
  out.fresh_full_character_id.reset();
  out.source_projection_ready=false;
  out.unavailable_reason={};
  out.raw.fill(std::byte{});
  out.defined_bytes.fill(0);
  const auto fail=[&out](std::string_view reason) noexcept {
    out.unavailable_reason=reason;
    return false;
  };
  if (!access.module_base || access.module_base >
      std::numeric_limits<std::uintptr_t>::max()-0x54DE2E0)
    return fail("lifestyle_character_scope_module_unavailable");
  std::uint32_t id=0;
  if (!ReadFreshFullId(access,resolved_character,id))
    return fail("lifestyle_character_scope_fresh_id_unavailable");
  out.fresh_full_character_id=id;
  // Actual9D78D0 clears DWORD0, then writes WORD kind4. A DWORD+18 read into
  // EAX zero-extends all generation bits into the original QWORD+8 payload.
  Store(out,0x00,std::uint32_t{0});
  Store(out,0x00,std::uint16_t{4});
  Store(out,0x08,static_cast<std::uint64_t>(id));
  Store(out,0x10,std::uint32_t{0xFFFFFFFF});
  if (!ProjectChild(access,out)) return fail("lifestyle_character_scope_child_source_unavailable");
  Store(out,0x100,std::uint64_t{0});
  Store(out,0x108,std::uint64_t{0});
  Store(out,0x110,static_cast<std::uint64_t>(access.module_base+0x54DE270));
  Store(out,0x118,static_cast<std::uint64_t>(access.module_base+0x448D1F8));
  Store(out,0x120,static_cast<std::uint64_t>(access.module_base+0x448D268));
  Store(out,0x128,std::uint64_t{0});
  Store(out,0x130,std::uint64_t{0});
  Store(out,0x138,static_cast<std::uint64_t>(access.module_base+0x54DE278));
  Store(out,0x140,std::uint32_t{0});
  Store(out,0x148,std::uint64_t{0});
  Store(out,0x150,std::uint64_t{0});
  Store(out,0x158,static_cast<std::uint64_t>(access.module_base+0x54DE270));
  Store(out,0x160,std::uint32_t{0xFFFFFFFF});
  Store(out,0x164,std::uint16_t{0});
  Store(out,0x166,std::uint8_t{0});
  out.source_projection_ready=true;
  return true;
}

bool CopyDefinedLifestyleCharacterScopeBytes12004(
    const LifestyleCharacterScope12004 &scope, std::size_t offset,
    void *output, std::size_t size) noexcept {
  if (!scope.source_projection_ready || offset > scope.raw.size() ||
      size > scope.raw.size()-offset || (size && !output)) return false;
  for (std::size_t i=offset; i<offset+size; ++i)
    if (!scope.defined_bytes[i]) return false;
  if (size) std::memcpy(output,scope.raw.data()+offset,size);
  return true;
}
} // namespace xar::ck3_12004::lifestyle
