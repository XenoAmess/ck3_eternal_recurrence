#pragma once

#include "xar_bridge/ck3_12004_first_heir_reproductive_inputs.hpp"
#include "xar_bridge/current_first_heir_conception_candidate_inputs_v1.hpp"
#include "xar_bridge/ck3_12004_family_abi.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include <algorithm>
#include <bit>
#include <limits>

namespace xar::ck3_12004 {

struct NativeConceptionCandidateBindingsV1 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  bool (*read_memory)(void *, const void *, void *, std::size_t) noexcept = nullptr;
  void *read_context = nullptr;
  std::int32_t (*highest_tier)(void *) = nullptr;
  ConceptionReverseCloseOrExtended12004Getter reverse_close_or_extended = nullptr;
};

inline NativeConceptionCandidateBindingsV1 BindNativeConceptionCandidateInputsV1(
    std::uintptr_t module_base, std::string_view executable_sha256,
    bool (*read_memory)(void *, const void *, void *, std::size_t) noexcept,
    void *read_context = nullptr) noexcept {
  return {module_base != 0 && executable_sha256 == kExecutableSha256 &&
              read_memory != nullptr,
          module_base, read_memory, read_context,
          module_base != 0 && executable_sha256 == kExecutableSha256 &&
              read_memory != nullptr ? reinterpret_cast<std::int32_t (*)(void *)>(
                  module_base + kFamilyHighestTierRva) : nullptr,
          module_base != 0 && executable_sha256 == kExecutableSha256 &&
              read_memory != nullptr ? reinterpret_cast<ConceptionReverseCloseOrExtended12004Getter>(
                  module_base + kFamilyCloseOrExtendedFamilyRva) : nullptr};
}

namespace current_conception_candidate_detail {
inline bool ReadIntegerAddress(void *opaque, std::uintptr_t address,
                               void *output, std::size_t bytes) noexcept {
  const auto *b = static_cast<const NativeConceptionCandidateBindingsV1 *>(opaque);
  return b != nullptr && b->enabled && b->read_memory != nullptr &&
      address != 0 && b->read_memory(b->read_context,
                                   reinterpret_cast<const void *>(address),
                                   output, bytes);
}
template <typename T>
inline bool Field(const NativeConceptionCandidateBindingsV1 &b,
                  std::uintptr_t object, std::size_t offset, T &output) noexcept {
  return b.enabled && b.read_memory != nullptr && object != 0 &&
      object <= std::numeric_limits<std::uintptr_t>::max() - offset &&
      b.read_memory(b.read_context, reinterpret_cast<const void *>(object + offset),
                    &output, sizeof(output));
}
} // namespace current_conception_candidate_detail


// Independently copied current scalars preserve usable values when an unused
// scalar cannot be read. The legacy all-seven diagnostic stays unchanged.
inline ConceptionProviderNumericInputs12004 ReadProviderNumericInputsV1(
    const NativeConceptionCandidateBindingsV1 &b) noexcept {
  ConceptionProviderNumericInputs12004 output{};
  std::array<std::optional<std::int64_t> *, 7> fields{
      &output.base_average_floor, &output.linked_pair_addend,
      &output.linked_pair_title_state_addend,
      &output.both_title_state_absent_multiplier,
      &output.first_relation_multiplier, &output.second_relation_multiplier,
      &output.alternate_relation_multiplier};
  for (std::size_t index = 0; index < fields.size(); ++index) {
    std::int64_t raw = 0;
    if (current_conception_candidate_detail::Field(
            b, b.module_base, conception_pair_value_inputs::kLoadedNumericSlotRvas[index], raw))
      *fields[index] = raw;
  }
  return output;
}

