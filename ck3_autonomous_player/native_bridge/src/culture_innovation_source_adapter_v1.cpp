#include "xar_bridge/culture_innovation_source_adapter_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

using Failure = CultureInnovationSourceAdapterFailureV1;
using Presence = game::CultureInnovationPresenceV1;

constexpr std::int32_t kMaximumComponents = 4'194'304;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::size_t kMaximumNativeStringBytes =
    game::kCultureInnovationStableKeyCapacityV1 - 1;

struct StockMetadata {
  std::string_view key;
  std::string_view group;
  std::string_view skill;
};

// The table is derived from the exact stock sources admitted by
// culture_innovation_v1_abi.json. Era identity is still read from each live
// definition; only the two immutable schema attributes use this table.
constexpr std::array<StockMetadata, 108> kStockMetadata{{
    {"fp3_innovation_fritware", "culture_group_civic", "learning"},
    {"fp3_innovation_mural_sextant", "culture_group_civic", "learning"},
    {"innovation_adaptive_militia", "culture_group_military", "martial"},
    {"innovation_advanced_bowmaking", "culture_group_military", "learning"},
    {"innovation_african_canoes", "culture_group_military", "martial"},
    {"innovation_all_things", "culture_group_civic", "diplomacy"},
    {"innovation_arched_saddle", "culture_group_military", "martial"},
    {"innovation_armilary_sphere", "culture_group_civic", "learning"},
    {"innovation_baliffs", "culture_group_civic", "stewardship"},
    {"innovation_bamboo_bows", "culture_group_military", "martial"},
    {"innovation_bannus", "culture_group_military", "martial"},
    {"innovation_barracks", "culture_group_military", "martial"},
    {"innovation_battlements", "culture_group_military", "stewardship"},
    {"innovation_block_printing", "culture_group_civic", "learning"},
    {"innovation_bulkheads", "culture_group_civic", "stewardship"},
    {"innovation_burhs", "culture_group_military", "stewardship"},
    {"innovation_caballeros", "culture_group_military", "martial"},
    {"innovation_castle_baileys", "culture_group_military", "martial"},
    {"innovation_casus_belli", "culture_group_civic", "diplomacy"},
    {"innovation_catapult", "culture_group_military", "learning"},
    {"innovation_champa_rice", "culture_group_civic", "stewardship"},
    {"innovation_chronicle_writing", "culture_group_civic", "learning"},
    {"innovation_city_planning", "culture_group_civic", "stewardship"},
    {"innovation_coking", "culture_group_civic", "stewardship"},
    {"innovation_compass", "culture_group_civic", "learning"},
    {"innovation_composite_crossbow", "culture_group_military", "learning"},
    {"innovation_condottieri", "culture_group_military", "intrigue"},
    {"innovation_court_officials", "culture_group_civic", "stewardship"},
    {"innovation_cranes", "culture_group_civic", "stewardship"},
    {"innovation_crop_rotation", "culture_group_civic", "stewardship"},
    {"innovation_cupellation", "culture_group_civic", "stewardship"},
    {"innovation_currency_01", "culture_group_civic", "stewardship"},
    {"innovation_currency_02", "culture_group_civic", "stewardship"},
    {"innovation_currency_03", "culture_group_civic", "stewardship"},
    {"innovation_currency_04", "culture_group_civic", "stewardship"},
    {"innovation_deccan_unity", "culture_group_civic", "diplomacy"},
    {"innovation_desert_tactics", "culture_group_military", "martial"},
    {"innovation_development_01", "culture_group_civic", "stewardship"},
    {"innovation_development_02", "culture_group_civic", "stewardship"},
    {"innovation_development_03", "culture_group_civic", "stewardship"},
    {"innovation_development_04", "culture_group_civic", "stewardship"},
    {"innovation_divine_right", "culture_group_civic", "diplomacy"},
    {"innovation_double_entry_bookkeeping", "culture_group_civic", "stewardship"},
    {"innovation_dragon_kiln", "culture_group_civic", "learning"},
    {"innovation_east_settling", "culture_group_civic", "stewardship"},
    {"innovation_elephantry", "culture_group_military", "stewardship"},
    {"innovation_ermine_cloaks", "culture_group_civic", "stewardship"},
    {"innovation_fire_medicine", "culture_group_military", "learning"},
    {"innovation_french_peerage", "culture_group_civic", "diplomacy"},
    {"innovation_gavelkind", "culture_group_civic", "diplomacy"},
    {"innovation_ghilman", "culture_group_military", "martial"},
    {"innovation_grenades", "culture_group_military", "learning"},
    {"innovation_guilds", "culture_group_civic", "stewardship"},
    {"innovation_gunpowder", "culture_group_military", "learning"},
    {"innovation_heraldry", "culture_group_civic", "diplomacy"},
    {"innovation_hereditary_rule", "culture_group_civic", "diplomacy"},
    {"innovation_hoardings", "culture_group_military", "stewardship"},
    {"innovation_hobbies", "culture_group_military", "martial"},
    {"innovation_horseshoes", "culture_group_military", "martial"},
    {"innovation_house_soldiers", "culture_group_military", "martial"},
    {"innovation_knighthood", "culture_group_military", "martial"},
    {"innovation_lacquered_armor", "culture_group_military", "stewardship"},
    {"innovation_land_grants", "culture_group_civic", "stewardship"},
    {"innovation_ledger", "culture_group_civic", "stewardship"},
    {"innovation_legionnaires", "culture_group_military", "martial"},
    {"innovation_longboats", "culture_group_military", "martial"},
    {"innovation_machicolations", "culture_group_military", "stewardship"},
    {"innovation_mangonel", "culture_group_military", "learning"},
    {"innovation_manorialism", "culture_group_civic", "stewardship"},
    {"innovation_men_at_arms", "culture_group_military", "martial"},
    {"innovation_motte", "culture_group_military", "stewardship"},
    {"innovation_muladi", "culture_group_civic", "diplomacy"},
    {"innovation_mustering_grounds", "culture_group_military", "martial"},
    {"innovation_noblesse_oblige", "culture_group_civic", "diplomacy"},
    {"innovation_pharmacopoeia", "culture_group_civic", "learning"},
    {"innovation_pike_columns", "culture_group_military", "martial"},
    {"innovation_plate_armor", "culture_group_military", "martial"},
    {"innovation_plenary_assemblies", "culture_group_civic", "diplomacy"},
    {"innovation_pole_vault", "culture_group_military", "martial"},
    {"innovation_primogeniture", "culture_group_civic", "diplomacy"},
    {"innovation_quilted_armor", "culture_group_military", "martial"},
    {"innovation_reconquista", "culture_group_military", "martial"},
    {"innovation_rectilinear_schiltron", "culture_group_military", "martial"},
    {"innovation_repeating_crossbow", "culture_group_military", "learning"},
    {"innovation_rightful_ownership", "culture_group_civic", "diplomacy"},
    {"innovation_rocket_cart", "culture_group_military", "learning"},
    {"innovation_royal_armory", "culture_group_military", "martial"},
    {"innovation_royal_prerogative", "culture_group_civic", "diplomacy"},
    {"innovation_sahel_horsemen", "culture_group_military", "martial"},
    {"innovation_sanitation", "culture_group_civic", "stewardship"},
    {"innovation_sappers", "culture_group_military", "martial"},
    {"innovation_sarawit", "culture_group_military", "martial"},
    {"innovation_scutage", "culture_group_civic", "stewardship"},
    {"innovation_seigneurialism", "culture_group_civic", "stewardship"},
    {"innovation_sericulture", "culture_group_civic", "stewardship"},
    {"innovation_standing_armies", "culture_group_military", "martial"},
    {"innovation_stem_duchies", "culture_group_civic", "diplomacy"},
    {"innovation_table_of_princes", "culture_group_civic", "diplomacy"},
    {"innovation_tiefutu", "culture_group_military", "martial"},
    {"innovation_trebuchet", "culture_group_military", "learning"},
    {"innovation_valets", "culture_group_military", "martial"},
    {"innovation_varangian_adventurers", "culture_group_military", "martial"},
    {"innovation_war_camels", "culture_group_military", "stewardship"},
    {"innovation_waterworks", "culture_group_civic", "stewardship"},
    {"innovation_wierdijks", "culture_group_civic", "stewardship"},
    {"innovation_windmills", "culture_group_civic", "stewardship"},
    {"innovation_wootz_steel", "culture_group_civic", "learning"},
    {"innovation_zweihanders", "culture_group_military", "martial"},
}};

