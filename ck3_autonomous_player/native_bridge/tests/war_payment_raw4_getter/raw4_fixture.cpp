// Authored seam fixture. Not built/executed by this source-only delivery.
// Future explicit build/run proves callback mechanics, never natural CK3 calls.
#include "xar_bridge/war_payment_runtime_12004.hpp"
#include <array>
#include <cstring>
#include <cstdlib>
using namespace xar::ck3_12004;
namespace {
std::array<unsigned char,0x1C8> character{};
std::array<unsigned char,0x4A8> context{};
std::uint64_t output=0;unsigned calls=0;std::uint64_t sequence=0;bool fail_output=false,mismatch_return=false;
WarPaymentJournal12004 journal;
void Check(bool v){if(!v)std::abort();}
template<class T>void Put(auto &a,std::size_t offset,T value){std::memcpy(a.data()+offset,&value,sizeof value);}
bool Read(void *,std::uintptr_t p,void *out,std::size_t n) noexcept {
  const auto within=[&](const void *base,std::size_t size){const auto b=reinterpret_cast<std::uintptr_t>(base);
    return p>=b&&p-b<=size&&n<=size-(p-b);};
  if(fail_output&&p==reinterpret_cast<std::uintptr_t>(&output))return false;
  if(!within(character.data(),character.size())&&!within(context.data(),context.size())&&!within(&output,sizeof output))return false;
  std::memcpy(out,reinterpret_cast<void *>(p),n);return true;
}
ArmyNaturalPhaseEvent12004 Event(void *) noexcept {return {1,++sequence,2};}
WarPaymentSession12004 Session(void *) noexcept {WarPaymentSession12004 s{};
  s.pid=3;s.process_create_time_100ns=4;s.connection_generation=5;s.loaded_game_epoch=6;
  s.player_character_full_id=7;return s;}
std::uintptr_t __fastcall Original(void *,void *out,std::int32_t selector) {
  Check(out==&output);++calls;std::uint64_t v=selector==4?9:123;std::memcpy(out,&v,sizeof v);return reinterpret_cast<std::uintptr_t>(out)+(mismatch_return?8:0);
}
}
int main() {
  static_assert(kWarPaymentHookCount12004==6);
  Check(WarPaymentHookDescriptions12004()[5].rva==0x28B9490);
  Check(WarPaymentHookDescriptions12004()[5].prefix_bytes==14);
  Put(character,0x18,std::uint32_t{7});Put(character,0x1C,std::uint32_t{0x43686172});
  Put(character,0x1B0,std::uintptr_t{1});Put(character,0x1C0,reinterpret_cast<std::uintptr_t>(context.data()));
  Put(context,0x4A0,std::uint64_t{9});
  WarPaymentBindings12004 b{};b.exact_build_and_prefixes_verified=true;b.read=Read;b.next_event=Event;
  b.session=Session;b.journal=&journal;b.raw4_getter_capture_enabled=true;b.raw4_module_base=0x140000000;
  (void)journal.SetEnabled(true);
  const auto invoke=[&](int selector){const auto before=calls;const auto r=InvokeWarPaymentRaw4Getter12004(b,Original,
    character.data(),&output,selector,0x140001234);Check(calls==before+1&&r==reinterpret_cast<std::uintptr_t>(&output)+(mismatch_return?8:0));};
  invoke(4);auto j=journal.Copy();Check(j.raw4.records.size()==1&&j.raw4.records[0].out64_bits==9);
  invoke(3);Check(journal.Copy().raw4.records.size()==1);
  b.raw4_getter_capture_enabled=false;invoke(4);Check(journal.Copy().raw4.records.size()==1);
  b.raw4_getter_capture_enabled=true;fail_output=true;invoke(4);j=journal.Copy();
  Check(j.raw4.records.size()==2&&!j.raw4.records[1].out64_bits&&j.raw4.records[1].output_failed_reads==1);
  fail_output=false;mismatch_return=true;invoke(4);j=journal.Copy();
  Check(j.raw4.records.size()==3&&j.raw4.records[2].raw_return_bits==reinterpret_cast<std::uintptr_t>(&output)+8);
  (void)journal.SetEnabled(false);(void)journal.SetEnabled(true);
  Check(journal.Copy().raw4.records.empty());
}
