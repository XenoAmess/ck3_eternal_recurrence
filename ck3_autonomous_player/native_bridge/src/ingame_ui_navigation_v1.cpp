#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include "xar_bridge/protocol.hpp"
#include "xar_bridge/title_map_navigation_v1_camera.hpp"
#include <windows.h>
#include <bcrypt.h>
#pragma comment(lib,"bcrypt.lib")
#include <array>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <vector>
#include <limits>
#include <sstream>

namespace xar::ck3_11906 {
namespace {
constexpr std::uintptr_t kCharacterStorage = 0x570C130;
constexpr std::uintptr_t kUnitStorage = 0x570CC80;
constexpr std::uintptr_t kArmyStorage = 0x570C730;
constexpr std::uintptr_t kCombatStorage = 0x570C758;
constexpr std::array<std::uint32_t,4> kViewTypes{8,6,0x1A,0x55};
constexpr std::array<std::uintptr_t,4> kTypeDescriptors{0x52159F0,0x52670E0,0x5277158,0x5262670};
constexpr std::uintptr_t kMilitaryTypeDescriptor = 0x5260210;
constexpr std::uintptr_t kImageSize = 0x5C2D000;
using CharacterClick = void (__fastcall *)(std::uint32_t);
using SelectUnit = void (__fastcall *)(void *,std::uint32_t,bool);
using OpenView = void (__fastcall *)(void *,std::uint32_t,bool);
using OpenViewData = void (__fastcall *)(void *,std::uint32_t,const void *);
using AnyType = void * (__fastcall *)();
using SetHoveredWidget = void (__fastcall *)(void *,void *);
constexpr std::uintptr_t kSetHoveredWidgetRva = 0x36CBAC0;
constexpr std::uintptr_t kGuiTextWidgetTypeDescriptor = 0x5020010;
constexpr std::uintptr_t kGuiWindowTypeDescriptor = 0x511B880;
constexpr std::uintptr_t kGuiRectRva=0x369C450;
constexpr std::uintptr_t kGuiAbsoluteToLocalRva=0x369C2A0;
constexpr std::uintptr_t kGuiAnchoredPositionRva=0x369C110;
constexpr std::uintptr_t kGuiSetPositionRva=0x369C030;
constexpr std::string_view kStockCombatGuiSha256="7FEE98B7341E21607ED3BB9089C51EF890D229DB6C16865C88133C3BA3579236";
using GuiRectGetter=UiRectV1 * (__fastcall *)(void *,UiRectV1 *,const UiRectV1 *);
using GuiPointTransform=UiFloat2V1 * (__fastcall *)(void *,UiFloat2V1 *,const UiFloat2V1 *);
using GuiPositionGetter=UiFloat2V1 * (__fastcall *)(void *,UiFloat2V1 *);
using GuiPositionSetter=void (__fastcall *)(void *,const UiFloat2V1 *);
struct IdAnyV1 { void *type = nullptr; std::array<std::uint8_t,32> data{}; };
static_assert(sizeof(IdAnyV1)==40);

bool Read(const void *address,void *output,std::size_t size) noexcept {
  SIZE_T got=0;
  return address && output && size && ReadProcessMemory(GetCurrentProcess(),address,output,size,&got) && got==size;
}
template<class T> bool Value(const void *object,std::size_t offset,T &value) noexcept {
  if (!object) return false;
  return Read(reinterpret_cast<const std::uint8_t *>(object)+offset,&value,sizeof(value));
}
template<class T> bool Slot(std::uintptr_t address,T &value) noexcept {return Read(reinterpret_cast<void *>(address),&value,sizeof(value));}
// Original ShortcutManagerActivate 36E1C70..36E1CA6 scans receiver+D0 bit08
// rather than treating nonzero registration count as an active modal. Global
// typed navigation is conservatively stricter: any effective-visible receiver
// refuses navigation, with no descendant allowance or exception by name.
bool ReadModalNavigationAdmission(const void *context,
                                 IngameUiModalAdmissionV1 &out) noexcept {
  out={};out.attempted=true;
  void **receivers=nullptr;
  if(!Value(context,kZhongguoGuiModalReceiversOffset,receivers) ||
     !Value(context,kZhongguoGuiModalReceiverCountOffset,out.receiver_count)) {
    out.unavailable_reason="modal_receiver_header_unreadable";return false;
  }
  out.header_read=true;out.vector_address=reinterpret_cast<std::uintptr_t>(receivers);
  if(out.receiver_count<0 || out.receiver_count>256) {
    out.unavailable_reason="modal_receiver_count_out_of_bounds";return false;
  }
  if(out.receiver_count && !receivers) {
    out.unavailable_reason="modal_receiver_vector_missing";return false;
  }
  for(std::int32_t index=0;index<out.receiver_count;++index) {
    void *receiver=nullptr;std::uint8_t flags=0;
    if(!Value(receivers,static_cast<std::size_t>(index)*sizeof(void *),receiver) || !receiver) {
      out.unavailable_reason="modal_receiver_entry_unreadable_or_null";return false;
    }
    if(!Value(receiver,kZhongguoWidgetHiddenFlagsOffset,flags)) {
      out.unavailable_reason="modal_receiver_flags_unreadable";return false;
    }
    out.receivers.push_back({reinterpret_cast<std::uintptr_t>(receiver),flags});
    if((flags & kZhongguoWidgetEffectiveHiddenMask)==0)++out.effective_visible_count;
  }
  void **later_receivers=nullptr;std::int32_t later_count=0;
  if(!Value(context,kZhongguoGuiModalReceiversOffset,later_receivers) ||
     !Value(context,kZhongguoGuiModalReceiverCountOffset,later_count) ||
     later_receivers!=receivers || later_count!=out.receiver_count) {
    out.unavailable_reason="modal_receiver_header_changed_during_read";return false;
  }
  out.receivers_verified=true;
  if(out.effective_visible_count) {
    out.unavailable_reason="effective_visible_modal_receiver_blocks_navigation";return false;
  }
  return true;
}
bool Object(std::uintptr_t base,std::uintptr_t storage_rva,std::uint32_t id,std::size_t id_offset,void *&object) noexcept {
  object=nullptr;
  if (id==(std::numeric_limits<std::uint32_t>::max)()) return false;
  void *storage=nullptr;void *slots=nullptr;std::uint32_t count=0;std::uint32_t actual=0;
  const std::uint32_t index=id&0xFFFFFF;
  return Slot(base+storage_rva,storage) && Value(storage,0x20,slots) && Value(storage,0x2C,count) &&
      count<=0x1000000 && index<count && Value(slots,std::size_t(index)*16+8,object) && object &&
      Value(object,id_offset,actual) && actual==id;
}
// MSVC x64 complete-object RTTI: COL signature 1, image-relative descriptor.
bool TypedObject(std::uintptr_t base,void *object,std::uintptr_t descriptor) noexcept {
  void *vt=nullptr;void *col=nullptr;std::uint32_t signature=0,type=0,self=0;
  if (!Value(object,0,vt))return false;
  auto v=reinterpret_cast<std::uintptr_t>(vt);
  if(v<base+8 || v>=base+kImageSize || !Slot(v-8,col))return false;
  auto c=reinterpret_cast<std::uintptr_t>(col);
  return c>=base && c+24<=base+kImageSize && Value(col,0,signature) && signature==1 &&
      Value(col,12,type) && type==descriptor && Value(col,20,self) && base+self==c;
}
bool InvokeCast(NativeRuntimeDynamicCastV1 fn,void *object,const void *source,const void *target,void *&out) noexcept {
#if defined(_MSC_VER)
  __try {out=fn(object,0,source,target,0);return true;} __except(EXCEPTION_EXECUTE_HANDLER) {out=nullptr;return false;}
#else
  out=fn(object,0,source,target,0);return true;
#endif
}
bool ResolveHandler(std::uintptr_t base,void *&handler) noexcept {
  handler=nullptr;void *root=nullptr;void *idler=nullptr;void *cast=nullptr;void *vt=nullptr;std::int32_t mode=1;
  return Slot(base+kTitleMapIngameIdlerRootSlotRva,root) && Value(root,0x10,idler) && idler &&
      InvokeCast(reinterpret_cast<NativeRuntimeDynamicCastV1>(base+kTitleMapRuntimeDynamicCastRva),idler,
                 reinterpret_cast<void *>(base+kTitleMapIdlerBaseTypeDescriptorRva),
                 reinterpret_cast<void *>(base+kTitleMapIngameIdlerTypeDescriptorRva),cast) &&
      Value(cast,0x88,handler) && handler && Value(handler,0,vt) &&
      reinterpret_cast<std::uintptr_t>(vt)==base+kTitleMapHandlerVtableRva &&
      Value(handler,0x60,mode) && mode!=1;
}
bool InvokeCharacter(std::uintptr_t base,std::uint32_t id) noexcept {
#if defined(_MSC_VER)
  __try {reinterpret_cast<CharacterClick>(base+kUiDefaultOnCharacterClickRvaV1)(id);return true;} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  reinterpret_cast<CharacterClick>(base+kUiDefaultOnCharacterClickRvaV1)(id);return true;
#endif
}
bool InvokeUnit(std::uintptr_t base,void *handler,std::uint32_t id) noexcept {
#if defined(_MSC_VER)
  __try {reinterpret_cast<SelectUnit>(base+kUiSelectUnitRvaV1)(handler,id,true);return true;} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  reinterpret_cast<SelectUnit>(base+kUiSelectUnitRvaV1)(handler,id,true);return true;
#endif
}
bool InvokeKnights(std::uintptr_t base,void *handler) noexcept {
#if defined(_MSC_VER)
  __try {reinterpret_cast<OpenView>(base+kUiOpenViewRvaV1)(handler,0x55,true);return true;} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  reinterpret_cast<OpenView>(base+kUiOpenViewRvaV1)(handler,0x55,true);return true;
#endif
}
bool InvokeCombat(std::uintptr_t base,void *handler,std::uint32_t id) noexcept {
  IdAnyV1 argument{};
#if defined(_MSC_VER)
  __try {
#endif
    argument.type=reinterpret_cast<AnyType>(base+kUiIdAnyTypeGetterRvaV1)();
    if(!argument.type)return false;
    std::memcpy(argument.data.data(),&id,sizeof(id));
    // The engine copies this primitive into its own view-open request; no
    // retained bridge-owned object or arbitrary CPdxAny type is supplied.
    reinterpret_cast<OpenViewData>(base+kUiOpenViewDataRvaV1)(handler,0x1A,&argument);
    return true;
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool ReadMilitaryOwner(std::uintptr_t base,void *handler,std::uint32_t &owner) noexcept {
  void *military=nullptr;void *character=nullptr;void *linked_handler=nullptr;
  return Value(handler,0xA0,military) && TypedObject(base,military,kMilitaryTypeDescriptor) &&
      Value(military,0xD0,linked_handler) && linked_handler==handler &&
      Value(military,0x248,owner) && Object(base,kCharacterStorage,owner,0x18,character);
}
bool ReadKnightsOwner(std::uintptr_t base,void *handler,void *knights,std::uint32_t &owner) noexcept {
  void *linked_handler=nullptr;
  return Value(knights,0xD0,linked_handler) && linked_handler==handler && ReadMilitaryOwner(base,handler,owner);
}
struct NativeUiStringV1 { alignas(8) std::array<std::uint8_t,32> bytes{}; };
using KnightCountGetter = std::int32_t (__fastcall *)(void *);
using KnightBreakdownGetter = void * (__fastcall *)(void *,NativeUiStringV1 *);
using NativeStringDestroy = void (__fastcall *)(NativeUiStringV1 *);
bool InvokeKnightCount(std::uintptr_t base,void *window,bool right,std::int32_t &value) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    value=reinterpret_cast<KnightCountGetter>(base+(right?0x12F4860:0x12F4790))(window);return value>=0 && value<=4096;
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool InvokeKnightBreakdown(std::uintptr_t base,void *window,bool right,NativeUiStringV1 &value) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return reinterpret_cast<KnightBreakdownGetter>(base+(right?0x12F4A10:0x12F4930))(window,&value)==&value;
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool DestroyNativeUiString(std::uintptr_t base,NativeUiStringV1 &value) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    reinterpret_cast<NativeStringDestroy>(base+0x7E97D0)(&value);return true;
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool ReadKnightBreakdown(std::uintptr_t base,void *window,bool right,std::string &text) noexcept {
  text.clear();NativeUiStringV1 value{};
  if(!InvokeKnightBreakdown(base,window,right,value))return false;
  std::uint64_t size=0,capacity=0;void *pointer=nullptr;
  std::memcpy(&size,value.bytes.data()+16,8);std::memcpy(&capacity,value.bytes.data()+24,8);
  bool valid=size<=65536 && capacity>=size;
  if(valid) {
    if(capacity<16)pointer=value.bytes.data();else std::memcpy(&pointer,value.bytes.data(),8);
    if(size){text.resize(static_cast<std::size_t>(size));valid=Read(pointer,text.data(),text.size());}
  }
  const bool destroyed=DestroyNativeUiString(base,value);
  if(!valid || !destroyed)text.clear();return valid && destroyed;
}
bool ReadCombatKnights(std::uintptr_t base,void *handler,IngameUiResultV1 &out) noexcept {
  void *window=nullptr;void *combat=nullptr;std::uint32_t before_id=0,after_id=0;
  return Value(handler,0x168,window) && TypedObject(base,window,kTypeDescriptors[2]) &&
      Value(window,0xF8,before_id) && before_id==out.current_subject_id && Object(base,kCombatStorage,before_id,8,combat) &&
      InvokeKnightCount(base,window,false,out.left_knight_count) && InvokeKnightCount(base,window,true,out.right_knight_count) &&
      ReadKnightBreakdown(base,window,false,out.left_knight_breakdown) && ReadKnightBreakdown(base,window,true,out.right_knight_breakdown) &&
      Value(window,0xF8,after_id) && after_id==before_id;
}
bool ResolveKnightCountWidget(const ZhongguoScoreboardNativeEnvironmentV1 &env,bool right,void *&target) noexcept {
  ZhongguoScoreboardAccessV1 access{};void *root=nullptr;void *vt=nullptr;std::string actual;bool visible=false,enabled=false;
  const auto name=right?"right_knights":"left_knights";
  return ResolveNamedGuiWidgetV1(env,access,"combat_window",name,root,target) && root && target &&
      ReadGuiWidgetRuntimeV1(access,target,actual,vt,visible,enabled) && actual==name && visible && enabled &&
      TypedObject(env.module_base,target,kGuiTextWidgetTypeDescriptor);
}
bool InvokeHover(std::uintptr_t base,void *context,void *target) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    reinterpret_cast<SetHoveredWidget>(base+kSetHoveredWidgetRva)(context,target);return true;
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
void ReadCombatHover(const ZhongguoScoreboardNativeEnvironmentV1 &env,IngameUiResultV1 &out) noexcept {
  ZhongguoScoreboardAccessV1 access{};void *context=nullptr;void *owner=nullptr;void *hovered=nullptr;
  if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,context,owner) || !Value(context,0xF0,hovered))return;
  out.hover_state_available=true;
  if(!out.effective_visible || !out.subject_id_available || !hovered)return;
  for(bool right:{false,true}) {
    void *target=nullptr;void *widget_context=nullptr;
    if(ResolveKnightCountWidget(env,right,target) && target==hovered && Value(target,0xD8,widget_context) && widget_context==context) {
      out.hovered_widget_name=right?"right_knights":"left_knights";out.hovered_ui_side=right?"right":"left";
      out.hovered_combat_id=out.current_subject_id;return;
    }
  }
}
bool FiniteRect(const UiRectV1 &r,bool positive=false) noexcept {
  return std::isfinite(r.x) && std::isfinite(r.y) && std::isfinite(r.width) && std::isfinite(r.height) &&
      std::abs(r.x)<=1048576 && std::abs(r.y)<=1048576 && r.width>=0 && r.height>=0 &&
      r.width<=1048576 && r.height<=1048576 && (!positive || (r.width>0 && r.height>0));
}
void UnionRect(UiRectV1 &r,const UiRectV1 &x) noexcept {
  const float right=(std::max)(r.x+r.width,x.x+x.width),bottom=(std::max)(r.y+r.height,x.y+x.height);
  r.x=(std::min)(r.x,x.x);r.y=(std::min)(r.y,x.y);r.width=right-r.x;r.height=bottom-r.y;
}
bool StockCombatGuiMatches() noexcept {
  // The only non-widget extents used are the two stock backgrounds' declared
  // -23/-17 GUI-unit margins. Verify their exact original source bytes; these
  // are not screenshot coordinates or a guessed desktop scale. The managed
  // vanilla capture additionally verifies its enabled-mods list is empty.
  BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
  bool okay=false;
  try {
    std::array<wchar_t,32768> name{};const DWORD n=GetModuleFileNameW(nullptr,name.data(),static_cast<DWORD>(name.size()));
    if(!n || n>=name.size())return false;
    const auto path=std::filesystem::path(name.data()).parent_path().parent_path()/L"game"/L"gui"/L"window_combat.gui";
    std::ifstream stream(path,std::ios::binary|std::ios::ate);
    if(!stream || stream.tellg()!=58008)return false;
    std::array<unsigned char,58008> bytes{};stream.seekg(0);stream.read(reinterpret_cast<char *>(bytes.data()),static_cast<std::streamsize>(bytes.size()));
    if(!stream)return false;
    DWORD object_size=0,got=0;
    if(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0 &&
       BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&object_size),sizeof(object_size),&got,0)>=0 &&
       got==sizeof(object_size) && object_size>0 && object_size<=65536) {
      std::vector<unsigned char> object(object_size);std::array<unsigned char,32> digest{};
      if(BCryptCreateHash(algorithm,&hash,object.data(),object_size,nullptr,0,0)>=0 &&
         BCryptHashData(hash,bytes.data(),static_cast<ULONG>(bytes.size()),0)>=0 &&
         BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0)>=0) {
        constexpr char hex[]="0123456789ABCDEF";std::string actual;actual.reserve(64);
        for(auto c:digest){actual+=hex[c>>4];actual+=hex[c&15];}okay=actual==kStockCombatGuiSha256;
      }
      if(hash){BCryptDestroyHash(hash);hash=nullptr;}
    }
  }catch(...) {okay=false;}
  if(hash)BCryptDestroyHash(hash);
  if(algorithm)BCryptCloseAlgorithmProvider(algorithm,0);
  return okay;
}
bool OriginalGuiRect(std::uintptr_t base,void *widget,const UiRectV1 &local,UiRectV1 &rect) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return reinterpret_cast<GuiRectGetter>(base+kGuiRectRva)(widget,&rect,&local)==&rect && FiniteRect(rect);
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool ReadCombatGeometry(const ZhongguoScoreboardNativeEnvironmentV1 &env,void *handler,
                        std::uint32_t combat_id,CombatUiGeometryV1 &g) noexcept {
  g={};g.combat_id=combat_id;g.unavailable_reason="native_geometry_not_verified";
  void *window=nullptr;void *combat=nullptr;std::uint32_t before=0,after=0;
  if(!Value(handler,0x168,window) || !TypedObject(env.module_base,window,kTypeDescriptors[2]) ||
     !Value(window,0xF8,before) || before!=combat_id || !Object(env.module_base,kCombatStorage,before,8,combat))return false;
  ZhongguoScoreboardAccessV1 access{};void *context=nullptr;void *owner=nullptr;void *root=nullptr;void *target=nullptr;
  if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,context,owner) ||
     !ResolveNamedGuiWidgetV1(env,access,"combat_window","combat_window",root,target) || root!=target ||
     !TypedObject(env.module_base,root,kGuiWindowTypeDescriptor))return false;
  // Stock CPdxGuiWindow clamp 374E060 reads this exact native viewport and uses
  // GetRect369C450 in the same coordinate space; no OS/screenshot transform.
  if(!Value(context,0x3C0,g.viewport.width) || !Value(context,0x3C4,g.viewport.height) ||
     !FiniteRect(g.viewport,true) || g.viewport.width>65536 || g.viewport.height>65536)return false;
  std::array<void *,512> queue{},parents{},seen{};queue[0]=root;std::size_t count=1,index=0,visible_count=0;
  while(index<count) {
    auto *widget=queue[index];void *widget_context=nullptr;void *actual_parent=nullptr;void *vt=nullptr;
    bool visible=false,enabled=false;std::string name;
    if(!Value(widget,0xD8,widget_context) || widget_context!=context ||
       !ReadGuiWidgetRuntimeV1(access,widget,name,vt,visible,enabled) ||
       reinterpret_cast<std::uintptr_t>(vt)<env.module_base || reinterpret_cast<std::uintptr_t>(vt)>=env.module_base+kImageSize)return false;
    for(std::size_t j=0;j<index;++j)if(seen[j]==widget){g.unavailable_reason="geometry_duplicate_or_cycle";return false;}
    seen[index]=widget;
    if(index && (!Value(widget,0xE8,actual_parent) || actual_parent!=parents[index]))return false;
    // The original transforms walk the parent chain. Validate it is bounded,
    // acyclic, readable and attached to this same GUI context first.
    auto *ancestor=widget;std::array<void *,64> chain{};std::size_t depth=0;
    while(ancestor) {
      if(depth>=chain.size()){g.unavailable_reason="geometry_parent_depth_exceeded";return false;}
      for(std::size_t j=0;j<depth;++j)if(chain[j]==ancestor){g.unavailable_reason="geometry_parent_cycle";return false;}
      chain[depth++]=ancestor;float scale=0,cumulative=0;void *ctx=nullptr;
      if(!Value(ancestor,0xD8,ctx) || ctx!=context || !Value(ancestor,0x110,scale) ||
         !Value(ancestor,0x114,cumulative) || !std::isfinite(scale) || !std::isfinite(cumulative) ||
         scale<=0 || scale>64 || cumulative<=0 || cumulative>4096 || !Value(ancestor,0xE8,ancestor))return false;
    }
    if(index==0 && (!visible || !enabled || name!="combat_window")){g.unavailable_reason="geometry_combat_window_not_visible";return false;}
    if(visible) {
      UiRectV1 local{},rect{};
      if(!Value(widget,0x128,local.width) || !Value(widget,0x12C,local.height) || !FiniteRect(local) ||
         !OriginalGuiRect(env.module_base,widget,local,rect))return false;
      if(!index){if(!FiniteRect(rect,true))return false;g.window_rect=rect;g.content_union=rect;}
      else UnionRect(g.content_union,rect);
      ++visible_count;
    }
    void *children=nullptr;std::int32_t child_count=0;
    if(!Value(widget,0xFC,child_count) || child_count<0 || child_count>512 ||
       (child_count && (!Value(widget,0xF0,children) || !children)) || count+static_cast<std::size_t>(child_count)>queue.size()) {
      g.unavailable_reason="geometry_subtree_truncated_or_unreadable";return false;
    }
    for(std::int32_t child=0;child<child_count;++child) {
      void *item=nullptr;if(!Value(children,static_cast<std::size_t>(child)*8,item) || !item)return false;
      queue[count]=item;parents[count]=widget;++count;
    }
    ++index;
  }
  g.stock_margin_source_verified=StockCombatGuiMatches();
  if(!g.stock_margin_source_verified){g.unavailable_reason="stock_combat_gui_margin_source_mismatch";return false;}
  // GUI lines52-81: the first background widget is 100% of this root, with
  // two backgrounds whose margin={-23 -17}. Convert the declared outer rect
  // through the same original getter, so both axes use actual native scale.
  UiRectV1 outer{-23,-17,0,0},outer_rect{};
  if(!Value(root,0x128,outer.width) || !Value(root,0x12C,outer.height))return false;
  outer.width+=46;outer.height+=34;
  if(!OriginalGuiRect(env.module_base,root,outer,outer_rect))return false;
  UnionRect(g.content_union,outer_rect);
  if(!Value(window,0xF8,after) || after!=before)return false;
  g.widget_count=static_cast<std::uint32_t>(visible_count);
  if(!ComputeCombatUiFitTranslationV1(g.viewport,g.content_union,g.proposed_translation)) {
    g.unavailable_reason="combat_content_exceeds_native_viewport";return false;
  }
  g.fit_required=g.proposed_translation.x!=0 || g.proposed_translation.y!=0;
  g.content_inside_viewport=!g.fit_required;g.available=true;g.unavailable_reason.clear();return true;
}
bool InvokeCombatFit(std::uintptr_t base,void *root,const CombatUiGeometryV1 &g) noexcept {
  const UiFloat2V1 desired{g.window_rect.x+g.proposed_translation.x,g.window_rect.y+g.proposed_translation.y};
  UiFloat2V1 local{},anchored{},position{};float scale=0;
  if(!Value(root,0x110,scale) || !std::isfinite(scale) || scale<=0 || scale>64)return false;
#if defined(_MSC_VER)
  __try {
#endif
    // This is the original 374E060 window-clamp conversion recipe. Its root
    // destination is now derived from the entire visible bounded subtree.
    if(reinterpret_cast<GuiPointTransform>(base+kGuiAbsoluteToLocalRva)(root,&local,&desired)!=&local ||
       reinterpret_cast<GuiPositionGetter>(base+kGuiAnchoredPositionRva)(root,&anchored)!=&anchored)return false;
    position={anchored.x+local.x*scale,anchored.y+local.y*scale};
    if(!std::isfinite(position.x) || !std::isfinite(position.y) || std::abs(position.x)>1048576 || std::abs(position.y)>1048576)return false;
    reinterpret_cast<GuiPositionSetter>(base+kGuiSetPositionRva)(root,&position);return true;
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
std::string JsonEscape(std::string_view s) {
  std::string x;for(unsigned char c:s){if(c=='"'||c=='\\'){x+='\\';x+=c;}else if(c<32){const char *h="0123456789ABCDEF";x+="\\u00";x+=h[c>>4];x+=h[c&15];}else x+=c;}return x;
}
bool ReadWindow(const ZhongguoScoreboardNativeEnvironmentV1 &env,void *handler,
                IngameUiWindowKindV1 kind,IngameUiResultV1 &out) noexcept {
  const auto n=static_cast<std::size_t>(kind);void *window=nullptr;
  if(n>=kViewTypes.size() || !Value(handler,0x98+kViewTypes[n]*8,window) ||
      !TypedObject(env.module_base,window,kTypeDescriptors[n])) {
    out.unavailable_reason="window_object_type_unverified";return false;
  }
  ZhongguoScoreboardAccessV1 access{};void *root=nullptr;void *widget=nullptr;
  const auto name=IngameUiWindowNameV1(kind);
  if(!ResolveNamedGuiWidgetV1(env,access,name,name,root,widget) || !root || widget!=root) {
    out.unavailable_reason="fixed_window_root_unavailable";return false;
  }
  std::string actual;void *vtable=nullptr;
  if(!ReadGuiWidgetRuntimeV1(access,root,actual,vtable,out.effective_visible,out.enabled) || actual!=name ||
      !InspectNamedGuiSubtreeV1(access,env.module_base,root,name,out.tree)) {
    out.unavailable_reason="window_widget_read_unavailable";return false;
  }
  out.window_exists=true;
  void *subject=nullptr;std::uint32_t id=0;
  // Hidden windows can retain the last selection. The ID is available only
  // after complete generation validation and is never proof of visibility.
  if(kind==IngameUiWindowKindV1::character) {
    out.subject_id_available=Value(window,0xF8,id) && Object(env.module_base,kCharacterStorage,id,0x18,subject);
  } else if(kind==IngameUiWindowKindV1::combat) {
    out.subject_id_available=Value(window,0xF8,id) && Object(env.module_base,kCombatStorage,id,8,subject);
  } else if(kind==IngameUiWindowKindV1::army) {
    std::uint32_t native_id=0,reverse_id=0;void *unit=nullptr;
    out.subject_id_available=Value(window,0xF8,native_id) && Object(env.module_base,kArmyStorage,native_id,0x10,subject) &&
        Value(subject,0x124,id) && Object(env.module_base,kUnitStorage,id,0x10,unit) &&
        Value(unit,0x178,reverse_id) && reverse_id==native_id;
    if(out.subject_id_available)out.native_army_id=native_id;
  } else {
    out.subject_id_available=ReadKnightsOwner(env.module_base,handler,window,id);
    if(out.subject_id_available)out.owner_character_id=id;
  }
  if(out.subject_id_available)out.current_subject_id=id;
  return true;
}
} // namespace

bool ComputeCombatUiFitTranslationV1(const UiRectV1 &viewport,const UiRectV1 &content,UiFloat2V1 &delta) noexcept {
  delta={};
  if(!FiniteRect(viewport,true) || !FiniteRect(content,true) || content.width>viewport.width || content.height>viewport.height)return false;
  const float right=viewport.x+viewport.width,bottom=viewport.y+viewport.height;
  if(content.x<viewport.x)delta.x=viewport.x-content.x;
  else if(content.x+content.width>right)delta.x=right-content.x-content.width;
  if(content.y<viewport.y)delta.y=viewport.y-content.y;
  else if(content.y+content.height>bottom)delta.y=bottom-content.y-content.height;
  return std::isfinite(delta.x) && std::isfinite(delta.y);
}
bool ValidateIngameUiRequestV1(const IngameUiRequestV1 &r) noexcept {
  const auto k=static_cast<std::uint32_t>(r.window_kind),o=static_cast<std::uint32_t>(r.operation);
  if(k>3 || o>7 || r.subject_id==(std::numeric_limits<std::uint32_t>::max)())return false;
  if(r.operation==IngameUiOperationV1::query)return r.subject_id==0;
  if(r.operation==IngameUiOperationV1::open_knights)return r.window_kind==IngameUiWindowKindV1::knights && r.subject_id==0;
  return r.subject_id>0 && ((o==1 && k==0)||(o==2 && k==1)||((o==3 || o==5 || o==6 || o==7) && k==2));
}
bool ParseIngameUiRequestV1(std::string_view json,bool query,IngameUiRequestV1 &r) noexcept {
  r={};std::string kind,operation;std::uint64_t id=0;
  if(!bridge::JsonStringField(json,"window_kind",kind,16))return false;
  if(kind=="character")r.window_kind=IngameUiWindowKindV1::character;
  else if(kind=="army")r.window_kind=IngameUiWindowKindV1::army;
  else if(kind=="combat")r.window_kind=IngameUiWindowKindV1::combat;
  else if(kind=="knights")r.window_kind=IngameUiWindowKindV1::knights;
  else return false;
  if(!bridge::JsonUnsignedField(json,"subject_id",id) || id>(std::numeric_limits<std::uint32_t>::max)())return false;
  r.subject_id=static_cast<std::uint32_t>(id);
  if(query)r.operation=IngameUiOperationV1::query;
  else {
    if(!bridge::JsonStringField(json,"operation",operation,24))return false;
    if(operation=="open_character")r.operation=IngameUiOperationV1::open_character;
    else if(operation=="select_army")r.operation=IngameUiOperationV1::select_army;
    else if(operation=="open_combat")r.operation=IngameUiOperationV1::open_combat;
    else if(operation=="open_knights")r.operation=IngameUiOperationV1::open_knights;
    else if(operation=="hover_left_knights")r.operation=IngameUiOperationV1::hover_left_knights;
    else if(operation=="hover_right_knights")r.operation=IngameUiOperationV1::hover_right_knights;
    else if(operation=="fit_combat_window")r.operation=IngameUiOperationV1::fit_combat_window;
    else return false;
  }
  return ValidateIngameUiRequestV1(r);
}
std::string_view IngameUiWindowNameV1(IngameUiWindowKindV1 k) noexcept {
  switch(k){case IngameUiWindowKindV1::character:return "character_window";case IngameUiWindowKindV1::army:return "army_window";
    case IngameUiWindowKindV1::combat:return "combat_window";case IngameUiWindowKindV1::knights:return "knight_view";default:return "unavailable";}
}
bool ReadIngameUiGuiOwnerBindingV1(const ZhongguoScoreboardNativeEnvironmentV1 &env,
                                IngameUiGuiOwnerBindingV1 &out) noexcept {
  out={};
  if(!env.exact_build_admitted || env.offline_fixture_function_overrides || !env.module_base)return false;
  ZhongguoScoreboardAccessV1 access{};
  IngameUiGuiOwnerBindingV1 first{},second{};
  if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,first.context,first.owner) ||
     !first.context || !first.owner ||
     !ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,second.context,second.owner) ||
     first!=second)return false;
  out=first;return true;
}
bool ExecuteIngameUiNavigationV1(const ZhongguoScoreboardNativeEnvironmentV1 &env,const IngameUiRequestV1 &request,
                                const game::Snapshot &snapshot,const MainThreadExecutionStampV1 &stamp,
                                const IngameUiGuiOwnerBindingV1 &gui_binding,IngameUiResultV1 &out) noexcept {
  out={};out.date_raw=snapshot.date_raw;out.paused=snapshot.paused;out.played_character_id=snapshot.played_character_id;
  out.pump_epoch=stamp.pump_epoch;out.thread_id=stamp.thread_id;
  if(!env.exact_build_admitted || env.offline_fixture_function_overrides || !env.module_base ||
      !ValidateIngameUiRequestV1(request) || !snapshot.paused || !snapshot.map_ready || !snapshot.has_played_character ||
      !stamp.paused || stamp.date_raw!=snapshot.date_raw || stamp.thread_id!=GetCurrentThreadId() || !stamp.pump_epoch) {
    out.unavailable_reason="paused_exact_build_owner_admission_failed";return true;
  }
  IngameUiGuiOwnerBindingV1 current_gui{};
  if(!gui_binding.context || !gui_binding.owner || !ReadIngameUiGuiOwnerBindingV1(env,current_gui) || current_gui!=gui_binding) {
    out.unavailable_reason="current_gui_owner_binding_changed_before_navigation";return true;
  }
  void *handler=nullptr;
  if(!ResolveHandler(env.module_base,handler)){out.unavailable_reason="ingame_handler_unverified";return true;}
  if(!ReadWindow(env,handler,request.window_kind,out))return true;
  if(request.operation==IngameUiOperationV1::query && request.window_kind==IngameUiWindowKindV1::knights && (!out.subject_id_available ||
      out.owner_character_id!=static_cast<std::uint32_t>(snapshot.played_character_id))) {
    out.unavailable_reason="knights_owner_differs_from_played_actor";return true;
  }
  if(request.operation==IngameUiOperationV1::query){
    if(request.window_kind==IngameUiWindowKindV1::combat && out.subject_id_available && out.effective_visible) {
      if(!out.tree.truncated)ReadCombatGeometry(env,handler,out.current_subject_id,out.combat_geometry);
      else out.combat_geometry.unavailable_reason="target_census_truncated";
      out.combat_knights_read_available=ReadCombatKnights(env.module_base,handler,out);
      if(!out.combat_knights_read_available) {
        out.left_knight_count=-1;out.right_knight_count=-1;out.left_knight_breakdown.clear();out.right_knight_breakdown.clear();
      }
    }
    if(request.window_kind==IngameUiWindowKindV1::combat)ReadCombatHover(env,out);
    out.available=true;out.status="observed";return true;
  }
  // All actions, including semantic hover and fit, share the same original GUI
  // context and conservative effective-visible modal admission.
  ZhongguoScoreboardAccessV1 access{};void *context=nullptr;void *owner=nullptr;
  if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,context,owner) ||
      context!=gui_binding.context || owner!=gui_binding.owner) {
    out.unavailable_reason="modal_gui_context_binding_changed";return true;
  }
  if(!ReadModalNavigationAdmission(context,out.modal_admission)) {
    out.unavailable_reason=out.modal_admission.unavailable_reason;return true;
  }
  const auto expected=request.operation==IngameUiOperationV1::open_knights ? static_cast<std::uint32_t>(snapshot.played_character_id):request.subject_id;
  if((request.operation==IngameUiOperationV1::open_character || request.operation==IngameUiOperationV1::open_combat ||
      request.operation==IngameUiOperationV1::open_knights) && out.effective_visible && out.subject_id_available && out.current_subject_id==expected) {
    out.available=true;out.verification_pending=true;out.status="already_visible_verification_pending";return true;
  }
  void *subject=nullptr;bool invoked=false;
  if(request.operation==IngameUiOperationV1::open_character) {
    if(!Object(env.module_base,kCharacterStorage,request.subject_id,0x18,subject)){out.unavailable_reason="character_full_id_not_found";return true;}
    invoked=InvokeCharacter(env.module_base,request.subject_id);
  } else if(request.operation==IngameUiOperationV1::select_army) {
    std::int32_t actor=-1;std::uint32_t native_id=0,reverse=0;void *army=nullptr;
    if(!Object(env.module_base,kUnitStorage,request.subject_id,0x10,subject) || !Value(subject,0x174,actor) || actor!=snapshot.played_character_id ||
        !Value(subject,0x178,native_id) || !Object(env.module_base,kArmyStorage,native_id,0x10,army) ||
        !Value(army,0x124,reverse) || reverse!=request.subject_id) {out.unavailable_reason="player_unit_army_full_id_join_failed";return true;}
    invoked=InvokeUnit(env.module_base,handler,request.subject_id);
  } else if(request.operation==IngameUiOperationV1::open_combat) {
    if(!Object(env.module_base,kCombatStorage,request.subject_id,8,subject)){out.unavailable_reason="combat_full_id_not_found";return true;}
    // Limit opening to a combat already carried by this played actor's army
    // snapshot, rather than bypassing the original visibility admission.
    bool scoped=false;
    for(const auto &row:snapshot.player_armies) {
      void *unit=nullptr;void *army=nullptr;std::uint32_t native_id=0,reverse_id=0,combat_id=0;
      if(row.in_combat && row.army_id>=0 && row.owner_character_id==snapshot.played_character_id &&
          Object(env.module_base,kUnitStorage,static_cast<std::uint32_t>(row.army_id),0x10,unit) &&
          Value(unit,0x178,native_id) && Object(env.module_base,kArmyStorage,native_id,0x10,army) &&
          Value(army,0x124,reverse_id) && reverse_id==static_cast<std::uint32_t>(row.army_id) &&
          Value(army,0x128,combat_id) && combat_id==request.subject_id)scoped=true;
    }
    if(!scoped){out.unavailable_reason="combat_not_in_played_army_scope";return true;}
    invoked=InvokeCombat(env.module_base,handler,request.subject_id);
  } else if(request.operation==IngameUiOperationV1::fit_combat_window) {
    void *root=nullptr;void *target=nullptr;void *widget_context=nullptr;
    if(!out.effective_visible || !out.enabled || out.tree.truncated || !out.subject_id_available || out.current_subject_id!=request.subject_id ||
       !ReadCombatGeometry(env,handler,request.subject_id,out.combat_geometry) ||
       !ResolveNamedGuiWidgetV1(env,access,"combat_window","combat_window",root,target) || root!=target ||
       !Value(root,0xD8,widget_context) || widget_context!=context) {
      out.unavailable_reason=out.combat_geometry.unavailable_reason.empty()?"current_combat_geometry_unverified":out.combat_geometry.unavailable_reason;return true;
    }
    if(!out.combat_geometry.fit_required) {
      out.available=true;out.verification_pending=true;out.status="already_layout_fitted_verification_pending";return true;
    }
    invoked=InvokeCombatFit(env.module_base,root,out.combat_geometry);
    if(invoked)ReadCombatGeometry(env,handler,request.subject_id,out.combat_geometry);
  } else if(request.operation==IngameUiOperationV1::hover_left_knights || request.operation==IngameUiOperationV1::hover_right_knights) {
    void *target=nullptr;void *widget_context=nullptr;
    if(!out.effective_visible || !out.subject_id_available || out.current_subject_id!=request.subject_id ||
        !ResolveKnightCountWidget(env,request.operation==IngameUiOperationV1::hover_right_knights,target) ||
        !Value(target,0xD8,widget_context) || widget_context!=context) {
      out.unavailable_reason="current_combat_knight_text_target_unverified";return true;
    }
    invoked=InvokeHover(env.module_base,context,target);
  } else if(request.operation==IngameUiOperationV1::open_knights) {
    // Admission uses the original default-player MilitaryView context, not
    // whether the still-closed KnightsView has a selected/visible subject.
    std::uint32_t actor=0;
    if(!ReadMilitaryOwner(env.module_base,handler,actor) || actor!=static_cast<std::uint32_t>(snapshot.played_character_id)) {
      out.unavailable_reason="default_player_military_view_owner_unverified";return true;
    }
    out.owner_character_id=actor;out.current_subject_id=actor;out.subject_id_available=true;
    invoked=InvokeKnights(env.module_base,handler);
  }
  out.dispatch_invoked=invoked;out.available=invoked;out.verification_pending=invoked;
  out.status=invoked?"acknowledged_verification_pending":"unavailable";
  if(!invoked)out.unavailable_reason="native_navigation_fault";
  return true;
}

