#pragma once
#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {
struct GuiRefillReceiverEntry12004V1 {
  std::uint32_t ancestor_depth=0,entry_type_48=0;
  std::int8_t entry_mode_40=0;
  std::uint8_t entry_flag_4c=0;
  bool direct_value_present=false,provider_present=false;
  std::optional<std::uint64_t> provider_vtable_rva,provider_slot2_rva;
  std::optional<std::int32_t> direct_owner_full_id;
  bool direct_owner_identity_verified=false;
  bool operator==(const GuiRefillReceiverEntry12004V1 &) const=default;
};
struct GuiRefillReceiverCandidates12004V1 {
  std::string status="unavailable",unavailable_reason="candidate_read_not_admitted";
  std::optional<std::int32_t> receiver_variable_index;
  std::optional<std::uint32_t> declared_type_id;
  bool stable_double_read=false;
  std::vector<GuiRefillReceiverEntry12004V1> entries;
  bool operator==(const GuiRefillReceiverCandidates12004V1 &) const=default;
};
struct GuiRefillReceiverFrame12004V1 {
  std::uint64_t native_revision=0,connection_generation=0,pump_epoch=0,ticket_sequence=0;
  std::uint32_t game_pid=0,thread_id=0;
  std::int32_t played_character_full_id=-1,date_raw=0;
};
}

