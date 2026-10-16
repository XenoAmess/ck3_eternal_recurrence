// Source-only cold fixture: no process attachment, Windows APIs or CK3 execution.
#include "xar_bridge/gui_refill_receiver_candidates_12004.hpp"
#include <cassert>
#include <cstring>
#include <map>
struct Memory {
  std::map<std::uintptr_t,unsigned char> data;int contexts=0;bool change=false;
  template<class T> void put(std::uintptr_t p,T x){const auto *b=reinterpret_cast<const unsigned char*>(&x);for(std::size_t n=0;n<sizeof x;++n)data[p+n]=b[n];}
  static bool read(void *p,std::uintptr_t a,void *b,std::size_t size) noexcept {
    auto &m=*static_cast<Memory*>(p);
    if(a==0x10F0&&++m.contexts==2&&m.change)m.put<std::uintptr_t>(0x5000,0x9000);
    for(std::size_t n=0;n<size;++n){const auto it=m.data.find(a+n);if(it==m.data.end())return false;static_cast<unsigned char*>(b)[n]=it->second;}return true;
  }
  Memory(){
    put<std::uintptr_t>(0x10F0,0x2000);put<std::uintptr_t>(0x10A8,0x3000);put<std::int32_t>(0x10B4,1);
    put<std::uintptr_t>(0x10C0,0x3100);put<std::int32_t>(0x10CC,1);put<std::int32_t>(0x3100,0);put<std::uint32_t>(0x3000,635);
    put<std::uintptr_t>(0x20E0,0x4000);put<std::uint8_t>(0x4115,1);put<std::uintptr_t>(0x4090,0x5000);put<std::int32_t>(0x409C,1);
    put<std::uintptr_t>(0x4108,0);put<std::uintptr_t>(0x20E8,0);put<std::uint32_t>(0x5048,635);put<std::uint8_t>(0x504C,1);put<std::int8_t>(0x5040,3);
    put<std::uintptr_t>(0x5000,0);put<std::uintptr_t>(0x5038,0x6000);put<std::uintptr_t>(0x6000,0x10001000);put<std::uintptr_t>(0x10001010,0x10002000);
  }
};
int main(){
  const auto sample=[](Memory &m){return xar::ck3_12004::ReadGuiRefillReceiverCandidates12004(Memory::read,&m,0x10000000,0x1000);};
  Memory a;auto v=sample(a);assert(v.status=="available"&&v.stable_double_read&&v.entries.size()==1&&v.entries[0].provider_slot2_rva==0x2000);
  Memory b;b.change=true;assert(sample(b).status=="unavailable");
  Memory count;count.put<std::int32_t>(0x409C,257);assert(sample(count).status=="unavailable");
  Memory cycle;cycle.put<std::uint8_t>(0x504C,0);cycle.put<std::uintptr_t>(0x20E8,0x2000);assert(sample(cycle).unavailable_reason=="candidate_parent_cycle");
  Memory wrong;wrong.put<std::uint32_t>(0x3000,636);assert(sample(wrong).status=="unavailable");
  Memory direct;
  direct.put<std::int8_t>(0x5040,1);direct.put<std::uintptr_t>(0x5000,0x9000);
  direct.put<std::int32_t>(0x9218,31254);direct.put<std::uintptr_t>(0x15C67568,0x7000);
  direct.put<std::uintptr_t>(0x7020,0x8000);direct.put<std::int32_t>(0x702C,40000);
  direct.put<std::uintptr_t>(0x8000+31254*0x10+8,0xA000);
  direct.put<std::int32_t>(0xA018,31254);direct.put<std::uint32_t>(0xA01C,0x43686172);
  v=sample(direct);assert(v.status=="available"&&v.entries[0].direct_owner_full_id==31254&&v.entries[0].direct_owner_identity_verified);
  direct.contexts=0;direct.put<std::int32_t>(0xA018,31254+(1<<24));
  v=sample(direct);assert(v.status=="available"&&!v.entries[0].direct_owner_identity_verified);
  // A local nonzero flag excludes this receiver from pending: an unrelated
  // broken parent must not invalidate its candidate observation.
  Memory complete;complete.put<std::uintptr_t>(0x20E8,1);
  assert(sample(complete).status=="available");
  // Null ancestor definition is a native skip branch, and ancestor+115 is
  // never required. The next eligible parent has no mapped active byte.
  Memory parent;parent.put<std::uint8_t>(0x504C,0);parent.put<std::uintptr_t>(0x20E8,0xB000);
  parent.put<std::uintptr_t>(0xB0E0,0);parent.put<std::uintptr_t>(0xB0E8,0xC000);
  parent.put<std::uintptr_t>(0xC0E0,0xD000);parent.put<std::uintptr_t>(0xD090,0xE000);
  parent.put<std::int32_t>(0xD09C,1);parent.put<std::uintptr_t>(0xD108,0);parent.put<std::uintptr_t>(0xC0E8,0);
  parent.put<std::uint32_t>(0xE048,635);parent.put<std::int8_t>(0xE040,3);parent.put<std::uint8_t>(0xE04C,1);
  parent.put<std::uintptr_t>(0xE000,0);parent.put<std::uintptr_t>(0xE038,0x6000);
  v=sample(parent);assert(v.status=="available"&&v.entries.size()==2&&v.entries[1].ancestor_depth==2);
  Memory zero;zero.put<std::int32_t>(0x10B4,0);v=sample(zero);
  assert(v.status=="unavailable"&&v.failure_diagnostic&&v.failure_diagnostic->stage=="callback_declaration_count_b4"&&v.failure_diagnostic->kind=="declaration_count_out_of_bound");
  Memory unread;unread.data.erase(0x10C0);v=sample(unread);
  assert(v.status=="unavailable"&&v.failure_diagnostic&&v.failure_diagnostic->stage=="callback_indices_pointer_c0"&&v.failure_diagnostic->kind=="memory_read_failed");
  Memory null;null.put<std::uintptr_t>(0x5038,0);v=sample(null);assert(v.status=="available"&&!v.entries[0].provider_present&&!v.entries[0].provider_slot2_rva);
}
