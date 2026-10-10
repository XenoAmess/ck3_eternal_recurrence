#include "xar_bridge/prisoner_trigger_root_scope_gate_12004.hpp"
#include <cstring>
#include <stdexcept>

namespace xar::ck3_12004 {
namespace {
void RequireSourceGate63c(bool condition,const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}
struct SourceGateMemory63c {
  std::uint16_t word=4;
  std::uintptr_t vptr=0x8000,slot58=0x111111,slot60=0x222222;
  int reads=0;
  bool root_missing=false;
};
bool ReadSourceGate63c(void *context,const void *address,void *out,std::size_t size) noexcept {
  auto &memory=*static_cast<SourceGateMemory63c *>(context); ++memory.reads;
  const auto raw=reinterpret_cast<std::uintptr_t>(address);
  if (raw==0x6000 && size==sizeof(memory.word) && !memory.root_missing) {
    std::memcpy(out,&memory.word,size); return true;
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
SourceLeafFrame12004 SourceFrame63c() {
  SourceLeafFrame12004 frame{};
  frame.read_frame.executable_sha256=kPrisonerQuoteSourceExecutableSha25612004;
  frame.read_frame.module_base=0x100000; frame.read_frame.frame_identity=0x5000;
  frame.read_frame.native_revision=1; frame.read_frame.query_sequence=2;
  frame.read_frame.proof_epoch=3; frame.read_frame.date_raw=4;
  frame.read_frame.caller_domain="lifestyle"; frame.read_frame.caller_snapshot_confirmed=true;
  frame.producer_rva=0x372B4C0; frame.receiver_identity=0x7000;
  frame.primary_scope_identity=0x6000; frame.primary_scope_root_word=std::uint16_t{4};
  return frame;
}
}
// A new parent compound invokes this fragment. It does not replay the old
// twelve math vectors, add prisoner roles, invoke a getter, or define a main.
void RunSourceTriggerRootScopeGate12004Cases() {
  SourceGateMemory63c memory{};
  const SourceLeafReadOnlyAccess12004 access{&memory,&ReadSourceGate63c};
  const auto frame=SourceFrame63c();
  const auto raw=ReadPrisonerTriggerRootScopeGate12004(access,frame);
  RequireSourceGate63c(raw.raw_copy_ready && raw.frame==frame && raw.trigger_identity==frame.receiver_identity && raw.primary_scope_identity==frame.primary_scope_identity,"63c generic caller and leaf identities preserved");
  RequireSourceGate63c(raw.root_scope_kind_raw_u16==4 && raw.slot58_address_raw==0x111111 && raw.slot60_address_raw==0x222222,"63c generic guarded raw copies");
  RequireSourceGate63c(!raw.qualified_ready && !raw.getter_output_source_ready && !raw.returned_byte && !raw.conditional_allows,"63c generic raw slot addresses remain unqualified");
  auto invalid=frame; invalid.read_frame.caller_snapshot_confirmed=false;
  const auto before=memory.reads;
  RequireSourceGate63c(!ReadPrisonerTriggerRootScopeGate12004(access,invalid).raw_copy_ready && memory.reads==before,"63c unconfirmed generic snapshot does not read");
  invalid=frame; invalid.producer_rva=0x372B4C1;
  RequireSourceGate63c(!ReadPrisonerTriggerRootScopeGate12004(access,invalid).raw_copy_ready && memory.reads==before,"63c generic producer mismatch does not read");
  invalid=frame; invalid.primary_scope_identity=0;
  RequireSourceGate63c(!ReadPrisonerTriggerRootScopeGate12004(access,invalid).raw_copy_ready && memory.reads==before,"63c absent generic scope identity does not read");
  invalid=frame; invalid.primary_scope_root_word=std::uint16_t{5};
  const auto mismatch=ReadPrisonerTriggerRootScopeGate12004(access,invalid);
  RequireSourceGate63c(!mismatch.raw_copy_ready && mismatch.root_scope_kind_raw_u16==4 && !mismatch.returned_byte,"63c mismatched copied scope word retains partial raw input only");
  memory.root_missing=true;
  const auto partial=ReadPrisonerTriggerRootScopeGate12004(access,frame);
  RequireSourceGate63c(!partial.raw_copy_ready && !partial.root_scope_kind_raw_u16 && !partial.returned_byte,"63c missing generic scope word remains unknown");
  SourceTriggerRootScopeGateConditionalInput12004 input{};
  input.frame=frame; input.root_scope_kind_raw_u16=std::uint16_t{4}; input.preferred_kind_return_ax_raw_u16=std::uint16_t{4};
  const auto conditional=ProjectPrisonerTriggerRootScopeGate12004(input);
  RequireSourceGate63c(conditional.frame==frame && conditional.conditional_result_ready && !conditional.qualified_ready && !conditional.getter_output_source_ready && !conditional.returned_byte,"63c generic projection shares conditional core without qualification");
  input.frame.primary_scope_root_word=std::uint16_t{5};
  RequireSourceGate63c(!ProjectPrisonerTriggerRootScopeGate12004(input).conditional_allows,"63c generic projection refuses scope word mismatch");
}
} // namespace xar::ck3_12004
