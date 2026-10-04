#include "xar_bridge/aub_business_state_v1.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include <Windows.h>
#include <cstring>
#include <vector>
#include <limits>

namespace xar::ck3_12003 {
namespace {
using namespace ck3_11906;
constexpr std::string_view kSha="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
#include "aub_flag_exact_pins_v1.inc"
bool Bytes(const ZhongguoScoreboardAccessV1 &a,const void *p,void *out,std::size_t size) noexcept {
  if(!p||!out||!size)return false;
  if(a.read_memory)return a.read_memory(a.context,p,out,size);
  SIZE_T got=0;return ReadProcessMemory(GetCurrentProcess(),p,out,size,&got)&&got==size;
}
template<class T> bool Read(const ZhongguoScoreboardAccessV1 &a,const void *p,std::size_t offset,T &out) noexcept {
  const auto raw=reinterpret_cast<std::uintptr_t>(p);
  return raw&&offset<=std::numeric_limits<std::uintptr_t>::max()-raw&&Bytes(a,reinterpret_cast<const void *>(raw+offset),&out,sizeof(out));
}
template<class F,class R,class... A> bool Call(F f,R &r,A... args) noexcept {
  if(!f)return false;
#if defined(_MSC_VER)
  __try{r=f(args...);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  r=f(args...);return true;
#endif
}
bool Pins(const ZhongguoScoreboardNativeEnvironmentV1 &env,const ZhongguoScoreboardAccessV1 &a) noexcept {
  std::array<unsigned char,kAubFlagPin0.size()> p0{};std::array<unsigned char,kAubFlagPin1.size()> p1{};
  return Bytes(a,reinterpret_cast<const void *>(env.module_base+0x3F8A3A0),p0.data(),p0.size())&&p0==kAubFlagPin0&&
    Bytes(a,reinterpret_cast<const void *>(env.module_base+0x1D67200),p1.data(),p1.size())&&p1==kAubFlagPin1;
}
bool AtomName(const ZhongguoScoreboardAccessV1 &a,void *pool,std::uint32_t atom,std::string_view expected) {
  const void *records=nullptr;std::uint32_t count=0;
  if(!Read(a,pool,0x30,records)||!Read(a,pool,0x3C,count)||count>0x1000000||!records||(atom&0xFFFFFF)>=count)return false;
  const auto record=reinterpret_cast<const std::byte *>(records)+(atom&0xFFFFFF)*0x20ULL;
  std::uint64_t size=0,capacity=0;const void *text=record;
  if(!Read(a,record,0x10,size)||!Read(a,record,0x18,capacity)||size!=expected.size()||capacity<size||
      (capacity<16&&capacity!=15)||(capacity>=16&&(!Read(a,record,0,text)||!text)))return false;
  std::array<char,64> chars{};
  return size+1<=chars.size()&&Bytes(a,text,chars.data(),static_cast<std::size_t>(size)+1)&&chars[size]==0&&
      std::memcmp(chars.data(),expected.data(),static_cast<std::size_t>(size))==0;
}
struct FlagPass {
  void *script=nullptr,*collection=nullptr;const void *rows=nullptr;
  std::int32_t index=-2,count=-1;std::uint32_t pool_lock=1;
  std::array<std::uint32_t,4> atoms{};std::vector<std::uint32_t> keys;
  std::array<AubBusinessFlagV1,4> flags{};
  bool operator==(const FlagPass &) const=default;
};
bool Pass(const ZhongguoScoreboardAccessV1 &a,const AubFlagReadBindingsV1 &b,void *actor,std::int32_t id,FlagPass &p) {
  std::int32_t actual=-1;std::uint32_t magic=0;std::uint8_t dummy=1;const void *death=nullptr;
  if(id<=0||!Read(a,actor,0x18,actual)||actual!=id||!Read(a,actor,0x1C,magic)||magic!=0x43686172||
     !Read(a,actor,0x1D0,death)||death||!Read(a,actor,0x1A5,dummy)||dummy||!Read(a,actor,0x1B0,p.script))return false;
  const void *pool_rows=nullptr;std::int32_t pool_count=-1;
  if(!Read(a,b.atom_pool,0x10,pool_rows)||!pool_rows||!Read(a,b.atom_pool,0x1C,pool_count)||pool_count<0||pool_count>0x1000000||
      !Read(a,b.atom_pool,0x48,p.pool_lock)||(p.pool_lock&1))return false;
  for(std::size_t i=0;i<kAubBusinessFlagKeysV1.size();++i){
    const auto key=kAubBusinessFlagKeysV1[i];auto &o=p.flags[i];o.key=key;
    religion::repentance_recovery_inputs::NativeStringView view{key.data(),static_cast<std::int32_t>(key.size()),1,{}};
    p.atoms[i]=0xFFFFFFFF;std::uint32_t *returned=nullptr;
    if(!Call(b.existing_atom,returned,b.atom_pool,&p.atoms[i],&view)||returned!=&p.atoms[i]||
       (p.atoms[i]!=0xFFFFFFFF&&!AtomName(a,b.atom_pool,p.atoms[i],key)))return false;
    o.atom_registered=p.atoms[i]!=0xFFFFFFFF;
  }
  if(p.script){
    if(!Read(a,p.script,0,p.index)||p.index< -1)return false;
    if(p.index!=-1){
      if(!Call(b.flag_collection,p.collection,p.script)||!p.collection||!Read(a,p.collection,0x10,p.rows)||
          !Read(a,p.collection,0x1C,p.count)||p.count<0||p.count>65536||(p.count&&!p.rows))return false;
      p.keys.reserve(static_cast<std::size_t>(p.count));
      for(std::int32_t n=0;n<p.count;++n){std::uint32_t key=0xFFFFFFFF;
        if(!Read(a,p.rows,static_cast<std::size_t>(n)*0x20+8,key)||key==0xFFFFFFFF)return false;
        p.keys.push_back(key);
      }
    }
  }
  for(std::size_t i=0;i<p.flags.size();++i){
    std::size_t matches=0;for(const auto key:p.keys)if(key==p.atoms[i])++matches;
    if(matches>1)return false;p.flags[i].present=matches==1;p.flags[i].available=true;
  }
  std::uint32_t end_lock=1;
  return Read(a,b.atom_pool,0x48,end_lock)&&end_lock==p.pool_lock&&(end_lock&1)==0;
}
bool ActualActor(const ZhongguoScoreboardNativeEnvironmentV1 &env,const ZhongguoScoreboardAccessV1 &a,
    std::int32_t id,void *&actor) {
  std::int32_t current=-1,observed=-1;const void *storage=nullptr,*rows=nullptr,*death=nullptr;std::uint32_t count=0;
  return id>0&&Read(a,reinterpret_cast<const void *>(env.module_base+0x54DBC00),0,current)&&current==id&&
    Read(a,reinterpret_cast<const void *>(env.module_base+0x5C67568),0,storage)&&storage&&Read(a,storage,0x20,rows)&&rows&&
    Read(a,storage,0x2C,count)&&count>0&&count<=0x1000000&&(static_cast<std::uint32_t>(id)&0xFFFFFF)<count&&
    Read(a,rows,(static_cast<std::uint32_t>(id)&0xFFFFFF)*0x10ULL+8,actor)&&actor&&Read(a,actor,0x18,observed)&&
    observed==id&&Read(a,actor,0x1D0,death)&&!death;
}
bool Detail(const ZhongguoScoreboardNativeEnvironmentV1 &env,AubBusinessStateResultV1 &out) {
  ZhongguoScoreboardAccessV1 a{};void *root=nullptr,*widget=nullptr;NamedGuiTreeInspectionV1 tree{};
  if(!ResolveNamedGuiWidgetV1(env,a,"decisiondetail_view","decisiondetail_view",root,widget))return false;
  out.detail_root_available=root!=nullptr;
  if(!root){out.detail_census_verified=widget==nullptr;out.detail_tree_complete=widget==nullptr;return widget==nullptr;}
  if(root!=widget||!InspectNamedGuiSubtreeV1(a,env.module_base,root,"decisiondetail_view",tree)||tree.truncated||
      !tree.widget_count||tree.widget_count!=tree.widgets.size())return false;
  std::size_t roots=0;for(const auto &row:tree.widgets)if(row.child_path.empty()){
    if(row.runtime_name!="decisiondetail_view")return false;out.detail_effectively_visible=row.effective_visible;++roots;
  }
  out.detail_census_verified=roots==1;out.detail_tree_complete=roots==1;return roots==1;
}
std::string Text(std::string_view v){std::string s="\"";for(char c:v){if(c=='"'||c=='\\')s+='\\';s+=c;}return s+'"';}
} // namespace
bool ReadAubBusinessFlagsV1(const ZhongguoScoreboardNativeEnvironmentV1 &env,const ZhongguoScoreboardAccessV1 &a,
    const AubFlagReadBindingsV1 &b,void *actor,std::int32_t id,std::array<AubBusinessFlagV1,4> &out) noexcept {
  out={};for(std::size_t i=0;i<out.size();++i){out[i].key=kAubBusinessFlagKeysV1[i];out[i].unavailable_reason="flag_read_unavailable";}
  try {
    if(!env.exact_build_admitted||env.gui_abi_revision!=GuiAbiRevisionV1::crozier12003||!b.atom_pool||!b.existing_atom||!b.flag_collection)return false;
    if(!env.offline_fixture_function_overrides&&(b.atom_pool!=reinterpret_cast<void *>(env.module_base+0x5DC1390)||
       b.existing_atom!=reinterpret_cast<religion::repentance_recovery_inputs::ExistingAtomLookup>(env.module_base+0x3F8A3A0)||
       b.flag_collection!=reinterpret_cast<religion::repentance_recovery_inputs::ObjectGetter>(env.module_base+0x1D67200)||!Pins(env,a)))return false;
    FlagPass first{},second{};if(!Pass(a,b,actor,id,first)||!Pass(a,b,actor,id,second)||first!=second)return false;
    out=std::move(first.flags);return true;
  }catch(...){return false;}
}
bool ExecuteAubBusinessStateQueryV1(AubBusinessStateContextV1 &q,MainThreadQueryMailboxV1 &mailbox,
    const MainThreadExecutionStampV1 &stamp,const ZhongguoScoreboardNativeEnvironmentV1 &env) noexcept {
  auto &o=q.result;o={};o.native_revision=q.observation.native_revision;o.connection_generation=q.observation.connection_generation;
  o.game_pid=GetCurrentProcessId();
  try {
    const auto reject=[&](const char *why){o.available=false;o.unavailable_reason=why;return true;};
    if(!q.observation.game||q.observation.game->descriptor().game_version!="1.20.0.3"||q.observation.game->descriptor().executable_sha256!=kSha||
       !o.native_revision||!o.connection_generation||!env.exact_build_admitted||env.offline_fixture_function_overrides||
       env.gui_abi_revision!=GuiAbiRevisionV1::crozier12003)return reject("exact_aub_business_query_unavailable");
    if(!IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()))return reject("paused_application_owner_unverified");
    o.owner_thread_verified=true;game::Snapshot before{};
    if(!game::ReadSnapshot(*q.observation.game,before)||before!=q.observation.expected_snapshot||!before.paused||!before.map_ready||
       !before.has_played_character||!before.played_character_alive||before.played_character_id<=0||before.date_raw!=stamp.date_raw||
       before.has_active_event||before.has_pending_character_interaction)return reject("fresh_alive_paused_noevent_frame_unverified");
    o.played_character_id=before.played_character_id;o.date_raw=before.date_raw;
    ZhongguoScoreboardAccessV1 a{};void *context=nullptr,*owner=nullptr,*actor=nullptr;
    if(!Pins(env,a))return reject("loaded_aub_flag_abi_pins_changed");o.source_abi_pins_verified=true;
    if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,a,context,owner)||
       !ActualActor(env,a,o.played_character_id,actor))return reject("actual_actor_or_gui_owner_unverified");
    AubFlagReadBindingsV1 b{reinterpret_cast<religion::repentance_recovery_inputs::ExistingAtomLookup>(env.module_base+0x3F8A3A0),
      reinterpret_cast<religion::repentance_recovery_inputs::ObjectGetter>(env.module_base+0x1D67200),reinterpret_cast<void *>(env.module_base+0x5DC1390)};
    if(!ReadAubBusinessFlagsV1(env,a,b,actor,o.played_character_id,o.flags))return reject("actual_flag_rows_or_names_unstable");
    o.stable_two_pass_verified=true;if(!Detail(env,o))return reject("actual_detail_census_incomplete");
    game::Snapshot after{};void *after_context=nullptr,*after_owner=nullptr,*after_actor=nullptr;
    o.gui_owner_binding_verified=ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,a,after_context,after_owner)&&context==after_context&&owner==after_owner;
    o.frame_verified=game::ReadSnapshot(*q.observation.game,after)&&after==before&&ActualActor(env,a,o.played_character_id,after_actor)&&actor==after_actor&&
      IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId());
    if(!o.gui_owner_binding_verified||!o.frame_verified)return reject("aub_business_completion_binding_changed");
    std::array<AubBusinessFlagV1,4> last{};
    if(!ReadAubBusinessFlagsV1(env,a,b,actor,o.played_character_id,last)||last!=o.flags)return reject("aub_business_completion_flags_changed");
    o.available=true;return true;
  }catch(...){o.available=false;o.unavailable_reason="aub_business_read_exception";return true;}
}
bool AubFlagsMatchSelectedPolicyV1(std::string_view key,const AubBusinessStateResultV1 &s) noexcept {
  if(!s.available)return false;std::size_t choice=kAubPolicyValueKeysV1.size();
  for(std::size_t i=0;i<kAubPolicyValueKeysV1.size();++i)if(kAubPolicyValueKeysV1[i]==key)choice=i;
  if(choice>=kAubPolicyValueKeysV1.size())return false;
  const std::array<bool,4> expected{true,choice<2,choice>=2&&choice<4,(choice%2)==0};
  for(std::size_t i=0;i<s.flags.size();++i)if(s.flags[i].key!=kAubBusinessFlagKeysV1[i]||!s.flags[i].available||!s.flags[i].present||*s.flags[i].present!=expected[i])return false;
  return true;
}
std::string SerializeAubBusinessStateV1(const AubBusinessStateResultV1 &o){
  std::string s="{\"schema\":\"ck3-aub-business-state-v1\",\"step\":\"query-aub-business-state-v1\",\"read_only\":true,\"game_version\":\"1.20.0.3\",\"executable_sha256\":\"";
  s+=kSha;s+='"';
  const auto number=[&](const char *k,auto v){s+=","+Text(k)+":"+std::to_string(v);};
  const auto boolean=[&](const char *k,bool v){s+=","+Text(k)+":"+(v?"true":"false");};
  number("native_revision",o.native_revision);number("connection_generation",o.connection_generation);number("game_pid",o.game_pid);
  number("played_character_id",o.played_character_id);number("date_raw",o.date_raw);
  boolean("available",o.available);boolean("owner_thread_verified",o.owner_thread_verified);boolean("frame_verified",o.frame_verified);
  boolean("source_abi_pins_verified",o.source_abi_pins_verified);boolean("gui_owner_binding_verified",o.gui_owner_binding_verified);
  boolean("stable_two_pass_verified",o.stable_two_pass_verified);boolean("detail_census_verified",o.detail_census_verified);
  boolean("detail_root_available",o.detail_root_available);boolean("detail_tree_complete",o.detail_tree_complete);boolean("detail_effectively_visible",o.detail_effectively_visible);
  s+=",\"flags\":[";bool comma=false;for(const auto &f:o.flags){if(comma)s+=',';comma=true;
    s+="{\"key\":"+Text(f.key)+",\"available\":"+(f.available?"true":"false")+",\"atom_registered\":"+(f.atom_registered?"true":"false")+",\"present\":";
    s+=f.present?(*f.present?"true":"false"):"null";s+=",\"unavailable_reason\":"+Text(f.unavailable_reason)+'}';}
  return s+"],\"unavailable_reason\":"+Text(o.unavailable_reason)+",\"rendered_text_available\":false,\"rendered_down_available\":false,\"product_acceptance_proven\":false}";
}
std::string SerializeAubConfirmV1(const AubConfirmResultV1 &o){
  std::string s="{\"schema\":\"ck3-aub-confirm-v1\",\"step\":\"confirm-aub-policy-v1\",\"read_only\":false,\"game_version\":\"1.20.0.3\",\"executable_sha256\":\"";
  s+=kSha;s+='"';
  const auto boolean=[&](const char *k,bool v){s+=","+Text(k)+":"+(v?"true":"false");};
  s+=",\"selected_key\":"+Text(o.selected_key)+",\"target_child_path\":"+Text(o.target_child_path);
  boolean("receiver_qualified",o.receiver_qualified);boolean("selected_policy_revalidated",o.selected_policy_revalidated);
  boolean("dispatch_attempted",o.dispatch_attempted);boolean("dispatch_invoked",o.dispatch_invoked);boolean("native_handled",o.native_handled);
  boolean("postcondition_verified",o.postcondition_verified);boolean("verification_pending",o.dispatch_attempted&&!o.postcondition_verified);
  s+=",\"before_actual_model\":"+ck3_11906::SerializeIngameDecisionItemV1(o.keyed_before);
  s+=",\"state_before\":"+SerializeAubBusinessStateV1(o.state_before)+",\"state_after\":"+SerializeAubBusinessStateV1(o.state_after);
  s+=",\"actual_policy_before\":{\"ready\":";s+=o.policy_before.ready?"true":"false";
  s+=",\"selected_key\":"+Text(o.policy_before.selected_key)+",\"entries\":[";bool comma=false;
  for(const auto &entry:o.policy_before.entries){if(comma)s+=',';comma=true;s+="{\"value_key\":"+Text(entry.value_key)+",\"selected\":"+(entry.selected?"true":"false")+'}';}
  return s+"]},\"unavailable_reason\":"+Text(o.unavailable_reason)+",\"product_acceptance_proven\":false}";
}
} // namespace xar::ck3_12003
