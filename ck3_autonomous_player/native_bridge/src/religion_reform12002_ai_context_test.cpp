#include "xar_bridge/religion_reform12002_ai_context.hpp"
#include "xar_bridge/religion_reform12002_schedule.hpp"
#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
using namespace xar::ck3_12002::religion_reform;
namespace {
template <typename T,std::size_t N>
void Put(std::array<std::byte,N> &o,std::size_t offset,T value) {
  std::memcpy(o.data()+offset,&value,sizeof(value));
}
std::int32_t HighestTier(void *) { return 2; }
bool Independent(void *) { return true; }
}
int main() {
  std::array<std::byte,0xA8> root{};
  std::array<std::byte,0x2D70> state{};
  std::array<std::byte,0x30> holder{},ordinary{},special{},default_ai{},other_ai{};
  std::array<std::byte,0x20> actor{},other_actor{};
  std::array<std::byte,0x2A0> extension{};
  std::array<const void *,3> table{};
  const void *root_slot=root.data();
  AIContextBindings b{true,&root_slot};
  const std::uint32_t actor_id=0x02000005U;
  Put(actor,0x18,actor_id);Put(actor,0x1C,std::uint32_t{0x43686172});
  Put(other_actor,0x18,std::uint32_t{0x01000005});Put(other_actor,0x1C,std::uint32_t{0x43686172});
  Put(root,0xA0,state.data());Put(state,0x2D48+0x20,holder.data());
  Put(holder,0x08,default_ai.data());Put(default_ai,0x28,std::uint32_t{0x41495374});
  auto read=[&]{return ReadActorReformAIContext12002(b,actor.data(),actor_id);};
  assert(!BindReformAIContextImage12002(1,"wrong").enabled);
  assert(ReadActorReformAIContext12002({},actor.data(),actor_id).status==AIContextStatus::bindings_unavailable);
  // Empty actual table remains legal even though default +8 has the AISt tag.
  auto c=read();assert(c.status==AIContextStatus::observed_no_ai && c.controllers.empty());
  const auto none_json=SerializeActorReformAIContext12002(c);
  assert(none_json.find("\"available\":true")!=std::string::npos);
  Put(other_ai,0x18,other_actor.data());Put(other_ai,0x28,std::uint32_t{0x41495374});
  table[0]=other_ai.data();Put(holder,0x10,table.data());Put(holder,0x1C,std::int32_t{1});
  assert(read().status==AIContextStatus::observed_no_ai); // same low24, different generation
  Put(ordinary,0x18,actor.data());Put(ordinary,0x28,std::uint32_t{0x41495374});
  Put(ordinary,0x2C,std::uint8_t{1});Put(ordinary,0x14,std::uint16_t{0x40});
  Put(ordinary,0x16,std::uint8_t{1});Put(ordinary,0x20,extension.data());
  Put(extension,0x284,std::int32_t{-4});table[0]=ordinary.data();
  c=read();assert(c.status==AIContextStatus::observed_controllers && c.controllers.size()==1);
  assert(c.controllers[0].actual_ai==ordinary.data() && c.controllers[0].kind==AIControllerKind::ordinary);
  std::array<std::int32_t,7> ticks{180,720,360,180,180,180,180};
  const std::int32_t *tick_data=ticks.data();std::uint8_t toggle=1;
  ScheduleBindings sb{true,HighestTier,Independent,&tick_data,&toggle};
  auto schedule=ReadReformScheduleInputs12002(sb,actor.data(),actor_id,c.controllers[0].actual_ai);
  assert(schedule.ai_status==ScheduleAIStatus::observed && schedule.rare_countdown_prepare_ticks==-4 && schedule.handler_cache_gates_pass);
  Put(special,0x18,actor.data());Put(special,0x28,std::uint32_t{0x41495374});
  Put(special,0x2C,std::uint8_t{1});Put(special,0x2E,std::uint8_t{1});
  table[0]=special.data();c=read();assert(c.controllers.size()==1 && c.controllers[0].kind==AIControllerKind::player_special);
  schedule=ReadReformScheduleInputs12002(sb,actor.data(),actor_id,c.controllers[0].actual_ai);
  assert(schedule.ai_status==ScheduleAIStatus::gates_only && schedule.ai_special==1 && !schedule.handler_cache_gates_pass);
  // Both current actual records are returned; neither receives guessed priority.
  table[0]=ordinary.data();table[1]=special.data();Put(holder,0x1C,std::int32_t{2});
  Put(ordinary,0x2C,std::uint8_t{0});const auto before_holder=holder;
  c=read();assert(c.controllers.size()==2 && c.controllers[0].active_raw==0 && holder==before_holder);
  const auto json=SerializeActorReformAIContext12002(c);
  assert(json.find("actual_ai")==std::string::npos && json.find("pointer")==std::string::npos && json.find("0x")==std::string::npos);
  assert(ReadActorReformAIContext12002(b,actor.data(),0x01000005U).status==AIContextStatus::actor_unavailable);
  Put(actor,0x18,std::uint32_t{0});
  assert(ReadActorReformAIContext12002(b,actor.data(),0).controllers.size()==2);
  root_slot=nullptr;assert(ReadActorReformAIContext12002(b,actor.data(),0).status==AIContextStatus::container_unavailable);
  std::cout<<"GREEN 9 cases: binding, legal default-only no AI, full-generation association, ordinary schedule input, player-special schedule input, multiple/inactive contexts with readonly holder and address-free serialization, stale actor generation, legal zero ID, unavailable container\n";
  std::cout<<"wire:"<<json<<'\n';
}
