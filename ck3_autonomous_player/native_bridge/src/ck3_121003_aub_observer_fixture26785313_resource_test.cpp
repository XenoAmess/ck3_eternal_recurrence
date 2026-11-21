#include "ck3_121003_aub_observer_fixture26785313_wire_v1.cpp"
#include "ck3_121003_aub_observer_fixture26785313_v1.cpp"
#include <iostream>
#include <stdexcept>
using namespace xar::ck3_121003::build26785313;
unsigned destroy_calls=0,exit_calls=0;bool fail_destroy=false,fail_exit=false;
void Destroy(xar::ck3_12002::ConsoleFixtureNativeString*s){++destroy_calls;if(fail_destroy)RaiseException(0xE0004114,0,0,nullptr);s->size=0;s->capacity=15;s->storage[0]=0;}
void Exit(xar::ck3_12002::ConsoleFixtureRandomScope*s){++exit_calls;if(fail_exit)RaiseException(0xE0004115,0,0,nullptr);if(s->restore_slot)*s->previous_slot_target=s->previous_value;}
void Check(bool v){if(!v)throw std::runtime_error("fixed fixture resource lifetime invariant");}
int main(){try{
 for(unsigned scenario=0;scenario<3;++scenario){Resource r;std::array<std::byte,32> owner{};const auto base=reinterpret_cast<std::uintptr_t>(owner.data())-0x5D55998;
  std::uint32_t tid=42;std::memcpy(owner.data()+16,&tid,4);int prior=1;void*wrapper=&r.scope;
  r.enter_attempted=r.enter_completed=r.wrapper_installed=r.string_attempted=true;r.scope.owner_state=owner.data();r.scope.owns_owner=0;r.scope.previous_slot_target=&wrapper;r.scope.previous_value=&prior;r.scope.restore_slot=1;r.prior_wrapper=&prior;r.prior_owner_tid=tid;
  xar::ck3_12002::ConsoleFixtureBindings b;b.random_wrapper_slot=&wrapper;b.destroy_string=&Destroy;b.exit_random_scope=&Exit;
  destroy_calls=exit_calls=0;fail_destroy=scenario==1;fail_exit=scenario==2;
  const bool first=Cleanup(b,r,base);Check(first==(scenario==0));Check(destroy_calls==1&&exit_calls==1);
  const bool second=Cleanup(b,r,base);Check(second==first&&destroy_calls==1&&exit_calls==1);
  if(scenario!=2)Check(wrapper==&prior);else Check(wrapper==&r.scope);
  wrapper=&prior; // Test-owned local pointer only; no Game/global restoration.
 }
 AubObserverFixtureSession267V1 session;AubObserverFixtureContext267V1 q;q.session=&session;xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
 Check(!ExecuteAubObserverFixtureOnOwner267V1(nullptr,stamp));Check(ExecuteAubObserverFixtureOnOwner267V1(&q,stamp));Check(!q.result.effect_attempted&&!q.result.native_returned&&!q.result.claim_sequence);
 std::cout<<"PASS local-only resource symmetry, SEH fail retained/no cleanup replay and default-OFF no authority\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
