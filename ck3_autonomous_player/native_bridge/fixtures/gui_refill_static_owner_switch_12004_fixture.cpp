// Focused authored wire cases; source layouts only, no callback/provider call.
#include "xar_bridge/gui_refill_receiver_candidates_serializer_12004.hpp"
#include <iostream>
#include <map>
#include <stdexcept>
#include <string_view>
namespace {
void Need(bool ok){if(!ok)throw std::runtime_error("static owner switch fixture");}
struct Memory {
  std::map<std::uintptr_t,unsigned char> bytes;
  std::map<std::uintptr_t,unsigned> reads;
  unsigned passes=0;bool mutate=false;
  template<class T> void put(std::uintptr_t at,T value){const auto *b=reinterpret_cast<const unsigned char*>(&value);for(std::size_t i=0;i<sizeof value;++i)bytes[at+i]=b[i];}
  Memory(){
    put<std::uintptr_t>(0x10F0,0x20000);put<std::uintptr_t>(0x10A8,0x3000);put<std::int32_t>(0x10B4,1);
    put<std::uintptr_t>(0x10C0,0x3100);put<std::int32_t>(0x10CC,1);put<std::int32_t>(0x3100,0);put<std::uint32_t>(0x3000,635U);
    for(std::uintptr_t n=0;n<=8;++n){
      const auto context=0x20000+n*0x1000,definition=0x40000+n*0x1000,table=0x60000+n*0x1000;
      put<std::uintptr_t>(context+0xE0,n>=5&&n<=7?0:definition);put<std::uintptr_t>(context+0xE8,context+0x1000);
      put<std::uintptr_t>(definition+0x90,table);put<std::int32_t>(definition+0x9C,n==8?3:n==0||n==4?1:0);put<std::uintptr_t>(definition+0x108,0);
      put<std::uint32_t>(table+0x48,635U);put<std::int8_t>(table+0x40,n==8?1:0);put<std::uint8_t>(table+0x4C,n==8?1:0);
      put<std::uintptr_t>(table,n==8?0x90000:0);put<std::uintptr_t>(table+0x38,0);
    }
    put<std::uint8_t>(0x40115,1);put<std::int32_t>(0x90218,31254);
    put<std::uintptr_t>(0x10000000+0x5C67568,0xA0000);put<std::uintptr_t>(0xA0020,0xB0000);put<std::int32_t>(0xA002C,40000);
    put<std::uintptr_t>(0xB0000+std::uintptr_t{31254}*16+8,0xC0000);put<std::int32_t>(0xC0018,31254);put<std::uint32_t>(0xC001C,0x43686172U);
    put<std::uintptr_t>(0xC01C0,0xD0000);put<std::uint8_t>(0xD04A9,0);
  }
  static bool read(void *opaque,std::uintptr_t at,void *out,std::size_t count) noexcept {
    auto &m=*static_cast<Memory*>(opaque);++m.reads[at];
    if(at==0x10F0&&++m.passes==2U&&m.mutate)m.put<std::uint8_t>(0xD04A9,2);
    for(std::size_t n=0;n<count;++n){const auto it=m.bytes.find(at+n);if(it==m.bytes.end())return false;static_cast<unsigned char*>(out)[n]=it->second;}return true;
  }
};
auto Sample(Memory &m){return xar::ck3_12004::ReadGuiRefillReceiverCandidates12004(Memory::read,&m,0x10000000,0x1000);}
void Quote(std::string &s,std::string_view v){s+='"';for(char c:v){if(c=='"'||c=='\\')s+='\\';s+=c;}s+='"';}
void Wire(const xar::game::GuiRefillReceiverCandidates12004V1 &v){std::string s;xar::game::AppendGuiRefillReceiverCandidates12004(s,v,Quote);std::cout<<s<<'\n';}
void Source(const xar::game::GuiRefillReceiverCandidates12004V1 &v){
  Need(v.status=="unavailable"&&v.unavailable_reason=="candidate_parent_depth_exhausted");
  Need(v.failure_diagnostic&&v.failure_diagnostic->capture_pass==1U&&v.failure_diagnostic->read_ordinal==51U);
  Need(v.definition_frontier_continuation_depth8_12&&v.definition_frontier_continuation_depth8_12->status=="available");
  Need(v.definition_frontier_continuation_depth8_12->stop_depth==std::uint32_t{8});
}
}
int main(){try{
  Memory m;auto value=Sample(m);Source(value);
#if XAR_ENABLE_GUI_REFILL_STATIC_OWNER_SWITCH_12004
  auto leaf=value.definition_frontier_continuation_depth8_12->static_direct_owner_switch_12004;
  Need(leaf&&leaf->status=="available"&&leaf->stable_double_read&&leaf->owner_full_id==std::int32_t{31254});
  Need(leaf->raw_byte_4a9==std::uint8_t{0}&&leaf->enabled==false);Wire(value);
  Memory nonzero;nonzero.put<std::uint8_t>(0xD04A9,2);auto enabled=Sample(nonzero);Source(enabled);
  Need(enabled.definition_frontier_continuation_depth8_12->static_direct_owner_switch_12004->enabled==true);Wire(enabled);
  Memory null_component;null_component.put<std::uintptr_t>(0xC01C0,0);auto zero=Sample(null_component);Source(zero);
  leaf=zero.definition_frontier_continuation_depth8_12->static_direct_owner_switch_12004;
  Need(leaf->status=="available"&&leaf->military_component_present==false&&!leaf->raw_byte_4a9&&leaf->enabled==false&&leaf->value_basis=="native_null_military_zero");
  Need(!null_component.reads.contains(0xD04A9));Wire(zero);
  Memory missing;missing.bytes.erase(0xD04A9);auto unavailable=Sample(missing);Source(unavailable);
  leaf=unavailable.definition_frontier_continuation_depth8_12->static_direct_owner_switch_12004;
  Need(leaf->status=="unavailable"&&!leaf->raw_byte_4a9&&!leaf->enabled);Wire(unavailable);
  Memory component_failed;component_failed.bytes.erase(0xC01C0);auto no_component=Sample(component_failed);Source(no_component);
  Need(no_component.definition_frontier_continuation_depth8_12->static_direct_owner_switch_12004->unavailable_reason=="static_owner_military_read_failed");Wire(no_component);
  Memory changed;changed.mutate=true;auto unstable=Sample(changed);Source(unstable);
  leaf=unstable.definition_frontier_continuation_depth8_12->static_direct_owner_switch_12004;
  Need(leaf->unavailable_reason=="static_owner_switch_changed_during_capture"&&!leaf->owner_full_id&&!leaf->enabled);Wire(unstable);
  Memory bad_owner;bad_owner.put<std::int32_t>(0xC0018,31255);auto mismatch=Sample(bad_owner);Source(mismatch);
  Need(mismatch.definition_frontier_continuation_depth8_12->static_direct_owner_switch_12004->status=="unavailable");
  Need(!bad_owner.reads.contains(0xC01C0));Wire(mismatch);
  Memory filtered;filtered.put<std::uint8_t>(0x6804C,0);filtered.put<std::uintptr_t>(0x280E8,0);auto flag0=Sample(filtered);
  Need(flag0.status=="unavailable"&&flag0.definition_frontier_continuation_depth8_12->status=="available");
  Need(flag0.definition_frontier_continuation_depth8_12->stop_reason=="null_end");
  Need(flag0.definition_frontier_continuation_depth8_12->static_direct_owner_switch_12004->status=="unavailable");
  Need(!filtered.reads.contains(0x90218)&&!filtered.reads.contains(0xC01C0));Wire(flag0);
#else
  Need(!value.definition_frontier_continuation_depth8_12->static_direct_owner_switch_12004);
  Need(!m.reads.contains(0xC01C0)&&!m.reads.contains(0xD04A9));Wire(value);
#endif
  return 0;
}catch(...){return 1;}}
