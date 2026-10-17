#include "xar_bridge/military_reinforcement_action_12004.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include "xar_bridge/ingame_private_gui_profile_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <windows.h>
#include <array>
#include <charconv>
#include <limits>
#include <vector>

namespace xar::ck3_11906 {
namespace {
#if XAR_ENABLE_FIXED_MILITARY_REINFORCEMENT_ACTION_12004
struct CodePin { std::uintptr_t rva; std::array<unsigned char,32> bytes; };
constexpr CodePin kPins[]{
  {0x3AAB0E0,{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x81,0xd0,0x00,0x00,0x00,0x48,0x8b,0xfa,0x48,0x8b}},
  {0x3ABC4B0,{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x60,0x49,0x8b,0xf0,0x8b,0xea,0x48,0x8b,0xf9,0x49,0x8b,0x59,0x48}},
  {0x3A78210,{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xf1,0x48,0x8b,0xea,0x48,0x8b,0x89,0xf0,0x00,0x00}},
  {0x3AA0D20,{0x40,0x53,0x48,0x83,0xec,0x20,0x48,0x8b,0xd9,0x0f,0xb6,0x89,0xd0,0x00,0x00,0x00,0x80,0xe1,0x02,0x74,0x26,0x44,0x8b,0x42,0x10,0x41,0x83,0xe8,0x0d,0x74,0x0c,0x41}},
};
template<class T> bool ReadAt(void *object,std::size_t offset,T &out) noexcept {
  if (!object || reinterpret_cast<std::uintptr_t>(object) > std::numeric_limits<std::uintptr_t>::max()-offset) return false;
  SIZE_T got=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void *>(reinterpret_cast<std::uintptr_t>(object)+offset),&out,sizeof(out),&got)&&got==sizeof(out);
}
bool PinsMatch(const ZhongguoScoreboardNativeEnvironmentV1 &env) noexcept {
  if (!env.exact_build_admitted || env.offline_fixture_function_overrides ||
      (env.gui_abi_revision!=GuiAbiRevisionV1::crozier12004 || env.executable_sha256!=ck3_12004::kExecutableSha256)) return false;
  const std::array<std::uintptr_t,4> rvas{GuiFindTopLevelWidgetRvaV1(env.gui_abi_revision),
      GuiShortcutManagerActivateRvaV1(env.gui_abi_revision),GuiStrictDescendantRvaV1(env.gui_abi_revision),
      GuiButtonBaseSlot13RvaV1(env.gui_abi_revision)};
  for (std::size_t i=0;i<std::size(kPins);++i) {
    const auto &pin=kPins[i];
    std::array<unsigned char,32> actual{};SIZE_T got=0;
    if(!ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void *>(env.module_base+rvas[i]),actual.data(),actual.size(),&got)||got!=actual.size()||actual!=pin.bytes)return false;
  }
  return true;
}
bool ParsePath(std::string_view text,std::vector<std::uint32_t> &path) {
  path.clear();if(text.empty())return true;
  while(!text.empty()) {
    if(path.size()>=64)return false;
    const auto sep=text.find('/');auto token=text.substr(0,sep);std::uint32_t index=0;
    const auto parsed=std::from_chars(token.data(),token.data()+token.size(),index);
    if(token.empty()||parsed.ec!=std::errc{}||parsed.ptr!=token.data()+token.size()||index>=2048)return false;
    path.push_back(index);if(sep==std::string_view::npos)break;
    text.remove_prefix(sep+1);if(text.empty())return false;
  }
  return true;
}
const NamedGuiWidgetInspectionV1 *Row(const NamedGuiTreeInspectionV1 &tree,std::string_view path) noexcept {
  const NamedGuiWidgetInspectionV1 *found=nullptr;
  for(const auto &row:tree.widgets)if(row.child_path==path){if(found)return nullptr;found=&row;}
  return found;
}

