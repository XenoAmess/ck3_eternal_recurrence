// SOURCE_ONLY: fixed Main/Viv creator routes only. Requires actual confirmation/modal/panel, current player/owner/private lease. No arbitrary script/key/row or dynamic AddScope.
namespace {
struct CourtierAny267V1 {std::uintptr_t type=0;std::array<std::byte,32> storage{};};
static_assert(sizeof(CourtierAny267V1)==40);
struct CourtierArgTable267V1 {CourtierAny267V1*data=nullptr;};
struct CourtierArgCursor267V1 {CourtierArgTable267V1*table=nullptr;std::uint32_t index=0,reserved=0;};
enum class CourtierNativePhase267V1{read_predicates,execute_fixed_route};
struct CourtierNative267V1{
 std::uintptr_t definition=0;
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
// Both enum values are validated before one of the eight reviewed literal keys.
[[maybe_unused]]bool NativeFixedCourtier267V1(std::uintptr_t image,void*actual_character,std::uint32_t actor,
 CourtierProduct267V1 product,CourtierControl267V1 control,std::uint64_t wall_deadline,std::uint64_t monotonic_deadline,std::uintptr_t expected_definition,CourtierNativePhase267V1 phase,CourtierNative267V1&out)noexcept{
 out={};if(!actual_character||static_cast<unsigned>(product)>1||static_cast<unsigned>(control)>3)return false;
 constexpr std::array<std::array<const char*,4>,2>keys{{
  {{"xar_cc_cancel_gui","xar_cc_confirm_gui","xar_cc_age_minus_1_gui","xar_cc_age_plus_1_gui"}},
  {{"ervc_cc_cancel_gui","ervc_cc_confirm_gui","ervc_cc_age_minus_1_gui","ervc_cc_age_plus_1_gui"}}
 }};
 const auto key=keys[static_cast<unsigned>(product)][static_cast<unsigned>(control)];const auto length=std::strlen(key);
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
    if(!out.shown||!out.valid)break;
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