namespace xar::ck3_12004 {
using GuiRefillRead12004=bool(*)(void*,std::uintptr_t,void*,std::size_t) noexcept;
// Pure memory only. No callback/provider invocation and no native variable-table
// claim: 3AC38C0 creates that table in its own temporary stack invocation.
inline game::GuiRefillReceiverCandidates12004V1 ReadGuiRefillReceiverCandidates12004(
    GuiRefillRead12004 read,void *opaque,std::uintptr_t module_base,
    std::uintptr_t callback) {
  using Result=game::GuiRefillReceiverCandidates12004V1;
  constexpr std::uintptr_t image_size=0x61C5000;
  Result rejected;
  if(!read||!module_base||module_base>UINTPTR_MAX-image_size||!callback)return rejected;
  const auto started=std::chrono::steady_clock::now();
  std::size_t reads=0,bytes=0;
  const char *failure="candidate_memory_unreadable";
  const auto load=[&]<class T>(std::uintptr_t object,std::size_t offset,T &value) {
    if(!object||object>UINTPTR_MAX-offset||object+offset>UINTPTR_MAX-sizeof(T))return false;
    if(++reads>4096||(bytes+=sizeof(T))>65536||
        std::chrono::steady_clock::now()-started>std::chrono::milliseconds(20)){
      failure="candidate_read_budget_exhausted";return false;
    }
    return read(opaque,object+offset,&value,sizeof(T));
  };
  const auto rva=[&](std::uintptr_t p,std::size_t n)->std::optional<std::uint64_t>{
    if(p<=module_base||n>image_size||p-module_base>image_size-n)return {};
    return p-module_base;
  };
  struct Capture {Result result;std::vector<std::uintptr_t> private_identity;};
  const auto once=[&](Capture &out) {
    auto &v=out.result;auto &identity=out.private_identity;
    std::uintptr_t context=0,declarations=0,indices=0;
    std::int32_t count=0,index_count=0,index=0;std::uint32_t key=0;
    // The callback+10 expression block supplies declaration keys and the last
    // receiver-variable index. These are declarations, not an evaluated table.
    if(!load(callback,0xF0,context)||!context||
        !load(callback,0xA8,declarations)||!load(callback,0xB4,count)||count<1||count>256||!declarations||
        !load(callback,0xC0,indices)||!load(callback,0xCC,index_count)||index_count<1||index_count>256||!indices||
        !load(indices,static_cast<std::size_t>(index_count-1)*4,index)||index<0||index>=count||
        !load(declarations,static_cast<std::size_t>(index)*8,key))return false;
    v.receiver_variable_index=index;v.declared_type_id=key;
    if(key!=635){failure="receiver_declaration_not_type635";return false;}
    identity={callback,context,declarations,indices,static_cast<std::uintptr_t>(count),static_cast<std::uintptr_t>(index_count)};
    std::array<std::uintptr_t,8> visited{};
    for(std::uint32_t depth=0;context;++depth){
      if(depth==visited.size()){failure="candidate_parent_depth_exhausted";return false;}
      for(std::size_t n=0;n<depth;++n)if(visited[n]==context){failure="candidate_parent_cycle";return false;}
      visited[depth]=context;
      std::uintptr_t definition=0,table=0,parent=0,matched=0;std::int32_t entries=0;std::uint8_t active=0;
      if(!load(context,0xE0,definition)||!definition||!load(definition,0x115,active)||
          (depth==0&&active==0)||!load(definition,0x90,table)||!load(definition,0x9C,entries)||
          entries<0||entries>256||(entries&&!table))return false;
      identity.insert(identity.end(),{context,definition,table,static_cast<std::uintptr_t>(entries),active});
      // First match follows native lookup order; a duplicate key is not
      // silently treated as a second native receiver candidate.
      for(std::int32_t n=0;n<entries;++n){
        std::uint32_t actual=0;const auto offset=static_cast<std::size_t>(n)*0x50;
        if(!load(table,offset+0x48,actual))return false;
        identity.push_back(actual);
        if(!matched&&actual==key){if(table>UINTPTR_MAX-offset)return false;matched=table+offset;}
      }
      if(matched){
        game::GuiRefillReceiverEntry12004V1 e;e.ancestor_depth=depth;
        std::uintptr_t direct=0,provider=0,vt=0,target=0;
        if(!load(matched,0x48,e.entry_type_48)||e.entry_type_48!=key||!load(matched,0x40,e.entry_mode_40)||
            !load(matched,0x4C,e.entry_flag_4c)||!load(matched,0,direct)||!load(matched,0x38,provider))return false;
        e.direct_value_present=direct!=0;e.provider_present=provider!=0;
        identity.insert(identity.end(),{matched,direct,provider,static_cast<std::uintptr_t>(static_cast<std::uint8_t>(e.entry_mode_40)),e.entry_flag_4c});
        if(e.entry_mode_40>=2&&provider){
          if(!load(provider,0,vt))return false;
          e.provider_vtable_rva=rva(vt,24);
          if(e.provider_vtable_rva){if(!load(vt,0x10,target))return false;e.provider_slot2_rva=rva(target,1);}
          identity.insert(identity.end(),{vt,target});
        }
        if(e.entry_mode_40==1&&direct){
          std::int32_t owner=-1;std::uintptr_t storage=0,slots=0,character=0;std::int32_t capacity=0,id=-1;std::uint32_t magic=0;
          if(!load(direct,0x218,owner))return false;
          e.direct_owner_full_id=owner;
          const auto slot=static_cast<std::uint32_t>(owner)&0xFFFFFFU;
          if(owner!=-1&&load(module_base,0x5C67568,storage)&&storage&&
              load(storage,0x20,slots)&&load(storage,0x2C,capacity)&&slots&&capacity>0&&slot<static_cast<std::uint32_t>(capacity)&&
              load(slots,static_cast<std::size_t>(slot)*0x10+8,character)&&character&&
              load(character,0x18,id)&&load(character,0x1C,magic)&&id==owner&&magic==0x43686172)
            e.direct_owner_identity_verified=true;
          identity.insert(identity.end(),{static_cast<std::uintptr_t>(static_cast<std::uint32_t>(owner)),storage,slots,character,static_cast<std::uintptr_t>(static_cast<std::uint32_t>(capacity)),static_cast<std::uintptr_t>(static_cast<std::uint32_t>(id)),magic});
        }
        v.entries.push_back(e);
      }
      // Publish bounded entry candidates, without predicting whether a dynamic
      // provider returns success or which pending parent entry native selects.
      if(!load(definition,0x108,parent))return false;
      if(!parent&&!load(context,0xE8,parent))return false;
      identity.push_back(parent);context=parent;
    }
    v.status="available";v.unavailable_reason.clear();return true;
  };
  Capture a,b;
  if(!once(a)||!once(b)){rejected.unavailable_reason=failure;return rejected;}
  if(a.private_identity!=b.private_identity||a.result!=b.result){rejected.unavailable_reason="candidate_identity_or_type_changed";return rejected;}
  a.result.stable_double_read=true;return a.result;
}
}
