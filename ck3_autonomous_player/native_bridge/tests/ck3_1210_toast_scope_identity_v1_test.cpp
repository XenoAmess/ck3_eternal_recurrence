#ifdef NDEBUG
#undef NDEBUG
#endif
#include "xar_bridge/ck3_1210_toast_scope_identity_v1.hpp"
#include "xar_bridge/ck3_1210_toast_objects_v1.hpp"
#include <cassert>
#include <cstring>
#include <iostream>
#include <map>
#include <utility>
using namespace xar::ck3_1210;
namespace {
struct Memory {
  std::map<std::uintptr_t,std::vector<std::byte>> bytes;
  std::size_t reads=0,target_reads=0;
  std::uintptr_t changing=0;
  void add(std::uintptr_t at,std::size_t size) {assert(bytes.emplace(at,std::vector<std::byte>(size)).second);}
  std::byte *find(std::uintptr_t at,std::size_t n) {
    auto i=bytes.upper_bound(at);if(i==bytes.begin())return nullptr;--i;
    const auto offset=at-i->first;
    return offset<=i->second.size() && n<=i->second.size()-offset?i->second.data()+offset:nullptr;
  }
  template<class T>void put(std::uintptr_t at,const T &value) {auto *p=find(at,sizeof(value));assert(p);std::memcpy(p,&value,sizeof(value));}
  static bool copy(void *opaque,std::uintptr_t at,void *out,std::size_t n) noexcept {
    auto &m=*static_cast<Memory *>(opaque);++m.reads;const auto *p=m.find(at,n);if(!p)return false;
    std::memcpy(out,p,n);if(at==m.changing && ++m.target_reads>1)std::memset(out,0,n);return true;
  }
};
struct Fixture {
  static constexpr std::uintptr_t base=0x140000000ULL,story=0x10000,characters=0x20000,story_slots=0x30000,char_slots=0x40000;
  static constexpr std::uintptr_t story_object=0x50000,char_object=0x60000;
  static constexpr std::uint32_t id=0x03000002;
  Memory memory;
  ToastScopeIdentityBindingsV1 bindings{base,true};
  Fixture() {
    memory.add(base+0x6A66700,8);memory.put(base+0x6A66700,story);
    memory.add(base+kCharacterStorageSlotRva,8);memory.put(base+kCharacterStorageSlotRva,characters);
    for(auto pair:{std::pair{story,story_slots},std::pair{characters,char_slots}}) {
      memory.add(pair.first,0x30);memory.put(pair.first+0x20,pair.second);memory.put(pair.first+0x2C,std::uint32_t{3});
      memory.add(pair.second,0x30);
    }
    memory.put(story_slots+0x28,story_object);memory.put(char_slots+0x28,char_object);
    memory.add(story_object,0x20);memory.put(story_object+0x10,id);memory.put(story_object+0x14,std::uint32_t{0x41635374});
    memory.add(char_object,0x20);memory.put(char_object+0x18,id);memory.put(char_object+0x1C,std::uint32_t{0x43686172});
  }
  static std::array<std::byte,16> token(std::uint16_t tag,std::uint64_t value=id) {
    std::array<std::byte,16> t{};std::memcpy(t.data(),&tag,2);std::memcpy(t.data()+8,&value,8);return t;
  }
  bool read(const std::array<std::byte,16> &t,ToastScopeIdentityV1 &out) {
    return ReadToastScopeIdentityV1(bindings,t,{&memory,&Memory::copy},out);
  }
};
} // namespace
int main() {
  unsigned checks=0;
  {Fixture f;ToastScopeIdentityV1 out;assert(f.read(Fixture::token(0x16),out));
    assert(out.status==ToastScopeIdentityStatusV1::available && out.kind==ToastScopeKindV1::story && out.full_id==Fixture::id);++checks;}
  {Fixture f;ToastScopeIdentityV1 out;assert(f.read(Fixture::token(4),out));
    assert(out.status==ToastScopeIdentityStatusV1::available && out.kind==ToastScopeKindV1::character && out.full_id==Fixture::id);++checks;}
  {Fixture f;ToastScopeIdentityV1 out;assert(f.read(Fixture::token(0x24),out));
    assert(out.status==ToastScopeIdentityStatusV1::unsupported && out.full_id==0 && f.memory.reads==0);++checks;}
  {Fixture f;ToastScopeIdentityV1 out;auto t=Fixture::token(0x16);t[2]=std::byte{0xA5};assert(f.read(t,out));
    assert(out.full_id==Fixture::id);++checks;}
  for(auto payload:{std::uint64_t{0x100000002},std::uint64_t{0xFFFFFFFF},std::uint64_t{0x04000002}}) {
    Fixture f;ToastScopeIdentityV1 out;assert(!f.read(Fixture::token(0x16,payload),out));
    assert(out.status==ToastScopeIdentityStatusV1::unavailable && out.full_id==0);++checks;
  }
  {Fixture f;ToastScopeIdentityV1 out;f.memory.put(Fixture::story+0x2C,std::uint32_t{2});assert(!f.read(Fixture::token(0x16),out));++checks;}
  {Fixture f;ToastScopeIdentityV1 out;f.memory.put(Fixture::story+0x2C,std::uint32_t{0x1000001});assert(!f.read(Fixture::token(0x16),out));++checks;}
  {Fixture f;ToastScopeIdentityV1 out;f.memory.put(Fixture::story_slots+0x28,std::uintptr_t{0});assert(!f.read(Fixture::token(0x16),out));++checks;}
  {Fixture f;ToastScopeIdentityV1 out;f.memory.put(Fixture::story_object+0x14,std::uint32_t{0x43686172});assert(!f.read(Fixture::token(0x16),out));++checks;}
  {Fixture f;ToastScopeIdentityV1 out;f.memory.put(Fixture::char_object+0x1C,std::uint32_t{0x41635374});assert(!f.read(Fixture::token(4),out));++checks;}
  {Fixture f;ToastScopeIdentityV1 out;f.memory.changing=Fixture::base+0x6A66700;assert(!f.read(Fixture::token(0x16),out));++checks;}
  {Fixture f;ToastScopeIdentityV1 out;f.memory.changing=Fixture::story_slots+0x28;assert(!f.read(Fixture::token(0x16),out));++checks;}
  {Fixture f;ToastScopeIdentityV1 out;f.memory.changing=Fixture::story_object+0x10;assert(!f.read(Fixture::token(0x16),out));++checks;}
  {Fixture f;ToastScopeIdentityV1 out;f.bindings.exact_build_admitted=false;assert(!f.read(Fixture::token(0x16),out));assert(f.memory.reads==0);++checks;}
  {Fixture f;ToastScopeIdentityV1 out;f.bindings.module_base=~std::uintptr_t{0};assert(!f.read(Fixture::token(0x16),out));assert(f.memory.reads==0);++checks;}
  {Fixture f;ToastScopeIdentityV1 out;assert(!ReadToastScopeIdentityV1(f.bindings,Fixture::token(0x16),{},out));++checks;}
  std::cout<<"toast saved-scope identity: "<<checks<<" checks; owned memory only; no recipient, news or delivery admission\n";
}
