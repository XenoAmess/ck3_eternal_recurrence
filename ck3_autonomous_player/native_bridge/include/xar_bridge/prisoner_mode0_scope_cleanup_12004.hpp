#pragma once
#include "xar_bridge/prisoner_quote_readonly_source_12004.hpp"
#include <array>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kPrisonerMode0CleanupScalarRva12004=0x307C340;
inline constexpr std::uintptr_t kPrisonerMode0CleanupScoreReturnRva12004=0x307C3A9;
inline constexpr std::uintptr_t kPrisonerMode0CleanupCallRva12004=0x307C3B2;
inline constexpr std::array<std::size_t,4> kPrisonerMode0CleanupPointerOffsets12004{0x18,0x100,0x128,0x148};
enum class PrisonerMode0CleanupInputKind12004 : std::uint8_t {
  unavailable,actual_stack_scope,source_equivalent_cleanup_entry_shape
};
enum class PrisonerMode0Scope18CleanupPath12004 : std::uint8_t {
  unavailable,null_buffer,inline_allocator_855830
};
struct PrisonerMode0ScopeCleanupInputs12004 {
  PrisonerQuoteSourceFrame12004 frame;
  PrisonerMode0CleanupInputKind12004 kind=PrisonerMode0CleanupInputKind12004::unavailable;
  std::uintptr_t actual_scalar_helper_rva=0,actual_score_return_rva=0,actual_cleanup_callsite_rva=0;
  // Actual or source-equivalent *post-wrapper* shape, never constructor zeros.
  bool same_frame_cleanup_entry_shape_ready=false;
  std::optional<std::uintptr_t> physical_scope_identity,actual_body_rsp_identity,original_out_q64_identity;
  std::array<std::optional<std::uintptr_t>,4> scope_buffer_qwords{};
  PrisonerMode0Scope18CleanupPath12004 scope18_path=PrisonerMode0Scope18CleanupPath12004::unavailable;
  // Source-equivalent shapes describe a NONNULL self-relative pointer without
  // inventing its physical address. Physical captures validate the raw aliases.
  std::optional<std::size_t> scope18_data_relative_offset,scope18_allocator_relative_offset;
  std::optional<std::uintptr_t> scope18_allocator_identity,scope18_allocator_vtable_rva,scope18_free_target_rva;
  std::optional<std::uint64_t> before_out_q64_bits;
};
struct PrisonerMode0ScopeCleanupProjection12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::optional<std::uint64_t> preserved_out_q64_bits;
  bool null_cleanup_path_source_ready=false;
  bool inline_scope18_release_source_ready=false,scope18_count_cleared=false;
  bool cleanup_effects_source_ready=false;
  bool native_cleanup_called=false,actual_native_output_observed=false;
  std::string unavailable_reason;
};
inline PrisonerMode0ScopeCleanupProjection12004 ProjectPrisonerMode0ScopeCleanup12004(
    const PrisonerMode0ScopeCleanupInputs12004 &input) {
  PrisonerMode0ScopeCleanupProjection12004 out{};out.frame=input.frame;
  const auto fail=[&](const char *reason){out.unavailable_reason=reason;return out;};
  if(!PrisonerQuoteSourceFrameReady12004(input.frame) || !input.same_frame_cleanup_entry_shape_ready ||
     input.actual_scalar_helper_rva!=kPrisonerMode0CleanupScalarRva12004 ||
     input.actual_score_return_rva!=kPrisonerMode0CleanupScoreReturnRva12004 ||
     input.actual_cleanup_callsite_rva!=kPrisonerMode0CleanupCallRva12004)
    return fail("mode0_cleanup_entry_frame_unavailable");
  if(input.kind==PrisonerMode0CleanupInputKind12004::actual_stack_scope) {
    if(!input.actual_body_rsp_identity || !*input.actual_body_rsp_identity || !input.physical_scope_identity ||
       !input.original_out_q64_identity || !*input.original_out_q64_identity ||
       *input.actual_body_rsp_identity>(std::numeric_limits<std::uintptr_t>::max)()-0x1A0 ||
       *input.physical_scope_identity!=*input.actual_body_rsp_identity+0x20 ||
       *input.original_out_q64_identity<*input.actual_body_rsp_identity+0x1A0 ||
       *input.original_out_q64_identity>(std::numeric_limits<std::uintptr_t>::max)()-8)
      return fail("mode0_cleanup_physical_scope_or_output_stack_alias_unavailable");
  }else if(input.kind==PrisonerMode0CleanupInputKind12004::source_equivalent_cleanup_entry_shape) {
    if(input.physical_scope_identity || input.actual_body_rsp_identity || input.original_out_q64_identity)
      return fail("mode0_cleanup_copied_shape_has_invented_physical_alias");
  }else return fail("mode0_cleanup_input_kind_unavailable");
  for(std::size_t index=1;index<input.scope_buffer_qwords.size();++index) {
    const auto &raw=input.scope_buffer_qwords[index];
    if(!raw)return fail("mode0_cleanup_post_wrapper_pointer_unavailable");
    if(*raw!=0)return fail("mode0_cleanup_nonempty_effect_path_unavailable");
  }
  if(input.scope18_path==PrisonerMode0Scope18CleanupPath12004::null_buffer) {
    if(!input.scope_buffer_qwords[0])return fail("mode0_cleanup_post_wrapper_pointer_unavailable");
    if(*input.scope_buffer_qwords[0]!=0)return fail("mode0_cleanup_nonempty_effect_path_unavailable");
    out.null_cleanup_path_source_ready=true;
  }else if(input.scope18_path==PrisonerMode0Scope18CleanupPath12004::inline_allocator_855830) {
    if(input.scope18_data_relative_offset!=std::size_t{0x38} ||
       input.scope18_allocator_relative_offset!=std::size_t{0x30} ||
       input.scope18_allocator_vtable_rva!=std::uintptr_t{0x448D2A0} ||
       input.scope18_free_target_rva!=std::uintptr_t{0x855830})
      return fail("mode0_cleanup_inline_allocator_relation_unavailable");
    if(input.kind==PrisonerMode0CleanupInputKind12004::actual_stack_scope) {
      if(input.scope_buffer_qwords[0]!=*input.physical_scope_identity+0x38 ||
         input.scope18_allocator_identity!=*input.physical_scope_identity+0x30)
        return fail("mode0_cleanup_inline_physical_alias_mismatch");
    }else if(input.scope_buffer_qwords[0] || input.scope18_allocator_identity)
      return fail("mode0_cleanup_inline_copied_shape_has_invented_pointer_bits");
    // RCX=scope+30,RDX=scope+38 ->855844 equality ->85585F ->RET.
    // Caller307C403 clears only DWORDscope+24 before that no-effect release.
    out.inline_scope18_release_source_ready=true;out.scope18_count_cleared=true;
  }else return fail("mode0_cleanup_scope18_path_unavailable");
  if(!input.before_out_q64_bits)return fail("mode0_cleanup_before_output_bits_unavailable");
  // 889700/direct889780 paths are skipped. Scope18 is either NULL or the exact
  // inline855830 equality arm. No actual cleanup/allocator call is executed.
  out.preserved_out_q64_bits=input.before_out_q64_bits;
  out.cleanup_effects_source_ready=true;
  return out;
}
// Caller supplies an actual post-wrapper boundary binding. An ordinary query
// must not call this reader with the original source scope in place of a clone.
inline PrisonerMode0ScopeCleanupInputs12004 ReadPrisonerMode0ScopeCleanup12004(
    const PrisonerQuoteReadOnlyAccess12004 &access,PrisonerMode0ScopeCleanupInputs12004 boundary) {
  if(boundary.kind!=PrisonerMode0CleanupInputKind12004::actual_stack_scope ||
     !PrisonerQuoteSourceFrameReady12004(boundary.frame) || !boundary.same_frame_cleanup_entry_shape_ready ||
     boundary.actual_scalar_helper_rva!=kPrisonerMode0CleanupScalarRva12004 ||
     boundary.actual_score_return_rva!=kPrisonerMode0CleanupScoreReturnRva12004 ||
     boundary.actual_cleanup_callsite_rva!=kPrisonerMode0CleanupCallRva12004 ||
     !boundary.actual_body_rsp_identity || !*boundary.actual_body_rsp_identity || !boundary.physical_scope_identity ||
     *boundary.actual_body_rsp_identity>(std::numeric_limits<std::uintptr_t>::max)()-0x1A0 ||
     *boundary.physical_scope_identity!=*boundary.actual_body_rsp_identity+0x20 ||
     !boundary.original_out_q64_identity || *boundary.original_out_q64_identity<*boundary.actual_body_rsp_identity+0x1A0) {
    boundary.same_frame_cleanup_entry_shape_ready=false;
    boundary.scope_buffer_qwords={};boundary.before_out_q64_bits.reset();return boundary;
  }
  for(std::size_t i=0;i<boundary.scope_buffer_qwords.size();++i)
    boundary.scope_buffer_qwords[i]=ReadPrisonerQuoteSource12004<std::uintptr_t>(access,
      *boundary.physical_scope_identity,kPrisonerMode0CleanupPointerOffsets12004[i]);
  boundary.scope18_path=PrisonerMode0Scope18CleanupPath12004::unavailable;
  boundary.scope18_data_relative_offset.reset();boundary.scope18_allocator_relative_offset.reset();
  boundary.scope18_allocator_identity.reset();boundary.scope18_allocator_vtable_rva.reset();boundary.scope18_free_target_rva.reset();
  if(boundary.scope_buffer_qwords[0]==std::uintptr_t{0})
    boundary.scope18_path=PrisonerMode0Scope18CleanupPath12004::null_buffer;
  else if(boundary.scope_buffer_qwords[0]==*boundary.physical_scope_identity+0x38) {
    boundary.scope18_allocator_identity=ReadPrisonerQuoteSource12004<std::uintptr_t>(access,*boundary.physical_scope_identity,0x28);
    if(boundary.scope18_allocator_identity==*boundary.physical_scope_identity+0x30) {
      boundary.scope18_data_relative_offset=0x38;boundary.scope18_allocator_relative_offset=0x30;
      const auto vtable=ReadPrisonerQuoteSource12004<std::uintptr_t>(access,*boundary.scope18_allocator_identity);
      if(vtable && *vtable>=boundary.frame.module_base) {
        boundary.scope18_allocator_vtable_rva=*vtable-boundary.frame.module_base;
        const auto target=ReadPrisonerQuoteSource12004<std::uintptr_t>(access,*vtable,0x10);
        if(target && *target>=boundary.frame.module_base)
          boundary.scope18_free_target_rva=*target-boundary.frame.module_base;
      }
      boundary.scope18_path=PrisonerMode0Scope18CleanupPath12004::inline_allocator_855830;
    }
  }
  boundary.before_out_q64_bits=ReadPrisonerQuoteSource12004<std::uint64_t>(access,*boundary.original_out_q64_identity);
  return boundary;
}
} // namespace xar::ck3_12004
