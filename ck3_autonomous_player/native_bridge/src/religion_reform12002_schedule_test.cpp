#include "xar_bridge/religion_reform12002_schedule.hpp"
#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
using namespace xar::ck3_12002::religion_reform;
namespace {
std::int32_t tier = 2;
bool independent = true;
std::int32_t GetTier(void *) { return tier; }
bool GetIndependent(void *) { return independent; }
template <typename T, std::size_t N>
void Put(std::array<std::byte, N> &o, std::size_t off, T value) {
  std::memcpy(o.data()+off, &value, sizeof(value));
}
}
int main() {
  std::array<std::byte, 0x20> actor{};
  std::array<std::byte, 0x30> ai{};
  std::array<std::byte, 0x2A0> extension{};
  std::array<std::int32_t,7> periods{180,720,360,180,180,180,180};
  const std::int32_t *data = periods.data();
  std::uint8_t toggle=1;
  ScheduleBindings b{true,GetTier,GetIndependent,&data,&toggle};
  const std::uint32_t full_id=0x01000000U;
  Put(actor,0x18,full_id);Put(actor,0x1C,std::uint32_t{0x43686172U});
  Put(ai,0x18,actor.data());Put(ai,0x20,extension.data());
  Put(ai,0x28,std::uint32_t{0x41495374U});Put(ai,0x2C,std::uint8_t{1});
  Put(ai,0x14,std::uint16_t{0x40});Put(ai,0x16,std::uint8_t{1});
  auto read=[&]{return ReadReformScheduleInputs12002(b,actor.data(),full_id,ai.data());};
  assert(!BindReformScheduleImage12002(1,"wrong").enabled);
  assert(read().status==ScheduleStatus::observed);
  toggle=0;
  auto o=read();assert(!o.reformation_enabled && o.handler_cache_gates_pass);
  // A false toggle is a valid value; cache gates are a separate output.
  o=ReadReformScheduleInputs12002(b,actor.data(),full_id,nullptr);
  assert(o.status==ScheduleStatus::observed && o.ai_status==ScheduleAIStatus::not_supplied);
  Put(ai,0x18,static_cast<void *>(nullptr));assert(read().ai_status==ScheduleAIStatus::actor_mismatch);
  Put(ai,0x18,actor.data());
  independent=false;Put(extension,0x284,std::int32_t{-8});Put(extension,0x29B,std::uint8_t{1});
  o=read();assert(!o.current_independent_ruler && o.cached_independent_ruler);
  assert(o.ai_status==ScheduleAIStatus::observed && o.rare_countdown_prepare_ticks==-8 && o.rare_selected_raw==1);
  Put(ai,0x20,static_cast<void *>(nullptr));assert(read().ai_status==ScheduleAIStatus::gates_only);
  Put(ai,0x20,extension.data());periods[2]=77;assert(read().rare_period==77);
  assert(ReadReformScheduleInputs12002(b,actor.data(),0U,ai.data()).status==ScheduleStatus::actor_unavailable);
  std::cout<<"GREEN 8 cases: exact binding, valid false toggle, optional AI, actor association, cache/current drift with negative timer, no extension, current define, full generation\n";
}
