#include "xar_bridge/prisoner_mode0_scope_cleanup_12004.hpp"
#include <cstring>
#include <stdexcept>
namespace {
using namespace xar::ck3_12004;
void Require(bool ok,const char *reason){if(!ok)throw std::runtime_error(reason);}
PrisonerMode0ScopeCleanupInputs12004 BoundShape() {
  PrisonerMode0ScopeCleanupInputs12004 in{};
  in.frame.executable_sha256=kPrisonerQuoteSourceExecutableSha25612004;
  in.frame.module_base=0x140000000;in.frame.native_revision=73;in.frame.query_sequence=1;in.frame.proof_epoch=1;
  in.frame.date_raw=7;in.frame.jailer_full_id=0x01000001;in.frame.prisoner_full_id=0x02000002;in.frame.recipient_full_id=0x03000003;
  in.frame.definition_identity=0x500000;in.frame.interaction_context_identity=0x600000;in.frame.original_scope_identity=0x600008;
  in.frame.roles_verified_in_owned_context=true;in.frame.same_frame_confirmed=true;
  in.kind=PrisonerMode0CleanupInputKind12004::source_equivalent_cleanup_entry_shape;
  in.actual_scalar_helper_rva=0x307C340;in.actual_score_return_rva=0x307C3A9;in.actual_cleanup_callsite_rva=0x307C3B2;
  in.same_frame_cleanup_entry_shape_ready=true;
  in.scope18_path=PrisonerMode0Scope18CleanupPath12004::null_buffer;
  for(auto &q:in.scope_buffer_qwords)q=0;
  in.before_out_q64_bits=0xFEDCBA9876543210ULL;return in;
}
struct Memory {std::array<std::uint8_t,0x240> bytes{};bool fail148=false,inline_slots=false;std::size_t reads=0;};
bool Read(void *context,const void *address,void *out,std::size_t size) noexcept {
  auto &m=*static_cast<Memory *>(context);++m.reads;
  const auto p=reinterpret_cast<std::uintptr_t>(address),begin=reinterpret_cast<std::uintptr_t>(m.bytes.data());
  if(m.inline_slots && p==0x140000000ULL+0x448D2B0 && size==8) {
    const std::uintptr_t target=0x140000000ULL+0x855830;std::memcpy(out,&target,8);return true;
  }
  if(p<begin || p-begin>m.bytes.size() || size>m.bytes.size()-(p-begin) || (m.fail148 && p==begin+0x20+0x148))return false;
  std::memcpy(out,address,size);return true;
}
}
void RunPrisonerMode0ScopeCleanupFocus12004() {
  auto shape=BoundShape();const auto closed=ProjectPrisonerMode0ScopeCleanup12004(shape);
  Require(closed.cleanup_effects_source_ready && closed.preserved_out_q64_bits==shape.before_out_q64_bits &&
    !closed.native_cleanup_called && !closed.actual_native_output_observed,"closed NULL cleanup shape did not preserve exact unsigned output bits");
  for(std::size_t i=0;i<4;++i) {
    auto missing=shape;missing.scope_buffer_qwords[i].reset();const auto unknown=ProjectPrisonerMode0ScopeCleanup12004(missing);
    Require(!unknown.cleanup_effects_source_ready && !unknown.preserved_out_q64_bits,"missing post-wrapper pointer became constructor zero");
    auto nonempty=shape;nonempty.scope_buffer_qwords[i]=0x100000;const auto pending=ProjectPrisonerMode0ScopeCleanup12004(nonempty);
    Require(!pending.cleanup_effects_source_ready && !pending.preserved_out_q64_bits,"nonempty destructor/free path inherited NULL output preservation");
  }
  auto initialized_only=shape;initialized_only.same_frame_cleanup_entry_shape_ready=false;
  Require(!ProjectPrisonerMode0ScopeCleanup12004(initialized_only).cleanup_effects_source_ready,"initialization zeros were treated as a post-wrapper witness");
  auto wrong=shape;wrong.actual_score_return_rva++;
  Require(!ProjectPrisonerMode0ScopeCleanup12004(wrong).preserved_out_q64_bits,"wrong return boundary admitted cleanup witness");
  auto unavailable_output=shape;unavailable_output.before_out_q64_bits.reset();const auto noout=ProjectPrisonerMode0ScopeCleanup12004(unavailable_output);
  Require(noout.null_cleanup_path_source_ready && !noout.cleanup_effects_source_ready && !noout.preserved_out_q64_bits,"output read failure erased independent NULL path or invented output");
  auto fabricated_alias=shape;fabricated_alias.physical_scope_identity=0x700000;
  Require(!ProjectPrisonerMode0ScopeCleanup12004(fabricated_alias).cleanup_effects_source_ready,"copied shape invented physical clone alias");
  auto inline_shape=shape;inline_shape.scope18_path=PrisonerMode0Scope18CleanupPath12004::inline_allocator_855830;
  inline_shape.scope_buffer_qwords[0].reset();inline_shape.scope18_data_relative_offset=0x38;
  inline_shape.scope18_allocator_relative_offset=0x30;inline_shape.scope18_allocator_vtable_rva=0x448D2A0;inline_shape.scope18_free_target_rva=0x855830;
  const auto inline_closed=ProjectPrisonerMode0ScopeCleanup12004(inline_shape);
  Require(inline_closed.cleanup_effects_source_ready && inline_closed.inline_scope18_release_source_ready && inline_closed.scope18_count_cleared &&
    !inline_closed.null_cleanup_path_source_ready && inline_closed.preserved_out_q64_bits==shape.before_out_q64_bits,"NONNULL relational inline cleanup became NULL or lost preserved output");
  auto foreign=inline_shape;foreign.scope18_data_relative_offset=0x40;
  Require(!ProjectPrisonerMode0ScopeCleanup12004(foreign).cleanup_effects_source_ready,"unequal pointer branch inherited inline no-effect release");
  foreign=inline_shape;foreign.scope18_free_target_rva=0x8571C0;
  Require(!ProjectPrisonerMode0ScopeCleanup12004(foreign).cleanup_effects_source_ready,"other free target inherited855830 equality proof");
  foreign=inline_shape;foreign.scope_buffer_qwords[0]=0;
  Require(!ProjectPrisonerMode0ScopeCleanup12004(foreign).cleanup_effects_source_ready,"logical inline backing was forged as physical NULL");
  Memory memory{};std::uint64_t value=*shape.before_out_q64_bits;std::memcpy(memory.bytes.data()+0x1A0,&value,sizeof value);
  auto physical=shape;physical.kind=PrisonerMode0CleanupInputKind12004::actual_stack_scope;
  physical.actual_body_rsp_identity=reinterpret_cast<std::uintptr_t>(memory.bytes.data());
  physical.physical_scope_identity=*physical.actual_body_rsp_identity+0x20;
  physical.original_out_q64_identity=*physical.actual_body_rsp_identity+0x1A0;
  PrisonerQuoteReadOnlyAccess12004 access{};access.context=&memory;access.read_memory=&Read;
  auto read=ReadPrisonerMode0ScopeCleanup12004(access,physical);
  const auto actual=ProjectPrisonerMode0ScopeCleanup12004(read);
  Require(memory.reads==5 && actual.cleanup_effects_source_ready && actual.preserved_out_q64_bits==value,"bounded physical reader did not use four pointers plus exact output QWORD");
  memory.fail148=true;read=ReadPrisonerMode0ScopeCleanup12004(access,physical);
  Require(read.before_out_q64_bits==value && !ProjectPrisonerMode0ScopeCleanup12004(read).preserved_out_q64_bits,"physical pointer fault converted to NULL or changed independent output read");
  memory.fail148=false;memory.inline_slots=true;
  const auto scope=*physical.physical_scope_identity;
  const std::uintptr_t data=scope+0x38,allocator=scope+0x30,vtable=0x140000000ULL+0x448D2A0;
  std::memcpy(memory.bytes.data()+0x38,&data,8);std::memcpy(memory.bytes.data()+0x48,&allocator,8);std::memcpy(memory.bytes.data()+0x50,&vtable,8);
  read=ReadPrisonerMode0ScopeCleanup12004(access,physical);const auto physical_inline=ProjectPrisonerMode0ScopeCleanup12004(read);
  Require(physical_inline.inline_scope18_release_source_ready && physical_inline.preserved_out_q64_bits==value,"physical allocator/data equality arm did not validate exact loaded target");
  physical.original_out_q64_identity=*physical.actual_body_rsp_identity+8;
  Require(!ProjectPrisonerMode0ScopeCleanup12004(physical).cleanup_effects_source_ready,"callee saved-register/output stack alias admitted");
  auto stale=shape;stale.frame.same_frame_confirmed=false;
  Require(!ProjectPrisonerMode0ScopeCleanup12004(stale).cleanup_effects_source_ready,"unbound query frame admitted lifetime projection");
}
