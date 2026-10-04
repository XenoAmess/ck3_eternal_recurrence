#include "xar_bridge/white_player_business_variables_v1.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include <windows.h>
#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {
constexpr std::int64_t kWhiteVariableFixedScaleV1 = 100000;
constexpr std::int32_t kWhiteVariableMaximumRowsV1 = 65536;
#include "white_business_exact_pins_v1.inc"

bool ReadBytes(const void *address,void *out,std::size_t size) noexcept {
  SIZE_T got=0;
  return address&&out&&size&&ReadProcessMemory(GetCurrentProcess(),address,out,size,&got)&&got==size;
}
template<class T> bool ReadAt(const void *object,std::size_t offset,T &out) noexcept {
  const auto address=reinterpret_cast<std::uintptr_t>(object);
  return object&&address<=std::numeric_limits<std::uintptr_t>::max()-offset&&
      ReadBytes(reinterpret_cast<const void *>(address+offset),&out,sizeof(out));
}
bool PinsMatch(std::uintptr_t base) noexcept {
  std::array<unsigned char,271> actual{};
  for(const auto &pin:kWhiteBusinessCodePinsV1)
    if(pin.size>actual.size()||!ReadBytes(reinterpret_cast<void *>(base+pin.rva),actual.data(),pin.size)||
        !std::equal(actual.begin(),actual.begin()+pin.size,pin.data))return false;
  return true;
}
bool GuardedIdentifier(const ck3_12002::PhaseDefinitionBindings &definitions,
    std::string_view key,std::int32_t &identifier) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    return ck3_12002::ResolvePhaseVariableIdentifier(definitions,key,identifier);
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool GuardedActor(const ck3_12002::CoreBindings &core,std::int32_t actor,void *&character) noexcept {
  character=nullptr;
#if defined(_MSC_VER)
  __try {
#endif
    character=ck3_12002::ResolveCoreCharacter(core,actor);return character!=nullptr;
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool GuardedContext(const ck3_12002::PhaseDefinitionBindings &definitions,
    std::int32_t actor,void *&context) noexcept {
  context=nullptr;const ck3_12002::PhaseVariableTarget target{4,{},actor};
#if defined(_MSC_VER)
  __try {
#endif
    context=definitions.variable_context(&target);return context!=nullptr;
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool DefinitionsMatch(std::uintptr_t base,const ck3_12002::PhaseDefinitionBindings &b) noexcept {
  return b.enabled&&reinterpret_cast<std::uintptr_t>(b.variable_context)==base+0x370EB10&&
      reinterpret_cast<std::uintptr_t>(b.variable_table)==base+0x3F8A800&&
      reinterpret_cast<std::uintptr_t>(b.lookup_variable_identifier)==base+0x3F8A680&&
      reinterpret_cast<std::uintptr_t>(b.variable_identifier_name)==base+0x3F8A6F0;
}
bool ReadFields(void *context,const std::array<std::int32_t,8> &ids,
    std::array<WhitePlayerBusinessScalarV1,8> &out) noexcept {
  out={};void *rows=nullptr;std::int32_t count=0;
  if(!ReadAt(context,0x10,rows)||!ReadAt(context,0x1C,count)||count<0||count>kWhiteVariableMaximumRowsV1||
      (count&&!rows))return false;
  for(std::int32_t index=0;index<count;++index) {
    std::array<unsigned char,0x20> raw{};
    const auto offset=static_cast<std::size_t>(index)*raw.size();
    const auto address=reinterpret_cast<std::uintptr_t>(rows);
    if(address>std::numeric_limits<std::uintptr_t>::max()-offset||
        !ReadBytes(reinterpret_cast<void *>(address+offset),raw.data(),raw.size()))return false;
    std::int32_t id=-1;std::memcpy(&id,raw.data()+8,sizeof(id));
    const auto found=std::find(ids.begin(),ids.end(),id);
    if(found==ids.end())continue;
    auto &value=out[static_cast<std::size_t>(found-ids.begin())];
    if(value.present)return false;
    value.present=true;
    std::memcpy(&value.actual_kind,raw.data()+0x10,sizeof(value.actual_kind));
    std::memcpy(&value.actual_payload,raw.data()+0x18,sizeof(value.actual_payload));
    // This is the existing EventTarget fixed-point encoding, not a GUI parse.
    // Absent/wrong-type/fractional values remain distinguishable from real 0.
    if(value.actual_kind==1) {
      value.fixed_raw=value.actual_payload;
      if(value.actual_payload%kWhiteVariableFixedScaleV1==0)
        value.integer_value=value.actual_payload/kWhiteVariableFixedScaleV1;
    }
  }
  void *later_rows=nullptr;std::int32_t later_count=0;
  return ReadAt(context,0x10,later_rows)&&ReadAt(context,0x1C,later_count)&&rows==later_rows&&count==later_count;
}
bool QualifiedFrame(const game::Snapshot &s,const MainThreadExecutionStampV1 &stamp) noexcept {
  return s.paused&&s.map_ready&&s.has_played_character&&s.played_character_alive&&s.played_character_id>0&&
      !s.has_active_event&&s.date_raw==stamp.date_raw;
}
}

bool ExecuteWhitePlayerBusinessVariablesV1(WhitePlayerBusinessVariablesContextV1 &query,
    MainThreadQueryMailboxV1 &mailbox,const MainThreadExecutionStampV1 &stamp) noexcept {
  auto &out=query.result;out={};out.game_pid=GetCurrentProcessId();
  out.native_revision=query.native_revision;out.connection_generation=query.connection_generation;
  try {
    const auto reject=[&](const char *why){out.unavailable_reason=why;return true;};
    if(!query.game||query.game->descriptor().game_version!=ck3_12003::kGameVersion||
        query.game->descriptor().executable_sha256!=ck3_12003::kExecutableSha256||
        !query.native_revision||!query.connection_generation)return reject("exact_12003_request_unavailable");
    if(!IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()))return reject("paused_application_owner_unverified");
    out.owner_thread_verified=true;out.application_thread_id=stamp.thread_id;
    out.application_pump_epoch=stamp.pump_epoch;out.application_tls_context=stamp.tls_context;
    game::Snapshot before{};
    if(!game::ReadSnapshot(*query.game,before)||before!=query.expected_snapshot||!QualifiedFrame(before,stamp))
      return reject("fresh_alive_paused_noevent_frame_unverified");
    out.played_character_id=before.played_character_id;out.date_raw=before.date_raw;
    const auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if(!base||!PinsMatch(base))return reject("exact_12003_variable_code_pins_changed");
    out.source_abi_pins_verified=true;
    // Reuse the reviewed exact .3 adapter gate. Never relax the .2 binder gate
    // and never pass old Zhongguo 1.19 variable-context pointers to this query.
    const auto bindings=game::BindCk3_12003AdapterImage(base,ck3_12003::kExecutableSha256);
    const auto &definitions=bindings.phase.definitions;
    void *character=nullptr,*later_character=nullptr;
    if(!DefinitionsMatch(base,definitions)||!GuardedActor(bindings.core,before.played_character_id,character))
      return reject("current_native_player_or_variable_binding_unavailable");
    std::array<std::int32_t,8> ids{};
    for(std::size_t i=0;i<ids.size();++i) {
      if(!GuardedIdentifier(definitions,kWhitePlayerBusinessVariableKeysV1[i],ids[i])||ids[i]<0)
        return reject("compiled_variable_identifier_roundtrip_failed");
      for(std::size_t j=0;j<i;++j)if(ids[i]==ids[j])return reject("compiled_variable_identifiers_ambiguous");
    }
    void *context=nullptr,*later_context=nullptr;
    std::array<WhitePlayerBusinessScalarV1,8> first{},second{};
    if(!GuardedContext(definitions,before.played_character_id,context)||!ReadFields(context,ids,first)||
        !GuardedContext(definitions,before.played_character_id,later_context)||context!=later_context||
        !ReadFields(later_context,ids,second)||first!=second)return reject("variable_scope_or_values_changed_or_unreadable");
    out.player_scope_verified=true;out.variable_context=reinterpret_cast<std::uintptr_t>(context);
    out.character_address=reinterpret_cast<std::uintptr_t>(character);
    game::Snapshot after{};
    if(!game::ReadSnapshot(*query.game,after)||after!=before||!QualifiedFrame(after,stamp)||
        !IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId())||
        !GuardedActor(bindings.core,after.played_character_id,later_character)||later_character!=character)
      return reject("postread_episode_or_owner_changed");
    out.fields=first;out.stable_two_pass_values=true;out.frame_verified=true;
    out.all_eight_numeric_integers=std::all_of(first.begin(),first.end(),[](const auto &field){return field.present&&field.integer_value.has_value();});
    out.available=true;out.status="observed_business_variables";return true;
  } catch(...) {out.available=false;out.unavailable_reason="business_variable_query_exception";return true;}
}

std::string SerializeWhitePlayerBusinessVariablesV1(const WhitePlayerBusinessVariablesResultV1 &out) {
  // All strings below are fixed literals or internal fixed refusal values.
  std::string wire="{\"schema\":\"ck3-native-white-player-business-variables-v1\",\"step\":\""+
      std::string(kWhitePlayerBusinessVariablesV1Step)+"\",\"available\":"+(out.available?"true":"false");
  const auto boolean=[&](const char *key,bool value){wire+=",\""+std::string(key)+"\":"+(value?"true":"false");};
  const auto number=[&](const char *key,auto value){wire+=",\""+std::string(key)+"\":"+std::to_string(value);};
  boolean("all_eight_numeric_integers",out.all_eight_numeric_integers);
  boolean("owner_thread_verified",out.owner_thread_verified);boolean("frame_verified",out.frame_verified);
  boolean("source_abi_pins_verified",out.source_abi_pins_verified);boolean("player_scope_verified",out.player_scope_verified);
  boolean("stable_two_pass_values",out.stable_two_pass_values);
  boolean("rendered_text_available",false);boolean("selected_down_available",false);boolean("scriptvalue_price_available",false);
  number("game_pid",out.game_pid);number("native_revision",out.native_revision);number("connection_generation",out.connection_generation);
  number("played_character_id",out.played_character_id);number("date_raw",out.date_raw);
  number("application_thread_id",out.application_thread_id);number("application_pump_epoch",out.application_pump_epoch);
  number("application_tls_context",out.application_tls_context);number("variable_context",out.variable_context);
  number("character_address",out.character_address);
  number("fixed_scale",kWhiteVariableFixedScaleV1);
  wire+=",\"fields\":{";
  for(std::size_t i=0;i<out.fields.size();++i) {
    if(i)wire+=',';
    const auto &value=out.fields[i];
    wire+='"'+std::string(kWhitePlayerBusinessVariableKeysV1[i])+"\":{\"present\":"+(value.present?"true":"false");
    wire+=",\"actual_kind\":"+(value.present?std::to_string(value.actual_kind):"null");
    wire+=",\"actual_payload\":"+(value.present?std::to_string(value.actual_payload):"null");
    wire+=",\"fixed_raw\":"+(value.fixed_raw?std::to_string(*value.fixed_raw):"null");
    wire+=",\"integer_value\":"+(value.integer_value?std::to_string(*value.integer_value):"null")+'}';
  }
  wire+="},\"status\":\""+out.status+"\",\"unavailable_reason\":\""+out.unavailable_reason+"\"}";
  return wire;
}
} // namespace xar::ck3_11906
