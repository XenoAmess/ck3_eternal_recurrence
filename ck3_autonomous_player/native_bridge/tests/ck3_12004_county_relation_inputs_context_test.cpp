#include "xar_bridge/ck3_12004_county_relation_inputs_context.hpp"
#include "xar_bridge/army_county_relation_inputs_v1_serializer.hpp"
#include "xar_bridge/army_position_relation_28bc250_12004.hpp"
#include <array>
#include <cstdio>
#include <cstring>
#include <map>
#include <stdexcept>
#include <string>
#if defined(_WIN32) && defined(_M_X64)
#include <windows.h>
#endif

// Authored offline fixture, NOTRUN. Its fabricated addresses and answers do
// not provide a native-game observation or qualification.
namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kBase=0x10000000, kReceiver=0x200000, kActor=0x300000;
constexpr std::uintptr_t kMap=0x400000, kRows=0x500000, kRelation=0x600000;
constexpr std::uintptr_t kManager=0x700000, kTable=0x800000, kWar=0x900000;
constexpr std::uintptr_t kFallback=0xA00000, kCounty=0xB00000;
struct Cell { std::array<std::byte,8> data{}; std::size_t bytes=0; };
struct Scene {
  std::map<std::uintptr_t,Cell> cells;
  std::size_t reads=0,native_calls=0;
  bool native_answer=false, internal_call=false, mutate_id=false;
  ArmyRegularCoreReadonlyAccess12004 access{};
};
Scene *g_scene=nullptr;
template<class T> void Put(Scene &scene,std::uintptr_t at,T value) {
  Cell cell{};cell.bytes=sizeof(value);
  static_assert(sizeof(value)<=8);
  std::memcpy(cell.data.data(),&value,sizeof(value));scene.cells[at]=cell;
}
bool Read(void *opaque,std::uintptr_t at,void *out,std::size_t bytes) noexcept {
  auto &scene=*static_cast<Scene *>(opaque);++scene.reads;
  const auto found=scene.cells.find(at);
  if(found==scene.cells.end() || found->second.bytes!=bytes)return false;
  std::memcpy(out,found->second.data.data(),bytes);return true;
}
void Check(bool ok,const char *why){if(!ok)throw std::runtime_error(why);}
void Setup(Scene &scene,std::uint32_t receiver_id=0x81000042,
    std::uint32_t actor_id=0x82000042,std::int32_t war_id=-1) {
  scene=Scene{};
  scene.access={kBase,&scene,&Read,256};
  Put(scene,kReceiver+0x18,receiver_id);Put(scene,kActor+0x18,actor_id);
  Put(scene,kReceiver+0x1B0,kMap);
  Put(scene,kMap+0x20,kRows);Put(scene,kMap+0x2C,std::int32_t{1});
  Put(scene,kRows,actor_id);Put(scene,kRows+8,kRelation);
  Put(scene,kRelation+0x20,war_id);
  Put(scene,kBase+0x5D1DE58,kManager);
  Put(scene,kManager+0x2C,std::uint32_t{2});Put(scene,kManager+0x20,kTable);
  Put(scene,kTable+16+8,kWar);Put(scene,kWar+8,std::uint32_t{0x12000001});
  Put(scene,kWar+0x358,std::uint8_t{0});
  Put(scene,kBase+0x5D1DE40,kFallback);Put(scene,kFallback+0x358,std::uint8_t{5});
  g_scene=&scene;
}
#if defined(_MSC_VER)
bool __fastcall Relation(void *,void *,std::uintptr_t,std::uintptr_t) {
#else
bool Relation(void *,void *,std::uintptr_t,std::uintptr_t) {
#endif
  ++g_scene->native_calls;
  if(g_scene->mutate_id)Put(*g_scene,kReceiver+0x18,std::uint32_t{0x83000042});
  return g_scene->native_answer;
}
#if defined(_MSC_VER)
bool __fastcall P(void *actor,void *,std::uintptr_t,std::uintptr_t opaque_r9) {
#else
bool P(void *actor,void *,std::uintptr_t,std::uintptr_t opaque_r9) {
#endif
  if(g_scene->internal_call)
    (void)InvokeCountyRelationInputs12004(&Relation,reinterpret_cast<void *>(kReceiver),
        actor,0,opaque_r9,std::nullopt,7,g_scene->access);
  return InvokeCountyRelationInputs12004(&Relation,reinterpret_cast<void *>(kReceiver),
      actor,0,opaque_r9,0x12345,7,g_scene->access);
}
xar::game::ArmyCountyPredicateTraceV1 Capture(Scene &) {
  CountyPredicateTraceScope12004 scope(true,1,7,reinterpret_cast<void *>(kActor),
      reinterpret_cast<void *>(kCounty),reinterpret_cast<void *>(kCounty));
  const bool returned=InvokeCountyPredicateTrace12004(&P,reinterpret_cast<void *>(kActor),
      reinterpret_cast<void *>(kCounty),0x24E22B3,7,0,0xCAFE);
  return scope.Finish(true,returned,true,7,true,false,false);
}
std::string Wire(const xar::game::ArmyCountyRelationInputsV1 &value) {
  std::string wire;
  const auto number=[](auto v){return std::to_string(v);};
  const auto quote=[](std::string &out,const std::string &s){
    out+='"';for(const char ch:s){if(ch=='"'||ch=='\\')out+='\\';out+=ch;}out+='"';
  };
  xar::game::AppendCountyRelationInputsV1(wire,value,number,quote);return wire;
}
void SameCompleteId() {
  Scene s;Setup(s,0x81000042,0x81000042);
  const auto trace=Capture(s);const auto &r=*trace.stages[0].relation_inputs_v1;
  Check(trace.available && r.available && r.returned==false && r.call_count==1,
      "same complete ID preserves actual false in the known P stage");
  Check(!r.sampled_relation_available && !r.sampled_relation_identity &&
      s.native_calls==1 && s.reads==4,"same-ID branch must not read pair state");
  const auto wire=Wire(r);
  Check(wire.find("\"status\":\"available\"")!=std::string::npos &&
      wire.find("\"receiver_full_id\":2164260930")!=std::string::npos &&
      wire.find("\"returned\":false")!=std::string::npos &&
      wire.find("\"auxiliary_identity\":null")!=std::string::npos &&
      wire.find("\"unknown_or_inputs\":true")!=std::string::npos,
      "actual serializer preserves UInt32 IDs/AL and unknown OR inputs");
}
void DifferentGenerationAndNoWar() {
  Scene s;Setup(s);s.internal_call=true;
  const auto trace=Capture(s);const auto &r=*trace.stages[0].relation_inputs_v1;
  Check(r.available && r.receiver_full_id!=r.actor_full_id && r.returned==false &&
      r.sampled_relation_available && r.sampled_relation_full_war_id==-1 &&
      r.sampled_direct_war_gate==false && !r.sampled_selected_war_identity &&
      s.native_calls==2 && r.call_count==1,"native internal caller is not the P tail call");
  Check(Wire(r).find("\"sampled_relation_full_war_id\":-1")!=std::string::npos,
      "serializer must preserve signed no-war sentinel");
}
void RawWarByteAndFallback() {
  Scene s;Setup(s,0x81000042,0x82000042,0x12000001);
  auto sampled=ReadCountyRelationInputs12004(s.access,kReceiver,kActor,kWar);
  Check(sampled.sampled_relation_available && sampled.sampled_selected_war_identity==kWar &&
      sampled.sampled_selected_war_used_fallback==false &&
      sampled.sampled_selected_war_byte_358_u8==0 && sampled.sampled_direct_war_matches_aux==true &&
      sampled.sampled_direct_war_gate==true,"full-generation matching War selects row and raw byte");
  Put(s,kWar+8,std::uint32_t{0x13000001});
  sampled=ReadCountyRelationInputs12004(s.access,kReceiver,kActor,0);
  Check(sampled.sampled_relation_available && sampled.sampled_selected_war_identity==kFallback &&
      sampled.sampled_selected_war_used_fallback==true &&
      sampled.sampled_selected_war_byte_358_u8==5 && sampled.sampled_direct_war_gate==false,
      "same index with another generation uses fallback; raw nonzero byte is retained");
  Check(Wire(sampled).find("\"sampled_selected_war_byte_358_u8\":5")!=std::string::npos,
      "uint8 serializer must emit a number, not a character");
}
void PartialSamplingAndChangedId() {
  Scene s;Setup(s);s.cells.erase(kRelation+0x20);
  auto trace=Capture(s);auto r=*trace.stages[0].relation_inputs_v1;
  Check(r.available && r.returned==false && !r.sampled_relation_available &&
      r.sampled_relation_identity==kRelation && !r.sampled_relation_full_war_id &&
      !r.sampled_relation_unavailable_reason.empty(),
      "pair read failure stays unknown without discarding actual entry/return");
  Setup(s);s.mutate_id=true;trace=Capture(s);r=*trace.stages[0].relation_inputs_v1;
  Check(!r.available && r.returned==false && r.identity_before_after_match==false,
      "changed complete ID cannot become ready actual relation evidence");
  Check(Wire(r).find("\"status\":\"unavailable\"")!=std::string::npos,
      "serializer must expose rejected actual identity sample");
}
#if defined(_WIN32) && defined(_M_X64)
void OwnedTrampolineUnwind() {
  struct OwnedUnwind {
    std::uint8_t *memory = nullptr;
    RUNTIME_FUNCTION entry{};
    bool registered = false;
    ~OwnedUnwind() {
      if(registered)(void)RtlDeleteFunctionTable(&entry);
      if(memory)(void)VirtualFree(memory,0,MEM_RELEASE);
    }
  } owned;
  owned.memory=static_cast<std::uint8_t *>(VirtualAlloc(nullptr,48,
      MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
  Check(owned.memory!=nullptr,"allocate fixture-owned unwind bytes");
  // Same held15B prologue and16B xdata as the candidate installer. This
  // owned buffer is never executed and never reads or calls the game EXE.
  constexpr std::array<std::uint8_t,15> prefix{
      0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x74,
      0x24,0x10,0x57,0x48,0x83,0xEC,0x20};
  constexpr std::array<std::uint8_t,13> jump{
      0x49,0xBB,0,0,0,0,0,0,0,0,0x41,0xFF,0xE3};
  constexpr std::array<std::uint8_t,16> unwind{
      0x01,0x0F,0x06,0x00,0x0F,0x64,0x07,0x00,
      0x0F,0x34,0x06,0x00,0x0F,0x32,0x0B,0x70};
  std::memcpy(owned.memory,prefix.data(),prefix.size());
  std::memcpy(owned.memory+15,jump.data(),jump.size());
  std::memcpy(owned.memory+32,unwind.data(),unwind.size());
  owned.entry.BeginAddress=0;owned.entry.EndAddress=28;owned.entry.UnwindData=32;
  const auto image=reinterpret_cast<DWORD64>(owned.memory);
  owned.registered=RtlAddFunctionTable(&owned.entry,1,image)!=FALSE;
  Check(owned.registered,"register fixture-owned trampoline function table");
  const auto exercise=[&](std::uint32_t pc_offset,bool after_push,bool after_alloc) {
    alignas(16) std::array<DWORD64,32> stack{};
    const auto current_full_rsp=reinterpret_cast<DWORD64>(stack.data()+8);
    const auto entry_rsp=current_full_rsp+40;
    constexpr DWORD64 saved_rbx=0x1111222233334444ULL;
    constexpr DWORD64 saved_rsi=0x5555666677778888ULL;
    constexpr DWORD64 saved_rdi=0x9999AAAABBBBCCCCULL;
    constexpr DWORD64 caller_return=0x123456789ABCULL;
    // Full prologue: return at+40, savedRBX+48/RSI+56/RDI+32.
    stack[8+4]=saved_rdi;stack[8+5]=caller_return;
    stack[8+6]=saved_rbx;stack[8+7]=saved_rsi;
    CONTEXT context{};context.ContextFlags=CONTEXT_CONTROL|CONTEXT_INTEGER;
    context.Rsp=after_alloc?current_full_rsp:(after_push?entry_rsp-8:entry_rsp);
    context.Rip=image+pc_offset;
    context.Rbx=after_alloc?0:saved_rbx;
    context.Rsi=after_alloc?0:saved_rsi;
    context.Rdi=after_push?0:saved_rdi;
    DWORD64 found_image=0;
    const auto found=RtlLookupFunctionEntry(context.Rip,&found_image,nullptr);
    Check(found==&owned.entry && found_image==image,
        "dynamic lookup must bind the owned range and xdata");
    PVOID handler_data=nullptr;DWORD64 establisher=0;
    (void)RtlVirtualUnwind(UNW_FLAG_NHANDLER,image,context.Rip,found,
        &context,&handler_data,&establisher,nullptr);
    if(context.Rip!=caller_return || context.Rsp!=entry_rsp+8 ||
        context.Rbx!=saved_rbx || context.Rsi!=saved_rsi || context.Rdi!=saved_rdi)
      std::fprintf(stderr,
          "owned_unwind pc_offset=%u RIP=%llx expectedRIP=%llx RSP=%llx expectedRSP=%llx "
          "RBX=%llx RSI=%llx RDI=%llx\n",static_cast<unsigned>(pc_offset),
          static_cast<unsigned long long>(context.Rip),
          static_cast<unsigned long long>(caller_return),
          static_cast<unsigned long long>(context.Rsp),
          static_cast<unsigned long long>(entry_rsp+8),
          static_cast<unsigned long long>(context.Rbx),
          static_cast<unsigned long long>(context.Rsi),static_cast<unsigned long long>(context.Rdi));
    Check(context.Rip==caller_return && context.Rsp==entry_rsp+8,
        "virtual unwind must recover caller return and caller RSP");
    Check(context.Rbx==saved_rbx && context.Rsi==saved_rsi && context.Rdi==saved_rdi,
        "virtual unwind must recover RBX/RSI/RDI at each prologue boundary");
  };
  exercise(0,false,false);   // Entry, before either save or push.
  exercise(10,false,false);  // Both stores complete, push not executed.
  exercise(11,true,false);  // Push complete, allocation not executed.
  exercise(15,true,true);   // Full prologue, MOV R11 immediate instruction.
  exercise(25,true,true);   // Actual JMP R11 instruction, ModRM mod3.
}
#endif
}
int main(){
  const char *active_case="same_complete_id";
  try {
  SameCompleteId();
  active_case="different_generation_and_no_war";DifferentGenerationAndNoWar();
  active_case="raw_war_byte_and_fallback";RawWarByteAndFallback();
  active_case="partial_sampling_and_changed_id";
  PartialSamplingAndChangedId();
#if defined(_WIN32) && defined(_M_X64)
  active_case="owned_trampoline_unwind";
  OwnedTrampolineUnwind();
#endif
  return 0;
  } catch(const std::exception &error) {
    std::fprintf(stderr,"county_relation_inputs_fixture case=%s: %s\n",active_case,error.what());
    return 1;
  } catch(...) {
    std::fprintf(stderr,"county_relation_inputs_fixture case=%s: non_std_exception\n",active_case);
    return 1;
  }
}
