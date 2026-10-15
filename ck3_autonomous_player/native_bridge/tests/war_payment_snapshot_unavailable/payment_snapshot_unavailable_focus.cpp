#include "xar_bridge/war_payment_passive_12004.hpp"
#include "xar_bridge/war_payment_runtime_12004.hpp"
#if defined(XAR_PAYMENT_WINDOW_FIXTURE)
#include "xar_bridge/war_payment_window_12004.hpp"
#endif
#include <windows.h>
#include <intrin.h>
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdio>
#include <cstring>
#include <limits>
#include <memory>
#include <fstream>
#include <string>
#include <vector>

using namespace xar::ck3_12004;
#if defined(XAR_PAYMENT_WINDOW_FIXTURE)
namespace fixture_natural_dependency {ArmyObserverResearchSamplingState12004 state{};}
namespace xar::ck3_12004 {
// Explicit fake dependency: window calls the existing natural sampler status.
// This fixture does not compile/install or claim to qualify that other observer.
ArmyObserverResearchSamplingState12004 ReadArmyNaturalPhaseResearchSampling12004() noexcept {
  return ::fixture_natural_dependency::state;
}
}
#endif
extern "C" const unsigned char xar_payment_abi_probe[];
extern "C" const unsigned char xar_payment_abi_bad_callback[];
namespace {
using U=std::uintptr_t;
constexpr U kTransitionReturn=0xFEDCBA9876543211ULL,kGatewayReturn=0xDEADC0DE87654321ULL,kWriterReturn=0xABCDEF0987654321ULL;
int g_failures=0,g_checks=0;
const char *g_machine_id=nullptr;
const char *g_case="init";
void Check(bool value,const char *name) {
  ++g_checks;if(!value)++g_failures;
  std::printf("{\"machine_id\":\"%s\",\"case\":\"%s\",\"check\":\"%s\",\"passed\":%s}\n",g_machine_id,g_case,name,value?"true":"false");
}
template<class T,std::size_t N> void Put(std::array<unsigned char,N> &a,std::size_t off,T value) {
  if(off+sizeof value>a.size())std::terminate();std::memcpy(a.data()+off,&value,sizeof value);
}
template<class T,std::size_t N> T Get(const std::array<unsigned char,N> &a,std::size_t off) {
  T value{};if(off+sizeof value>a.size())std::terminate();std::memcpy(&value,a.data()+off,sizeof value);return value;
}
struct World {
  std::array<unsigned char,0x400> character{},extension{},land{};
  std::array<unsigned char,0x240> army{};
  std::array<unsigned char,0x900> province{};
  std::unique_ptr<WarPaymentJournal12004> journal=std::make_unique<WarPaymentJournal12004>();
  WarPaymentBindings12004 bindings{};WarPaymentSession12004 session{};
  std::uint64_t event=1;std::uint32_t event_thread=GetCurrentThreadId();
  int transitions=0,gateways=0,writers=0;bool reads_fail=false,mutate_epoch=false,disable_in_original=false;
  bool side_effect=false,busy_witness=false,mutate_clock=false;
  bool mutate_window=false,mutate_owner=false,mutate_generation=false;
  bool mutate_character=false,mutate_land=false,mutate_create_time=false;
  int recursion=0,remaining_recursion=0;
  U received_character=0;std::int32_t received_resource=0,received_component=0;
  std::int64_t received_amount=0;U received_wrapper=0;
  std::int32_t selected_resource=0;
  std::int64_t payment_amount=500000;
  std::vector<std::pair<U,std::size_t>> code_ranges;
  void *Character(){return character.data();}void *Army(){return army.data();}void *Province(){return province.data();}
  void *Wrapper(bool use_land=false){return use_land?land.data()+0x310:extension.data()+0xF8;}
  World();
};
World *g_world=nullptr;
bool Read(void *context,U address,void *out,std::size_t bytes) noexcept {
  auto &w=*static_cast<World*>(context);if(w.reads_fail)return false;
  for(auto [ptr,size]:std::array<std::pair<const unsigned char*,std::size_t>,5>{{
      {w.character.data(),w.character.size()},{w.extension.data(),w.extension.size()},
      {w.land.data(),w.land.size()},{w.army.data(),w.army.size()},{w.province.data(),w.province.size()}}}) {
    const auto begin=reinterpret_cast<U>(ptr);
    if(address>=begin && address-begin<=size && bytes<=size-(address-begin)) {
      std::memcpy(out,reinterpret_cast<const void*>(address),bytes);return true;
    }
  }
  for(const auto [begin,size]:w.code_ranges)
    if(address>=begin && address-begin<=size && bytes<=size-(address-begin)) {
      std::memcpy(out,reinterpret_cast<const void*>(address),bytes);return true;
    }
  return false;
}
ArmyNaturalPhaseEvent12004 Next(void *context) noexcept {
  auto &w=*static_cast<World*>(context);return {reinterpret_cast<U>(&w),++w.event,w.event_thread};
}
WarPaymentSession12004 Session(void *context) noexcept {return static_cast<World*>(context)->session;}
ArmyNaturalPhaseScope12004 Natural(void *context) noexcept {
  auto &w=*static_cast<World*>(context);ArmyNaturalPhaseScope12004 p{};
  p.observed=true;p.phase=ArmyNaturalPhaseKind12004::post_date;p.actual_entry_rva=0x2A9A570;
  p.primary_manager_identity=reinterpret_cast<U>(&w)+1;p.game_state_identity=reinterpret_cast<U>(&w)+2;
  p.session_identity=w.session.loaded_game_epoch;p.entry_event={reinterpret_cast<U>(&w),1,w.event_thread};
  p.date_raw=123456;p.absolute_day_raw=5144;return p;
}
World::World() {
  Put(character,0x18,std::uint32_t{0x7E654321});Put(character,0x1C,std::uint32_t{0x43686172});
  Put(character,0x1B0,reinterpret_cast<U>(extension.data()));Put(extension,0x100,std::uint64_t{90'000'000});
  Put(land,0x10,std::uint32_t{0x1234});Put(land,0x14,std::uint32_t{0x4C616E64});Put(land,0x318,std::uint64_t{80'000'000});
  Put(army,0x10,std::uint32_t{0x654321});Put(army,0x14,std::uint32_t{0x41726D79});
  Put(army,0x124,std::uint32_t{0xAA012345});Put(army,0x1D4,std::uint8_t{0});Put(province,0x85C,std::uint32_t{0x50726F76});
  session.pid=GetCurrentProcessId();session.connection_generation=7;session.loaded_game_epoch=0x9876;
  FILETIME create{},exit{},kernel{},user{};
  if(GetProcessTimes(GetCurrentProcess(),&create,&exit,&kernel,&user))
    session.process_create_time_100ns=(std::uint64_t{create.dwHighDateTime}<<32)|create.dwLowDateTime;
  session.game_state_identity_witness=reinterpret_cast<U>(this)+2;
  session.native_date_raw=123456;session.absolute_day_raw=5144;
  session.player_character_full_id=Get<std::uint32_t>(character,0x18);session.snapshot_revision=4;
  bindings.exact_build_and_prefixes_verified=true;bindings.read=&Read;bindings.read_context=this;
  bindings.next_event=&Next;bindings.event_context=this;bindings.session=&Session;bindings.session_context=this;
  bindings.natural_metadata=&Natural;bindings.natural_context=this;bindings.journal=journal.get();
  journal->SetEnabled(true);g_world=this;
}
U __fastcall OriginalWriter(void *wrapper,std::int64_t amount,void *character) noexcept {
  auto &w=*g_world;++w.writers;w.received_wrapper=reinterpret_cast<U>(wrapper);
  w.received_character=reinterpret_cast<U>(character);w.received_amount=amount;
  w.busy_witness=w.journal->Copy().sampling.busy;
  std::uint64_t value{};std::memcpy(&value,static_cast<unsigned char*>(wrapper)+8,8);
  value-=static_cast<std::uint64_t>(amount);if(w.side_effect)value+=200000;
  std::memcpy(static_cast<unsigned char*>(wrapper)+8,&value,8);
  if(w.mutate_epoch)w.session.loaded_game_epoch=w.session.loaded_game_epoch.value()+1;
  if(w.mutate_clock)++w.event_thread;
  if(w.mutate_window)++w.session.controlled_window_id;
  if(w.mutate_owner)w.session.player_character_full_id=w.session.player_character_full_id.value()+1;
  if(w.mutate_generation)++w.session.connection_generation;
  if(w.mutate_create_time)++w.session.process_create_time_100ns;
  if(w.mutate_character)Put(w.character,0x18,Get<std::uint32_t>(w.character,0x18)+1);
  if(w.mutate_land)Put(w.land,0x10,Get<std::uint32_t>(w.land,0x10)+1);
  if(w.disable_in_original)w.journal->SetEnabled(false);
  return kWriterReturn;
}
U __fastcall OriginalAdd(void *wrapper,std::int64_t amount,void *character) noexcept {
  auto &w=*g_world;++w.writers;w.received_wrapper=reinterpret_cast<U>(wrapper);
  w.received_character=reinterpret_cast<U>(character);w.received_amount=amount;
  std::uint64_t value{};std::memcpy(&value,static_cast<unsigned char*>(wrapper)+8,8);
  value+=static_cast<std::uint64_t>(amount);std::memcpy(static_cast<unsigned char*>(wrapper)+8,&value,8);
  return kWriterReturn;
}
U __fastcall OriginalGateway(void *character,std::int32_t resource,std::int64_t amount,std::int32_t component) noexcept {
  auto &w=*g_world;++w.gateways;w.received_character=reinterpret_cast<U>(character);
  w.received_resource=resource;w.received_component=component;w.received_amount=amount;
  if(resource==0 || resource==3)
    InvokeWarPaymentWriter12004(w.bindings,&OriginalWriter,resource==0?WarPaymentKind12004::personal_sub:WarPaymentKind12004::land_sub,
      w.Wrapper(resource==3),amount,character,resource==0?0x28B99B2:0x28B9A6D);
  return kGatewayReturn;
}
U __fastcall OriginalTransition(void *army,void *province) noexcept {
  auto &w=*g_world;++w.transitions;
  if(army!=w.Army() || province!=w.Province())return 0;
  if(w.remaining_recursion>0) {
    --w.remaining_recursion;++w.recursion;
    InvokeWarPaymentTransition12004(w.bindings,&OriginalTransition,army,province,0x2A9A8C5);
  } else InvokeWarPaymentGateway12004(w.bindings,&OriginalGateway,w.Character(),w.selected_resource,w.payment_amount,3,0x24E8F40);
  return kTransitionReturn;
}
const WarPaymentRecord12004 *Find(const WarPaymentJournalSnapshot12004 &s,WarPaymentKind12004 kind) {
  for(const auto &r:s.records)if(r.kind==kind)return &r;return nullptr;
}
struct alignas(16) AbiResult {
  U returned=0,stack_before=0,stack_after=0;
  std::array<U,8> gp{};U canary=0;std::array<std::array<std::uint64_t,2>,10> xmm{};
};
using Probe=U(__fastcall *)(U,const std::array<U,4>*,AbiResult*);
void Abi(U callback,std::array<U,4> args,U expected) {
  if(offsetof(AbiResult,xmm)!=96){Check(false,"ABI_probe_layout");return;}
  AbiResult r{};const auto returned=reinterpret_cast<Probe>(const_cast<unsigned char*>(xar_payment_abi_probe))(callback,&args,&r);
  Check(returned==expected && r.returned==expected,"opaque_full_64_bit_RAX");
  Check(r.stack_before==r.stack_after && (r.stack_before&15)==0,"RSP_recovered_and_call_alignment");
  Check(r.canary==0xD1E2F31425364758ULL,"caller_stack_canary");
  Check(r.gp==std::array<U,8>{0x1111111122222222ULL,0x3333333344444444ULL,0x5555555566666666ULL,0x7777777788888888ULL,0x99999999AAAAAAAAULL,0xBBBBBBBBCCCCCCCCULL,0xDDDDDDDDEEEEEEEEULL,0x123456789ABCDEF0ULL},"all_8_nonvolatile_GP_registers");
  bool xmm=true;for(std::size_t i=0;i<10;++i)for(const auto lane:r.xmm[i])xmm=xmm && lane==((~std::uint64_t{0})<<(i+6));
  Check(xmm,"all_10_nonvolatile_XMM_registers");
}
U __fastcall TransitionEntry(void *a,void *p) noexcept {
  return InvokeWarPaymentTransition12004(g_world->bindings,&OriginalTransition,a,p,0x2A9A8C5);
}
U __fastcall GatewayEntry(void *c,std::int32_t resource,std::int64_t amount,std::int32_t component) noexcept {
  return InvokeWarPaymentGateway12004(g_world->bindings,&OriginalGateway,c,resource,amount,component,0x24E8F40);
}
U __fastcall AddEntry(void *p,std::int64_t a,void *c) noexcept {
  return InvokeWarPaymentWriter12004(g_world->bindings,&OriginalAdd,WarPaymentKind12004::personal_add,p,a,c,0x111);
}
U __fastcall SubEntry(void *p,std::int64_t a,void *c) noexcept {
  return InvokeWarPaymentWriter12004(g_world->bindings,&OriginalWriter,WarPaymentKind12004::personal_sub,p,a,c,0x222);
}
U __fastcall LandEntry(void *p,std::int64_t a,void *c) noexcept {
  return InvokeWarPaymentWriter12004(g_world->bindings,&OriginalWriter,WarPaymentKind12004::land_sub,p,a,c,0x333);
}
void SeamCases() {
  {
    g_case="ABI_probe_sensitivity";AbiResult r{};const std::array<U,4> args{};
    const auto returned=reinterpret_cast<Probe>(const_cast<unsigned char*>(xar_payment_abi_probe))(
      reinterpret_cast<U>(xar_payment_abi_bad_callback),&args,&r);
    Check(returned==0x1122334455667788ULL && r.returned==returned,"probe_observes_intentional_callback_return");
    Check(r.gp[0]==0 && r.xmm[0][0]==0 && r.xmm[0][1]==0 && r.canary==0,"probe_detects_deliberate_GP_XMM_and_caller_canary_corruption");
  }
  {
    g_case="enabled_nested_personal";World w;
    const auto ret=TransitionEntry(w.Army(),w.Province());const auto s=w.journal->Copy();
    Check(ret==kTransitionReturn && w.transitions==1 && w.gateways==1 && w.writers==1,"all_originals_once");
    Check(s.read_complete && s.records.size()==3 && s.latest_sequence==3,"three_distinct_owned_records");
    const auto *leaf=Find(s,WarPaymentKind12004::personal_sub);
    Check(leaf && leaf->source_boarding_call_chain_matches && leaf->same_wrapper_after && leaf->same_character_after,"personal_PC_TLS_account_join");
    Check(leaf && leaf->natural_parent_matches && leaf->session_matches && leaf->clock_thread_order_matches,"phase_session_clock_fences");
    Check(leaf && leaf->before.wrapper_balance_bits==90000000 && leaf->after.wrapper_balance_bits==89500000,"independent_before_after_values");
    Check(w.busy_witness,"query_inside_native_callback_reports_busy");
  }
  {
    g_case="land_account_distinction";World w;w.selected_resource=3;TransitionEntry(w.Army(),w.Province());
    const auto s=w.journal->Copy();const auto *leaf=Find(s,WarPaymentKind12004::land_sub);
    Check(leaf && leaf->source_boarding_call_chain_matches && leaf->same_wrapper_after && !leaf->personal_wrapper_matches_character,"Land_identity_distinct_from_personal");
    Check(Get<std::uint64_t>(w.extension,0x100)==90000000 && Get<std::uint64_t>(w.land,0x318)==79500000,"only_selected_fake_native_account_debited");
  }
  {
    g_case="failed_reads";World w;w.reads_fail=true;TransitionEntry(w.Army(),w.Province());const auto s=w.journal->Copy();
    Check(w.transitions==1 && w.gateways==1 && w.writers==1 && s.records.size()==3,"read_failure_never_replays_or_skips_original");
    const auto *leaf=Find(s,WarPaymentKind12004::personal_sub);
    Check(leaf && leaf->before.failed_reads && !leaf->same_wrapper_after && !leaf->source_boarding_call_chain_matches,"failed_capture_retained_unqualified");
  }
  {
    g_case="sampling_disabled";World w;w.journal->SetEnabled(false);TransitionEntry(w.Army(),w.Province());
    const auto s=w.journal->Copy();Check(w.transitions==1 && w.gateways==1 && w.writers==1,"disabled_original_once");
    Check(!s.read_complete && s.records.empty() && !s.sampling.enabled,"disabled_no_fake_history");
  }
  {
    g_case="native_side_effects";World w;w.side_effect=true;
    SubEntry(w.Wrapper(),500000,w.Character());const auto s=w.journal->Copy();const auto &r=s.records.front();
    Check(r.before.wrapper_balance_bits==90000000 && r.after.wrapper_balance_bits==89700000,"retained_return_balance_not_forced_to_nominal_request");
    Check(!r.source_boarding_call_chain_matches,"generic_gold_write_not_named_boarding_or_maintenance");
  }
  {
    g_case="epoch_changes_in_native";World w;w.mutate_epoch=true;SubEntry(w.Wrapper(),500000,w.Character());
    const auto s=w.journal->Copy();Check(!s.records.front().session_matches,"actual_entry_return_epoch_change_rejected");
  }
  {
    g_case="missing_epoch";World w;w.session.loaded_game_epoch.reset();SubEntry(w.Wrapper(),500000,w.Character());
    const auto s=w.journal->Copy();Check(!s.records.front().session_matches,"missing_epoch_not_fabricated");
  }
  {
    g_case="thread_changes_in_clock";World w;w.mutate_clock=true;SubEntry(w.Wrapper(),500000,w.Character());
    const auto s=w.journal->Copy();Check(!s.records.front().clock_thread_order_matches,"thread_mismatch_rejected");
  }
  {
    g_case="explicit_same_process_no_load_window";World w;w.session.loaded_game_epoch.reset();
    w.session.same_owned_process_no_load_window=true;w.session.controlled_window_id=71;
    SubEntry(w.Wrapper(),500000,w.Character());const auto s=w.journal->Copy();
    Check(s.records.front().session_matches && !s.records.front().session_entry.loaded_game_epoch,"explicit_finite_window_accepted_without_fabricated_load_epoch");
  }
  for(int mode=0;mode<3;++mode) {
    g_case=mode==0?"finite_window_changes":mode==1?"finite_window_owner_changes":"finite_window_generation_changes";
    World w;w.session.loaded_game_epoch.reset();w.session.same_owned_process_no_load_window=true;w.session.controlled_window_id=72;
    w.mutate_window=mode==0;w.mutate_owner=mode==1;w.mutate_generation=mode==2;
    SubEntry(w.Wrapper(),500000,w.Character());const auto s=w.journal->Copy();
    Check(!s.records.front().session_matches,"controlled_contract_change_rejected");
  }
  for(int mode=0;mode<3;++mode) {
    g_case=mode==0?"character_generation_changes":mode==1?"Land_generation_changes":"process_create_time_changes";
    World w;w.mutate_character=mode==0;w.mutate_land=mode==1;w.mutate_create_time=mode==2;
    InvokeWarPaymentWriter12004(w.bindings,&OriginalWriter,mode==1?WarPaymentKind12004::land_sub:WarPaymentKind12004::personal_sub,
      w.Wrapper(mode==1),5,w.Character(),0x456);
    const auto s=w.journal->Copy();const auto &r=s.records.front();
    Check(mode==0?!r.same_character_after:mode==1?!r.same_wrapper_after:!r.session_matches,"generation_or_process_change_is_not_repaired_from_return_frame");
  }
  {
    g_case="signed64_minimum_amount";World w;const auto amount=(std::numeric_limits<std::int64_t>::min)();
    SubEntry(w.Wrapper(),amount,w.Character());const auto s=w.journal->Copy();const auto &r=s.records.front();
    Check(w.writers==1 && r.amount_raw==amount && r.after.wrapper_balance_bits==std::uint64_t{90000000}-static_cast<std::uint64_t>(amount),"signed64_argument_and_modular_account_bits_preserved_without_CPP_overflow");
  }
  {
    g_case="disable_while_active";World w;w.disable_in_original=true;SubEntry(w.Wrapper(),500000,w.Character());
    auto s=w.journal->Copy();Check(w.writers==1 && !s.read_complete && !s.sampling.enabled,"disable_blocks_inflight_publication");
    const auto old_epoch=s.sampling.epoch;w.journal->SetEnabled(true);s=w.journal->Copy();
    Check(s.read_complete && s.records.empty() && s.sampling.epoch>old_epoch,"reenable_clears_and_changes_sampling_epoch");
  }
  {
    g_case="513_event_retention";World w;for(int i=0;i<513;++i)SubEntry(w.Wrapper(),1,w.Character());
    const auto s=w.journal->Copy();Check(w.writers==513 && s.records.size()==512 && s.latest_sequence==513 && s.oldest_sequence==2 && s.overwritten==1,"explicit_ring_overwrite_fences");
    Check(s.records.front().journal_sequence==2 && s.records.back().journal_sequence==513,"records_match_retained_fence");
  }
  {
    g_case="TLS_depth_bound";World w;w.remaining_recursion=10;TransitionEntry(w.Army(),w.Province());
    const auto s=w.journal->Copy();bool exceeded=false;for(const auto &r:s.records)exceeded|=r.tls_depth_exceeded;
    Check(w.transitions==11 && w.gateways==1 && w.writers==1 && exceeded,"finite_TLS_depth_is_observed_without_skipping_native");
  }
  {
    g_case="five_seam_ABIs";World w;
    Abi(reinterpret_cast<U>(&TransitionEntry),{reinterpret_cast<U>(w.Army()),reinterpret_cast<U>(w.Province()),0,0},kTransitionReturn);
    Abi(reinterpret_cast<U>(&GatewayEntry),{reinterpret_cast<U>(w.Character()),std::uint64_t{0xFFFFFFFFU},std::uint64_t{0xFFF00000ABCD1234ULL},std::uint64_t{0xFFFFFFF9U}},kGatewayReturn);
    Check(w.received_resource==-1 && w.received_component==-7 && static_cast<std::uint64_t>(w.received_amount)==0xFFF00000ABCD1234ULL,"gateway_low32_enums_and_signed64_amount_preserved");
    Abi(reinterpret_cast<U>(&AddEntry),{reinterpret_cast<U>(w.Wrapper()),17,reinterpret_cast<U>(w.Character()),0},kWriterReturn);
    Abi(reinterpret_cast<U>(&SubEntry),{reinterpret_cast<U>(w.Wrapper()),19,reinterpret_cast<U>(w.Character()),0},kWriterReturn);
    Abi(reinterpret_cast<U>(&LandEntry),{reinterpret_cast<U>(w.Wrapper(true)),23,reinterpret_cast<U>(w.Character()),0},kWriterReturn);
    Check(w.received_wrapper==reinterpret_cast<U>(w.Wrapper(true)) && w.received_character==reinterpret_cast<U>(w.Character()) && w.received_amount==23,"writer_three_actual_arguments_preserved");
  }
}
#if !defined(XAR_PAYMENT_SEAM_ONLY)
#include "payment_runtime_cases.inc"
#if defined(XAR_PAYMENT_WINDOW_FIXTURE)
#include "payment_window_cases.inc"
#include "payment_snapshot_unavailable_cases-a02.inc"
#endif
#endif
} // namespace
int main(int argc,char **argv) {
  if(argc!=3||std::strcmp(argv[1],"--machine-id")!=0||!argv[2][0]||std::strlen(argv[2])>128)return 2;
  g_machine_id=argv[2];
  SnapshotUnavailableCases12004();
  std::printf("{\"machine_id\":\"%s\",\"summary\":true,\"checks\":%d,\"failures\":%d,\"actual_game_calls\":0}\n",g_machine_id,g_checks,g_failures);
  return g_failures?1:0;
}
