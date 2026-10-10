#include "xar_bridge/lifestyle_perk_truth_producer_12004.hpp"

#include <cstring>
#include <limits>
#include <map>
#include <stdexcept>
#include <utility>
#include <vector>

namespace {
using namespace xar::ck3_12004;
using namespace xar::ck3_12004::lifestyle;
constexpr std::uintptr_t kBase09d = 0x180000000;
constexpr std::uintptr_t kCharacter09d = 0x6000;
constexpr std::uintptr_t kPerk09d = 0x7000;
constexpr std::uintptr_t kVtable09d = 0x8000;
struct Memory09d {
  std::map<std::uintptr_t,std::vector<std::byte>> fields;
  int calls = 0;
  bool throw_reads = false;
  template<class T> void Put(std::uintptr_t address,T value) {
    std::vector<std::byte> bytes(sizeof(value));
    std::memcpy(bytes.data(),&value,sizeof(value));
    fields[address] = std::move(bytes);
  }
};
bool Read09d(void *context,std::uintptr_t address,void *output,std::size_t size) {
  auto &memory=*static_cast<Memory09d *>(context);
  ++memory.calls;
  if (memory.throw_reads) throw std::runtime_error("09d synthetic guarded read");
  const auto found=memory.fields.find(address);
  if (found==memory.fields.end() || found->second.size()!=size) return false;
  std::memcpy(output,found->second.data(),size); return true;
}
void Require09d(bool value,const char *reason) {
  if (!value) throw std::runtime_error(reason);
}
SourceReadFrame12004 Frame09d() {
  SourceReadFrame12004 frame{};
  frame.executable_sha256="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
  frame.module_base=kBase09d;
  frame.frame_identity=0x902;
  frame.native_revision=3; frame.query_sequence=4; frame.proof_epoch=5;
  frame.date_raw=123456;
  frame.caller_domain="lifestyle_selected_perk_truth";
  frame.caller_snapshot_confirmed=true;
  return frame;
}
void PutFields09d(Memory09d &memory) {
  memory.Put(kCharacter09d+0x18,std::uint32_t{0xA5000091});
  memory.Put(kPerk09d+0x80,kVtable09d);
  memory.Put(kPerk09d+0x80+0x38,std::uintptr_t{0});
  memory.Put(kVtable09d+0x58,std::uintptr_t{0x110000});
  memory.Put(kVtable09d+0x60,std::uintptr_t{0x120000});
  memory.Put(kVtable09d+0xC8,std::uintptr_t{0x130000});
  memory.Put(kBase09d+kLifestylePerkTruthEvaluationFlagRva12004,std::uint8_t{0x80});
}
void RequireUnknown09d(const LifestylePerkTruthProducer37998D0Result12004 &result) {
  Require09d(!result.value && !result.source_projected_returned_raw_u8 &&
      !result.child_source_value_ready && !result.native_callback_executed &&
      !result.actual_trigger_evaluation_observed,"09d missing virtual producers stay unknown");
}
} // namespace

