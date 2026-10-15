#include "xar_bridge/war_payment_runtime_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <array>
#include <bit>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using namespace xar::ck3_12004;
std::uint64_t checks=0,failures=0;
void Check(bool ok,const char *name) {++checks;if(!ok){++failures;std::cerr<<"FAILED "<<name<<'\n';}}
template<class T,std::size_t N> void Put(std::array<std::byte,N> &buffer,std::size_t offset,T value) {
  if(offset+sizeof value>buffer.size())throw std::runtime_error("fixture offset");
  std::memcpy(buffer.data()+offset,&value,sizeof value);
}
struct Fixture {
  std::array<std::byte,0x200> character{};
  std::array<std::byte,0x400> living{};
  std::array<std::byte,0x300> context{},other_context{};
  std::uint64_t clock_sequence=0;
  std::uint32_t original_calls=0,context_pointer_reads=0,stack_calls=0;
  bool failed_2c8=false,unstable_pointer=false,mutate_context=false,bad_arguments=false;
  int stack_mode=0;
  std::int64_t amount=300000;
  WarPaymentKind12004 kind=WarPaymentKind12004::personal_add;
  Fixture() {
    Put(character,0x10,std::uint32_t{999999}); // Poison neighboring identity field.
    Put(character,0x18,std::uint32_t{32101});Put(character,0x1C,std::uint32_t{0x43686172});
    Put(character,0x1B0,reinterpret_cast<std::uintptr_t>(living.data()));
    Put(character,0x1C0,reinterpret_cast<std::uintptr_t>(context.data()));
    Put(living,0x100,std::uint64_t{10000000});
    Put(living,0x2C0,std::int64_t{777777777}); // Must not confuse living with context.
    Put(context,0x20,std::int64_t{123456789});
    Put(context,0x2C0,std::int64_t{1000000});Put(context,0x2C8,std::int64_t{400000});
    Put(context,0x28,std::int64_t{100000});Put(context,0x30,std::int64_t{200000});
    other_context=context;
  }
};
Fixture *active=nullptr;
bool Read(void *opaque,std::uintptr_t address,void *out,std::size_t bytes) noexcept {
  auto &f=*static_cast<Fixture *>(opaque);
  if(address==reinterpret_cast<std::uintptr_t>(f.character.data())+0x1C0) {
    ++f.context_pointer_reads;
    if(f.unstable_pointer&&f.context_pointer_reads==2) {
      const auto changed=reinterpret_cast<std::uintptr_t>(f.other_context.data());
      if(bytes!=sizeof changed)return false;
      std::memcpy(out,&changed,bytes);return true;
    }
  }
  if(f.failed_2c8&&address==reinterpret_cast<std::uintptr_t>(f.context.data())+0x2C8)return false;
  const auto copy=[&](const auto &buffer) {
    const auto begin=reinterpret_cast<std::uintptr_t>(buffer.data());
    if(address<begin||bytes>buffer.size()||address-begin>buffer.size()-bytes)return false;
    std::memcpy(out,buffer.data()+(address-begin),bytes);return true;
  };
  return copy(f.character)||copy(f.living)||copy(f.context)||copy(f.other_context);
}
ArmyNaturalPhaseEvent12004 Next(void *opaque) noexcept {
  auto &f=*static_cast<Fixture *>(opaque);return {991,++f.clock_sequence,77};
}
WarPaymentSession12004 Session(void *) noexcept {
  WarPaymentSession12004 s{};s.pid=1234;s.process_create_time_100ns=4567;s.connection_generation=9;
  s.controlled_window_id=3;s.same_owned_process_no_load_window=true;s.game_state_identity_witness=0x5555;
  s.player_character_full_id=32101;s.snapshot_revision=7;s.native_date_raw=53145072;s.absolute_day_raw=389378;return s;
}
std::uint32_t Stack(void *opaque,std::uintptr_t *frames,std::size_t capacity) noexcept {
  auto &f=*static_cast<Fixture *>(opaque);++f.stack_calls;
  Check(capacity==32,"bounded stack ABI capacity32");
  if(!frames||capacity<4)return 0;
  constexpr std::uintptr_t base=0x140000000,known=base+kWarPaymentGenericReturn12004;
  frames[0]=0x700000000000;frames[1]=known;frames[2]=base+0x28A1234;frames[3]=0x710000000000;
  switch(f.stack_mode) {
    case 1:frames[1]=base+0x1234;return 4; // Known caller absent.
    case 2:frames[2]=known;return 4; // Ambiguous recursion, no parent claim.
    case 3:frames[2]=0x7FFF00001234;return 4; // Parent belongs to another image.
    case 4:return 0;
    case 5:return 33; // Malformed provider count; retain unknown, no OOB.
    case 6:frames[0]=known;return 1; // Known caller at end; parent unavailable.
    default:return 4;
  }
}
std::uintptr_t __fastcall Original(void *wrapper,std::int64_t amount,void *character) {
  auto &f=*active;++f.original_calls;
  if(wrapper!=f.living.data()+0xF8||character!=f.character.data()||amount!=f.amount)f.bad_arguments=true;
  std::uint64_t balance=0;std::memcpy(&balance,f.living.data()+0x100,sizeof balance);
  if(f.kind==WarPaymentKind12004::personal_sub)balance-=static_cast<std::uint64_t>(amount);
  else balance+=static_cast<std::uint64_t>(amount);
  Put(f.living,0x100,balance);
  if(f.mutate_context)Put(f.context,0x2C8,std::int64_t{400001});
  return 0x1122334455667788;
}
std::string Run(const char *name,int mode) {
  auto fixture=std::make_unique<Fixture>();auto &f=*fixture;active=&f;
  auto journal=std::make_unique<WarPaymentJournal12004>();(void)journal->SetEnabled(true);
  WarPaymentBindings12004 b{};b.exact_build_and_prefixes_verified=true;b.read=&Read;b.read_context=&f;
  b.next_event=&Next;b.event_context=&f;b.session=&Session;b.journal=journal.get();
  b.generic_context_capture_enabled=mode!=1;b.generic_module_base=0x140000000;b.generic_module_image_size=0x6000000;
  b.capture_stack_frames=&Stack;b.capture_stack_context=&f;
  auto pc=kWarPaymentGenericReturn12004;
  if(mode==2)++pc;
  if(mode==3)f.kind=WarPaymentKind12004::personal_sub;
  if(mode==4)f.failed_2c8=true;
  if(mode==5)f.unstable_pointer=true;
  if(mode==6)Put(f.character,0x1C0,std::uintptr_t{0});
  if(mode>=7&&mode<=12)f.stack_mode=mode-6;
  if(mode==13)f.mutate_context=true;
  if(mode==14) {
    Put(f.context,0x2C0,(std::numeric_limits<std::int64_t>::max)());
    Put(f.context,0x2C8,std::int64_t{-1});Put(f.context,0x28,std::int64_t{0});Put(f.context,0x30,std::int64_t{0});f.amount=0;
  }
  if(mode==15) {
    Put(f.context,0x2C0,std::int64_t{100});Put(f.context,0x2C8,std::int64_t{100});
    Put(f.context,0x28,std::int64_t{0});Put(f.context,0x30,std::int64_t{0});f.amount=0;
  }
  const auto returned=InvokeWarPaymentWriter12004(b,&Original,f.kind,f.living.data()+0xF8,f.amount,f.character.data(),pc);
  Check(f.original_calls==1,"original called once under success/failure/OFF");
  Check(returned==0x1122334455667788&&!f.bad_arguments,"actual Win64 three-argument forwarding and return preserved");
  const auto snapshot=journal->Copy();Check(snapshot.read_complete&&snapshot.records.size()==1,"raw record retained");
  if(snapshot.records.size()!=1)throw std::runtime_error("fixture journal record absent");
  const auto &record=snapshot.records[0];
  Check(record.before.character_id==32101U,"Character identity uses18 not poisoned10");
  const bool selected=mode!=1&&mode!=2&&mode!=3;
  Check(record.generic_wallet_context.has_value()==selected,"defaultOFF and exact kind/caller selector");
  Check(f.context_pointer_reads==(selected?4U:0U)&&f.stack_calls==(selected?1U:0U),"unselected path performs no extra context/stack reads");
  if(selected) {
    const auto &g=*record.generic_wallet_context;
    if(mode==4)Check(!g.before.capture_complete&&g.before.failed_reads==1&&!g.before.value_2c8&&!g.before_computed_add_raw,"read failure retained null");
    else if(mode==5)Check(!g.before.context_stable&&!g.before.capture_complete&&g.before.value_2c0==1000000,"changed after pointer preserves previously read raw fields");
    else if(mode==6)Check(!g.before.capture_complete&&g.before.context_identity_before==std::uintptr_t{0}&&!g.before.value_2c0,"null context is not observed zero input");
    else if(mode==14)Check(g.before_computed_add_raw==(std::numeric_limits<std::int64_t>::min)()&&g.before_formula_matches_amount==false,"signed64 source wrap without UB");
    else if(mode==15)Check(g.before_computed_add_raw==0&&g.before_formula_matches_amount==true&&g.before.value_28==0,"available signed zero inputs preserved");
    else Check(g.before.value_2c0==1000000&&g.before.value_2c8==400000&&g.before.value_28==100000&&g.before.value_30==200000&&g.before_computed_add_raw==300000,"exact1C0 and all four source offsets, not poisoned living/20");
    if(mode==13)Check(!g.context_values_stable&&g.before_formula_matches_amount==true,"changed after context not promoted stable");
    if(mode==7||mode==8||mode==10||mode==11||mode==12)Check(!g.parent_trace.parent_return_rva,"missing/ambiguous/failed/bounded stack stays null parent");
    else if(mode==9)Check(g.parent_trace.parent_return_absolute.has_value()&&!g.parent_trace.parent_return_rva&&!g.parent_trace.parent_in_same_image,"foreign-image parent absolute retained, no false EXE RVA");
    else Check(g.parent_trace.parent_return_rva==std::uintptr_t{0x28A1234}&&g.parent_trace.parent_in_same_image,"unique actual-caller-following frame derives same-image parent RVA");
  }
  WarPaymentEnvelope12004 e{};e.machine_id="fixture-only";e.executable_sha256=kExecutableSha256;
  e.current_session=Session(nullptr);e.installed=true;e.controlled_window_admitted=true;
  ArmyNaturalPhaseJournalStatus12004 ns{};ns.read_complete=true;
  const auto json=SerializeWarPaymentJournal12004(snapshot,e,{},ns);
  return std::string("{\"case\":\"")+name+"\",\"value\":"+json+"}";
}
} // namespace
int main(int argc,char **argv) {
  if(argc!=2)return 2;
  try {
    const std::array<const char *,16> names{{"positive","default_off","wrong_caller","wrong_kind","failed_value_read","changed_context_pointer","null_context","missing_caller_frame","duplicate_caller_frame","foreign_image_parent","stack_failure","stack_provider_count_overflow","parent_unavailable_at_trace_end","changed_after_inputs","source_signed_wrap","available_zero_inputs"}};
    std::string wire="[";
    for(std::size_t i=0;i<names.size();++i){if(i)wire+=',';wire+=Run(names[i],static_cast<int>(i));}
    wire+="]\n";std::ofstream output(argv[1],std::ios::binary);output<<wire;
    if(!output)return 2;
    std::cout<<"{\"summary\":true,\"checks\":"<<checks<<",\"failures\":"<<failures<<",\"case_count\":16}\n";
    return failures?1:0;
  } catch(const std::exception &error) {std::cerr<<error.what()<<'\n';return 2;}
}