std::string SerializeIngameUiResultV1(const IngameUiRequestV1 &r,const IngameUiResultV1 &v,std::uint64_t revision) {
  std::ostringstream o;o<<std::boolalpha<<std::setprecision(std::numeric_limits<float>::max_digits10);
  o<<"{\"schema\":\"ck3-ingame-ui-window-v1\",\"accepted\":"<<v.available<<",\"available\":"<<v.available
   <<",\"status\":\""<<v.status<<"\",\"window_kind\":\"";
  constexpr std::array<std::string_view,4> kinds{"character","army","combat","knights"};o<<kinds[static_cast<std::size_t>(r.window_kind)]
   <<"\",\"window_name\":\""<<IngameUiWindowNameV1(r.window_kind)<<"\",\"requested_subject_id\":"<<r.subject_id
   <<",\"window_exists\":"<<v.window_exists<<",\"effective_visible\":"<<v.effective_visible<<",\"enabled\":"<<v.enabled
   <<",\"subject_id_available\":"<<v.subject_id_available<<",\"current_subject_id\":"<<v.current_subject_id
   <<",\"native_army_id\":"<<v.native_army_id<<",\"owner_character_id\":"<<v.owner_character_id
   <<",\"dispatch_invoked\":"<<v.dispatch_invoked<<",\"verification_pending\":"<<v.verification_pending
   <<",\"date_raw\":"<<v.date_raw<<",\"paused\":"<<v.paused<<",\"played_character_id\":"<<v.played_character_id
   <<",\"native_revision\":"<<revision<<",\"pump_epoch\":"<<v.pump_epoch<<",\"thread_id\":"<<v.thread_id
   <<",\"application_owner_thread_verified\":"<<v.application_owner_thread_verified
   <<",\"gui_owner_binding_verified\":"<<v.gui_owner_binding_verified
   <<",\"gui_context_address\":"<<v.gui_context_address<<",\"gui_owner_address\":"<<v.gui_owner_address
   <<",\"rng_owner_thread_id\":"<<v.rng_owner_thread_id<<",\"rng_owner_is_ui_admission_gate\":false"
   <<",\"combat_knights_read_available\":"<<v.combat_knights_read_available
   <<",\"left_knight_count\":"<<v.left_knight_count<<",\"right_knight_count\":"<<v.right_knight_count
   <<",\"left_knight_breakdown\":\""<<JsonEscape(v.left_knight_breakdown)<<"\",\"right_knight_breakdown\":\""<<JsonEscape(v.right_knight_breakdown)
   <<"\",\"combat_roster_full_ids_available\":false,\"native_backend_id\":\"ck3-1.19.0.6-native-ingame-ui-v1\""
   <<",\"hover_state_available\":"<<v.hover_state_available<<",\"hovered_widget_name\":\""<<v.hovered_widget_name
   <<"\",\"hovered_ui_side\":\""<<v.hovered_ui_side<<"\",\"hovered_combat_id\":"<<v.hovered_combat_id
   <<",\"hover_readback_is_pixels\":false";
  const auto &m=v.modal_admission;
  o<<",\"modal_admission\":{\"attempted\":"<<m.attempted<<",\"header_read\":"<<m.header_read
   <<",\"receivers_verified\":"<<m.receivers_verified<<",\"receiver_count\":";
  if(m.header_read)o<<m.receiver_count;else o<<"null";
  o<<",\"vector_address\":"<<m.vector_address<<",\"effective_visible_count\":"<<m.effective_visible_count
   <<",\"effective_hidden_mask\":8,\"policy\":\"refuse_any_effective_visible_receiver\""
   <<",\"unavailable_reason\":\""<<JsonEscape(m.unavailable_reason)<<"\",\"receivers\":[";
  for(std::size_t index=0;index<m.receivers.size();++index) {
    if(index)o<<',';
    o<<"{\"address\":"<<m.receivers[index].address<<",\"flags_d0\":"<<static_cast<unsigned>(m.receivers[index].flags_d0)<<'}';
  }
  o<<"]}";
  o<<",\"combat_geometry\":{\"available\":"<<v.combat_geometry.available
   <<",\"combat_id\":"<<v.combat_geometry.combat_id<<",\"widget_count\":"<<v.combat_geometry.widget_count
   <<",\"coordinate_space\":\"native_gui_absolute\",\"scope\":\"visible_widget_union_and_verified_stock_background_margins\""
   <<",\"stock_margin_source_verified\":"<<v.combat_geometry.stock_margin_source_verified
   <<",\"stock_margin_source_sha256\":\""<<(v.combat_geometry.stock_margin_source_verified?kStockCombatGuiSha256:std::string_view{})<<"\""
   <<",\"content_inside_viewport\":"<<(v.combat_geometry.available && v.combat_geometry.content_inside_viewport)
   <<",\"fit_required\":"<<(v.combat_geometry.available && v.combat_geometry.fit_required)
   <<",\"readback_is_pixels\":false,\"full_panel_pixels_proven\":false";
  const auto &g=v.combat_geometry;
  const auto write_rect=[&o,&g](std::string_view name,const UiRectV1 &x){
    const UiRectV1 z=g.available?x:UiRectV1{};
    o<<",\""<<name<<"\":{\"x\":"<<z.x<<",\"y\":"<<z.y<<",\"width\":"<<z.width<<",\"height\":"<<z.height<<'}';
  };
  write_rect("viewport",g.viewport);write_rect("window_rect",g.window_rect);write_rect("content_union",g.content_union);
  o<<",\"proposed_translation\":{\"x\":"<<(g.available?g.proposed_translation.x:0)
   <<",\"y\":"<<(g.available?g.proposed_translation.y:0)<<"},\"unavailable_reason\":\""
   <<JsonEscape(g.available?std::string_view{}:(g.unavailable_reason.empty()?std::string_view{"not_visible_current_combat_window"}:std::string_view{g.unavailable_reason}))<<"\"}"
   <<",\"game_version\":\"1.19.0.6\",\"executable_sha256\":\"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\""
   <<",\"unavailable_reason\":\""<<v.unavailable_reason<<"\",\"knights_list_scope\":\"military_eligible_not_active_combat_roster\""
   <<",\"tree\":{\"scope_root_name\":\""<<v.tree.scope_root_name<<"\",\"root_available\":"<<v.tree.root_available
   <<",\"truncated\":"<<v.tree.truncated<<",\"widget_count\":"<<v.tree.widget_count<<",\"widgets\":[";
  for(std::size_t i=0;i<v.tree.widget_count;++i){if(i)o<<',';const auto &w=v.tree.widgets[i];
    // Runtime names are engine-owned strings and require JSON escaping.
    o<<"{\"runtime_name\":\""<<JsonEscape(w.runtime_name)<<"\",\"child_path\":\""<<JsonEscape(w.child_path)
     <<"\",\"depth\":"<<w.depth<<",\"child_count\":"<<w.child_count<<",\"vtable_rva\":"<<w.vtable_rva
     <<",\"effective_visible\":"<<w.effective_visible<<",\"enabled\":"<<w.enabled<<'}';
  }o<<"]}}";return o.str();
}
} // namespace xar::ck3_11906
