#include "xar_bridge/ingame_decisions_opener_v1.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include <windows.h>
#include <array>
#include <charconv>
#include <cstring>
#include <limits>
#include <vector>

namespace xar::ck3_11906 {
namespace {
// Bytes read from the installed exact .3 image, not an inherited .2/.19 pin.
struct CodePin { std::uintptr_t rva; std::array<unsigned char,32> bytes; };
constexpr CodePin kPins[]{
  {0x3AAB100,{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x81,0xd0,0x00,0x00,0x00,0x48,0x8b,0xfa,0x48,0x8b}},
  {0x3ABC4D0,{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x60,0x49,0x8b,0xf0,0x8b,0xea,0x48,0x8b,0xf9,0x49,0x8b,0x59,0x48}},
  {0x3A78230,{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xf1,0x48,0x8b,0xea,0x48,0x8b,0x89,0xf0,0x00,0x00}},
  {0x3AA0D40,{0x40,0x53,0x48,0x83,0xec,0x20,0x48,0x8b,0xd9,0x0f,0xb6,0x89,0xd0,0x00,0x00,0x00,0x80,0xe1,0x02,0x74,0x26,0x44,0x8b,0x42,0x10,0x41,0x83,0xe8,0x0d,0x74,0x0c,0x41}},
};
template<class T> bool ReadAt(void *object,std::size_t offset,T &out) noexcept {
  if (!object || reinterpret_cast<std::uintptr_t>(object) > std::numeric_limits<std::uintptr_t>::max()-offset) return false;
  SIZE_T got=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void *>(reinterpret_cast<std::uintptr_t>(object)+offset),&out,sizeof(out),&got)&&got==sizeof(out);
}
bool PinsMatch(const ZhongguoScoreboardNativeEnvironmentV1 &env) noexcept {
  if (!env.exact_build_admitted || env.offline_fixture_function_overrides || env.gui_abi_revision!=GuiAbiRevisionV1::crozier12003) return false;
  for (const auto &pin:kPins) {
    std::array<unsigned char,32> actual{};SIZE_T got=0;
    if(!ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void *>(env.module_base+pin.rva),actual.data(),actual.size(),&got)||got!=actual.size()||actual!=pin.bytes)return false;
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
bool InspectRoot(const ZhongguoScoreboardNativeEnvironmentV1 &env,std::string_view name,void *&root,NamedGuiTreeInspectionV1 &tree,bool &visible) noexcept {
  ZhongguoScoreboardAccessV1 access{};void *widget=nullptr;root=nullptr;tree={};visible=false;
  if(!ResolveNamedGuiWidgetV1(env,access,name,name,root,widget))return false;
  if(root==nullptr)return widget==nullptr;
  if(widget!=root||!InspectNamedGuiSubtreeV1(access,env.module_base,root,name,tree)||tree.truncated||tree.widget_count==0||tree.widget_count!=tree.widgets.size())return false;
  const auto *row=Row(tree,"");if(!row||row->runtime_name!=name)return false;
  visible=row->effective_visible;return true;
}
// Path comes only from this fresh native census. HUD source proves the named
// tab container has one direct button_normal child containing maintab_button.
bool ResolveReceiver(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    const NamedGuiTreeInspectionV1 &tree,void *expected_root,void *expected_context,
    void *&target,void *&vtable,std::string &target_path) {
  target=nullptr;vtable=nullptr;const NamedGuiWidgetInspectionV1 *tab=nullptr;
  for(const auto &row:tree.widgets)if(row.runtime_name=="tab_decisions"){if(tab)return false;tab=&row;}
  if(!tab||!tab->effective_visible||!tab->enabled||tab->child_count!=1)return false;
  target_path=tab->child_path.empty()?"0":tab->child_path+"/0";
  const auto *button=Row(tree,target_path);
  if(!button||!button->runtime_name.empty()||!button->effective_visible||!button->enabled)return false;
  std::vector<std::uint32_t> indices;if(!ParsePath(target_path,indices)||indices.empty())return false;
  ZhongguoScoreboardAccessV1 access{};void *previous=nullptr;std::string prefix;
  for(std::size_t length=0;length<=indices.size();++length) {
    void *root=nullptr,*widget=nullptr;
    if(!ResolveFixedGuiChildPathV1(env,access,"ingame_topbar",indices.data(),length,root,widget)||root!=expected_root||!widget)return false;
    const auto *row=Row(tree,prefix);std::string name;void *actual_vtable=nullptr;bool visible=false,enabled=false;
    void *widget_context=nullptr;
    if(!row||row->vtable_rva==0||row->vtable_rva>=GuiExactImageSizeV1(env.gui_abi_revision)||!ReadGuiWidgetRuntimeV1(access,widget,name,actual_vtable,visible,enabled)||!visible||!enabled||name!=row->runtime_name||reinterpret_cast<std::uintptr_t>(actual_vtable)!=env.module_base+row->vtable_rva||!ReadAt(widget,kZhongguoWidgetGuiContextOffset,widget_context)||widget_context!=expected_context)return false;
    if(previous){void *parent=nullptr;if(!ReadAt(widget,kZhongguoWidgetParentOffset,parent)||parent!=previous)return false;}
    previous=widget;if(length==indices.size()){target=widget;vtable=actual_vtable;break;}
    if(!prefix.empty())prefix+='/';prefix+=std::to_string(indices[length]);
  }
  return target!=nullptr;
}
} // namespace

bool ExecuteIngameDecisionsOpenV1(IngameDecisionsOpenContextV1 &query,
    MainThreadQueryMailboxV1 &mailbox,const MainThreadExecutionStampV1 &stamp,
    const ZhongguoScoreboardNativeEnvironmentV1 &env,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch) noexcept {
  auto &out=query.result;out={};out.native_revision=query.native_revision;out.connection_generation=query.connection_generation;out.game_pid=GetCurrentProcessId();
  try {
    const auto reject=[&](const char *why){out.unavailable_reason=why;return true;};
    if(!query.game||query.game->descriptor().game_version!="1.20.0.3"||query.game->descriptor().executable_sha256!="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"||query.native_revision==0||query.connection_generation==0)return reject("exact_12003_request_unavailable");
    if(!IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()))return reject("paused_application_owner_unverified");
    out.owner_thread_verified=true;game::Snapshot before{};
    if(!game::ReadSnapshot(*query.game,before)||before!=query.expected_snapshot||!before.paused||!before.map_ready||!before.has_played_character||!before.played_character_alive||before.played_character_id<=0||before.date_raw!=stamp.date_raw)return reject("fresh_alive_paused_frame_unverified");
    out.played_character_id=before.played_character_id;out.date_raw=before.date_raw;
    if(!PinsMatch(env)||dispatch.gui_abi_revision!=GuiAbiRevisionV1::crozier12003)return reject("loaded_12003_gui_code_pins_changed");out.source_abi_pins_verified=true;
    ZhongguoScoreboardAccessV1 access{};void *context=nullptr,*owner=nullptr;
    if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,context,owner))return reject("gui_owner_unavailable");
    void *decisions_before=nullptr;NamedGuiTreeInspectionV1 initial{};
    if(!InspectRoot(env,"decisions_view",decisions_before,initial,out.before_visible))return reject("decisions_before_census_incomplete");
    if(!out.before_visible) {
      void *topbar=nullptr;NamedGuiTreeInspectionV1 tree{};bool visible=false;
      if(!InspectRoot(env,"ingame_topbar",topbar,tree,visible)||!topbar||!visible)return reject("topbar_census_incomplete_or_hidden");
      out.topbar_tree_complete=true;out.topbar_widget_count=tree.widget_count;
      void *target=nullptr,*vtable=nullptr;
      if(!ResolveReceiver(env,tree,topbar,context,target,vtable,out.target_child_path)||!InspectFixedGuiWidgetDispatchAdmissionV1(dispatch,target,vtable))return reject("decisions_button_receiver_unqualified");
      out.receiver_qualified=true;
      // Revalidate frame/owner immediately before the one ToggleGameView call.
      game::Snapshot predispatch{};void *current_context=nullptr,*current_owner=nullptr;
      if(!game::ReadSnapshot(*query.game,predispatch)||predispatch!=before||!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,current_context,current_owner)||current_context!=context||current_owner!=owner)return reject("predispatch_binding_changed");
      out.dispatch_invoked=DispatchFixedGuiWidgetNativeV1(&dispatch,game::ZhongguoScoreboardActionV1::open,target,vtable,out.native_handled);
      if(!out.dispatch_invoked)return reject("native_shortcut_dispatch_failed");
    }
    // Separate resolution/traversal after dispatch; never reuse the HUD tree.
    void *decisions_after=nullptr;NamedGuiTreeInspectionV1 after_tree{};
    out.native_after_read=InspectRoot(env,"decisions_view",decisions_after,after_tree,out.native_after_visible);
    out.native_after_tree_complete=out.native_after_read&&after_tree.root_available&&!after_tree.truncated;
    out.after_widget_count=after_tree.widget_count;
    void *after_context=nullptr,*after_owner=nullptr;game::Snapshot after{};
    out.gui_owner_binding_verified=ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,after_context,after_owner)&&after_context==context&&after_owner==owner;
    out.frame_verified=game::ReadSnapshot(*query.game,after)&&after==before;
    out.postcondition_verified=out.native_after_tree_complete&&out.native_after_visible&&out.gui_owner_binding_verified&&out.frame_verified;
    out.status=out.postcondition_verified?"observed_visible":out.dispatch_invoked?"acknowledged_verification_pending":"unavailable";
    if(!out.native_after_read)out.unavailable_reason="native_after_census_incomplete";
    else if(!out.frame_verified||!out.gui_owner_binding_verified)out.unavailable_reason="post_dispatch_binding_changed";
    return true;
  }catch(...){out.postcondition_verified=false;out.unavailable_reason="native_provider_exception";return true;}
}

