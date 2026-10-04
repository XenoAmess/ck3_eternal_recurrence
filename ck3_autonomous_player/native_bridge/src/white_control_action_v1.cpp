#include "xar_bridge/white_control_action_v1.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include <Windows.h>
#include <charconv>
#include <limits>
#include <vector>
namespace xar::ck3_11906 {
namespace {
constexpr auto kRoot="ervc_courtier_creator_window";
constexpr auto kInner="ervc_courtier_creator_modal";

bool Bytes(const void *p,void *out,std::size_t n) noexcept {
  SIZE_T got=0;return p&&out&&n&&ReadProcessMemory(GetCurrentProcess(),p,out,n,&got)&&got==n;
}
template<class T> bool Read(const void *p,std::size_t n,T &out) noexcept {
  const auto a=reinterpret_cast<std::uintptr_t>(p);
  return a&&n<=std::numeric_limits<std::uintptr_t>::max()-a&&Bytes(reinterpret_cast<const void *>(a+n),&out,sizeof(out));
}
bool Pins(std::uintptr_t base) noexcept {
#include "white_control_action_exact_pins_v1.inc"
  return true;
}
bool PushButton(const void *widget,std::uintptr_t base) noexcept {
  const void *vt=nullptr,*col=nullptr,*slot13=nullptr;std::array<std::uint32_t,6> raw{};
  return Read(widget,0,vt)&&reinterpret_cast<std::uintptr_t>(vt)==base+0x49656B8&&
      Read(vt,13*8,slot13)&&reinterpret_cast<std::uintptr_t>(slot13)==base+0x3AA0D40&&
      Bytes(reinterpret_cast<const void *>(base+0x49656B0),&col,sizeof(col))&&
      reinterpret_cast<std::uintptr_t>(col)==base+0x5061978&&Bytes(col,raw.data(),sizeof(raw))&&
      raw[0]==1&&raw[1]==0&&raw[3]==0x55A6870&&raw[5]==0x5061978;
}
bool Path(std::string_view path,std::vector<std::uint32_t> &indices) {
  indices.clear();while(!path.empty()){
    const auto end=path.find('/');const auto part=path.substr(0,end);std::uint32_t n=0;
    const auto value=std::from_chars(part.data(),part.data()+part.size(),n);
    if(part.empty()||value.ec!=std::errc{}||value.ptr!=part.data()+part.size()||n>2048||indices.size()>=64)return false;
    indices.push_back(n);if(end==std::string_view::npos)break;path.remove_prefix(end+1);if(path.empty())return false;
  }return !indices.empty();
}
const NamedGuiWidgetInspectionV1 *Named(const NamedGuiTreeInspectionV1 &tree,std::string_view name) noexcept {
  const NamedGuiWidgetInspectionV1 *match=nullptr;
  for(const auto &row:tree.widgets)if(row.runtime_name==name){if(match)return nullptr;match=&row;}
  return match;
}
const NamedGuiWidgetInspectionV1 *Row(const NamedGuiTreeInspectionV1 &tree,std::string_view path) noexcept {
  const NamedGuiWidgetInspectionV1 *match=nullptr;
  for(const auto &row:tree.widgets)if(row.child_path==path){if(match)return nullptr;match=&row;}
  return match;
}
struct Callback {const void *object=nullptr,*vtable=nullptr,*slot2=nullptr;bool operator==(const Callback &) const=default;};
struct Receiver {
  void *context=nullptr,*owner=nullptr,*root=nullptr,*target=nullptr,*vtable=nullptr;
  const void *callback_data=nullptr;std::int32_t callback_count=0;std::size_t callback_group=0,widget_count=0;
  std::string path;std::vector<Callback> callbacks;
  bool operator==(const Receiver &) const=default;
};
bool Callbacks(Receiver &r,std::uintptr_t base) {
  std::int32_t primary=-1;
  if(!Read(r.target,kZhongguoPrimaryCallbackGroupOffset+kZhongguoCallbackGroupCountOffset,primary)||
      primary<0||primary>kZhongguoMaximumCallbacks)return false;
  r.callback_group=primary?kZhongguoPrimaryCallbackGroupOffset:kZhongguoFallbackCallbackGroupOffset;
  if(!Read(r.target,r.callback_group+kZhongguoCallbackGroupCountOffset,r.callback_count)||
      r.callback_count<=0||r.callback_count>kZhongguoMaximumCallbacks||
      !Read(r.target,r.callback_group+kZhongguoCallbackGroupDataOffset,r.callback_data)||!r.callback_data)return false;
  for(std::int32_t n=0;n<r.callback_count;++n){
    Callback c{};if(!Read(r.callback_data,static_cast<std::size_t>(n)*kZhongguoCallbackStride+kZhongguoCallbackObjectOffset,c.object)||
        !c.object||!Read(c.object,0,c.vtable)||!c.vtable||!Read(c.vtable,kZhongguoCallbackVtableSlot2Offset,c.slot2))return false;
    const auto address=reinterpret_cast<std::uintptr_t>(c.slot2);
    if(address<base||address>=base+kCrozierExactImageSize)return false;r.callbacks.push_back(c);
  }return true;
}
bool ReceiverPass(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    const ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch,const WhiteControlSpecV1 &spec,Receiver &out) {
  ZhongguoScoreboardAccessV1 access{};void *root_widget=nullptr;
  if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,out.context,out.owner)||!out.context||!out.owner||
      !ResolveNamedGuiWidgetV1(env,access,kRoot,kRoot,out.root,root_widget)||!out.root||root_widget!=out.root)return false;
  NamedGuiTreeInspectionV1 tree{};
  if(!InspectNamedGuiSubtreeV1(access,env.module_base,out.root,kRoot,tree)||!tree.root_available||tree.truncated||
      !tree.widget_count||tree.widget_count!=tree.widgets.size())return false;
  const auto *inner=Named(tree,kInner),*target=Named(tree,spec.button);
  if(!inner||inner->child_path!="0"||!inner->effective_visible||!inner->enabled||!target||
      !target->effective_visible||!target->enabled||target->vtable_rva!=0x49656B8||!target->child_path.starts_with("0/"))return false;
  out.widget_count=tree.widget_count;out.path=target->child_path;
  std::vector<std::uint32_t> path;if(!Path(out.path,path))return false;
  void *previous=nullptr;std::string prefix;
  for(std::size_t length=0;length<=path.size();++length){
    const auto *row=Row(tree,prefix);void *root=nullptr,*widget=nullptr,*vt=nullptr,*context=nullptr;
    std::string name;bool visible=false,enabled=false;
    if(!row||!row->effective_visible||!row->enabled||!row->vtable_rva||row->vtable_rva>=kCrozierExactImageSize||
        !ResolveFixedGuiChildPathV1(env,access,kRoot,path.data(),length,root,widget)||root!=out.root||!widget||
        !ReadGuiWidgetRuntimeV1(access,widget,name,vt,visible,enabled)||!visible||!enabled||name!=row->runtime_name||
        reinterpret_cast<std::uintptr_t>(vt)!=env.module_base+row->vtable_rva||
        !Read(widget,kZhongguoWidgetGuiContextOffset,context)||context!=out.context)return false;
    if(previous){const void *parent=nullptr;if(!Read(widget,kZhongguoWidgetParentOffset,parent)||parent!=previous)return false;}
    previous=widget;if(length==path.size()){out.target=widget;out.vtable=vt;break;}
    if(!prefix.empty())prefix+='/';prefix+=std::to_string(path[length]);
  }
  // Includes the existing strict current-modal-descendant guard unchanged.
  return PushButton(out.target,env.module_base)&&Callbacks(out,env.module_base)&&
      InspectFixedGuiWidgetDispatchAdmissionV1(dispatch,out.target,out.vtable);
}
bool BeforeValues(WhiteControlActionContextV1 &query,MainThreadQueryMailboxV1 &mailbox,
    const MainThreadExecutionStampV1 &stamp,const ZhongguoScoreboardNativeEnvironmentV1 &env,const WhiteControlSpecV1 &spec) {
  WhitePlayerBusinessVariablesContextV1 business{};business.game=query.game;business.expected_snapshot=query.expected_snapshot;
  business.native_revision=query.native_revision;business.connection_generation=query.connection_generation;
  WhiteRenderedTextContextV1 text{};text.game=query.game;text.expected_snapshot=query.expected_snapshot;
  text.native_revision=query.native_revision;text.connection_generation=query.connection_generation;
  return ExecuteWhitePlayerBusinessVariablesV1(business,mailbox,stamp)&&business.result.available&&
      business.result.all_eight_numeric_integers&&business.result.fields[spec.variable_index].integer_value==(spec.legacy_age?query.expected_before_age:query.expected_before_value)&&
      ExecuteWhiteRenderedTextV1(text,mailbox,stamp,env)&&text.result.available&&
      text.result.fields[spec.text_index].text_utf8==std::to_string(spec.legacy_age?query.expected_before_age:query.expected_before_value)&&
      (spec.legacy_age||text.result.fields[7].text_utf8==query.expected_before_price_text);
}
bool CurrentFrame(WhiteControlActionContextV1 &query,MainThreadQueryMailboxV1 &mailbox,
    const MainThreadExecutionStampV1 &stamp,const ZhongguoScoreboardNativeEnvironmentV1 &env) noexcept {
  game::Snapshot actual{};std::int32_t actor=-1;const void *logical=nullptr;
  return query.game&&game::ReadSnapshot(*query.game,actual)&&actual==query.expected_snapshot&&actual.paused&&actual.map_ready&&
      actual.has_played_character&&actual.played_character_alive&&actual.played_character_id>0&&!actual.has_active_event&&actual.date_raw==stamp.date_raw&&
      IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId())&&
      Bytes(reinterpret_cast<const void *>(env.module_base+0x54DBC00),&actor,sizeof(actor))&&actor==actual.played_character_id&&
      Bytes(reinterpret_cast<const void *>(env.module_base+0x5C6A520),&logical,sizeof(logical))&&stamp.jomini_state&&
      reinterpret_cast<std::uintptr_t>(logical)==stamp.jomini_state;
}
}
bool ExecuteWhiteControlActionV1(WhiteControlActionContextV1 &query,MainThreadQueryMailboxV1 &mailbox,
    const MainThreadExecutionStampV1 &stamp,const ZhongguoScoreboardNativeEnvironmentV1 &env,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch) noexcept {
  auto &out=query.result;out={};out.game_pid=GetCurrentProcessId();out.native_revision=query.native_revision;
  out.connection_generation=query.connection_generation;out.expected_before_age=query.expected_before_age;
  try {
    const auto reject=[&](const char *why){out.available=false;out.unavailable_reason=why;return true;};
    const auto *spec=FindWhiteControlSpecV1(query.control);
    if(!spec)return reject("fixed_white_control_not_allowlisted");
    const auto before=spec->legacy_age?query.expected_before_age:query.expected_before_value;
    out.control=std::string(spec->control);out.expected_before_value=before;
    if(!query.game||query.game->descriptor().game_version!="1.20.0.3"||
        query.game->descriptor().executable_sha256!="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"||
        !query.native_revision||!query.connection_generation||before<0||before>=spec->maximum||
        (!spec->legacy_age&&(query.expected_before_price_text.empty()||query.expected_before_price_text.size()>2048||query.expected_before_price_text.find('\0')!=std::string::npos))||
        !env.module_base||!env.exact_build_admitted||env.offline_fixture_function_overrides||env.gui_abi_revision!=GuiAbiRevisionV1::crozier12003||
        dispatch.module_base!=env.module_base||!dispatch.exact_build_admitted||dispatch.offline_fixture_function_overrides||dispatch.gui_abi_revision!=GuiAbiRevisionV1::crozier12003)
      return reject("exact_12003_fixed_white_action_admission_failed");
    if(!CurrentFrame(query,mailbox,stamp,env))return reject("actual_alive_paused_noevent_player_frame_unverified");
    out.played_character_id=query.expected_snapshot.played_character_id;out.date_raw=query.expected_snapshot.date_raw;
    if(!Pins(env.module_base))return reject("loaded_12003_fixed_click_pins_changed");out.source_abi_pins_verified=true;
    if(!BeforeValues(query,mailbox,stamp,env,*spec))return reject("actual_white_age_business_and_text_before_mismatch");
    out.before_price_bound=!spec->legacy_age;
    Receiver first{},second{};
    if(!ReceiverPass(env,dispatch,*spec,first)||!ReceiverPass(env,dispatch,*spec,second)||first!=second)return reject("actual_fixed_white_receiver_or_callbacks_unstable");
    out.receiver_qualified=true;out.target_child_path=first.path;
    if(!CurrentFrame(query,mailbox,stamp,env)||!BeforeValues(query,mailbox,stamp,env,*spec))return reject("actual_white_predispatch_frame_or_before_changed");
    Receiver last{};
    if(!ReceiverPass(env,dispatch,*spec,last)||last!=first)return reject("actual_fixed_white_predispatch_receiver_changed");
    out.dispatch_attempted=true; // Consumed before the callback; faults never license another invocation.
    out.dispatch_invoked=DispatchFixedGuiWidgetNativeV1(&dispatch,game::ZhongguoScoreboardActionV1::open,last.target,last.vtable,out.native_handled);
    if(!out.dispatch_invoked)return reject("native_white_dispatch_failed_result_unknown_no_retry");
    Receiver after{};out.native_after_read=ReceiverPass(env,dispatch,*spec,after);
    out.gui_owner_binding_verified=out.native_after_read&&after.context==first.context&&after.owner==first.owner&&after.root==first.root;
    out.frame_verified=CurrentFrame(query,mailbox,stamp,env);
    if(!out.gui_owner_binding_verified||!out.frame_verified)return reject("native_white_completion_owner_or_frame_changed_no_retry");
    out.available=true;return true;
  }catch(...){out.available=false;out.unavailable_reason="native_white_action_exception_result_unknown_no_retry";return true;}
}
std::string SerializeWhiteControlActionV1(const WhiteControlActionResultV1 &v) {
  const bool legacy=v.control=="age_plus_1";
  std::string s="{\"schema\":\"ck3-native-white-control-action-v1\",\"step\":\"";
  s+=legacy?std::string(kWhiteControlActionV1Step):std::string(kWhiteNumericControlActionV1Step);
  s+="\",\"control\":\""+v.control+"\",\"read_only\":false,\"selected_down_available\":false,\"postcondition_verified\":false";
  const auto number=[&](const char *key,auto n){s+=",\""+std::string(key)+"\":"+std::to_string(n);};
  const auto boolean=[&](const char *key,bool b){s+=",\""+std::string(key)+"\":"+(b?"true":"false");};
  number("game_pid",v.game_pid);number("native_revision",v.native_revision);number("connection_generation",v.connection_generation);
  number("played_character_id",v.played_character_id);number("date_raw",v.date_raw);
  if(legacy)number("expected_before_age",v.expected_before_age);
  else {number("expected_before_value",v.expected_before_value);boolean("before_price_bound",v.before_price_bound);}
  boolean("available",v.available);boolean("source_abi_pins_verified",v.source_abi_pins_verified);boolean("receiver_qualified",v.receiver_qualified);
  boolean("gui_owner_binding_verified",v.gui_owner_binding_verified);boolean("frame_verified",v.frame_verified);
  boolean("dispatch_attempted",v.dispatch_attempted);boolean("dispatch_invoked",v.dispatch_invoked);boolean("native_handled",v.native_handled);boolean("native_after_read",v.native_after_read);
  return s+",\"target_child_path\":\""+v.target_child_path+"\",\"unavailable_reason\":\""+v.unavailable_reason+"\"}";
}
}
