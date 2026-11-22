// SOURCE_ONLY: fixed Main/Viv creator routes only. Requires actual confirmation/modal/panel, current player/owner/private lease. No arbitrary script/key/row or dynamic AddScope.
namespace {
struct CourtierAny267V1 {std::uintptr_t type=0;std::array<std::byte,32> storage{};};
static_assert(sizeof(CourtierAny267V1)==40);
struct CourtierArgTable267V1 {CourtierAny267V1*data=nullptr;std::uint32_t capacity=1,count=1;std::uintptr_t allocator=0;};
struct CourtierArgCursor267V1 {CourtierArgTable267V1*table=nullptr;std::uint32_t index=0,reserved=0;};
enum class CourtierNativePhase267V1{read_predicates,execute_fixed_route};
struct CourtierNative267V1{
 std::uintptr_t definition=0,cost_definition=0;
 CourtierConfigurationValues267V1 configuration;
 bool entered=false,shown=false,valid=false,effect_entered=false,native_returned=false,cleanup_known=true;
};
[[maybe_unused]]bool CourtierReferenceMatches267V1(const void*scope,std::uint32_t actor)noexcept{
 if(!scope)return false;
 __try{std::uint32_t tag=0;std::uint64_t id=0;std::memcpy(&tag,scope,4);std::memcpy(&id,static_cast<const std::byte*>(scope)+8,8);return tag==4&&id==actor;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool DestroyCourtierAny267V1(CourtierAny267V1&any,std::uintptr_t empty,std::uintptr_t reference,std::uintptr_t top,std::uintptr_t boolean)noexcept{
 __try{
  if(any.type!=empty&&any.type!=reference&&any.type!=top&&any.type!=boolean)return false;
  const auto table=*reinterpret_cast<const std::uintptr_t*>(any.type);
  const auto destroy=*reinterpret_cast<const std::uintptr_t*>(table+0x18);
  reinterpret_cast<void(__fastcall*)(void*,void*)>(destroy)(reinterpret_cast<void*>(any.type),any.storage.data());
  any={};any.type=empty;return true;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}

// Exact callbacks: Var(ref, ArgCursor)->borrowed native ref; GetValue(ref,out,ArgCursor)
// and ScriptValue(ref,out,ArgCursor). Read only reviewed product names.
[[maybe_unused]]bool ReadCourtierConfigurationValues267V1(std::uintptr_t image,const CourtierAny267V1&root,CourtierProduct267V1 product,CourtierConfigurationValues267V1&out,std::uintptr_t&cost_definition,bool&cleanup_known)noexcept{
 out={};cost_definition=0;cleanup_known=true;
 constexpr std::array<std::array<const char*,10>,2>names{{
  {{"xar_cc_age","xar_cc_female","xar_cc_diplomacy","xar_cc_martial","xar_cc_stewardship","xar_cc_intrigue","xar_cc_learning","xar_cc_prowess","xar_cc_same_house","xar_courtier_creator_cost"}},
  {{"ervc_cc_age","ervc_cc_female","ervc_cc_diplomacy","ervc_cc_martial","ervc_cc_stewardship","ervc_cc_intrigue","ervc_cc_learning","ervc_cc_prowess","ervc_cc_same_house","ervc_courtier_creator_cost"}}
 }};
 using Factory=std::uintptr_t(__fastcall*)();CourtierAny267V1 text{},value{};
 std::uintptr_t empty=0,string_type=0,fixed=0;bool initialized=false,text_entered=false,text_complete=false,good=false;
 __try{
  empty=reinterpret_cast<Factory>(image+0x8B2EF0)();string_type=reinterpret_cast<Factory>(image+0x8C21D0)();fixed=reinterpret_cast<Factory>(image+0xA3FDD0)();
  text.type=value.type=empty;initialized=true;
  do{
   for(std::size_t n=0;n<10;++n){
    const auto name=names[static_cast<unsigned>(product)][n];
    text.type=string_type;std::uint64_t cap=15;std::memcpy(text.storage.data()+24,&cap,8);text_entered=true;text_complete=false;
    reinterpret_cast<void*(__fastcall*)(void*,const char*,std::size_t)>(image+0x896BB0)(text.storage.data(),name,std::strlen(name));text_complete=true;
    CourtierArgTable267V1 table{&text,1,1,0};CourtierArgCursor267V1 args{&table,0,0};
    bool available=false;
    if(n<9){
     const auto actual=reinterpret_cast<const std::byte*(__fastcall*)(const void*,const CourtierArgCursor267V1*)>(image+0x3D26A70)(root.storage.data(),&args);
     if(!actual)break;
     std::array<std::byte,16> before{},after{};std::memcpy(before.data(),actual,16);std::uint16_t tag=0;std::memcpy(&tag,before.data(),2);
     if(tag==1){
      if(!reinterpret_cast<bool(__fastcall*)(const void*,CourtierAny267V1*,const CourtierArgCursor267V1*)>(image+0x3D5CCE0)(actual,&value,&args)||value.type!=fixed)break;
      std::int64_t raw=0,original=0;std::memcpy(&raw,value.storage.data(),8);std::memcpy(&original,before.data()+8,8);std::memcpy(after.data(),actual,16);if(before!=after||raw!=original)break;out.raw[n]=raw;
     }
     available=true;
    }else{
     // The original ScriptValue callback returns zero for missing names. Bind its
     // actual loaded registry definition first; missing never becomes fake 0.
     const auto db=reinterpret_cast<Factory>(image+0xA6E9B0)();
     const auto hash=reinterpret_cast<std::uint32_t(__fastcall*)(std::uint32_t,const char*,std::uint32_t)>(image+0x4503FF0)(0,name,static_cast<std::uint32_t>(std::strlen(name)));
     const auto definition=reinterpret_cast<std::uintptr_t(__fastcall*)(std::uintptr_t,std::uint32_t)>(image+0xA6E870)(db,hash);
     if(!definition)break;std::uint32_t magic=0;std::memcpy(&magic,reinterpret_cast<const void*>(definition+0x38),4);
     if(magic==0x4744624F){
      if(!reinterpret_cast<bool(__fastcall*)(const void*,CourtierAny267V1*,const CourtierArgCursor267V1*)>(image+0x3D5DBC0)(root.storage.data(),&value,&args)||value.type!=fixed)break;
      std::int64_t raw=0;std::memcpy(&raw,value.storage.data(),8);out.raw[n]=raw;cost_definition=definition;
     }
     available=true;
    }
    reinterpret_cast<void(__fastcall*)(void*)>(image+0x897460)(text.storage.data());text={};text.type=empty;text_entered=text_complete=false;
    if(!available)break;if(n==9)good=true;
   }
  }while(false);
 }__except(EXCEPTION_EXECUTE_HANDLER){good=false;cleanup_known=false;}
 bool clean=true;
 if(text_entered){if(!text_complete)clean=false;else{__try{reinterpret_cast<void(__fastcall*)(void*)>(image+0x897460)(text.storage.data());}__except(EXCEPTION_EXECUTE_HANDLER){clean=false;}}}
 if(initialized){__try{if(value.type!=empty&&value.type!=fixed)clean=false;else{const auto vt=*reinterpret_cast<const std::uintptr_t*>(value.type);reinterpret_cast<void(__fastcall*)(void*,void*)>(*reinterpret_cast<const std::uintptr_t*>(vt+0x18))(reinterpret_cast<void*>(value.type),value.storage.data());}}__except(EXCEPTION_EXECUTE_HANDLER){clean=false;}}
 cleanup_known=cleanup_known&&clean;return good&&cleanup_known;
}

// Both enum values are validated before one of the eight reviewed literal keys.
[[maybe_unused]]bool NativeFixedCourtier267V1(std::uintptr_t image,void*actual_character,std::uint32_t actor,
 CourtierProduct267V1 product,CourtierSetting267V1 setting,std::uint64_t wall_deadline,std::uint64_t monotonic_deadline,std::uintptr_t expected_definition,CourtierNativePhase267V1 phase,CourtierNative267V1&out)noexcept{
 out={};if(!actual_character||static_cast<unsigned>(product)>1||static_cast<unsigned>(setting)>3)return false;
 constexpr std::array<std::array<const char*,4>,2>keys{{
  {{"xar_cc_choose_female_gui","xar_cc_diplomacy_plus_10_gui","xar_cc_prowess_plus_10_gui","xar_cc_choose_same_house_gui"}},
  {{"ervc_cc_choose_female_gui","ervc_cc_diplomacy_plus_10_gui","ervc_cc_prowess_plus_10_gui","ervc_cc_choose_same_house_gui"}}
 }};
 const auto key=keys[static_cast<unsigned>(product)][static_cast<unsigned>(setting)];const auto length=std::strlen(key);
 CourtierAny267V1 reference_any{},top_any{},bool_any{};
 std::array<std::byte,32> text{};
 std::uintptr_t empty_type=0,reference_type=0,top_type=0,bool_type=0,builder=0;
 bool initialized=false,string_entered=false,string_complete=false,scope_complete=false,okay=false;
 std::uint64_t cap=15;std::memcpy(text.data()+24,&cap,8);
 out.entered=true;
 __try{
  using Factory=std::uintptr_t(__fastcall*)();
  empty_type=reinterpret_cast<Factory>(image+0x8B2EF0)();
  reference_type=reinterpret_cast<Factory>(image+0x8B5030)();
  top_type=reinterpret_cast<Factory>(image+0x16AFB60)();
  bool_type=reinterpret_cast<Factory>(image+0x8C2930)();
  reference_any.type=top_any.type=bool_any.type=empty_type;initialized=true;
  do{
   using MakeScope=bool(__fastcall*)(void*,CourtierAny267V1*);
   if(!reinterpret_cast<MakeScope>(image+0x2BA7A20)(actual_character,&reference_any)||reference_any.type!=reference_type||!CourtierReferenceMatches267V1(reference_any.storage.data(),actor))break;
   // Current GuiScope getter resets a real 0x170 native builder. SetRoot's
   // actual registration field offset is zero; the callback writes its 16B
   // native reference there. End moves the full native builder into owned Any.
   builder=reinterpret_cast<Factory>(image+0x3D42F70)();
   if(builder!=image+0x6B03530)break;
   CourtierArgTable267V1 reference_table{&reference_any};CourtierArgCursor267V1 reference_args{&reference_table,0,0};
   using SetRoot=void*(__fastcall*)(void*,const CourtierArgCursor267V1*);
   if(reinterpret_cast<SetRoot>(image+0x3D5D7F0)(reinterpret_cast<void*>(builder),&reference_args)!=reinterpret_cast<void*>(builder)||!CourtierReferenceMatches267V1(reinterpret_cast<void*>(builder),actor))break;
   using End=bool(__fastcall*)(void*,CourtierAny267V1*);
   if(!reinterpret_cast<End>(image+0x3D5D8C0)(reinterpret_cast<void*>(builder),&top_any)||top_any.type!=top_type)break;
   scope_complete=true;
   const auto top=*reinterpret_cast<const std::uintptr_t*>(top_any.storage.data());
   if(!CourtierReferenceMatches267V1(reinterpret_cast<void*>(top),actor))break;
   if(!ReadCourtierConfigurationValues267V1(image,reference_any,product,out.configuration,out.cost_definition,out.cleanup_known))break;
   using Assign=void*(__fastcall*)(void*,const char*,std::size_t);
   string_entered=true;reinterpret_cast<Assign>(image+0x896BB0)(text.data(),key,static_cast<std::size_t>(length));string_complete=true;
   using Lookup=void*(__fastcall*)(const void*);
   out.definition=reinterpret_cast<std::uintptr_t>(reinterpret_cast<Lookup>(image+0x3D42F00)(text.data()));
   if(!out.definition||(expected_definition&&out.definition!=expected_definition))break;
   CourtierArgTable267V1 top_table{&top_any};CourtierArgCursor267V1 top_args{&top_table,0,0};
   using Predicate=bool(__fastcall*)(void*,CourtierAny267V1*,const CourtierArgCursor267V1*);
   if(!reinterpret_cast<Predicate>(image+0x3DD1970)(reinterpret_cast<void*>(out.definition),&bool_any,&top_args)||bool_any.type!=bool_type||std::to_integer<unsigned>(bool_any.storage.front())>1)break;
   out.shown=bool_any.storage.front()!=std::byte{};
   if(!reinterpret_cast<Predicate>(image+0x3DD19D0)(reinterpret_cast<void*>(out.definition),&bool_any,&top_args)||bool_any.type!=bool_type||std::to_integer<unsigned>(bool_any.storage.front())>1)break;
   out.valid=bool_any.storage.front()!=std::byte{};
   if(!CourtierReferenceMatches267V1(reinterpret_cast<void*>(top),actor))break;
   if(phase==CourtierNativePhase267V1::execute_fixed_route){
    if(!out.shown||!out.valid||!std::all_of(out.configuration.raw.begin(),out.configuration.raw.end(),[](const auto&v){return v.has_value();}))break;
    const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
    if(!wall_deadline||!monotonic_deadline||wall<=0||static_cast<std::uint64_t>(wall)>=wall_deadline||GetTickCount64()>=monotonic_deadline)break;
    // The typed thunk validates the engine-owned TopScope and adjusts the
    // real ScriptedGui receiver through its current virtual base descriptor.
    out.effect_entered=true;
    if(!reinterpret_cast<Predicate>(image+0x3DD18A0)(reinterpret_cast<void*>(out.definition),&bool_any,&top_args)){out.cleanup_known=false;break;}
    out.native_returned=true;
   }
   okay=true;
  }while(false);
 }__except(EXCEPTION_EXECUTE_HANDLER){out.cleanup_known=false;}
 if(string_complete){__try{reinterpret_cast<void(__fastcall*)(void*)>(image+0x897460)(text.data());}__except(EXCEPTION_EXECUTE_HANDLER){out.cleanup_known=false;}}
 else if(string_entered)out.cleanup_known=false;
 if(initialized){
  if(!DestroyCourtierAny267V1(bool_any,empty_type,reference_type,top_type,bool_type))out.cleanup_known=false;
  // A partially constructed allocated TopScope is never falsely declared
  // clean or destroyed as if its full native constructor had returned.
  if(scope_complete||top_any.type==empty_type){if(!DestroyCourtierAny267V1(top_any,empty_type,reference_type,top_type,bool_type))out.cleanup_known=false;}
  else out.cleanup_known=false;
  if(!DestroyCourtierAny267V1(reference_any,empty_type,reference_type,top_type,bool_type))out.cleanup_known=false;
 }
 return okay&&out.cleanup_known;
}
}