std::string SerializeIngameDecisionsOpenV1(const IngameDecisionsOpenResultV1 &v) {
  std::string s="{\"schema\":\"ck3-ingame-decisions-open-v1\",\"step\":\"activate-ingame-decisions-v1\",\"game_version\":\"1.20.0.3\",\"executable_sha256\":\"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6\"";
  const auto number=[&](const char *k,auto n){s+=",\"";s+=k;s+="\":";s+=std::to_string(n);};
  const auto boolean=[&](const char *k,bool b){s+=",\"";s+=k;s+="\":";s+=b?"true":"false";};
  const auto text=[&](const char *k,const std::string &t){s+=",\"";s+=k;s+="\":\"";s+=t;s+='"';};
  number("native_revision",v.native_revision);number("connection_generation",v.connection_generation);number("game_pid",v.game_pid);number("played_character_id",v.played_character_id);number("date_raw",v.date_raw);
  number("topbar_widget_count",v.topbar_widget_count);number("after_widget_count",v.after_widget_count);
  boolean("owner_thread_verified",v.owner_thread_verified);boolean("frame_verified",v.frame_verified);boolean("source_abi_pins_verified",v.source_abi_pins_verified);boolean("gui_owner_binding_verified",v.gui_owner_binding_verified);
  boolean("topbar_tree_complete",v.topbar_tree_complete);boolean("receiver_qualified",v.receiver_qualified);boolean("before_visible",v.before_visible);boolean("dispatch_invoked",v.dispatch_invoked);boolean("native_handled",v.native_handled);
  boolean("native_after_read",v.native_after_read);boolean("native_after_visible",v.native_after_visible);boolean("native_after_tree_complete",v.native_after_tree_complete);boolean("postcondition_verified",v.postcondition_verified);
  boolean("verification_pending",v.dispatch_invoked&&!v.postcondition_verified);text("target_child_path",v.target_child_path);text("status",v.status);text("unavailable_reason",v.unavailable_reason);return s+'}';
}
} // namespace xar::ck3_11906