template <typename T>
bool Read(const CultureInnovationSourceNativeAccessV1 &native,
          std::uintptr_t address, T &output) noexcept {
  return native.read_memory != nullptr && address != 0 &&
      native.read_memory(native.context, address, &output, sizeof(output));
}

bool ReadBytes(const CultureInnovationSourceNativeAccessV1 &native,
               std::uintptr_t address, void *output,
               std::size_t size) noexcept {
  return native.read_memory != nullptr && address != 0 && output != nullptr &&
      native.read_memory(native.context, address, output, size);
}

bool DirectReadMemory(void *, std::uintptr_t address, void *output,
                      std::size_t size) noexcept {
  if (address == 0 || output == nullptr) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

bool DirectCanGainProgress(void *, std::uintptr_t module_base,
                           std::uintptr_t innovation_state,
                           bool &output) noexcept {
  if (module_base == 0 || innovation_state == 0) return false;
  using Predicate = bool (*)(void *, void *);
  output = reinterpret_cast<Predicate>(
      module_base + kCultureSourceCanGainProgressRvaV1)(
      reinterpret_cast<void *>(innovation_state), nullptr);
  return true;
}

bool DirectCanBeFascination(void *, std::uintptr_t module_base,
                            std::uintptr_t innovation_definition,
                            std::uintptr_t culture, bool &output) noexcept {
  if (module_base == 0 || innovation_definition == 0 || culture == 0) {
    return false;
  }
  using Predicate = bool (*)(void *, void *);
  output = reinterpret_cast<Predicate>(
      module_base + kCultureSourceCanBeFascinationRvaV1)(
      reinterpret_cast<void *>(innovation_definition),
      reinterpret_cast<void *>(culture));
  return true;
}

bool ReadNativeStableKey(
    const CultureInnovationSourceNativeAccessV1 &native,
    std::uintptr_t storage,
    game::CultureInnovationStableKeyV1 &output) noexcept {
  output = {};
  std::size_t size = 0;
  std::size_t capacity = 0;
  if (!Read(native, storage + 0x10, size) ||
      !Read(native, storage + 0x18, capacity) || size == 0 ||
      size > capacity || size > kMaximumNativeStringBytes) {
    return false;
  }
  std::uintptr_t data = storage;
  if (capacity >= 16 && !Read(native, storage, data)) return false;
  std::array<char, game::kCultureInnovationStableKeyCapacityV1> bytes{};
  if (!ReadBytes(native, data, bytes.data(), size)) return false;
  return AssignCultureInnovationStableKeyV1(
      std::string_view(bytes.data(), size), output);
}

bool ReadSpan(const CultureInnovationSourceNativeAccessV1 &native,
              std::uintptr_t owner, std::size_t data_offset,
              std::size_t count_offset, std::int32_t maximum,
              bool allow_empty, std::uintptr_t &data,
              std::int32_t &count) noexcept {
  data = 0;
  count = 0;
  if (!Read(native, owner + data_offset, data) ||
      !Read(native, owner + count_offset, count) || count < 0 ||
      count > maximum || (!allow_empty && count == 0) ||
      (count != 0 && data == 0)) {
    return false;
  }
  return true;
}

bool ResolveComponent(const CultureInnovationSourceAdapterContextV1 &context,
                      std::uintptr_t store_slot_rva, std::int32_t full_id,
                      std::size_t identity_offset,
                      std::uintptr_t &object) noexcept {
  object = 0;
  if (context.module_base == 0 || full_id < 0) return false;
  std::uintptr_t store = 0;
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  if (!Read(context.native, context.module_base + store_slot_rva, store) ||
      store == 0 || !Read(context.native, store + kStorageSlotsOffset, slots) ||
      !Read(context.native, store + kStorageCapacityOffset, capacity) ||
      slots == 0 || capacity <= 0 || capacity > kMaximumComponents) {
    return false;
  }
  const auto index =
      static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity) ||
      !Read(context.native,
            slots + static_cast<std::size_t>(index) * kStorageSlotStride +
                kStorageObjectOffset,
            object) ||
      object == 0) {
    object = 0;
    return false;
  }
  std::int32_t round_trip = -1;
  if (!Read(context.native, object + identity_offset, round_trip) ||
      round_trip != full_id) {
    object = 0;
    return false;
  }
  return true;
}

