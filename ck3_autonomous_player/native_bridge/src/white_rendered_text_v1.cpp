#include "xar_bridge/white_rendered_text_v1.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
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
const void *At(const void *p,std::size_t n) noexcept {
  const auto value=reinterpret_cast<std::uintptr_t>(p);
  return value&&n<=std::numeric_limits<std::uintptr_t>::max()-value?reinterpret_cast<const void *>(value+n):nullptr;
}
template<class T> bool Read(const void *p,std::size_t n,T &out) noexcept {return Bytes(At(p,n),&out,sizeof(out));}
bool Textbox(const void *widget,std::uintptr_t base) noexcept {
  // Installed .3 CPdxGuiTextbox: actual R11/R12 vtable + exact .3 RTTI.
  const void *vt=nullptr,*col=nullptr,*get=nullptr;std::array<std::uint32_t,6> raw{};
  return Read(widget,0,vt)&&reinterpret_cast<std::uintptr_t>(vt)==base+0x497B828&&
      Read(vt,66*8,get)&&reinterpret_cast<std::uintptr_t>(get)==base+0x1042240&&
      Bytes(reinterpret_cast<const void *>(base+0x497B820),&col,sizeof(col))&&
      reinterpret_cast<std::uintptr_t>(col)==base+0x50821A8&&Bytes(col,raw.data(),sizeof(raw))&&
      raw[0]==1&&raw[1]==0&&raw[3]==0x55BD330&&raw[5]==0x50821A8;
}
bool Pins(std::uintptr_t base) noexcept {
  constexpr std::array<unsigned char,8> getter{0x48,0x8D,0x81,0x90,0x03,0x00,0x00,0xC3};
  constexpr std::array<unsigned char,32> find{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x81,0xd0,0x00,0x00,0x00,0x48,0x8b,0xfa,0x48,0x8b};
  std::array<unsigned char,8> a{};std::array<unsigned char,32> b{};
  return Bytes(reinterpret_cast<const void *>(base+0x1042240),a.data(),a.size())&&a==getter&&
      Bytes(reinterpret_cast<const void *>(base+0x3AAB100),b.data(),b.size())&&b==find;
}
bool ActualText(const void *widget,std::string &out) {
  // Slot66 returns this+390; slot67/69 consume that same UTF-8 std::string.
  // Read the actual widget cache, without calling the game or evaluating script.
  const void *header=At(widget,0x390),*data=header;std::uint64_t size=0,capacity=0;
  std::array<char,2049> raw{};
  if(!Read(header,0x10,size)||!Read(header,0x18,capacity)||size>2048||size>capacity||
      (capacity<16&&capacity!=15)||(capacity>=16&&(!Read(header,0,data)||!data))||
      !Bytes(data,raw.data(),static_cast<std::size_t>(size)+1)||raw[size]!=0)return false;
  out.assign(raw.data(),static_cast<std::size_t>(size));
  return out.find('\0')==std::string::npos&&(out.empty()||
      MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,out.data(),static_cast<int>(out.size()),nullptr,0)>0);
}
bool Path(std::string_view path,std::vector<std::uint32_t> &indices) {
  indices.clear();while(!path.empty()){
    const auto end=path.find('/');const auto part=path.substr(0,end);std::uint32_t n=0;
    const auto converted=std::from_chars(part.data(),part.data()+part.size(),n);
    if(part.empty()||converted.ec!=std::errc{}||converted.ptr!=part.data()+part.size()||n>2048||indices.size()>=64)return false;
    indices.push_back(n);if(end==std::string_view::npos)break;path.remove_prefix(end+1);
  }return !indices.empty();
}
bool Ancestors(const void *widget,const void *root,const void *context) noexcept {
  for(std::size_t n=0;n<64&&widget;++n){
    const void *current_context=nullptr,*parent=nullptr;std::uint8_t flags=0;
    if(!Read(widget,kZhongguoWidgetGuiContextOffset,current_context)||current_context!=context||
        !Read(widget,kZhongguoWidgetHiddenFlagsOffset,flags)||(flags&kZhongguoWidgetEffectiveHiddenMask))return false;
    if(widget==root)return true;
    if(!Read(widget,kZhongguoWidgetParentOffset,parent)||!parent||parent==widget)return false;
    widget=parent;
  }return false;
}
struct Pass {
  void *context=nullptr,*owner=nullptr,*root=nullptr,*inner=nullptr;
  std::size_t count=0;std::array<const void *,9> widgets{};
  std::array<WhiteRenderedTextFieldV1,9> fields{};
  friend bool operator==(const Pass &,const Pass &)=default;
};
bool Observe(const ZhongguoScoreboardNativeEnvironmentV1 &env,Pass &out) {
  ZhongguoScoreboardAccessV1 access{};void *root_widget=nullptr;
  if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,out.context,out.owner)||!out.context||!out.owner||
      !ResolveNamedGuiWidgetV1(env,access,kRoot,kRoot,out.root,root_widget)||!out.root||root_widget!=out.root)return false;
  NamedGuiTreeInspectionV1 tree{};
  if(!InspectNamedGuiSubtreeV1(access,env.module_base,out.root,kRoot,tree)||tree.truncated||
      !tree.root_available||!tree.widget_count||tree.widget_count!=tree.widgets.size())return false;
  out.count=tree.widget_count;std::size_t roots=0,inners=0;
  for(const auto &row:tree.widgets){
    if(row.child_path.empty()){if(row.runtime_name!=kRoot||!row.effective_visible)return false;++roots;}
    if(row.runtime_name==kInner){if(row.child_path!="0"||!row.effective_visible)return false;++inners;}
  }
  const std::uint32_t inner_path[]{0};void *actual_root=nullptr;
  if(roots!=1||inners!=1||!ResolveFixedGuiChildPathV1(env,access,kRoot,inner_path,1,actual_root,out.inner)||
      actual_root!=out.root||!out.inner||!Ancestors(out.inner,out.root,out.context))return false;
  for(std::size_t n=0;n<out.fields.size();++n){
    const NamedGuiWidgetInspectionV1 *match=nullptr;std::size_t count=0;
    for(const auto &row:tree.widgets)if(row.runtime_name==kWhiteRenderedTextNamesV1[n]){match=&row;++count;}
    if(count!=1||!match||!match->effective_visible||match->vtable_rva!=0x497B828||!match->child_path.starts_with("0/"))return false;
    std::vector<std::uint32_t> path;if(!Path(match->child_path,path))return false;
    void *widget=nullptr;std::string name;void *vt=nullptr;bool visible=false,enabled=false;
    if(!ResolveFixedGuiChildPathV1(env,access,kRoot,path.data(),path.size(),actual_root,widget)||actual_root!=out.root||
        !widget||!ReadGuiWidgetRuntimeV1(access,widget,name,vt,visible,enabled)||name!=kWhiteRenderedTextNamesV1[n]||
        !visible||visible!=match->effective_visible||enabled!=match->enabled||!Textbox(widget,env.module_base)||
        !Ancestors(widget,out.inner,out.context)||!ActualText(widget,out.fields[n].text_utf8))return false;
    out.widgets[n]=widget;out.fields[n].child_path=match->child_path;
    out.fields[n].effective_visible=visible;out.fields[n].enabled=enabled;
  }
  return true;
}
bool Frame(const game::Snapshot &s,const MainThreadExecutionStampV1 &stamp) noexcept {
  return s.paused&&s.map_ready&&s.has_played_character&&s.played_character_alive&&s.played_character_id>0&&
      !s.has_active_event&&s.date_raw==stamp.date_raw;
}
std::string Quote(std::string_view value) {
  constexpr auto hex="0123456789abcdef";std::string out="\"";
  for(unsigned char c:value){
    if(c=='"'||c=='\\'){out+='\\';out+=static_cast<char>(c);}
    else if(c<32){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}
    else out+=static_cast<char>(c);
  }return out+'"';
}
}
bool ExecuteWhiteRenderedTextV1(WhiteRenderedTextContextV1 &query,MainThreadQueryMailboxV1 &mailbox,
    const MainThreadExecutionStampV1 &stamp,const ZhongguoScoreboardNativeEnvironmentV1 &env) noexcept {
  auto &out=query.result;out={};out.game_pid=GetCurrentProcessId();
  out.native_revision=query.native_revision;out.connection_generation=query.connection_generation;
  try {
    const auto reject=[&](const char *why){out.available=false;out.fields={};out.unavailable_reason=why;return true;};
    if(!query.game||query.game->descriptor().game_version!="1.20.0.3"||
        query.game->descriptor().executable_sha256!="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"||
        !query.native_revision||!query.connection_generation||!env.module_base||!env.exact_build_admitted||
        env.offline_fixture_function_overrides||env.gui_abi_revision!=GuiAbiRevisionV1::crozier12003)
      return reject("exact_12003_white_text_admission_failed");
    if(!IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()))return reject("paused_application_owner_unverified");
    out.owner_thread_verified=true;game::Snapshot before{};
    if(!game::ReadSnapshot(*query.game,before)||before!=query.expected_snapshot||!Frame(before,stamp))return reject("fresh_alive_paused_noevent_frame_unverified");
    out.played_character_id=before.played_character_id;out.date_raw=before.date_raw;const void *logical=nullptr;
    if(!stamp.jomini_state||!Bytes(reinterpret_cast<const void *>(env.module_base+0x5C6A520),&logical,sizeof(logical))||
        reinterpret_cast<std::uintptr_t>(logical)!=stamp.jomini_state||!Pins(env.module_base))return reject("current_jomini_or_text_pins_changed");
    out.source_abi_pins_verified=true;Pass first{},second{};
    if(!Observe(env,first)||!Observe(env,second)||first!=second)return reject("actual_visible_white_text_or_owner_unstable");
    out.tree_complete=true;out.inner_modal_visible=true;out.widget_count=first.count;out.stable_two_pass_text=true;
    game::Snapshot after{};void *context=nullptr,*owner=nullptr;ZhongguoScoreboardAccessV1 access{};
    out.gui_owner_binding_verified=ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,context,owner)&&context==first.context&&owner==first.owner;
    out.frame_verified=game::ReadSnapshot(*query.game,after)&&after==before&&Frame(after,stamp)&&IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId());
    if(!out.gui_owner_binding_verified||!out.frame_verified||
        !Bytes(reinterpret_cast<const void *>(env.module_base+0x5C6A520),&logical,sizeof(logical))||
        reinterpret_cast<std::uintptr_t>(logical)!=stamp.jomini_state)return reject("white_text_completion_binding_changed");
    out.fields=first.fields;out.available=true;return true;
  }catch(...){out.available=false;out.fields={};out.unavailable_reason="white_text_query_exception";return true;}
}
std::string SerializeWhiteRenderedTextV1(const WhiteRenderedTextResultV1 &v) {
  std::string s="{\"schema\":\"ck3-native-white-rendered-text-v1\",\"step\":\"query-white-rendered-text-v1\",\"read_only\":true,\"selected_down_available\":false";
  const auto number=[&](const char *key,auto n){s+=','+Quote(key)+':'+std::to_string(n);};
  const auto boolean=[&](const char *key,bool b){s+=','+Quote(key)+':'+(b?"true":"false");};
  boolean("available",v.available);boolean("rendered_text_available",v.available);
  boolean("owner_thread_verified",v.owner_thread_verified);boolean("source_abi_pins_verified",v.source_abi_pins_verified);
  boolean("frame_verified",v.frame_verified);boolean("gui_owner_binding_verified",v.gui_owner_binding_verified);
  boolean("tree_complete",v.tree_complete);boolean("inner_modal_visible",v.inner_modal_visible);boolean("stable_two_pass_text",v.stable_two_pass_text);
  number("game_pid",v.game_pid);number("native_revision",v.native_revision);number("connection_generation",v.connection_generation);
  number("played_character_id",v.played_character_id);number("date_raw",v.date_raw);number("widget_count",v.widget_count);
  s+=",\"fields\":{";
  for(std::size_t n=0;n<v.fields.size();++n){if(n)s+=',';s+=Quote(kWhiteRenderedTextNamesV1[n])+':';
    if(!v.available){s+="null";continue;}const auto &f=v.fields[n];
    s+="{\"child_path\":"+Quote(f.child_path)+",\"text_utf8\":"+Quote(f.text_utf8)+
      ",\"effective_visible\":true,\"enabled\":"+(f.enabled?std::string("true"):std::string("false"))+"}";
  }return s+="},\"text_source\":\"actual_CPdxGuiTextbox_GetText_390\",\"unavailable_reason\":"+Quote(v.unavailable_reason)+"}";
}
}
