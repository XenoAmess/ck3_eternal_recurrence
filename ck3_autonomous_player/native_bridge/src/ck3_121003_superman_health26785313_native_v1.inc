// Fixed original20 case role references and product14 ScriptValues only.
// No CCharacter health/base-skill offsets, generic script names or caller scope.
namespace {
struct HealthAny267V1{std::uintptr_t type=0;std::array<std::byte,32>storage{};};static_assert(sizeof(HealthAny267V1)==40);
struct HealthArgTable267V1{HealthAny267V1*data=nullptr;std::uint32_t capacity=1,count=1;std::uintptr_t allocator=0;};
struct HealthArgCursor267V1{HealthArgTable267V1*table=nullptr;std::uint32_t index=0,reserved=0;};
using HealthNames267V1=std::array<std::string,40>;
[[maybe_unused]]bool HealthDestroy267V1(HealthAny267V1&v,std::uintptr_t empty,std::uintptr_t ref,std::uintptr_t fixed)noexcept{
 __try{if(v.type!=empty&&v.type!=ref&&v.type!=fixed)return false;const auto vt=*reinterpret_cast<const std::uintptr_t*>(v.type);reinterpret_cast<void(__fastcall*)(void*,void*)>(*reinterpret_cast<const std::uintptr_t*>(vt+0x18))(reinterpret_cast<void*>(v.type),v.storage.data());v={};v.type=empty;return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool HealthReadNumeric267V1(const ReadonlyBindings&b,std::int32_t actor,const HealthNames267V1&names,SupermanHealthNumeric267V1&out)noexcept{
 out={};HealthAny267V1 root{},reverse{},text{},value{};std::uintptr_t empty=0,ref=0,fixed=0,string_type=0;bool init=false,text_entered=false,text_complete=false,good=false;const auto image=b.module_base;
 __try{
  using Factory=std::uintptr_t(__fastcall*)();empty=reinterpret_cast<Factory>(image+0x8B2EF0)();ref=reinterpret_cast<Factory>(image+0x8B5030)();fixed=reinterpret_cast<Factory>(image+0xA3FDD0)();string_type=reinterpret_cast<Factory>(image+0x8C21D0)();root.type=reverse.type=text.type=value.type=empty;init=true;out.entered=true;
  do{
   void*actual=ck3_1210::ResolveCoreCharacter(b.core,actor);if(!actual||!reinterpret_cast<bool(__fastcall*)(void*,HealthAny267V1*)>(image+0x2BA7A20)(actual,&root)||root.type!=ref)break;
   std::uint32_t root_tag=0;std::uint64_t root_id=0;std::memcpy(&root_tag,root.storage.data(),4);std::memcpy(&root_id,root.storage.data()+8,8);if(root_tag!=4||root_id!=static_cast<std::uint32_t>(actor))break;
   bool complete=true;
   // Actual loaded ScriptValue definition must exist before native callback;
   // its authored balance expression may legitimately yield zero.
   for(std::size_t m=0;m<14;++m){const auto name=kSupermanHealthValueNames267V1[m];const auto db=reinterpret_cast<Factory>(image+0xA6E9B0)();const auto hash=reinterpret_cast<std::uint32_t(__fastcall*)(std::uint32_t,const char*,std::uint32_t)>(image+0x4503FF0)(0,name.data(),static_cast<std::uint32_t>(name.size()));out.definitions[m]=reinterpret_cast<std::uintptr_t(__fastcall*)(std::uintptr_t,std::uint32_t)>(image+0xA6E870)(db,hash);if(!out.definitions[m]||*reinterpret_cast<const std::uint32_t*>(out.definitions[m]+0x38)!=0x4744624F){complete=false;break;}}
   if(!complete)break;
   for(std::size_t n=0;n<42;++n){const char*name=n<40?names[n].c_str():(n==40?"sxat_health_baseline_ready":"sxat_health_matrix_done");
    text.type=string_type;std::uint64_t cap=15;std::memcpy(text.storage.data()+24,&cap,8);text_entered=true;text_complete=false;reinterpret_cast<void*(__fastcall*)(void*,const char*,std::size_t)>(image+0x896BB0)(text.storage.data(),name,std::strlen(name));text_complete=true;
    HealthArgTable267V1 table{&text};HealthArgCursor267V1 args{&table};const auto borrowed=reinterpret_cast<const std::byte*(__fastcall*)(const void*,const HealthArgCursor267V1*)>(image+0x3D26A70)(root.storage.data(),&args);if(!borrowed){complete=false;break;}
    std::array<std::byte,16>before{},after{};std::memcpy(before.data(),borrowed,16);std::uint16_t tag=0;std::memcpy(&tag,before.data(),2);
    if(n<40){
     std::uint64_t full_id=0;std::memcpy(&full_id,before.data()+8,8);if(tag!=4||full_id>0xFFFFFFFF||static_cast<std::uint32_t>(full_id)==0xFFFFFFFF){complete=false;break;}const auto id=static_cast<std::int32_t>(full_id);if((n==0&&id!=actor)){complete=false;break;}
     for(std::size_t prior=0;prior<n;++prior)if(out.characters[prior]&&out.references[prior]==before)complete=false;if(!complete)break;
     auto*character=ck3_1210::ResolveCoreCharacter(b.core,id);if(!character){complete=false;break;}out.characters[n]=reinterpret_cast<std::uintptr_t>(character);
     if(!HealthDestroy267V1(reverse,empty,ref,fixed)||!reinterpret_cast<bool(__fastcall*)(void*,HealthAny267V1*)>(image+0x2BA7A20)(character,&reverse)||reverse.type!=ref||std::memcmp(reverse.storage.data(),before.data(),16)){complete=false;break;}out.references[n]=before;
    }else if(tag==1){if(!HealthDestroy267V1(value,empty,ref,fixed)||!reinterpret_cast<bool(__fastcall*)(const void*,HealthAny267V1*,const HealthArgCursor267V1*)>(image+0x3D5CCE0)(borrowed,&value,&args)||value.type!=fixed){complete=false;break;}std::int64_t raw=0,stored=0;std::memcpy(&raw,value.storage.data(),8);std::memcpy(&stored,before.data()+8,8);if(raw!=stored){complete=false;break;}out.phase_vars[n-40]=raw;}
    std::memcpy(after.data(),borrowed,16);if(before!=after){complete=false;break;}
    reinterpret_cast<void(__fastcall*)(void*)>(image+0x897460)(text.storage.data());text={};text.type=empty;text_entered=text_complete=false;
   }
   if(!complete)break;
   for(std::size_t n=0;n<40&&complete;++n)for(std::size_t m=0;m<14;++m){
    const auto name=kSupermanHealthValueNames267V1[m];text.type=string_type;std::uint64_t cap=15;std::memcpy(text.storage.data()+24,&cap,8);text_entered=true;text_complete=false;reinterpret_cast<void*(__fastcall*)(void*,const char*,std::size_t)>(image+0x896BB0)(text.storage.data(),name.data(),name.size());text_complete=true;
    HealthArgTable267V1 table{&text};HealthArgCursor267V1 args{&table};if(!HealthDestroy267V1(value,empty,ref,fixed)||!reinterpret_cast<bool(__fastcall*)(const void*,HealthAny267V1*,const HealthArgCursor267V1*)>(image+0x3D5DBC0)(out.references[n].data(),&value,&args)||value.type!=fixed){complete=false;break;}std::memcpy(&out.values[n][m],value.storage.data(),8);
    reinterpret_cast<void(__fastcall*)(void*)>(image+0x897460)(text.storage.data());text={};text.type=empty;text_entered=text_complete=false;
   }
   good=complete;
  }while(false);
 }__except(EXCEPTION_EXECUTE_HANDLER){out.cleanup_known=false;}
 if(text_entered){if(!text_complete)out.cleanup_known=false;else{__try{reinterpret_cast<void(__fastcall*)(void*)>(image+0x897460)(text.storage.data());}__except(EXCEPTION_EXECUTE_HANDLER){out.cleanup_known=false;}}}
 if(init){if(!HealthDestroy267V1(value,empty,ref,fixed)||!HealthDestroy267V1(reverse,empty,ref,fixed)||!HealthDestroy267V1(root,empty,ref,fixed))out.cleanup_known=false;}
 return good&&out.cleanup_known;
}
}
