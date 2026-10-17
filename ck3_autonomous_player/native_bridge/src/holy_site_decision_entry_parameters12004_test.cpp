#include "xar_bridge/holy_site_decision_entry_parameters12004.hpp"
#include <algorithm>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <utility>
#include <vector>

using namespace xar::ck3_12004::religion::holy_site;
namespace {
constexpr std::uintptr_t base=0x140000000ULL;
constexpr std::uint32_t site_id=0x81000002U, class_id=0x233U, selected_token=0x10293847U;
struct Region {std::uintptr_t address;std::vector<unsigned char> bytes;};
struct Entry {
  std::uintptr_t button,owner,ancestor,button_def,owner_def,ancestor_def;
  std::uintptr_t button_row,owner_row,ancestor_row,callbacks,callback0,callback1;
  std::uintptr_t arguments,declarations,indices,params,definition,key,scopes,cache_rows;
};
struct Fixture;
Fixture *current=nullptr;
void Require(bool condition,const char *why) {if(!condition)throw std::runtime_error(why);}
struct Fixture {
  std::vector<Region> regions;
  std::size_t lookup_calls=0,changed_return_reads=0;
  std::uintptr_t changed_return_address=0;
  bool change_lookup_on_second=false;
  Fixture() {
    current=this;
    for(const auto &pin:entry_parameters_source::kPins) {
      Add(base+pin.rva,pin.hex.size()/2);
      for(std::size_t i=0;i<pin.hex.size()/2;++i) {
        const auto hex=[](char c){return unsigned(c<='9'?c-'0':c-'a'+10);};
        Put(base+pin.rva,i,std::uint8_t(hex(pin.hex[2*i])*16+hex(pin.hex[2*i+1])));
      }
    }
    Add(base+0x5000,14*8);Put(base+0x5000,13*8,base+0x3AA0D20);
    Add(base+0x6000,24);Put(base+0x6000,0x10,base+0x3AA30E0);
    Meta(0x54D7588,0x44DF830,0x4A922E8,0x56C73B0);
    Meta(0x54D7570,0x44DF6E0,0x4A92248,0x56C7530);
    Add(base+0x48BD150-8,24);Put(base+0x48BD150-8,0,base+0x4AA0020);
    Add(base+0x4AA0020,24);Put(base+0x4AA0020,0,std::uint32_t{1});
    Put(base+0x4AA0020,12,std::uint32_t{0x5586B90});Put(base+0x4AA0020,20,std::uint32_t{0x4AA0020});
    Add(base+0x5D50198,4);Put(base+0x5D50198,0,class_id);
    Add(base+0x5D4C2EC,4);Put(base+0x5D4C2EC,0,selected_token);
    Add(base+0x5D1DE80,8);Put(base+0x5D1DE80,0,std::uintptr_t{0x20000000});
    Add(0x20000000,0x40);Put(0x20000000,0x20,std::uintptr_t{0x20001000});
    Put(0x20000000,0x2C,std::uint32_t{3});Add(0x20001000,3*16);
    Put(0x20001000,2*16+8,std::uintptr_t{0x20002000});Add(0x20002000,0x30);
    Put(0x20002000,0x10,site_id);Put(0x20002000,0x14,std::uint32_t{0x486F5374});
  }
  void Add(std::uintptr_t address,std::size_t size) {
    for(const auto &r:regions)Require(address+size<=r.address||r.address+r.bytes.size()<=address,"fixture region overlap");
    regions.push_back({address,std::vector<unsigned char>(size)});
  }
  template<class T>void Put(std::uintptr_t address,std::size_t offset,T value) {
    const auto a=address+offset;
    for(auto &r:regions)if(a>=r.address&&a-r.address<=r.bytes.size()&&sizeof(T)<=r.bytes.size()-(a-r.address)) {
      std::memcpy(r.bytes.data()+a-r.address,&value,sizeof(T));return;
    }
    throw std::runtime_error("fixture write unmapped");
  }
  template<class T>T Get(std::uintptr_t address,std::size_t offset=0) const {
    T out{};const auto a=address+offset;
    for(const auto &r:regions)if(a>=r.address&&a-r.address<=r.bytes.size()&&sizeof(T)<=r.bytes.size()-(a-r.address)) {
      std::memcpy(&out,r.bytes.data()+a-r.address,sizeof(T));return out;
    }
    throw std::runtime_error("fixture read unmapped");
  }
  void Meta(std::uintptr_t object,std::uintptr_t vtable,std::uintptr_t col,std::uint32_t td) {
    Add(base+object,8);Put(base+object,0,base+vtable);
    Add(base+vtable-8,24);Put(base+vtable-8,0,base+col);
    Add(base+col,24);Put(base+col,0,std::uint32_t{1});Put(base+col,12,td);
    Put(base+col,20,std::uint32_t(col));
  }
  void Header(std::uintptr_t at,std::size_t offset,std::uintptr_t data,std::int32_t count) {
    Put(at,offset,data);Put(at,offset+8,count);Put(at,offset+12,count);Put(at,offset+16,std::uintptr_t{});
  }
  void Row(std::uintptr_t at,std::uintptr_t params,std::int8_t mode,std::uint8_t final) {
    Put(at,0,params);Put(at,0x38,std::uintptr_t{});Put(at,0x40,mode);
    Put(at,0x48,class_id);Put(at,0x4C,final);
  }
  std::size_t Bucket() const {
    const auto key=base+0x54D7588;std::uint32_t hash=0x811C9DC5U;
    for(unsigned i=0;i<8;++i)hash=(hash^std::uint8_t(key>>(8*i)))*0x1000193U;
    return hash&3U;
  }
  void Cache(std::uintptr_t widget,std::uintptr_t rows,std::uintptr_t params) {
    Add(rows,5*0x30);Put(widget,0x1D8+8,rows);Put(widget,0x1D8+0x14,std::int32_t{3});
    Put(widget,0x1D8+0x18,std::uint8_t{});
    Put(rows,Bucket()*0x30+4,std::uint8_t{1});Put(rows,Bucket()*0x30+8,base+0x54D7588);
    Put(rows,Bucket()*0x30+0x10,params);
    Put(rows,4*0x30+4,std::uint8_t{0xFF});
  }
  Entry AddEntry(std::size_t index,DecisionAction action) {
    const auto o=index*0x100000U;
    Entry e{0x10000000+o,0x10001000+o,0x10002000+o,
      0x11000000+o,0x11001000+o,0x11002000+o,
      0x12000000+o,0x12001000+o,0x12002000+o,
      0x13000000+o,0x13001000+o,0x13002000+o,
      0x14000000+o,0x15000000+o,0x15001000+o,
      0x16000000+o,0x17000000+o,0x18000000+o,0x19000000+o,0x1A000000+o};
    for(auto w:{e.button,e.owner,e.ancestor})Add(w,0x500);
    for(auto d:{e.button_def,e.owner_def,e.ancestor_def})Add(d,0x130);
    for(auto row:{e.button_row,e.owner_row,e.ancestor_row})Add(row,0xA0);
    Put(e.button,0,base+0x5000);Put(e.button,0xE0,e.button_def);Put(e.button,0xE8,e.owner);
    Put(e.owner,0xE0,e.owner_def);Put(e.ancestor,0xE0,e.ancestor_def);
    for(auto pair:{std::pair{e.button_def,e.button_row},std::pair{e.owner_def,e.owner_row},std::pair{e.ancestor_def,e.ancestor_row}}) {
      Header(pair.first,0x90,pair.second,1);Put(pair.first,0x115,std::uint8_t{1});
    }
    Row(e.button_row,e.params,0,0);Row(e.owner_row,e.params,0,1);Row(e.ancestor_row,e.params,0,1);
    Add(e.callbacks,2*0x48);Header(e.button,0x338,e.callbacks,2);
    Add(e.callback0,0x140);Add(e.callback1,0x140);
    for(std::size_t i=0;i<2;++i) {
      const auto c=i?e.callback1:e.callback0;
      Put(e.callbacks,i*0x48+0x40,c);Put(c,0,base+0x6000);Put(c,8,base+0x3A9F960);
      Put(c,0xF0,e.button);Put(c,0x10+0x34,std::uint32_t{4});
      Put(c,0x10+0x38,base+(i?0x1031E60:0xA79540));
    }
    Add(e.arguments,0x80);Add(e.declarations,8);Add(e.indices,12);
    Header(e.callback0,0x10,e.arguments,2);Put(e.callback0,0x10+0xB0,e.indices);
    Put(e.callback0,0x10+0xBC,std::int32_t{3});Put(e.indices,4,std::int32_t{0});
    Put(e.callback0,0x10+0x98,e.declarations);Put(e.callback0,0x10+0xA4,std::int32_t{1});
    Put(e.declarations,0,class_id);Put(e.arguments,0x40+0x18,std::uint32_t{0xA1B2C3D4});
    Put(e.arguments,0x40+0x1C,std::uint32_t{2});Put(e.arguments,0x40+0x20,base+0xCAB1C0);
    Put(e.arguments,0x40+0x30,class_id);Put(e.arguments,0x40+0x38,std::uint32_t{1});
    Add(e.params,0x118);Add(e.definition,0x50);Add(e.key,64);Add(e.scopes,0x18);
    Put(e.params,0,e.definition);Put(e.definition,0,base+0x48BD150);
    Put(e.definition,0x38,std::uint32_t{0x4744624F});
    const auto key=DecisionKey(action);Require(!key.empty()&&key.size()<64,"fixed fixture key invalid");
    for(std::size_t i=0;i<key.size();++i)Put(e.key,i,std::uint8_t(key[i]));
    Put(e.definition,0x18,e.key);Put(e.definition,0x28,std::uint64_t(key.size()));
    Put(e.definition,0x30,std::uint64_t{63});Header(e.params,0x30,e.scopes,1);
    Put(e.scopes,0,selected_token);Put(e.scopes,8,std::uint16_t{23});Put(e.scopes,10,std::uint16_t{});
    Put(e.scopes,12,std::uint32_t{0xDEADBEEF}); // uninitialized Scope16 padding is not identity.
    Put(e.scopes,16,std::uint64_t{site_id});Cache(e.owner,e.cache_rows,e.params);
    return e;
  }
  static bool Read(void *context,const void *source,void *out,std::size_t size) noexcept {
    auto &f=*static_cast<Fixture*>(context);const auto a=reinterpret_cast<std::uintptr_t>(source);
    for(const auto &r:f.regions)if(a>=r.address&&a-r.address<=r.bytes.size()&&size<=r.bytes.size()-(a-r.address)) {
      std::memcpy(out,r.bytes.data()+a-r.address,size);
      if(a==f.changed_return_address&&size==4&&++f.changed_return_reads==2) {
        const std::uint32_t changed=0xA1B2C3D5;std::memcpy(out,&changed,4);
      }
      return true;
    }
    return false;
  }
  static const void **__fastcall Lookup(const void *map,const void **out,const void *const *key) {
    auto &f=*current;++f.lookup_calls;const auto m=reinterpret_cast<std::uintptr_t>(map);
    const auto rows=f.Get<std::uintptr_t>(m,8);const auto count=f.Get<std::int32_t>(m,0x14)+1+f.Get<std::uint8_t>(m,0x18);
    *out=reinterpret_cast<const void*>(rows+std::size_t(count)*0x30);
    if(f.change_lookup_on_second&&f.lookup_calls==2)return out;
    for(std::int32_t i=0;i<count;++i)if(f.Get<std::uint8_t>(rows,std::size_t(i)*0x30+4)
        &&f.Get<std::uintptr_t>(rows,std::size_t(i)*0x30+8)==reinterpret_cast<std::uintptr_t>(*key)) {
      *out=reinterpret_cast<const void*>(rows+std::size_t(i)*0x30);break;
    }
    return out;
  }
  EntryParameterBindings Bind() {
    current=this;auto b=BindHolySiteDecisionEntryParametersImage12004(base,xar::ck3_12004::kExecutableSha256);
    b.read_memory=&Read;b.read_context=this;b.cache_lookup=&Lookup;return b;
  }
  bool ReadEntry(const Entry &e,DecisionAction action,EntryParameterSnapshot &out,std::uint32_t id=site_id) {
    return ReadHolySiteDecisionEntryParameters12004(Bind(),reinterpret_cast<const void*>(e.button),action,id,out);
  }
};
void SameSignatureDifferentActions() {
  Fixture f;const auto promote=f.AddEntry(0,DecisionAction::promote),abandon=f.AddEntry(1,DecisionAction::abandon);
  EntryParameterSnapshot out{};
  Require(f.ReadEntry(promote,DecisionAction::promote,out)&&out.available&&out.decision_key_verified,"promote receiver unavailable");
  Require(out.params==reinterpret_cast<const void*>(promote.params)&&out.source_widget==reinterpret_cast<const void*>(promote.owner),"promote cache identity lost");
  Require(out.self_return_type_raw==0xA1B2C3D4,"raw return type was renamed or omitted");
  Require(f.ReadEntry(abandon,DecisionAction::abandon,out)&&out.decision_key==DecisionKey(DecisionAction::abandon),"same-signature abandon receiver unavailable");
  Require(!f.ReadEntry(abandon,DecisionAction::promote,out)&&out.decision_key_verified
      &&out.decision_key==DecisionKey(DecisionAction::abandon)&&out.unavailable_reason=="entry_parameter_decision_key_differs","other fixed action cannot be excluded safely");
}
void IdentityRejections() {
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);f.Put(base+0x5D4C2EC,0,std::uint32_t{});
   f.Put(e.scopes,0,std::uint32_t{});EntryParameterSnapshot out{};
   Require(f.ReadEntry(e,DecisionAction::promote,out),"source-bound token zero was rejected without an original invalid-token rule");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::demote);EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::demote,out,0x82000002)&&!out.decision_key_verified,"wrong generation qualified a sibling");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::demote);f.Put(e.scopes,16,(std::uint64_t{1}<<32)|site_id);EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::demote,out)&&!out.decision_key_verified,"scope high bits were truncated");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::demote);f.Put(0x20002000,0x10,std::uint32_t{0x82000002});EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::demote,out)&&!out.decision_key_verified,"storage generation was not checked");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);f.Put(e.callback0,0xF0,e.owner);EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::promote,out)&&!out.decision_key_verified,"foreign callback receiver qualified");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);f.Put(e.arguments,0x40+0x1C,std::uint32_t{1});EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::promote,out)&&out.unavailable_reason=="entry_parameter_kind1_receiver_unknown","kind1 guessed its receiver flag");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);f.Put(e.arguments,0x40+0x38,std::int32_t{});EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::promote,out)&&!out.decision_key_verified
       &&out.unavailable_reason=="entry_parameter_self_argument_differs"&&f.lookup_calls==0,"Self writing the first argument was mistaken for the second actual input");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);f.Header(e.button,0x3F8,e.callbacks,1);EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::promote,out)&&!out.decision_key_verified,"populated primary was skipped for fallback");}
}
void NativeInheritance() {
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);f.Row(e.owner_row,e.params,1,1);EntryParameterSnapshot out{};
   Require(f.ReadEntry(e,DecisionAction::promote,out),"native direct mode1 was mistaken for a provider");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);f.Put(e.owner,0xE8,e.ancestor);
   f.Row(e.owner_row,e.params,2,1);EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::promote,out)&&!out.decision_key_verified
       &&out.unavailable_reason=="entry_parameter_context_provider_unknown"&&f.lookup_calls==0,"unknown provider was skipped for distant ancestor");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);
   f.Row(e.owner_row,e.params+8,3,0);EntryParameterSnapshot out{};
   Require(f.ReadEntry(e,DecisionAction::promote,out),"no eligible ancestor did not preserve initial direct value");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);f.Header(e.owner_def,0x90,e.owner_row,2);
   f.Row(e.owner_row,e.params+8,2,0);f.Row(e.owner_row+0x50,e.params+8,0,1);EntryParameterSnapshot out{};
   Require(f.ReadEntry(e,DecisionAction::promote,out),"second same-type row overrode native first matching row");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::abandon);f.Put(e.button_def,0x108,e.ancestor);
   f.Put(e.owner,0xE8,e.owner); // unused physical parent is deliberately cyclic.
   f.Put(e.owner,0x1D8+8,std::uintptr_t{});f.Put(e.owner,0x1D8+0x14,std::int32_t{});
   f.Cache(e.ancestor,e.cache_rows+0x1000,e.params);EntryParameterSnapshot out{};
   Require(f.ReadEntry(e,DecisionAction::abandon,out)&&out.source_widget==reinterpret_cast<const void*>(e.ancestor),"definition override did not take priority over parent");}
}
void CacheAndStability() {
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);f.Put(e.cache_rows,4*0x30+4,std::uint8_t{});EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::promote,out)&&!out.decision_key_verified
       &&out.unavailable_reason=="entry_parameter_cache_end_invalid"&&f.lookup_calls==0,"zero terminal was accepted or passed to native lookup");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);
   for(std::size_t i=f.Bucket();i<4;++i){f.Put(e.cache_rows,i*0x30+4,std::uint8_t(i-f.Bucket()+1));
     f.Put(e.cache_rows,i*0x30+8,base+0x54D7000);}
   EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::promote,out)&&!out.decision_key_verified
       &&out.unavailable_reason=="entry_parameter_cache_probe_unavailable"&&f.lookup_calls==0,"terminal probe entered native lookup");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);f.Cache(e.button,e.cache_rows+0x1000,e.params);EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::promote,out)&&!out.decision_key_verified
       &&out.unavailable_reason=="entry_parameter_cache_owner_ambiguous","two eligible owner caches qualified");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);f.Cache(e.button,e.cache_rows+0x1000,e.params+8);EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::promote,out)&&!out.decision_key_verified,"foreign nearest cache was skipped for distant pointer match");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);const auto other=(f.Bucket()+1)%4;
   f.Put(e.cache_rows,other*0x30+4,std::uint8_t{1});f.Put(e.cache_rows,other*0x30+8,base+0x54D7588);EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::promote,out)&&!out.decision_key_verified
       &&out.unavailable_reason=="entry_parameter_cache_type_ambiguous","duplicate typed cache rows qualified");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);f.changed_return_address=e.arguments+0x40+0x18;EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::promote,out)&&!out.decision_key_verified
       &&out.unavailable_reason=="entry_parameter_source_changed","unmapped return type source change was missed");}
  {Fixture f;auto e=f.AddEntry(0,DecisionAction::promote);f.change_lookup_on_second=true;EntryParameterSnapshot out{};
   Require(!f.ReadEntry(e,DecisionAction::promote,out)&&!out.decision_key_verified,"changed native lookup return qualified");}
  Require(!BindHolySiteDecisionEntryParametersImage12004(base,"foreign-image").enabled,"foreign executable was admitted");
}
}
int main() {
  try {
    SameSignatureDifferentActions();IdentityRejections();NativeInheritance();CacheAndStability();
    std::cout<<"same-signature action identities / complete generation / context provider boundary / native inherited cache ownership / double-read stability PASS\n";
    return 0;
  }catch(const std::exception &error){std::cerr<<error.what()<<'\n';return 1;}
}