bool ReadMilitarySource(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    std::int32_t actor,void *&root,NamedGuiTreeInspectionV1 &tree,
    MilitaryReinforcementSource12004 &source) {
  ZhongguoScoreboardAccessV1 access{};void *widget=nullptr;root=nullptr;tree={};
  if(!ResolveNamedGuiWidgetV1(env,access,"military_view","military_view",root,widget)||
      !root||root!=widget||!InspectNamedGuiSubtreeV1(access,env.module_base,root,
          "military_view",tree,true,true))return false;
  const auto *row=Row(tree,"");
  return row&&row->runtime_name=="military_view"&&row->effective_visible&&row->enabled&&
      SelectMilitaryReinforcementSource12004(tree,actor,source);
}
bool ResolveCurrentSourceWidget(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    const NamedGuiTreeInspectionV1 &tree,void *expected_root,void *expected_context,
    const std::string &target_path,void *&target,void *&vtable) {
  target=nullptr;vtable=nullptr;
  std::vector<std::uint32_t> indices;if(!ParsePath(target_path,indices)||indices.empty())return false;
  ZhongguoScoreboardAccessV1 access{};void *previous=nullptr;std::string prefix;
  for(std::size_t length=0;length<=indices.size();++length) {
    void *root=nullptr,*widget=nullptr;
    if(!ResolveFixedGuiChildPathV1(env,access,"military_view",indices.data(),length,root,widget)||root!=expected_root||!widget)return false;
    const auto *row=Row(tree,prefix);std::string name;void *actual_vtable=nullptr;bool visible=false,enabled=false;
    void *widget_context=nullptr;
    if(!row||row->vtable_rva==0||row->vtable_rva>=GuiExactImageSizeV1(env.gui_abi_revision)||!ReadGuiWidgetRuntimeV1(access,widget,name,actual_vtable,visible,enabled)||!visible||!enabled||name!=row->runtime_name||reinterpret_cast<std::uintptr_t>(actual_vtable)!=env.module_base+row->vtable_rva||!ReadAt(widget,kZhongguoWidgetGuiContextOffset,widget_context)||widget_context!=expected_context)return false;
    if(previous){void *parent=nullptr;if(!ReadAt(widget,kZhongguoWidgetParentOffset,parent)||parent!=previous)return false;}
    previous=widget;if(length==indices.size()){target=widget;vtable=actual_vtable;break;}
    if(!prefix.empty())prefix+='/';prefix+=std::to_string(indices[length]);
  }
  return target!=nullptr;
}
#endif
} // namespace

bool ExecuteMilitaryReinforcementAction12004(MilitaryReinforcementActionContext12004 &query,
    MainThreadQueryMailboxV1 &mailbox,const MainThreadExecutionStampV1 &stamp,
    const ZhongguoScoreboardNativeEnvironmentV1 &env,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch) noexcept {
  auto &out=query.result;out={};out.desired_enabled=query.desired_enabled;
  out.native_revision=query.native_revision;out.connection_generation=query.connection_generation;
  out.game_pid=GetCurrentProcessId();
#if !XAR_ENABLE_FIXED_MILITARY_REINFORCEMENT_ACTION_12004
  (void)mailbox;(void)stamp;(void)env;(void)dispatch;
  out.unavailable_reason="fixed_military_reinforcement_action_disabled";return true;
#else
  try {
    const auto reject=[&](const char *why){out.unavailable_reason=why;return true;};
    if(!query.game||query.native_revision==0||query.connection_generation==0)
      return reject("exact_crozier_request_unavailable");
    const auto &descriptor=query.game->descriptor();
    if(descriptor.game_version!=ck3_12004::kGameVersion||descriptor.executable_sha256!=ck3_12004::kExecutableSha256||
        !IngamePrivateGuiIdentityAdmittedV1(descriptor.game_version,descriptor.executable_sha256,env.gui_abi_revision)||
        dispatch.gui_abi_revision!=env.gui_abi_revision)return reject("exact_crozier_request_unavailable");
    out.game_version=descriptor.game_version;out.executable_sha256=descriptor.executable_sha256;
    if(!IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()))
      return reject("paused_application_owner_unverified");
    out.owner_thread_verified=true;game::Snapshot before{};
    if(!game::ReadSnapshot(*query.game,before)||before!=query.expected_snapshot||!before.paused||!before.map_ready||
        !before.has_played_character||!before.played_character_alive||before.played_character_id<=0||
        before.date_raw!=stamp.date_raw)return reject("fresh_alive_paused_frame_unverified");
    out.played_character_id=before.played_character_id;out.date_raw=before.date_raw;
    if(!PinsMatch(env))return reject("loaded_crozier_gui_code_pins_changed");
    out.source_abi_pins_verified=true;
    ZhongguoScoreboardAccessV1 access{};void *context=nullptr,*owner=nullptr;
    if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,context,owner))
      return reject("gui_owner_unavailable");
    void *root=nullptr;NamedGuiTreeInspectionV1 tree{};MilitaryReinforcementSource12004 source{};
    if(!ReadMilitarySource(env,before.played_character_id,root,tree,source))
      return reject("visible_refill_source_or_owner_switch_unavailable");
    out.current_tree_complete=true;out.source_profile_verified=true;
    out.source_child_path=source.child_path;out.before_switch=source.owner_switch;
    void *target=nullptr,*vtable=nullptr;
    if(!ResolveCurrentSourceWidget(env,tree,root,context,source.child_path,target,vtable)||
        !InspectFixedGuiWidgetDispatchAdmissionV1(dispatch,target,vtable))
      return reject("refill_widget_slot13_or_modal_unqualified");
    out.no_blocking_modal_verified=true;
    game::Snapshot predispatch{};void *current_context=nullptr,*current_owner=nullptr;
    if(!game::ReadSnapshot(*query.game,predispatch)||predispatch!=before||
        !ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,current_context,current_owner)||
        current_context!=context||current_owner!=owner)return reject("predispatch_binding_changed");
    out.frame_verified=true;out.gui_owner_binding_verified=true;out.accepted=true;
    ApplyMilitaryReinforcementDecision12004(source,query.desired_enabled,[&](bool &handled){
      return DispatchFixedGuiWidgetNativeV1(&dispatch,game::ZhongguoScoreboardActionV1::open,target,vtable,handled);
    },out);
    // A new resolution/census is diagnostic. Only the caller's later independent
    // same-owner read can publish a verified switch; native_handled is no proof.
    void *after_root=nullptr;NamedGuiTreeInspectionV1 after_tree{};MilitaryReinforcementSource12004 after_source{};
    out.native_after_tree_complete=ReadMilitarySource(env,before.played_character_id,after_root,after_tree,after_source);
    if(out.native_after_tree_complete) {
      out.native_after_switch=after_source.owner_switch;
      out.before_after_same_source=after_source.child_path==source.child_path&&
          after_source.vtable_rva==source.vtable_rva&&after_source.owner_switch.owner_full_id==source.owner_switch.owner_full_id;
    }
    game::Snapshot after{};void *after_context=nullptr,*after_owner=nullptr;
    out.gui_owner_binding_verified=ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,after_context,after_owner)&&
        after_context==context&&after_owner==owner;
    out.frame_verified=game::ReadSnapshot(*query.game,after)&&after==before;
    if(!out.frame_verified||!out.gui_owner_binding_verified) {
      out.status="unavailable";out.unavailable_reason="post_dispatch_binding_changed_no_retry";
    }
    return true;
  }catch(...){out.status="unavailable";out.unavailable_reason="native_action_exception_no_retry";return true;}
