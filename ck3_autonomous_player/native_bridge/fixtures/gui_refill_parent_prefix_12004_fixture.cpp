// Authored memory cases, not a reconstruction of R186's private GUI chain.
#include "xar_bridge/gui_refill_receiver_candidates_serializer_12004.hpp"
#include <chrono>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string_view>
#include <thread>
#if !XAR_ENABLE_GUI_REFILL_PARENT_PREFIX_12004
#error parent prefix fixture requires its explicit source profile
#endif
namespace {
void Need(bool ok){if(!ok)throw std::runtime_error("parent prefix fixture failed");}
struct Memory {
  std::map<std::uintptr_t,unsigned char> bytes;
  std::set<std::uintptr_t> observed;
  unsigned passes=0;
  enum Mutation{none,edge_source,parent_mode};
  Mutation mutation=none;
  bool spend_deadline=false;
  template<class T> void put(std::uintptr_t at,T value){
    const auto *p=reinterpret_cast<const unsigned char*>(&value);
    for(std::size_t n=0;n<sizeof value;++n)bytes[at+n]=p[n];
  }
  Memory(){
    put<std::uintptr_t>(0x10F0,0x20000);put<std::uintptr_t>(0x10A8,0x3000);put<std::int32_t>(0x10B4,1);
    put<std::uintptr_t>(0x10C0,0x3100);put<std::int32_t>(0x10CC,1);put<std::int32_t>(0x3100,0);put<std::uint32_t>(0x3000,635U);
    for(std::uintptr_t n=0;n<8;++n){
      const auto context=0x20000+n*0x1000,definition=0x40000+n*0x1000,table=0x60000+n*0x1000;
      put<std::uintptr_t>(context+0xE0,definition);put<std::uintptr_t>(context+0xE8,context+0x1000);
      put<std::uintptr_t>(definition+0x90,table);put<std::int32_t>(definition+0x9C,n==0||n==1||n==3?1:0);
      put<std::uintptr_t>(definition+0x108,0);
      put<std::uint32_t>(table+0x48,635U);put<std::int8_t>(table+0x40,n==0?0:3);
      put<std::uint8_t>(table+0x4C,n==3?1:0);put<std::uintptr_t>(table,0);
      // Depth1's filtered provider is deliberately unmapped. Depth3's eligible
      // provider has a module vtable/slot2, but is never invoked by the reader.
      put<std::uintptr_t>(table+0x38,n==1?0xDEAD:n==3?0x7000:0);
    }
    put<std::uint8_t>(0x40115,1);put<std::uintptr_t>(0x7000,0x10001000);
    put<std::uintptr_t>(0x10001010,0x10002000);
  }
  static bool read(void *opaque,std::uintptr_t at,void *out,std::size_t count) noexcept {
    auto &m=*static_cast<Memory*>(opaque);m.observed.insert(at);
    if(at==0x10F0&&++m.passes==2U){
      if(m.mutation==edge_source)m.put<std::uintptr_t>(0x41108,0x22000);
      if(m.mutation==parent_mode)m.put<std::int8_t>(0x61040,4);
    }
    for(std::size_t n=0;n<count;++n){
      const auto it=m.bytes.find(at+n);if(it==m.bytes.end())return false;
      static_cast<unsigned char*>(out)[n]=it->second;
    }
    if(m.spend_deadline&&at==0x270E8)std::this_thread::sleep_for(std::chrono::milliseconds(25));
    return true;
  }
};
auto Sample(Memory &memory){return xar::ck3_12004::ReadGuiRefillReceiverCandidates12004(Memory::read,&memory,0x10000000,0x1000);}
void OriginalFailure(const xar::game::GuiRefillReceiverCandidates12004V1 &v){
  Need(v.status=="unavailable"&&v.unavailable_reason=="candidate_parent_depth_exhausted");
  Need(v.failure_diagnostic->capture_pass==1U&&v.failure_diagnostic->ancestor_depth==8U);
  Need(!v.failure_diagnostic->definition_present&&!v.failure_diagnostic->raw_definition_entry_count);
  Need(v.entries.empty()&&!v.receiver_variable_index&&!v.declared_type_id&&!v.stable_double_read);
}
void Quote(std::string &out,std::string_view value){out+='"';for(char c:value){if(c=='"'||c=='\\')out+='\\';out+=c;}out+='"';}
void StableVisitedPrefix(){
  Memory memory;auto value=Sample(memory);OriginalFailure(value);
  const auto &prefix=*value.definition_chain_prefix_depth8;
  Need(prefix.status=="available"&&prefix.stable_double_read&&prefix.rows.size()==8);
  Need(value.local_definition_entry_only->status=="available");
  Need(prefix.rows[0].entries[0].entry_mode_40==0&&!prefix.rows[0].entries[0].direct_value_present);
  Need(prefix.rows[1].entries[0].provider_present&&!prefix.rows[1].entries[0].provider_slot2_rva);
  Need(prefix.rows[3].entries[0].provider_slot2_rva==std::uint64_t{0x2000});
  Need(!memory.observed.contains(0xDEAD)&&!memory.observed.contains(0x280E0));
  std::string json;xar::game::AppendGuiRefillReceiverCandidates12004(json,value,Quote);std::cout<<json<<'\n';
}
void ChangedPrefix(){
  for(const auto mutation:{Memory::edge_source,Memory::parent_mode}){
    Memory memory;memory.mutation=mutation;auto value=Sample(memory);OriginalFailure(value);
    Need(value.local_definition_entry_only->status=="available");
    const auto &prefix=*value.definition_chain_prefix_depth8;
    Need(prefix.status=="unavailable"&&prefix.unavailable_reason=="definition_prefix_identity_or_rows_changed");
    Need(prefix.rows.empty()&&!prefix.receiver_variable_index&&!prefix.declared_type_id);
  }
}
void SharedBudget(){
  Memory memory;memory.spend_deadline=true;auto value=Sample(memory);OriginalFailure(value);
  const auto &prefix=*value.definition_chain_prefix_depth8;
  Need(prefix.status=="unavailable"&&prefix.unavailable_reason=="definition_prefix_shared_budget_exhausted");
  Need(prefix.rows.empty()&&!prefix.stable_double_read&&memory.passes==1U);
}
}
int main(){try{StableVisitedPrefix();ChangedPrefix();SharedBudget();return 0;}catch(...){return 1;}}
