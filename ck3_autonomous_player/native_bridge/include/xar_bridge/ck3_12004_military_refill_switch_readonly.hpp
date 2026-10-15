#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {
// Raw read primitive only. No command, checkbox callback or direct state write.
// The caller must supply a source-resolved *reinforcement owner*, not assume the
// player character owns every Regi referenced by the selected Army's DATA.
using MilitaryRefillSwitchRead12004=bool(*)(void*,std::uintptr_t,void*,std::size_t) noexcept;
struct MilitaryRefillSwitch12004 {
  std::optional<std::int32_t> owner_full_id;
  std::optional<std::uint32_t> character_magic;
  std::optional<std::uintptr_t> military_component;
  std::optional<std::uint8_t> raw_byte_4a9;
  std::optional<bool> enabled;
  bool identity_exact=false;
  bool read_complete=false;
};
inline MilitaryRefillSwitch12004 ReadMilitaryRefillSwitch12004(
    MilitaryRefillSwitchRead12004 read,void *context,std::uintptr_t character,
    std::int32_t expected_full_id,std::string_view actual_exe_sha256) noexcept {
  MilitaryRefillSwitch12004 out;
  if(actual_exe_sha256!="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")return out;
  if(!read||!character||character>UINTPTR_MAX-0x1C8)return out;
  std::int32_t id=0;std::uint32_t magic=0;std::uintptr_t component=0;
  if(!read(context,character+0x18,&id,sizeof id)||
      !read(context,character+0x1C,&magic,sizeof magic))return out;
  out.owner_full_id=id;out.character_magic=magic;
  // Existing Character contract: 'Char' magic; generation equality is full DWORD.
  if(id!=expected_full_id||id==-1||magic!=0x43686172)return out;
  out.identity_exact=true;
  if(!read(context,character+0x1C0,&component,sizeof component))return out;
  out.military_component=component;
  if(!component||component>UINTPTR_MAX-0x4AA)return out;
  std::uint8_t value=0;
  if(!read(context,component+0x4A9,&value,sizeof value))return out;
  // Re-read identity/component; a changed receiver cannot qualify a switch.
  std::int32_t after_id=0;std::uint32_t after_magic=0;std::uintptr_t after_component=0;
  if(!read(context,character+0x18,&after_id,sizeof after_id)||
      !read(context,character+0x1C,&after_magic,sizeof after_magic)||
      !read(context,character+0x1C0,&after_component,sizeof after_component)||
      after_id!=id||after_magic!=magic||after_component!=component)return out;
  out.raw_byte_4a9=value;out.enabled=value!=0;out.read_complete=true;return out;
}
}
