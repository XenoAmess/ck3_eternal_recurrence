// Actual Actor executor negative source fixture. No CK3 process, code, injection
// or memory access. A forbidden RAM getter would run in the unfixed prefix.
#include "xar_bridge/ck3_1210_personal_gold_frame_v1.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#include <array>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <windows.h>
using namespace xar::ck3_1210;
namespace {
unsigned getter_calls=0;
void *ForbiddenGetter(void *){++getter_calls;return nullptr;}
template<std::size_t N,class T>void Put(std::array<std::byte,N> &a,std::size_t offset,T value){
  if(offset>N || sizeof(T)>N-offset){std::abort();}
  std::memcpy(a.data()+offset,&value,sizeof(value));
}
}
int main(){
  std::array<std::byte,0xA8> state{};std::array<std::byte,0x21> jomini{};std::array<std::byte,0x200> players{};
  void *state_pointer=state.data(),*jomini_pointer=jomini.data(),*storage_pointer=nullptr;
  Put(state,8,std::int32_t{123456});Put(state,0x70,std::int32_t{3});
  Put(jomini,0x18,players.data());jomini[0x20]=std::byte{1};Put(players,0x1F0,std::int32_t{7});
  CoreBindings forged{true,&state_pointer,&jomini_pointer,&storage_pointer,&ForbiddenGetter};
  auto game=xar::game::CreateCk3_1210AdapterFromBindings(forged);
  if(!game->supports(kActorResourceLeafCapabilityV2)){std::cerr<<"NOT_RUN: v2 producer feature required\n";return 1;}
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};PersonalGoldMailboxContextV1 q{};
  q.kind=ActorObservationKindV1::resource_leaf;q.game=game.get();q.bindings={true,forged};q.mailbox=&mailbox;q.ticket.sequence=9;
  q.image_base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};stamp.thread_id=GetCurrentThreadId();stamp.pump_epoch=2;
  stamp.tls_initialized=1;stamp.tls_main_thread_marker=1;stamp.tls_context=1;stamp.paused=true;stamp.date_raw=123456;
  stamp.game_state=reinterpret_cast<std::uintptr_t>(state_pointer);stamp.jomini_state=reinterpret_cast<std::uintptr_t>(jomini_pointer);
  mailbox.state.store(xar::ck3_11906::MainThreadQueryMailboxStateV1::executing);mailbox.iat_hook_installed.store(true);
  mailbox.owner_thread_id.store(stamp.thread_id);mailbox.paused_owner_verified_pump_epochs.store(2);mailbox.published_sequence.store(9);
  mailbox.executor.store(&ExecutePersonalGoldMailboxV1);mailbox.executor_context=&q;
  if(!ExecutePersonalGoldMailboxV1(&q,stamp) || getter_calls!=0 || q.resource_leaf.prestige_raw || q.resource_leaf.piety_raw ||
      q.resource_leaf.unavailable_reason!="resource_targets_before_unavailable"){
    std::cerr<<"FAIL foreign getter reached before resource target admission\n";return 1;
  }
  std::cout<<"PASS actual executor resource precore denial; forbidden getter calls=0; no Game\n";
}