bool ReadModulePointer(const CultureInnovationSourceAdapterContextV1 &context,
                       std::uintptr_t rva,
                       std::uintptr_t &output) noexcept {
  return context.module_base != 0 &&
      Read(context.native, context.module_base + rva, output);
}

const StockMetadata *FindMetadata(
    const game::CultureInnovationStableKeyV1 &key) noexcept {
  const auto view = CultureInnovationStableKeyViewV1(key);
  const auto iterator = std::lower_bound(
      kStockMetadata.begin(), kStockMetadata.end(), view,
      [](const StockMetadata &row, std::string_view candidate) {
        return row.key < candidate;
      });
  return iterator != kStockMetadata.end() && iterator->key == view
             ? &*iterator
             : nullptr;
}

bool Contains(const std::array<std::uintptr_t,
                               game::kCultureInnovationMaximumInnovationsV1>
                  &values,
              std::int32_t count, std::uintptr_t needle) noexcept {
  return std::find(values.begin(), values.begin() + count, needle) !=
      values.begin() + count;
}

Failure ReadPointerList(
    const CultureInnovationSourceNativeAccessV1 &native,
    std::uintptr_t owner, std::size_t data_offset, std::size_t count_offset,
    bool allow_empty,
    std::array<std::uintptr_t,
               game::kCultureInnovationMaximumInnovationsV1> &output,
    std::int32_t &count) noexcept {
  output.fill(0);
  std::uintptr_t data = 0;
  if (!ReadSpan(native, owner, data_offset, count_offset,
                static_cast<std::int32_t>(output.size()), allow_empty, data,
                count)) {
    return Failure::innovation_collection_invalid;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    if (!Read(native, data + static_cast<std::size_t>(index) * sizeof(void *),
              output[static_cast<std::size_t>(index)]) ||
        output[static_cast<std::size_t>(index)] == 0) {
      return Failure::innovation_collection_invalid;
    }
    for (std::int32_t prior = 0; prior < index; ++prior) {
      if (output[static_cast<std::size_t>(prior)] ==
          output[static_cast<std::size_t>(index)]) {
        return Failure::innovation_collection_invalid;
      }
    }
  }
  return Failure::none;
}

} // namespace

