#include "xar_bridge/appointment_window_snapshot_v1.hpp"
#include <algorithm>
#include <array>
#include <limits>
#include <sstream>
#include <iomanip>
#include <unordered_set>

namespace xar::ck3_11906 {
namespace {
constexpr std::uintptr_t kTitles=0x5D1DAF8,kCharacters=0x5C67568,kWindowVtable=0x4587AA8;
constexpr std::uint32_t kMaximumPool=4096,kInvalid=0xFFFFFFFF;
template<class T> bool Read(const AppointmentWindowAccessV1 &a,std::uintptr_t p,T &v) noexcept {
  return p && a.read && a.read(a.context,p,&v,sizeof(v));
}
bool Object(const AppointmentWindowAccessV1 &a,std::uintptr_t slot,std::uint32_t id,std::size_t idoff,std::uintptr_t &o) noexcept {
  o=0;std::uintptr_t storage=0,slots=0;std::uint32_t cap=0,actual=0;
  return id!=kInvalid && Read(a,a.module_base+slot,storage) && Read(a,storage+0x20,slots) &&
    Read(a,storage+0x2C,cap) && cap<=0x1000000 && (id&0xFFFFFF)<cap &&
    Read(a,slots+std::size_t(id&0xFFFFFF)*16+8,o) && o && Read(a,o+idoff,actual) && actual==id;
}
bool CString(const AppointmentWindowAccessV1 &a,std::uintptr_t p,std::string &s,std::size_t bound) {
  std::uint64_t n=0,cap=0;std::uintptr_t chars=p;
  if(!Read(a,p+0x10,n)||!Read(a,p+0x18,cap)||n>bound||cap<n||cap>0x1000000)return false;
  if(cap>15 && !Read(a,p,chars))return false;
  if(cap<=15 && n>15)return false;
  s.assign(std::size_t(n),'\0');
  if(n && (!chars || !a.read(a.context,chars,s.data(),std::size_t(n))))return false;
  char end=1;return Read(a,chars+std::size_t(n),end) && end==0 && s.find('\0')==std::string::npos;
}
bool LawKey(const AppointmentWindowAccessV1 &a,std::uintptr_t law,std::string &s) {
  if(!CString(a,law+0x18,s,160)||s.empty())return false;
  return std::all_of(s.begin(),s.end(),[](unsigned char c){return (c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_';});
}
struct Header {
 std::uintptr_t vt=0,handler=0,root=0,slot=0,items=0,pool=0,cache=0,law=0,rule=0;
 std::uint32_t title=0;std::int32_t count=0,pool_count=0,cache_count=0;
 friend bool operator==(const Header &,const Header &)=default;
};
bool HeaderRead(const AppointmentWindowAccessV1 &a,Header &h) noexcept {
  const auto w=a.window,l=w+0xD0;
  return Read(a,w,h.vt)&&h.vt==a.module_base+kWindowVtable&&Read(a,w+0xA0,h.handler)&&h.handler==a.handler&&
   Read(a,w+0x60,h.root)&&h.root==a.gui_root&&Read(a,a.handler+0x518,h.slot)&&h.slot==w&&
   Read(a,w+0xC8,h.title)&&Read(a,w+0xBC0,h.law)&&h.law&&Read(a,w+0xBE8,h.rule)&&h.rule&&
   Read(a,l+0x18,h.items)&&Read(a,l+0x24,h.count)&&Read(a,l+0x1C8,h.pool)&&Read(a,l+0x1D4,h.pool_count)&&
   Read(a,l+0x9F8,h.cache)&&Read(a,l+0xA04,h.cache_count)&&h.count>=0&&h.count<=kMaximumPool&&
   h.count==h.pool_count&&h.count==h.cache_count&&(!h.count||(h.items&&h.pool&&h.cache));
}
bool CandidatesRead(const AppointmentWindowAccessV1 &a,const Header &h,std::vector<AppointmentCandidateV1> &v) {
  std::unordered_set<std::uint32_t> ids,indices;
  for(std::int32_t n=0;n<h.count;++n) {
    AppointmentCandidateV1 c;std::uintptr_t item=0,item_owner=0,pool_char=0,actual_char=0;std::uint32_t pool_id=0,cache_id=0;
    if(!Read(a,h.items+std::size_t(n)*8,item)||!Read(a,item,item_owner)||item_owner!=a.window+0xD0||!Read(a,item+8,c.character_id)||!Read(a,item+0xC,c.list_index)||
      c.list_index>=std::uint32_t(h.count)||!Read(a,h.pool+std::size_t(n)*8,pool_char)||!Read(a,pool_char+0x18,pool_id)||
      c.character_id!=pool_id||!Object(a,kCharacters,c.character_id,0x18,actual_char)||actual_char!=pool_char||
      !ids.insert(c.character_id).second||!indices.insert(c.list_index).second)return false;
    const auto row=h.cache+std::size_t(c.list_index)*0x2F8;
    if(!Read(a,row+0x40,cache_id)||cache_id!=c.character_id||!Read(a,row+0x28,c.native_rank)||
      !Read(a,row+0x38,c.score_raw)||c.native_rank< -1||c.native_rank>h.count)return false;
    std::uintptr_t death=0;
    if(!Read(a,actual_char+0x1D0,death)||!a.human_player||!a.human_player(a.context,c.character_id,c.is_human_player))return false;
    c.alive=death==0;c.is_ai=!c.alive||!c.is_human_player;
    v.push_back(c);
  }
  return true;
}
struct Normalized {
 std::uint32_t holder=0,title=0;std::string branch,key;
 friend bool operator==(const Normalized &,const Normalized &)=default;
};
bool Normalize(const AppointmentWindowAccessV1 &a,std::uint32_t id,Normalized &r) {
 std::uintptr_t t=0,c=0,g=0,first=0;std::int32_t count=0;
 if(!Object(a,kTitles,id,0x10,t)||!Read(a,t+0x128,r.holder)||!Object(a,kCharacters,r.holder,0x18,c)||!Read(a,c+0x1C0,g))return false;
 if(g) {
  r.branch="character_1c0";
  if(!Read(a,g+0x1EC,count)||count<=0||count>kMaximumPool||!Read(a,g+0x1E0,first))return false;
 } else {
  r.branch="character_1d0";
  if(!Read(a,c+0x1D0,g)||!g||!Read(a,g+0x74,count)||count<=0||count>kMaximumPool||!Read(a,g+0x68,first))return false;
 }
 if(!Read(a,first,r.title)||!Object(a,kTitles,r.title,0x10,t)||!a.title_key||!a.title_key(a.context,t,r.key))return false;
 std::uint32_t holder=0;return Read(a,t+0x128,holder)&&holder==r.holder;
}
bool ScoreTree(const AppointmentWindowAccessV1 &a,std::uintptr_t p,AppointmentScoreNodeV1 &out,
   std::unordered_set<std::uintptr_t> &visited,std::size_t &bytes,std::uint32_t depth) {
 if(depth>8||visited.size()>=128||!visited.insert(p).second)return false;
 std::uintptr_t children=0;std::int32_t count=0;
 if(!Read(a,p,children)||!Read(a,p+0xC,count)||count<0||count>128||(!children&&count)||
    !CString(a,p+0x18,out.text0,512)||!CString(a,p+0x38,out.text1,512)||!CString(a,p+0x58,out.text2,512)||
    !Read(a,p+0x78,out.value_raw)||!Read(a,p+0x80,out.factor_raw)||!Read(a,p+0x88,out.mode)||!Read(a,p+0x8E,out.flags))return false;
 bytes+=out.text0.size()+out.text1.size()+out.text2.size();if(bytes>12000)return false;
 for(std::int32_t n=0;n<count;++n) {
  AppointmentScoreNodeV1 child;
  if(!ScoreTree(a,children+std::size_t(n)*0x90,child,visited,bytes,depth+1))return false;
  out.children.push_back(std::move(child));
 }
 return true;
}
std::string Escape(std::string_view s) {
 std::ostringstream o;
 for(unsigned char c:s) {if(c=='"'||c=='\\')o<<'\\'<<c;else if(c<32)o<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<unsigned(c)<<std::dec;else o<<c;}
 return o.str();
}
void TreeJson(std::ostringstream &o,const AppointmentScoreNodeV1 &n) {
 o<<"{\"text0\":\""<<Escape(n.text0)<<"\",\"text1\":\""<<Escape(n.text1)<<"\",\"text2\":\""<<Escape(n.text2)
  <<"\",\"value_raw\":"<<n.value_raw<<",\"factor_raw\":"<<n.factor_raw<<",\"mode\":"<<n.mode<<",\"flags\":"<<unsigned(n.flags)<<",\"children\":[";
 for(std::size_t k=0;k<n.children.size();++k){if(k)o<<',';TreeJson(o,n.children[k]);}o<<"]}";
}
std::string Token(const std::vector<AppointmentCandidateV1> &v,std::uint32_t title,std::string_view law) {
 std::uint64_t h=14695981039346656037ull;
 auto u=[&h](std::uint64_t x){for(unsigned k=0;k<8;++k){h^=(x>>(k*8))&255;h*=1099511628211ull;}};
 u(title);for(unsigned char c:law){h^=c;h*=1099511628211ull;}
 for(const auto &c:v){u(c.character_id);u(c.list_index);u(std::uint32_t(c.native_rank));u(std::uint64_t(c.score_raw));u(c.alive);u(c.is_human_player);}
 std::ostringstream o;o<<"fnv1a64:"<<std::hex<<std::setw(16)<<std::setfill('0')<<h;return o.str();
}
}
bool ValidateAppointmentWindowRequestV1(const AppointmentWindowRequestV1 &r) noexcept {
 return r.requested_title_id!=kInvalid&&r.breakdown_character_id!=kInvalid&&r.candidate_offset<=kMaximumPool&&r.candidate_limit>0&&r.candidate_limit<=64;
}
bool ReadAppointmentWindowSnapshotV1(const AppointmentWindowAccessV1 &a,const AppointmentWindowRequestV1 &r,AppointmentWindowSnapshotV1 &out) noexcept {
 out={};out.requested_title_id=r.requested_title_id;out.candidate_offset=r.candidate_offset;out.breakdown_character_id=r.breakdown_character_id;
 auto fail=[&](std::string why){out.available=false;out.candidates.clear();out.breakdown_available=false;out.breakdown={};out.unavailable_reason=std::move(why);return false;};
 try {
  if(!ValidateAppointmentWindowRequestV1(r)||!a.module_base||!a.handler||!a.window||!a.gui_root||!a.read||!a.title_key)return fail("invalid_private_reader_admission");
  Header h,later;Normalized norm,norm_later;std::uintptr_t title=0;std::vector<AppointmentCandidateV1> all,again;
  if(!HeaderRead(a,h))return fail("current_appointment_header_or_full_pool_unverified");
  out.current_window_title_id=h.title;
  if(!Object(a,kTitles,h.title,0x10,title)||!a.title_key(a.context,title,out.current_title_key)||
     !Read(a,title+0x128,out.current_holder_character_id)||!LawKey(a,h.law,out.effective_succession_law_key))return fail("current_title_or_effective_law_unverified");
  std::uintptr_t holder=0;if(!Object(a,kCharacters,out.current_holder_character_id,0x18,holder))return fail("current_holder_full_id_unverified");
  if(r.requested_title_id) {
   if(!Normalize(a,r.requested_title_id,norm))return fail("requested_title_normalization_unverified");
   out.requested_holder_character_id=norm.holder;out.native_group_branch=norm.branch;out.group_first_title_id=norm.title;
   out.resolved_title_id=norm.title;out.resolved_title_key=norm.key;out.requested_resolves_to_current=norm.title==h.title;
  }
  if(!CandidatesRead(a,h,all)||r.candidate_offset>all.size())return fail("complete_candidate_pool_join_failed");
  if(r.breakdown_character_id) {
   auto it=std::find_if(all.begin(),all.end(),[&](const auto &c){return c.character_id==r.breakdown_character_id;});
   if(it==all.end())out.breakdown_unavailable_reason="requested_full_character_id_not_in_current_pool";
   else {
    std::uintptr_t character=0,result=0;
    if(!Object(a,kCharacters,it->character_id,0x18,character)||!a.breakdown)out.breakdown_unavailable_reason="native_score_getter_unavailable";
    else {
     out.breakdown_getter_invoked=true;
     std::unordered_set<std::uintptr_t> visited;std::size_t bytes=0;
     if(!a.breakdown(a.context,a.window,character,result)||result!=a.window+0xAE0+0x90||
        !ScoreTree(a,a.window+0xAE0,out.breakdown,visited,bytes,0))out.breakdown_unavailable_reason="native_score_getter_or_bounded_tree_unverified";
     else if(it->native_rank<=0||out.breakdown.value_raw!=it->score_raw)out.breakdown_unavailable_reason="breakdown_total_differs_from_cached_native_score";
     else out.breakdown_available=true;
    }
   }
   if(!out.breakdown_available)out.breakdown={};
  }
  std::string law_later,key_later;std::uint32_t holder_later=0;std::uintptr_t title_later=0;
  if(!HeaderRead(a,later)||later!=h||!CandidatesRead(a,later,again)||again!=all||
     !Object(a,kTitles,h.title,0x10,title_later)||title_later!=title||
     !a.title_key(a.context,title,key_later)||key_later!=out.current_title_key||!Read(a,title+0x128,holder_later)||holder_later!=out.current_holder_character_id||
     !LawKey(a,h.law,law_later)||law_later!=out.effective_succession_law_key||
     (r.requested_title_id&&(!Normalize(a,r.requested_title_id,norm_later)||norm_later!=norm)))return fail("current_window_or_full_pool_changed_during_query");
  out.full_candidate_count=std::uint32_t(all.size());out.source_pool_count=std::uint32_t(h.pool_count);
  out.pool_consistency_token=Token(all,h.title,out.effective_succession_law_key);
  out.next_offset=(std::min)(std::uint32_t(all.size()),r.candidate_offset+r.candidate_limit);
  out.candidates.assign(all.begin()+r.candidate_offset,all.begin()+out.next_offset);
  out.available=true;
  if(SerializeAppointmentWindowSnapshotV1(out).size()>44000)return fail("appointment_serialized_packet_budget_exceeded");
  return true;
 } catch(...) {return fail("appointment_reader_exception");}
}
std::string SerializeAppointmentWindowSnapshotV1(const AppointmentWindowSnapshotV1 &v) {
 std::ostringstream o;o<<std::boolalpha;
 o<<"{\"schema\":\"ck3-current-title-appointment-v1\",\"available\":"<<v.available
  <<",\"requested_title_id\":"<<v.requested_title_id<<",\"requested_holder_character_id\":"<<v.requested_holder_character_id
  <<",\"native_group_branch\":\""<<v.native_group_branch<<"\",\"group_first_title_id\":"<<v.group_first_title_id
  <<",\"resolved_title_id\":"<<v.resolved_title_id<<",\"current_window_title_id\":"<<v.current_window_title_id
  <<",\"requested_resolves_to_current\":"<<v.requested_resolves_to_current
  <<",\"current_holder_character_id\":"<<v.current_holder_character_id
  <<",\"current_title_key\":\""<<Escape(v.current_title_key)<<"\",\"resolved_title_key\":\""<<Escape(v.resolved_title_key)
  <<"\",\"effective_succession_law_key\":\""<<Escape(v.effective_succession_law_key)
  <<"\",\"full_candidate_count\":"<<v.full_candidate_count<<",\"source_pool_count\":"<<v.source_pool_count
  <<",\"candidate_offset\":"<<v.candidate_offset<<",\"next_offset\":"<<v.next_offset
  <<",\"pool_consistency_token\":\""<<v.pool_consistency_token<<"\",\"score_fixed_point_scale\":100000"
  <<",\"candidate_scope\":\"complete_native_base_list_joined_to_source_pool_and_score_cache\",\"ai_control_available\":"<<v.available<<",\"candidates\":[";
 for(std::size_t n=0;n<v.candidates.size();++n){if(n)o<<',';const auto &c=v.candidates[n];
  o<<"{\"character_id\":"<<c.character_id<<",\"list_index\":"<<c.list_index<<",\"native_rank\":"<<c.native_rank<<",\"score_present\":"<<(c.native_rank>0)<<",\"score_raw\":"<<c.score_raw<<",\"alive\":"<<c.alive<<",\"is_human_player\":"<<c.is_human_player<<",\"is_ai\":"<<c.is_ai<<",\"candidate_pool_member\":true}";}
 o<<"],\"breakdown_character_id\":"<<v.breakdown_character_id<<",\"breakdown_getter_invoked\":"<<v.breakdown_getter_invoked
  <<",\"breakdown_cache_refresh_only\":true,\"breakdown_available\":"<<v.breakdown_available<<",\"breakdown\":";
 if(v.breakdown_available)TreeJson(o,v.breakdown);else o<<"null";
 o<<",\"breakdown_unavailable_reason\":\""<<Escape(v.breakdown_unavailable_reason)<<"\",\"unavailable_reason\":\""<<Escape(v.unavailable_reason)<<"\"}";
 return o.str();
}
}
