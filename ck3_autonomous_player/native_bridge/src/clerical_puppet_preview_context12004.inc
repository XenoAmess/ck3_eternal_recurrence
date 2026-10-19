// Included only by the existing ordinary context provider. This is an exact .4
// UI consumer; ordinary_context_supported and all Send/option-intent paths stay unchanged.
namespace xar::ck3_12004::clerical_preview {
namespace {
using namespace ck3_12003;
using namespace ck3_12003::ordinary_interaction;
bool Sample(const Bindings&b,const OrdinaryInteractionRequestV1&r,const void*storage,Context&out) {
  out={};
  if(!b.enabled||!b.module_base||!b.education_rows_actual_12004||!AllowedKey(r.interaction_key)||
      r.child_full_id||r.guardian_full_id||r.requested_option_keys||!storage||
      !b.get_script_identifier_table||!b.lookup_script_identifier_id)return false;
  const auto actor_id=static_cast<std::uint32_t>(r.expected_player_character_id);
  void*actor=Resolve(b.interaction.core,actor_id),*recipient=Resolve(b.interaction.core,r.recipient_id);
  bool actor_alive=false,recipient_alive=false;
  if(!actor||!recipient||!Alive(actor,actor_alive)||!actor_alive||!Alive(recipient,recipient_alive)||!recipient_alive)return false;
  void*database=nullptr,*loaded=nullptr,*definition=nullptr,*options=nullptr,*bank=nullptr,*special=nullptr;
  std::int32_t hash=0,count=-1,bank_count=-1;std::uint8_t kind=255;
  if(!Call(b.get_database,database)||!database||
      !Call(b.stable_hash,hash,database,r.interaction_key.data(),static_cast<std::uint32_t>(r.interaction_key.size()))||
      !Call(b.lookup_definition,loaded,database,hash)||!loaded||
      !Read(storage,0,definition)||definition!=loaded||!DefinitionMatches(definition,hash,r.interaction_key)||
      !Read(definition,0x26F9,kind)||kind!=0||
      !Read(definition,0x2258,options)||!options||!Read(definition,0x2264,count)||count!=6||
      !Read(storage,0x300,bank)||!bank||!Read(storage,0x30C,bank_count)||bank_count<6||bank_count>4096||
      !Read(storage,0x330,special)||special)return false;
  Context c{};c.key=r.interaction_key;c.definition_hash=std::bit_cast<std::uint32_t>(hash);c.kind=kind;
  for(std::size_t i=0;i<6;++i){
    if(!Read(storage,0x2D8+4*i,c.roles[i]))return false;
  }
  c.actor=c.roles[0];c.recipient=c.roles[1];c.effective_actor=c.roles[5];c.declared_count=6;
  struct IdentifierView{const char*data;std::int32_t length;std::uint8_t owned,padding[3];};
  static_assert(sizeof(IdentifierView)==16);
  void*table=nullptr;if(!Call(b.get_script_identifier_table,table)||!table)return false;
  for(std::size_t i=0;i<6;++i){
    std::int32_t expected=-1;std::int32_t*returned=nullptr;
    const IdentifierView key{kOptionKeys[i].data(),static_cast<std::int32_t>(kOptionKeys[i].size()),0,{0,0,0}};
    bool selected=false;
    if(!Call(b.lookup_script_identifier_id,returned,table,&expected,static_cast<const void*>(&key))||returned!=&expected||expected==-1||
        !Read(options,i*0x730+0x368,c.option_flags[i])||c.option_flags[i]!=std::bit_cast<std::uint32_t>(expected)||
        !Read(bank,i,c.option_bank[i])||c.option_bank[i]!=0||
        !Call(b.read_option,selected,const_cast<void*>(storage),c.option_flags[i])||selected)return false;
  }
  bool shown=false;
  if(!Call(b.is_shown,shown,const_cast<void*>(storage))||!shown||
      !Call(b.interaction.evaluate_trigger,c.needs_confirmation,
        static_cast<void*>(static_cast<std::byte*>(definition)+0x13D8),
        static_cast<const void*>(static_cast<const std::byte*>(storage)+8))||!c.needs_confirmation)return false;
  c.available=true;
  if(!DefaultOnly(c,r.interaction_key,actor_id,r.recipient_id))return false;
  // Bookend pointers/counts and role/option bytes, including the original bank.
  void*definition2=nullptr,*options2=nullptr,*bank2=nullptr,*special2=nullptr;
  std::int32_t count2=-1,bank_count2=-1;std::uint8_t kind2=255;
  if(!Read(storage,0,definition2)||definition2!=definition||!Read(definition,0x2258,options2)||options2!=options||
      !Read(definition,0x2264,count2)||count2!=6||!Read(definition,0x26F9,kind2)||kind2!=0||
      !Read(storage,0x300,bank2)||bank2!=bank||!Read(storage,0x30C,bank_count2)||bank_count2!=bank_count||
      !Read(storage,0x330,special2)||special2)return false;
  for(std::size_t i=0;i<6;++i){std::uint32_t role=0,flag=0;std::uint8_t value=255;
    if(!Read(storage,0x2D8+4*i,role)||role!=c.roles[i]||!Read(options,i*0x730+0x368,flag)||flag!=c.option_flags[i]||
        !Read(bank,i,value)||value!=0)return false;
  }
  if(!Alive(actor,actor_alive)||!actor_alive||!Alive(recipient,recipient_alive)||!recipient_alive)return false;
  out=std::move(c);return true;
}
bool DoubleSample(const Bindings&b,const OrdinaryInteractionRequestV1&r,const void*storage,Context&out) {
  Context first{},last{};
  if(!Sample(b,r,storage,first)||!Sample(b,r,storage,last)||first!=last){out={};return false;}
  out=std::move(first);return true;
}
}
bool ReadDefault(const ck3_12003::ordinary_interaction::Bindings&b,
    const ck3_12003::OrdinaryInteractionRequestV1&r,Context&out) noexcept {
  out={};try{
    ck3_12003::ordinary_interaction::NativeContext context{};
    ck3_12003::ordinary_interaction::Observation unused{};
    if(!AllowedKey(r.interaction_key)||!ck3_12003::ordinary_interaction::Prepare(b,r,context,unused))return false;
    return DoubleSample(b,r,context.bytes.data(),out);
  }catch(...){out={};return false;}
}
bool ReadInstalled(const ck3_12003::ordinary_interaction::Bindings&b,
    const ck3_12003::OrdinaryInteractionRequestV1&r,const void*owned,Context&out) noexcept {
  out={};try{return DoubleSample(b,r,owned,out);}catch(...){out={};return false;}
}
void OpenDefault(const ck3_12003::ordinary_interaction::Bindings&b,
    const ck3_12003::OrdinaryInteractionRequestV1&r,const Context&expected,
    const WindowBindings&w,Attempt&out) noexcept {
  out={};try{
    if(!AllowedKey(r.interaction_key)||!w.confirmation||!w.handler||!w.copy_context||!w.open_window||!w.refresh_window){out.reason="clerical_preview_ui_leaves_unavailable";return;}
    ck3_12003::ordinary_interaction::NativeContext context{};
    ck3_12003::ordinary_interaction::Observation unused{};
    if(!ck3_12003::ordinary_interaction::Prepare(b,r,context,unused)||!DoubleSample(b,r,context.bytes.data(),out.actual_default)||out.actual_default!=expected){out.reason="clerical_preview_default_context_changed";return;}
    bool same=false;
    if(!b.dispatch_frame_context||!ck3_12003::ordinary_interaction::Call(b.verify_dispatch_frame,same,b.dispatch_frame_context)||!same){out.reason="clerical_preview_dispatch_frame_changed";return;}
    out.invoked=true;
    // Only the stock true branch leaves. Never call AF2810, Send or option setters.
    out.completed=ck3_12003::ordinary_interaction::CallVoid(w.copy_context,w.confirmation,static_cast<const void*>(context.bytes.data()))&&
        ck3_12003::ordinary_interaction::CallVoid(w.open_window,w.handler,std::int32_t{11},std::int32_t{1})&&
        ck3_12003::ordinary_interaction::CallVoid(w.refresh_window,w.confirmation);
    out.reason=out.completed?nullptr:"clerical_preview_open_result_unknown_no_retry";
  }catch(...){out.reason="clerical_preview_exception_no_retry_if_invoked";}
}
}
