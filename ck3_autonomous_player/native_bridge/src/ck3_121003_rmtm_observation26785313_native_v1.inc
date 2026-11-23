// Private mechanical ABI reuse. Fixed keys are selected internally; these are
// not an arbitrary Var, view, widget or interaction execution interface.
struct Any40 {std::uintptr_t type=0;std::array<std::byte,32>storage{};};
struct ArgTable24 {Any40*data=nullptr;std::uint32_t capacity=0,count=0;std::uintptr_t allocator=0;};
struct ArgCursor16 {ArgTable24*table=nullptr;std::uint32_t index=0,reserved=0;};
static_assert(sizeof(Any40)==40&&sizeof(ArgTable24)==24&&sizeof(ArgCursor16)==16);
[[maybe_unused]]bool DestroyAny([[maybe_unused]]std::uintptr_t image,Any40&any,std::uintptr_t empty,std::uintptr_t reference,std::uintptr_t text,std::uintptr_t character)noexcept{
 __try{
  if(any.type!=empty&&any.type!=reference&&any.type!=text&&any.type!=character)return false;
  const auto vt=*reinterpret_cast<const std::uintptr_t*>(any.type);const auto fn=*reinterpret_cast<const std::uintptr_t*>(vt+0x18);
  if(fn<image||fn-image>=kImageSize)return false;
  OfferTraceMark267(OfferStage267V1::any_destroy_enter);
  reinterpret_cast<void(__fastcall*)(void*,void*)>(fn)(reinterpret_cast<void*>(any.type),any.storage.data());OfferTraceMark267(OfferStage267V1::any_destroy_returned,true);any={};any.type=empty;return true;
 }__except(OfferTraceException267(GetExceptionInformation())){return false;}
}
[[maybe_unused]]bool DestroyText([[maybe_unused]]std::uintptr_t image,void*text)noexcept{
 __try{OfferTraceMark267(OfferStage267V1::text_destroy_enter);reinterpret_cast<void(__fastcall*)(void*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x897460))(text);OfferTraceMark267(OfferStage267V1::text_destroy_returned,true);return true;}__except(OfferTraceException267(GetExceptionInformation())){return false;}
}
[[maybe_unused]]bool OfferTarget([[maybe_unused]]std::uintptr_t image,std::uintptr_t actor,std::uint32_t fullActor,RmtmOfferTarget267V1 target,std::uint32_t&fullTarget,std::uintptr_t&actual,std::array<std::byte,16>&reference,bool&clean)noexcept{
 clean=true;fullTarget=invalid;actual=0;reference={};if(static_cast<unsigned>(target)>1)return false;
 constexpr std::array<const char*,2>keys{"rqa_vassalization_target_a","rqa_vassalization_target_b"};
 Any40 root{},text{},characterValue{};std::uintptr_t empty=0,refType=0,textType=0,charType=0;bool initialized=false,textEntered=false,textComplete=false,rootEntered=false,rootComplete=false,charEntered=false,charComplete=false,good=false;
 __try{
  using Factory=std::uintptr_t(__fastcall*)();
  empty=reinterpret_cast<Factory>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x8B2EF0))();refType=reinterpret_cast<Factory>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x8B5030))();textType=reinterpret_cast<Factory>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x8C21D0))();charType=reinterpret_cast<Factory>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0xA3F530))();
  root.type=text.type=characterValue.type=empty;initialized=true;
  do{
   rootEntered=true;const bool made=reinterpret_cast<bool(__fastcall*)(void*,Any40*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x2BA7A20))(reinterpret_cast<void*>(actor),&root);rootComplete=true;
   std::uint16_t rootKind=0;std::uint64_t rootID=0;std::memcpy(&rootKind,root.storage.data(),2);std::memcpy(&rootID,root.storage.data()+8,8);
   if(!made||root.type!=refType||rootKind!=4||rootID!=fullActor)break;
   // Official owner availability is checked separately: Var's default can also
   // mean a bad receiver. It must never be converted into an absent target.
   if(!reinterpret_cast<void*(__fastcall*)(const void*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x262F5E0))(root.storage.data()))break;
   text.type=textType;const std::uint64_t cap=15;std::memcpy(text.storage.data()+24,&cap,8);textEntered=true;
   const auto name=keys[static_cast<unsigned>(target)];reinterpret_cast<void*(__fastcall*)(void*,const char*,std::size_t)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x896BB0))(text.storage.data(),name,std::strlen(name));textComplete=true;
   ArgTable24 table{&text,1,1,0};ArgCursor16 cursor{&table,0,0};
   const auto borrowed=reinterpret_cast<const void*(__fastcall*)(const void*,const ArgCursor16*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x3D26A70))(root.storage.data(),&cursor);
   if(!borrowed||reinterpret_cast<std::uintptr_t>(borrowed)==image+0x4AE2008)break;
   std::array<std::byte,16>after{};std::memcpy(reference.data(),borrowed,16);std::uint16_t kind=0;std::memcpy(&kind,reference.data(),2);std::memcpy(&fullTarget,reference.data()+8,4);
   if(kind!=4||fullTarget==invalid)break;
   charEntered=true;const bool handled=reinterpret_cast<bool(__fastcall*)(const void*,Any40*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x2BA7750))(borrowed,&characterValue);charComplete=true;
   std::memcpy(after.data(),borrowed,16);if(!handled||characterValue.type!=charType||reference!=after)break;
   std::memcpy(&actual,characterValue.storage.data(),8);std::uint32_t id=invalid,magic=0;std::uintptr_t fallback=0;
   std::memcpy(&fallback,reinterpret_cast<const void*>(image+0x68A8930),8);
   if(!actual||actual==fallback)break;std::memcpy(&id,reinterpret_cast<const void*>(actual+0x18),4);std::memcpy(&magic,reinterpret_cast<const void*>(actual+0x1C),4);
   good=id==fullTarget&&magic==0x43686172U;
  }while(false);
 }__except(OfferTraceException267(GetExceptionInformation())){clean=false;}
 if(textEntered){if(!textComplete||!DestroyText(image,text.storage.data()))clean=false;text.type=empty;}
 if(initialized){if(rootEntered&&!rootComplete)clean=false;else if(!DestroyAny(image,root,empty,refType,textType,charType))clean=false;if(charEntered&&!charComplete)clean=false;else if(!DestroyAny(image,characterValue,empty,refType,textType,charType))clean=false;}
 return good&&clean;
}
[[maybe_unused]]RmtmObservationCall267V1 OpenBudget(const ReadonlyBindings&b,const RmtmObservationFrame267V1&f,const RmtmObservationRequest267V1&q,std::uint64_t mono)noexcept{
 RmtmObservationCall267V1 out;const auto image=b.module_base;std::array<Any40,2>args{};alignas(void*)std::array<std::byte,32>key{};const std::uint64_t cap=15;std::memcpy(key.data()+24,&cap,8);
 volatile bool effectEntered=false,nativeReturned=false;
 std::uintptr_t empty=0,text=0,character=0;bool initialized=false,keyEntered=false,keyComplete=false,copyEntered=false,copyComplete=false,playerEntered=false,playerComplete=false;
 __try{
  using Factory=std::uintptr_t(__fastcall*)();empty=reinterpret_cast<Factory>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x8B2EF0))();text=reinterpret_cast<Factory>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x8C21D0))();character=reinterpret_cast<Factory>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0xA3F530))();args[0].type=args[1].type=empty;initialized=true;
  constexpr char name[]="treasury_budget_change";keyEntered=true;reinterpret_cast<void*(__fastcall*)(void*,const char*,std::size_t)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x896BB0))(key.data(),name,sizeof(name)-1);keyComplete=true;
  copyEntered=true;reinterpret_cast<void(__fastcall*)(Any40*,const void*,void*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x8B4960))(&args[0],key.data(),reinterpret_cast<void*>(text));copyComplete=true;
  playerEntered=true;const bool player=reinterpret_cast<bool(__fastcall*)(void*,Any40*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x2B48940))(nullptr,&args[1]);playerComplete=true;std::uintptr_t p=0;std::memcpy(&p,args[1].storage.data(),8);
  if(player&&args[0].type==text&&args[1].type==character&&p==reinterpret_cast<std::uintptr_t>(f.role.world.actor)&&Fresh(b,f,q,mono)){
   ArgTable24 table{args.data(),2,2,0};ArgCursor16 cursor{&table,0,0};effectEntered=true;out.cleanup_known=false;out.status=RmtmObservationCallStatus267V1::indeterminate;
   out.native_handled=reinterpret_cast<bool(__fastcall*)(void*,void*,const ArgCursor16*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0xBC1C40))(nullptr,nullptr,&cursor);nativeReturned=true;out.cleanup_known=true;out.status=RmtmObservationCallStatus267V1::returned;
  }
 }__except(OfferTraceException267(GetExceptionInformation())){out.cleanup_known=false;}
 // Persist actual progress across SEH in optimized builds. The compiler can
 // otherwise move an ordinary aggregate's returned=true store before the call.
 out.entered=effectEntered;out.native_returned=nativeReturned;
 if(!nativeReturned)out.native_handled=false;
 if(keyEntered&&(!keyComplete||!DestroyText(image,key.data())))out.cleanup_known=false;
 if(initialized){if(copyEntered&&!copyComplete)out.cleanup_known=false;else if(!DestroyAny(image,args[0],empty,0,text,character))out.cleanup_known=false;if(playerEntered&&!playerComplete)out.cleanup_known=false;else if(!DestroyAny(image,args[1],empty,0,text,character))out.cleanup_known=false;}
 if(!out.cleanup_known)out.status=RmtmObservationCallStatus267V1::indeterminate;return out;
}
[[maybe_unused]]bool NativeCString([[maybe_unused]]std::uintptr_t image,std::uintptr_t self,std::uintptr_t rva,void*out)noexcept{
 __try{return reinterpret_cast<void*(__fastcall*)(const void*,void*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,rva))(reinterpret_cast<const void*>(self),out)==out;}__except(OfferTraceException267(GetExceptionInformation())){return false;}
}
[[maybe_unused]]bool Description([[maybe_unused]]std::uintptr_t image,std::uintptr_t window,std::string&text,std::vector<std::byte>&proof,bool&clean){
 alignas(void*)std::array<std::byte,32>owned{};const std::uint64_t cap=15;std::memcpy(owned.data()+24,&cap,8);const bool returned=NativeCString(image,window,0x11C0410,owned.data());bool valid=false;
 try{std::vector<std::byte>temporary;if(returned)valid=String(reinterpret_cast<std::uintptr_t>(owned.data()),16384,text,temporary);}catch(...){valid=false;}
 // A temporary's stack address is not a persistent source fingerprint. Retain
 // its exact header/value bytes only, and always destroy the owned output.
 const bool destroyed=DestroyText(image,owned.data());clean=returned&&destroyed;
 if(valid&&clean){const auto n=static_cast<std::uint32_t>(text.size());const auto old=proof.size();proof.resize(old+sizeof(n)+text.size());std::memcpy(proof.data()+old,&n,sizeof(n));if(!text.empty())std::memcpy(proof.data()+old+sizeof(n),text.data(),text.size());}
 return valid&&clean;
}
[[maybe_unused]]bool RightClick([[maybe_unused]]std::uintptr_t image,std::uint32_t target,std::uintptr_t widget)noexcept{
 __try{OfferTraceMark267(OfferStage267V1::right_click_enter);reinterpret_cast<void(__fastcall*)(std::uint32_t,void*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0xBC3A70))(target,reinterpret_cast<void*>(widget));OfferTraceMark267(OfferStage267V1::right_click_returned,true);return true;}__except(OfferTraceException267(GetExceptionInformation())){return false;}
}
[[maybe_unused]]bool Close([[maybe_unused]]std::uintptr_t image,std::uintptr_t rva,std::uintptr_t window)noexcept{
 __try{reinterpret_cast<void(__fastcall*)(void*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,rva))(reinterpret_cast<void*>(window));return true;}__except(OfferTraceException267(GetExceptionInformation())){return false;}
}
[[maybe_unused]]bool PopulateOffer([[maybe_unused]]std::uintptr_t image,std::uintptr_t manager,std::uintptr_t item,std::uintptr_t definition,std::uintptr_t expectedWindow,bool&clean,bool&entered)noexcept{
 // The original item callback owns a record on a 0x370-byte stack frame at+20.
 // Reserve more than that complete extent, invoke its official constructor,
 // and invoke its official destructor. No hand-built scripting context.
 alignas(16)std::array<std::byte,0x400>record{};bool made=false,makeEntered=false,good=false;clean=true;entered=false;
 __try{
  makeEntered=true;OfferTraceMark267(OfferStage267V1::record_construct_enter);made=reinterpret_cast<void*(__fastcall*)(const void*,void*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x1446C50))(reinterpret_cast<const void*>(item),record.data())==record.data();
  OfferTraceMark267(OfferStage267V1::record_construct_returned,true);OfferTraceMark267(made?OfferStage267V1::record_construct_output_matched:OfferStage267V1::record_construct_output_rejected);
  if(made){std::uintptr_t actualDef=0;std::memcpy(&actualDef,record.data(),8);
   if(actualDef==definition)OfferTraceMark267(OfferStage267V1::trigger_eval_enter);
   const bool can=actualDef==definition&&reinterpret_cast<bool(__fastcall*)(const void*,const void*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x3D47320))(reinterpret_cast<const void*>(definition+0xB48),record.data()+8);if(actualDef==definition)OfferTraceMark267(can?OfferStage267V1::trigger_eval_returned_true:OfferStage267V1::trigger_eval_returned_false,true);else OfferTraceMark267(OfferStage267V1::record_definition_mismatch);
   if(can){
    OfferTraceMark267(OfferStage267V1::window_getter_enter);const auto window=reinterpret_cast<std::uintptr_t>(reinterpret_cast<void*(__fastcall*)(void*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0xB041B0))(reinterpret_cast<void*>(manager)));OfferTraceMark267(window==expectedWindow?OfferStage267V1::window_getter_returned_match:OfferStage267V1::window_getter_returned_mismatch,true);
    if(window==expectedWindow){
     // Deliberately use only the official true/display branch. AF0050 and
     // CSendCharacterInteractionCommand are never called by this family.
     entered=true;OfferTraceMark267(OfferStage267V1::populate_enter);reinterpret_cast<void(__fastcall*)(void*,const void*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x11BB3C0))(reinterpret_cast<void*>(window),record.data());OfferTraceMark267(OfferStage267V1::populate_returned,true);
     OfferTraceMark267(OfferStage267V1::activate_enter);reinterpret_cast<void(__fastcall*)(void*,std::uint32_t,bool)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0xAF1110))(reinterpret_cast<void*>(manager),0xB,true);OfferTraceMark267(OfferStage267V1::activate_returned,true);
     OfferTraceMark267(OfferStage267V1::refresh_enter);reinterpret_cast<void(__fastcall*)(void*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x11BBC30))(reinterpret_cast<void*>(window));OfferTraceMark267(OfferStage267V1::refresh_returned,true);good=true;
    }
   }
  }
 }__except(OfferTraceException267(GetExceptionInformation())){clean=false;}
 if(made){__try{OfferTraceMark267(OfferStage267V1::record_destroy_enter);reinterpret_cast<void(__fastcall*)(void*)>(XAR_RMTM_OBSERVATION_CALL_ADDRESS(image,0x3624460))(record.data());OfferTraceMark267(OfferStage267V1::record_destroy_returned,true);}__except(OfferTraceException267(GetExceptionInformation())){clean=false;}}
 else if(makeEntered)clean=false;
 return good&&clean;
}
