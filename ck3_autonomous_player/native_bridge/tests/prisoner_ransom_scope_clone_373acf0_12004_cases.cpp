#include "xar_bridge/prisoner_ransom_scope_clone_373acf0_12004.hpp"
#include <stdexcept>

namespace xar::ck3_12004 {
namespace {
void Require(bool value,const char *reason) { if(!value)throw std::runtime_error(reason); }
struct Memory {
  static constexpr std::uintptr_t module=0x100000000ULL,context=0x200000000ULL,cells=0x400000000ULL;
  std::array<std::uint8_t,0x300> context_bytes{};
  std::array<std::uint8_t,192> cell_bytes{};
  std::uint8_t flag=0xA5;
  bool change_header=false;
  std::size_t header_reads=0;
  template<class T> void Put(std::size_t offset,T value) {
    std::memcpy(context_bytes.data()+offset,&value,sizeof(value));
  }
  static bool Read(void *opaque,const void *address,void *target,std::size_t count) noexcept {
    auto &self=*static_cast<Memory *>(opaque);
    const auto at=reinterpret_cast<std::uintptr_t>(address);
    if(at==module+0x5D1DADC && count==1) {
      std::memcpy(target,&self.flag,count);return true;
    }
    if(at>=context && at-context<=self.context_bytes.size() &&
       count<=self.context_bytes.size()-static_cast<std::size_t>(at-context)) {
      std::memcpy(target,self.context_bytes.data()+static_cast<std::size_t>(at-context),count);
      if(at==context+8 && count==20 && self.change_header && ++self.header_reads==2)
        static_cast<std::uint8_t *>(target)[2]^=std::uint8_t{1};
      return true;
    }
    if(at>=cells && at-cells<=self.cell_bytes.size() &&
       count<=self.cell_bytes.size()-static_cast<std::size_t>(at-cells)) {
      std::memcpy(target,self.cell_bytes.data()+static_cast<std::size_t>(at-cells),count);return true;
    }
    return false;
  }
  Memory() {
    for(std::size_t i=0;i<20;++i)context_bytes[8+i]=static_cast<std::uint8_t>(0x80+i);
    for(std::size_t i=0;i<cell_bytes.size();++i)cell_bytes[i]=static_cast<std::uint8_t>(0x3A+i%97);
    Put(0x2E8,std::uint32_t{0xED030004});
    Put(8+0x18,cells);Put(8+0x24,std::int32_t{2});
    Put(8+0x100,std::uintptr_t{0x777777});Put(8+0x10C,std::int32_t{0});
    Put(8+0x134,std::int32_t{0});Put(8+0x154,std::int32_t{0});
    Put(8+0x140,std::uint32_t{0x81234567});
  }
  PrisonerQuoteReadOnlyAccess12004 Access() { return {this,&Read,64}; }
};
PrisonerQuoteSourceFrame12004 Frame() {
  PrisonerQuoteSourceFrame12004 out;
  out.executable_sha256=kPrisonerQuoteSourceExecutableSha25612004;
  out.module_base=Memory::module;out.native_revision=17;out.query_sequence=9;out.proof_epoch=3;
  out.date_raw=std::int32_t{-3};out.jailer_full_id=std::uint32_t{0xAB000101};
  out.prisoner_full_id=std::uint32_t{0xBC000202};out.recipient_full_id=std::uint32_t{0xED030004};
  out.definition_identity=std::uintptr_t{0x300000000ULL};out.interaction_context_identity=Memory::context;
  out.original_scope_identity=Memory::context+8;out.roles_verified_in_owned_context=true;
  out.same_frame_confirmed=true;return out;
}
} // namespace

void RunPrisonerRansomScopeClone373ACF012004Cases() {
  // Literal header copy followed by caller root/payload stores; vector cells
  // are copied raw and the logical clone never becomes the original address.
  Memory memory;const auto frame=Frame();const auto access=memory.Access();
  const auto input=ReadPrisonerRansomScopeCloneInputs12004(access,frame);
  const auto vector=ReadPrisonerScopeVectorCopy260E04012004(access,frame,frame.original_scope_identity);
  const auto child=ProjectPrisonerRansomScopeVector18Child12004(vector);
  auto partial=ProjectPrisonerRansomScopeClone12004(input,{},child,{});
  Require(partial.header_copy_source_ready && !partial.source_equivalent_clone_shape_ready,"missing children became full clone");
  Require(ReadPrisonerRansomScopeRawScalar12004<std::uint16_t>(partial.returned_scope,0)==std::uint16_t{4},"caller root override");
  Require(ReadPrisonerRansomScopeRawScalar12004<std::uint64_t>(partial.returned_scope,8)==std::uint64_t{0xED030004},"recipient generation truncated");
  Require(partial.returned_scope.raw[2]==std::uint8_t{0x82} && partial.returned_scope.raw[0x10]==std::uint8_t{0x90},"copied header bytes lost");
  Require(!partial.returned_scope.source_defined[0x14] && !partial.returned_scope.source_defined[0x68],"unwritten padding became defined");
  Require(!partial.physical_cloned_scope_identity && !partial.internal_aliases.primary_scope &&
          !partial.internal_aliases.tertiary_scope && !partial.internal_aliases.support118_identity &&
          partial.internal_aliases.secondary_scope==std::uintptr_t{0} && !partial.native_clone_called,"physical clone fabricated");
  const auto inline_pointer=ReadPrisonerRansomScopePointer12004(partial.returned_scope,0x18);
  Require(inline_pointer && inline_pointer->kind==PrisonerRansomScopePointerKind12004::clone_relative &&
          inline_pointer->relative_offset_or_rva==std::uintptr_t{0x38} &&
          !ReadPrisonerRansomScopeRawScalar12004<std::uintptr_t>(partial.returned_scope,0x18),"inline relation changed to numerical null");
  Require(std::memcmp(partial.returned_scope.raw.data()+0x38,memory.cell_bytes.data(),48)==0,"raw24B cells rebased");

  // Ordinary producer calls the actual owned child readers. Empty vectors can
  // have nonzero source data bits; the distinct fresh destination is null.
  memory.Put(8+0x128,std::uintptr_t{0x876543});memory.Put(8+0x148,std::uintptr_t{0x654321});
  const auto complete=ReadPrisonerRansomScopeClone12004(access,frame);
  Require(complete.source_equivalent_clone_shape_ready && complete.support118_source &&
          complete.support118_source->final_predicate_al_raw_u8==std::uint8_t{0},"actual empty child chain not consumed");
  Require(ReadPrisonerRansomScopeRawScalar12004<std::uintptr_t>(complete.returned_scope,0x100)==std::uintptr_t{0} &&
          ReadPrisonerRansomScopeRawScalar12004<std::uintptr_t>(complete.returned_scope,0x128)==std::uintptr_t{0} &&
          ReadPrisonerRansomScopeRawScalar12004<std::uintptr_t>(complete.returned_scope,0x148)==std::uintptr_t{0},"source data aliased as returned data");
  Require(ReadPrisonerRansomScopeRawScalar12004<std::uint32_t>(complete.returned_scope,0x140)==std::uint32_t{0x81234567} &&
          !complete.returned_scope.source_defined[0x144] && !complete.returned_scope.source_defined[0x167],"support scalar/padding contract");
  memory.Put(8+0x10C,std::int32_t{1});
  const auto allocated_unknown=ReadPrisonerRansomScopeClone12004(access,frame);
  Require(!allocated_unknown.source_equivalent_clone_shape_ready && allocated_unknown.vector100_source &&
          allocated_unknown.vector100_source->source_count_raw_i32==std::int32_t{1} &&
          allocated_unknown.vector100_source->ordered_source_record_identities.empty() &&
          !allocated_unknown.returned_scope.source_defined[0x100],"positive allocation postimage fabricated");
  memory.Put(8+0x10C,std::int32_t{0});
  memory.Put(8+0x154,std::int32_t{-1});
  const auto support_unknown=ReadPrisonerRansomScopeClone12004(access,frame);
  Require(!support_unknown.source_equivalent_clone_shape_ready &&
          !support_unknown.returned_scope.source_defined[0x148],"negative support converted to empty postimage");
  memory.Put(8+0x154,std::int32_t{0});

  // Negative signed count is a reached no-allocation branch of260E040 and
  // preserves the same nonnull relation; it does not define unused cells.
  memory.Put(8+0x24,std::int32_t{-2});
  const auto negative=ProjectPrisonerRansomScopeVector18Child12004(
      ReadPrisonerScopeVectorCopy260E04012004(access,frame,frame.original_scope_identity));
  partial=ProjectPrisonerRansomScopeClone12004(input,{},negative,{});
  Require(ReadPrisonerRansomScopeRawScalar12004<std::int32_t>(partial.returned_scope,0x24)==std::int32_t{-2} &&
          !partial.returned_scope.source_defined[0x38] &&
          ReadPrisonerRansomScopePointer12004(partial.returned_scope,0x18).has_value(),"negative vector copy converted to empty/null");

  // Growth cannot be completed with only literal allocator source.
  memory.Put(8+0x24,std::int32_t{9});
  const auto growth=ProjectPrisonerRansomScopeVector18Child12004(
      ReadPrisonerScopeVectorCopy260E04012004(access,frame,frame.original_scope_identity));
  Require(!growth.minimum_returned_fields_source_ready,"unobserved allocation accepted");

  auto wrong_frame=child;wrong_frame.frame.proof_epoch+=1;
  partial=ProjectPrisonerRansomScopeClone12004(input,{},wrong_frame,{});
  Require(!partial.returned_scope.source_defined[0x18],"cross-frame child joined");
  auto conflicting=child;conflicting.pointers.front().observed_raw=std::uintptr_t{0};
  partial=ProjectPrisonerRansomScopeClone12004(input,{},conflicting,{});
  Require(!partial.returned_scope.source_defined[0x18],"conflicting relation accepted");

  auto wrong_original=frame;wrong_original.original_scope_identity+=8;
  Require(!ReadPrisonerRansomScopeCloneInputs12004(access,wrong_original).original_header_copied,"original context binding ignored");
  memory.Put(0x2E8,std::uint32_t{0xCC030004});
  partial=ProjectPrisonerRansomScopeClone12004(ReadPrisonerRansomScopeCloneInputs12004(access,frame),{},child,{});
  Require(!partial.header_copy_source_ready,"same low24 different generation accepted");

  memory.Put(0x2E8,std::uint32_t{0xED030004});memory.change_header=true;
  Require(!ReadPrisonerRansomScopeCloneInputs12004(access,frame).original_header_copied,"changing copied header accepted");
}
} // namespace xar::ck3_12004