#endif
}

std::string SerializeMilitaryReinforcementAction12004(const MilitaryReinforcementResult12004 &v) {
  const auto text=[](std::string &s,std::string_view value){s+='"';for(const auto ch:value){
    if(ch=='"'||ch=='\\')s+='\\';s+=ch;}s+='"';};
  std::string s="{";
  const auto str=[&](const char *key,std::string_view value){if(s.size()>1)s+=',';text(s,key);s+=':';text(s,value);};
  const auto number=[&](const char *key,auto value){if(s.size()>1)s+=',';text(s,key);s+=':';s+=std::to_string(value);};
  const auto boolean=[&](const char *key,bool value){if(s.size()>1)s+=',';text(s,key);s+=value?":true":":false";};
  str("schema","ck3-military-reinforcement-set-12004-v1");
  str("step",v.desired_enabled?kMilitaryReinforcementEnable12004Step:kMilitaryReinforcementDisable12004Step);
  str("game_version",v.game_version);str("executable_sha256",v.executable_sha256);
  str("source_gui_sha256",kMilitaryReinforcementSourceGuiSha12004);str("source_child_path",v.source_child_path);
  str("status",v.status);if(v.unavailable_reason.empty())s+=",\"unavailable_reason\":null";else str("unavailable_reason",v.unavailable_reason);
  number("native_revision",v.native_revision);number("connection_generation",v.connection_generation);number("game_pid",v.game_pid);
  number("played_character_id",v.played_character_id);number("date_raw",v.date_raw);
  boolean("accepted",v.accepted);boolean("desired_enabled",v.desired_enabled);
  boolean("owner_thread_verified",v.owner_thread_verified);boolean("frame_verified",v.frame_verified);
  boolean("source_abi_pins_verified",v.source_abi_pins_verified);boolean("gui_owner_binding_verified",v.gui_owner_binding_verified);
  boolean("source_profile_verified",v.source_profile_verified);boolean("current_tree_complete",v.current_tree_complete);
  boolean("no_blocking_modal_verified",v.no_blocking_modal_verified);
  boolean("dispatch_attempted",v.dispatch_attempted);boolean("dispatch_invoked",v.dispatch_invoked);boolean("native_handled",v.native_handled);
  boolean("postcondition_verified",false);boolean("verification_pending",true);
  boolean("current_variable_table_observed",false);boolean("native_receiver_selected",false);boolean("provider_invoked",false);
  boolean("native_after_tree_complete",v.native_after_tree_complete);boolean("before_after_same_source",v.before_after_same_source);
  s+=",\"before_switch\":";game::AppendGuiRefillStaticOwnerSwitch12004(s,v.before_switch,text);
  s+=",\"native_after_switch\":";if(v.native_after_switch)game::AppendGuiRefillStaticOwnerSwitch12004(s,*v.native_after_switch,text);else s+="null";
  return s+'}';
}
} // namespace xar::ck3_11906