// Query-local automatic join. Unknown or skipped providers remain optional;
// the source-ordered evaluator alone decides which operands are required.
inline ConceptionPairProviderInputs12004 BuildConceptionProviderInputsV1(
    const ck3_11906::CurrentHouseholdConceptionPairInputsV1 &pair,
    const ck3_11906::CurrentCharacterConceptionCandidateRowV1 *first,
    const ck3_11906::CurrentCharacterConceptionCandidateRowV1 *second,
    std::optional<bool> first_pregnancy_record_present) noexcept {
  ConceptionPairProviderInputs12004 input{};
  if (pair.short_circuit.first_evaluated)
    input.first_excluded = pair.short_circuit.first.predicate_true;
  if (pair.short_circuit.second_evaluated)
    input.second_excluded = pair.short_circuit.second.predicate_true;
  input.first_pregnancy_record_present = first_pregnancy_record_present;
  input.recent_child_gate_passes = pair.last_child_date.recent_child_branch_passed;
  input.first_title_state_present = pair.first_title_state_present;
  input.first_own_tier_raw = pair.first_highest_tier_raw;
  input.second_own_tier_raw = pair.second_highest_tier_raw;
  if (pair.selected_character_id == pair.first_character_id)
    input.observed_count_role = ConceptionProviderCountRole12004::first;
  else if (pair.selected_character_id == pair.second_character_id)
    input.observed_count_role = ConceptionProviderCountRole12004::second;
  input.selected_offspring_count_raw = pair.offspring_count.native_count;
  input.selected_child_limit_raw = pair.child_limit.value.child_limit_raw;
  if (first != nullptr) {
    input.first_raw = first->first_value.first_output_raw;
    input.first_selects_alternate = first->secondary_context.selects_alternate_relation_path;
  }
  if (second != nullptr) {
    input.second_raw = second->second_value.value_raw;
    input.second_selects_alternate = second->secondary_context.selects_alternate_relation_path;
  }
  input.numeric = pair.provider_numeric;
  input.primary_relation_match = pair.list_bonus.primary_relation_match;
  input.first_child_count_raw = pair.list_bonus.first_child_count_raw;
  input.second_child_count_raw = pair.list_bonus.second_child_count_raw;
  input.first_list_has_second_parent_witness = pair.list_bonus.first_list_has_second_parent_witness;
  input.second_list_has_first_parent_witness = pair.list_bonus.second_list_has_first_parent_witness;
  input.second_title_state_present = pair.second_title_state_present;
  input.normal_close_family = pair.normal_close_family.normal_close_family;
  input.normal_related_pair = pair.related_pair.related_pair_predicate;
  input.second_family_present = pair.secondary_family_membership.second_family_present;
  input.second_family20_contains_first = pair.secondary_family_membership.second_family20_contains_first;
  input.alternate_close_or_extended = pair.reverse_close_or_extended.alternate_close_or_extended;
  return input;
}

