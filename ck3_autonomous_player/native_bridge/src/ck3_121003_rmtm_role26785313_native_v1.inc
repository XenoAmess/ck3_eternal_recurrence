#ifndef XAR_RMTM_ROLE_CALL_ADDRESS
#define XAR_RMTM_ROLE_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif
// SOURCE_ONLY. Existing exact859 ABI reuse; Native owner alone assembles/qualifies.
// Caller: actual application-main owner, current Core/full actor identity, original
// wall/monotonic deadline and serialized canonical GuiScope builder ownership.
// No arbitrary key, actor authorization, IsValid, Execute or effect invocation.
namespace {
struct RmtmRoleAny267V1 {std::uintptr_t type=0;std::array<std::byte,32>storage{};};
struct RmtmRoleArgTable267V1 {RmtmRoleAny267V1*data=nullptr;std::uint32_t capacity=1,count=1;std::uintptr_t allocator=0;};
struct RmtmRoleArgCursor267V1 {RmtmRoleArgTable267V1*table=nullptr;std::uint32_t index=0,reserved=0;};
static_assert(sizeof(RmtmRoleAny267V1)==40);
static_assert(sizeof(RmtmRoleArgTable267V1)==24);
static_assert(offsetof(RmtmRoleArgTable267V1,capacity)==8&&offsetof(RmtmRoleArgTable267V1,count)==12&&offsetof(RmtmRoleArgTable267V1,allocator)==16);
static_assert(sizeof(RmtmRoleArgCursor267V1)==16);
struct RmtmRoleNative267V1 {std::uintptr_t definition=0;bool entered=false,shown=false,cleanup_known=true;};
[[maybe_unused]]bool RmtmRoleBeforeDeadline267V1(std::uint64_t wall,std::uint64_t mono)noexcept{
 const auto now=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
 return wall&&mono&&now>0&&static_cast<std::uint64_t>(now)<wall&&GetTickCount64()<mono;
}
[[maybe_unused]]bool RmtmRoleReferenceMatches267V1(const void*scope,std::uint32_t actor)noexcept{
 if(!scope)return false;
 __try{std::uint32_t tag=0;std::uint64_t full=0;std::memcpy(&tag,scope,4);std::memcpy(&full,static_cast<const std::byte*>(scope)+8,8);return tag==4&&full==static_cast<std::uint64_t>(actor);}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool DestroyRmtmRoleAny267V1(RmtmRoleAny267V1&any,std::uintptr_t empty,std::uintptr_t reference,std::uintptr_t top,std::uintptr_t boolean)noexcept{
 __try{
  if(any.type!=empty&&any.type!=reference&&any.type!=top&&any.type!=boolean)return false;
  const auto table=*reinterpret_cast<const std::uintptr_t*>(any.type);
  const auto destroy=*reinterpret_cast<const std::uintptr_t*>(table+0x18);
  reinterpret_cast<void(__fastcall*)(void*,void*)>(destroy)(reinterpret_cast<void*>(any.type),any.storage.data());
  any={};any.type=empty;return true;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool NativeRmtmFixedPredicate267V1(std::uintptr_t image,void*actual_character,std::uint32_t actor,std::uint8_t predicate,
 std::uint64_t wall,std::uint64_t mono,RmtmRoleNative267V1&out)noexcept{
 out={};if(!image||!actual_character||!RmtmRoleBeforeDeadline267V1(wall,mono))return false;
 constexpr std::array<const char*,7> keys{"rqa120_native_song_role_gui","rqa120_native_successor_role_gui","rqa120_native_later_context_gui","rqa120_native_own_law_gui","rqa120_native_realm_law_gui","rqa120_native_ui_checkpoint_gui","rqa120_native_ready_succession_gui"};if(predicate>=keys.size())return false;const char*key=keys[predicate];
 RmtmRoleAny267V1 reference_any{},top_any{},bool_any{};std::array<std::byte,32>text{};
 std::uintptr_t empty_type=0,reference_type=0,top_type=0,bool_type=0,builder=0;
 bool initialized=false,string_entered=false,string_complete=false,scope_complete=false,okay=false;
 std::uint64_t cap=15;std::memcpy(text.data()+24,&cap,8);
 __try{
  using Factory=std::uintptr_t(__fastcall*)();
  do{
   out.entered=true;
   if(!RmtmRoleBeforeDeadline267V1(wall,mono))break;
   empty_type=reinterpret_cast<Factory>(XAR_RMTM_ROLE_CALL_ADDRESS(image,0x8B2EF0))();
   if(!RmtmRoleBeforeDeadline267V1(wall,mono))break;
   reference_type=reinterpret_cast<Factory>(XAR_RMTM_ROLE_CALL_ADDRESS(image,0x8B5030))();
   if(!RmtmRoleBeforeDeadline267V1(wall,mono))break;
   top_type=reinterpret_cast<Factory>(XAR_RMTM_ROLE_CALL_ADDRESS(image,0x16AFB60))();
   if(!RmtmRoleBeforeDeadline267V1(wall,mono))break;
   bool_type=reinterpret_cast<Factory>(XAR_RMTM_ROLE_CALL_ADDRESS(image,0x8C2930))();
   if(!RmtmRoleBeforeDeadline267V1(wall,mono))break;
   reference_any.type=top_any.type=bool_any.type=empty_type;initialized=true;
   using MakeScope=bool(__fastcall*)(void*,RmtmRoleAny267V1*);
   if(!RmtmRoleBeforeDeadline267V1(wall,mono))break;
   const bool made=reinterpret_cast<MakeScope>(XAR_RMTM_ROLE_CALL_ADDRESS(image,0x2BA7A20))(actual_character,&reference_any);
   if(!RmtmRoleBeforeDeadline267V1(wall,mono)||!made||reference_any.type!=reference_type||!RmtmRoleReferenceMatches267V1(reference_any.storage.data(),actor))break;
   if(!RmtmRoleBeforeDeadline267V1(wall,mono))break;
   builder=reinterpret_cast<Factory>(XAR_RMTM_ROLE_CALL_ADDRESS(image,0x3D42F70))();
   if(!RmtmRoleBeforeDeadline267V1(wall,mono)||builder!=image+0x6B03530)break;
   RmtmRoleArgTable267V1 reference_table{&reference_any,1,1,0};RmtmRoleArgCursor267V1 reference_args{&reference_table,0,0};
   using SetRoot=void*(__fastcall*)(void*,const RmtmRoleArgCursor267V1*);
   if(!RmtmRoleBeforeDeadline267V1(wall,mono))break;
   const auto rooted=reinterpret_cast<SetRoot>(XAR_RMTM_ROLE_CALL_ADDRESS(image,0x3D5D7F0))(reinterpret_cast<void*>(builder),&reference_args);
   if(!RmtmRoleBeforeDeadline267V1(wall,mono)||rooted!=reinterpret_cast<void*>(builder)||!RmtmRoleReferenceMatches267V1(reinterpret_cast<void*>(builder),actor))break;
   using End=bool(__fastcall*)(void*,RmtmRoleAny267V1*);
   if(!RmtmRoleBeforeDeadline267V1(wall,mono))break;
   const bool ended=reinterpret_cast<End>(XAR_RMTM_ROLE_CALL_ADDRESS(image,0x3D5D8C0))(reinterpret_cast<void*>(builder),&top_any);
   // Constructor completion is tracked even if its deadline expires on return.
   if(ended&&top_any.type==top_type)scope_complete=true;
   if(!RmtmRoleBeforeDeadline267V1(wall,mono)||!scope_complete)break;
   const auto top=*reinterpret_cast<const std::uintptr_t*>(top_any.storage.data());
   if(!RmtmRoleReferenceMatches267V1(reinterpret_cast<void*>(top),actor)||!RmtmRoleReferenceMatches267V1(reference_any.storage.data(),actor))break;
   using Assign=void*(__fastcall*)(void*,const char*,std::size_t);
   if(!RmtmRoleBeforeDeadline267V1(wall,mono))break;
   string_entered=true;reinterpret_cast<Assign>(XAR_RMTM_ROLE_CALL_ADDRESS(image,0x896BB0))(text.data(),key,std::strlen(key));string_complete=true;
   if(!RmtmRoleBeforeDeadline267V1(wall,mono))break;
   using Lookup=void*(__fastcall*)(const void*);
   if(!RmtmRoleBeforeDeadline267V1(wall,mono))break;
   out.definition=reinterpret_cast<std::uintptr_t>(reinterpret_cast<Lookup>(XAR_RMTM_ROLE_CALL_ADDRESS(image,0x3D42F00))(text.data()));
   if(!RmtmRoleBeforeDeadline267V1(wall,mono))break;
   // Missing exact definition is successful read-only DATA, never permission.
   if(!out.definition){okay=true;break;}
   RmtmRoleArgTable267V1 table{&top_any,1,1,0};RmtmRoleArgCursor267V1 args{&table,0,0};
   using IsShown=bool(__fastcall*)(void*,RmtmRoleAny267V1*,const RmtmRoleArgCursor267V1*);
   if(!RmtmRoleBeforeDeadline267V1(wall,mono))break;
   const bool queried=reinterpret_cast<IsShown>(XAR_RMTM_ROLE_CALL_ADDRESS(image,0x3DD1970))(reinterpret_cast<void*>(out.definition),&bool_any,&args);
   if(!RmtmRoleBeforeDeadline267V1(wall,mono)||!queried||bool_any.type!=bool_type||std::to_integer<unsigned>(bool_any.storage.front())>1)break;
   if(!RmtmRoleReferenceMatches267V1(reinterpret_cast<void*>(top),actor)||!RmtmRoleReferenceMatches267V1(reference_any.storage.data(),actor))break;
   out.shown=bool_any.storage.front()!=std::byte{};okay=true;
  }while(false);
 }__except(EXCEPTION_EXECUTE_HANDLER){out.cleanup_known=false;}
 // Required best-effort destruction is not skipped after deadline. No new
 // predicate/effect call is made during cleanup; no partial TopScope invented.
 if(string_complete){__try{reinterpret_cast<void(__fastcall*)(void*)>(XAR_RMTM_ROLE_CALL_ADDRESS(image,0x897460))(text.data());}__except(EXCEPTION_EXECUTE_HANDLER){out.cleanup_known=false;}}
 else if(string_entered)out.cleanup_known=false;
 if(initialized){
  if(!DestroyRmtmRoleAny267V1(bool_any,empty_type,reference_type,top_type,bool_type))out.cleanup_known=false;
  if(scope_complete||top_any.type==empty_type){if(!DestroyRmtmRoleAny267V1(top_any,empty_type,reference_type,top_type,bool_type))out.cleanup_known=false;}
  else out.cleanup_known=false;
  if(!DestroyRmtmRoleAny267V1(reference_any,empty_type,reference_type,top_type,bool_type))out.cleanup_known=false;
 }
 return okay&&out.cleanup_known&&RmtmRoleBeforeDeadline267V1(wall,mono);
}
[[maybe_unused]]bool NativeRmtmRole267V1(std::uintptr_t image,void*actor,std::uint32_t id,bool successor,std::uint64_t wall,std::uint64_t mono,RmtmRoleNative267V1&out)noexcept{return NativeRmtmFixedPredicate267V1(image,actor,id,successor?1:0,wall,mono,out);}
}
