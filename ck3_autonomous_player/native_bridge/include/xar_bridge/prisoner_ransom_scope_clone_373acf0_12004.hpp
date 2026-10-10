#pragma once

#include "xar_bridge/prisoner_quote_readonly_source_12004.hpp"
#include "xar_bridge/prisoner_scope_vector_copy_260e040_12004.hpp"
#include "xar_bridge/prisoner_scope_clone_vector100_12004.hpp"
#include "xar_bridge/prisoner_scope_clone_support118_12004.hpp"
#include <array>
#include <cstring>
#include <type_traits>

#define XAR_HAS_PRISONER_RANSOM_SCOPE_CLONE_373ACF0_12004 1

namespace xar::ck3_12004 {
inline constexpr std::size_t kPrisonerRansomScopeCloneBytes12004 = 0x168;
inline constexpr std::uintptr_t kPrisonerRansomScopeCloneRva12004 = 0x373ACF0;

enum class PrisonerRansomScopePointerKind12004 : std::uint8_t {
  unavailable, null_value, observed_raw, clone_relative, module_relative
};
struct PrisonerRansomScopePointer12004 {
  std::size_t member_offset = 0;
  PrisonerRansomScopePointerKind12004 kind = PrisonerRansomScopePointerKind12004::unavailable;
  std::optional<std::uintptr_t> observed_raw, relative_offset_or_rva;
};
struct PrisonerRansomScopeRaw12004 {
  std::array<std::uint8_t,kPrisonerRansomScopeCloneBytes12004> raw{};
  // Relational self pointers are source-defined with unknown numeric bits.
  // Zero placeholders are never observed null pointers.
  std::array<std::uint8_t,kPrisonerRansomScopeCloneBytes12004> source_defined{};
  std::array<std::uint8_t,kPrisonerRansomScopeCloneBytes12004> numeric_known{};
  std::vector<PrisonerRansomScopePointer12004> pointers;
};
struct PrisonerRansomScopeByteWrite12004 {
  std::size_t scope_member_offset = 0;
  std::vector<std::uint8_t> bytes;
};
// Produced by the exclusive child owner from its frozen same-frame source.
// This does not accept an allocator result address as a numerical result.
struct PrisonerRansomScopeChildPostimage12004 {
  PrisonerQuoteSourceFrame12004 frame{};
  std::uintptr_t actual_callee_rva = 0, actual_callsite_rva = 0;
  std::size_t source_member_offset = 0, destination_member_offset = 0;
  std::vector<PrisonerRansomScopeByteWrite12004> byte_writes;
  std::vector<PrisonerRansomScopePointer12004> pointers;
  bool minimum_returned_fields_source_ready = false;
  bool actual_native_copy_observed = false;
};
struct PrisonerRansomScopeCloneInputs12004 {
  PrisonerQuoteSourceFrame12004 frame{};
  std::array<std::uint8_t,20> original_header{};
  bool original_header_copied = false;
  std::optional<std::uint32_t> context_recipient_full_id;
  std::optional<std::uint8_t> loaded_evaluation_flag;
};
struct PrisonerRansomScopeCloneSource12004 {
  PrisonerQuoteSourceFrame12004 frame{};
  PrisonerRansomScopeRaw12004 returned_scope{};
  std::optional<std::uintptr_t> physical_cloned_scope_identity;
  PrisonerQuoteInternalAliases12004 internal_aliases{};
  std::optional<PrisonerScopeVectorCopy260E04012004> vector18_source;
  std::optional<PrisonerScopeCloneVector10012004> vector100_source;
  std::optional<PrisonerScopeCloneSupport118Source12004> support118_source;
  bool header_copy_source_ready = false, source_equivalent_clone_shape_ready = false;
  bool primary_and_tertiary_are_same_logical_clone = false;
  bool support_is_logical_clone_plus118 = false;
  bool native_clone_called = false;
  std::string unavailable_reason;
};

namespace prisoner_ransom_scope_clone_detail {
inline bool Range(std::size_t offset,std::size_t count,std::size_t begin=0,
                  std::size_t end=kPrisonerRansomScopeCloneBytes12004) noexcept {
  return offset>=begin && offset<=end && count<=end-offset;
}
inline bool Defined(const PrisonerRansomScopeRaw12004 &out,std::size_t offset,std::size_t count) {
  if(!Range(offset,count))return false;
  for(std::size_t i=offset;i<offset+count;++i)if(!out.source_defined[i])return false;
  return true;
}
inline void Bytes(PrisonerRansomScopeRaw12004 &out,std::size_t offset,
                  const std::uint8_t *bytes,std::size_t count) {
  std::memcpy(out.raw.data()+offset,bytes,count);
  for(std::size_t i=offset;i<offset+count;++i)out.source_defined[i]=out.numeric_known[i]=1;
}
template<class T> inline void Number(PrisonerRansomScopeRaw12004 &out,std::size_t offset,T value) {
  static_assert(std::is_integral_v<T>);
  Bytes(out,offset,reinterpret_cast<const std::uint8_t *>(&value),sizeof(value));
}
inline bool Pointer(PrisonerRansomScopeRaw12004 &out,const PrisonerRansomScopePointer12004 &p,
                    std::uintptr_t module_base) {
  if(!Range(p.member_offset,8))return false;
  std::optional<std::uintptr_t> numeric;
  switch(p.kind) {
    case PrisonerRansomScopePointerKind12004::null_value:
      if(p.observed_raw || p.relative_offset_or_rva)return false;
      numeric=0;break;
    case PrisonerRansomScopePointerKind12004::observed_raw:
      if(!p.observed_raw || p.relative_offset_or_rva)return false;
      numeric=p.observed_raw;break;
    case PrisonerRansomScopePointerKind12004::clone_relative:
      if(p.observed_raw || !p.relative_offset_or_rva || *p.relative_offset_or_rva>=kPrisonerRansomScopeCloneBytes12004)return false;
      break;
    case PrisonerRansomScopePointerKind12004::module_relative:
      if(p.observed_raw || !p.relative_offset_or_rva || module_base>(std::numeric_limits<std::uintptr_t>::max)()-*p.relative_offset_or_rva)return false;
      numeric=module_base+*p.relative_offset_or_rva;break;
    default:return false;
  }
  if(numeric)Number(out,p.member_offset,static_cast<std::uint64_t>(*numeric));
  else for(std::size_t i=p.member_offset;i<p.member_offset+8;++i) {
    out.raw[i]=0;out.source_defined[i]=1;out.numeric_known[i]=0;
  }
  for(const auto &existing:out.pointers)if(existing.member_offset==p.member_offset)return false;
  out.pointers.push_back(p);return true;
}
inline bool ApplyChild(PrisonerRansomScopeRaw12004 &out,const PrisonerQuoteSourceFrame12004 &frame,
    const PrisonerRansomScopeChildPostimage12004 &child,std::uintptr_t callee,std::uintptr_t callsite,
    std::size_t begin,std::size_t end) {
  if(!child.minimum_returned_fields_source_ready || child.frame!=frame ||
     child.actual_callee_rva!=callee || child.actual_callsite_rva!=callsite ||
     child.source_member_offset!=begin || child.destination_member_offset!=begin)return false;
  PrisonerRansomScopeRaw12004 fragment;
  for(const auto &write:child.byte_writes) {
    if(write.bytes.empty() || !Range(write.scope_member_offset,write.bytes.size(),begin,end))return false;
    for(std::size_t i=write.scope_member_offset;i<write.scope_member_offset+write.bytes.size();++i)
      if(fragment.source_defined[i])return false;
    Bytes(fragment,write.scope_member_offset,write.bytes.data(),write.bytes.size());
  }
  for(const auto &pointer:child.pointers) {
    if(!Range(pointer.member_offset,8,begin,end))return false;
    for(std::size_t i=pointer.member_offset;i<pointer.member_offset+8;++i)
      if(fragment.source_defined[i])return false;
    if(!Pointer(fragment,pointer,frame.module_base))return false;
  }
  for(std::size_t i=begin;i<end;++i)if(fragment.source_defined[i]) {
    out.raw[i]=fragment.raw[i];out.source_defined[i]=1;out.numeric_known[i]=fragment.numeric_known[i];
  }
  out.pointers.insert(out.pointers.end(),fragment.pointers.begin(),fragment.pointers.end());
  return true;
}
} // namespace prisoner_ransom_scope_clone_detail

inline PrisonerRansomScopeCloneInputs12004 ReadPrisonerRansomScopeCloneInputs12004(
    const PrisonerQuoteReadOnlyAccess12004 &access,const PrisonerQuoteSourceFrame12004 &frame) {
  PrisonerRansomScopeCloneInputs12004 out;out.frame=frame;
  if(!PrisonerQuoteSourceFrameReady12004(frame) ||
     frame.interaction_context_identity>(std::numeric_limits<std::uintptr_t>::max)()-8 ||
     frame.original_scope_identity!=frame.interaction_context_identity+8)return out;
  if(access.read_memory && frame.original_scope_identity<=(std::numeric_limits<std::uintptr_t>::max)()-20)
    out.original_header_copied=access.read_memory(access.context,reinterpret_cast<const void *>(frame.original_scope_identity),
                                                out.original_header.data(),out.original_header.size());
  if(out.original_header_copied) {
    std::array<std::uint8_t,20> after{};
    out.original_header_copied=access.read_memory(access.context,reinterpret_cast<const void *>(frame.original_scope_identity),
                                                 after.data(),after.size()) && after==out.original_header;
  }
  out.loaded_evaluation_flag=ReadPrisonerQuoteSource12004<std::uint8_t>(access,frame.module_base,0x5D1DADC);
  out.context_recipient_full_id=ReadPrisonerQuoteSource12004<std::uint32_t>(
      access,frame.interaction_context_identity,0x2E8);
  return out;
}
inline PrisonerRansomScopeCloneSource12004 ProjectPrisonerRansomScopeClone12004(
    const PrisonerRansomScopeCloneInputs12004 &input,
    const PrisonerRansomScopeChildPostimage12004 &vector100={},
    const PrisonerRansomScopeChildPostimage12004 &vector18={},
    const PrisonerRansomScopeChildPostimage12004 &support118={}) {
  using namespace prisoner_ransom_scope_clone_detail;
  PrisonerRansomScopeCloneSource12004 out;out.frame=input.frame;
  if(!PrisonerQuoteSourceFrameReady12004(input.frame) ||
     input.frame.interaction_context_identity>(std::numeric_limits<std::uintptr_t>::max)()-8 ||
     input.frame.original_scope_identity!=input.frame.interaction_context_identity+8 || !input.original_header_copied ||
     input.context_recipient_full_id!=input.frame.recipient_full_id ||
     *input.context_recipient_full_id==std::uint32_t{0xFFFFFFFF}) {
    out.unavailable_reason="ransom_scope_original_header_or_frame_unavailable";return out;
  }
  Bytes(out.returned_scope,0,input.original_header.data(),input.original_header.size());
  Number(out.returned_scope,0,std::uint16_t{4});
  Number(out.returned_scope,8,static_cast<std::uint64_t>(*input.frame.recipient_full_id));
  out.header_copy_source_ready=true;
  const bool copied100=ApplyChild(out.returned_scope,input.frame,vector100,0x37282B0,0x373ADA1,0x100,0x118);
  const bool copied18=ApplyChild(out.returned_scope,input.frame,vector18,0x260E040,0x373ADAE,0x18,0x100);
  const bool copied118=ApplyChild(out.returned_scope,input.frame,support118,0x3727180,0x373ADBD,0x118,0x168);
  out.primary_and_tertiary_are_same_logical_clone=true;
  out.support_is_logical_clone_plus118=true;
  // Only the actual internal null/evaluation byte and source-defined root are
  // supplied. No source pointer or local DTO address becomes the native clone.
  out.internal_aliases.secondary_scope=std::uintptr_t{0};
  out.internal_aliases.evaluation_flag_raw_u8=input.loaded_evaluation_flag;
  out.internal_aliases.primary_scope_root_word=std::uint16_t{4};
  bool minimum_fields=Defined(out.returned_scope,0,20) &&
      Defined(out.returned_scope,0x18,0x20) && Defined(out.returned_scope,0xF8,8) &&
      Defined(out.returned_scope,0x100,0x18) && Defined(out.returned_scope,0x118,0x2C) &&
      Defined(out.returned_scope,0x148,0x1F);
  if(minimum_fields) {
    std::int32_t inline_count=0;
    for(std::size_t i=0x24;i<0x28;++i)minimum_fields=minimum_fields && out.returned_scope.numeric_known[i]!=0;
    if(minimum_fields)std::memcpy(&inline_count,out.returned_scope.raw.data()+0x24,sizeof(inline_count));
    if(inline_count>8)minimum_fields=false;
    else if(inline_count>0)
      minimum_fields=minimum_fields && Defined(out.returned_scope,0x38,static_cast<std::size_t>(inline_count)*24);
  }
  out.source_equivalent_clone_shape_ready=copied100 && copied18 && copied118 && minimum_fields;
  if(!out.source_equivalent_clone_shape_ready)
    out.unavailable_reason="ransom_scope_child_returned_fields_source_unavailable";
  return out;
}
template<class T> inline std::optional<T> ReadPrisonerRansomScopeRawScalar12004(
    const PrisonerRansomScopeRaw12004 &scope,std::size_t offset) noexcept {
  static_assert(std::is_integral_v<T>);
  if(!prisoner_ransom_scope_clone_detail::Range(offset,sizeof(T)))return {};
  for(std::size_t i=offset;i<offset+sizeof(T);++i)if(!scope.numeric_known[i])return {};
  T value{};std::memcpy(&value,scope.raw.data()+offset,sizeof(T));return value;
}
inline std::optional<PrisonerRansomScopePointer12004> ReadPrisonerRansomScopePointer12004(
    const PrisonerRansomScopeRaw12004 &scope,std::size_t offset) {
  for(const auto &p:scope.pointers)if(p.member_offset==offset)return p;
  return {};
}

// The owner46 postimage and reused48 initializer define this exact no-allocation
// vector relation. Growth remains unavailable without a physical result witness.
PrisonerRansomScopeChildPostimage12004 ProjectPrisonerRansomScopeVector18Child12004(
    const PrisonerScopeVectorCopy260E04012004 &source);
PrisonerRansomScopeChildPostimage12004 ProjectPrisonerRansomScopeVector100Child12004(
    const PrisonerScopeCloneVector10012004 &source);
PrisonerRansomScopeChildPostimage12004 ProjectPrisonerRansomScopeSupport118Child12004(
    const PrisonerScopeCloneSupport118Source12004 &source);

// Reads only the minimum accepted fields/cells in the existing copied query.
// Positive vector100 input retains count/data but does not build unused record
// lists. Its allocation and returned data identity remain unavailable.
PrisonerRansomScopeCloneSource12004 ReadPrisonerRansomScopeClone12004(
    const PrisonerQuoteReadOnlyAccess12004 &access,const PrisonerQuoteSourceFrame12004 &frame);

} // namespace xar::ck3_12004
