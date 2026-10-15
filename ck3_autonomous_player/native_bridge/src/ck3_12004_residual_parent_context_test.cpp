#include "xar_bridge/ck3_12004_residual_parent_hook.hpp"
#include "xar_bridge/ck3_12004_actual_loss_writer_journal.hpp"
#include <array>
#include <atomic>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>

// Project code and owned local memory only. Source PCs are synthetic premises.
namespace {
namespace native=xar::ck3_12004;
namespace game=xar::game;
constexpr std::int32_t kRegiment=0x03000001,kPersistent=0x05000001;
constexpr std::int32_t kNativeArmy=0x01000000,kPublicArmy=0;
constexpr std::uint64_t kDate=53145552;
#if defined(XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004)
constexpr bool kEnabled=true;
#else
constexpr bool kEnabled=false;
#endif
#if XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004
constexpr bool kSupplyEnabled=true;
#else
constexpr bool kSupplyEnabled=false;
#endif
void Need(bool v,const char *message){if(!v)throw std::runtime_error(message);}
template<class T,std::size_t N>void Store(std::array<std::byte,N> &a,std::size_t offset,T value){
  Need(offset+sizeof(value)<=N,"fixture store outside owned object");
  std::memcpy(a.data()+offset,&value,sizeof value);
}
template<class T,std::size_t N>T Load(const std::array<std::byte,N> &a,std::size_t offset){
  Need(offset+sizeof(T)<=N,"fixture load outside owned object");
  T value{};std::memcpy(&value,a.data()+offset,sizeof value);return value;
}
struct Fixture {
  std::array<std::byte,0x200> army{};
  std::array<std::int32_t,2> ids{kRegiment,0x04000002};
  std::array<std::byte,0x50> regiment{};
  std::array<std::byte,0x20> data{},physical{};
  std::array<std::byte,0x10> game_state{};
  void *game_state_slot=game_state.data();
  std::atomic<unsigned> originals{0},writers{0};
  unsigned zero_bypasses=0,mode=0;
  std::uint8_t expected_flags=0;
  Fixture(){
    Store(army,0x10,kNativeArmy);Store(army,0x14,std::uint32_t{0x41726D79});
    Store(army,0x124,kPublicArmy);Store(army,0x38,ids.data());
    Store(army,0x40,std::int32_t{2});Store(army,0x44,std::int32_t{2});
    Store(army,0x180,std::int64_t{1234567});
    Store(regiment,0x10,kRegiment);Store(regiment,0x14,std::uint32_t{0x41725267});
    Store(regiment,0x20,static_cast<void*>(data.data()));Store(regiment,0x28,std::int32_t{2});
    Store(regiment,0x2C,std::int32_t{2});Store(regiment,0x38,std::int32_t{1000});
    Store(regiment,0x3C,std::int32_t{2000});
    for(auto offset:{std::size_t{0},std::size_t{16}}){
      Store(data,offset+8,kPersistent);Store(data,offset+12,std::int32_t{0});
    }
    Store(physical,0,std::int32_t{2000});Store(physical,4,std::int32_t{1000});
    Store(physical,8,kPersistent);Store(physical,0xC,std::int32_t{0});
    Store(physical,0x10,kRegiment);Store(physical,0x18,std::int32_t{1});
    Store(game_state,8,static_cast<std::int32_t>(kDate));
  }
}*active=nullptr;
bool InRange(const void *address,std::size_t bytes,const void *base,std::size_t extent) noexcept {
  const auto a=reinterpret_cast<std::uintptr_t>(address),b=reinterpret_cast<std::uintptr_t>(base);
  return a>=b&&a-b<=extent&&bytes<=extent-(a-b);
}
bool Read(void *context,const void *address,void *out,std::size_t bytes) noexcept {
  const auto &f=*static_cast<Fixture*>(context);
  const bool owned=InRange(address,bytes,f.army.data(),f.army.size())||
      InRange(address,bytes,f.ids.data(),sizeof f.ids)||
      InRange(address,bytes,f.regiment.data(),f.regiment.size())||
      InRange(address,bytes,f.data.data(),f.data.size())||
      InRange(address,bytes,f.physical.data(),f.physical.size())||
      InRange(address,bytes,f.game_state.data(),f.game_state.size())||
      InRange(address,bytes,&f.game_state_slot,sizeof f.game_state_slot);
  if(!owned)return false;
  std::memcpy(out,address,bytes);return true;
}
void *__fastcall Select(void *record){
  return record==active->data.data()||record==active->data.data()+16?active->physical.data():nullptr;
}
void __fastcall OriginalWriter(void *regiment,std::int64_t request){
  auto &f=*active;++f.writers;
  Need(regiment==f.regiment.data()&&request==500000,"writer ABI changed");
  const auto now=Load<std::int32_t>(f.physical,4)-5;
  Store(f.physical,4,now);Store(f.regiment,0x38,now);
}
void InvokeWriter(std::uint64_t synthetic_writer_return=0x2A958E8){
  native::InvokeActualLossWriterJournalWithCaller12004V1(
      active->regiment.data(),500000,synthetic_writer_return);
}
std::uintptr_t __fastcall OriginalResidual(void *array,std::int32_t budget,std::uint8_t flags){
  auto &f=*active;++f.originals;
  Need(array==f.army.data()+0x38&&budget==7&&flags==f.expected_flags,"residual ABI changed");
#if defined(XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004)
  const auto *frame=native::CurrentNativeInvocationContext12004();
  Need(frame&&frame->parent_kind==native::NativeInvocationParentKind12004::residual_allocator,
      "nonzero continuation entered without residual frame");
#endif
  if(f.mode==1)Store(f.army,0x10,kNativeArmy+0x01000000);
  if(f.mode==2)f.ids[0]=kRegiment+0x01000000;
  if(f.mode==3){
#if defined(XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004)
    {
      native::NativeInvocationScope12004 unknown_kind(
          static_cast<native::NativeInvocationParentKind12004>(99),GetCurrentThreadId(),nullptr);
      InvokeWriter();
    }
    Need(native::CurrentNativeInvocationContext12004()==frame,"nested unknown parent failed to restore residual");
#else
    InvokeWriter();
#endif
  }
  if(f.mode==4){
    std::thread foreign([](){
      Need(!native::CurrentNativeInvocationContext12004(),"foreign thread inherited caller TLS");
      InvokeWriter();
    });foreign.join();
  }
#if defined(XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004)
  const auto thread=static_cast<std::uint32_t>(GetCurrentThreadId());
  const auto wrong=native::CaptureResidualParentWriterContext12004(thread+1,kRegiment,0x2A958E8);
  Need(wrong&&wrong->capture_failure_flags==1&&!wrong->source_complete,
      "foreign thread identity qualified context");
#endif
  InvokeWriter(f.mode==5?0xDEADBEEF:0x2A958E8);
  if(f.mode==1)Store(f.army,0x10,kNativeArmy);
  if(f.mode==2)f.ids[0]=kRegiment;
  return 0xBEEF;
}
void InvokeResidual(Fixture &f,std::int32_t budget,std::uint8_t flags,std::uint64_t caller){
  const auto before=f.originals.load();f.expected_flags=flags;
  const auto *before_frame=native::CurrentNativeInvocationContext12004();
  const auto before_token=native::native_invocation_detail_12004::next_token.load();
  std::uintptr_t result=0;
  // Models the exact source's first TEST EDX / JE RET, which the candidate
  // leaves before the continuation hook. CK3 prologue bytes are not executed.
  if(budget==0){++f.zero_bypasses;}
  else {
#if defined(XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004)
    result=native::InvokeActualResidualNonzeroParent12004({&f,&Read},&OriginalResidual,
        f.army.data()+0x38,budget,flags,caller,GetCurrentThreadId());
#else
    (void)caller;result=OriginalResidual(f.army.data()+0x38,budget,flags);
#endif
  }
  Need(f.originals==before+(budget==0?0U:1U),"original nonzero continuation not called exactly once");
  Need(result==(budget==0?0U:0xBEEFU),"opaque nonzero return changed");
  Need(native::CurrentNativeInvocationContext12004()==before_frame,"allocator frame leaked");
  if(budget==0)Need(native::native_invocation_detail_12004::next_token.load()==before_token,
      "zero budget allocated a scope token");
}
void CheckPhysical(const game::ArmyActualLossWriterObservationV1 &e){
  Need(e.physical_capture_complete&&e.capture_failure_flags==0&&e.actual_physical_soldier_debit==5,
      "physical debit capture failed");
  Need(e.captured_data_record_count==2&&e.physical_slot_count==1&&
      e.data_aliases[0].physical_slot_index==0&&e.data_aliases[1].physical_slot_index==0,
      "physical alias was counted twice");
}
}
int main(int argc,char **argv){
  try{
    Need(argc==2,"usage: residual-parent-fixture <fresh-wire.json>");
    Fixture f;active=&f;
    native::ActualLossWriterJournalBindingsV1 binding{};binding.enabled=true;
    binding.read_context=&f;binding.read_memory=Read;binding.game_state_slot=&f.game_state_slot;
    binding.select_physical_slot=Select;
    Need(native::InitializeActualLossWriterJournalFixture12004(binding,OriginalWriter),"writer init failed");
    Need(!native::CurrentNativeInvocationContext12004(),"unexpected starting scope");
    InvokeResidual(f,0,0,0x24E2630);
    InvokeWriter(); // outside before
    InvokeResidual(f,7,0,0x24E2630); // county
    std::optional<std::uint64_t> outer_token;
    {
#if defined(XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004)
      native::SupplyParentJoinScope12004 supply(f.army.data(),kPublicArmy,kNativeArmy,kDate,
          0x2A9AB46,GetCurrentThreadId(),true);
      outer_token=native::CurrentNativeInvocationContext12004()->invocation_token;
#endif
      InvokeResidual(f,0,0,0x24E3690);
      InvokeResidual(f,7,0,0x24E3690); // explicitly synthetic within source callback range
      InvokeResidual(f,7,0,0x24E2630); // exact county caller wins over outer supply
      InvokeResidual(f,7,0,0xDEADBEEF); // unknown caller cannot borrow outer supply
      f.mode=1;InvokeResidual(f,7,0,0x24E2630); // CArmy generation changed at writer
      f.mode=2;InvokeResidual(f,7,0,0x24E2630); // source roster holds wrong ArRg generation
      f.mode=3;InvokeResidual(f,7,0,0x24E2630); // unknown kind shadows, restores residual
      f.mode=4;InvokeResidual(f,7,0,0x24E2630); // foreign thread has no caller TLS
      f.mode=5;InvokeResidual(f,7,0,0x24E2630); // wrong writer return stays incomplete
      f.mode=0;
#if defined(XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004)
      Need(native::CurrentNativeInvocationContext12004()->invocation_token==outer_token,
          "residual failed to restore supply frame");
#endif
      InvokeWriter(0x24E35FF); // outer supply context restored after residual
    }
    InvokeWriter(); // outside after
    const std::array ids{kRegiment};const auto events=native::ReadActualLossWriterObservations12004(ids);
    Need(events&&events->events.size()==14&&f.writers==14&&f.originals==9&&f.zero_bypasses==2,
        "original or event counts differ from frozen fixture cases");
    for(const auto &e:events->events)CheckPhysical(e);
    const auto &e=events->events;
    if(kEnabled){
      Need(e[1].residual_parent_context_v1&&e[1].residual_parent_context_v1->source_complete&&
          e[1].residual_parent_context_v1->request_source==game::ArmyResidualRequestSource12004::county_entry,
          "county direct residual not closed");
      Need(e[2].residual_parent_context_v1&&e[2].residual_parent_context_v1->source_complete&&
          e[2].residual_parent_context_v1->request_source==game::ArmyResidualRequestSource12004::periodic_callback&&
          e[2].residual_parent_context_v1->parent_invocation_token==outer_token,"periodic residual parent not closed");
      Need(e[3].residual_parent_context_v1&&e[3].residual_parent_context_v1->request_source==game::ArmyResidualRequestSource12004::county_entry&&
          !e[3].supply_parent_context_v1,"county borrowed outer supply cause");
      Need(e[4].residual_parent_context_v1&&!e[4].residual_parent_context_v1->source_complete&&!e[4].supply_parent_context_v1,
          "unknown direct caller borrowed outer context");
      Need(e[5].residual_parent_context_v1&&!e[5].residual_parent_context_v1->source_complete&&
          (e[5].residual_parent_context_v1->capture_failure_flags&8U)!=0,"changed CArmy accepted");
      Need(e[6].residual_parent_context_v1&&!e[6].residual_parent_context_v1->source_complete&&
          (e[6].residual_parent_context_v1->capture_failure_flags&32U)!=0,"wrong-generation full ID accepted");
      Need(!e[7].residual_parent_context_v1&&!e[7].supply_parent_context_v1&&
          e[8].residual_parent_context_v1&&e[8].residual_parent_context_v1->source_complete,"unknown frame did not shadow/restore");
      Need(!e[9].residual_parent_context_v1&&!e[9].supply_parent_context_v1&&
          e[10].residual_parent_context_v1&&e[10].residual_parent_context_v1->source_complete,"foreign thread inherited/lost parent");
      Need(e[11].residual_parent_context_v1&&!e[11].residual_parent_context_v1->source_complete&&
          e[11].residual_parent_context_v1->capture_failure_flags==2,"wrong writer return accepted");
      Need(!e[0].residual_parent_context_v1&&!e[0].supply_parent_context_v1&&
          !e[13].residual_parent_context_v1&&!e[13].supply_parent_context_v1,"outside context invented");
      if(kSupplyEnabled){
        Need(e[2].supply_parent_context_v1&&e[2].supply_parent_context_v1->receiver_identity_matches&&
            e[2].supply_parent_context_v1->invocation.invocation_token==outer_token&&
            e[2].supply_parent_context_v1->stock_at_writer_entry_raw==1234567,"FromFrame lost supply identity/stock");
        Need(!e[12].residual_parent_context_v1&&e[12].supply_parent_context_v1&&
            e[12].supply_parent_context_v1->invocation.invocation_token==outer_token,"outer supply not restored");
      }
    }else{
      Need(native::native_invocation_detail_12004::next_token.load()==0,"default OFF allocated scope token");
      for(const auto &item:e)Need(!item.residual_parent_context_v1&&!item.supply_parent_context_v1,
          "default OFF published parent context");
    }
    Need(!native::CurrentNativeInvocationContext12004(),"ending context leaked");
    std::string wire="{\"fixture_target_kind\":\"typed_local_original_callbacks\",\"native_EXE_invoked\":false,"
        "\"source_pc_kind\":\"explicit_synthetic_rva_premises\",\"source_prologue_executed\":false,"
        "\"parent_enabled\":";
    wire+=kEnabled?"true":"false";wire+=",\"supply_parent_enabled\":";wire+=kSupplyEnabled?"true":"false";
    wire+=",\"original_nonzero_calls\":9,\"zero_budget_bypasses\":2,\"original_writer_calls\":14,"
        "\"army_regiment_id\":50331649,\"outer_supply_token\":";
    if(outer_token)wire+=std::to_string(*outer_token);else wire+="null";
    wire+=",\"writers\":";game::AppendArmyActualLossWriterObservationsV1(wire,*events);wire+='}';
    Need(!std::filesystem::exists(argv[1]),"fresh wire path required");
    const auto parent=std::filesystem::path(argv[1]).parent_path();
    if(!parent.empty())std::filesystem::create_directories(parent);
    std::ofstream out(argv[1],std::ios::binary);out<<wire<<'\n';Need(static_cast<bool>(out),"wire write failed");
    std::cout<<"residual fixture passed: original-once, zero bypass, typed sources, physical aliases; not CK3\n";
    return 0;
  }catch(const std::exception &ex){std::cerr<<ex.what()<<'\n';return 1;}
}
