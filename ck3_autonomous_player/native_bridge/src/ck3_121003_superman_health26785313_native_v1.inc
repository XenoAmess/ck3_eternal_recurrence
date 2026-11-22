// Fixed original20 role references and product14 ScriptValues. Diagnostic DATA
// records only the last actual native stage; all original guards remain required.
namespace {
struct HealthAny267V1{std::uintptr_t type=0;std::array<std::byte,32>storage{};};static_assert(sizeof(HealthAny267V1)==40);
struct HealthArgTable267V1{HealthAny267V1*data=nullptr;std::uint32_t capacity=1,count=1;std::uintptr_t allocator=0;};
struct HealthArgCursor267V1{HealthArgTable267V1*table=nullptr;std::uint32_t index=0,reserved=0;};
using HealthNames267V1=std::array<std::string,40>;
struct HealthNumericDiagnostic267V1{const char*stage="factories";int role=-1,value=-1;bool exception=false;const char*cleanup=nullptr;};
[[maybe_unused]]std::string HealthNumericReason267V1(const HealthNumericDiagnostic267V1&d){
 std::string s="superman_health_numeric_";if(d.exception)s+="exception_at_";s+=d.stage;
 if(d.role>=0&&d.role<40){s+="_role_";s+=kSupermanHealthCases267V1[static_cast<std::size_t>(d.role)/2];s+=d.role%2?"_donor":"_receiver";}
 else if(d.role==40)s+="_phase_baseline_ready";else if(d.role==41)s+="_phase_matrix_done";
 if(d.value>=0&&d.value<14){s+="_value_";s+=kSupermanHealthValueNames267V1[static_cast<std::size_t>(d.value)];}
 if(d.cleanup){s+="_cleanup_unknown_at_";s+=d.cleanup;}return s;
}
// Current859 Any equality8B50A0 compares WORD0, WORD2 and QWORD8.
// MakeScope2BA7A20 does not initialize bytes4..7; they are not identity.
[[maybe_unused]]bool HealthReferenceIdentity267V1(const void*a,const void*z)noexcept{
 std::uint32_t ah=0,zh=0;std::uint64_t av=0,zv=0;std::memcpy(&ah,a,4);std::memcpy(&zh,z,4);std::memcpy(&av,static_cast<const std::byte*>(a)+8,8);std::memcpy(&zv,static_cast<const std::byte*>(z)+8,8);return ah==zh&&av==zv;
}
[[maybe_unused]]bool HealthDestroy267V1(HealthAny267V1&v,std::uintptr_t empty,std::uintptr_t ref,std::uintptr_t fixed)noexcept{
 __try{if(v.type!=empty&&v.type!=ref&&v.type!=fixed)return false;const auto vt=*reinterpret_cast<const std::uintptr_t*>(v.type);reinterpret_cast<void(__fastcall*)(void*,void*)>(*reinterpret_cast<const std::uintptr_t*>(vt+0x18))(reinterpret_cast<void*>(v.type),v.storage.data());v={};v.type=empty;return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool HealthReadNumeric267V1(const ReadonlyBindings&b,std::int32_t actor,const HealthNames267V1&names,SupermanHealthNumeric267V1&out,HealthNumericDiagnostic267V1&diag)noexcept{
 out={};diag={};HealthAny267V1 root{},reverse{},text{},value{};std::uintptr_t empty=0,ref=0,fixed=0,string_type=0;bool init=false,text_entered=false,text_complete=false,good=false;const auto image=b.module_base;
 __try{
  using Factory=std::uintptr_t(__fastcall*)();diag.stage="empty_factory";empty=reinterpret_cast<Factory>(image+0x8B2EF0)();diag.stage="reference_factory";ref=reinterpret_cast<Factory>(image+0x8B5030)();diag.stage="fixed_factory";fixed=reinterpret_cast<Factory>(image+0xA3FDD0)();diag.stage="string_factory";string_type=reinterpret_cast<Factory>(image+0x8C21D0)();root.type=reverse.type=text.type=value.type=empty;init=true;out.entered=true;
  do{
   diag.stage="root_resolve";void*actual=ck3_1210::ResolveCoreCharacter(b.core,actor);if(!actual)break;
   diag.stage="root_make_scope";if(!reinterpret_cast<bool(__fastcall*)(void*,HealthAny267V1*)>(image+0x2BA7A20)(actual,&root))break;
   diag.stage="root_any_type";if(root.type!=ref)break;
   std::uint32_t root_tag=0;std::uint64_t root_id=0;std::memcpy(&root_tag,root.storage.data(),4);std::memcpy(&root_id,root.storage.data()+8,8);diag.stage="root_reference_identity";if(root_tag!=4||root_id!=static_cast<std::uint32_t>(actor))break;
   bool complete=true;
   for(std::size_t m=0;m<14;++m){diag.value=static_cast<int>(m);const auto name=kSupermanHealthValueNames267V1[m];diag.stage="loaded_value_database";const auto db=reinterpret_cast<Factory>(image+0xA6E9B0)();diag.stage="loaded_value_hash";const auto hash=reinterpret_cast<std::uint32_t(__fastcall*)(std::uint32_t,const char*,std::uint32_t)>(image+0x4503FF0)(0,name.data(),static_cast<std::uint32_t>(name.size()));diag.stage="loaded_value_lookup";out.definitions[m]=reinterpret_cast<std::uintptr_t(__fastcall*)(std::uintptr_t,std::uint32_t)>(image+0xA6E870)(db,hash);if(!out.definitions[m]){complete=false;break;}diag.stage="loaded_value_definition_type";if(*reinterpret_cast<const std::uint32_t*>(out.definitions[m]+0x38)!=0x4744624F){complete=false;break;}}
   if(!complete)break;diag.value=-1;
   for(std::size_t n=0;n<42;++n){diag.role=static_cast<int>(n);const char*name=n<40?names[n].c_str():(n==40?"sxat_health_baseline_ready":"sxat_health_matrix_done");
    text.type=string_type;std::uint64_t cap=15;std::memcpy(text.storage.data()+24,&cap,8);text_entered=true;text_complete=false;diag.stage="variable_key_construct";reinterpret_cast<void*(__fastcall*)(void*,const char*,std::size_t)>(image+0x896BB0)(text.storage.data(),name,std::strlen(name));text_complete=true;
    HealthArgTable267V1 table{&text};HealthArgCursor267V1 args{&table};diag.stage="variable_lookup";const auto borrowed=reinterpret_cast<const std::byte*(__fastcall*)(const void*,const HealthArgCursor267V1*)>(image+0x3D26A70)(root.storage.data(),&args);if(!borrowed){complete=false;break;}
    std::array<std::byte,16>before{},after{};diag.stage="variable_reference_read";std::memcpy(before.data(),borrowed,16);std::uint16_t tag=0;std::memcpy(&tag,before.data(),2);
    if(n<40){
     std::uint64_t full_id=0;std::memcpy(&full_id,before.data()+8,8);diag.stage="role_reference_tag";if(tag!=4){complete=false;break;}diag.stage="role_reference_id";if(full_id>0xFFFFFFFF||static_cast<std::uint32_t>(full_id)==0xFFFFFFFF){complete=false;break;}const auto id=static_cast<std::int32_t>(full_id);diag.stage="role_root_identity";if(n==0&&id!=actor){complete=false;break;}
     diag.stage="role_reference_unique";for(std::size_t prior=0;prior<n;++prior)if(out.characters[prior]&&HealthReferenceIdentity267V1(out.references[prior].data(),before.data()))complete=false;if(!complete)break;
     diag.stage="role_character_resolve";auto*character=ck3_1210::ResolveCoreCharacter(b.core,id);if(!character){complete=false;break;}out.characters[n]=reinterpret_cast<std::uintptr_t>(character);
     diag.stage="role_reverse_destroy";if(!HealthDestroy267V1(reverse,empty,ref,fixed)){complete=false;break;}diag.stage="role_reverse_make_scope";if(!reinterpret_cast<bool(__fastcall*)(void*,HealthAny267V1*)>(image+0x2BA7A20)(character,&reverse)){complete=false;break;}diag.stage="role_reverse_any_type";if(reverse.type!=ref){complete=false;break;}diag.stage="role_reverse_reference_identity";if(!HealthReferenceIdentity267V1(reverse.storage.data(),before.data())){complete=false;break;}out.references[n]=before;
    }else if(tag==1){diag.stage="phase_value_destroy";if(!HealthDestroy267V1(value,empty,ref,fixed)){complete=false;break;}diag.stage="phase_value_getter";if(!reinterpret_cast<bool(__fastcall*)(const void*,HealthAny267V1*,const HealthArgCursor267V1*)>(image+0x3D5CCE0)(borrowed,&value,&args)){complete=false;break;}diag.stage="phase_value_any_type";if(value.type!=fixed){complete=false;break;}std::int64_t raw=0,stored=0;std::memcpy(&raw,value.storage.data(),8);std::memcpy(&stored,before.data()+8,8);diag.stage="phase_value_identity";if(raw!=stored){complete=false;break;}out.phase_vars[n-40]=raw;}
    diag.stage="variable_reference_stable";std::memcpy(after.data(),borrowed,16);if(before!=after){complete=false;break;}
    diag.stage="variable_key_destroy";reinterpret_cast<void(__fastcall*)(void*)>(image+0x897460)(text.storage.data());text={};text.type=empty;text_entered=text_complete=false;
   }
   if(!complete)break;
   for(std::size_t n=0;n<40&&complete;++n)for(std::size_t m=0;m<14;++m){diag.role=static_cast<int>(n);diag.value=static_cast<int>(m);
    const auto name=kSupermanHealthValueNames267V1[m];text.type=string_type;std::uint64_t cap=15;std::memcpy(text.storage.data()+24,&cap,8);text_entered=true;text_complete=false;diag.stage="script_value_key_construct";reinterpret_cast<void*(__fastcall*)(void*,const char*,std::size_t)>(image+0x896BB0)(text.storage.data(),name.data(),name.size());text_complete=true;
    HealthArgTable267V1 table{&text};HealthArgCursor267V1 args{&table};diag.stage="script_value_destroy";if(!HealthDestroy267V1(value,empty,ref,fixed)){complete=false;break;}diag.stage="script_value_getter";if(!reinterpret_cast<bool(__fastcall*)(const void*,HealthAny267V1*,const HealthArgCursor267V1*)>(image+0x3D5DBC0)(out.references[n].data(),&value,&args)){complete=false;break;}diag.stage="script_value_any_type";if(value.type!=fixed){complete=false;break;}std::memcpy(&out.values[n][m],value.storage.data(),8);
    diag.stage="script_value_key_destroy";reinterpret_cast<void(__fastcall*)(void*)>(image+0x897460)(text.storage.data());text={};text.type=empty;text_entered=text_complete=false;
   }
   good=complete;
  }while(false);
 }__except(EXCEPTION_EXECUTE_HANDLER){diag.exception=true;out.cleanup_known=false;}
 if(text_entered){if(!text_complete){diag.cleanup="incomplete_string";out.cleanup_known=false;}else{__try{reinterpret_cast<void(__fastcall*)(void*)>(image+0x897460)(text.storage.data());}__except(EXCEPTION_EXECUTE_HANDLER){diag.cleanup="string_destroy";out.cleanup_known=false;}}}
 if(init){if(!HealthDestroy267V1(value,empty,ref,fixed)){diag.cleanup="value_destroy";out.cleanup_known=false;}else if(!HealthDestroy267V1(reverse,empty,ref,fixed)){diag.cleanup="reverse_destroy";out.cleanup_known=false;}else if(!HealthDestroy267V1(root,empty,ref,fixed)){diag.cleanup="root_destroy";out.cleanup_known=false;}}
 return good&&out.cleanup_known;
}
}
