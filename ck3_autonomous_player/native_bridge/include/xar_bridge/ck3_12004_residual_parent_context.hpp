#pragma once
#include "xar_bridge/army_actual_residual_parent_v1.hpp"
#include "xar_bridge/ck3_12004_native_invocation_context.hpp"
#include "xar_bridge/ck3_12004_supply_parent_join_context.hpp"
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>

namespace xar::ck3_12004 {
using ResidualParentRead12004=bool(*)(void*,const void*,void*,std::size_t) noexcept;
struct ResidualParentReader12004 {
  void *context=nullptr;
  ResidualParentRead12004 read=nullptr;
  template<class T> bool At(const void *p,std::size_t offset,T &out) const noexcept {
    const auto a=reinterpret_cast<std::uintptr_t>(p);
    if(!a||!read||offset>(std::numeric_limits<std::uintptr_t>::max)()-a)return false;
    return read(context,reinterpret_cast<const void*>(a+offset),&out,sizeof out);
  }
};
namespace residual_parent_detail_12004 {
struct Header {
  const void *data=nullptr;std::int32_t capacity=0,count=0;
};
inline bool Array(const ResidualParentReader12004 &r,const void *p,Header &h) noexcept {
  return r.At(p,0,h.data)&&r.At(p,8,h.capacity)&&r.At(p,12,h.count)&&
      h.count>=0&&h.capacity>=h.count&&(h.count==0||h.data!=nullptr);
}
struct Identity {std::int32_t native=-1,public_id=-1;std::uint32_t magic=0;};
inline bool Army(const ResidualParentReader12004 &r,const void *p,Identity &i) noexcept {
  return r.At(p,0x10,i.native)&&r.At(p,0x14,i.magic)&&r.At(p,0x124,i.public_id)&&
      i.magic==0x41726D79U&&i.native!=-1&&i.public_id!=-1;
}
inline bool PeriodicCaller(std::optional<std::uint64_t> pc,
    const NativeInvocationFrame12004 *parent) noexcept {
  return pc&&*pc>0x24E3410&&*pc<0x24E3A3C&&parent&&parent->typed_payload&&
      parent->parent_kind==NativeInvocationParentKind12004::periodic_supply_callback;
}
struct Payload {
  ResidualParentReader12004 reader;
  const void *actual_array=nullptr,*source_carmy=nullptr;
  std::int32_t budget=0;std::uint8_t flags=0;
  std::optional<std::uint64_t> caller_return_rva;
  const NativeInvocationFrame12004 *enclosing=nullptr;
  Header entry_array;Identity entry_army;
  std::optional<game::ArmyActualResidualSiegeBudgetV1> siege_budget_at_allocator_v1;
  bool entry_array_valid=false,entry_army_valid=false;
  game::ArmyResidualRequestSource12004 source=game::ArmyResidualRequestSource12004::unknown;
};
inline Payload Make(const ResidualParentReader12004 &reader,const void *array,
    std::int32_t budget,std::uint8_t flags,std::optional<std::uint64_t> caller,
    const void *natural_return_slot) noexcept {
  Payload p{};p.reader=reader;p.actual_array=array;p.budget=budget;p.flags=flags;
  p.caller_return_rva=caller;p.enclosing=CurrentNativeInvocationContext12004();
  const auto address=reinterpret_cast<std::uintptr_t>(array);
  if(caller==0x24E2630&&flags==0&&address>=0x38){
    // Source24E2627 literally forms RCX=actual county CArmy+38.
    p.source=game::ArmyResidualRequestSource12004::county_entry;
    p.source_carmy=reinterpret_cast<const void*>(address-0x38);
  } else if(PeriodicCaller(caller,p.enclosing)) {
    const auto &s=*static_cast<const supply_parent_join_detail_12004::Payload*>(p.enclosing->typed_payload);
    const auto a=reinterpret_cast<std::uintptr_t>(s.receiver);
    if(a&&a<=(std::numeric_limits<std::uintptr_t>::max)()-0x38&&a+0x38==address){
      p.source=game::ArmyResidualRequestSource12004::periodic_callback;p.source_carmy=s.receiver;
    }
  }
  // 24E37AE calls from the unchanged 24E3410 frame. The continuation hook
  // follows only TEST/JE (no stack mutation), so caller RSP is return_slot+8.
  // Capture before the allocator executes; never use this helper's own stack.
  if(p.source==game::ArmyResidualRequestSource12004::periodic_callback&&
      caller==0x24E37B3&&flags==0){
    auto &v=p.siege_budget_at_allocator_v1.emplace();
    if(!natural_return_slot)v.capture_failure_flags|=1U;
    else {
      std::int32_t value=0;
      if(reader.At(natural_return_slot,0x88,value))v.original_siege_budget_soldiers=value;
      else v.capture_failure_flags|=2U;
      if(reader.At(natural_return_slot,0x90,value))v.combined_siege_raid_budget_soldiers=value;
      else v.capture_failure_flags|=4U;
    }
  }
  p.entry_array_valid=Array(reader,array,p.entry_array);
  if(p.source_carmy)p.entry_army_valid=Army(reader,p.source_carmy,p.entry_army);
  return p;
}
}
class ResidualParentScope12004 final {
public:
  ResidualParentScope12004(const ResidualParentReader12004 &reader,const void *array,
      std::int32_t budget,std::uint8_t flags,std::optional<std::uint64_t> caller,
      std::uint32_t thread,const void *natural_return_slot=nullptr) noexcept
      :payload_(residual_parent_detail_12004::Make(reader,array,budget,flags,caller,natural_return_slot)),
       scope_(NativeInvocationParentKind12004::residual_allocator,thread,&payload_){}
  ResidualParentScope12004(const ResidualParentScope12004 &)=delete;
  ResidualParentScope12004 &operator=(const ResidualParentScope12004 &)=delete;
private:
  residual_parent_detail_12004::Payload payload_;
  NativeInvocationScope12004 scope_;
};
inline std::optional<game::ArmyActualResidualParentV1>
CaptureResidualParentWriterContext12004(std::uint32_t thread,std::int32_t writer_full_id,
    std::optional<std::uint64_t> writer_return) noexcept {
  using namespace residual_parent_detail_12004;
  const auto *frame=CurrentNativeInvocationContext12004();
  if(!frame||frame->parent_kind!=NativeInvocationParentKind12004::residual_allocator||
      !frame->typed_payload||!frame->invocation_token)return std::nullopt;
  const auto &p=*static_cast<const Payload*>(frame->typed_payload);
  game::ArmyActualResidualParentV1 result{};
  result.invocation_token=frame->invocation_token;result.native_thread_id=frame->native_thread_id;
  result.nesting_depth=frame->nesting_depth;result.parent_invocation_token=frame->parent_invocation_token;
  result.allocator_caller_return_rva=p.caller_return_rva;
  result.requested_budget=p.budget;result.flags_raw=p.flags;result.request_source=p.source;
  result.siege_budget_at_allocator_v1=p.siege_budget_at_allocator_v1;
  if(p.enclosing)result.enclosing_parent_kind=static_cast<std::uint32_t>(p.enclosing->parent_kind);
  if(thread!=frame->native_thread_id||!thread){result.capture_failure_flags|=1U;return result;}
  if(writer_return!=0x2A958E8){result.capture_failure_flags|=2U;return result;}
  Header now{};Identity army{};
  result.array_header_matches=p.entry_array_valid&&Array(p.reader,p.actual_array,now)&&
      now.data==p.entry_array.data&&now.capacity==p.entry_array.capacity&&now.count==p.entry_array.count;
  if(!result.array_header_matches)result.capture_failure_flags|=4U;
  const bool valid=p.source_carmy&&Army(p.reader,p.source_carmy,army);
  if(valid){result.army_id=army.public_id;result.native_carmy_id=army.native;}
  result.receiver_identity_matches=p.entry_army_valid&&valid&&
      p.entry_army.native==army.native&&p.entry_army.public_id==army.public_id;
  if(!result.receiver_identity_matches)result.capture_failure_flags|=8U;
  if(result.array_header_matches&&now.count<=4096&&writer_full_id!=-1){
    for(std::int32_t index=0;index<now.count;++index){
      std::int32_t raw=-1;
      if(!p.reader.At(now.data,static_cast<std::size_t>(index)*4U,raw)){
        result.capture_failure_flags|=16U;break;
      }
      if(raw==writer_full_id){result.writer_full_id_in_actual_array=true;result.matching_roster_occurrence=index;break;}
    }
  }
  if(!result.writer_full_id_in_actual_array)result.capture_failure_flags|=32U;
  result.source_complete=result.capture_failure_flags==0&&
      result.request_source!=game::ArmyResidualRequestSource12004::unknown;
  return result;
}
// Preserve the existing periodic parent metadata through this one source-proved
// direct allocator child. No TLS rebinding or arbitrary ancestor search occurs.
template<class ReadAt>
inline std::optional<game::ArmyActualSupplyParentWriterContextV1>
CaptureResidualEnclosingSupplyWriterContext12004(std::uint32_t thread,
    std::optional<std::uint64_t> writer_return,ReadAt read_at) noexcept {
  const auto *frame=CurrentNativeInvocationContext12004();
  if(!frame||frame->parent_kind!=NativeInvocationParentKind12004::residual_allocator||
      !frame->typed_payload||frame->native_thread_id!=thread||writer_return!=0x2A958E8)
    return std::nullopt;
  const auto &p=*static_cast<const residual_parent_detail_12004::Payload*>(frame->typed_payload);
  if(p.source!=game::ArmyResidualRequestSource12004::periodic_callback||
      !residual_parent_detail_12004::PeriodicCaller(p.caller_return_rva,p.enclosing))return std::nullopt;
  return CaptureSupplyParentWriterContextFromFrame12004(p.enclosing,thread,read_at);
}
}
