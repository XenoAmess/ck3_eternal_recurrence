#pragma once
#include "xar_bridge/army_actual_supply_parent_join_v1.hpp"
#include "xar_bridge/ck3_12004_native_invocation_context.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>
#ifndef XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004
#define XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004 0
#endif
namespace xar::ck3_12004 {
namespace supply_parent_join_detail_12004 {
using native_invocation_detail_12004::next_token;
using native_invocation_detail_12004::AllocateToken;
struct Payload {
  const void *receiver=nullptr;
  std::int32_t entry_army_id=-1,entry_native_carmy_id=-1;
  std::optional<std::uint64_t> passed_date,caller_return_rva;
  bool entry_identity_complete=false;
};
inline game::ArmyActualSupplyParentInvocationV1 Metadata(
    const NativeInvocationFrame12004 &frame,const Payload &payload) noexcept {
  return {frame.invocation_token,frame.native_thread_id,frame.nesting_depth,
      frame.parent_invocation_token,payload.caller_return_rva};
}
}
class SupplyParentJoinScope12004 final {
public:
  SupplyParentJoinScope12004(const void *receiver,std::int32_t army_id,std::int32_t native_id,
      std::optional<std::uint64_t> date,std::optional<std::uint64_t> caller,
      std::uint32_t thread_id,bool identity_complete) noexcept
      :payload_{receiver,army_id,native_id,date,caller,identity_complete},
       scope_(NativeInvocationParentKind12004::periodic_supply_callback,thread_id,&payload_){}
  SupplyParentJoinScope12004(const SupplyParentJoinScope12004 &)=delete;
  SupplyParentJoinScope12004 &operator=(const SupplyParentJoinScope12004 &)=delete;
  std::optional<game::ArmyActualSupplyParentInvocationV1> invocation() const noexcept {
    if(scope_.frame().invocation_token==0)return std::nullopt;
    return supply_parent_join_detail_12004::Metadata(scope_.frame(),payload_);
  }
private:
  // Construct payload first; destroy scope before its payload lifetime ends.
  supply_parent_join_detail_12004::Payload payload_{};
  NativeInvocationScope12004 scope_;
};
template <typename ReadAt>
inline std::optional<game::ArmyActualSupplyParentWriterContextV1>
// The typed owner must supply a currently live, source-validated frame. This
// helper performs no ancestor traversal and retains every original read gate.
CaptureSupplyParentWriterContextFromFrame12004(const NativeInvocationFrame12004 *frame,
    std::uint32_t thread_id,ReadAt read_at) noexcept {
  if(frame==nullptr||frame->invocation_token==0||frame->typed_payload==nullptr||
      frame->parent_kind!=NativeInvocationParentKind12004::periodic_supply_callback)return std::nullopt;
  const auto &payload=*static_cast<const supply_parent_join_detail_12004::Payload*>(frame->typed_payload);
  game::ArmyActualSupplyParentWriterContextV1 result{};
  result.invocation=supply_parent_join_detail_12004::Metadata(*frame,payload);
  result.passed_date_raw64=payload.passed_date;
  if(frame->native_thread_id!=thread_id){result.capture_failure_flags|=1U;return result;}
  std::int32_t public_id=-1,native_id=-1;std::int64_t stock=0;
  const bool public_read=read_at(payload.receiver,0x124,&public_id,sizeof(public_id));
  const bool native_read=read_at(payload.receiver,0x10,&native_id,sizeof(native_id));
  const bool stock_read=read_at(payload.receiver,0x180,&stock,sizeof(stock));
  if(public_read)result.army_id=public_id;
  if(native_read)result.native_carmy_id=native_id;
  if(stock_read)result.stock_at_writer_entry_raw=stock;
  result.receiver_identity_matches=payload.entry_identity_complete&&public_read&&native_read&&
      public_id!=-1&&native_id!=-1&&payload.entry_army_id==public_id&&payload.entry_native_carmy_id==native_id;
  if(!public_read||!native_read)result.capture_failure_flags|=2U;
  if(!stock_read)result.capture_failure_flags|=4U;
  if(!result.receiver_identity_matches)result.capture_failure_flags|=8U;
  return result;
}
template <typename ReadAt>
inline std::optional<game::ArmyActualSupplyParentWriterContextV1>
CaptureSupplyParentWriterContext12004(std::uint32_t thread_id,ReadAt read_at) noexcept {
  return CaptureSupplyParentWriterContextFromFrame12004(
      CurrentNativeInvocationContext12004(),thread_id,read_at);
}
}