inline ck3_11906::CurrentFirstHeirConceptionCandidateInputsReadV1
ReadCurrentFirstHeirConceptionCandidateInputsV1(
    const ck3_12002::FamilyBindings &family,
    const NativeConceptionCandidateBindingsV1 &b,
    const ck3_11906::CurrentFirstHeirRelationshipReadV1 &relationship) {
  using namespace current_conception_candidate_detail;
  using namespace first_heir_descendants_detail;
  ck3_11906::CurrentFirstHeirConceptionCandidateInputsReadV1 result{};
  if (!b.enabled || !relationship.reproductive_inputs ||
      relationship.reproductive_inputs->status == "unavailable") return result;
  CoreSnapshotPrefix before{}, after{};
  if (!Frame(family, before) || relationship.failure !=
      ck3_11906::CurrentFirstHeirRelationshipFailureV1::none) {
    result.unavailable_reason = "current_household_conception_frame_unavailable";
    return result;
  }
  struct Receiver { std::int32_t id; std::uintptr_t character; };
  std::vector<Receiver> receivers;
  struct PendingContext { const NativeConceptionCandidateBindingsV1 *binding;
                          const CoreBindings *core; };
  PendingContext pending_context{&b, &family.context.core};
  conception_candidate_pending::Access pending_access{};
  pending_access.exact_build_admitted = b.enabled;
  pending_access.executable_sha256 = kExecutableSha256;
  pending_access.context = &pending_context;
  pending_access.read_memory = [](void *opaque, std::uintptr_t address,
                                 void *output, std::size_t bytes) noexcept {
    const auto &c = *static_cast<const PendingContext *>(opaque);
    return ReadIntegerAddress(const_cast<NativeConceptionCandidateBindingsV1 *>(c.binding),
                              address, output, bytes);
  };
  pending_access.resolve_character = [](void *opaque, std::int32_t id) noexcept {
    const auto &c = *static_cast<const PendingContext *>(opaque);
    return xar::ck3_12004::ResolveCoreCharacter(*c.core, id);
  };
  const auto extended = BindConceptionExtendedGate12004(
      "1.20.0.4", kExecutableSha256, b.read_memory, b.read_context);
  const auto first_binding = BindConceptionFirstValue12004(
      "1.20.0.4", kExecutableSha256, b.module_base, b.read_memory, b.read_context);
  const auto second_binding = BindConceptionSecondValue12004(
      b.module_base, "1.20.0.4", kExecutableSha256, &ReadIntegerAddress,
      const_cast<NativeConceptionCandidateBindingsV1 *>(&b));
  const auto modifier_binding = BindConceptionModifierContext12004(
      b.module_base, "1.20.0.4", kExecutableSha256, &ReadIntegerAddress,
      const_cast<NativeConceptionCandidateBindingsV1 *>(&b));
  const auto secondary = BindConceptionSecondaryContext12004(
      "1.20.0.4", kExecutableSha256, b.module_base, b.read_memory, b.read_context);
  for (const auto &household : relationship.reproductive_inputs->rows) {
    ck3_11906::CurrentCharacterConceptionCandidateRowV1 row{};
    row.character_id = household.character_id;
    const auto character = reinterpret_cast<std::uintptr_t>(
        xar::ck3_12004::ResolveCoreCharacter(family.context.core, row.character_id));
    const auto full_id = std::bit_cast<std::uint32_t>(row.character_id);
    receivers.push_back({row.character_id, character});
    row.extended_gate = ReadConceptionExtendedGateForCharacter12004(
        extended, character, full_id);
    row.pending_candidate = conception_candidate_pending::Read(
        pending_access, reinterpret_cast<const void *>(character), row.character_id);
    row.secondary_context = ReadConceptionSecondaryContextForCharacter12004(
        secondary, character, full_id);
    ck3_12002::family_value::CharacterValue first{}, checked{};
    std::string_view reason = "current_household_provider_seed_unavailable";
    if (ck3_12002::family_value::ReadCharacterValue(family.values,
            row.character_id, first, true, &reason) &&
        ck3_12002::family_value::ReadCharacterValue(family.values,
            row.character_id, checked, true, &reason) && first == checked) {
      const auto modifier_context = ResolveConceptionModifierContext12004(
          modifier_binding, character, row.character_id);
      auto first_inputs = ReadConceptionFirstValueInputsWithModifierContext12004(
          first_binding, modifier_binding, character, full_id, checked,
          modifier_context, &reason);
      row.first_value = EvaluateConceptionFirstValue12004(first_inputs);
      if (!first_inputs) row.first_value.unavailable_reason = reason;
      ConceptionSecondValueInputs12004 second_inputs{};
      std::string second_reason;
      if (ReadConceptionSecondValueInputs12004(second_binding, character,
              row.character_id, checked.fertility, second_inputs, second_reason))
        row.second_value = ComputeConceptionSecondValue12004(second_inputs);
      else row.second_value.reason = std::move(second_reason);
    } else {
      row.first_value.unavailable_reason = reason;
      row.second_value.reason = std::string(reason);
    }
    result.rows.push_back(std::move(row));
  }
  const auto find_receiver = [&receivers](std::int32_t id) {
    const auto found = std::find_if(receivers.begin(), receivers.end(),
        [id](const auto &r) { return r.id == id; });
    return found == receivers.end() ? std::uintptr_t{0} : found->character;
  };
  const auto find_row = [&result](std::int32_t id) {
    return std::find_if(result.rows.begin(), result.rows.end(),
        [id](const auto &r) { return r.character_id == id; });
  };
  const auto heir = relationship.heir_character_id;
  std::vector<std::int32_t> spouses;
  const auto add_spouse = [&spouses, heir](std::int32_t id) {
    if (id > 0 && id != heir && std::find(spouses.begin(), spouses.end(), id) == spouses.end())
      spouses.push_back(id);
  };
  add_spouse(relationship.relationship.primary_spouse_character_id);
  for (const auto id : relationship.relationship.spouse_character_ids) add_spouse(id);
  const auto list_binding = BindConceptionPairListBonus12004(
      b.module_base, "1.20.0.4", kExecutableSha256, b.read_memory, b.read_context);
  const auto related_binding = BindConceptionRelatedPair12004(
      "1.20.0.4", kExecutableSha256, b.module_base, b.read_memory, b.read_context);
  const auto normal_close_family_binding = BindConceptionNormalCloseFamily12004(
      b.module_base, kExecutableSha256, b.read_memory, b.read_context);
  const auto secondary_membership_binding = BindConceptionSecondaryFamilyMembership12004(
      "1.20.0.4", kExecutableSha256, b.read_memory, b.read_context);
  const auto second_title_binding = BindConceptionSecondTitleState12004(
      "1.20.0.4", kExecutableSha256, b.read_memory, b.read_context);
  auto reverse_related_binding = BindConceptionReverseCloseOrExtended12004(
      b.module_base, kExecutableSha256, b.read_memory, b.read_context);
  reverse_related_binding.getter = b.reverse_close_or_extended;
  const auto lineage_binding = BindConceptionPairMaxInputImage(
      "1.20.0.4", kExecutableSha256, b.module_base, b.read_memory, b.read_context);
  const auto child_limit_binding = BindConceptionChildLimit12004(
      "1.20.0.4", kExecutableSha256, b.module_base, b.read_memory, b.read_context);
  const auto offspring_binding = BindConceptionOffspringCount12004(
      b.module_base, "1.20.0.4", kExecutableSha256, b.read_memory, b.read_context);
  const auto short_circuit_binding = BindConceptionPairShortCircuit12004(
      b.module_base, "1.20.0.4", kExecutableSha256, b.read_memory, b.read_context);
  conception_last_child_date::Access date_access{};
  date_access.exact_build_admitted = b.enabled;
  date_access.executable_sha256 = kExecutableSha256;
  date_access.image_base = b.module_base;
  date_access.context = &pending_context;
  date_access.read_memory = pending_access.read_memory;
  date_access.resolve_character = pending_access.resolve_character;
  for (const auto spouse : spouses) {
    ck3_11906::CurrentHouseholdConceptionPairInputsV1 pair{};
    pair.first_character_id = heir;
    pair.second_character_id = spouse;
    const auto first = find_receiver(heir), second = find_receiver(spouse);
    const auto first_id = std::bit_cast<std::uint32_t>(heir);
    const auto second_id = std::bit_cast<std::uint32_t>(spouse);
    const auto second_title = ReadConceptionSecondTitleStatePresenceForCharacter12004(
        second_title_binding, second, second_id);
    pair.second_title_state_status = second_title.status;
    pair.second_title_state_unavailable_reason = second_title.unavailable_reason;
    pair.second_1c0_raw_u64 = second_title.second_1c0_raw_u64;
    pair.second_title_state_present = second_title.second_title_state_present;
    pair.provider_numeric = ReadProviderNumericInputsV1(b);
    pair.loaded_numeric = conception_pair_value_inputs::ReadLoadedNumericInputs(
        {b.module_base, kExecutableSha256, &ReadIntegerAddress,
         const_cast<NativeConceptionCandidateBindingsV1 *>(&b)});
    const auto first_row = find_row(heir), second_row = find_row(spouse);
    const auto first_raw = first_row == result.rows.end() ? std::optional<std::int64_t>{} :
        first_row->first_value.first_output_raw;
    const auto second_raw = second_row == result.rows.end() ? std::optional<std::int64_t>{} :
        second_row->second_value.value_raw;
    const auto floor = pair.loaded_numeric.inputs ?
        std::optional<std::int64_t>{pair.loaded_numeric.inputs->base_average_floor} : std::nullopt;
    pair.base_stage = conception_pair_value_inputs::EvaluateBaseStage(first_raw, second_raw, floor);
    pair.list_bonus = ReadConceptionPairListBonusForCharacters12004(
        list_binding, first, first_id, second, second_id);
    pair.related_pair = ReadConceptionRelatedPairForHousehold12004(
        related_binding, first, first_id, second, second_id);
    pair.secondary_family_membership = ReadConceptionSecondaryFamilyMembershipForPair12004(
        secondary_membership_binding, second, second_id, first, first_id);
    pair.reverse_close_or_extended = ReadConceptionReverseCloseOrExtended12004(
        reverse_related_binding, second, second_id, first, first_id);
    pair.short_circuit = ReadConceptionPairShortCircuit12004(
        short_circuit_binding, first, first_id, second, second_id);
    const auto date_source = conception_last_child_date::ReadCurrentHouseholdSourceInputs(
        date_access, reinterpret_cast<const void *>(first), heir, 3);
    if (date_source.source_inputs_available)
      pair.last_child_date = conception_last_child_date::Read(date_access, date_source.source);
    else {
      pair.last_child_date.source = date_source.source;
      pair.last_child_date.unavailable_reason = date_source.unavailable_reason;
    }
    pair.alternate_relation_path = SelectConceptionSecondaryRelationPath12004(
        first_row == result.rows.end() ? std::nullopt : first_row->secondary_context.selects_alternate_relation_path,
        second_row == result.rows.end() ? std::nullopt : second_row->secondary_context.selects_alternate_relation_path);
    pair.normal_close_family = ReadConceptionNormalCloseFamilyForPair12004(
        normal_close_family_binding, first, first_id, second, second_id,
        first_row == result.rows.end() ? std::nullopt :
            first_row->secondary_context.selects_alternate_relation_path,
        second_row == result.rows.end() ? std::nullopt :
            second_row->secondary_context.selects_alternate_relation_path);
    pair.lineage_tiers = ReadConceptionPairMaxInput(
        lineage_binding, first, first_id, second, second_id);
    std::uintptr_t title_state = 0;
    std::uint32_t observed_first_id = 0, observed_second_id = 0;
    if (Field(b, first, 0x18, observed_first_id) && observed_first_id == first_id &&
        Field(b, second, 0x18, observed_second_id) && observed_second_id == second_id &&
        Field(b, first, 0x1C0, title_state)) {
      pair.first_title_state_present = title_state != 0;
      auto role = ConceptionChildLimitRole12004::second;
      if (title_state != 0 && b.highest_tier != nullptr) {
        // This existing exact4 read-only getter is independently source-closed
        // at 28AC690. Its own-tier returns differ from the lineage max above.
        pair.first_highest_tier_raw = b.highest_tier(reinterpret_cast<void *>(first));
        pair.second_highest_tier_raw = b.highest_tier(reinterpret_cast<void *>(second));
        role = SelectConceptionChildLimitRole12004(true,
            *pair.first_highest_tier_raw, *pair.second_highest_tier_raw);
      }
      if (title_state == 0 || (pair.first_highest_tier_raw && pair.second_highest_tier_raw)) {
        const bool select_first = role == ConceptionChildLimitRole12004::first;
        pair.selected_character_id = select_first ? heir : spouse;
        const auto selected = select_first ? first : second;
        const auto selected_id = select_first ? first_id : second_id;
        pair.offspring_count = ReadConceptionOffspringCountForCharacter12004(
            offspring_binding, selected, selected_id);
        if (pair.lineage_tiers.pair_lineage_tier_max_raw)
          pair.child_limit = ReadConceptionChildLimitForPair12004(
              child_limit_binding, first, first_id, second, second_id,
              selected, selected_id, *pair.lineage_tiers.pair_lineage_tier_max_raw);
        else pair.child_limit.unavailable_reason = "child_limit_lineage_tier_input_unavailable";
      }
    }
    std::optional<bool> pregnancy_record;
    const auto pregnancy_row = std::find_if(relationship.reproductive_inputs->rows.begin(),
        relationship.reproductive_inputs->rows.end(),
        [heir](const auto &r) { return r.character_id == heir; });
    if (pregnancy_row != relationship.reproductive_inputs->rows.end() &&
        pregnancy_row->native_pregnancy.status == "available")
      pregnancy_record = pregnancy_row->native_pregnancy.is_pregnant;
    pair.provider_inputs = BuildConceptionProviderInputsV1(pair,
        first_row == result.rows.end() ? nullptr : &*first_row,
        second_row == result.rows.end() ? nullptr : &*second_row, pregnancy_record);
    pair.provider_result = EvaluateConceptionPairProvider12004(pair.provider_inputs);
    result.pairs.push_back(std::move(pair));
  }
  const auto checked = ck3_12002::ReadCurrentFirstHeirRelationshipV1(family, heir);
  bool same_receivers = true;
  for (const auto &receiver : receivers)
    same_receivers = same_receivers &&
        reinterpret_cast<std::uintptr_t>(xar::ck3_12004::ResolveCoreCharacter(family.context.core, receiver.id)) == receiver.character;
  if (!Frame(family, after) || !SameFrame(before, after) || !same_receivers ||
      checked.failure != ck3_11906::CurrentFirstHeirRelationshipFailureV1::none ||
      checked.relationship != relationship.relationship) {
    result = {};
    result.unavailable_reason = "current_household_conception_frame_changed";
    return result;
  }
  result.status = "available";
  result.unavailable_reason = {};
  return result;
}

} // namespace xar::ck3_12004
#endif
