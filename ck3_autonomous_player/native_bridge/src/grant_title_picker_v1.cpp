#include "xar_bridge/grant_title_picker_v1.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include "xar_bridge/ordinary_character_interaction_v1.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_grant_title_picker_profile.hpp"
#include <Windows.h>
#include <algorithm>
#include <array>
#include <charconv>
#include <limits>
#include <span>

namespace xar::ck3_12003 {
namespace {
constexpr std::string_view kSha="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
using ImageProfile=ck3_12004::GrantTitlePickerImageProfileV1;
constexpr ImageProfile kImageProfile12003{
    false,ck3_11906::GuiAbiRevisionV1::crozier12003,
    0x44D6048,0x55072C0,0x44BC408,0x5514460,
    0x44BA890,0x5694B50,0x452DBD8,0x5742F88,
    0x45250D8,0x5731DB8,0x4712A18,
    0x10EC1F0,0x10EC2F0,0x10EC4B0,0x10EC0E0,
    0x117C530,0x117BAE0,0x10E6FF0,0xAF34A0,0x10E7810,0x21603A0};
const ImageProfile *Profile(const game::AdapterDescriptor &d) noexcept {
  if(d.game_version=="1.20.0.3"&&d.executable_sha256==kSha)return &kImageProfile12003;
  if(game::IsCk3_12004Descriptor(d))return &ck3_12004::kGrantTitlePickerImageProfile12004V1;
  return nullptr;
}
constexpr std::size_t kMaximumRows=2048,kMaximumRequested=64;
bool Bytes(const void *p,void *out,std::size_t n) noexcept {
  if(!p||!out||!n)return false;SIZE_T got=0;
  return ReadProcessMemory(GetCurrentProcess(),p,out,n,&got)&&got==n;
}
template<class T> bool Load(const void *p,std::size_t off,T &out) noexcept {
  const auto a=reinterpret_cast<std::uintptr_t>(p);
  return a&&off<=std::numeric_limits<std::uintptr_t>::max()-a&&Bytes(reinterpret_cast<const void *>(a+off),&out,sizeof(out));
}
template<class F,class R,class... A> bool Call(F f,R &out,A... args) noexcept {
  __try {out=f(args...);return true;} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool CallVoid(std::uintptr_t f,void *object) noexcept {
  __try {reinterpret_cast<void(*)(void *)>(f)(object);return true;} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
#include "grant_title_picker_pins_v1.inc"
#include "grant_title_picker_pins_12004_v1.inc"
struct CodePin {std::uintptr_t rva;std::array<std::uint8_t,32> bytes;};
#include "ordinary_interaction_code_pins_v1.inc"
#include "ordinary_interaction_code_pins_12004_v1.inc"
bool GrantPins12004(std::uintptr_t base) noexcept {
  std::array<unsigned char,1358> actual{};
  for(const auto &pin:kGrantImageCodePins12004V1){
    if(pin.bytes.size()>actual.size()||!Bytes(reinterpret_cast<const void *>(base+pin.rva),actual.data(),pin.bytes.size())||
        !std::equal(pin.bytes.begin(),pin.bytes.end(),actual.begin()))return false;
  }
  return true;
}
bool GrantClosedPins12004(std::uintptr_t base,const ImageProfile &profile) noexcept {
  const void *grant_method=nullptr,*confirmation_method=nullptr;
  return Load(reinterpret_cast<const void *>(base+profile.grant_vtable),0x38,grant_method)&&
      grant_method==reinterpret_cast<const void *>(base+profile.is_open)&&
      Load(reinterpret_cast<const void *>(base+profile.confirmation_vtable),0x38,confirmation_method)&&confirmation_method==grant_method;
}
bool OrdinaryPins(std::uintptr_t base,bool actual4) noexcept {
  const auto &pins=actual4?kOrdinaryInteractionCodePins12004V1:kOrdinaryInteractionCodePinsV1;
  for(const auto &pin:pins){std::array<std::uint8_t,32> actual{};
    if(!Bytes(reinterpret_cast<const void *>(base+pin.rva),actual.data(),actual.size())||actual!=pin.bytes)return false;}
  return true;
}
bool Typed(const void *p,std::uintptr_t base,std::uintptr_t vt,std::uint32_t td) noexcept {
  const void *vptr=nullptr,*col=nullptr;std::array<std::uint32_t,6> data{};
  return Load(p,0,vptr)&&reinterpret_cast<std::uintptr_t>(vptr)==base+vt&&
      Load(reinterpret_cast<const void *>(base+vt-8),0,col)&&Bytes(col,data.data(),sizeof(data))&&
      data[0]==1&&data[1]==0&&data[3]==td&&data[5]==reinterpret_cast<std::uintptr_t>(col)-base;
}
void *Resolve(std::uintptr_t base,std::uintptr_t slot,std::uintptr_t fallback,std::uint32_t id,std::size_t identity) noexcept {
  if(id==UINT32_MAX)return nullptr;
  const void *storage=nullptr,*entries=nullptr,*null_object=nullptr;void *object=nullptr;
  std::int32_t count=0;std::uint32_t observed=UINT32_MAX;
  const auto index=id&0xFFFFFFU;
  if(!Load(reinterpret_cast<const void *>(base+slot),0,storage)||!storage||
      !Load(storage,0x20,entries)||!entries||!Load(storage,0x2C,count)||count<=0||count>0x1000000||
      index>=static_cast<std::uint32_t>(count)||!Load(entries,index*0x10ULL+8,object)||!object||
      !Load(reinterpret_cast<const void *>(base+fallback),0,null_object)||object==null_object||
      !Load(object,identity,observed)||observed!=id)return nullptr;
  return object;
}
bool Character(std::uintptr_t base,std::uint32_t id,bool alive) noexcept {
  const auto *p=Resolve(base,0x5C67568,0x5C67570,id,0x18);std::uint32_t kind=0;const void *death=nullptr;
  return p&&Load(p,0x1C,kind)&&kind==0x43686172U&&Load(p,0x1D0,death)&&(!alive||!death);
}
bool Holder(std::uintptr_t base,std::uint32_t id,GrantTitlePickerHolderV1 &out,const ImageProfile &profile) noexcept {
  out={};out.title_full_id=id;
  const auto *p=Resolve(base,0x5D1DAF8,0x5D1DAE0,id,0x10);std::uintptr_t vt=0;std::uint32_t holder=UINT32_MAX;
  if(!p||!Load(p,0,vt)||vt!=base+profile.title_vtable||!Load(p,0x128,holder))return false;
  if(holder!=UINT32_MAX){if(!Character(base,holder,false))return false;out.holder_character_full_id=holder;}
  out.available=true;return true;
}
bool Key(const void *definition) noexcept {
  constexpr std::string_view key="grant_titles_interaction";
  if(!definition)return false;
  const void *text=static_cast<const std::byte *>(definition)+0x18;
  std::uint64_t size=0,capacity=0;std::array<char,25> actual{};
  return definition&&Load(definition,0x28,size)&&size==key.size()&&Load(definition,0x30,capacity)&&capacity>=size&&
      (capacity<16||Load(definition,0x18,text))&&Bytes(text,actual.data(),key.size()+1)&&
      actual[key.size()]==0&&std::string_view(actual.data(),key.size())==key;
}
bool Ids(const std::vector<std::uint32_t> &v,bool allow_empty) {
  if(v.size()>kMaximumRequested||(!allow_empty&&v.empty()))return false;
  auto sorted=v;std::sort(sorted.begin(),sorted.end());
  return std::find(sorted.begin(),sorted.end(),UINT32_MAX)==sorted.end()&&
      std::adjacent_find(sorted.begin(),sorted.end())==sorted.end();
}
bool SameIds(const std::vector<std::uint32_t> &a,const std::vector<std::uint32_t> &b) {
  auto x=a,y=b;std::sort(x.begin(),x.end());std::sort(y.begin(),y.end());return x==y;
}
struct Pass {
  void *logical=nullptr,*gfx=nullptr,*handler=nullptr,*grant=nullptr,*confirmation=nullptr,*root=nullptr;
  bool confirmation_visible=false;
  const void *data=nullptr;
  std::vector<void *> items;
  GrantTitlePickerObservationV1 observation{};
  bool operator==(const Pass &) const=default;
};
bool ReadPass(const GrantTitlePickerContextV1 &c,const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &env,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,Pass &p,const ImageProfile &profile,bool permit_closed_prepare=false) {
  const auto base=env.module_base;const void *back=nullptr,*definition=nullptr;std::uint32_t actor=UINT32_MAX,recipient=UINT32_MAX,effective_actor=UINT32_MAX;
  if(!Load(reinterpret_cast<const void *>(base+0x5C6A520),0,p.logical)||
      reinterpret_cast<std::uintptr_t>(p.logical)!=stamp.jomini_state||!Typed(p.logical,base,profile.logical_vtable,profile.logical_type)||
      !Load(p.logical,0x10,p.gfx)||!Typed(p.gfx,base,profile.gfx_vtable,profile.gfx_type)||
      !Load(p.gfx,0x20,back)||back!=p.logical||!Load(p.gfx,0x88,p.handler)||!Typed(p.handler,base,profile.handler_vtable,profile.handler_type))return false;
  // Both actual profiles qualify the stock Grant+110 and Confirmation+F0 slots.
  if(!Load(p.handler,0x110,p.grant)||!Typed(p.grant,base,profile.grant_vtable,profile.grant_type)||
      !Load(p.handler,0xF0,p.confirmation)||!Typed(p.confirmation,base,profile.confirmation_vtable,profile.confirmation_type)||
      !Load(p.grant,0x98,back)||back!=p.logical||
      !Load(p.grant,0xA0,back)||back!=p.handler||!Load(p.confirmation,0x98,back)||back!=p.logical||
      !Load(p.confirmation,0xA0,back)||back!=p.handler)return false;
  if(permit_closed_prepare&&c.operation==GrantTitlePickerOperationV1::prepare){
    // Each profile checks both primary VT+38 slots and its exact IsOpen body.
    // The NULL +60 path is closed; stock first-open establishes C8 and GUI binding.
    // No row/selection or business eligibility is inferred from a closed model.
    using Predicate=bool(*)(void *);bool grant_open=true;
    if(!(profile.actual4?GrantClosedPins12004(base,profile):GrantClosedPins(base))||
        !Call(reinterpret_cast<Predicate>(base+profile.is_open),grant_open,p.grant)||
        !Call(reinterpret_cast<Predicate>(base+profile.is_open),p.confirmation_visible,p.confirmation))return false;
    if(!grant_open){
      if(!Load(p.grant,0x60,p.root))return false;
      for(const auto id:c.requested_title_full_ids){GrantTitlePickerHolderV1 h{};if(!Holder(base,id,h,profile))return false;p.observation.requested_title_holders.push_back(h);}
      p.observation.available=true;return true;
    }
  }
  if(!Load(p.grant,0xC8,back)||back!=p.confirmation)return false;
  ck3_11906::ZhongguoScoreboardAccessV1 access{};void *widget=nullptr;ck3_11906::NamedGuiTreeInspectionV1 tree{};
  constexpr std::string_view name="grant_titles_interaction_window";
  if(!ck3_11906::ResolveNamedGuiWidgetV1(env,access,name,name,p.root,widget)||!p.root||widget!=p.root||
      !Load(p.grant,0x60,back)||back!=p.root||!ck3_11906::InspectNamedGuiSubtreeV1(access,base,p.root,name,tree)||
      tree.truncated||tree.widget_count!=tree.widgets.size()||tree.widgets.empty())return false;
  std::size_t root_matches=0;
  for(const auto &row:tree.widgets)if(row.child_path.empty()){
    if(row.runtime_name!=name)return false;++root_matches;p.observation.window_visible=row.effective_visible;
  }
  if(root_matches!=1)return false;
  void *confirmation_root=nullptr,*confirmation_vtable=nullptr;std::string confirmation_name;bool confirmation_enabled=false;
  if(!Load(p.confirmation,0x60,confirmation_root)||!confirmation_root||
      !ck3_11906::ReadGuiWidgetRuntimeV1(access,confirmation_root,confirmation_name,confirmation_vtable,p.confirmation_visible,confirmation_enabled))return false;
  for(const auto id:c.requested_title_full_ids){GrantTitlePickerHolderV1 h{};if(!Holder(base,id,h,profile))return false;p.observation.requested_title_holders.push_back(h);}
  p.observation.available=true;
  if(!p.observation.window_visible)return true;
  if(!Load(p.confirmation,0x3A0,actor)||actor!=static_cast<std::uint32_t>(c.expected_snapshot.played_character_id)||
      !Load(p.confirmation,0x3A4,recipient)||recipient!=c.recipient_character_full_id||
      !Load(p.confirmation,0x3B4,effective_actor)||effective_actor!=actor||
      !Character(base,actor,true)||!Character(base,recipient,true)||!Load(p.confirmation,0xC8,definition)||!Key(definition))return false;
  p.observation.window_binding_verified=true;
  std::int32_t count=-1;
  // Capacity+1018 is not a source-qualified requirement. GetTitles copies ptr/count only.
  if(!Load(p.confirmation,0x1010,p.data)||!Load(p.confirmation,0x101C,count)||count<0||static_cast<std::size_t>(count)>kMaximumRows||(count&&!p.data))return false;
  using Getter=void *(*)(void *);using Predicate=bool(*)(void *);
  for(std::int32_t i=0;i<count;++i){
    void *item=nullptr,*title=nullptr;const void *controller=nullptr,*parent=nullptr;std::uint32_t id=UINT32_MAX,returned_id=UINT32_MAX;
    if(!Load(p.data,static_cast<std::size_t>(i)*8,item)||!item||!Load(item,0x30,back)||back!=p.confirmation||
        !Load(item,0x38,controller)||controller!=static_cast<const std::byte *>(static_cast<const void *>(p.confirmation))+0x1028||
        !Load(controller,0,back)||back!=p.confirmation||!Load(item,0x18,parent)||!Load(item,0x24,id)||id==UINT32_MAX)return false;
    // Validate every parent before invoking the native selected predicate, which follows parent links.
    std::size_t depth=0;const void *ancestor=parent;
    while(ancestor){
      if(++depth>static_cast<std::size_t>(count)||!Load(ancestor,0x30,back)||back!=p.confirmation)return false;
      bool member=false;for(std::int32_t j=0;j<count;++j){const void *candidate=nullptr;if(!Load(p.data,static_cast<std::size_t>(j)*8,candidate))return false;if(candidate==ancestor)member=true;}
      if(!member||!Load(ancestor,0x18,ancestor))return false;
    }
    if(!Call(reinterpret_cast<Getter>(base+profile.row_title),title,item)||!title||
        title!=Resolve(base,0x5D1DAF8,0x5D1DAE0,id,0x10)||!Load(title,0x10,returned_id)||returned_id!=id)return false;
    GrantTitlePickerHolderV1 h{};GrantTitlePickerRowV1 row{};row.title_full_id=id;
    if(!Holder(base,id,h,profile)||!Call(reinterpret_cast<Predicate>(base+profile.row_selected),row.selected,item)||
        !Call(reinterpret_cast<Predicate>(base+profile.row_selectable),row.selectable,item))return false;
    row.holder_character_full_id=h.holder_character_full_id;
    if(std::any_of(p.observation.rows.begin(),p.observation.rows.end(),[id](const auto &r){return r.title_full_id==id;}))return false;
    if(row.selected)p.observation.selected_title_full_ids.push_back(id);
    p.items.push_back(item);p.observation.rows.push_back(row);
  }
  bool can_send=false;std::uint8_t warning=0;
  if(!Call(reinterpret_cast<Predicate>(base+profile.can_send),can_send,p.grant)||!Load(p.grant,0x158,warning)||warning>1)return false;
  p.observation.native_can_send=can_send;p.observation.warning_confirmation_required=warning!=0;p.observation.rows_complete=true;
  return true;
}
bool Control(const game::Snapshot &a,const game::Snapshot &b) noexcept {
  return a.map_ready&&b.map_ready&&a.paused&&b.paused&&a.has_played_character&&b.has_played_character&&
      a.played_character_alive&&b.played_character_alive&&a.played_character_id==b.played_character_id&&a.date_raw==b.date_raw;
}
} // namespace

bool IsGrantTitlePickerBuildV1(const game::AdapterDescriptor &d) noexcept {return Profile(d)!=nullptr;}

bool ParseGrantTitlePickerIdsV1(std::string_view text,std::vector<std::uint32_t> &out,bool allow_empty) noexcept {
  try {out.clear();if(text.empty())return allow_empty;while(!text.empty()){
    if(out.size()>=kMaximumRequested)return false;const auto pos=text.find(',');const auto token=text.substr(0,pos);std::uint32_t id=0;
    if(token.empty()||(token.size()>1&&token.front()=='0'))return false;
    const auto converted=std::from_chars(token.data(),token.data()+token.size(),id);
    if(converted.ec!=std::errc{}||converted.ptr!=token.data()+token.size()||id==UINT32_MAX||std::find(out.begin(),out.end(),id)!=out.end())return false;
    out.push_back(id);if(pos==std::string_view::npos)break;text.remove_prefix(pos+1);if(text.empty())return false;
  }return true;}catch(...){out.clear();return false;}
}
bool ParseGrantTitlePickerIdsFieldV1(std::string_view json,std::string_view key,std::vector<std::uint32_t> &out,bool allow_empty) noexcept {
  try {
    // These provider-private compact CSV fields also admit the empty set.
    // The shared control-string parser intentionally rejects empty strings.
    if(key!="requested_title_full_ids"&&key!="expected_selected_title_full_ids")return false;
    const std::string needle="\""+std::string(key)+"\":\"";
    const auto begin=json.find(needle);
    if(begin==std::string_view::npos||json.find(needle,begin+needle.size())!=std::string_view::npos)return false;
    const auto value_begin=begin+needle.size(),end=json.find('"',value_begin);
    return end!=std::string_view::npos&&end-value_begin<=704&&
        ParseGrantTitlePickerIdsV1(json.substr(value_begin,end-value_begin),out,allow_empty);
  }catch(...){out.clear();return false;}
}
bool ExecuteGrantTitlePickerV1(GrantTitlePickerContextV1 &c,ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &env) noexcept {
  auto &out=c.result;out={};out.operation=c.operation;out.native_revision=c.native_revision;out.connection_generation=c.connection_generation;
  out.game_pid=GetCurrentProcessId();out.recipient_character_full_id=c.recipient_character_full_id;
  try {
    const auto reject=[&](const char *reason){out.status="unavailable";out.unavailable_reason=reason;return true;};
    const auto *profile=c.game?Profile(c.game->descriptor()):nullptr;
    if(!profile||
        !c.native_revision||!c.connection_generation||!c.recipient_character_full_id||c.recipient_character_full_id==UINT32_MAX||
        !Ids(c.requested_title_full_ids,true)||!Ids(c.expected_selected_title_full_ids,true)||
        !env.exact_build_admitted||env.offline_fixture_function_overrides||env.gui_abi_revision!=profile->gui_revision)
      return reject(c.game&&c.game->descriptor().game_version=="1.20.0.4"?
          "exact_12004_grant_request_unavailable":"exact_12003_grant_request_unavailable");
    out.exact_build=c.game->descriptor().game_version;out.executable_sha256=c.game->descriptor().executable_sha256;
    if(!ck3_11906::IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()))return reject("paused_application_owner_unverified");
    out.owner_thread_verified=true;game::Snapshot before{};
    if(!game::ReadSnapshot(*c.game,before)||before!=c.expected_snapshot||!Control(before,before)||before.date_raw!=stamp.date_raw||
        before.has_active_event||before.has_pending_character_interaction)return reject("fresh_grant_frame_unverified");
    out.played_character_id=before.played_character_id;out.date_raw=before.date_raw;
    if(!Character(env.module_base,c.recipient_character_full_id,true))return reject("grant_recipient_full_identity_unavailable");
    const bool grant_pins=profile->actual4?GrantPins12004(env.module_base):
        GrantPins(env.module_base)&&GrantOpenPins(env.module_base)&&GrantRefreshPin(env.module_base);
    if(!grant_pins||!OrdinaryPins(env.module_base,profile->actual4))return reject(profile->actual4?
        "loaded_12004_grant_method_pins_changed":"loaded_12003_grant_method_pins_changed");out.source_abi_pins_verified=true;
    Pass first{},second{};
    const bool prepare=c.operation==GrantTitlePickerOperationV1::prepare;
    if(!ReadPass(c,env,stamp,first,*profile,prepare)||!ReadPass(c,env,stamp,second,*profile,prepare)||first!=second)return reject("grant_window_or_complete_rows_unstable");
    out.before=first.observation;
    if(c.operation==GrantTitlePickerOperationV1::prepare){
      if(first.observation.window_visible){if(!first.observation.window_binding_verified)return reject("existing_grant_window_binding_changed");}
      else{
        // AF2810 resets a previously open Confirmation before replacing it.
        // This minimal Prepare only enters from a closed stock Confirmation;
        // it never discards another interaction's live selection/context.
        if(first.confirmation_visible)return reject("other_stock_confirmation_window_open");
        struct Frame {const game::GameAdapter *game; game::Snapshot snapshot;};Frame frame{c.game,before};
        auto bindings=profile->actual4?
            ordinary_interaction::BindOrdinaryInteractionImage12004(env.module_base,out.executable_sha256):
            ordinary_interaction::BindOrdinaryInteractionImage12003(env.module_base,kSha);
        bindings.dispatch_frame_context=&frame;
        bindings.verify_dispatch_frame=[](void *raw) noexcept {const auto &f=*static_cast<const Frame *>(raw);game::Snapshot actual{};return game::ReadSnapshot(*f.game,actual)&&actual==f.snapshot;};
        OrdinaryInteractionRequestV1 request{};
        request.interaction_key="grant_titles_interaction";request.recipient_id=c.recipient_character_full_id;
        request.expected_player_character_id=before.played_character_id;request.expected_revision=c.native_revision;
        request.expected_connection_generation=c.connection_generation;request.expected_game_pid=GetCurrentProcessId();
        ordinary_interaction::GrantWindowBindingsV1 window{};window.confirmation=first.confirmation;window.handler=first.handler;
        window.install_context=reinterpret_cast<decltype(window.install_context)>(env.module_base+profile->copy_context);
        window.open_window=reinterpret_cast<decltype(window.open_window)>(env.module_base+profile->handler_open);
        window.refresh_window=reinterpret_cast<decltype(window.refresh_window)>(env.module_base+profile->refresh);
        ordinary_interaction::GrantPrepareObservationV1 prepared{};
        ordinary_interaction::PrepareGrantTitlePickerWindowV1(bindings,request,window,prepared);
        out.dispatch_invoked=prepared.dispatch_invoked;out.native_call_completed=prepared.native_call_completed;
        if(prepared.reason)return reject(prepared.reason);
      }
    }else if(c.operation!=GrantTitlePickerOperationV1::query){
      if(!first.observation.window_visible||!first.observation.window_binding_verified||!first.observation.rows_complete||
          !SameIds(first.observation.selected_title_full_ids,c.expected_selected_title_full_ids))return reject("fresh_grant_window_selection_changed");
      game::Snapshot dispatch{};if(!game::ReadSnapshot(*c.game,dispatch)||dispatch!=before)return reject("grant_dispatch_frame_changed");
      if(c.operation==GrantTitlePickerOperationV1::select){
        auto row=std::find_if(first.observation.rows.begin(),first.observation.rows.end(),[&](const auto &r){return r.title_full_id==c.title_full_id;});
        if(row==first.observation.rows.end()||row->holder_character_full_id!=static_cast<std::uint32_t>(before.played_character_id)||!row->selectable)return reject("requested_title_not_selectable_owned_row");
        if(row->selected!=c.desired_selected){
          out.dispatch_invoked=true;const auto i=static_cast<std::size_t>(row-first.observation.rows.begin());
          out.native_call_completed=CallVoid(env.module_base+profile->row_toggle,first.items[i]);
          if(!out.native_call_completed)return reject("grant_selection_call_result_unknown_no_retry");
        }
      }else{
        if(c.expected_selected_title_full_ids.empty()||!SameIds(c.requested_title_full_ids,c.expected_selected_title_full_ids)||!first.observation.native_can_send.value_or(false))return reject("native_grant_can_send_false_or_targets_changed");
        // The stock warning dialog must receive its own fresh qualification; no bypass or auto-confirm.
        if(first.observation.warning_confirmation_required.value_or(true))return reject("stock_grant_warning_confirmation_required");
        for(const auto id:c.expected_selected_title_full_ids){GrantTitlePickerHolderV1 h{};if(!Holder(env.module_base,id,h,*profile)||h.holder_character_full_id!=static_cast<std::uint32_t>(before.played_character_id))return reject("selected_title_holder_changed");}
        out.dispatch_invoked=true;out.native_call_completed=CallVoid(env.module_base+profile->send,first.grant);
        if(!out.native_call_completed)return reject("grant_send_call_result_unknown_no_retry");
      }
    }
    // Resolve the current model afresh. Send can close/rebuild a model; old pointers are never reread.
    Pass after{},stable{};game::Snapshot completion{};
    if(!game::ReadSnapshot(*c.game,completion)||(c.operation==GrantTitlePickerOperationV1::send?!Control(before,completion):completion!=before)||
        !ReadPass(c,env,stamp,after,*profile)||!ReadPass(c,env,stamp,stable,*profile)||after!=stable)return reject("grant_completion_state_unavailable_no_retry");
    out.after=after.observation;out.frame_verified=true;
    if(c.operation==GrantTitlePickerOperationV1::query){out.status="observed";return true;}
    if(c.operation==GrantTitlePickerOperationV1::prepare){
      if(!out.after.window_visible||!out.after.window_binding_verified||!out.after.rows_complete)return reject("stock_grant_window_open_not_observed_no_retry");
      out.status="prepared";return true;
    }
    if(c.operation==GrantTitlePickerOperationV1::select){
      auto desired=c.expected_selected_title_full_ids;
      if(c.desired_selected){if(std::find(desired.begin(),desired.end(),c.title_full_id)==desired.end())desired.push_back(c.title_full_id);}
      else desired.erase(std::remove(desired.begin(),desired.end(),c.title_full_id),desired.end());
      out.selection_verified=out.after.rows_complete&&SameIds(out.after.selected_title_full_ids,desired);
      out.status=out.selection_verified?"selection_observed":"selection_changed_observed";return true;
    }
    out.transfer_verified=out.dispatch_invoked&&out.native_call_completed&&!c.expected_selected_title_full_ids.empty();
    for(const auto id:c.expected_selected_title_full_ids){GrantTitlePickerHolderV1 h{};out.transfer_verified=Holder(env.module_base,id,h,*profile)&&h.holder_character_full_id==c.recipient_character_full_id&&out.transfer_verified;}
    out.status=out.transfer_verified?"holder_transfer_observed":"pending";return true;
  }catch(...){out.status="unavailable";out.unavailable_reason="grant_provider_exception_no_retry";return true;}
}

namespace {
const char *Bool(bool b){return b?"true":"false";}
std::string Opt(const std::optional<bool> &b){return b?Bool(*b):"null";}
std::string Id(const std::optional<std::uint32_t> &v){return v?std::to_string(*v):"null";}
std::string VectorIds(const std::vector<std::uint32_t> &v){std::string s="[";for(const auto n:v){if(s.size()>1)s+=',';s+=std::to_string(n);}return s+"]";}
std::string Observation(const GrantTitlePickerObservationV1 &v){
  std::string s="{\"available\":";s+=Bool(v.available);s+=",\"window_visible\":";s+=Bool(v.window_visible);
  s+=",\"window_binding_verified\":";s+=Bool(v.window_binding_verified);s+=",\"rows_complete\":";s+=Bool(v.rows_complete);
  s+=",\"native_can_send\":"+Opt(v.native_can_send)+",\"warning_confirmation_required\":"+Opt(v.warning_confirmation_required);
  s+=",\"selected_title_full_ids\":"+VectorIds(v.selected_title_full_ids)+",\"rows\":[";
  bool comma=false;for(const auto &r:v.rows){if(comma)s+=',';comma=true;s+="{\"title_full_id\":"+std::to_string(r.title_full_id)+",\"holder_character_full_id\":"+Id(r.holder_character_full_id)+",\"selected\":"+Bool(r.selected)+",\"selectable\":"+Bool(r.selectable)+"}";}
  s+="],\"requested_title_holders\":[";comma=false;for(const auto &h:v.requested_title_holders){if(comma)s+=',';comma=true;s+="{\"title_full_id\":"+std::to_string(h.title_full_id)+",\"available\":"+Bool(h.available)+",\"holder_character_full_id\":"+Id(h.holder_character_full_id)+"}";}return s+"]}";
}
}
std::string SerializeGrantTitlePickerV1(const GrantTitlePickerResultV1 &r){
  const auto operation=r.operation==GrantTitlePickerOperationV1::query?"query":r.operation==GrantTitlePickerOperationV1::prepare?"prepare":r.operation==GrantTitlePickerOperationV1::select?"select":"send";
  std::string s="{\"schema\":\"ck3_12003_grant_title_picker_v1\",\"operation\":\"";s+=operation;
  s+="\",\"exact_build\":\""+r.exact_build+"\",\"executable_sha256\":\""+r.executable_sha256;
  s+="\",\"native_revision\":"+std::to_string(r.native_revision)+",\"connection_generation\":"+std::to_string(r.connection_generation)+",\"game_pid\":"+std::to_string(r.game_pid);
  s+=",\"played_character_id\":"+std::to_string(r.played_character_id)+",\"date_raw\":"+std::to_string(r.date_raw)+",\"recipient_character_full_id\":"+std::to_string(r.recipient_character_full_id);
  s+=",\"owner_thread_verified\":";s+=Bool(r.owner_thread_verified);s+=",\"frame_verified\":";s+=Bool(r.frame_verified);s+=",\"source_abi_pins_verified\":";s+=Bool(r.source_abi_pins_verified);
  s+=",\"dispatch_invoked\":";s+=Bool(r.dispatch_invoked);s+=",\"native_call_completed\":";s+=Bool(r.native_call_completed);s+=",\"selection_verified\":";s+=Bool(r.selection_verified);
  s+=",\"transfer_verified\":";s+=Bool(r.transfer_verified);s+=",\"before\":"+Observation(r.before)+",\"after\":"+Observation(r.after);
  return s+",\"status\":\""+r.status+"\",\"unavailable_reason\":\""+r.unavailable_reason+"\",\"business_full_credit\":false}";
}
} // namespace xar::ck3_12003
