#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_first_heir_descendants.hpp"
#include "xar_bridge/current_first_heir_conception_trait_inputs_v1.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
namespace xar::ck3_12004 {

struct NativeConceptionTraitBindingsV1 {
  bool enabled = false;
  const void *const *trait_database_slot = nullptr;
  const void *const *invalid_trait_definition_slot = nullptr;
};

// Actual4 TraitDB loaded pointer is independently named by 89E5B0. The original
// exclusion predicate28A6280 has synchronization, so this reader calls neither
// that predicate nor any database accessor/initializer.
inline NativeConceptionTraitBindingsV1 BindNativeConceptionTraitInputsV1(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  if (module_base == 0 || executable_sha256 != kExecutableSha256) return {};
  return {true,
      reinterpret_cast<const void *const *>(module_base + 0x5C67528),
      reinterpret_cast<const void *const *>(module_base + 0x5D1E318)};
}

inline ck3_11906::CurrentCharacterConceptionTraitExclusionReadV1
ReadCurrentCharacterConceptionTraitExclusionV1(
    const CoreBindings &core, const NativeConceptionTraitBindingsV1 &bindings,
    std::int32_t character_id) noexcept {
  using first_heir_descendants_detail::Load;
  ck3_11906::CurrentCharacterConceptionTraitExclusionReadV1 result{};
  if (!core.enabled || !bindings.enabled) return result;
  const auto *character = xar::ck3_12004::ResolveCoreCharacter(core, character_id);
  if (character == nullptr ||
      Load<std::uint32_t>(character, 0x1C) != 0x43686172U) {
    result.unavailable_reason = "native_conception_traits_character_unavailable";
    return result;
  }
  const auto count = Load<std::int32_t>(character, 0x104);
  const auto *ids = Load<const std::int32_t *>(character, 0xF8);
  bool excluded = false;
  // The actual predicate returns false for signed count<=0. An empty list
  // requires no definition or loaded database and is a known native result.
  if (count > 0) {
    if (ids == nullptr) {
      result.unavailable_reason = "native_conception_trait_rows_unavailable";
      return result;
    }
    const void *database = bindings.trait_database_slot == nullptr ? nullptr :
        *bindings.trait_database_slot;
    if (database == nullptr) {
      result.unavailable_reason = "native_conception_trait_database_unavailable";
      return result;
    }
    const auto definition_count = Load<std::int32_t>(database, 0x5C);
    const auto *entries = Load<const void *const *>(database, 0x50);
    for (std::int32_t index = 0; index < count; ++index) {
      const auto id = ids[index];
      const void *trait_entry = nullptr;
      if (id >= 0 && id < definition_count) {
        if (entries != nullptr) trait_entry = entries[id];
      } else if (bindings.invalid_trait_definition_slot != nullptr) {
        trait_entry = *bindings.invalid_trait_definition_slot;
      }
      if (trait_entry == nullptr) {
        result.unavailable_reason = "native_conception_trait_definition_unavailable";
        return result;
      }
      // Actual28A6396 reads DWORD4A4 and tests bit3; either Character's true
      // return excludes the pair at2929BDA/2929C04. The authored flag name is
      // deliberately not inferred, and bit5 fertility is a separate input.
      if ((Load<std::uint32_t>(trait_entry, 0x4A4) & 0x8U) != 0) {
        excluded = true;
        break;
      }
    }
  }
  result.status = "available";
  result.unavailable_reason = {};
  result.blocks_pair_conception = excluded;
  return result;
}

inline ck3_11906::CurrentFirstHeirConceptionTraitInputsReadV1
ReadCurrentFirstHeirConceptionTraitInputsV1(
    const ck3_12002::FamilyBindings &family,
    const NativeConceptionTraitBindingsV1 &trait_bindings,
    const ck3_11906::CurrentFirstHeirRelationshipReadV1 &relationship) noexcept {
  using namespace first_heir_descendants_detail;
  ck3_11906::CurrentFirstHeirConceptionTraitInputsReadV1 result{};
  if (!relationship.reproductive_inputs.has_value()) return result;
  for (const auto &household_row : relationship.reproductive_inputs->rows) {
    ck3_11906::CurrentCharacterConceptionTraitExclusionRowV1 row{};
    row.character_id = household_row.character_id;
    result.rows.push_back(row);
  }
  CoreSnapshotPrefix before{}, after{};
  if (!Frame(family, before) || relationship.failure !=
          ck3_11906::CurrentFirstHeirRelationshipFailureV1::none) {
    for (auto &row : result.rows)
      row.read.unavailable_reason = "native_conception_traits_frame_unavailable";
    return result;
  }
  for (auto &row : result.rows) {
    row.read = ReadCurrentCharacterConceptionTraitExclusionV1(
        family.context.core, trait_bindings, row.character_id);
  }
  if (!Frame(family, after) || !SameFrame(before, after)) {
    for (auto &row : result.rows) {
      row.read = {};
      row.read.unavailable_reason = "native_conception_traits_frame_changed";
    }
  }
  return result;
}

} // namespace xar::ck3_12004
#endif
