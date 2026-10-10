#include "xar_bridge/construction_pointer_membership_30a6080_12004.hpp"
#include <bit>
#include <limits>

namespace xar::ck3_12004::construction_owner_mode3 {
static_assert(sizeof(std::uintptr_t)==8);
ConstructionPointerMembership30A6080Result12004
ReadConstructionPointerMembership30A6080V1(const RawReceiverAccessV1 &access,
    const ContextPredicateInputsV1 &inputs,std::uintptr_t rcx,
    std::uintptr_t rdx) noexcept {
  ConstructionPointerMembership30A6080Result12004 out;
  out.inputs=inputs;out.actual_rcx=rcx;out.actual_rdx=rdx;
  const auto fail=[&](PointerMembershipFailure12004 why){out.failure=why;return out;};
  if(!access.exact_12004_bound)return fail(PointerMembershipFailure12004::exact_build);
  if(!access.read_memory)return fail(PointerMembershipFailure12004::read_callback);
  if(rcx!=inputs.selector_object_pointer || rdx!=inputs.first_pointer)
    return fail(PointerMembershipFailure12004::copied_operands);
  std::uintptr_t begin=0;
  std::int32_t count=0;
  // Literal native load order: [RCX+420] then MOVSXD [RCX+42C].
  if(!RawReceiverReadV1(access,rcx,0x420,begin))
    return fail(PointerMembershipFailure12004::collection_header);
  out.collection_pointer=begin;
  if(!RawReceiverReadV1(access,rcx,0x42C,count))
    return fail(PointerMembershipFailure12004::collection_header);
  out.count_raw_i32=count;
  // LEA's qword wrapping end is an identity comparison, not a memory read.
  const auto signed_count=static_cast<std::int64_t>(count);
  out.end_pointer_bits=begin+static_cast<std::uint64_t>(signed_count)*8U;
  auto base=begin;
  const auto probe=[&](std::uintptr_t object,std::size_t offset,
      std::uintptr_t &value){
    std::uintptr_t address=0;
    if(!RawReceiverAddV1(object,offset,address)){
      out.failure=PointerMembershipFailure12004::probe_address;return false;
    }
    if(out.probe_count>=out.probes.size()){
      out.failure=PointerMembershipFailure12004::probe_address;return false;
    }
    auto &entry=out.probes[out.probe_count++];entry.address=address;
    if(!RawReceiverReadV1(access,object,offset,value)){
      out.failure=PointerMembershipFailure12004::probe_copy;return false;
    }
    entry.copied_value=value;return true;
  };
  if(count>0){
    auto remaining=static_cast<std::uint64_t>(count);
    do {
      const auto half=remaining>>1U;
      const auto advance=remaining-half;
      std::uintptr_t copied=0;
      if(!probe(base,static_cast<std::size_t>(half)*8U,copied))return out;
      // CMP [R8+RDX*8],R11; CMOVB R8,[R8+(oldcount-half)*8].
      if(copied<rdx)base+=advance*8U;
      remaining=half;
    }while(remaining!=0);
  }
  out.selected_pointer_bits=base;
  if(base==out.end_pointer_bits){
    out.path=PointerMembershipPath12004::iterator_at_end_false;out.value=false;return out;
  }
  // Zero count skips this probe; negative count takes it exactly as the body.
  std::uintptr_t selected_value=0;
  if(!probe(base,0,selected_value))return out;
  if(rdx<selected_value){
    out.path=PointerMembershipPath12004::candidate_greater_false;out.value=false;return out;
  }
  const auto delta=std::bit_cast<std::int64_t>(base-begin);
  const auto quotient=delta>>3;
  const auto low=static_cast<std::uint32_t>(quotient);
  const auto index=std::bit_cast<std::int32_t>(low);
  out.selected_index_raw_i32=index;
  out.value=index!=-1;
  out.path=*out.value?PointerMembershipPath12004::candidate_index_true:
      PointerMembershipPath12004::candidate_minus_one_false;
  return out;
}
bool ReadConstructionPointerMembership30A6080ChildV1(void *,
    const RawReceiverAccessV1 &access,const ContextPredicateInputsV1 &inputs,
    std::uintptr_t rcx,std::uintptr_t rdx,bool &output) noexcept {
  const auto result=ReadConstructionPointerMembership30A6080V1(access,inputs,rcx,rdx);
  if(!result.value)return false;
  output=*result.value;return true;
}
} // namespace xar::ck3_12004::construction_owner_mode3
