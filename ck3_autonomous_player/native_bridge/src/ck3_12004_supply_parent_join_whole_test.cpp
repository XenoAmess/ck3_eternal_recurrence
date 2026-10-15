#include "xar_bridge/ck3_12004_actual_supply_callback_journal.hpp"
#include "xar_bridge/ck3_12004_actual_loss_writer_journal.hpp"
#include "xar_bridge/ck3_12004_supply_parent_join_context.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <thread>

namespace {
namespace native=xar::ck3_12004;
namespace game=xar::game;
constexpr std::int32_t kRegiment=0x03000001, kPersistent=0x05000001;
constexpr std::int32_t kPublicA=0, kNativeA=0x01000000;
constexpr std::int32_t kPublicB=1, kNativeB=0x01000001;
constexpr std::uint64_t kDate=53288448;
void Check(bool value,const char *message) { if(!value)throw std::runtime_error(message); }
template<class T,std::size_t N> void Store(std::array<std::byte,N> &a,std::size_t offset,T value) {
  Check(offset+sizeof(value)<=N,"fixture store outside owned object");
  std::memcpy(a.data()+offset,&value,sizeof(value));
}
template<class T,std::size_t N> T Load(const std::array<std::byte,N> &a,std::size_t offset) {
  Check(offset+sizeof(T)<=N,"fixture load outside owned object");
  T value{};std::memcpy(&value,a.data()+offset,sizeof(value));return value;
}
struct Fixture {
  std::array<std::byte,0x190> a{},b{};
  std::array<std::byte,0x50> regiment{};
  std::array<std::byte,0x20> data{},physical{};
  std::array<std::byte,0x10> game_state{};
  void *game_state_slot=game_state.data();
  std::uint64_t date=kDate;
  std::atomic<unsigned> original_callbacks{0},original_writers{0};
  unsigned mode=0;
  bool deny_writer_stock=false;
  Fixture() {
    Store(a,0x10,kNativeA);Store(a,0x124,kPublicA);Store(a,0x180,std::int64_t{2000000});
    Store(b,0x10,kNativeB);Store(b,0x124,kPublicB);Store(b,0x180,std::int64_t{3000000});
    Store(a,0x188,kDate);Store(b,0x188,kDate);
    Store(regiment,0x10,kRegiment);Store(regiment,0x14,std::uint32_t{0x41725267});
    Store(regiment,0x20,static_cast<void*>(data.data()));Store(regiment,0x28,std::int32_t{2});Store(regiment,0x2C,std::int32_t{2});
    Store(regiment,0x38,std::int32_t{100});Store(regiment,0x3C,std::int32_t{120});
    for(auto offset:{std::size_t{0},std::size_t{16}}){Store(data,offset+8,kPersistent);Store(data,offset+12,std::int32_t{0});}
    Store(physical,0,std::int32_t{120});Store(physical,4,std::int32_t{100});Store(physical,8,kPersistent);
    Store(physical,0x10,kRegiment);Store(physical,0x18,std::int32_t{1});
    Store(game_state,8,static_cast<std::int32_t>(kDate));
  }
}*active=nullptr;
bool InRange(const void *address,std::size_t size,const void *base,std::size_t extent) noexcept {
  const auto x=reinterpret_cast<std::uintptr_t>(address),y=reinterpret_cast<std::uintptr_t>(base);
  return x>=y && x-y<=extent && size<=extent-(x-y);
}
bool Read(void *context,const void *address,void *output,std::size_t size) noexcept {
  auto &f=*static_cast<Fixture*>(context);
  const bool owned=InRange(address,size,f.a.data(),f.a.size())||InRange(address,size,f.b.data(),f.b.size())||
      InRange(address,size,f.regiment.data(),f.regiment.size())||InRange(address,size,f.data.data(),f.data.size())||
      InRange(address,size,f.physical.data(),f.physical.size())||InRange(address,size,f.game_state.data(),f.game_state.size())||
      InRange(address,size,&f.game_state_slot,sizeof(f.game_state_slot))||InRange(address,size,&f.date,sizeof(f.date));
  if(!owned)return false;
  if(f.deny_writer_stock && address==f.a.data()+0x180)return false;
  std::memcpy(output,address,size);return true;
}
void *__fastcall Select(void *data) {
  return data==active->data.data()||data==active->data.data()+16 ? active->physical.data():nullptr;
}
void __fastcall Writer(void *regiment,std::int64_t request) {
  auto &f=*active;++f.original_writers;
  Check(regiment==f.regiment.data()&&request==500000,"writer original ABI changed");
  const auto current=Load<std::int32_t>(f.physical,4)-5;
  Store(f.physical,4,current);Store(f.regiment,0x38,current);
}
void InvokeWriter(){native::XarActualLossWriterHook12004V1(active->regiment.data(),500000);}
void __fastcall Callback(void *army,const void *date) {
  auto &f=*active;++f.original_callbacks;
  Check((army==f.a.data()||army==f.b.data())&&date==&f.date,"callback original ABI changed");
  if(army==f.b.data()){
    Store(f.b,0x180,std::int64_t{1000000});InvokeWriter();return;
  }
  Store(f.a,0x180,std::int64_t{999999});InvokeWriter();
  if(f.mode==1){
    // Joinable callbacks remain on the caller thread. This foreign thread calls
    // the writer directly and must never inherit that caller's TLS context.
    std::thread foreign([](){InvokeWriter();});foreign.join();
    native::XarActualSupplyCallbackHook12004V1(f.b.data(),&f.date);
    Store(f.a,0x180,std::int64_t{500000});InvokeWriter();
  }else if(f.mode==2){
    f.deny_writer_stock=true;InvokeWriter();f.deny_writer_stock=false;
  }else if(f.mode==3){
    Store(f.a,0x10,kNativeA+0x01000000);InvokeWriter();Store(f.a,0x10,kNativeA);
  }
}
void PureScopeChecks(Fixture &f) {
#if XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004
  const auto read=[&f](const void *object,std::size_t offset,void *out,std::size_t size) noexcept {
    return Read(&f,static_cast<const std::byte*>(object)+offset,out,size);
  };
  const auto thread=static_cast<std::uint32_t>(GetCurrentThreadId());
  Check(!native::CaptureSupplyParentWriterContext12004(thread,read),"outside context was invented");
  {
    native::SupplyParentJoinScope12004 scope(f.a.data(),kPublicA,kNativeA,kDate,std::nullopt,thread,true);
    const auto parent=scope.invocation();Check(parent.has_value(),"scope token absent");
    {
      const auto *outer=native::CurrentNativeInvocationContext12004();
      native::NativeInvocationScope12004 county(
          native::NativeInvocationParentKind12004::county_entry_callback,thread,nullptr);
      Check(county.frame().parent_invocation_token==outer->invocation_token,
          "cross-kind parent token not shared");
      Check(!native::CaptureSupplyParentWriterContext12004(thread,read),
          "county context borrowed outer supply typed receiver");
      native::NativeInvocationScope12004 refill(
          native::NativeInvocationParentKind12004::regular_refill_core,thread,nullptr);
      Check(refill.frame().parent_invocation_token==county.frame().invocation_token&&
          !native::CaptureSupplyParentWriterContext12004(thread,read),
          "refill context borrowed supply receiver or separate token stack");
    }
    Check(native::CurrentNativeInvocationContext12004()->invocation_token==parent->invocation_token,
        "cross-kind scopes did not restore supply frame");
    auto wrong_thread=native::CaptureSupplyParentWriterContext12004(thread+1,read);
    Check(wrong_thread&&wrong_thread->capture_failure_flags==1&&!wrong_thread->stock_at_writer_entry_raw,
        "foreign thread identity accepted");
    try {
      native::SupplyParentJoinScope12004 invalid(f.b.data(),-1,-1,kDate,std::nullopt,thread,false);
      const auto nested=native::CaptureSupplyParentWriterContext12004(thread,read);
      Check(nested&&nested->invocation.invocation_token!=parent->invocation_token&&
          !nested->receiver_identity_matches,"partial nested scope borrowed outer identity");
      throw 1;
    } catch(int) {}
    const auto restored=native::CaptureSupplyParentWriterContext12004(thread,read);
    Check(restored&&restored->invocation.invocation_token==parent->invocation_token,
        "exception scope failed to restore outer invocation");
  }
  Check(!native::CaptureSupplyParentWriterContext12004(thread,read),"scope leaked after return");
  std::atomic<std::uint64_t> exhausted{std::numeric_limits<std::uint64_t>::max()-1};
  Check(native::supply_parent_join_detail_12004::AllocateToken(exhausted)==std::numeric_limits<std::uint64_t>::max()&&
        native::supply_parent_join_detail_12004::AllocateToken(exhausted)==0&&
        native::supply_parent_join_detail_12004::AllocateToken(exhausted)==0,"invocation token wrapped/reused");
#else
  (void)f;
  Check(native::supply_parent_join_detail_12004::next_token.load()==0,"disabled mode allocated context tokens");
#endif
}
} // namespace

