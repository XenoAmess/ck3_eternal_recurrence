#include "xar_bridge/war_payment_window_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <limits>

namespace xar::ck3_12004 {
namespace {
bool MachineId(std::string_view value) noexcept {
  if(value.empty()||value.size()>128)return false;
  for(const auto c:value)if(!((c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='-'))return false;
  return true;
}
std::uint64_t CreateTime() noexcept {
  FILETIME created{},exit{},kernel{},user{};
  if(!GetProcessTimes(GetCurrentProcess(),&created,&exit,&kernel,&user))return 0;
  return (static_cast<std::uint64_t>(created.dwHighDateTime)<<32)|created.dwLowDateTime;
}
bool State(WarPaymentWindow12004 &w,std::uintptr_t &identity,std::uint64_t &date,std::uint32_t &day) noexcept {
  constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
  return w.read&&w.module_base&&w.module_base<=max-0x5C68C50&&
    w.read(w.read_context,w.module_base+0x5C68C50,&identity,sizeof identity)&&identity&&identity<=max-0xA0&&
    w.read(w.read_context,identity+8,&date,sizeof date)&&w.read(w.read_context,identity+0x9C,&day,sizeof day);
}
void StopLocked(WarPaymentWindow12004 &w,std::string_view reason) {
  w.admitted=false;w.session.same_owned_process_no_load_window=false;
  w.session.controlled_window_id=0;w.reason=reason;
  if(w.journal)(void)w.journal->SetEnabled(false);
}
bool CheckLocked(WarPaymentWindow12004 &w) {
  if(!w.admitted)return false;
  if(!ReadArmyNaturalPhaseResearchSampling12004().enabled) {StopLocked(w,"natural_phase_sampling_disabled");return false;}
  std::uintptr_t state=0;std::uint64_t date=0;std::uint32_t day=0;
  if(!State(w,state,date,day)) {StopLocked(w,"game_state_read_failed");return false;}
  if(state!=w.session.game_state_identity_witness) {StopLocked(w,"game_state_identity_changed");return false;}
  if(w.session.native_date_raw&&static_cast<std::uint32_t>(date)<static_cast<std::uint32_t>(*w.session.native_date_raw)) {StopLocked(w,"native_date_rollback");return false;}
  if(w.session.absolute_day_raw&&day<*w.session.absolute_day_raw) {StopLocked(w,"absolute_day_rollback");return false;}
  w.session.native_date_raw=date;w.session.absolute_day_raw=day;return true;
}
} // namespace
void ConfigureWarPaymentWindow12004(WarPaymentWindow12004 &w,std::uintptr_t base,
  ArmyNaturalPhaseRead12004 read,void *context,WarPaymentJournal12004 &journal) noexcept {
  try {const std::lock_guard lock(w.mutex);w.module_base=base;w.read=read;w.read_context=context;w.journal=&journal;StopLocked(w,"not_enabled");}catch(...){}
}
WarPaymentWindowControl12004 ControlWarPaymentWindow12004(WarPaymentWindow12004 &w,std::string_view mode,
  std::string_view contract,std::string_view machine,const WarPaymentCurrentFrame12004 &f) noexcept {
  try {
    const std::lock_guard lock(w.mutex);WarPaymentWindowControl12004 out{};out.requested=mode;
    if(mode!="query"&&mode!="enable"&&mode!="disable") {out.reason="invalid_control";return out;}
    if(!w.journal) {out.reason="observer_not_configured";return out;}
    if(MachineId(machine)) {
      if(!w.machine_id.empty()&&w.machine_id!=machine) {StopLocked(w,"machine_binding_changed");out.reason=w.reason;return out;}
      w.machine_id=machine;
    }
    if(mode=="disable") {
      StopLocked(w,"explicitly_disabled");const auto state=w.journal->SetEnabled(false);
      out.accepted=state.available&&!state.enabled&&!state.busy&&state.clear_completed;
      out.reason=out.accepted?"disabled":"clear_pending";return out;
    }
    if(mode=="query") {if(w.machine_id.empty()&&MachineId(machine))w.machine_id=machine;out.accepted=true;if(w.admitted)(void)CheckLocked(w);out.reason=w.reason;return out;}
    if(contract!="same_owned_process_no_load_v1"||!MachineId(machine)) {out.reason="explicit_no_load_window_and_machine_id_required";return out;}
    if(!f.connection_generation||!f.snapshot_revision||!f.player_character_full_id||f.player_character_full_id==0xFFFFFFFFU||
       !f.paused||!f.map_ready||!f.alive) {out.reason="current_paused_player_frame_required";return out;}
    const auto natural=ReadArmyNaturalPhaseResearchSampling12004();
    if(!natural.available||!natural.enabled||natural.busy) {out.reason="natural_phase_sampling_must_be_enabled";return out;}
    std::uintptr_t state=0;std::uint64_t date=0;std::uint32_t day=0;const auto created=CreateTime();
    if(!created||!State(w,state,date,day)||static_cast<std::uint32_t>(date)!=static_cast<std::uint32_t>(f.native_date_raw)) {out.reason="actual_process_and_game_state_binding_unavailable";return out;}
    if(w.admitted) {
      if(w.machine_id!=machine||w.session.connection_generation!=f.connection_generation||
         w.session.player_character_full_id!=f.player_character_full_id||w.session.process_create_time_100ns!=created||
         w.session.game_state_identity_witness!=state) {StopLocked(w,"existing_window_binding_changed");out.reason=w.reason;return out;}
      if(!CheckLocked(w)) {out.reason=w.reason;return out;}
      w.session.snapshot_revision=f.snapshot_revision;out.accepted=true;out.reason="already_enabled";return out;
    }
    const auto sampling=w.journal->SetEnabled(true);
    if(!sampling.available||!sampling.enabled||!sampling.epoch) {out.reason="sampling_enable_incomplete";return out;}
    w.machine_id=machine;w.session={};w.session.pid=GetCurrentProcessId();w.session.process_create_time_100ns=created;
    w.session.connection_generation=f.connection_generation;w.session.player_character_full_id=f.player_character_full_id;
    w.session.controlled_window_id=sampling.epoch;w.session.same_owned_process_no_load_window=true;
    w.session.game_state_identity_witness=state;w.session.snapshot_revision=f.snapshot_revision;
    w.session.native_date_raw=date;w.session.absolute_day_raw=day;
    // loaded_game_epoch deliberately remains null. The window is an explicit
    // operator contract; a pointer, process clock or journal epoch is not a load epoch.
    w.admitted=true;w.reason="enabled_controlled_no_load_window";out.accepted=true;out.reason=w.reason;return out;
  }catch(...) {return {false,std::string(mode),"control_exception"};}
}
void ObserveWarPaymentWindowFrame12004(WarPaymentWindow12004 &w,const WarPaymentCurrentFrame12004 &f) noexcept {
  try {
    const std::lock_guard lock(w.mutex);if(!w.admitted)return;
    if(!f.map_ready||!f.alive||!f.player_character_full_id||f.player_character_full_id==0xFFFFFFFFU||
       f.connection_generation!=w.session.connection_generation||f.player_character_full_id!=w.session.player_character_full_id||
       (w.session.native_date_raw&&static_cast<std::uint32_t>(f.native_date_raw)<static_cast<std::uint32_t>(*w.session.native_date_raw))) {StopLocked(w,"current_frame_or_owner_or_connection_changed");return;}
    if(CheckLocked(w))w.session.snapshot_revision=f.snapshot_revision;
  }catch(...) {InvalidateWarPaymentWindow12004(w,"frame_observation_exception");}
}
void InvalidateWarPaymentWindow12004(WarPaymentWindow12004 &w,std::string_view reason) noexcept {
  try {const std::lock_guard lock(w.mutex);StopLocked(w,reason);}catch(...){}
}
WarPaymentSession12004 ReadWarPaymentWindowSession12004(void *context) noexcept {
  if(!context)return {};
  auto &w=*static_cast<WarPaymentWindow12004 *>(context);
  try {const std::lock_guard lock(w.mutex);(void)CheckLocked(w);return w.session;}catch(...) {return {};}
}
bool RetainWarPaymentWindowActor12004(void *context,WarPaymentKind12004 kind,std::uintptr_t receiver,std::uintptr_t second) noexcept {
  if(!context)return true;
  auto &w=*static_cast<WarPaymentWindow12004 *>(context);
  try {
    const std::lock_guard lock(w.mutex);if(!w.admitted)return false;
    // The transition's Army is retained without resolving native registries.
    // Gateway/leaf retain only the dynamically bound full-generation Character.
    if(kind==WarPaymentKind12004::transition)return true;
    const auto character=kind==WarPaymentKind12004::gateway?receiver:second;
    if(!character||character>(std::numeric_limits<std::uintptr_t>::max)()-0x20||!w.read)return true;
    std::uint32_t id=0,magic=0;
    if(!w.read(w.read_context,character+0x18,&id,sizeof id)||!w.read(w.read_context,character+0x1C,&magic,sizeof magic))return true;
    return magic!=0x43686172U||id==0xFFFFFFFFU||!w.session.player_character_full_id||id==*w.session.player_character_full_id;
  }catch(...) {return true;}
}
WarPaymentEnvelope12004 ReadWarPaymentWindowEnvelope12004(WarPaymentWindow12004 &w,const WarPaymentDetourState12004 &state) {
  const std::lock_guard lock(w.mutex);if(w.admitted)(void)CheckLocked(w);
  WarPaymentEnvelope12004 out{};out.machine_id=w.machine_id;out.executable_sha256=kExecutableSha256;
  out.current_session=w.session;out.installed=state.installed.load(std::memory_order_acquire);
  out.install_failure_flags=state.failure_flags.load(std::memory_order_acquire);out.controlled_window_admitted=w.admitted;return out;
}
std::string SerializeWarPaymentWindowControl12004(const WarPaymentWindowControl12004 &control) {
  const auto quote=[](std::string_view value) {
    std::string out="\"";constexpr char hex[]="0123456789abcdef";
    for(const unsigned char c:value) {
      if(c=='"'||c=='\\') {out+='\\';out+=static_cast<char>(c);}
      else if(c<32) {out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}
      else out+=static_cast<char>(c);
    }
    out+='"';return out;
  };
  return "{\"requested\":"+quote(control.requested)+",\"accepted\":"+(control.accepted?"true":"false")+",\"reason\":"+quote(control.reason)+"}";
}
} // namespace xar::ck3_12004