CultureInnovationSourceNativeAccessV1
DirectCultureInnovationSourceNativeAccessV1() noexcept {
  CultureInnovationSourceNativeAccessV1 output{};
  output.read_memory = DirectReadMemory;
  output.can_gain_progress = DirectCanGainProgress;
  output.can_be_fascination = DirectCanBeFascination;
  return output;
}

CultureInnovationSourceAdapterFailureV1
ReadExactBuildCultureInnovationSourceV1(
    CultureInnovationSourceAdapterContextV1 &context,
    std::uintptr_t played_character,
    CultureInnovationSourceSampleV1 &output) noexcept {
  output = {};
  context.last_failure = Failure::none;
  const auto fail = [&context, &output](Failure failure) noexcept {
    output = {};
    context.last_failure = failure;
    return failure;
  };
  if (context.module_base == 0 || played_character == 0 ||
      context.native.read_memory == nullptr ||
      context.native.can_gain_progress == nullptr ||
      context.native.can_be_fascination == nullptr) {
    return fail(Failure::invalid_context);
  }

  std::int32_t player_id = -1;
  if (!Read(context.native,
            played_character + kCultureSourceCharacterIdentityOffsetV1,
            player_id) ||
      player_id < 0) {
    return fail(Failure::player_identity_invalid);
  }
  std::uintptr_t player_round_trip = 0;
  if (!ResolveComponent(context, kCultureSourceCharacterStoreSlotV1,
                        player_id, kCultureSourceCharacterIdentityOffsetV1,
                        player_round_trip) ||
      player_round_trip != played_character) {
    return fail(Failure::player_identity_round_trip_failed);
  }
  std::uintptr_t character_fallback = 0;
  if (!ReadModulePointer(context, kCultureSourceCharacterFallbackSlotV1,
                         character_fallback) ||
      played_character == character_fallback) {
    return fail(Failure::player_identity_round_trip_failed);
  }

  std::int32_t culture_id = -1;
  if (!Read(context.native,
            played_character + kCultureSourceCharacterCultureIdOffsetV1,
            culture_id) ||
      culture_id < 0) {
    return fail(Failure::culture_handle_invalid);
  }
  std::uintptr_t culture = 0;
  if (!ResolveComponent(context, kCultureSourceCultureStoreSlotV1, culture_id,
                        kCultureSourceCultureIdentityOffsetV1, culture)) {
    return fail(Failure::culture_store_invalid);
  }
  std::uintptr_t culture_fallback = 0;
  if (!ReadModulePointer(context, kCultureSourceCultureFallbackSlotV1,
                         culture_fallback) ||
      culture == culture_fallback) {
    return fail(Failure::culture_identity_round_trip_failed);
  }

  output.player_character_id = player_id;
  output.player_identity_round_trip = true;
  output.state.culture_id = culture_id;

  std::int32_t head_id = -1;
  if (!Read(context.native, culture + kCultureHeadHandleOffsetV1, head_id)) {
    return fail(Failure::native_read_failed);
  }
  if (head_id == -1) {
    output.state.culture_head_presence = Presence::absent;
    output.state.culture_head_character_id = -1;
  } else {
    if (head_id < 0) return fail(Failure::culture_head_handle_invalid);
    std::uintptr_t head = 0;
    if (!ResolveComponent(context, kCultureSourceCharacterStoreSlotV1,
                          head_id, kCultureSourceCharacterIdentityOffsetV1,
                          head) ||
        head == character_fallback) {
      return fail(Failure::culture_head_identity_round_trip_failed);
    }
    output.state.culture_head_presence = Presence::present;
    output.state.culture_head_character_id = head_id;
    output.state.is_player_culture_head = head_id == player_id;
  }

  std::uintptr_t era_data = 0;
  std::int32_t era_count = 0;
  if (!ReadSpan(context.native, culture, kCultureEraStateVectorOffsetV1,
                kCultureEraStateCountOffsetV1,
                static_cast<std::int32_t>(
                    game::kCultureInnovationMaximumErasV1),
                false, era_data, era_count)) {
    return fail(Failure::era_collection_invalid);
  }
  output.state.era_count = static_cast<std::uint32_t>(era_count);
  std::array<std::uintptr_t, game::kCultureInnovationMaximumErasV1>
      era_definitions{};
  for (std::int32_t index = 0; index < era_count; ++index) {
    const auto era_state =
        era_data + static_cast<std::size_t>(index) * kCultureEraStateStrideV1;
    auto &row = output.state.eras[static_cast<std::size_t>(index)];
    std::uintptr_t era_definition = 0;
    std::uintptr_t era_culture = 0;
    std::int32_t definition_index = -1;
    if (!Read(context.native,
              era_state + kCultureSourceEraDefinitionOffsetV1,
              era_definition) ||
        era_definition == 0 ||
        !Read(context.native,
              era_state + kCultureSourceEraCultureOffsetV1, era_culture) ||
        era_culture != culture ||
        !Read(context.native,
              era_definition + kCultureSourceDefinitionIndexOffsetV1,
              definition_index) ||
        definition_index != index ||
        !ReadNativeStableKey(
            context.native,
            era_definition + kCultureSourceDefinitionStableKeyOffsetV1,
            row.key)) {
      return fail(Failure::era_definition_invalid);
    }
    if (!Read(context.native,
              era_state + kCultureSourceEraProgressOffsetV1,
              row.progress_raw)) {
      return fail(Failure::native_read_failed);
    }
    if (row.progress_raw < 0 ||
        row.progress_raw > kCultureInnovationCompleteFixedPointV1) {
      return fail(Failure::era_progress_invalid);
    }
    if (std::find(era_definitions.begin(), era_definitions.begin() + index,
                  era_definition) != era_definitions.begin() + index) {
      return fail(Failure::era_collection_invalid);
    }
    era_definitions[static_cast<std::size_t>(index)] = era_definition;
  }

  std::array<std::uintptr_t,
             game::kCultureInnovationMaximumInnovationsV1>
      active_definitions{};
  std::int32_t active_count = 0;
  if (const auto failure = ReadPointerList(
          context.native, culture,
          kCultureSourceActiveInnovationVectorOffsetV1,
          kCultureSourceActiveInnovationCountOffsetV1, true,
          active_definitions, active_count);
      failure != Failure::none) {
    return fail(failure);
  }
  std::array<std::uintptr_t,
             game::kCultureInnovationMaximumInnovationsV1>
      candidate_definitions{};
  std::int32_t candidate_count = 0;
  if (const auto failure = ReadPointerList(
          context.native, culture,
          kCultureInnovationDefinitionVectorOffsetV1,
          kCultureInnovationDefinitionCountOffsetV1, true,
          candidate_definitions, candidate_count);
      failure != Failure::none) {
    return fail(failure);
  }

  std::uintptr_t innovation_fallback = 0;
  std::uintptr_t fascination = 0;
  std::uintptr_t spread = 0;
  if (!ReadModulePointer(context, kCultureSourceInnovationFallbackSlotV1,
                         innovation_fallback) ||
      innovation_fallback == 0 ||
      !Read(context.native, culture + kCultureFascinationMarkerOffsetV1,
            fascination) ||
      !Read(context.native, culture + kCultureSpreadMarkerOffsetV1, spread)) {
    return fail(Failure::native_read_failed);
  }
  if (fascination == 0 || fascination == innovation_fallback) {
    output.state.fascination_presence = Presence::absent;
  } else {
    output.state.fascination_presence = Presence::present;
  }

  std::uintptr_t innovation_data = 0;
  std::int32_t innovation_count = 0;
  if (!ReadSpan(context.native, culture,
                kCultureInnovationStateVectorOffsetV1,
                kCultureInnovationStateCountOffsetV1,
                static_cast<std::int32_t>(
                    game::kCultureInnovationMaximumInnovationsV1),
                false, innovation_data, innovation_count)) {
    return fail(Failure::innovation_collection_invalid);
  }
  output.state.innovation_count =
      static_cast<std::uint32_t>(innovation_count);
  std::array<std::uintptr_t,
             game::kCultureInnovationMaximumInnovationsV1>
      state_definitions{};
  for (std::int32_t index = 0; index < innovation_count; ++index) {
    const auto state = innovation_data +
        static_cast<std::size_t>(index) * kCultureInnovationStateStrideV1;
    auto &row = output.state.innovations[static_cast<std::size_t>(index)];
    std::uintptr_t state_culture = 0;
    std::uintptr_t definition = 0;
    std::int32_t definition_index = -1;
    if (!Read(context.native, state + kInnovationCultureOffsetV1,
              state_culture) ||
        state_culture != culture ||
        !Read(context.native, state + kInnovationDefinitionOffsetV1,
              definition) ||
        definition == 0 || definition == innovation_fallback ||
        !Read(context.native,
              definition + kCultureSourceDefinitionIndexOffsetV1,
              definition_index) ||
        definition_index != index ||
        !ReadNativeStableKey(
            context.native,
            definition + kCultureSourceDefinitionStableKeyOffsetV1,
            row.key)) {
      return fail(Failure::innovation_definition_invalid);
    }
    if (std::find(state_definitions.begin(), state_definitions.begin() + index,
                  definition) != state_definitions.begin() + index) {
      return fail(Failure::innovation_definition_round_trip_failed);
    }
    state_definitions[static_cast<std::size_t>(index)] = definition;

    std::uintptr_t era_definition = 0;
    if (!Read(context.native,
              definition + kCultureSourceInnovationEraDefinitionOffsetV1,
              era_definition) ||
        std::find(era_definitions.begin(),
                  era_definitions.begin() + era_count,
                  era_definition) ==
            era_definitions.begin() + era_count) {
      return fail(Failure::innovation_definition_invalid);
    }
    if (!ReadNativeStableKey(
            context.native,
            era_definition + kCultureSourceDefinitionStableKeyOffsetV1,
            row.era_key)) {
      return fail(Failure::innovation_definition_invalid);
    }
    const auto *const metadata = FindMetadata(row.key);
    if (metadata == nullptr ||
        !AssignCultureInnovationStableKeyV1(metadata->group,
                                            row.group_key) ||
        !AssignCultureInnovationStableKeyV1(metadata->skill,
                                            row.skill_key)) {
      return fail(Failure::innovation_metadata_unavailable);
    }
    if (!Read(context.native, state + kInnovationProgressOffsetV1,
              row.progress_raw)) {
      return fail(Failure::native_read_failed);
    }
    if (row.progress_raw < 0 ||
        row.progress_raw > kCultureInnovationCompleteFixedPointV1) {
      return fail(Failure::innovation_progress_invalid);
    }
    row.is_active = Contains(active_definitions, active_count, definition);
    row.is_fascination = fascination == definition;
    row.has_spread_marker = spread == definition;
    if (!context.native.can_gain_progress(
            context.native.context, context.module_base, state,
            row.can_gain_progress) ||
        !context.native.can_be_fascination(
            context.native.context, context.module_base, definition, culture,
            row.can_be_fascination)) {
      return fail(Failure::native_predicate_unavailable);
    }
    if (row.is_fascination) {
      output.state.current_fascination_key = row.key;
    }
  }

  for (std::int32_t index = 0; index < active_count; ++index) {
    if (!Contains(state_definitions, innovation_count,
                  active_definitions[static_cast<std::size_t>(index)])) {
      return fail(Failure::innovation_definition_round_trip_failed);
    }
  }
  for (std::int32_t index = 0; index < candidate_count; ++index) {
    if (!Contains(state_definitions, innovation_count,
                  candidate_definitions[static_cast<std::size_t>(index)])) {
      return fail(Failure::innovation_definition_round_trip_failed);
    }
  }
  if (output.state.fascination_presence == Presence::present &&
      !Contains(state_definitions, innovation_count, fascination)) {
    return fail(Failure::innovation_definition_round_trip_failed);
  }
  if (spread != 0 && spread != innovation_fallback &&
      !Contains(state_definitions, innovation_count, spread)) {
    return fail(Failure::innovation_definition_round_trip_failed);
  }
  context.last_failure = Failure::none;
  return Failure::none;
}

