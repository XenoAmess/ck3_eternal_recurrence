#include "xar_bridge/ck3_1210_gui_control_v1.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#include <windows.h>
#include <cstring>
#include <limits>
#include <algorithm>
#include <unordered_set>

namespace xar::ck3_1210 {
namespace {
#include "ck3_1210_gui_pins_v1.inc"
constexpr std::size_t kImageSize=0x6FE4C00;
constexpr std::uintptr_t kButtonInputRva=0x406D780;
constexpr std::size_t kMaximumGlobalWidgets=32768,kMaximumChildren=4096,kMaximumDepth=64;
bool Bytes(std::uintptr_t address,void *data,std::size_t size) noexcept {
  SIZE_T got=0;
  return address && size && address<=(std::numeric_limits<std::uintptr_t>::max)()-size &&
      ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void *>(address),data,size,&got) && got==size;
}
template<class T> bool Load(std::uintptr_t p,std::size_t offset,T &out) noexcept {
  return p && offset<=(std::numeric_limits<std::uintptr_t>::max)()-p && Bytes(p+offset,&out,sizeof(out));
}
bool Image(const GuiControlBindingsV1 &b,std::uintptr_t address,std::size_t size) {
  return address>=b.module_base && size<=kImageSize && address-b.module_base<=kImageSize-size;
}
template<std::size_t N> bool Pin(const GuiControlBindingsV1 &b,std::uintptr_t rva,const std::array<unsigned char,N> &expected) {
  std::array<unsigned char,N> actual{};return Load(b.module_base,rva,actual) && actual==expected;
}
bool Pins(const GuiControlBindingsV1 &b) {
  return b.exact_build_admitted && Pin(b,kGuiFindTopRvaV1,kGuiFindTopPinV1) &&
      Pin(b,kGuiShortcutRvaV1,kGuiShortcutPinV1) && Pin(b,kGuiButtonInputRvaV1,kGuiButtonInputPinV1) &&
      Pin(b,kGuiCallbackGroupRvaV1,kGuiCallbackGroupPinV1) && Pin(b,kGuiContextChainRvaV1,kGuiContextChainPinV1) &&
      Pin(b,kGuiHostBackrefRvaV1,kGuiHostBackrefPinV1) && Pin(b,kGuiHostStoreRvaV1,kGuiHostStorePinV1) &&
      Pin(b,kGuiShortcutStoreRvaV1,kGuiShortcutStorePinV1) &&
      Pin(b,kGuiCallbackCtorRvaV1,kGuiCallbackCtorPinV1) && Pin(b,kGuiCallbackThunkRvaV1,kGuiCallbackThunkPinV1) &&
      Pin(b,kGuiExpressionCopyRvaV1,kGuiExpressionCopyPinV1) && Pin(b,kGuiChainCopyRvaV1,kGuiChainCopyPinV1);
}
std::uint64_t Wall() noexcept {
  FILETIME f{};GetSystemTimeAsFileTime(&f);
  return (((std::uint64_t{f.dwHighDateTime}<<32)|f.dwLowDateTime)-116444736000000000ULL)/10000;
}
bool Unexpired(const GuiControlContextV1 &c) {
  return c.monotonic_deadline_ms && Wall()<c.request.deadline_unix_ms && GetTickCount64()<c.monotonic_deadline_ms;
}
bool Owned(GuiControlContextV1 &c,const ck3_11906::MainThreadExecutionStampV1 &s) {
  if(!c.game || !c.game->enabled() || !game::IsCk3_1210Descriptor(c.game->descriptor()) ||
      !c.game->supports(kGuiControlQueryCapabilityV1) ||
      (c.request.activate && !c.game->supports(kGuiControlActivateCapabilityV1)) ||
      !c.native_full_adapter || !c.native_full_adapter->supports_snapshot() ||
      !game::IsCk3_1210Descriptor(c.native_full_adapter->descriptor()) ||
      !c.expected_full_snapshot || !c.mailbox || !c.bindings.core.enabled || !c.provider ||
      !c.ticket.sequence || !c.connection_generation || !s.pump_epoch || !s.thread_id ||
      GetCurrentThreadId()!=s.thread_id || !s.paused || s.tls_initialized!=1 ||
      s.tls_main_thread_marker!=1 || !s.tls_context || !s.game_state || !s.jomini_state)return false;
  const auto &m=*c.mailbox;std::uintptr_t gs=0,js=0;
  if(!Load(reinterpret_cast<std::uintptr_t>(c.bindings.core.game_state_slot),0,gs) ||
      !Load(reinterpret_cast<std::uintptr_t>(c.bindings.core.jomini_state_slot),0,js))return false;
  return !m.offline_fixture && m.state.load(std::memory_order_acquire)==ck3_11906::MainThreadQueryMailboxStateV1::executing &&
      !m.stop_requested.load(std::memory_order_acquire) && !m.failure_flags.load(std::memory_order_acquire) &&
      !m.proof_reset_requested.load(std::memory_order_acquire) &&
      m.pump_epochs.load(std::memory_order_acquire)==s.pump_epoch &&
      m.published_sequence.load(std::memory_order_acquire)==c.ticket.sequence &&
      m.owner_thread_id.load(std::memory_order_acquire)==s.thread_id &&
      m.executor.load(std::memory_order_acquire)==&ExecuteGuiControlMailboxV1 && m.executor_context==&c &&
      m.paused_owner_verified_pump_epochs.load(std::memory_order_acquire)>=ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
      m.owner_verified_pump_epochs.load(std::memory_order_acquire)>=ck3_11906::kMainThreadQueryMinimumOwnerVerifiedPumpEpochs &&
      gs==s.game_state && js==s.jomini_state;
}
struct Native {GuiControlContextV1 &c;const ck3_11906::MainThreadExecutionStampV1 &stamp;};
bool Current(Native &n,std::string &reason) {
  if(!Unexpired(n.c)) {reason="request_expired";return false;}
  game::Snapshot fresh{};
  if(!Owned(n.c,n.stamp) || !n.c.native_full_adapter->read_snapshot(fresh) ||
      fresh!=*n.c.expected_full_snapshot || !fresh.paused || fresh.date_raw!=n.stamp.date_raw ||
      !fresh.map_ready || !fresh.has_played_character || !fresh.played_character_alive || fresh.has_active_event) {
    reason="stale_full_snapshot";return false;
  }
  return true;
}
bool Name(std::uintptr_t p,std::string &out) {
  std::uint64_t size=0,capacity=0;std::uintptr_t text=p+0x1B8;
  if(!Load(p,0x1C8,size) || !Load(p,0x1D0,capacity) || size>192 || size>capacity ||
      (capacity<16 && capacity!=15))return false;
  if(capacity>=16 && !Load(p,0x1B8,text))return false;
  std::array<char,193> bytes{};
  if(!Bytes(text,bytes.data(),static_cast<std::size_t>(size)+1) || bytes[static_cast<std::size_t>(size)]!=0)return false;
  for(std::size_t i=0;i<size;++i)if(static_cast<unsigned char>(bytes[i])<0x20)return false;
  out.assign(bytes.data(),static_cast<std::size_t>(size));return true;
}
struct Node {
  std::uintptr_t p=0,parent=0;std::size_t depth=0;std::string path;
  bool visible=true,enabled=true;
};
bool TreeNode(const GuiControlBindingsV1 &b,const Node &n,std::uintptr_t context,GuiControlIdentityV1 &w) {
  w={};w.widget=n.p;std::uintptr_t vt=0;
  if(!Load(n.p,0,vt) || !Image(b,vt,14*8) || !Load(n.p,0xD8,w.context) || w.context!=context ||
      !Load(n.p,0xE8,w.parent) || (n.parent && n.parent!=w.parent) ||
      !Load(n.p,0xF0,w.children) || !Load(n.p,0xFC,w.child_count) ||
      w.child_count<0 || w.child_count>static_cast<std::int32_t>(kMaximumChildren) || (w.child_count && !w.children) ||
      !Load(n.p,0xD0,w.flags) || !Name(n.p,w.row.runtime_name))return false;
  w.row.child_path=n.path;w.row.vtable_rva=static_cast<std::uint32_t>(vt-b.module_base);
  w.row.effective_visible=n.visible && (w.flags&0x18)==0;w.row.enabled=n.enabled && (w.flags&0x06)==0;
  return true;
}
bool Children(const Node &n,const GuiControlIdentityV1 &w,std::vector<Node> &nodes,
    std::unordered_set<std::uintptr_t> &seen,std::size_t maximum) {
  if(w.child_count && (n.depth>=kMaximumDepth || nodes.size()+static_cast<std::size_t>(w.child_count)>maximum))return false;
  for(std::int32_t i=0;i<w.child_count;++i) {
    std::uintptr_t child=0;if(!Load(w.children,static_cast<std::size_t>(i)*8,child))return false;if(!child)continue;
    if(!seen.insert(child).second)return false;
    std::string path=n.path;if(!path.empty())path+='/';path+=std::to_string(i);
    nodes.push_back({child,n.p,n.depth+1,std::move(path),w.row.effective_visible,w.row.enabled});
  }return true;
}
bool SourceVector(std::uintptr_t object,std::size_t offset,std::size_t stride,
    std::vector<std::byte> &out,bool nested_chain=false) {
  std::uintptr_t data=0;std::int32_t capacity=0,count=0;
  if(!Load(object,offset,data) || !Load(object,offset+8,capacity) || !Load(object,offset+12,count) ||
      count<0 || count>64 || capacity<count || (count && !data))return false;
  const auto start=out.size(),size=static_cast<std::size_t>(count)*stride;
  out.resize(start+size);if(size && !Bytes(data,out.data()+start,size))return false;
  if(nested_chain)for(std::int32_t i=0;i<count;++i)
    if(!SourceVector(data,static_cast<std::size_t>(i)*stride,0x18,out))return false;
  return true;
}
bool CallbackGroup(const GuiControlBindingsV1 &b,std::uintptr_t widget,std::size_t group,
    std::vector<GuiControlCallbackV1> &out,bool &proven) {
  std::int32_t count=0,capacity=0;std::uintptr_t data=0;
  if(!Load(widget,group,data) || !Load(widget,group+8,capacity) || !Load(widget,group+12,count) ||
      count<0 || count>64 || capacity<count || (count && !data))return false;
  for(std::int32_t i=0;i<count;++i) {
    GuiControlCallbackV1 cb{};
    if(!Bytes(data+static_cast<std::size_t>(i)*0x48,cb.binding.data(),cb.binding.size()))return false;
    std::memcpy(&cb.object,cb.binding.data()+0x40,sizeof(cb.object));
    if(!cb.object || !Bytes(cb.object,cb.object_header.data(),cb.object_header.size()))return false;
    std::memcpy(&cb.vtable,cb.object_header.data(),sizeof(cb.vtable));
    if(!Image(b,cb.vtable,24) || !Load(cb.vtable,16,cb.invoke) || !Image(b,cb.invoke,1))return false;
    // The ordinary expression callback constructor 406F680 allocates F8, copies
    // its expression at +10, and binds the native receiver at +F0. The current
    // thunk is 406FC40 (different code from 1.20). Snapshot the whole source and
    // all bounded operand vectors, including each parameter's scope chain.
    // Other callback classes remain observable but cannot grant activation.
    if(cb.vtable==b.module_base+0x50BF430 && cb.invoke==b.module_base+0x406FC40) {
      cb.native_source.resize(0xF8);
      if(!Bytes(cb.object,cb.native_source.data(),0xF8) ||
          !SourceVector(cb.object,0x10,0x40,cb.native_source,true) ||
          !SourceVector(cb.object,0x28,0x18,cb.native_source) ||
          !SourceVector(cb.object,0x90,0x30,cb.native_source) ||
          !SourceVector(cb.object,0xA8,8,cb.native_source) ||
          !SourceVector(cb.object,0xC0,4,cb.native_source))return false;
    } else proven=false;
    out.push_back(cb);
  }return true;
}
bool StrictDescendant(const std::vector<Node> &nodes,std::uintptr_t root,std::uintptr_t target) {
  if(root==target)return false;
  for(std::size_t depth=0;depth<kMaximumDepth && target;++depth) {
    std::uintptr_t parent=0;if(!Load(target,0xE8,parent))return false;
    if(parent==root)return true;target=parent;
    if(std::none_of(nodes.begin(),nodes.end(),[target](const Node &n){return n.p==target;}))return false;
  }return false;
}
bool Capture(void *p,std::string_view root_name,GuiControlCaptureV1 &out,std::string &reason) noexcept {
  try {
    auto &n=*static_cast<Native *>(p);out={};const auto &b=n.c.bindings;
    const auto fail=[&](const char *why){reason=why;return false;};
    if(!Current(n,reason))return false;
    out.played_character_id=n.c.expected_full_snapshot->played_character_id;out.date_raw=n.c.expected_full_snapshot->date_raw;
    out.native_revision=n.c.request.native_revision;out.connection_generation=n.c.connection_generation;out.root_name.assign(root_name);
    std::uintptr_t vtable=0,first=0,host=0,back=0;
    if(!Load(reinterpret_cast<std::uintptr_t>(b.core.jomini_state_slot),0,out.logical_owner) ||
        out.logical_owner!=n.stamp.jomini_state || !Load(out.logical_owner,0x18,out.application) ||
        !Load(out.application,0,vtable) || vtable!=b.module_base+0x4AFA620 ||
        !Load(out.application,0x1B8,first) || !Load(first,0x58,out.context) ||
        !Load(out.context,0x3D8,host) || !Load(host,8,out.gui_owner) || out.gui_owner!=out.context ||
        !Load(out.gui_owner,0xD0,out.global_root) || !out.global_root ||
        !Load(out.context,0x3E8,out.shortcut_manager) || !Load(out.shortcut_manager,0,back) || back!=out.context)
      return fail("gui_current_owner_chain_unavailable");
    std::int32_t modal_count=0,modal_capacity=0;std::uintptr_t modals=0;
    if(!Load(out.context,0x298,modals) || !Load(out.context,0x2A0,modal_capacity) ||
        !Load(out.context,0x2A4,modal_count) || modal_count<0 || modal_count>64 || modal_capacity<modal_count ||
        (modal_count && !modals))return fail("gui_modal_vector_unavailable");
    for(std::int32_t i=0;i<modal_count;++i) {
      std::uintptr_t modal=0;std::uint8_t flags=0;
      if(!Load(modals,static_cast<std::size_t>(i)*8,modal) || !modal || !Load(modal,0xD0,flags))return fail("gui_modal_receiver_unavailable");
      out.modal_receivers.push_back(modal);out.modal_flags.push_back(flags);
    }
    // Read-only bounded owner tree search also finds registered scripted widgets
    // which the engine's direct top-level lookup omits. No focus/restore/input.
    std::vector<Node> global{{out.global_root,0,0,{},true,true}};
    std::unordered_set<std::uintptr_t> global_seen{out.global_root};
    Node selected{};std::size_t matches=0;
    for(std::size_t i=0;i<global.size();++i) {
      const auto node=global[i];GuiControlIdentityV1 row{};
      if(!TreeNode(b,node,out.context,row))return fail("gui_global_tree_invalid");
      if(row.row.runtime_name==root_name) {selected=node;out.root=node.p;++matches;}
      if(!Children(node,row,global,global_seen,kMaximumGlobalWidgets))return fail("gui_global_tree_budget_exhausted");
    }
    if(matches!=1)return fail(matches?"gui_root_ambiguous":"gui_root_not_materialized");
    selected.path.clear();std::vector<Node> nodes{selected};std::unordered_set<std::uintptr_t> seen{selected.p};
    bool any_visible_modal=false;
    for(const auto flag:out.modal_flags)if((flag&8)==0)any_visible_modal=true;
    const auto modal_top=out.modal_receivers.empty()?0:out.modal_receivers.back();
    for(std::size_t i=0;i<nodes.size();++i) {
      const auto node=nodes[i];GuiControlIdentityV1 w{};
      if(!TreeNode(b,node,out.context,w))return fail("gui_root_subtree_invalid");
      w.row.widget_id=i+1;std::uintptr_t vt=0,slot=0;
      if(!Load(w.widget,0,vt) || !Load(vt,13*8,slot))return fail("gui_widget_vtable_unavailable");
      if(slot==b.module_base+kButtonInputRva) {
        bool callback_source_proven=true;
        // Pin both groups because the actual mode-0 dispatcher chooses primary
        // or fallback internally. Binding records include the engine's native
        // datacontext, actor/row receiver and callback object witnesses.
        if(!CallbackGroup(b,w.widget,0x4B8,w.callbacks,callback_source_proven) ||
            !CallbackGroup(b,w.widget,0x3F8,w.callbacks,callback_source_proven))
          return fail("gui_callback_binding_unavailable");
        const bool modal_admitted=!any_visible_modal || StrictDescendant(global,modal_top,w.widget);
        w.row.clickable=w.row.effective_visible && w.row.enabled && !w.callbacks.empty() &&
            modal_admitted && callback_source_proven;
      }
      if(!Children(node,w,nodes,seen,kGuiControlMaximumRowsV1))return fail("gui_root_subtree_budget_exhausted");
      out.widgets.push_back(std::move(w));
    }
    if(!Current(n,reason))return false;out.complete=true;reason.clear();return true;
  }catch(...) {reason="gui_capture_exception";return false;}
}
bool Dispatch(void *p,const GuiControlCaptureV1 &capture,const GuiControlIdentityV1 &target,
    bool &handled,bool &attempted) noexcept {
  auto &n=*static_cast<Native *>(p);handled=false;attempted=false;
  try {
  std::string reason;
  // Revalidate the full source immediately before the first possible UI effect.
  if(!Current(n,reason) || !Pins(n.c.bindings) || !target.row.clickable ||
      capture.connection_generation!=n.c.connection_generation)return false;
  alignas(void *) std::array<std::byte,0x20> text{};const std::uint64_t capacity=15;
  std::memcpy(text.data()+0x18,&capacity,8);alignas(void *) std::array<std::byte,0x50> pimpl{};
  std::memcpy(pimpl.data()+0x48,&target.widget,8);
  using Activate=bool (*)(void *,std::int32_t,void *,void *);
  const auto function=reinterpret_cast<Activate>(n.c.bindings.module_base+kGuiShortcutRvaV1);
  attempted=true;n.c.result.effect_attempted=true;
  handled=function(reinterpret_cast<void *>(capture.shortcut_manager),0,text.data(),pimpl.data());
  return true;
  }catch(...) {return false;}
}
bool Execute(GuiControlContextV1 &c,const ck3_11906::MainThreadExecutionStampV1 &s) {
  c.result={};
  if(!Owned(c,s)) {c.result.unavailable_reason="gui_owner_unavailable";return true;}
  c.result.application_main_observed=true;
  Native native{c,s};std::string reason;
  if(!Current(native,reason)) {
    c.result.status=reason=="request_expired"?GuiControlStatusV1::expired:GuiControlStatusV1::stale_full_snapshot;
    c.result.unavailable_reason=reason;return true;
  }
  c.result.full_snapshot_before_verified=true;
  if(!Pins(c.bindings)) {c.result.unavailable_reason="gui_source_abi_pins_unavailable";return true;}
  GuiControlResultV1 result;
  const GuiControlBackendV1 backend{&native,&Capture,&Dispatch};
  ApplyGuiControlV1(*c.provider,c.request,backend,result);
  const bool attempted=c.result.effect_attempted;c.result=std::move(result);
  c.result.effect_attempted=c.result.effect_attempted || attempted;
  c.result.application_main_observed=true;c.result.full_snapshot_before_verified=true;c.result.source_abi_pins_verified=true;
  return true;
}
bool ExecuteCpp(GuiControlContextV1 &c,const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  try {return Execute(c,s);}catch(...) {
    if(c.provider)c.provider->valid=false;
    c.result.status=c.result.effect_attempted?GuiControlStatusV1::indeterminate:GuiControlStatusV1::unavailable;
    return true;
  }
}
} // namespace
GuiControlBindingsV1 BindGuiControlImageV1(std::uintptr_t base,std::string_view hash) noexcept {
  GuiControlBindingsV1 b{};b.core=BindCoreImage(base,hash);
  if(!b.core.enabled || !base || base>(std::numeric_limits<std::uintptr_t>::max)()-kImageSize)return {};
  b.module_base=base;b.exact_build_admitted=true;return b;
}
void ArmGuiControlDeadlineV1(GuiControlContextV1 &c) noexcept {
  c.monotonic_deadline_ms=0;const auto now=Wall();if(c.request.deadline_unix_ms<=now)return;
  c.monotonic_deadline_ms=GetTickCount64()+(std::min)(c.request.deadline_unix_ms-now,std::uint64_t{8000});
}
bool ExecuteGuiControlMailboxV1(void *p,const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  if(!p)return false;auto &c=*static_cast<GuiControlContextV1 *>(p);
#if defined(_MSC_VER)
  __try {return ExecuteCpp(c,s);}
  __except(EXCEPTION_EXECUTE_HANDLER) {
    if(c.provider)c.provider->valid=false;
    c.result.status=c.result.effect_attempted?GuiControlStatusV1::indeterminate:GuiControlStatusV1::unavailable;
    c.result.unavailable_reason="native_gui_exception_no_retry";return true;
  }
#else
  return ExecuteCpp(c,s);
#endif
}
} // namespace xar::ck3_1210