// No main, no native evaluation. The sole16/62/10 new compound invokes once.
bool RunLifestylePerkTruthProducer12004NewCases() {
  try {
    Memory09d memory{};
    PutFields09d(memory);
    LifestylePerkReadonlyAccess12004 access{kBase09d,&memory,&Read09d};
    LifestyleCharacterScope12004 scope{};
    Require09d(ProjectLifestyleCharacterScope9D78D012004(access,kCharacter09d,scope),
        "09d adapter fixture uses actual18 source projection");
    const auto frame=Frame09d();
    auto before=memory.calls;
    const auto missing_frame=ReadLifestylePerkTruthProducer37998D012004(access,kPerk09d,scope);
    RequireUnknown09d(missing_frame);
    Require09d(missing_frame.context_projection_available &&
        missing_frame.context_root_word==4 &&
        missing_frame.context_full_id_payload==std::uint64_t{0xA5000091} &&
        !missing_frame.copied_frame_ready && !missing_frame.child_frame &&
        memory.calls==before,"09d context projection cannot create caller frame");

    auto invalid=frame; invalid.caller_snapshot_confirmed=false;
    const auto unconfirmed=ReadLifestylePerkTruthProducer37998D012004(access,kPerk09d,scope,&invalid);
    RequireUnknown09d(unconfirmed);
    Require09d(!unconfirmed.copied_frame_ready && !unconfirmed.child_frame &&
        memory.calls==before,"09d unconfirmed frame performs no native field reads");
    invalid=frame; invalid.module_base+=0x1000;
    const auto mismatch=ReadLifestylePerkTruthProducer37998D012004(access,kPerk09d,scope,&invalid);
    RequireUnknown09d(mismatch);
    Require09d(!mismatch.copied_frame_ready && memory.calls==before,
        "09d frame and source module mismatch is unavailable");

    const auto raw=ReadLifestylePerkTruthProducer37998D012004(access,kPerk09d,scope,&frame);
    RequireUnknown09d(raw);
    Require09d(raw.copied_frame_ready && raw.child_frame &&
        raw.child_frame->read_frame==frame &&
        raw.child_frame->producer_rva==0x372E000 &&
        raw.child_frame->receiver_identity==kPerk09d+0x80 &&
        raw.child_frame->primary_scope_identity==reinterpret_cast<std::uintptr_t>(scope.raw.data()) &&
        raw.child_frame->primary_scope_root_word==4 &&
        raw.trigger_vtable_raw==kVtable09d &&
        raw.root_kind_getter_slot58_raw==std::uintptr_t{0x110000} &&
        raw.root_mask_getter_slot60_raw==std::uintptr_t{0x120000} &&
        raw.final_evaluator_slotc8_raw==std::uintptr_t{0x130000} &&
        raw.evaluation_flag_raw_u8==std::uint8_t{0x80},
        "09d original source receiver and owned masked context reach generic child unchanged");

    auto string_frame=frame; string_frame.frame_identity=0;
    string_frame.snapshot_identity="fixture / opaque snapshot09d";
    const auto string_raw=ReadLifestylePerkTruthProducer37998D012004(access,kPerk09d,scope,&string_frame);
    RequireUnknown09d(string_raw);
    Require09d(string_raw.copied_frame_ready && string_raw.child_frame &&
        string_raw.child_frame->read_frame==string_frame &&
        string_raw.child_frame->read_frame.frame_identity==0 &&
        string_raw.child_frame->read_frame.snapshot_identity==string_frame.snapshot_identity,
        "09d actual string-only snapshot carrier is copied without numeric fabrication");

    const auto defined_root=scope.defined_bytes[0];
    scope.defined_bytes[0]=0;
    before=memory.calls;
    const auto hole=ReadLifestylePerkTruthProducer37998D012004(access,kPerk09d,scope,&frame);
    RequireUnknown09d(hole);
    Require09d(!hole.context_root_word && !hole.child_frame && memory.calls==before,
        "09d unknown owned root byte cannot fall back to native reader or zero");
    scope.defined_bytes[0]=defined_root;
    const auto defined_payload=scope.defined_bytes[8];
    scope.defined_bytes[8]=0;
    const auto payload_hole=ReadLifestylePerkTruthProducer37998D012004(access,kPerk09d,scope,&frame);
    RequireUnknown09d(payload_hole);
    Require09d(!payload_hole.context_full_id_payload && !payload_hole.child_frame &&
        memory.calls==before,"09d unknown owned payload remains distinct from known zero");
    scope.defined_bytes[8]=defined_payload;

    const auto overflow=ReadLifestylePerkTruthProducer37998D012004(
        access,std::numeric_limits<std::uintptr_t>::max()-0x7F,scope,&frame);
    RequireUnknown09d(overflow);
    Require09d(!overflow.compiled_trigger_receiver_identity && !overflow.child_frame &&
        memory.calls==before,"09d selected Perk plus80 overflow is unavailable");

    memory.fields.erase(kBase09d+kLifestylePerkTruthEvaluationFlagRva12004);
    const auto flag_missing=ReadLifestylePerkTruthProducer37998D012004(access,kPerk09d,scope,&frame);
    RequireUnknown09d(flag_missing);
    Require09d(!flag_missing.evaluation_flag_raw_u8 && !flag_missing.input_leaf_ready,
        "09d missing source flag is not synthesized zero");
    memory.Put(kBase09d+kLifestylePerkTruthEvaluationFlagRva12004,std::uint8_t{0});
    const auto flag_zero=ReadLifestylePerkTruthProducer37998D012004(access,kPerk09d,scope,&frame);
    RequireUnknown09d(flag_zero);
    Require09d(flag_zero.evaluation_flag_raw_u8==std::uint8_t{0},
        "09d known flag zero does not reject or qualify final predicate");
    memory.throw_reads=true;
    const auto read_throws=ReadLifestylePerkTruthProducer37998D012004(access,kPerk09d,scope,&frame);
    RequireUnknown09d(read_throws);
    Require09d(!read_throws.evaluation_flag_raw_u8 && !read_throws.input_leaf_ready,
        "09d external guarded read exceptions retain unknown");
    return true;
  } catch (...) {
    return false;
  }
}
