// Reviewed current859 player-rooted catalogue leaves. No public caller addresses,
// guessed tags, shared-static MakeScope or arbitrary ScriptedGui names.
namespace {
struct ChoiceAny267V1{std::uintptr_t type=0;std::array<std::byte,32>storage{};};
static_assert(sizeof(ChoiceAny267V1)==40);
struct ChoiceArgTable267V1{ChoiceAny267V1*data=nullptr;std::uint32_t capacity=1,count=1;std::uintptr_t allocator=0;};
struct ChoiceArgs267V1{ChoiceArgTable267V1*table=nullptr;std::uint32_t index=0,reserved=0;};
struct ChoiceIdentity267V1{
 std::array<std::byte,16>reference{};std::uintptr_t definition=0;std::array<std::byte,64>definition_header{};
 std::array<char,129>key{};std::uint16_t key_size=0;
 friend bool operator==(const ChoiceIdentity267V1&,const ChoiceIdentity267V1&)=default;
};
[[maybe_unused]]bool ChoiceReferenceSame267V1(const void*a,const void*b)noexcept{
 if(!a||!b)return false;__try{std::uint32_t at=0,bt=0;std::uint64_t av=0,bv=0;std::memcpy(&at,a,4);std::memcpy(&bt,b,4);std::memcpy(&av,static_cast<const std::byte*>(a)+8,8);std::memcpy(&bv,static_cast<const std::byte*>(b)+8,8);return at==bt&&av==bv;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool DestroyChoiceAny267V1(ChoiceAny267V1&any,std::uintptr_t empty,std::span<const std::uintptr_t>allowed)noexcept{
 __try{if(any.type!=empty&&std::find(allowed.begin(),allowed.end(),any.type)==allowed.end())return false;const auto vt=*reinterpret_cast<const std::uintptr_t*>(any.type);const auto destroy=*reinterpret_cast<const std::uintptr_t*>(vt+0x18);reinterpret_cast<void(__fastcall*)(void*,void*)>(destroy)(reinterpret_cast<void*>(any.type),any.storage.data());any={};any.type=empty;return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool ChoiceKey267V1(const ChoiceAny267V1&text,std::array<char,129>&key,std::uint16_t&size)noexcept{
 size=0;__try{std::uint64_t n=0,cap=0;std::memcpy(&n,text.storage.data()+16,8);std::memcpy(&cap,text.storage.data()+24,8);if(!n||n>128||(cap!=15&&(cap<16||cap>4096||n>cap)))return false;const char*data=reinterpret_cast<const char*>(text.storage.data());if(cap>15)std::memcpy(&data,text.storage.data(),8);if(!data||data[n])return false;for(std::size_t i=0;i<n;++i){const auto c=data[i];if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='.'||c=='-'))return false;key[i]=c;}key[n]=0;size=static_cast<std::uint16_t>(n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
// Resolve the exact type, reject its default sentinel and check official inverse
// MakeScope identity before accepting a copied canonical key. Inputs are actual
// current model rows, never caller-created tags or IDs.
[[maybe_unused]]bool ReadChoiceIdentity267V1(std::uintptr_t image,CourtierCatalog267V1 catalog,const std::array<std::byte,16>&reference,ChoiceIdentity267V1&out,bool&cleanup_known)noexcept{
 out={};cleanup_known=true;if(static_cast<unsigned>(catalog)>6)return false;
 const bool faith=catalog==CourtierCatalog267V1::faith;const bool culture=catalog==CourtierCatalog267V1::culture;std::uint32_t tag=0,id=0;std::memcpy(&tag,reference.data(),4);std::memcpy(&id,reference.data()+8,4);if(tag!=(culture?0x1FU:faith?0x12U:0x36U)||id==0xFFFFFFFFU||(!faith&&!culture&&static_cast<std::int32_t>(id)<0))return false;
 ChoiceAny267V1 object{},text{},inverse{};std::uintptr_t empty=0,object_type=0,string_type=0,reference_type=0;bool initialized=false,object_entered=false,object_complete=false,text_entered=false,text_complete=false,inverse_entered=false,inverse_complete=false,okay=false;
 __try{
  using Factory=std::uintptr_t(__fastcall*)();empty=reinterpret_cast<Factory>(image+0x8B2EF0)();object_type=reinterpret_cast<Factory>(image+(culture?0xC9EE60:faith?0xC2E250:0xC2E130))();string_type=reinterpret_cast<Factory>(image+0x8C21D0)();reference_type=reinterpret_cast<Factory>(image+0x8B5030)();object.type=text.type=inverse.type=empty;initialized=true;
  do{
   std::uintptr_t db=0,data=0,wanted=0,fallback=0;std::int32_t count=0;
   std::memcpy(&db,reinterpret_cast<const void*>(image+(culture?0x6A67620:faith?0x6A672B8:0x68AFAE8)),8);std::memcpy(&fallback,reinterpret_cast<const void*>(image+(culture?0x6A67600:faith?0x6A67270:0x6A67A70)),8);if(!db||!fallback)break;
   std::memcpy(&data,reinterpret_cast<const void*>(db+((faith||culture)?0x20:0x50)),8);std::memcpy(&count,reinterpret_cast<const void*>(db+((faith||culture)?0x2C:0x5C)),4);const auto index=(faith||culture)?(id&0xFFFFFFU):id;if(count<0||index>=static_cast<std::uint32_t>(count)||!data)break;
   std::memcpy(&wanted,reinterpret_cast<const void*>(data+static_cast<std::size_t>(index)*((faith||culture)?16:8)+((faith||culture)?8:0)),8);if(!wanted||wanted==fallback)break;std::uint32_t actual_id=0;std::memcpy(&actual_id,reinterpret_cast<const void*>(wanted+(faith?8:0x10)),4);if(actual_id!=id)break;
   object_entered=true;
   if(!reinterpret_cast<bool(__fastcall*)(const void*,ChoiceAny267V1*)>(image+(culture?0x2BA5330:faith?0x2BA6230:0x2BA37D0))(reference.data(),&object)||object.type!=object_type)break;object_complete=true;
   std::uintptr_t resolved=0;std::memcpy(&resolved,object.storage.data(),8);if(resolved!=wanted||resolved==fallback)break;
   inverse_entered=true;if(!reinterpret_cast<bool(__fastcall*)(const void*,ChoiceAny267V1*)>(image+(culture?0x2BA5410:faith?0x2BA6310:0x2BA38A0))(reinterpret_cast<void*>(resolved),&inverse)||inverse.type!=reference_type)break;inverse_complete=true;if(!ChoiceReferenceSame267V1(reference.data(),inverse.storage.data()))break;
   if(culture){const auto size=std::snprintf(out.key.data(),out.key.size(),"culture-%u",id);if(size<=0||static_cast<std::size_t>(size)>=out.key.size())break;out.key_size=static_cast<std::uint16_t>(size);}else{text_entered=true;if(!reinterpret_cast<bool(__fastcall*)(const void*,ChoiceAny267V1*)>(image+(faith?0x2953D50:0x25A8F20))(reinterpret_cast<void*>(resolved),&text)||text.type!=string_type)break;text_complete=true;if(!ChoiceKey267V1(text,out.key,out.key_size))break;}
   std::uintptr_t current_db=0,current_data=0,current_object=0;std::int32_t current_count=0;std::memcpy(&current_db,reinterpret_cast<const void*>(image+(culture?0x6A67620:faith?0x6A672B8:0x68AFAE8)),8);if(current_db!=db)break;std::memcpy(&current_data,reinterpret_cast<const void*>(db+((faith||culture)?0x20:0x50)),8);std::memcpy(&current_count,reinterpret_cast<const void*>(db+((faith||culture)?0x2C:0x5C)),4);if(current_data!=data||current_count!=count)break;std::memcpy(&current_object,reinterpret_cast<const void*>(data+static_cast<std::size_t>(index)*((faith||culture)?16:8)+((faith||culture)?8:0)),8);if(current_object!=resolved)break;
   out.reference=reference;out.definition=resolved;std::memcpy(out.definition_header.data(),reinterpret_cast<const void*>(resolved),out.definition_header.size());okay=true;
  }while(false);
 }__except(EXCEPTION_EXECUTE_HANDLER){cleanup_known=false;}
 if(initialized){const std::array<std::uintptr_t,3>allowed{object_type,string_type,reference_type};
  if((!object_entered||object_complete||object.type==empty)){if(!DestroyChoiceAny267V1(object,empty,allowed))cleanup_known=false;}else cleanup_known=false;
  if((!text_entered||text_complete||text.type==empty)){if(!DestroyChoiceAny267V1(text,empty,allowed))cleanup_known=false;}else cleanup_known=false;
  if((!inverse_entered||inverse_complete||inverse.type==empty)){if(!DestroyChoiceAny267V1(inverse,empty,allowed))cleanup_known=false;}else cleanup_known=false;
 }
 return okay&&cleanup_known;
}

enum class ChoiceScopePhase267V1{predicates,execute};
struct ChoiceScope267V1{std::uintptr_t action_definition=0,selected_definition=0;std::array<std::byte,64>action_header{},selected_header{};bool shown=false,valid=false,selected=false,entered=false,effect_entered=false,native_returned=false,cleanup_known=true;};
[[maybe_unused]]bool NativeChoiceScope267V1(std::uintptr_t image,void*actual_actor,std::int32_t actor,CourtierProduct267V1 product,CourtierCatalog267V1 catalog,const ChoiceIdentity267V1&identity,std::uint64_t wall_deadline,std::uint64_t monotonic_deadline,std::uintptr_t expected_action,std::uintptr_t expected_selected,ChoiceScopePhase267V1 phase,ChoiceScope267V1&out)noexcept{
 out={};if(!actual_actor||static_cast<unsigned>(product)>1||static_cast<unsigned>(catalog)>6)return false;const bool faith=catalog==CourtierCatalog267V1::faith;const bool culture=catalog==CourtierCatalog267V1::culture;
 constexpr std::array<std::array<const char*,2>,2>trait_keys{{{{"xar_cc_toggle_trait_gui","xar_cc_trait_selected_gui"}},{{"ervc_cc_toggle_trait_gui","ervc_cc_trait_selected_gui"}}}};
 constexpr std::array<std::array<const char*,2>,2>faith_keys{{{{"xar_cc_select_faith_gui","xar_cc_faith_selected_gui"}},{{"ervc_cc_select_faith_gui","ervc_cc_faith_selected_gui"}}}};
 constexpr std::array<std::array<const char*,2>,2>culture_keys{{{{"xar_cc_select_culture_gui","xar_cc_culture_selected_gui"}},{{"ervc_cc_select_culture_gui","ervc_cc_culture_selected_gui"}}}};
 const auto&keys=culture?culture_keys[static_cast<unsigned>(product)]:faith?faith_keys[static_cast<unsigned>(product)]:trait_keys[static_cast<unsigned>(product)];const char*scope_name=product==CourtierProduct267V1::vivhite?(culture?"ervc_culture":faith?"ervc_faith":"ervc_trait"):(culture?"culture":faith?"faith":"trait");
 ChoiceAny267V1 root{},top{},boolean{},definition_name{};std::array<ChoiceAny267V1,2>named{};
 std::uintptr_t empty=0,reference_type=0,top_type=0,bool_type=0,string_type=0;bool initialized=false,root_entered=false,root_complete=false,top_entered=false,top_complete=false,selected_entered=false,selected_complete=false,named_entered=false,named_complete=false,definition_entered=false,definition_complete=false,okay=false;out.entered=true;
 __try{
  using Factory=std::uintptr_t(__fastcall*)();empty=reinterpret_cast<Factory>(image+0x8B2EF0)();reference_type=reinterpret_cast<Factory>(image+0x8B5030)();top_type=reinterpret_cast<Factory>(image+0x16AFB60)();bool_type=reinterpret_cast<Factory>(image+0x8C2930)();string_type=reinterpret_cast<Factory>(image+0x8C21D0)();root.type=top.type=boolean.type=definition_name.type=named[0].type=named[1].type=empty;initialized=true;
  do{
   ChoiceIdentity267V1 fresh;bool identity_cleanup=true;if(!ReadChoiceIdentity267V1(image,catalog,identity.reference,fresh,identity_cleanup)||!identity_cleanup){out.cleanup_known=identity_cleanup;break;}if(fresh!=identity)break;
   root_entered=true;if(!reinterpret_cast<bool(__fastcall*)(void*,ChoiceAny267V1*)>(image+0x2BA7A20)(actual_actor,&root)||root.type!=reference_type)break;root_complete=true;std::uint32_t root_tag=0,root_id=0;std::memcpy(&root_tag,root.storage.data(),4);std::memcpy(&root_id,root.storage.data()+8,4);if(root_tag!=4||root_id!=static_cast<std::uint32_t>(actor))break;
   selected_entered=true;if(!reinterpret_cast<bool(__fastcall*)(const void*,ChoiceAny267V1*)>(image+(culture?0x2BA5410:faith?0x2BA6310:0x2BA38A0))(reinterpret_cast<void*>(fresh.definition),&named[1])||named[1].type!=reference_type)break;selected_complete=true;if(!ChoiceReferenceSame267V1(named[1].storage.data(),fresh.reference.data()))break;
   const auto builder=reinterpret_cast<Factory>(image+0x3D42F70)();if(builder!=image+0x6B03530)break;ChoiceArgTable267V1 roots{&root,1,1,0};ChoiceArgs267V1 root_args{&roots,0,0};
   if(reinterpret_cast<void*(__fastcall*)(void*,const ChoiceArgs267V1*)>(image+0x3D5D7F0)(reinterpret_cast<void*>(builder),&root_args)!=reinterpret_cast<void*>(builder)||!ChoiceReferenceSame267V1(reinterpret_cast<void*>(builder),root.storage.data()))break;
   named[0].type=string_type;std::uint64_t cap=15;std::memcpy(named[0].storage.data()+24,&cap,8);named_entered=true;reinterpret_cast<void*(__fastcall*)(void*,const char*,std::size_t)>(image+0x896BB0)(named[0].storage.data(),scope_name,std::strlen(scope_name));named_complete=true;
   ChoiceArgTable267V1 values{named.data(),2,2,0};ChoiceArgs267V1 values_args{&values,0,0};if(reinterpret_cast<void*(__fastcall*)(void*,const ChoiceArgs267V1*)>(image+0x3D5D880)(reinterpret_cast<void*>(builder),&values_args)!=reinterpret_cast<void*>(builder))break;
   top_entered=true;if(!reinterpret_cast<bool(__fastcall*)(void*,ChoiceAny267V1*)>(image+0x3D5D8C0)(reinterpret_cast<void*>(builder),&top)||top.type!=top_type)break;top_complete=true;std::uintptr_t scope=0;std::memcpy(&scope,top.storage.data(),8);if(!ChoiceReferenceSame267V1(reinterpret_cast<void*>(scope),root.storage.data()))break;
   // The exact typed End output is owned; no local fake TopScope or arbitrary
   // builder memory survives the current owner call.
   ChoiceArgTable267V1 arguments{&top,1,1,0};ChoiceArgs267V1 args{&arguments,0,0};using Predicate=bool(__fastcall*)(void*,ChoiceAny267V1*,const ChoiceArgs267V1*);
   for(std::size_t n=0;n<2;++n){
    definition_name.type=string_type;std::memcpy(definition_name.storage.data()+24,&cap,8);definition_entered=true;definition_complete=false;reinterpret_cast<void*(__fastcall*)(void*,const char*,std::size_t)>(image+0x896BB0)(definition_name.storage.data(),keys[n],std::strlen(keys[n]));definition_complete=true;
    const auto definition=reinterpret_cast<std::uintptr_t(__fastcall*)(const void*)>(image+0x3D42F00)(definition_name.storage.data());if(!definition)break;
    if(n==0){out.action_definition=definition;if(expected_action&&expected_action!=definition)break;std::memcpy(out.action_header.data(),reinterpret_cast<const void*>(definition),64);if(!reinterpret_cast<Predicate>(image+0x3DD1970)(reinterpret_cast<void*>(definition),&boolean,&args)||boolean.type!=bool_type||std::to_integer<unsigned>(boolean.storage[0])>1)break;out.shown=boolean.storage[0]!=std::byte{};if(!reinterpret_cast<Predicate>(image+0x3DD19D0)(reinterpret_cast<void*>(definition),&boolean,&args)||boolean.type!=bool_type||std::to_integer<unsigned>(boolean.storage[0])>1)break;out.valid=boolean.storage[0]!=std::byte{};
    }else{out.selected_definition=definition;if(expected_selected&&expected_selected!=definition)break;std::memcpy(out.selected_header.data(),reinterpret_cast<const void*>(definition),64);if(!reinterpret_cast<Predicate>(image+0x3DD1970)(reinterpret_cast<void*>(definition),&boolean,&args)||boolean.type!=bool_type||std::to_integer<unsigned>(boolean.storage[0])>1)break;out.selected=boolean.storage[0]!=std::byte{};}
    if(!DestroyChoiceAny267V1(definition_name,empty,std::span<const std::uintptr_t>(&string_type,1))){out.cleanup_known=false;break;}definition_entered=definition_complete=false;
    if(n==1)okay=true;
   }
   if(!okay||!ChoiceReferenceSame267V1(reinterpret_cast<void*>(scope),root.storage.data())){okay=false;break;}
   if(phase==ChoiceScopePhase267V1::execute){
    okay=false;if(!out.shown||!out.valid)break;const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();if(wall<=0||!wall_deadline||!monotonic_deadline||static_cast<std::uint64_t>(wall)>=wall_deadline||GetTickCount64()>=monotonic_deadline)break;
    out.effect_entered=true;if(!reinterpret_cast<Predicate>(image+0x3DD18A0)(reinterpret_cast<void*>(out.action_definition),&boolean,&args)){out.cleanup_known=false;break;}out.native_returned=true;okay=true;
   }
  }while(false);
 }__except(EXCEPTION_EXECUTE_HANDLER){out.cleanup_known=false;}
 if(initialized){const std::array<std::uintptr_t,5>allowed{reference_type,top_type,bool_type,string_type,empty};
  const auto clean=[&](ChoiceAny267V1&value,bool entered,bool complete){if(!entered||complete||value.type==empty){if(!DestroyChoiceAny267V1(value,empty,allowed))out.cleanup_known=false;}else out.cleanup_known=false;};
  clean(boolean,false,true);clean(definition_name,definition_entered,definition_complete);clean(named[0],named_entered,named_complete);clean(named[1],selected_entered,selected_complete);clean(top,top_entered,top_complete);clean(root,root_entered,root_complete);
 }
 return okay&&out.cleanup_known;
}
}