int main(int argc,char **argv) {
  try {
    Check(argc==2,"usage: parent-join-fixture <fresh-output.json>");
    Fixture fixture;active=&fixture;
    native::ActualSupplyCallbackJournalBindingsV1 cb{};cb.enabled=true;cb.read_context=&fixture;cb.read_memory=Read;
    native::ActualLossWriterJournalBindingsV1 wr{};wr.enabled=true;wr.game_state_slot=&fixture.game_state_slot;
    wr.read_context=&fixture;wr.read_memory=Read;wr.select_physical_slot=Select;
    Check(native::InitializeActualSupplyCallbackJournalFixture12004(cb,Callback)&&
        native::InitializeActualLossWriterJournalFixture12004(wr,Writer),"fixture journal initialization failed");
    InvokeWriter();
    for(unsigned mode=1;mode<=3;++mode){fixture.mode=mode;native::XarActualSupplyCallbackHook12004V1(fixture.a.data(),&fixture.date);}
    InvokeWriter();
    const std::array ids{kRegiment};
    const auto writers=native::ReadActualLossWriterObservations12004(ids);
    const auto a=native::ReadActualSupplyCallbackObservations12004(kPublicA,kNativeA);
    const auto b=native::ReadActualSupplyCallbackObservations12004(kPublicB,kNativeB);
    Check(writers&&a&&b&&writers->events.size()==10&&a->events.size()==3&&b->events.size()==1,
        "natural wrapper event counts differ");
    Check(fixture.original_callbacks==4&&fixture.original_writers==10,"original not forwarded exactly once");
    for(const auto &e:writers->events)Check(e.actual_physical_soldier_debit==5,"physical alias debit differs");
#if XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004
    Check(!writers->events[0].supply_parent_context_v1&&!writers->events[2].supply_parent_context_v1&&
          !writers->events[9].supply_parent_context_v1,"outside/foreign thread borrowed parent");
    const auto outer=a->events[0].supply_parent_invocation_v1;
    const auto inner=b->events[0].supply_parent_invocation_v1;
    Check(outer&&inner&&inner->parent_invocation_token==outer->invocation_token&&
          inner->nesting_depth==2&&b->events[0].sequence<a->events[0].sequence,"nested parent correlation/order differs");
    Check(writers->events[1].supply_parent_context_v1->stock_at_writer_entry_raw==999999&&
          writers->events[3].supply_parent_context_v1->stock_at_writer_entry_raw==1000000&&
          writers->events[4].supply_parent_context_v1->stock_at_writer_entry_raw==500000&&
          writers->events[4].supply_parent_context_v1->invocation.invocation_token==outer->invocation_token,
        "stock reused callback entry/return or nested scope not restored");
    Check(!writers->events[6].supply_parent_context_v1->stock_at_writer_entry_raw&&
          (writers->events[6].supply_parent_context_v1->capture_failure_flags&4U)!=0,
        "partial stock read fabricated zero");
    Check(!writers->events[8].supply_parent_context_v1->receiver_identity_matches,
        "changed generation accepted as same receiver");
#else
    for(const auto &e:writers->events)Check(!e.supply_parent_context_v1,"default OFF published parent context");
    for(const auto &e:a->events)Check(!e.supply_parent_invocation_v1,"default OFF published invocation token");
#endif
    PureScopeChecks(fixture);
    std::string out="{\"fixture_target_kind\":\"typed_local_original_callbacks\",\"native_EXE_invoked\":false,"
        "\"original_callback_calls\":4,\"original_writer_calls\":10,\"parent_join_enabled\":";
    out+=XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004?"true":"false";
    out+=",\"army_a_id\":0,\"native_carmy_a_id\":16777216,\"army_b_id\":1,\"native_carmy_b_id\":16777217,\"callback_a\":";
    game::AppendArmyActualSupplyCallbackObservationsV1(out,*a);
    out+=",\"callback_b\":";game::AppendArmyActualSupplyCallbackObservationsV1(out,*b);
    out+=",\"writers\":";game::AppendArmyActualLossWriterObservationsV1(out,*writers);out+='}';
    Check(!std::filesystem::exists(argv[1]),"output exists");
    std::ofstream file(argv[1],std::ios::binary);file<<out<<'\n';Check(static_cast<bool>(file),"wire write failed");
    std::cout<<"parent join fixture passed; typed originals exactly once; not CK3\n";return 0;
  } catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
