namespace lyd_common {
[[maybe_unused]]bool Bytes(std::uintptr_t p,void*out,std::size_t n)noexcept{
 if(!p||!out||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;
 __try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<class T>bool At(std::uintptr_t p,std::size_t off,T&v)noexcept{return p&&off<=(std::numeric_limits<std::uintptr_t>::max)()-p&&Bytes(p+off,&v,sizeof(v));}
[[maybe_unused]]bool Typed(std::uintptr_t p,std::uintptr_t image,std::uintptr_t vt)noexcept{std::uintptr_t value=0;return At(p,0,value)&&value==image+vt;}
[[maybe_unused]]bool EqualCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&expected,const LydScene267V1&s,std::uint64_t mono)noexcept{
 const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();if(!mono||GetTickCount64()>=mono||wall<=0||!s.wall_deadline||static_cast<std::uint64_t>(wall)>=s.wall_deadline)return false;
 __try{
  ck3_1210::CoreSnapshotPrefix actual;if(!ck3_1210::ReadCoreSnapshot(b.core,actual)||!EqualCore(actual,expected))return false;
  if(s.kind==LydKind267V1::readback)return true;
  std::uintptr_t j=0,g=0,h=0,a=0,f=0,c=0,global=0;
  return At(reinterpret_cast<std::uintptr_t>(b.core.jomini_state_slot),0,j)&&j==s.jomini&&At(j,0x10,g)&&g==s.gfx&&Typed(g,b.module_base,0x4B24748)&&At(g,0x20,a)&&a==j&&At(g,0x88,h)&&h==s.handler&&Typed(h,b.module_base,0x4B22578)&&At(j,0x18,a)&&a==s.application&&Typed(a,b.module_base,kGuiRootApplicationVtableRvaV1)&&At(a,0x1B8,f)&&At(f,0x58,c)&&c==s.context&&At(c,0xD0,global)&&global==s.global;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<class T>bool Value(std::vector<std::byte>&proof,const T&v){if(proof.size()>512*1024-sizeof(v))return false;const auto n=proof.size();proof.resize(n+sizeof(v));std::memcpy(proof.data()+n,&v,sizeof(v));return true;}
[[maybe_unused]]bool Text(std::uintptr_t p,std::size_t max,std::string&out,bool ascii_key=false){
 std::array<std::byte,32>a{},z{};if(!Bytes(p,a.data(),a.size()))return false;std::uint64_t length=0,cap=0;std::uintptr_t data=p;
 std::memcpy(&length,a.data()+16,8);std::memcpy(&cap,a.data()+24,8);if(length>max||length>cap||cap<15||cap>0x1000000)return false;
 if(cap==15){if(length>15)return false;}else std::memcpy(&data,a.data(),8);
 std::vector<char>text(static_cast<std::size_t>(length)+1);if(!Bytes(data,text.data(),text.size())||text[length]||std::memchr(text.data(),0,static_cast<std::size_t>(length))||!Bytes(p,z.data(),z.size())||a!=z)return false;
 if(length&&MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),static_cast<int>(length),nullptr,0)==0)return false;
 if(ascii_key){if(!length)return false;for(std::size_t i=0;i<length;++i){const auto c=text[i];if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_'||c=='.'||c=='-'))return false;}}
 out.assign(text.data(),static_cast<std::size_t>(length));return true;
}
[[maybe_unused]]bool Array(std::uintptr_t at,std::size_t max,std::uintptr_t&data,std::int32_t&count,std::vector<std::byte>&proof,bool semantic=true){
 std::int32_t capacity=0;if(!At(at,0,data)||!At(at,8,capacity)||!At(at,12,count)||count<0||static_cast<std::size_t>(count)>max||capacity<count||capacity>0x1000000||(count&&!data))return false;
 if(!semantic&&!Value(proof,data))return false;return Value(proof,count);
}
[[maybe_unused]]bool Key(std::uintptr_t image,std::uintptr_t definition,std::string&key,std::vector<std::byte>&proof){
 std::uintptr_t vb=0,secondary=0;std::uint32_t magic=0,index=0;
 return definition&&Typed(definition,image,lyd_personal_pins::kSTenetPrimaryVtableRva)&&At(definition,8,vb)&&vb==image+lyd_personal_pins::kSTenetVbtableRva&&At(definition,0x10A8,secondary)&&secondary==image+lyd_personal_pins::kSTenetSecondary10A8VtableRva&&At(definition,0x38,magic)&&magic==0x4744624F&&At(definition,0x10,index)&&index!=0xFFFFFFFFU&&Text(definition+0x18,192,key,true)&&Value(proof,definition)&&Value(proof,index)&&Value(proof,magic)&&Value(proof,static_cast<std::uint32_t>(key.size()))&&([&]{for(const auto c:key)if(!Value(proof,c))return false;return true;})();
}
} // namespace lyd_common
