#include "xar_bridge/ck3_121003_doctrine_knowledge26785313_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_knowledge26785313_pins_v1.hpp"
#include <array>
#include <cstring>
#include <limits>
#include <utility>
#include <windows.h>

namespace xar::ck3_121003::build26785313 { namespace {
[[maybe_unused]] bool Copy(std::uintptr_t from,void *to,std::size_t bytes) noexcept {
  if(!from||!to||!bytes)return false;
  __try {std::memcpy(to,reinterpret_cast<const void*>(from),bytes);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<class T> bool At(std::uintptr_t object,std::size_t offset,T&out) noexcept {
  constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
  return object&&offset<=max-object&&sizeof(T)-1<=max-object-offset&&Copy(object+offset,&out,sizeof(out));
}
struct ActorFacts {
  std::int32_t id=-1;
  std::uint32_t marker=0,faith_id=0;
  std::uintptr_t death=0,knowledge_override=0;
  friend bool operator==(const ActorFacts&,const ActorFacts&)=default;
};
struct MembershipFacts {
  std::uintptr_t list_owner=0,data=0;
  std::int32_t count=0;
  friend bool operator==(const MembershipFacts&,const MembershipFacts&)=default;
};
[[maybe_unused]] bool Facts(std::uintptr_t actor,ActorFacts&out) noexcept {
  return At(actor,0x18,out.id)&&At(actor,0x1C,out.marker)&&At(actor,0xB4,out.faith_id)&&
      At(actor,0x1C8,out.knowledge_override)&&At(actor,0x1D0,out.death)&&
      out.id!=-1&&out.marker==0x43686172U&&out.death==0;
}
[[maybe_unused]] bool Membership(std::uintptr_t image,const ActorFacts&actor,MembershipFacts&out) noexcept {
  if(actor.knowledge_override) {
    out.list_owner=actor.knowledge_override;
    if(!At(out.list_owner,0x128,out.data)||!At(out.list_owner,0x134,out.count))return false;
  } else {
    std::uintptr_t database=0,entries=0;std::uint32_t capacity=0,id=0;
    const auto index=actor.faith_id&0xFFFFFFU;
    if(!At(image,0x6A672C0,database)||!At(database,0x2C,capacity)||index>=capacity||
        !At(database,0x20,entries)||!At(entries,static_cast<std::size_t>(index)*16+8,out.list_owner)||
        !out.list_owner||!At(out.list_owner,8,id)||id!=actor.faith_id||
        !At(out.list_owner,0x7C0,out.data)||!At(out.list_owner,0x7CC,out.count))return false;
  }
  // A bounded observation ceiling, not an engine/business maximum. Unknown
  // shape is unavailable; do not enter native linear search on corrupt bounds.
  constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
  return out.count>=0&&out.count<=4096&&(!out.count||out.data)&&
      static_cast<std::uintptr_t>(out.count)<=max/8&&
      (!out.count||out.data<=max-static_cast<std::uintptr_t>(out.count)*8);
}
[[maybe_unused]] std::uintptr_t Resolve(const ReadonlyBindings&b,std::int32_t id) noexcept {
  __try {return reinterpret_cast<std::uintptr_t>(ck3_1210::ResolveCoreCharacter(b.core,id));}
  __except(EXCEPTION_EXECUTE_HANDLER){return 0;}
}
[[maybe_unused]] bool Exact(const ReadonlyBindings&b) noexcept {
  const auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  return base&&b.module_base==base&&b.exact_image_admitted&&b.core.enabled&&
      b.core.image_build==ck3_1210::ImageBuildV1::unknown&&
      reinterpret_cast<std::uintptr_t>(b.core.game_state_slot)==base+kGameStateSlotRva&&
      reinterpret_cast<std::uintptr_t>(b.core.jomini_state_slot)==base+kJominiStateSlotRva&&
      reinterpret_cast<std::uintptr_t>(b.core.character_storage_slot)==base+kCharacterStorageSlotRva&&
      reinterpret_cast<std::uintptr_t>(b.core.get_local_player)==base+kGetLocalPlayerRva;
}
[[maybe_unused]] bool Predicate(std::uintptr_t image,std::uintptr_t actor,std::uintptr_t doctrine,bool&value) noexcept {
  // Current typed reflection and real character-scope script trigger both reach
  // this exact helper. ABI: bool(CCharacter const*,SDoctrineType const*) in AL.
  using Native=bool(__fastcall*)(const void*,const void*);
  __try {value=reinterpret_cast<Native>(image+kKnowsDoctrineNativeRva267V1)(
      reinterpret_cast<const void*>(actor),reinterpret_cast<const void*>(doctrine));return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
} // namespace
std::span<const ImagePin> DoctrineKnowledgeImagePins267V1() noexcept {return doctrine_knowledge_pins::kPins;}
bool VerifyDoctrineKnowledgeImage267V1([[maybe_unused]]std::uintptr_t base) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_KNOWN_DOCTRINE_GATE_V1) && XAR_CK3_ENABLE_121003_26785313_KNOWN_DOCTRINE_GATE_V1
  if(!base||base!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||
      !VerifyReadonlyImage(base)||!VerifyDoctrineKeyImage267V1(base))return false;
  std::array<unsigned char,256> bytes{};
  for(const auto&pin:doctrine_knowledge_pins::kPins) {
    if(pin.bytes.empty()||pin.bytes.size()>bytes.size()||pin.rva>kImageSize-pin.bytes.size()||
        !Copy(base+pin.rva,bytes.data(),pin.bytes.size())||
        std::memcmp(bytes.data(),pin.bytes.data(),pin.bytes.size())!=0)return false;
  }
  for(const auto&pin:doctrine_knowledge_pins::kPointers) {
    std::uintptr_t value=0;
    if(!At(base,pin.slot,value)||value!=base+pin.target)return false;
  }
  return true;
#else
  return false;
#endif
}
RawDoctrineKnowledge267V1 ReadRawKnowsDoctrine267V1(
    [[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]std::uintptr_t actor,
    [[maybe_unused]]std::uintptr_t doctrine) noexcept {
  RawDoctrineKnowledge267V1 out;
#if defined(XAR_CK3_ENABLE_121003_26785313_KNOWN_DOCTRINE_GATE_V1) && XAR_CK3_ENABLE_121003_26785313_KNOWN_DOCTRINE_GATE_V1
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
  if(b.offline_fixture)return out;
#endif
  if(!Exact(b)||!actor||!doctrine||!VerifyDoctrineKnowledgeImage267V1(b.module_base))return out;
  ActorFacts first,second;MembershipFacts first_membership,second_membership;
  DoctrineInternalKey267V1 first_key,second_key;std::string reason;
  bool first_value=false,second_value=false;
  if(!Facts(actor,first)||Resolve(b,first.id)!=actor||!Membership(b.module_base,first,first_membership)||
      !ReadSDoctrineInternalKey267V1(b,doctrine,first_key,reason)||
      !Predicate(b.module_base,actor,doctrine,first_value)||
      !Predicate(b.module_base,actor,doctrine,second_value)||
      !Facts(actor,second)||first!=second||Resolve(b,second.id)!=actor||first_value!=second_value||
      !Membership(b.module_base,second,second_membership)||first_membership!=second_membership||
      !ReadSDoctrineInternalKey267V1(b,doctrine,second_key,reason)||first_key!=second_key||
      !VerifyDoctrineKnowledgeImage267V1(b.module_base))return out;
  out.actor_id=first.id;out.exact_doctrine=std::move(first_key);
  // False is not the full pam OR result: prophet_perk is deliberately unbound.
  out.status=first_value?RawDoctrineKnowledgeStatus267V1::native_true:RawDoctrineKnowledgeStatus267V1::pam_unresolved;
#endif
  return out;
}
} // namespace xar::ck3_121003::build26785313
