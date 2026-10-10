#include "xar_bridge/army_gathering_due_natural_stage_12004_serializer.hpp"
#include <cstring>
#include <map>
#include <stdexcept>

namespace {
using namespace xar::ck3_12004;
std::map<std::uintptr_t,std::uint8_t> bytes;
constexpr std::uintptr_t base=0x10000000, primary=0x10000, state=0x20000, army=0x30000,
    regi=0x40000, record=0x50000, ref=0x60000, queue=0x70000, arrg=0x80000;
constexpr std::uint32_t army_id=0xA1000001, regi_id=0xB2000002, arrg_id=0xC3000003;
constexpr std::uintptr_t rax_bits=0xFEDCBA9876543210ULL;
unsigned original_calls=0; bool deny=false, corrupt_parent=false;
ArmyGatheringDueNaturalBindings12004 due_binding;
ArmyGatheringDueNaturalStage12004 due_result;
void Require(bool v,const char *msg){if(!v)throw std::runtime_error(msg);}
template<class T> void Put(std::uintptr_t address,T value){
  auto *p=reinterpret_cast<const std::uint8_t*>(&value);
  for(std::size_t i=0;i<sizeof value;++i)bytes[address+i]=p[i];
}
bool Read(void*,std::uintptr_t address,void *out,std::size_t count) noexcept {
  if(deny)return false;
  auto *p=static_cast<std::uint8_t*>(out);
  for(std::size_t i=0;i<count;++i){auto found=bytes.find(address+i);if(found==bytes.end())return false;p[i]=found->second;}
  return true;
}
void Zero(std::uintptr_t address,std::size_t count){for(std::size_t i=0;i<count;++i)bytes[address+i]=0;}
void List(std::uintptr_t header,std::uintptr_t data,std::int32_t count){Put(header,data);Put(header+8,count);Put(header+12,count);}
void Setup(){
  bytes.clear();original_calls=0;deny=false;corrupt_parent=false;
  Zero(primary,0x200);Zero(state,0xD0);Zero(army,0x200);Zero(regi,0x160);Zero(record,0x38);Zero(ref,16);Zero(arrg,0x150);
  Put(state+8,std::uint64_t{0xABCDEF0000000018ULL});Put(state+0x9C,std::uint32_t{7});Put(state+0xC0,std::uint8_t{0x80});
  List(primary+0x158,queue,1);Put(queue,army_id);
  List(primary+0x30,queue+0x10,1);Put(queue+0x10,regi_id);
  List(primary+0x50,queue+0x20,1);Put(queue+0x20,army_id);
  // Registry absent is an observed native fallback, not an unreadable slot.
  for(auto r:{0x5D1DE48,0x5D1DE70,0x5D1EB68,0x5D1F340})Put(base+r,std::uintptr_t{0});
  Put(base+0x5D1DE50,army);Put(base+0x5D1DE18,army+0x300);
  Put(base+0x5D1EB58,regi);Put(base+0x5D1F338,arrg);
  Zero(army+0x300,0x10);Put(army+0x308,std::uint32_t{0xFFFFFFFF});
  Put(army+0x10,army_id);Put(army+0x14,std::uint32_t{0x41726D79});
  Put(army+0x128,std::uint32_t{0xFFFFFFFF});
  List(army+0x38,queue+0x30,1);Put(queue+0x30,arrg_id);
  Put(army+0x50,queue+0x40);Put(army+0x5C,std::int32_t{1});Put(queue+0x40,record);
  Put(record,std::int32_t{24});Put(record+8,ref);Put(record+0x14,std::int32_t{1});Put(record+0x2C,std::int32_t{0});
  Put(ref+8,regi_id);Put(ref+0xC,std::int32_t{0});
  Put(regi+0x10,regi_id);Put(regi+0x14,std::uint32_t{0x52656769});Put(regi+0x148,std::int64_t{123456});
  Put(regi+0x18,std::int32_t{100});Put(regi+0x1C,std::int32_t{61});
  Put(regi+0x20,regi_id);Put(regi+0x28,std::uint32_t{0xFFFFFFFF});
  Put(regi+0x2C,std::uint8_t{1});Put(regi+0x30,std::int32_t{3});Put(regi+0x34,std::uint64_t{0x1122334400000018ULL});
  Put(arrg+0x10,arrg_id);Put(arrg+0x14,std::uint32_t{0x41725267});Put(arrg+0x38,std::int32_t{61});Put(arrg+0x3C,std::int32_t{100});
  due_binding=BindArmyGatheringDueNaturalStage12004(base,"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",nullptr,Read);
  ClearArmyGatheringDueNaturalJournal12004();
}
std::uintptr_t __fastcall OriginalDue(void *p,const void *date){
  ++original_calls;Require(reinterpret_cast<std::uintptr_t>(p)==primary && reinterpret_cast<std::uintptr_t>(date)==state+8,"original arguments preserved");
  Put(primary+0x164,std::int32_t{0});Put(army+0x5C,std::int32_t{0});
  Put(regi+0x28,arrg_id);Put(regi+0x2C,std::uint8_t{0});Put(regi+0x34,std::uint64_t{0xFFFFFFFF029C77F8ULL});
  Put(arrg+0x38,std::int32_t{79});Put(army+0x130,std::uint64_t{0x87654321ABCDEF00ULL});
  // Removed record is no longer readable. Return capture must follow immutable
  // entry refs, not dereference record/pending-ref memory after destruction.
  for(std::size_t i=0;i<0x38;++i)bytes.erase(record+i);
  for(std::size_t i=0;i<16;++i)bytes.erase(ref+i);
  return rax_bits;
}
std::uintptr_t __fastcall Parent(void*){
  const auto pc=corrupt_parent?std::uintptr_t{0x2A9A67E}:kArmyGatheringDueNaturalReturnRva12004;
  due_result=InvokeArmyGatheringDueNatural12004(due_binding,OriginalDue,reinterpret_cast<void*>(primary),
      reinterpret_cast<const void*>(state+8),pc,std::uint8_t{0});
  return due_result.raw_return_bits;
}
ArmyNaturalPhaseRecord12004 RunParent(){
  ArmyNaturalPhaseBindings12004 b;b.read=Read;b.game_state_identity=state;b.next_event=NextArmyNaturalPhaseEvent12004;
  b.session_identity=std::uintptr_t{0x12345};
  return InvokeArmyNaturalPhaseScope12004(b,Parent,reinterpret_cast<void*>(primary+8),ArmyNaturalPhaseKind12004::post_date,0x123);
}
} // namespace

