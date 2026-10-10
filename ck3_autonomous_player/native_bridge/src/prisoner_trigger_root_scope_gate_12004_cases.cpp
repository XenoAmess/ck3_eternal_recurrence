#include "xar_bridge/prisoner_trigger_root_scope_gate_12004.hpp"
#include <cstring>
#include <stdexcept>

namespace xar::ck3_12004 {
namespace {
void Require63c(bool condition,const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}
struct GateMemory63c {
  std::uint16_t root = 4;
  std::uintptr_t vptr = 0x8000, slot58 = 0x111111, slot60 = 0x222222;
  int reads = 0;
  bool fail_root = false;
};
bool ReadGate63c(void *context,const void *address,void *out,std::size_t size) noexcept {
  auto &memory=*static_cast<GateMemory63c *>(context); ++memory.reads;
  const auto raw=reinterpret_cast<std::uintptr_t>(address);
  if (raw==0x6000 && size==sizeof(memory.root) && !memory.fail_root) {
    std::memcpy(out,&memory.root,size); return true;
  }
  if (raw==0x7000 && size==sizeof(memory.vptr)) {
    std::memcpy(out,&memory.vptr,size); return true;
  }
  if (raw==0x8058 && size==sizeof(memory.slot58)) {
    std::memcpy(out,&memory.slot58,size); return true;
  }
  if (raw==0x8060 && size==sizeof(memory.slot60)) {
    std::memcpy(out,&memory.slot60,size); return true;
  }
  return false;
}
PrisonerQuoteSourceFrame12004 Frame63c() {
  PrisonerQuoteSourceFrame12004 out{};
  out.executable_sha256=kPrisonerQuoteSourceExecutableSha25612004;
  out.module_base=0x100000; out.native_revision=1; out.query_sequence=2; out.proof_epoch=3;
  out.date_raw=4; out.jailer_full_id=5; out.prisoner_full_id=6; out.recipient_full_id=7;
  out.definition_identity=0x4000; out.interaction_context_identity=0x5000;
  out.original_scope_identity=0x6000; out.roles_verified_in_owned_context=true; out.same_frame_confirmed=true;
  return out;
}
}
// Parent35 owns the sole new connected-quote main/recipe. These are fresh
// source gate cases only, with no native callback, new clock or independent main.
void RunPrisonerTriggerRootScopeGate12004Cases() {
  GateMemory63c memory{};
  PrisonerQuoteReadOnlyAccess12004 access{&memory,&ReadGate63c};
  const auto frame=Frame63c();
  auto raw=ReadPrisonerTriggerRootScopeGate12004(access,frame,0x7000,0x6000);
  Require63c(raw.raw_copy_ready && raw.root_scope_kind_raw_u16==4 && raw.slot58_address_raw==0x111111 && raw.slot60_address_raw==0x222222,"63c raw source fields");
  Require63c(raw.frame==frame && raw.trigger_identity==0x7000 && raw.primary_scope_identity==0x6000,"63c copied frame identities");
  Require63c(!raw.qualified_ready && !raw.getter_output_source_ready && !raw.returned_byte && !raw.conditional_allows,"63c addresses cannot produce getter truth");
  auto bad_frame=frame; bad_frame.same_frame_confirmed=false;
  const auto before=memory.reads;
  Require63c(!ReadPrisonerTriggerRootScopeGate12004(access,bad_frame,0x7000,0x6000).raw_copy_ready && memory.reads==before,"63c invalid frame does not read");
  Require63c(!ReadPrisonerTriggerRootScopeGate12004(access,frame,0x7000,0x6001).raw_copy_ready && memory.reads==before,"63c root identity mismatch does not read");
  memory.fail_root=true;
  Require63c(!ReadPrisonerTriggerRootScopeGate12004(access,frame,0x7000,0x6000).root_scope_kind_raw_u16,"63c partial root remains unknown");
  PrisonerTriggerRootScopeGateConditionalInput12004 input{};
  input.frame=frame; input.trigger_identity=0x7000; input.primary_scope_identity=0x6000;
  const auto check=[&](std::uint16_t root,std::uint16_t preferred,
      std::optional<std::array<std::uint64_t,2>> mask,std::optional<bool> expected) {
    input.root_scope_kind_raw_u16=root; input.preferred_kind_return_ax_raw_u16=preferred;
    input.mask_return_words_raw_u64=mask;
    const auto projected=ProjectPrisonerTriggerRootScopeGate12004(input);
    Require63c(projected.conditional_allows==expected && projected.conditional_result_ready==expected.has_value(),"63c exact source conditional branch");
    Require63c(!projected.qualified_ready && !projected.getter_output_source_ready && !projected.returned_byte,"63c supplied conditional values cannot qualify native result");
  };
  // Independent expected branches from the held native instructions: no loop
  // over implementation output, no callback result injection into production.
  check(4,4,std::nullopt,true);
  check(4,0,std::array<std::uint64_t,2>{0,0},true);
  check(0,0,std::array<std::uint64_t,2>{1,0},false);
  check(1,0,std::array<std::uint64_t,2>{1,0},true);
  check(64,0,std::array<std::uint64_t,2>{1ULL<<63,0},true);
  check(65,0,std::array<std::uint64_t,2>{0,1},true);
  check(128,0,std::array<std::uint64_t,2>{0,1ULL<<63},true);
  check(127,0,std::array<std::uint64_t,2>{0,1ULL<<63},false);
  check(129,0,std::array<std::uint64_t,2>{1,0},std::nullopt);
  check(129,129,std::nullopt,true);
  check(65535,0,std::array<std::uint64_t,2>{0,0},true);
  check(1,0,std::nullopt,std::nullopt);
  input.preferred_kind_return_ax_raw_u16.reset();
  Require63c(!ProjectPrisonerTriggerRootScopeGate12004(input).conditional_allows,"63c absent preferred getter stays unknown");
}
} // namespace xar::ck3_12004
