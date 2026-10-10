#include "xar_bridge/lifestyle_character_scope_12004.hpp"
#include <cstring>
#include <type_traits>

namespace xar::ck3_12004::lifestyle {
namespace {
struct Input {
  std::uintptr_t character=0x12345000;
  std::uint32_t full_id=0xFABCDEF1;
  unsigned reads=0;
  bool unavailable=false;
};
bool Read(void *context,std::uintptr_t address,void *output,std::size_t size) {
  auto &input=*static_cast<Input *>(context);
  ++input.reads;
  if (input.unavailable || address != input.character+0x18 || size != sizeof(input.full_id))
    return false;
  std::memcpy(output,&input.full_id,size);
  return true;
}
template <class T>
bool Value(const LifestyleCharacterScope12004 &out,std::size_t offset,T expected) noexcept {
  T actual{};
  return CopyDefinedLifestyleCharacterScopeBytes12004(out,offset,&actual,sizeof(actual)) &&
      actual==expected;
}
}

// Four new constructor-consumer cases in the unique M5 compound; no main and
// no reuse of18b sample/RBX or48's previous qualification fragment.
int RunLifestyleCharacterScope9D78D0NewCases12004() noexcept {
  static_assert(!std::is_copy_constructible_v<LifestyleCharacterScope12004>);
  static_assert(!std::is_move_constructible_v<LifestyleCharacterScope12004>);
  Input input{};
  LifestylePerkReadonlyAccess12004 access{};
  access.module_base=0x140000000;
  access.read_context=&input;
  access.read_memory=&Read;
  LifestyleCharacterScope12004 out{};
  if (!ProjectLifestyleCharacterScope9D78D012004(access,input.character,out) ||
      input.reads!=1 || !out.source_projection_ready ||
      !Value(out,0,std::uint16_t{4}) ||
      !Value(out,8,std::uint64_t{0xFABCDEF1}) ||
      !Value(out,0x10,std::uint32_t{0xFFFFFFFF})) return 0;
  // Final owned self pointers, not addresses inside the temporary child DTO.
  const auto address=reinterpret_cast<std::uintptr_t>(out.raw.data());
  if (!Value(out,0x18,static_cast<std::uint64_t>(address+0x38)) ||
      !Value(out,0x28,static_cast<std::uint64_t>(address+0x30)) ||
      !Value(out,0x20,std::uint32_t{8}) || !Value(out,0x24,std::uint32_t{0}) ||
      !Value(out,0x118,static_cast<std::uint64_t>(access.module_base+0x448D1F8))) return 0;
  // Reprojection reads the current full generation ID and retains self lifetime.
  input.full_id=0x81234567;
  if (!ProjectLifestyleCharacterScope9D78D012004(access,input.character,out) ||
      !Value(out,8,std::uint64_t{0x81234567}) ||
      !Value(out,0x18,static_cast<std::uint64_t>(address+0x38))) return 0;
  std::uint64_t scratch=0xCCCCCCCCCCCCCCCC;
  unsigned defined=0;
  for (const auto byte:out.defined_bytes) defined+=byte!=0;
  const auto before_query=input.reads;
  if (defined!=155 || CopyDefinedLifestyleCharacterScopeBytes12004(out,4,&scratch,4) ||
      CopyDefinedLifestyleCharacterScopeBytes12004(out,0x38,&scratch,8) ||
      CopyDefinedLifestyleCharacterScopeBytes12004(out,0x167,&scratch,1) ||
      !Value(out,0x160,std::uint32_t{0xFFFFFFFF}) ||
      input.reads!=before_query || scratch!=0xCCCCCCCCCCCCCCCC) return 0;
  // A failed guarded source read remains unavailable; it never yields false
  // selected-perk truth or a projected zero-ID context.
  input.unavailable=true;
  if (ProjectLifestyleCharacterScope9D78D012004(access,input.character,out) ||
      out.source_projection_ready || out.fresh_full_character_id ||
      CopyDefinedLifestyleCharacterScopeBytes12004(out,8,&scratch,8) ||
      out.unavailable_reason.empty()) return 0;
  return 4;
}
} // namespace xar::ck3_12004::lifestyle