void RunArmyDueNaturalFocus12004(){
  Setup();const auto parent=RunParent();
  Require(original_calls==1 && parent.raw_return_bits==rax_bits && due_result.raw_return_bits==rax_bits,"one original and opaque64 RAX");
  Require(due_result.observed && due_result.actual_poststage_observed && due_result.same_clock_thread_order==true && due_result.active_parent_unchanged==true,"literal actual parent entry/returned clock join");
  Require(due_result.parent.saved_mask02_admitted==false && !due_result.parent.saved_c0_raw,"captured false mask is not guessed fullC0");
  Require(due_result.entry.queue158.count==1 && due_result.returned.queue158.count==0 && due_result.returned.entry_queue_extent_backing_full_ids==std::vector<std::uint32_t>{army_id},"original queue and returned backing IDs preserved separately");
  Require(due_result.entry.persistent.at(0).chunks.size()==7 && due_result.entry.persistent.at(0).prepared148==123456,"seven original physical chunks and prepared capture");
  const auto &before=due_result.entry.queued_armies.at(0).gathering_records.at(0).pending_refs.at(0);
  const auto &after=due_result.returned.entry_due_refs_at_return.at(0);
  Require(before.chunk && after.chunk && before.chunk->association_full_id==0xFFFFFFFF && after.chunk->association_full_id==arrg_id &&
      after.chunk->date_raw64==0xFFFFFFFF029C77F8ULL && after.source_ref_identity==ref,"actual returned physical association/date despite freed record");
  Require(due_result.entry.queued_armies.at(0).arrg.at(0).current38==61 && due_result.returned.roster_armies.at(0).arrg.at(0).current38==79,"actual refresh cache values, no refresh invocation");
  const auto immutable=ReadArmyGatheringDueNaturalForArmy12004(army_id);
  Require(immutable.size()==1 && ReadArmyGatheringDueNaturalForArmy12004(0xFFFFFFFF).empty(),"owned selected ID journal filter");
  Put(primary+0x164,std::int32_t{999});
  Require(ReadArmyGatheringDueNaturalForArmy12004(army_id).at(0).returned.queue158.count==0,"later current memory cannot rewrite historical return");
  const auto json=SerializeArmyGatheringDueNaturalStage12004(immutable);
  Require(json.find("\"session_identity\":74565")!=std::string::npos && json.find("\"prediction_ready\":false")!=std::string::npos &&
      json.find("\"entry_due_refs_at_return\"")!=std::string::npos,"full authoritative parent and fieldpartial rawwire");
  Setup();corrupt_parent=true;RunParent();Require(original_calls==1 && !due_result.actual_boundary_admitted && !due_result.observed,"wrong literalPC never certifies stage but original stillonce");
  Setup();deny=true;RunParent();Require(original_calls==1 && due_result.original_returned && !due_result.entry.queue158.count &&
      !due_result.entry.all_declared_reads_complete,"guard failure is null/partial not defaultzero");
  Setup();auto standalone=InvokeArmyGatheringDueNatural12004(due_binding,OriginalDue,reinterpret_cast<void*>(primary),reinterpret_cast<const void*>(state+8),kArmyGatheringDueNaturalReturnRva12004);
  Require(original_calls==1 && !standalone.actual_boundary_admitted,"independent current call cannot fabricate active parent");
  auto installer=BindArmyGatheringDueNaturalHook12004(base,"badpin");Require(!installer.complete_source_proof && !installer.primary_thread_suspended_proven && !InstallArmyGatheringDueNaturalHook12004(installer),"installer rejects missing exact pin/startup proof without touching image");
}
