#include "xar_bridge/clergy_position_check_31bd1a0_12004.hpp"

#include <cstring>
#include <map>
#include <stdexcept>
#include <utility>
#include <vector>

namespace xar::ck3_12004::religion::clergy {
namespace {
void Require31BD1A0(bool value, const char *reason) {
  if (!value) throw std::runtime_error(reason);
}
struct Fixture {
  std::map<std::uintptr_t, std::byte> memory;
  std::vector<std::uintptr_t> reads;
  ClergyPosition31BD1A0Arguments12004 args{
      0x140000000ULL,
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
      0x10000,0xA5000002U,0x20028,0,
      0x140000000ULL+kClergyPositionCheckLiteralRva12004,0};
  template <typename T> void Put(std::uintptr_t address, T value) {
    const auto *bytes = reinterpret_cast<const std::byte *>(&value);
    for (std::size_t index=0;index<sizeof(T);++index) memory[address+index]=bytes[index];
  }
  Fixture() {
    Put<std::uint8_t>(args.position_identity+0x2378,0);
    Put<std::uint32_t>(args.position_identity+0x21C4,0);
    Put<std::uint32_t>(args.position_identity+0x2338,0);
  }
  static bool Read(void *opaque,const void *pointer,void *out,std::size_t size) noexcept {
    auto &fixture=*static_cast<Fixture *>(opaque);
    const auto address=reinterpret_cast<std::uintptr_t>(pointer);
    fixture.reads.push_back(address);
    for (std::size_t index=0;index<size;++index) {
      const auto it=fixture.memory.find(address+index);
      if (it==fixture.memory.end()) return false;
      static_cast<std::byte *>(out)[index]=it->second;
    }
    return true;
  }
  ClergyPosition31BD1A0RawAL12004 Run() {
    return ReadClergyPosition31BD1A0RawAL12004(this,Read,args);
  }
  void Dynamic(std::uint32_t clock,std::uint32_t task) {
    args.r9_raw_u32=1;
    Put<std::uint8_t>(args.position_identity+0x2378,2);
    Put<std::uint32_t>(args.position_identity+0x2338,1);
    Put<std::uintptr_t>(args.module_base+kClergyPositionCheckClockSlotRva12004,0x30000);
    Put<std::uint32_t>(0x30008,clock);
    Put<std::uint32_t>(args.task28_identity,task);
  }
};
} // namespace

// No main, no native entry or old qualification. Parent26/02 routes these new
// cases to the sole connected-clergy acceptance owner10 when the join is ready.
int RunClergyPosition31BD1A0NewCases12004() {
  int count=0;
  {
    Fixture fixture; fixture.Put<std::uint8_t>(fixture.args.position_identity+0x2378,200);
    const auto out=fixture.Run();
    Require31BD1A0(out.available && out.raw_al==0 && out.initial_child.raw_al==200 &&
        !out.position2338_raw_u32 && fixture.reads.size()==1 &&
        out.initial_child.rcx_raw_u32==0xA5000002U,
        "raw nonzero initial AL rejects r9zero without date/mode demand or fullID masking");
    ++count;
  }
  {
    Fixture fixture; const auto out=fixture.Run();
    Require31BD1A0(out.available && out.raw_al==1 && out.initial_child.raw_al==0 &&
        !out.clock_identity && fixture.reads==std::vector<std::uintptr_t>{
          fixture.args.position_identity+0x2378,fixture.args.position_identity+0x21C4,
          fixture.args.position_identity+0x2338},
        "zero predicate then zero mode returns one through literal08 operands");
    ++count;
  }
  {
    Fixture fixture; fixture.args.r9_raw_u32=1;
    fixture.Put<std::uint8_t>(fixture.args.position_identity+0x2378,2);
    const auto out=fixture.Run();
    Require31BD1A0(out.available && out.raw_al==1 && out.initial_child.raw_al==2 &&
        fixture.reads.size()==2,"r9nonzero reaches mode guard even for noncanonical initial rawAL");
    ++count;
  }
  {
    Fixture fixture; fixture.memory.erase(fixture.args.position_identity+0x2378);
    const auto out=fixture.Run();
    Require31BD1A0(!out.available && !out.raw_al && !out.position2338_raw_u32 &&
        out.next_source_entry=="0x31BDDA0","unread initial literal stays unavailable");
    ++count;
  }
  {
    Fixture fixture; fixture.Put<std::uint32_t>(fixture.args.position_identity+0x21C4,1);
    const auto out=fixture.Run();
    Require31BD1A0(!out.available && !out.raw_al && out.initial_child.condition_child_required &&
        out.next_source_entry=="0x372DF10" && !out.position2338_raw_u32,
        "initial dynamic condition requires its exact next child");
    ++count;
  }
  {
    Fixture fixture; fixture.memory.erase(fixture.args.position_identity+0x2338);
    const auto out=fixture.Run();
    Require31BD1A0(!out.available && !out.raw_al &&
        out.unavailable_reason=="position2338_dword_unavailable","missing mode is not zero");
    ++count;
  }
  for (const auto operands : {std::pair<std::uint32_t,std::uint32_t>{0x80000000U,0x7FFFFFE8U},
                              {0U,25U},{0U,1U}}) {
    Fixture fixture; fixture.Dynamic(operands.first,operands.second);
    const auto out=fixture.Run();
    const auto expected=operands.first==0x80000000U ? 1 : (operands.second==25U ? -1 : 0);
    Require31BD1A0(!out.available && !out.raw_al && out.dynamic_numeric_required &&
        out.elapsed_signed_div24==expected &&
        out.clock_date_raw_u32==operands.first && out.task28_raw_u32==operands.second &&
        out.unavailable_reason=="dynamic_a0f0b0_named_context_cleanup_source_pending",
        "wrapped signed date division is preserved while dynamic numeric remains unknown");
    ++count;
  }
  {
    Fixture fixture; fixture.args.executable_sha256="other-image";
    const auto out=fixture.Run();
    Require31BD1A0(!out.available && !out.raw_al && fixture.reads.empty(),
        "wrong image cannot read current literal inputs");
    ++count;
  }
  {
    Fixture fixture; fixture.args.stack_argument5+=1;
    const auto out=fixture.Run();
    Require31BD1A0(!out.available && !out.raw_al && fixture.reads.empty(),
        "different CanReassign reason literal is not admitted as this caller");
    ++count;
  }
  {
    Fixture fixture; fixture.args.stack_argument6=0x40000;
    const auto out=fixture.Run();
    Require31BD1A0(!out.available && !out.raw_al && fixture.reads.empty(),
        "nonnull tooltip is outside the current caller effects closure");
    ++count;
  }
  {
    Fixture fixture;
    ClergyPosition31BD1A0ReadContext12004 context{
        &fixture,Fixture::Read,fixture.args.module_base,fixture.args.executable_sha256};
    std::uint8_t raw=77;
    const bool available=ReadClergyPosition31BD1A0Callback12004(
        &context,fixture.args.position_identity,fixture.args.owner_full_id_raw_u32,
        fixture.args.task28_identity,fixture.args.r9_raw_u32,fixture.args.stack_argument5,raw);
    Require31BD1A0(available && raw==1,"parent26 callback joins computed raw AL");
    fixture.Dynamic(24,0); raw=77;
    const bool unavailable=ReadClergyPosition31BD1A0Callback12004(
        &context,fixture.args.position_identity,fixture.args.owner_full_id_raw_u32,
        fixture.args.task28_identity,fixture.args.r9_raw_u32,fixture.args.stack_argument5,raw);
    Require31BD1A0(!unavailable && raw==77,
        "parent callback leaves output untouched for dynamic unknown instead of nativefalse");
    ++count;
  }
  return count;
}

} // namespace xar::ck3_12004::religion::clergy
