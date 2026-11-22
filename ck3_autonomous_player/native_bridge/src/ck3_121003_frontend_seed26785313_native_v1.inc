#ifndef XAR_FRONTEND_SEED_CALL_ADDRESS
#define XAR_FRONTEND_SEED_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif
// Current859 only. Every offset/call below has an independent actual ctor,
// reflected method or collection consumer in the a861 source packets.
// App+28 is current; App+78 is the consumed pending interface (a887).
struct SeedCharacter267V1 {
 std::uintptr_t object=0,parent=0;std::string key;
 friend bool operator==(const SeedCharacter267V1&,const SeedCharacter267V1&)=default;
};
struct SeedBookmark267V1 {
 std::uintptr_t object=0,group=0,characters=0;std::int32_t capacity=0,count=0,date=0;
 std::uint8_t playable=0;std::string key,group_key;std::vector<SeedCharacter267V1>roles;
 friend bool operator==(const SeedBookmark267V1&,const SeedBookmark267V1&)=default;
};
struct SeedSnapshot267V1 {
 std::uintptr_t application=0,context=0,owner=0,wrapper=0,handler=0,main=0,setup=0,
  main_root=0,setup_root=0,group_data=0,database=0,bookmark_data=0,selected_group=0,selected_bookmark=0,
  target_group=0,target_bookmark=0,target_character=0;
 std::int32_t state=-1,next_state=-1,group_capacity=0,group_count=0,bookmark_capacity=0,bookmark_count=0,
  selected_index=-1,target_index=-1;
 std::uint8_t starting=0;bool complete=false;std::optional<bool>native_can_start;
 std::vector<std::pair<std::uintptr_t,std::string>>groups;std::vector<SeedBookmark267V1>bookmarks;
 friend bool operator==(const SeedSnapshot267V1&,const SeedSnapshot267V1&)=default;
};
[[maybe_unused]]bool SeedTargets267V1(std::uintptr_t image)noexcept {
 std::array<std::uint8_t,4096>bytes{};
 for(const auto&p:frontend_seed_pins::kPins)if(p.bytes.empty()||p.bytes.size()>bytes.size()||
  !Copy(reinterpret_cast<const void*>(image+p.rva),bytes.data(),p.bytes.size())||
  std::memcmp(bytes.data(),p.bytes.data(),p.bytes.size()))return false;
 return true;
}
[[maybe_unused]]bool SeedType267V1(std::uintptr_t image,std::uintptr_t object,
 std::uintptr_t vtable,std::uintptr_t locator,std::uint32_t offset,std::uint32_t descriptor)noexcept {
 std::uintptr_t vt=0,col=0;std::uint32_t sig=0,off=0,td=0,self=0;
 return At(object,0,vt)&&vt==image+vtable&&At(vt-8,0,col)&&col==image+locator&&
  At(col,0,sig)&&sig==1&&At(col,4,off)&&off==offset&&At(col,12,td)&&td==descriptor&&
  At(col,20,self)&&self==locator;
}
[[maybe_unused]]bool SeedKey267V1(std::uintptr_t object,std::size_t offset,std::string&out) {
 std::uint64_t size=0,cap=0;std::uintptr_t chars=0;std::array<char,129>text{};
 if(!At(object,offset+16,size)||!At(object,offset+24,cap)||!size||size>128||cap<size||cap>0x1000000)return false;
 if(cap==15)chars=object+offset;else if(cap<=15||!At(object,offset,chars)||!chars)return false;
 if(!Copy(reinterpret_cast<const void*>(chars),text.data(),static_cast<std::size_t>(size)+1)||text[size])return false;
 for(std::size_t i=0;i<size;++i){const auto c=text[i];if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||
  (c>='0'&&c<='9')||c=='_'||c=='.'||c=='-'))return false;}
 out.assign(text.data(),static_cast<std::size_t>(size));return true;
}
[[maybe_unused]]bool SeedArray267V1(std::uintptr_t object,std::size_t offset,std::uintptr_t&data,
 std::int32_t&cap,std::int32_t&count,std::int32_t bound)noexcept {
 return At(object,offset,data)&&At(object,offset+8,cap)&&At(object,offset+12,count)&&
  count>=0&&cap>=count&&cap<=65536&&count<=bound&&(!count||data);
}
[[maybe_unused]]bool SeedNativeCanStart267V1(std::uintptr_t image,std::uintptr_t view,bool&out)noexcept {
 out=false;__try{using F=bool(__fastcall*)(void*);out=reinterpret_cast<F>(XAR_FRONTEND_SEED_CALL_ADDRESS(image,0x11320B0))(reinterpret_cast<void*>(view));return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool ReadSeed267V1(std::uintptr_t image,std::uintptr_t application,std::uintptr_t context,
 std::uintptr_t route_root,Route route,SeedSnapshot267V1&out) {
 out={};SeedSnapshot267V1 s;s.application=application;s.context=context;std::uintptr_t back=0,actual=0;
 if(!SeedTargets267V1(image)||!At(application,0x28,s.owner)||
  !SeedType267V1(image,s.owner,0x4B45978,0x51C8AF8,0,0x60B8E00)||
  !At(s.owner,0x18,back)||back!=application||!At(s.owner,0x10,s.wrapper)||
  !SeedType267V1(image,s.wrapper,0x4B7B2C0,0x5220950,0,0x5DB9748)||!At(s.wrapper,8,s.handler)||
  !SeedType267V1(image,s.handler,0x4B7B758,0x5221268,0,0x6120958)||
  !At(s.handler,8,s.state)||s.state<0||s.state>8||!At(s.handler,12,s.next_state)||
  !At(s.handler,0x10,s.main)||!At(s.handler,0x30,s.setup)||
  !SeedType267V1(image,s.main,0x4C620D8,0x539FDB8,0,0x62F7E98)||
  !SeedType267V1(image,s.main+0x10,0x4C62118,0x539FD90,0x10,0x62F7E98)||
  !SeedType267V1(image,s.setup,0x4B9FB58,0x524F740,0,0x6155B88)||
  !SeedType267V1(image,s.setup+0x10,0x4B9FB30,0x524F718,0x10,0x6155B88)||
  !At(s.main,0x98,back)||back!=s.owner||!At(s.main,0xA0,back)||back!=s.handler||
  !At(s.main,0x68,back)||back!=context||!At(s.setup,0x68,back)||back!=context||
  !At(s.setup,0x98,back)||back!=s.owner||!At(s.setup,0xA0,back)||back!=s.handler||
  !At(s.main,0x60,s.main_root)||!At(s.setup,0x60,s.setup_root)||
  !At(application,0x28,actual)||actual!=s.owner)return false;
 if(route==Route::main_menu){if(s.state!=0||s.main_root!=route_root)return false;out=std::move(s);return true;}
 if(route!=Route::bookmarks||s.state!=4||s.setup_root!=route_root||
  !SeedArray267V1(s.setup,0xC0,s.group_data,s.group_capacity,s.group_count,256)||!s.group_count)return false;
 std::unordered_set<std::uintptr_t>pointers;std::unordered_set<std::string>keys;
 for(std::int32_t i=0;i<s.group_count;++i){std::uintptr_t g=0;std::uint32_t magic=0;std::string key;
  if(!At(s.group_data,static_cast<std::size_t>(i)*8,g)||!pointers.insert(g).second||
   !SeedType267V1(image,g,0x4FEE390,0x57C34E0,0,0x5F8A678)||
   !At(g,0x38,magic)||magic!=0x4744624F||!SeedKey267V1(g,0x18,key)||!keys.insert(key).second)return false;
  if(key=="bm_group_1066")s.target_group=g;s.groups.emplace_back(g,std::move(key));
 }
 if(!At(image,0x68AFC40,s.database)||!SeedType267V1(image,s.database,0x5017038,0x57FA1A0,0,0x6731AF8)||
  !SeedArray267V1(s.database,0x50,s.bookmark_data,s.bookmark_capacity,s.bookmark_count,256)||!s.bookmark_count)return false;
 pointers.clear();keys.clear();
 for(std::int32_t i=0;i<s.bookmark_count;++i){SeedBookmark267V1 row;std::uint32_t magic=0;
  if(!At(s.bookmark_data,static_cast<std::size_t>(i)*8,row.object)||!pointers.insert(row.object).second||
   !SeedType267V1(image,row.object,0x4FEDA28,0x57C3530,0,0x5F8A6C8)||
   !At(row.object,0x38,magic)||magic!=0x4744624F||!SeedKey267V1(row.object,0x18,row.key)||!keys.insert(row.key).second||
   !At(row.object,0x40,row.date)||!At(row.object,0x100,row.playable)||row.playable>1||!At(row.object,0xF8,row.group)||
   !SeedType267V1(image,row.group,0x4FEE390,0x57C34E0,0,0x5F8A678)||!SeedKey267V1(row.group,0x18,row.group_key)||
   !SeedArray267V1(row.object,0x108,row.characters,row.capacity,row.count,64))return false;
  std::unordered_set<std::string>characters;
  for(std::int32_t j=0;j<row.count;++j){SeedCharacter267V1 c;c.object=row.characters+static_cast<std::size_t>(j)*0x1A0;
   if(!SeedType267V1(image,c.object,0x5017120,0x57FA1C8,0,0x6731B20)||
    !At(c.object,0x130,c.parent)||c.parent!=row.object||!SeedKey267V1(c.object,8,c.key)||!characters.insert(c.key).second)return false;
   if(row.key==kFrontendRobertBookmark267V1&&c.key==kFrontendRobertCharacter267V1){if(s.target_character)return false;s.target_character=c.object;s.target_index=j;}
   row.roles.push_back(std::move(c));
  }
  if(row.key==kFrontendRobertBookmark267V1){if(s.target_bookmark||row.group!=s.target_group||row.group_key!="bm_group_1066"||row.date!=53144328)return false;s.target_bookmark=row.object;}
  s.bookmarks.push_back(std::move(row));
 }
 if(!At(s.setup,0xD8,s.selected_group)||!At(s.setup,0x120,s.selected_bookmark)||!At(s.setup,0x128,s.selected_index)||
  !At(s.setup,0x130,s.starting)||s.starting>1||!s.target_group||!s.target_bookmark||!s.target_character)return false;
 const SeedBookmark267V1*selected=nullptr;
 for(const auto&b:s.bookmarks)if(b.object==s.selected_bookmark)selected=&b;
 if(!selected||s.selected_index<-1||s.selected_index>=selected->count)return false;
 if(s.selected_index>=0){bool can=false;if(!SeedNativeCanStart267V1(image,s.setup,can))return false;s.native_can_start=can;}
 s.complete=true;out=std::move(s);return true;
}
// Trivial SEH wrapper: no C++ object with a destructor crosses this boundary.
[[maybe_unused]]bool SeedCallAdmission267V1(std::uintptr_t image,const SeedSnapshot267V1&s,
 void*const*world_slot,std::uint64_t wall,std::uint64_t mono)noexcept {
 const auto time=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
 std::uintptr_t owner=0,wrapper=0,handler=0,view=0;void*world=reinterpret_cast<void*>(1);
 return time>0&&static_cast<std::uint64_t>(time)<wall&&GetTickCount64()<mono&&world_slot&&
  Copy(world_slot,&world,sizeof(world))&&!world&&At(s.application,0x28,owner)&&owner==s.owner&&
  At(owner,0x10,wrapper)&&wrapper==s.wrapper&&At(wrapper,8,handler)&&handler==s.handler&&
  At(handler,0x30,view)&&view==s.setup&&SeedType267V1(image,view,0x4B9FB58,0x524F740,0,0x6155B88);
}
[[maybe_unused]]bool InvokeSeed267V1(std::uintptr_t image,Action action,const SeedSnapshot267V1&s,
 void*const*world_slot,std::uint64_t wall,std::uint64_t mono)noexcept {
 __try{
  using Unary=void(__fastcall*)(void*);using Setter=void(__fastcall*)(void*,const void*);
  if(!SeedCallAdmission267V1(image,s,world_slot,wall,mono))return false;
  if(action==Action::open_bookmarks)reinterpret_cast<Unary>(XAR_FRONTEND_SEED_CALL_ADDRESS(image,0x1BB01C0))(reinterpret_cast<void*>(s.main));
  else if(action==Action::select_1066_bookmark){
   if(s.selected_group!=s.target_group)reinterpret_cast<Setter>(XAR_FRONTEND_SEED_CALL_ADDRESS(image,0x11314D0))(reinterpret_cast<void*>(s.setup),reinterpret_cast<void*>(s.target_group));
   std::uintptr_t group=0;if(!SeedCallAdmission267V1(image,s,world_slot,wall,mono)||!At(s.setup,0xD8,group)||group!=s.target_group)return false;
   reinterpret_cast<Setter>(XAR_FRONTEND_SEED_CALL_ADDRESS(image,0x1131EC0))(reinterpret_cast<void*>(s.setup),reinterpret_cast<void*>(s.target_bookmark));
  }else if(action==Action::select_robert_1066)reinterpret_cast<Setter>(XAR_FRONTEND_SEED_CALL_ADDRESS(image,0x1131FF0))(reinterpret_cast<void*>(s.setup),reinterpret_cast<void*>(s.target_character));
  else if(action==Action::start_robert_1066){
   reinterpret_cast<Unary>(XAR_FRONTEND_SEED_CALL_ADDRESS(image,0x1130E90))(reinterpret_cast<void*>(s.setup));
   std::uint8_t prepared=0;std::uintptr_t selected=0;std::int32_t index=-1;
   if(!SeedCallAdmission267V1(image,s,world_slot,wall,mono)||!At(s.setup,0x130,prepared)||prepared!=1||!At(s.setup,0x120,selected)||selected!=s.target_bookmark||
    !At(s.setup,0x128,index)||index!=s.target_index)return false;
   reinterpret_cast<Unary>(XAR_FRONTEND_SEED_CALL_ADDRESS(image,0x11315F0))(reinterpret_cast<void*>(s.setup));
  }else return false;return true;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
