// Authored source-layout cases. Never executes a GUI callback or provider.
#include "xar_bridge/gui_refill_receiver_candidates_serializer_12004.hpp"
#include <iostream>
#include <map>
#include <stdexcept>
#include <string_view>
namespace {
void Need(bool ok){if(!ok)throw std::runtime_error("frontier continuation fixture failed");}
struct Memory {
  std::map<std::uintptr_t,unsigned char> bytes;
  std::map<std::uintptr_t,unsigned> reads;
  unsigned passes=0;
  bool mutate_provider=false;
  template<class T> void put(std::uintptr_t at,T value){
    const auto *p=reinterpret_cast<const unsigned char*>(&value);
    for(std::size_t n=0;n<sizeof value;++n)bytes[at+n]=p[n];
  }
  void erase(std::uintptr_t at,std::size_t n){for(std::size_t i=0;i<n;++i)bytes.erase(at+i);}
  Memory(){
    put<std::uintptr_t>(0x10F0,0x20000);put<std::uintptr_t>(0x10A8,0x3000);put<std::int32_t>(0x10B4,1);
    put<std::uintptr_t>(0x10C0,0x3100);put<std::int32_t>(0x10CC,1);put<std::int32_t>(0x3100,0);put<std::uint32_t>(0x3000,635U);
    for(std::uintptr_t n=0;n<12;++n){
      const auto context=0x20000+n*0x1000,definition=0x40000+n*0x1000,table=0x60000+n*0x1000;
      put<std::uintptr_t>(context+0xE0,definition);put<std::uintptr_t>(context+0xE8,context+0x1000);
      put<std::uintptr_t>(definition+0x90,table);put<std::int32_t>(definition+0x9C,n==0||n==8||n==9?1:0);
      put<std::uintptr_t>(definition+0x108,0);
      put<std::uint32_t>(table+0x48,635U);put<std::int8_t>(table+0x40,n==0?0:3);
      put<std::uint8_t>(table+0x4C,n==8?1:0);put<std::uintptr_t>(table,0);
      put<std::uintptr_t>(table+0x38,n==8?0x7000:n==9?0xDEAD:0);
    }
    put<std::uint8_t>(0x40115,1);put<std::uintptr_t>(0x7000,0x10001000);
    put<std::uintptr_t>(0x10001010,0x10002000);
  }
  static bool read(void *opaque,std::uintptr_t at,void *out,std::size_t count) noexcept {
    auto &m=*static_cast<Memory*>(opaque);++m.reads[at];
    if(at==0x10F0&&++m.passes==2U&&m.mutate_provider)m.put<std::uintptr_t>(0x10001010,0x10003000);
    for(std::size_t n=0;n<count;++n){auto it=m.bytes.find(at+n);if(it==m.bytes.end())return false;static_cast<unsigned char*>(out)[n]=it->second;}
    return true;
  }
};
auto Sample(Memory &m){return xar::ck3_12004::ReadGuiRefillReceiverCandidates12004(Memory::read,&m,0x10000000,0x1000);}
void Quote(std::string &out,std::string_view value){out+='"';for(char c:value){if(c=='"'||c=='\\')out+='\\';out+=c;}out+='"';}
void Wire(const xar::game::GuiRefillReceiverCandidates12004V1 &v){std::string s;xar::game::AppendGuiRefillReceiverCandidates12004(s,v,Quote);std::cout<<s<<'\n';}
}
int main(){try{
  Memory m;auto value=Sample(m);
  Need(value.status=="unavailable"&&value.unavailable_reason=="candidate_parent_depth_exhausted");
  Need(value.failure_diagnostic&&value.failure_diagnostic->ancestor_depth==std::uint32_t{8}&&value.failure_diagnostic->capture_pass==1U);
  Need(value.entries.empty()&&!value.receiver_variable_index);
#if XAR_ENABLE_GUI_REFILL_FRONTIER_CONTINUATION_12004
  const auto &tail=*value.definition_frontier_continuation_depth8_12;
  Need(value.definition_chain_prefix_depth8->status=="available");
  Need(tail.status=="available"&&tail.stable_double_read&&tail.rows.size()==4);
  Need(tail.stop_reason=="depth_limit"&&tail.stop_depth==std::uint32_t{12}&&tail.next_context_present==true);
  Need(tail.rows[0].entries[0].provider_slot2_rva==std::uint64_t{0x2000});
  Need(tail.rows[1].entries[0].provider_present&&!tail.rows[1].entries[0].provider_slot2_rva);
  Need(!m.reads.contains(0xDEAD)&&!m.reads.contains(0x2C0E0));Wire(value);
  Memory changed;changed.mutate_provider=true;auto unstable=Sample(changed);
  Need(unstable.definition_chain_prefix_depth8->status=="available");
  Need(unstable.definition_frontier_continuation_depth8_12->unavailable_reason=="frontier_continuation_identity_or_rows_changed");
  Need(unstable.definition_frontier_continuation_depth8_12->rows.empty());Wire(unstable);
  Memory ended;ended.put<std::uintptr_t>(0x280E0,0);ended.put<std::uintptr_t>(0x280E8,0);auto end=Sample(ended);
  Need(end.definition_frontier_continuation_depth8_12->stop_reason=="null_end");
  Need(end.definition_frontier_continuation_depth8_12->stop_depth==std::uint32_t{9}&&!ended.reads.contains(0x290E0));Wire(end);
  Memory cyclic;cyclic.put<std::uintptr_t>(0x280E0,0);cyclic.put<std::uintptr_t>(0x280E8,0x23000);auto cycle=Sample(cyclic);
  Need(cycle.definition_frontier_continuation_depth8_12->stop_reason=="cycle");
  Need(cycle.definition_frontier_continuation_depth8_12->stop_depth==std::uint32_t{9}&&cyclic.reads[0x230E0]==2U);Wire(cycle);
  Memory direct;direct.put<std::int8_t>(0x68040,0);direct.erase(0x48108,8);direct.erase(0x280E8,8);auto stopped=Sample(direct);
  const auto &stop=*stopped.definition_frontier_continuation_depth8_12;
  Need(stop.status=="available"&&stop.stop_reason=="static_direct_terminal"&&stop.rows.size()==1);
  Need(!stop.rows[0].parent_present&&!stop.next_context_present&&!direct.reads.contains(0x48108));Wire(stopped);
  Memory missing;missing.erase(0x280E0,8);auto failed=Sample(missing);
  const auto &fail=*failed.definition_frontier_continuation_depth8_12;
  Need(fail.status=="unavailable"&&fail.rows.empty()&&fail.failure_diagnostic);
  Need(fail.failure_diagnostic->ancestor_depth==std::uint32_t{8}&&fail.failure_diagnostic->kind=="memory_read_failed");Wire(failed);
#else
  Need(!value.definition_frontier_continuation_depth8_12&&!m.reads.contains(0x280E0));Wire(value);
#endif
  return 0;
}catch(...){return 1;}}
