#include "xar_bridge/lifestyle_perk_truth_producer_12004.hpp"
#include "xar_bridge/source_auto_accept_trigger_condition_12004.hpp"
#include "xar_bridge/prisoner_trigger_root_scope_gate_12004.hpp"

#include <limits>

namespace xar::ck3_12004::lifestyle {
namespace {
struct MaskedContextRead09d {
  const LifestylePerkReadonlyAccess12004 &native;
  const LifestyleCharacterScope12004 &scope;
};

bool CopyMaskedOrNative09d(void *opaque,const void *source,void *output,
                          std::size_t size) noexcept {
  if (!opaque || !output || size==0) return false;
  auto &read=*static_cast<MaskedContextRead09d *>(opaque);
  const auto address=reinterpret_cast<std::uintptr_t>(source);
  const auto maximum=(std::numeric_limits<std::uintptr_t>::max)();
  const auto owned_begin=reinterpret_cast<std::uintptr_t>(read.scope.raw.data());
  if (size > maximum-address || read.scope.raw.size() > maximum-owned_begin) return false;
  const auto end=address+size;
  const auto owned_end=owned_begin+read.scope.raw.size();
  if (address < owned_end && owned_begin < end) {
    // Any overlap belongs to this source projection. Unknown holes and partial
    // overlap reject here; a native callback cannot fill them or invent zero.
    if (address < owned_begin || end > owned_end) return false;
    return CopyDefinedLifestyleCharacterScopeBytes12004(
        read.scope,static_cast<std::size_t>(address-owned_begin),output,size);
  }
  if (!address || !read.native.read_memory) return false;
  try {
    return read.native.read_memory(read.native.read_context,address,output,size);
  } catch (...) {
    return false;
  }
}

template<class T>
std::optional<T> ReadImageField09d(MaskedContextRead09d &read,
                                  std::uintptr_t rva) noexcept {
  const auto maximum=(std::numeric_limits<std::uintptr_t>::max)();
  if (!read.native.module_base || read.native.module_base > maximum-rva) return {};
  T value{};
  if (!CopyMaskedOrNative09d(&read,
        reinterpret_cast<const void *>(read.native.module_base+rva),
        &value,sizeof(value))) return {};
  return value;
}

template<class T>
std::optional<T> CopyContextField09d(const LifestyleCharacterScope12004 &scope,
                                    std::size_t offset) noexcept {
  T value{};
  if (!CopyDefinedLifestyleCharacterScopeBytes12004(scope,offset,&value,sizeof(value))) return {};
  return value;
}
} // namespace

LifestylePerkTruthProducer37998D0Result12004
ReadLifestylePerkTruthProducer37998D012004(
    const LifestylePerkReadonlyAccess12004 &access,
    std::uintptr_t selected_perk,
    const LifestyleCharacterScope12004 &stable_context,
    const SourceReadFrame12004 *caller_frame) noexcept {
  LifestylePerkTruthProducer37998D0Result12004 out{};
  out.selected_perk_identity=selected_perk;
  out.context_projection_available=stable_context.source_projection_ready;
  try {
    if (!out.context_projection_available) {
      out.unavailable_reason="lifestyle_truth_context_projection_unavailable";
      return out;
    }
    out.context_root_word=CopyContextField09d<std::uint16_t>(stable_context,0);
    out.context_full_id_payload=CopyContextField09d<std::uint64_t>(stable_context,8);
    if (!out.context_root_word || !out.context_full_id_payload ||
        !stable_context.fresh_full_character_id) {
      out.unavailable_reason="lifestyle_truth_context_defined_fields_unavailable";
      return out;
    }
    // The actual9D78D0 caller constructs kind4 and zero-extends Character+18.
    // This check admits that software input, never a native constructor result.
    if (*out.context_root_word!=4 ||
        *out.context_full_id_payload!=static_cast<std::uint64_t>(
            *stable_context.fresh_full_character_id)) {
      out.unavailable_reason="lifestyle_truth_context_source_contract_mismatch";
      return out;
    }
    const auto maximum=(std::numeric_limits<std::uintptr_t>::max)();
    if (!selected_perk || selected_perk > maximum-0x80) {
      out.unavailable_reason="lifestyle_truth_selected_perk_receiver_unavailable";
      return out;
    }
    out.compiled_trigger_receiver_identity=selected_perk+0x80;
    if (!caller_frame || !SourceReadFrameReady12004(*caller_frame) ||
        caller_frame->module_base!=access.module_base) {
      out.unavailable_reason="lifestyle_truth_current_caller_frame_unavailable";
      return out;
    }
    out.copied_frame_ready=true;
    SourceLeafFrame12004 child_frame{};
    child_frame.read_frame=*caller_frame;
    child_frame.producer_rva=kLifestylePerkTruthChildRva12004;
    child_frame.receiver_identity=*out.compiled_trigger_receiver_identity;
    child_frame.primary_scope_identity=
        reinterpret_cast<std::uintptr_t>(stable_context.raw.data());
    child_frame.primary_scope_root_word=out.context_root_word;
    out.child_frame=child_frame;

    MaskedContextRead09d read{access,stable_context};
    const SourceLeafReadOnlyAccess12004 guarded{&read,&CopyMaskedOrNative09d};
    out.evaluation_flag_raw_u8=ReadImageField09d<std::uint8_t>(
        read,kLifestylePerkTruthEvaluationFlagRva12004);
    PrisonerQuoteInternalAliases12004 aliases{};
    // 372DF10 source aliases; no physical native stack/support identity exists
    // in this software projection, and no prisoner role Frame is constructed.
    aliases.primary_scope=child_frame.primary_scope_identity;
    aliases.secondary_scope=std::uintptr_t{0};
    aliases.tertiary_scope=child_frame.primary_scope_identity;
    aliases.primary_scope_root_word=out.context_root_word;
    aliases.evaluation_flag_raw_u8=out.evaluation_flag_raw_u8;
    aliases.physical_aliases_copied=false;

    const auto raw=ReadPrisonerAutoAcceptTriggerCondition12004(
        guarded,child_frame,aliases);
    out.trigger_vtable_raw=raw.trigger_vtable;
    out.root_kind_getter_slot58_raw=raw.root_kind_getter_slot58;
    out.root_mask_getter_slot60_raw=raw.root_mask_getter_slot60;
    out.final_evaluator_slotc8_raw=raw.evaluator_slotc8;
    auto gate_frame=child_frame;
    gate_frame.producer_rva=0x372B4C0;
    const auto gate=ReadPrisonerTriggerRootScopeGate12004(guarded,gate_frame);
    const auto condition=EvaluatePrisonerAutoAcceptTriggerCondition12004(raw,gate);
    out.input_leaf_ready=out.evaluation_flag_raw_u8.has_value() &&
        raw.query_frame_ready && raw.parent_alias_shape_matches &&
        *raw.parent_alias_shape_matches &&
        raw.all_attempted_native_reads_complete && gate.raw_copy_ready;
    out.child_source_value_ready=condition.source_value_ready &&
        condition.source_projected_returned_raw_u8.has_value() &&
        out.evaluation_flag_raw_u8.has_value();
    if (out.child_source_value_ready) {
      // The null37998D0 tail and232B wrapper preserve AL. Only selected31EBE50
      // converts the independently source-qualified raw byte via TEST AL.
      out.source_projected_returned_raw_u8=condition.source_projected_returned_raw_u8;
      out.value=*out.source_projected_returned_raw_u8!=std::uint8_t{0};
      return out;
    }
    out.unavailable_reason=out.evaluation_flag_raw_u8
        ? condition.unavailable_reason
        : "lifestyle_truth_source_evaluation_flag_unavailable";
    // Raw vtable/descriptor addresses and conditional gate outputs remain
    // inputs. None is a returned virtual output or actual native evaluation.
    return out;
  } catch (...) {
    out.source_projected_returned_raw_u8.reset();
    out.value.reset();
    out.child_source_value_ready=false;
    out.unavailable_reason="lifestyle_truth_source_projection_exception";
    return out;
  }
}
} // namespace xar::ck3_12004::lifestyle
