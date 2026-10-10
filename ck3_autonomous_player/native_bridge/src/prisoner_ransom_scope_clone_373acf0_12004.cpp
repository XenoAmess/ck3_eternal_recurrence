#include "xar_bridge/prisoner_ransom_scope_clone_373acf0_12004.hpp"

namespace xar::ck3_12004 {
namespace {
template<class T> void WriteNumber(PrisonerRansomScopeChildPostimage12004 &out,
                                  std::size_t offset,T value) {
  static_assert(std::is_integral_v<T>);
  PrisonerRansomScopeByteWrite12004 write;
  write.scope_member_offset=offset;write.bytes.resize(sizeof(value));
  std::memcpy(write.bytes.data(),&value,sizeof(value));
  out.byte_writes.push_back(std::move(write));
}
PrisonerRansomScopePointer12004 Relation(std::size_t offset,
    PrisonerRansomScopePointerKind12004 kind,std::uintptr_t relative) {
  PrisonerRansomScopePointer12004 out;out.member_offset=offset;
  out.kind=kind;out.relative_offset_or_rva=relative;return out;
}
template<class T> T SupportScalar(const PrisonerScopeCloneSupport118Source12004 &source,
                                  std::size_t offset) {
  T out{};std::memcpy(&out,source.raw.data()+offset,sizeof(out));return out;
}
} // namespace

PrisonerRansomScopeChildPostimage12004 ProjectPrisonerRansomScopeVector18Child12004(
    const PrisonerScopeVectorCopy260E04012004 &source) {
  PrisonerRansomScopeChildPostimage12004 out;out.frame=source.frame;
  out.actual_callee_rva=0x260E040;out.actual_callsite_rva=0x373ADAE;
  out.source_member_offset=out.destination_member_offset=0x18;
  if(!PrisonerQuoteSourceFrameReady12004(source.frame) || !source.copied_shape_ready ||
     source.allocation_required || !source.count_i32 ||
     source.source_scope_identity!=source.frame.original_scope_identity ||
     source.source_scope_identity>(std::numeric_limits<std::uintptr_t>::max)()-0x18 ||
     source.source_vector_identity!=source.source_scope_identity+0x18 ||
     source.destination_capacity_i32!=8 || source.data_clone_relative_offset!=0x38 ||
     source.allocator_clone_relative_offset!=0x30 || *source.count_i32>8)return out;
  const std::size_t inline_bytes=*source.count_i32>0 ?
      static_cast<std::size_t>(*source.count_i32)*24 : 0;
  if(source.copied_inline_bytes!=inline_bytes)return out;
  for(std::size_t i=0;i<source.source_defined_inline_mask.size();++i)
    if((source.source_defined_inline_mask[i]!=0)!=(i<inline_bytes))return out;
  WriteNumber(out,0x20,std::int32_t{8});
  WriteNumber(out,0x24,*source.count_i32);
  out.pointers.push_back(Relation(0x18,PrisonerRansomScopePointerKind12004::clone_relative,0x38));
  out.pointers.push_back(Relation(0x28,PrisonerRansomScopePointerKind12004::clone_relative,0x30));
  out.pointers.push_back(Relation(0x30,PrisonerRansomScopePointerKind12004::module_relative,0x448D2A0));
  out.pointers.push_back(Relation(0xF8,PrisonerRansomScopePointerKind12004::module_relative,0x54DE2E0));
  if(inline_bytes!=0) {
    PrisonerRansomScopeByteWrite12004 write;write.scope_member_offset=0x38;
    write.bytes.resize(inline_bytes);
    std::memcpy(write.bytes.data(),source.inline_raw.data(),inline_bytes);
    out.byte_writes.push_back(std::move(write));
  }
  out.minimum_returned_fields_source_ready=true;
  return out;
}

PrisonerRansomScopeChildPostimage12004 ProjectPrisonerRansomScopeVector100Child12004(
    const PrisonerScopeCloneVector10012004 &source) {
  PrisonerRansomScopeChildPostimage12004 out;out.frame=source.frame;
  out.actual_callee_rva=0x37282B0;out.actual_callsite_rva=0x373ADA1;
  out.source_member_offset=out.destination_member_offset=0x100;
  if(!PrisonerQuoteSourceFrameReady12004(source.frame) || !source.logical_postimage_ready ||
     !source.source_inputs_ready || source.source_count_raw_i32!=std::int32_t{0} ||
     !source.source_data_identity || !source.source_member_identity ||
     source.frame.original_scope_identity>(std::numeric_limits<std::uintptr_t>::max)()-0x100 ||
     *source.source_member_identity!=source.frame.original_scope_identity+0x100 ||
     source.frame.module_base>(std::numeric_limits<std::uintptr_t>::max)()-0x54DE270)return out;
  for(const bool defined:source.header_defined_bytes)if(!defined)return out;
  std::uintptr_t data=0,allocator=0;
  std::int32_t capacity=0,count=0;
  std::memcpy(&data,source.header_raw.data(),8);
  std::memcpy(&capacity,source.header_raw.data()+8,4);
  std::memcpy(&count,source.header_raw.data()+0xC,4);
  std::memcpy(&allocator,source.header_raw.data()+0x10,8);
  if(data!=0 || capacity!=0 || count!=0 || allocator!=source.frame.module_base+0x54DE270)return out;
  WriteNumber(out,0x108,std::int32_t{0});WriteNumber(out,0x10C,std::int32_t{0});
  PrisonerRansomScopePointer12004 null_data;null_data.member_offset=0x100;
  null_data.kind=PrisonerRansomScopePointerKind12004::null_value;
  out.pointers.push_back(null_data);
  out.pointers.push_back(Relation(0x110,PrisonerRansomScopePointerKind12004::module_relative,0x54DE270));
  out.minimum_returned_fields_source_ready=true;
  return out;
}

PrisonerRansomScopeChildPostimage12004 ProjectPrisonerRansomScopeSupport118Child12004(
    const PrisonerScopeCloneSupport118Source12004 &source) {
  PrisonerRansomScopeChildPostimage12004 out;out.frame=source.frame;
  out.actual_callee_rva=0x3727180;out.actual_callsite_rva=0x373ADBD;
  out.source_member_offset=out.destination_member_offset=0x118;
  if(!PrisonerQuoteSourceFrameReady12004(source.frame) || !source.returned_fields_source_ready ||
     source.source_vector10_count!=std::int32_t{0} || source.source_vector30_count!=std::int32_t{0} ||
     !source.source_vector10_data || !source.source_vector30_data || !source.source_scalar28_raw_u32 ||
     source.final_predicate_al_raw_u8!=std::uint8_t{0} || !source.original_source_support_identity ||
     source.physical_cloned_support_identity || source.native_copy_called ||
     source.frame.original_scope_identity>(std::numeric_limits<std::uintptr_t>::max)()-0x118 ||
     *source.original_source_support_identity!=source.frame.original_scope_identity+0x118 ||
     source.frame.module_base>(std::numeric_limits<std::uintptr_t>::max)()-0x54DE278)return out;
  for(std::size_t i=0;i<source.defined.size();++i) {
    const bool expected=i<0x2C || (i>=0x30 && i<0x4F);
    if((source.defined[i]!=0)!=expected)return out;
  }
  std::uint32_t scalar=0;std::memcpy(&scalar,source.raw.data()+0x28,4);
  if(scalar!=*source.source_scalar28_raw_u32)return out;
  if(SupportScalar<std::uintptr_t>(source,0)!=source.frame.module_base+0x448D1F8 ||
     SupportScalar<std::uintptr_t>(source,8)!=source.frame.module_base+0x448D268 ||
     SupportScalar<std::uintptr_t>(source,0x10)!=0 || SupportScalar<std::uint64_t>(source,0x18)!=0 ||
     SupportScalar<std::uintptr_t>(source,0x20)!=source.frame.module_base+0x54DE278 ||
     SupportScalar<std::uintptr_t>(source,0x30)!=0 || SupportScalar<std::uint64_t>(source,0x38)!=0 ||
     SupportScalar<std::uintptr_t>(source,0x40)!=source.frame.module_base+0x54DE270 ||
     SupportScalar<std::int32_t>(source,0x48)!=std::int32_t{-1} ||
     SupportScalar<std::uint16_t>(source,0x4C)!=0 || source.raw[0x4E]!=0)return out;
  PrisonerRansomScopeByteWrite12004 first;first.scope_member_offset=0x118;
  first.bytes.assign(source.raw.begin(),source.raw.begin()+0x2C);
  PrisonerRansomScopeByteWrite12004 second;second.scope_member_offset=0x148;
  second.bytes.assign(source.raw.begin()+0x30,source.raw.begin()+0x4F);
  out.byte_writes.push_back(std::move(first));out.byte_writes.push_back(std::move(second));
  out.minimum_returned_fields_source_ready=true;
  return out;
}

PrisonerRansomScopeCloneSource12004 ReadPrisonerRansomScopeClone12004(
    const PrisonerQuoteReadOnlyAccess12004 &access,const PrisonerQuoteSourceFrame12004 &frame) {
  const auto input=ReadPrisonerRansomScopeCloneInputs12004(access,frame);
  const auto vector18=ReadPrisonerScopeVectorCopy260E04012004(access,frame,frame.original_scope_identity);
  auto bounded_access=access;bounded_access.maximum_modifier_occurrences=0;
  const auto vector100=ReadPrisonerScopeCloneVector10012004(bounded_access,frame);
  const auto support118=ReadPrisonerScopeCloneSupport11812004(access,frame);
  auto out=ProjectPrisonerRansomScopeClone12004(input,
      ProjectPrisonerRansomScopeVector100Child12004(vector100),
      ProjectPrisonerRansomScopeVector18Child12004(vector18),
      ProjectPrisonerRansomScopeSupport118Child12004(support118));
  out.vector18_source=vector18;out.vector100_source=vector100;out.support118_source=support118;
  return out;
}
} // namespace xar::ck3_12004