bool ReadExactBuildCultureInnovationNativeSourceV1(
    void *context, std::uintptr_t played_character,
    CultureInnovationSourceSampleV1 &output) noexcept {
  if (context == nullptr) {
    output = {};
    return false;
  }
  auto &adapter =
      *static_cast<CultureInnovationSourceAdapterContextV1 *>(context);
  return ReadExactBuildCultureInnovationSourceV1(
             adapter, played_character, output) == Failure::none;
}

std::string_view CultureInnovationSourceAdapterFailureKeyV1(
    CultureInnovationSourceAdapterFailureV1 failure) noexcept {
  using enum CultureInnovationSourceAdapterFailureV1;
  switch (failure) {
  case none: return "none";
  case invalid_context: return "invalid_context";
  case native_read_failed: return "native_read_failed";
  case player_identity_invalid: return "player_identity_invalid";
  case player_identity_round_trip_failed:
    return "player_identity_round_trip_failed";
  case culture_handle_invalid: return "culture_handle_invalid";
  case culture_store_invalid: return "culture_store_invalid";
  case culture_identity_round_trip_failed:
    return "culture_identity_round_trip_failed";
  case culture_head_handle_invalid: return "culture_head_handle_invalid";
  case culture_head_identity_round_trip_failed:
    return "culture_head_identity_round_trip_failed";
  case era_collection_invalid: return "era_collection_invalid";
  case era_definition_invalid: return "era_definition_invalid";
  case era_progress_invalid: return "era_progress_invalid";
  case innovation_collection_invalid: return "innovation_collection_invalid";
  case innovation_definition_invalid: return "innovation_definition_invalid";
  case innovation_definition_round_trip_failed:
    return "innovation_definition_round_trip_failed";
  case innovation_metadata_unavailable:
    return "innovation_metadata_unavailable";
  case innovation_progress_invalid: return "innovation_progress_invalid";
  case native_predicate_unavailable: return "native_predicate_unavailable";
  }
  return "unknown";
}

} // namespace xar::ck3_11906
