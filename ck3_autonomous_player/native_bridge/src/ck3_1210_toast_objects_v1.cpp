#include "xar_bridge/ck3_1210_toast_objects_v1.hpp"
#include <algorithm>
#include <bit>
#include <cstring>
#include <limits>
#include <unordered_set>

namespace xar::ck3_1210 {
namespace {
constexpr std::uintptr_t kIdentifierTable = 0x6B14640;
constexpr std::uintptr_t kToastVtable = 0x4B609C0;
constexpr std::uintptr_t kImageSize = 0x6FE4C00;
struct Read {
  const ToastObjectMemoryReaderV1 &reader;
  std::size_t consumed = 0;
  bool budget_exhausted=false;
  bool bytes(std::uintptr_t address, void *out, std::size_t count) noexcept {
    if(count>kToastObjectReadBudgetV1-consumed) {budget_exhausted=true;return false;}
    if (!reader.copy || !address || !out || !count ||
        count - 1 > (std::numeric_limits<std::uintptr_t>::max)() - address) return false;
    consumed += count;
    return reader.copy(reader.context, address, out, count);
  }
  template<class T> bool load(std::uintptr_t p, std::size_t offset, T &out) noexcept {
    return p && offset <= (std::numeric_limits<std::uintptr_t>::max)() - p &&
        bytes(p + offset, &out, sizeof(out));
  }
};
bool ScopeCopy(void *opaque,std::uintptr_t address,void *out,std::size_t count) noexcept {
  // The identity decoder's independent1KiB limit is inside the same4MiB
  // aggregate reader; no extra memory route bypasses the query's total budget.
  return static_cast<Read *>(opaque)->bytes(address,out,count);
}
bool ScopeIdentity(Read &reader,const ToastObjectBindingsV1 &b,const std::array<std::byte,16> &token,
    ToastScopeIdentityV1 &identity,std::string_view &reason) noexcept {
  if(!ReadToastScopeIdentityV1(b.scope_identities,token,{&reader,&ScopeCopy},identity)) {
    reason=identity.unavailable_reason;return false;
  }
  // Unknown tags are an explicit unavailable identity row, never a guessed
  // Story/Character or partial known-object success.
  return true;
}
ToastObjectScopeIdentityV1 PublicScope(std::string_view name,const ToastScopeIdentityV1 &identity) {
  ToastObjectScopeIdentityV1 out{};out.name.assign(name);out.kind=identity.kind;out.observed_tag=identity.observed_tag;
  out.identity_available=identity.status==ToastScopeIdentityStatusV1::available;
  if(out.identity_available) {
    if(identity.kind==ToastScopeKindV1::character)
      out.identity=std::to_string(std::bit_cast<std::int32_t>(identity.full_id));
    else out.identity=std::to_string(identity.full_id);
  }else out.unavailable_reason=identity.unavailable_reason;
  return out;
}
bool Mapped(std::uintptr_t base, std::uintptr_t address, std::size_t n) noexcept {
  return n <= kImageSize && address >= base && address-base <= kImageSize-n;
}
bool Utf8(const std::vector<char> &text) noexcept {
  for(std::size_t i=0;i+1<text.size();) {
    const auto c=static_cast<unsigned char>(text[i]);
    if(c<0x80) {if(!c)return false;++i;continue;}
    std::size_t extra=0;
    if(c>=0xC2 && c<=0xDF)extra=1;
    else if(c>=0xE0 && c<=0xEF)extra=2;
    else if(c>=0xF0 && c<=0xF4)extra=3;
    else return false;
    if(extra>=text.size()-1-i)return false;
    for(std::size_t j=1;j<=extra;++j) {
      const auto next=static_cast<unsigned char>(text[i+j]);
      if(next<0x80 || next>0xBF)return false;
      if(j==1 && ((c==0xE0 && next<0xA0) || (c==0xED && next>=0xA0) ||
          (c==0xF0 && next<0x90) || (c==0xF4 && next>=0x90)))return false;
    }
    i+=extra+1;
  }
  return true;
}
bool Text(Read &r, std::uintptr_t object, std::size_t offset,
    std::size_t maximum, std::string &out) {
  std::array<std::byte,0x20> header{}, after{};
  if (!r.load(object,offset,header)) return false;
  std::uint64_t size = 0, capacity = 0; std::uintptr_t data = object+offset;
  std::memcpy(&size,header.data()+0x10,8); std::memcpy(&capacity,header.data()+0x18,8);
  if (size > maximum || size > capacity || (capacity < 16 && capacity != 15)) return false;
  if (capacity >= 16) std::memcpy(&data,header.data(),8);
  std::vector<char> chars(static_cast<std::size_t>(size)+1);
  if (!r.bytes(data,chars.data(),chars.size()) || chars.back()!=0 ||
      !r.load(object,offset,after) || header!=after) return false;
  if(!Utf8(chars))return false;
  out.assign(chars.data(),static_cast<std::size_t>(size)); return true;
}
bool Graph(Read &r, const ToastObjectBindingsV1 &b, const IngameReadyGraphV1 &g) {
  std::uintptr_t value=0; std::uint8_t transition=0; std::uint64_t epoch=0;
  const auto root=reinterpret_cast<std::uintptr_t>(g.root);
  const auto app=reinterpret_cast<std::uintptr_t>(g.application);
  const auto gfx=reinterpret_cast<std::uintptr_t>(g.gfx);
  const auto handler=reinterpret_cast<std::uintptr_t>(g.handler);
  return root && app && gfx && handler && g.completed_frame_epoch &&
      r.load(b.module_base,kJominiStateSlotRva,value) && value==root &&
      r.load(root,0,value) && value==b.module_base+kIngameRootVtableRvaV1 &&
      r.load(root,0x18,value) && value==app && r.load(root,0x10,value) && value==gfx &&
      r.load(app,0,value) && value==b.module_base+kIngameApplicationVtableRvaV1 &&
      r.load(app,0x28,value) && value==root && r.load(app,0x78,value) && value==0 &&
      r.load(app,0x30,transition) && transition==0 &&
      r.load(app,kIngameCompletedFrameEpochOffsetV1,epoch) && epoch==g.completed_frame_epoch &&
      r.load(gfx,0,value) && value==b.module_base+kIngameGfxVtableRvaV1 &&
      r.load(gfx,0x20,value) && value==root && r.load(gfx,0x90,value) && value==app &&
      r.load(gfx,0x88,value) && value==handler &&
      r.load(handler,0,value) && value==b.module_base+kIngameHandlerVtableRvaV1 &&
      r.load(handler,0x40,value) && value==root;
}
struct NamesHeader {
  std::uintptr_t strings=0;
  std::int32_t count=0;
  std::uint8_t generation=0;
  std::uint32_t lock=0;
  bool operator==(const NamesHeader &) const = default;
};
bool Names(Read &r,std::uintptr_t base,NamesHeader &h) {
  const auto table=base+kIdentifierTable;
  return r.load(table,0,h.generation) && r.load(table,0x30,h.strings) &&
      r.load(table,0x3C,h.count) && r.load(table,0x48,h.lock) && h.lock==0 &&
      h.count>=0 && h.count<=0x100000 && (h.count==0 || h.strings);
}
bool ScopeNames(Read &r,const ToastObjectBindingsV1 &b,std::uintptr_t item,
    std::vector<ToastObjectNamedScopeV1> &out,std::string_view &reason) {
  const auto base=b.module_base;
  std::uintptr_t data=0;std::int32_t count=0,capacity=0;
  if(!r.load(item,0x38,data) || !r.load(item,0x40,capacity) || !r.load(item,0x44,count) ||
      count<0 || count>static_cast<std::int32_t>(kToastObjectMaximumNamedScopesV1) ||
      capacity<count || (count && !data))return false;
  if(!count)return true;
  NamesHeader first{},last{};if(!Names(r,base,first))return false;
  std::unordered_set<std::uint32_t> identifiers;
  for(std::int32_t i=0;i<count;++i) {
    std::array<std::byte,0x18> raw{};ToastObjectNamedScopeV1 scope{};
    if(!r.load(data,static_cast<std::size_t>(i)*0x18,raw))return false;
    std::memcpy(&scope.identifier,raw.data(),4);
    std::copy_n(raw.data()+8,16,scope.token.data());
    const auto index=scope.identifier&0xFFFFFFU;
    if((scope.identifier>>24)!=first.generation || index>=static_cast<std::uint32_t>(first.count) ||
        !identifiers.insert(scope.identifier).second ||
        !Text(r,first.strings,static_cast<std::size_t>(index)*0x20,192,scope.name) || scope.name.empty())return false;
    for(const unsigned char c:scope.name)if(c<0x21 || c>0x7E)return false;
    if(!ScopeIdentity(r,b,scope.token,scope.identity,reason))return false;
    out.push_back(std::move(scope));
  }
  return Names(r,base,last) && first==last;
}
bool ScriptScopes(Read &r,const ToastObjectBindingsV1 &b,std::uintptr_t item,std::vector<ToastObjectScriptScopeV1> &out,std::string_view &reason) {
  std::uintptr_t data=0;std::int32_t capacity=0,count=0;
  if(!r.load(item,0xF78,data) || !r.load(item,0xF80,capacity) || !r.load(item,0xF84,count) ||
      count<0 || count>static_cast<std::int32_t>(kToastObjectMaximumNamedScopesV1) ||
      capacity<count || (count && !data))return false;
  std::unordered_set<std::string> names;
  for(std::int32_t i=0;i<count;++i) {
    const auto at=data+static_cast<std::size_t>(i)*0x30;ToastObjectScriptScopeV1 scope{};
    if(at<data || !Text(r,at,0,192,scope.name) || scope.name.empty() ||
        !names.insert(scope.name).second || !r.load(at,0x20,scope.token))return false;
    for(const unsigned char c:scope.name)if(c<0x21 || c>0x7E)return false;
    if(!ScopeIdentity(r,b,scope.token,scope.identity,reason))return false;
    out.push_back(std::move(scope));
  }
  return true;
}
bool SameNamedSource(const ToastObjectCaptureV1 &capture) noexcept {
  for(const auto &gui:capture.saved_gui_scopes)for(const auto &script:capture.saved_script_scopes)
    if(gui.name==script.name && (gui.token!=script.token || gui.identity!=script.identity))return false;
  return true;
}
bool Widget(Read &r,const ToastObjectBindingsV1 &b,std::uintptr_t object,
    std::uintptr_t context,ToastObjectWidgetV1 &w) {
  w.object=object;
  return r.load(object,0,w.vtable) && Mapped(b.module_base,w.vtable,14*8) &&
      r.load(object,0xD8,w.context) && w.context==context &&
      r.load(object,0xE8,w.parent) && r.load(object,0xF0,w.children) &&
      r.load(object,0xFC,w.child_count) && w.child_count>=0 && w.child_count<=4096 &&
      (!w.child_count || w.children) && r.load(object,0xD0,w.flags) &&
      Text(r,object,0x1B8,192,w.name);
}
bool OwnsChild(Read &r,const ToastObjectWidgetV1 &w,std::uintptr_t child) {
  std::uint32_t matches=0;
  for(std::int32_t i=0;i<w.child_count;++i) {
    std::uintptr_t p=0;if(!r.load(w.children,static_cast<std::size_t>(i)*8,p))return false;
    if(p==child)++matches;
  }
  return matches==1;
}
bool Ui(Read &r,const ToastObjectBindingsV1 &b,ToastObjectCaptureV1 &out) {
  std::uintptr_t first=0,host=0,owner=0;
  if(!r.load(reinterpret_cast<std::uintptr_t>(out.graph.application),0x1B8,first) ||
      !r.load(first,0x58,out.context) || !r.load(out.context,0x3D8,host) ||
      !r.load(host,8,owner) || owner!=out.context || !r.load(owner,0xD0,out.gui_root) ||
      !r.load(out.handler,0x60,out.toast_widget) || !out.toast_widget)return false;
  ToastObjectWidgetV1 current{};
  if(!Widget(r,b,out.toast_widget,out.context,current) || current.name!="toast_container_widget")return false;
  bool visible=true;std::unordered_set<std::uintptr_t> seen;
  for(std::size_t depth=0;;++depth) {
    if(depth>=64 || !seen.insert(current.object).second)return false;
    visible=visible && (current.flags&0x18)==0;out.ancestry.push_back(current);
    if(current.object==out.gui_root)break;
    ToastObjectWidgetV1 parent{};
    if(!current.parent || !Widget(r,b,current.parent,out.context,parent) || !OwnsChild(r,parent,current.object))return false;
    current=std::move(parent);
  }
  struct Pending {std::uintptr_t object;std::uintptr_t parent;bool visible;std::size_t depth;};
  std::vector<Pending> pending{{out.toast_widget,out.ancestry[0].parent,visible,0}};
  seen.clear();std::size_t content_count=0;bool content_visible=false;
  for(std::size_t i=0;i<pending.size();++i) {
    const auto n=pending[i];ToastObjectWidgetV1 w{};
    if(n.depth>=64 || !seen.insert(n.object).second || !Widget(r,b,n.object,out.context,w) || w.parent!=n.parent)return false;
    const bool effective=n.visible && (w.flags&0x18)==0;
    if(w.name=="toast_content") {++content_count;content_visible=effective;}
    for(std::int32_t j=0;j<w.child_count;++j) {
      std::uintptr_t child=0;
      if(pending.size()>=kToastObjectMaximumWidgetsV1 || !r.load(w.children,static_cast<std::size_t>(j)*8,child) || !child)return false;
      pending.push_back({child,w.object,effective,n.depth+1});
    }
    out.subtree.push_back(std::move(w));
  }
  if(content_count!=1)return false;
  out.effective_visible=content_visible;return true;
}
bool Capture(Read &r,const ToastObjectBindingsV1 &b,const IngameReadyGraphV1 &g,
    ToastObjectCaptureV1 &out,std::string_view &reason) {
  out={};out.graph=g;
  if(!Graph(r,b,g)) {reason="toast_full_graph_changed";return false;}
  std::uintptr_t type=0,back=0;const auto interface_handler=reinterpret_cast<std::uintptr_t>(g.handler);
  if(!r.load(interface_handler,0x480,out.handler) || !out.handler ||
      !r.load(out.handler,0,type) || type!=b.module_base+kToastVtable ||
      !r.load(out.handler,0x98,back) || back!=reinterpret_cast<std::uintptr_t>(g.root) ||
      !r.load(out.handler,0xA0,back) || back!=interface_handler) {reason="toast_handler_unpublished_or_mismatched";return false;}
  if(!r.load(out.handler,0xC8,out.queue) || !r.load(out.handler,0xD0,out.queue_capacity) ||
      !r.load(out.handler,0xD4,out.queue_count) || out.queue_count<0 ||
      out.queue_count>static_cast<std::int32_t>(kToastObjectMaximumQueueV1) ||
      out.queue_capacity<out.queue_count || (out.queue_capacity && !out.queue)) {reason="toast_queue_header_invalid_or_bounded";return false;}
  if(out.queue_count) {
    out.current_item=out.queue;
    std::uintptr_t definition=0;std::uint32_t definition_marker=0;std::uint8_t presentation=0;
    if(!r.load(out.current_item,0,out.semantic_base) || !r.load(out.current_item,0,definition) ||
        !r.load(definition,0x38,definition_marker) || definition_marker!=0x4744624FU ||
        !r.load(out.current_item,0x10,presentation) || presentation!=2 ||
        !Text(r,out.current_item,0x11C8,8192,out.title) ||
        !Text(r,out.current_item,0x11E8,32768,out.description)) {reason="toast_message_or_scopes_unreadable";return false;}
    std::int32_t gui_count=0,script_count=0;
    if(!r.load(out.current_item,0x44,gui_count) || !r.load(out.current_item,0xF84,script_count) ||
        gui_count<0 || script_count<0 || gui_count>64 || script_count>64 || gui_count+script_count>64) {
      reason="toast_saved_scope_total_budget_exhausted_or_unreadable";return false;
    }
    if(!ScopeNames(r,b,out.current_item,out.saved_gui_scopes,reason) ||
        !ScriptScopes(r,b,out.current_item,out.saved_script_scopes,reason)) {
      if(reason.empty())reason="toast_saved_scope_source_unreadable";return false;
    }
    if(out.saved_gui_scopes.size()+out.saved_script_scopes.size()>kToastObjectMaximumNamedScopesV1) {
      reason="toast_saved_scope_total_budget_exhausted";return false;
    }
    if(!SameNamedSource(out)) {reason="toast_saved_scope_context_mismatch";return false;}
    if(!Ui(r,b,out)) {reason="toast_ui_source_unavailable_or_bounded";return false;}
  }
  if(!Graph(r,b,g)) {reason="toast_full_graph_changed";return false;}
  return true;
}
bool SameMessage(const ToastObjectCaptureV1 &a,const ToastObjectCaptureV1 &b) {
  return a.graph.root==b.graph.root && a.graph.application==b.graph.application &&
      a.graph.gfx==b.graph.gfx && a.graph.handler==b.graph.handler &&
      a.handler==b.handler && a.queue==b.queue && a.current_item==b.current_item &&
      a.context==b.context && a.gui_root==b.gui_root && a.toast_widget==b.toast_widget &&
      a.queue_capacity==b.queue_capacity && a.queue_count==b.queue_count &&
      a.semantic_base==b.semantic_base && a.title==b.title && a.description==b.description &&
      a.saved_gui_scopes==b.saved_gui_scopes && a.saved_script_scopes==b.saved_script_scopes &&
      a.ancestry==b.ancestry && a.subtree==b.subtree &&
      a.effective_visible==b.effective_visible;
}
} // namespace

bool ObservePublishedToastObjectV1(const ToastObjectBindingsV1 &b,const IngameReadyGraphV1 &g,
    const ToastObjectMemoryReaderV1 &reader,ToastObjectProviderV1 &provider,ToastObjectObservationV1 &out) noexcept {
  out={};
  const auto fail=[&](std::string_view why) noexcept {provider={};out={};out.unavailable_reason=why;return false;};
  try {
    if(!b.exact_build_admitted || !b.module_base ||
        b.module_base>(std::numeric_limits<std::uintptr_t>::max)()-kImageSize ||
        !reader.copy)return fail("toast_exact_binding_unavailable");
    if(!b.scope_identities.exact_build_admitted || b.scope_identities.module_base!=b.module_base)
      return fail("toast_exact_scope_binding_unavailable");
    Read r{reader};ToastObjectCaptureV1 first{},second{};std::string_view reason;
    if(!Capture(r,b,g,first,reason) || !Capture(r,b,g,second,reason))
      return fail(r.budget_exhausted?"toast_total_read_budget_exhausted":reason);
    if(first!=second)return fail("toast_capture_changed");
    out.completed_application_frame=g.completed_frame_epoch;out.queue_count=second.queue_count;
    out.title=second.title;out.description=second.description;
    for(const auto &scope:second.saved_gui_scopes)out.saved_gui_scopes.push_back(PublicScope(scope.name,scope.identity));
    for(const auto &scope:second.saved_script_scopes)out.saved_script_scopes.push_back(PublicScope(scope.name,scope.identity));
    if(!second.queue_count)out.stage=ToastObjectStageV1::empty;
    else if(!second.effective_visible)out.stage=ToastObjectStageV1::hidden;
    else if(provider.has_previous && SameMessage(provider.previous,second) &&
        g.completed_frame_epoch>provider.previous.graph.completed_frame_epoch)out.stage=ToastObjectStageV1::visible;
    else out.stage=ToastObjectStageV1::visible_pending_frame;
    // Canonical named identities do not grant recipient/news roles. These
    // remain false even for a visible object and a valid Story/Character ID.
    provider.has_previous=true;provider.previous=std::move(second);return true;
  }catch(...) {return fail("toast_capture_exception");}
}
} // namespace xar::ck3_1210
