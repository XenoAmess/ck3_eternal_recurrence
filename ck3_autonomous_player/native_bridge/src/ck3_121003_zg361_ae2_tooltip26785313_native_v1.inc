// External SOURCE candidate only. Native owns assembly/qualification/registration.
// Include in a dedicated finite AE2 consumer. This private read primitive grants
// no selector, event choice, fixture decision or public protocol authority.
#include "xar_bridge/ck3_121003_letter26785313_raw_v1.hpp"
#include <array>
#include <chrono>
#include <cstring>
#include <limits>
#include <string>
#include <string_view>
#include <windows.h>

#ifndef XAR_ZG361_AE2_TOOLTIP_CALL_ADDRESS
#define XAR_ZG361_AE2_TOOLTIP_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif

namespace xar::ck3_121003::build26785313::zg361_ae2_source {
inline constexpr std::string_view kDefinition = "zg361comp.1";
inline constexpr std::int32_t kAuthoredCount = 42;
inline constexpr std::array<std::int32_t,3> kAuthoredIndices{15,16,17};
inline constexpr std::array<std::string_view,3> kOptionKeys{
 "zg361comp.1.ae2.r1", "zg361comp.1.ae2.r2", "zg361comp.1.ae2.r3"};
enum class Tooltip267V1 : std::uint8_t {pay_now,acknowledge_backpay,reject_backpay};

[[maybe_unused]]static bool Deadline(std::uint64_t wall,std::uint64_t mono)noexcept {
 const auto now=std::chrono::duration_cast<std::chrono::milliseconds>(
  std::chrono::system_clock::now().time_since_epoch()).count();
 return wall&&mono&&now>0&&static_cast<std::uint64_t>(now)<wall&&GetTickCount64()<mono;
}
[[maybe_unused]]static bool Copy(std::uintptr_t at,void*out,std::size_t size)noexcept {
 if(!at||!out||!size||size-1>(std::numeric_limits<std::uintptr_t>::max)()-at)return false;
 __try{std::memcpy(out,reinterpret_cast<const void*>(at),size);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<class T>static bool At(std::uintptr_t at,std::size_t offset,T&value)noexcept {
 return at&&offset<=(std::numeric_limits<std::uintptr_t>::max)()-at&&Copy(at+offset,&value,sizeof(value));
}
[[maybe_unused]]static bool Utf8(std::string_view text)noexcept {
 if(text.size()>16384)return false;
 for(std::size_t i=0;i<text.size();){
  const auto c=static_cast<unsigned char>(text[i++]);std::uint32_t value=0;unsigned count=0;
  if(c<0x80)value=c;else if(c>=0xC2&&c<=0xDF){value=c&31;count=1;}
  else if(c>=0xE0&&c<=0xEF){value=c&15;count=2;}
  else if(c>=0xF0&&c<=0xF4){value=c&7;count=3;}else return false;
  if(i+count>text.size())return false;
  for(unsigned n=0;n<count;++n){const auto v=static_cast<unsigned char>(text[i++]);
   if((v&0xC0)!=0x80)return false;value=(value<<6)|(v&63);}
  if((count==1&&value<0x80)||(count==2&&value<0x800)||(count==3&&value<0x10000)||
     value>0x10FFFF||(value>=0xD800&&value<=0xDFFF))return false;
 }
 return true;
}

// Input must be the exact complete, twice-sampled LetterRaw just reacquired by
// the existing owner/GUI census. Its runtime pointers never enter a public wire.
// Parent must join controlled AE2 domain2/stage2/subject/cycle/case, admitted
// product bytes, actual human and same paused Core before/after all three reads.
// This check adds fixed definition/authored mapping and actual option backrefs;
// it is not a substitute for those owner/phase checks.
[[maybe_unused]]static bool FixedMaterial(const ck3_1210::CoreSnapshotPrefix&core,
 const LetterRaw267V1&raw)noexcept {
 const auto&s=raw.source;
 if(!raw.cleanup_known||!raw.window||!raw.data||!raw.runtime_event||!raw.definition||
    !core.clock.paused||!core.map_ready||!core.has_played_character||!core.played_character_alive||
    core.played_character_id==-1||!s.letter_found||!s.named_root_bound||!s.window_visible||
    !s.window_enabled||!s.instance_id||*s.instance_id<=0||
    s.recipient_character_id!=core.played_character_id||s.definition_key!=kDefinition||
    raw.authored_option_count!=kAuthoredCount||raw.authored_option_pointers.size()!=42||
    raw.option_pointers.size()!=3||s.options.size()!=3)return false;
 std::array<bool,3>seen{};
 for(std::size_t n=0;n<s.options.size();++n){
  const auto authored=s.options[n].authored_option_index;std::size_t slot=3;
  for(std::size_t k=0;k<3;++k)if(authored==kAuthoredIndices[k])slot=k;
  if(slot==3||seen[slot]||!raw.option_pointers[n])return false;seen[slot]=true;
  std::uintptr_t owner=0;std::int32_t actual=-1;
  if(!At(raw.option_pointers[n],0x160,owner)||owner!=raw.data||
     !At(raw.option_pointers[n],0x1B0,actual)||actual!=authored||
     !raw.authored_option_pointers[static_cast<std::size_t>(authored)])return false;
 }
 return seen[0]&&seen[1]&&seen[2];
}

// Official GetTooltip producer: const EventOption* RCX, owned CString32* RDX,
// RAX==RDX; registration363420 -> typed1B559E0 ->1B6C090, then897460.
// The existing exact letter pin set already contains the full2432B producer.
// Read-side richtext/control/embedded NUL are preserved by explicit length.
// No OnEnter/OnClick/Select, IsValid, resource write or forecast string executes.
[[maybe_unused]]static bool ReadFixedTooltip267V1(std::uintptr_t image,
 const ck3_1210::CoreSnapshotPrefix&core,const LetterRaw267V1&raw,Tooltip267V1 target,
 std::uint64_t wall,std::uint64_t mono,std::string&text,bool&cleanup_known,bool&entered)noexcept {
 text.clear();cleanup_known=true;entered=false;
 const auto slot=static_cast<std::size_t>(target);
 if(slot>=3||!Deadline(wall,mono)||
    image!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||
    !VerifyLetterImage267V1(image)||!FixedMaterial(core,raw))return false;
 std::uintptr_t option=0;
 for(std::size_t n=0;n<raw.source.options.size();++n)
  if(raw.source.options[n].authored_option_index==kAuthoredIndices[slot])option=raw.option_pointers[n];
 if(!option)return false;
 alignas(std::uintptr_t)std::array<std::byte,32>value{};
 const std::uint64_t initial_capacity=15;std::memcpy(value.data()+24,&initial_capacity,8);
 bool returned=false,valid=false,destroyed=false;entered=true;cleanup_known=false;
 __try {
  using Getter=void*(__fastcall*)(const void*,void*);
  returned=reinterpret_cast<Getter>(XAR_ZG361_AE2_TOOLTIP_CALL_ADDRESS(image,0x1B6C090))(
    reinterpret_cast<const void*>(option),value.data())==value.data();
  if(returned&&Deadline(wall,mono)){
   std::uint64_t length=0,capacity=0;std::uintptr_t chars=reinterpret_cast<std::uintptr_t>(value.data());
   std::memcpy(&length,value.data()+16,8);std::memcpy(&capacity,value.data()+24,8);
   if(length<=16384&&capacity>=length&&(capacity==15||capacity>=16)&&capacity<=0x10000000){
    if(capacity>=16)std::memcpy(&chars,value.data(),8);
    std::array<char,16385>bytes{};
    if(Copy(chars,bytes.data(),static_cast<std::size_t>(length)+1)&&!bytes[static_cast<std::size_t>(length)]){
     text.assign(bytes.data(),static_cast<std::size_t>(length));valid=Utf8(text);
    }
   }
  }
 }__except(EXCEPTION_EXECUTE_HANDLER){returned=false;}
 // Even partial/expired owned output receives best-effort official destruction.
 // Partial getter or destructor uncertainty remains UNKNOWN to the parent.
 __try {
  using Dtor=void(__fastcall*)(void*);
  reinterpret_cast<Dtor>(XAR_ZG361_AE2_TOOLTIP_CALL_ADDRESS(image,0x897460))(value.data());destroyed=true;
 }__except(EXCEPTION_EXECUTE_HANDLER){destroyed=false;}
 cleanup_known=returned&&destroyed;
 if(!cleanup_known||!valid||!Deadline(wall,mono)||!FixedMaterial(core,raw)){
  text.clear();return false;
 }
 return true;
}
} // namespace xar::ck3_121003::build26785313::zg361_ae2_source
