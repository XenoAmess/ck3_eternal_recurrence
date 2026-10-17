#include "xar_bridge/holy_site_decision_entry_parameters12004.hpp"
#include <windows.h>
#include <algorithm>
#include <cstring>
#include <limits>
#include <utility>
#include <vector>

namespace xar::ck3_12004::religion::holy_site {
namespace {
constexpr std::uint32_t absent = 0xFFFFFFFFU;
constexpr std::uintptr_t image_size = 0x61C5000;
const void *At(const void *p, std::size_t offset) noexcept {
  const auto a = reinterpret_cast<std::uintptr_t>(p);
  return a && offset <= (std::numeric_limits<std::uintptr_t>::max)() - a
      ? reinterpret_cast<const void *>(a + offset) : nullptr;
}
bool ProcessRead(void *, const void *p, void *out, std::size_t size) noexcept {
  SIZE_T actual = 0;
  return p && out && ReadProcessMemory(GetCurrentProcess(), p, out, size, &actual)
      && actual == size;
}
struct Reader {
  const EntryParameterBindings &b;
  std::vector<unsigned char> fingerprint;
  bool Bytes(const void *p, void *out, std::size_t size) {
    if (!p || !size || size > 65536 || fingerprint.size() + size + 16 > 2U*1024U*1024U
        || !b.read_memory(b.read_context, p, out, size)) return false;
    const auto address = reinterpret_cast<std::uintptr_t>(p);
    const auto append = [&](const void *v, std::size_t n) {
      const auto *a = static_cast<const unsigned char *>(v);
      fingerprint.insert(fingerprint.end(), a, a+n);
    };
    append(&address, sizeof(address)); append(&size, sizeof(size)); append(out, size);
    return true;
  }
  template<class T> bool Read(const void *p, std::size_t offset, T &value) {
    return Bytes(At(p, offset), &value, sizeof(value));
  }
  bool Image(const void *p, std::size_t bytes=1) const noexcept {
    const auto a = reinterpret_cast<std::uintptr_t>(p);
    return a >= b.image_base && bytes <= image_size
        && a - b.image_base <= image_size - bytes;
  }
  const void *ImageAt(std::uintptr_t rva) const noexcept {
    return reinterpret_cast<const void *>(b.image_base+rva);
  }
};
struct Pass {
  const void *params=nullptr, *definition=nullptr, *source_widget=nullptr;
  std::string key, reason;
  std::uint32_t return_type=0;
  std::vector<unsigned char> fingerprint;
};
bool Fail(Pass &p, const char *reason) { p.reason=reason; return false; }
unsigned Hex(char c) noexcept { return c>='0'&&c<='9' ? unsigned(c-'0') : unsigned(c-'a'+10); }
bool Pins(Reader &r) {
  for (const auto &pin: entry_parameters_source::kPins) {
    std::array<unsigned char,64> bytes{};
    const auto size=pin.hex.size()/2;
    if (!size || size>bytes.size() || !r.Bytes(r.ImageAt(pin.rva),bytes.data(),size)) return false;
    for(std::size_t i=0;i<size;++i)
      if(bytes[i] != (Hex(pin.hex[2*i])*16+Hex(pin.hex[2*i+1]))) return false;
  }
  return true;
}
bool Typed(Reader &r,const void *object,std::uintptr_t vt,std::uint32_t td,
           std::uintptr_t exact_col=0) {
  const void *actual=nullptr,*col=nullptr; std::uint32_t signature=0,type=0,self=0;
  return r.Read(object,0,actual) && actual==r.ImageAt(vt)
      && r.Read(r.ImageAt(vt-8),0,col) && r.Image(col,24)
      && (!exact_col || col==r.ImageAt(exact_col))
      && r.Read(col,0,signature) && signature==1
      && r.Read(col,12,type) && type==td
      && r.Read(col,20,self) && col==r.ImageAt(self);
}
bool DefinitionKey(Reader &r,const void *definition,std::string &key) {
  if(!Typed(r,definition,0x48BD150,0x5586B90)) return false;
  std::uint32_t magic=0; std::uint64_t size=0,capacity=0;
  const void *text=At(definition,0x18);
  if(!r.Read(definition,0x38,magic) || magic!=0x4744624FU
      || !r.Read(text,16,size) || !r.Read(text,24,capacity)
      || !size || size>512 || size>capacity || (capacity<16 && capacity!=15)) return false;
  if(capacity>=16 && (!r.Read(text,0,text)||!text)) return false;
  std::array<char,513> bytes{};
  if(!r.Bytes(text,bytes.data(),static_cast<std::size_t>(size)+1)
      || bytes[static_cast<std::size_t>(size)]!=0) return false;
  key.assign(bytes.data(),static_cast<std::size_t>(size)); return true;
}
bool FixedKey(std::string_view key) noexcept {
  for(auto action:{DecisionAction::adopt,DecisionAction::promote,DecisionAction::demote,DecisionAction::abandon})
    if(key==DecisionKey(action)) return true;
  return false;
}
struct Header {
  const void *data=nullptr,*allocator=nullptr;
  std::int32_t capacity=0,count=0;
};
bool Array(Reader &r,const void *p,std::size_t offset,Header &h,std::int32_t max=8192) {
  const auto *a=At(p,offset);
  return r.Read(a,0,h.data)&&r.Read(a,8,h.capacity)&&r.Read(a,12,h.count)
      &&r.Read(a,16,h.allocator)&&h.count>=0&&h.capacity>=h.count
      &&h.capacity<=max&&(h.count==0||h.data);
}
bool Callback(Reader &r,const void *button,const void *&block,Pass &p) {
  const void *vt=nullptr,*slot=nullptr;
  if(!r.Read(button,0,vt)||!r.Image(vt,14*8)||!r.Read(vt,13*8,slot)
      ||slot!=r.ImageAt(0x3AA0D20)) return Fail(p,"entry_parameter_button_slot13_differs");
  Header primary{},selected{};
  if(!Array(r,button,0x3F8,primary,256)) return Fail(p,"entry_parameter_primary_group_unreadable");
  if(primary.count) selected=primary;
  else if(!Array(r,button,0x338,selected,256)) return Fail(p,"entry_parameter_fallback_group_unreadable");
  if(selected.count!=2) return Fail(p,"entry_parameter_callback_group_differs");
  for(std::size_t i=0;i<2;++i) {
    const void *callback=nullptr,*cv=nullptr,*entry=nullptr,*receiver=nullptr,*final=nullptr;
    std::uint32_t kind=0;
    if(!r.Read(selected.data,i*0x48+0x40,callback)||!callback
        ||!r.Read(callback,0,cv)||!r.Image(cv,24)||!r.Read(cv,0x10,slot)
        ||slot!=r.ImageAt(0x3AA30E0)||!r.Read(callback,8,entry)||entry!=r.ImageAt(0x3A9F960)
        ||!r.Read(callback,0xF0,receiver)||receiver!=button
        ||!r.Read(callback,0x10+0x34,kind)||(kind!=3&&kind!=4)
        ||!r.Read(callback,0x10+0x38,final)
        ||final!=r.ImageAt(i?0x1031E60:0xA79540))
      return Fail(p,"entry_parameter_actual_callback_binding_differs");
    if(!i) block=At(callback,0x10);
  }
  return true;
}
bool SelfArgument(Reader &r,const void *block,std::uint32_t &type,Pass &p) {
  Header arguments{}; const void *indices=nullptr,*declarations=nullptr;
  std::int32_t index_count=0,declaration_count=0,index=-1;
  std::uint32_t runtime=absent,declared=absent,kind=0,required=absent,output_slot=0;
  std::uint8_t declaration_flag=0,receiver_flag=0;
  if(!Array(r,block,0,arguments)||arguments.count!=2
      ||!r.Read(block,0xB0,indices)||!indices||!r.Read(block,0xBC,index_count)
      ||index_count<2||index_count>8192||!r.Read(indices,4,index)||index<0
      ||!r.Read(block,0x98,declarations)||!declarations
      ||!r.Read(block,0xA4,declaration_count)||declaration_count<=index||declaration_count>8192
      ||!r.Read(r.b.decision_params_runtime_class_id,0,runtime)||runtime==absent
      ||!r.Read(declarations,std::size_t(index)*8,declared)||declared!=runtime
      ||!r.Read(declarations,std::size_t(index)*8+4,declaration_flag))
    return Fail(p,"entry_parameter_self_declaration_unavailable");
  const auto *arg=At(arguments.data,0x40);
  Header chain{}; const void *function=nullptr,*userdata=nullptr;
  if(!Array(r,arg,0,chain)||chain.count!=0
      ||!r.Read(arg,0x18,p.return_type)||!r.Read(arg,0x1C,kind)
      ||!r.Read(arg,0x20,function)||function!=r.ImageAt(0xCAB1C0)
      ||!r.Read(arg,0x28,userdata)||!r.Read(arg,0x30,required)||required!=runtime
      ||!r.Read(arg,0x34,receiver_flag)||!r.Read(arg,0x38,output_slot)||output_slot!=1)
    return Fail(p,"entry_parameter_self_argument_differs");
  if(kind!=2) return Fail(p,kind==1?"entry_parameter_kind1_receiver_unknown":"entry_parameter_argument_kind_unsupported");
  type=declared; return true;
}
struct Node {const void *widget=nullptr,*definition=nullptr;};
struct ContextRow {const void *value=nullptr,*provider=nullptr;std::int8_t mode=0;std::uint8_t final=0;};
bool FirstRow(Reader &r,const void *definition,std::uint32_t type,bool &found,ContextRow &row) {
  found=false; Header rows{};
  if(!Array(r,definition,0x90,rows)) return false;
  for(std::int32_t i=0;i<rows.count;++i) {
    const void *actual=At(rows.data,std::size_t(i)*0x50);std::uint32_t key=0;
    if(!r.Read(actual,0x48,key))return false;
    if(key!=type)continue;
    found=true;
    return r.Read(actual,0,row.value)&&r.Read(actual,0x38,row.provider)
        &&r.Read(actual,0x40,row.mode)&&r.Read(actual,0x4C,row.final);
  }
  return true;
}
bool Receiver(Reader &r,const void *button,std::uint32_t type,std::vector<Node> &chain,Pass &p) {
  const void *widget=button; bool initial=true,pending=false;
  for(std::size_t depth=0;widget&&depth<64;++depth) {
    if(std::any_of(chain.begin(),chain.end(),[&](const Node&n){return n.widget==widget;}))
      return Fail(p,"entry_parameter_context_inheritance_cycle");
    Node node{widget,nullptr};const void *next=nullptr;
    if(!r.Read(widget,0xE0,node.definition))return Fail(p,"entry_parameter_context_definition_unreadable");
    chain.push_back(node);
    if(initial) {
      std::uint8_t active=0;bool found=false;ContextRow row{};
      if(!node.definition||!r.Read(node.definition,0x115,active)||!active
          ||!FirstRow(r,node.definition,type,found,row)||!found)
        return Fail(p,"entry_parameter_initial_context_unavailable");
      if(row.mode<0||row.mode>=2)return Fail(p,"entry_parameter_context_provider_unknown");
      p.params=row.value;pending=row.final==0;initial=false;
    } else if(pending&&node.definition) {
      bool found=false;ContextRow row{};
      if(!FirstRow(r,node.definition,type,found,row))return Fail(p,"entry_parameter_ancestor_context_unreadable");
      if(found&&row.final) {
        if(row.mode<0||row.mode>=2)return Fail(p,"entry_parameter_context_provider_unknown");
        p.params=row.value;pending=false;
      }
    }
    if(node.definition&&(!r.Read(node.definition,0x108,next)))
      return Fail(p,"entry_parameter_context_override_unreadable");
    if(!next&&!r.Read(widget,0xE8,next))return Fail(p,"entry_parameter_context_parent_unreadable");
    widget=next;
  }
  if(widget)return Fail(p,"entry_parameter_context_chain_truncated");
  return p.params?true:Fail(p,"entry_parameter_self_receiver_null");
}
bool NativeLookup(const EntryParameterBindings &b,const void *map,const void **row,const void *const *key) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return b.cache_lookup(map,row,key)==row;
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER) {return false;}
#endif
}
bool Cache(Reader &r,const std::vector<Node> &chain,Pass &p) {
  const void *expected=r.ImageAt(0x54D7588);
  if(!Typed(r,expected,0x44DF830,0x56C73B0,0x4A922E8)
      ||!Typed(r,r.ImageAt(0x54D7570),0x44DF6E0,0x56C7530,0x4A92248))
    return Fail(p,"entry_parameter_cache_metadata_differs");
  std::size_t owners=0;
  for(const auto &node:chain) {
    const void *map=At(node.widget,0x1D8),*rows=nullptr;
    std::int32_t mask=0;std::uint8_t overflow=0;
    if(!r.Read(map,8,rows)||!r.Read(map,0x14,mask)||!r.Read(map,0x18,overflow))
      return Fail(p,"entry_parameter_cache_header_unreadable");
    if(!rows) {
      if(mask||overflow)return Fail(p,"entry_parameter_cache_missing_rows");
      continue;
    }
    const std::int64_t count=std::int64_t(mask)+1+overflow;
    if(mask<0||mask>8191||((std::uint32_t(mask)+1)&std::uint32_t(mask))||count<=0||count>8192)
      return Fail(p,"entry_parameter_cache_bounds_invalid");
    const void *end=At(rows,std::size_t(count)*0x30);std::uint8_t terminal=0;
    // Original producer 8794AD writes FF to the extra terminal row. It is
    // not an empty bucket: a probe reaching it must not enter CAE7A0.
    if(!r.Read(end,4,terminal)||terminal!=0xFF)return Fail(p,"entry_parameter_cache_end_invalid");
    std::size_t type_rows=0;
    for(std::int64_t i=0;i<count;++i) {
      const void *row=At(rows,std::size_t(i)*0x30),*type_key=nullptr;std::uint8_t distance=0;
      if(!r.Read(row,4,distance))return Fail(p,"entry_parameter_cache_row_unreadable");
      if(distance&&(!r.Read(row,8,type_key)))return Fail(p,"entry_parameter_cache_key_unreadable");
      if(distance&&type_key==expected&&++type_rows>1)return Fail(p,"entry_parameter_cache_type_ambiguous");
    }
    // Prevalidate every original lookup probe, then execute the original ABI.
    std::uint32_t hash=0x811C9DC5U;const auto raw=reinterpret_cast<std::uintptr_t>(expected);
    for(unsigned i=0;i<8;++i)hash=(hash^std::uint8_t(raw>>(i*8)))*0x1000193U;
    const void *probe=At(rows,std::size_t(hash&std::uint32_t(mask))*0x30),*predicted=end;
    std::uint16_t distance=1;
    for(;;) {
      const auto address=reinterpret_cast<std::uintptr_t>(probe),start=reinterpret_cast<std::uintptr_t>(rows);
      const auto finish=reinterpret_cast<std::uintptr_t>(end);std::uint8_t actual=0;const void *key=nullptr;
      if(address<start||address>=finish||(address-start)%0x30||distance>255
          ||!r.Read(probe,4,actual))return Fail(p,"entry_parameter_cache_probe_unavailable");
      if(actual<distance)break;
      if(!r.Read(probe,8,key))return Fail(p,"entry_parameter_cache_probe_key_unreadable");
      if(key==expected){predicted=probe;break;}
      probe=At(probe,0x30);++distance;
    }
    const void *row=nullptr;
    if(!NativeLookup(r.b,map,&row,&expected)||row!=predicted)
      return Fail(p,"entry_parameter_native_cache_lookup_changed");
    // Record the native return, not just the independently read map.
    const auto record=reinterpret_cast<std::uintptr_t>(row);
    const auto *bytes=reinterpret_cast<const unsigned char*>(&record);
    r.fingerprint.insert(r.fingerprint.end(),bytes,bytes+sizeof(record));
    if(row==end)continue;
    const void *metadata=nullptr,*params=nullptr;
    if(!r.Read(row,8,metadata)||metadata!=expected||!r.Read(row,0x10,params)||!params
        ||params!=p.params)return Fail(p,"entry_parameter_cache_self_pointer_differs");
    if(++owners!=1)return Fail(p,"entry_parameter_cache_owner_ambiguous");
    p.source_widget=node.widget;
  }
  return owners==1?true:Fail(p,"entry_parameter_owned_cache_not_found");
}
bool ParameterIdentity(Reader &r,std::uint32_t id,Pass &p) {
  if(!r.Read(p.params,0,p.definition)||!p.definition||!DefinitionKey(r,p.definition,p.key)||!FixedKey(p.key))
    return Fail(p,"entry_parameter_definition_identity_unavailable");
  Header named{};std::uint32_t token=0;std::size_t selected=0;
  if(!r.Read(r.b.selected_item_token,0,token)||!Array(r,p.params,0x30,named))
    return Fail(p,"entry_parameter_named_scope_dictionary_unavailable");
  for(std::int32_t i=0;i<named.count;++i) {
    const void *row=At(named.data,std::size_t(i)*0x18);std::uint32_t key=0;
    std::uint16_t kind=0,flags=0;std::uint64_t payload=0;
    // Ignore Scope16 padding +4..7, which the original does not initialize.
    if(!r.Read(row,0,key)||!r.Read(row,8,kind)||!r.Read(row,10,flags)||!r.Read(row,16,payload))
      return Fail(p,"entry_parameter_named_scope_row_unreadable");
    if(key==token) {
      if(++selected!=1||kind!=23||flags!=0||payload!=std::uint64_t(id))
        return Fail(p,"entry_parameter_selected_item_full_id_differs");
    }
  }
  if(selected!=1)return Fail(p,"entry_parameter_selected_item_missing");
  const void *storage=nullptr,*slots=nullptr,*site=nullptr;std::uint32_t count=0,actual=absent,magic=0;
  if(!r.Read(r.b.holy_site_storage,0,storage)||!storage||!r.Read(storage,0x20,slots)||!slots
      ||!r.Read(storage,0x2C,count)||count>0x1000000U||(id&0xFFFFFFU)>=count
      ||!r.Read(slots,std::size_t(id&0xFFFFFFU)*16+8,site)||!site
      ||!r.Read(site,0x10,actual)||actual!=id||!r.Read(site,0x14,magic)||magic!=0x486F5374U)
    return Fail(p,"entry_parameter_holy_site_storage_identity_differs");
  return true;
}
bool Capture(const EntryParameterBindings &b,const void *button,std::uint32_t id,Pass &p) {
  Reader r{b,{}};const void *block=nullptr;std::uint32_t declaration_type=0;std::vector<Node>chain;
  if(!Pins(r))return Fail(p,"entry_parameter_loaded_source_pins_changed");
  if(!Callback(r,button,block,p)||!SelfArgument(r,block,declaration_type,p)
      ||!Receiver(r,button,declaration_type,chain,p)||!Cache(r,chain,p)||!ParameterIdentity(r,id,p))return false;
  p.fingerprint=std::move(r.fingerprint);return true;
}
}
EntryParameterBindings BindHolySiteDecisionEntryParametersImage12004(std::uintptr_t base,std::string_view sha) noexcept {
  EntryParameterBindings b{};
  if(!base||base>(std::numeric_limits<std::uintptr_t>::max)()-image_size||sha!=ck3_12004::kExecutableSha256)return b;
  b.enabled=true;b.image_base=base;b.read_memory=&ProcessRead;
  b.cache_lookup=reinterpret_cast<CacheLookup>(base+0xCAE7A0);
  b.holy_site_storage=reinterpret_cast<void**>(base+0x5D1DE80);
  b.selected_item_token=reinterpret_cast<const std::uint32_t*>(base+0x5D4C2EC);
  b.decision_params_runtime_class_id=reinterpret_cast<const std::uint32_t*>(base+0x5D50198);
  return b;
}
bool ReadHolySiteDecisionEntryParameters12004(const EntryParameterBindings &b,const void *button,
    DecisionAction action,std::uint32_t id,EntryParameterSnapshot &out) noexcept {
  out={};
  try {
    if(!b.enabled||!b.image_base||b.image_base>(std::numeric_limits<std::uintptr_t>::max)()-image_size
        ||!b.read_memory||!b.cache_lookup||!b.holy_site_storage||!b.selected_item_token
        ||!b.decision_params_runtime_class_id||!button||id==absent||DecisionKey(action).empty()) {
      out.unavailable_reason="entry_parameter_bindings_or_request_unavailable";return false;
    }
    Pass first{},second{};
    if(!Capture(b,button,id,first)){out.unavailable_reason=first.reason;return false;}
    if(!Capture(b,button,id,second)){out.unavailable_reason=second.reason;return false;}
    if(first.fingerprint!=second.fingerprint||first.params!=second.params||first.definition!=second.definition
        ||first.source_widget!=second.source_widget||first.key!=second.key||first.return_type!=second.return_type) {
      out.unavailable_reason="entry_parameter_source_changed";return false;
    }
    out.params=first.params;out.definition=first.definition;out.source_widget=first.source_widget;
    out.decision_key=first.key;out.holy_site_id=id;out.self_return_type_raw=first.return_type;
    out.decision_key_verified=true;
    if(first.key!=DecisionKey(action)){out.unavailable_reason="entry_parameter_decision_key_differs";return false;}
    out.available=true;return true;
  }catch(...){out={};out.unavailable_reason="entry_parameter_reader_exception";return false;}
}
} // namespace xar::ck3_12004::religion::holy_site
