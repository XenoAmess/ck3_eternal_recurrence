// New source-shaped memory cases only; no game, process, provider or SDK call.
#include "xar_bridge/gui_refill_receiver_candidates_serializer_12004.hpp"
#include <array>
#include <chrono>
#include <cstring>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string_view>
#include <thread>

namespace {
void Need(bool ok){if(!ok)throw std::runtime_error("local prefix fixture failed");}
struct Memory {
  enum Change{none,mode,flag,provider_same_rvas,slot2};
  std::map<std::uintptr_t,unsigned char> bytes;
  std::set<std::uintptr_t> reads;
  unsigned contexts=0;
  Change change=none;
  bool spend_deadline=false,deadline_spent=false;
  template<class T> void put(std::uintptr_t at,T value){
    const auto *p=reinterpret_cast<const unsigned char*>(&value);
    for(std::size_t n=0;n<sizeof value;++n)bytes[at+n]=p[n];
  }
  Memory(){
    put<std::uintptr_t>(0x10F0,0x2000);put<std::uintptr_t>(0x10A8,0x3000);put<std::int32_t>(0x10B4,1);
    put<std::uintptr_t>(0x10C0,0x3100);put<std::int32_t>(0x10CC,1);put<std::int32_t>(0x3100,0);put<std::uint32_t>(0x3000,635);
    put<std::uintptr_t>(0x20E0,0x4000);put<std::uint8_t>(0x4115,1);
    put<std::uintptr_t>(0x4090,0x5000);put<std::int32_t>(0x409C,1);
    put<std::uint32_t>(0x5048,635);put<std::int8_t>(0x5040,3);put<std::uint8_t>(0x504C,0);
    put<std::uintptr_t>(0x5000,0);put<std::uintptr_t>(0x5038,0x6000);
    put<std::uintptr_t>(0x6000,0x10001000);put<std::uintptr_t>(0x6100,0x10001000);
    put<std::uintptr_t>(0x10001010,0x10002000);
    put<std::uintptr_t>(0x4108,0);put<std::uintptr_t>(0x20E8,0x21000);
    // This authored layout happens to consume51 reads before depth8. It does
    // not reconstruct R184's private chain from that scalar count.
    for(std::uintptr_t n=1;n<8;++n){
      const auto context=0x20000+n*0x1000;
      if(n<=4){
        const auto definition=0x40000+n*0x1000,table=0x60000+n*0x1000;
        put<std::uintptr_t>(context+0xE0,definition);put<std::uintptr_t>(definition+0x90,table);
        put<std::int32_t>(definition+0x9C,1);put<std::uint32_t>(table+0x48,636);
        put<std::uintptr_t>(definition+0x108,0);
      }else put<std::uintptr_t>(context+0xE0,0);
      put<std::uintptr_t>(context+0xE8,context+0x1000);
    }
  }
  static bool read(void *opaque,std::uintptr_t at,void *out,std::size_t count) noexcept {
    auto &m=*static_cast<Memory*>(opaque);m.reads.insert(at);
    if(at==0x10F0&&++m.contexts==2){
      if(m.change==mode)m.put<std::int8_t>(0x5040,4);
      if(m.change==flag)m.put<std::uint8_t>(0x504C,1);
      if(m.change==provider_same_rvas)m.put<std::uintptr_t>(0x5038,0x6100);
      if(m.change==slot2)m.put<std::uintptr_t>(0x10001010,0x10003000);
    }
    for(std::size_t n=0;n<count;++n){
      const auto it=m.bytes.find(at+n);if(it==m.bytes.end())return false;
      static_cast<unsigned char*>(out)[n]=it->second;
    }
    if(m.spend_deadline&&!m.deadline_spent&&at==0x270E8){
      m.deadline_spent=true;std::this_thread::sleep_for(std::chrono::milliseconds(25));
    }
    return true;
  }
};
auto Sample(Memory &memory){return xar::ck3_12004::ReadGuiRefillReceiverCandidates12004(
    Memory::read,&memory,0x10000000,0x1000);}
void LegacyDepthFailure(const xar::game::GuiRefillReceiverCandidates12004V1 &v){
  Need(v.status=="unavailable"&&v.entries.empty()&&!v.receiver_variable_index&&!v.declared_type_id&&!v.stable_double_read);
  Need(v.unavailable_reason=="candidate_parent_depth_exhausted"&&v.failure_diagnostic.has_value());
  const auto &d=*v.failure_diagnostic;
  Need(d.stage=="parent_walk"&&d.kind=="parent_depth_exhausted"&&d.capture_pass==1&&d.ancestor_depth==8);
  Need(!d.definition_present&&!d.raw_definition_entry_count);
}
void Quote(std::string &out,std::string_view value){
  out+='"';for(const char c:value){if(c=='"'||c=='\\')out+='\\';out+=c;}out+='"';
}
void StableLocal(){
  Memory memory;auto v=Sample(memory);LegacyDepthFailure(v);
  Need(v.failure_diagnostic->read_ordinal==51&&v.local_definition_entry_only.has_value());
  const auto &local=*v.local_definition_entry_only;
  Need(local.status=="available"&&local.stable_double_read&&local.definition_present==true&&local.local_entry_present==true);
  Need(local.entries.size()==1&&local.entries[0].ancestor_depth==0&&local.entries[0].provider_slot2_rva==0x2000);
  std::string json;xar::game::AppendGuiRefillReceiverCandidates12004(json,v,Quote);std::cout<<json<<'\n';
  // A complete, stable empty local lookup remains distinct from unreadable.
  Memory empty;empty.put<std::int32_t>(0x409C,0);auto e=Sample(empty);LegacyDepthFailure(e);
  Need(e.local_definition_entry_only->status=="available"&&e.local_definition_entry_only->local_entry_present==false&&e.local_definition_entry_only->entries.empty());
}
void ChangedPrefix(){
  for(const auto mutation:{Memory::mode,Memory::flag,Memory::provider_same_rvas,Memory::slot2}){
    Memory memory;memory.change=mutation;auto v=Sample(memory);LegacyDepthFailure(v);
    Need(v.local_definition_entry_only->status=="unavailable"&&!v.local_definition_entry_only->stable_double_read);
    Need(v.local_definition_entry_only->unavailable_reason=="local_prefix_identity_or_entry_changed");
    Need(v.local_definition_entry_only->entries.empty()&&!v.local_definition_entry_only->local_entry_present);
  }
}
void IncompletePrefix(){
  Memory memory;memory.bytes.erase(0x5038);auto v=Sample(memory);
  Need(v.status=="unavailable"&&v.failure_diagnostic->stage=="matched_provider_38");
  Need(v.local_definition_entry_only->status=="unavailable"&&v.local_definition_entry_only->entries.empty());
  Need(!v.local_definition_entry_only->raw_definition_entry_count&&!v.local_definition_entry_only->definition_present);
}
void FirstMatchStops(){
  Memory memory;memory.put<std::int32_t>(0x409C,2);auto v=Sample(memory);LegacyDepthFailure(v);
  Need(v.local_definition_entry_only->status=="available"&&v.local_definition_entry_only->entries.size()==1);
  Need(v.local_definition_entry_only->raw_definition_entry_count==2&&!memory.reads.contains(0x5098));
}
void SameBudget(){
  Memory memory;memory.spend_deadline=true;auto v=Sample(memory);LegacyDepthFailure(v);
  Need(v.local_definition_entry_only->status=="unavailable"&&!v.local_definition_entry_only->stable_double_read);
  Need(v.local_definition_entry_only->failure_diagnostic->kind=="read_budget_exhausted");
  Need(v.local_definition_entry_only->failure_diagnostic->capture_pass==2&&memory.contexts==1);
}
}
int main(){try{StableLocal();ChangedPrefix();IncompletePrefix();FirstMatchStops();SameBudget();return 0;}catch(...){return 1;}}
