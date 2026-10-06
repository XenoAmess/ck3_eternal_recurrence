#include "xar_bridge/ck3_12002_nonwar_realm.hpp"
#include <windows.h>
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <limits>
#include <utility>
namespace xar::ck3_12002 {
namespace {
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kCharacterDeathMarkerOffset = 0x1D0;
constexpr std::size_t kLandStateHeldTitleIdsOffset = kNonwarRealmHeldTitlesOffset;
constexpr std::size_t kVectorCapacityOffset = 0x08;
constexpr std::size_t kVectorCountOffset = 0x0C;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::size_t kLandedTitleIdentityOffset = 0x10;
constexpr std::size_t kLandedTitleTemplateOffset = 0x48;
constexpr std::size_t kLandedTitleTierOffset = 0x64;
// Exact .3 stock is_landless_type_title / is_noble_family_title leaves and
// Title.Capital() child span.  No preferred-capital substitution is made.
constexpr std::size_t kLandedTitleLandlessTypeOffset = 0x30;
constexpr std::size_t kLandedTitleNobleFamilyOffset = 0x32;
constexpr std::size_t kLandedTitleChildrenCountOffset = 0x11C;
constexpr std::size_t kLandedTitleTemplateKeyOffset = 0x18;
constexpr std::size_t kLandedTitleSuccessionDataOffset = kNonwarRealmTitleSuccessorDataOffset;
constexpr std::size_t kLandedTitleSuccessionCapacityOffset = kNonwarRealmTitleSuccessorCapacityOffset;
constexpr std::size_t kLandedTitleSuccessionCountOffset = kNonwarRealmTitleSuccessorCountOffset;
constexpr std::size_t kLandedTitleHolderCharacterIdOffset = kNonwarRealmTitleHolderOffset;
constexpr std::size_t kProvinceMapNodeOffset = 0x08;
constexpr std::size_t kProvinceIdentityOffset = 0x10;
constexpr std::size_t kGameDataProvinceArrayOffset = 0x140;
constexpr std::size_t kGameDataProvinceCountOffset = 0x14C;
constexpr std::size_t kMapNodeAdjacencyDataOffset = 0x50;
constexpr std::size_t kMapNodeAdjacencyCountOffset = 0x5C;
constexpr std::size_t kAdjacencyRowStride = 0x30;
constexpr std::size_t kAdjacencyRowKindOffset = 0x00;
constexpr std::size_t kAdjacencyRowTargetProvinceIdOffset = 0x04;
constexpr std::int32_t kMaximumComponentSlots = 4'194'304;
constexpr std::int32_t kMaximumProvinces = 1'000'000;
constexpr std::int32_t kMaximumAdjacencyRows = 4'096;
constexpr std::int32_t kMaximumLiegeDepth = 1'024;
constexpr std::int32_t kMaximumTitleSuccessors = 4'096;
constexpr std::int32_t kMaximumHeldTitles = 4'096;
using NativeCampaignRootProvinceHolderCharacterIdV1 =
    ck3_11906::NativeCampaignRootProvinceHolderCharacterIdV1;
struct ObservationV1 : NonwarRealmInput12002, NonwarRealmProjection12002 {};
bool GuardedDirectRead(const void *address, void *output,
                       std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, address, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(output, address, size);
  return true;
#endif
}

bool ReadBytes(const CampaignRootAccessV1 &access, const void *address,
               void *output, std::size_t size) noexcept {
  if (access.read_memory != nullptr) {
    return access.read_memory(access.context, address, output, size);
  }
  return GuardedDirectRead(address, output, size);
}

bool CheckedAddress(const void *base, std::size_t offset,
                    const void *&output) noexcept {
  const auto value = reinterpret_cast<std::uintptr_t>(base);
  if (base == nullptr ||
      offset > std::numeric_limits<std::uintptr_t>::max() - value) {
    output = nullptr;
    return false;
  }
  output = reinterpret_cast<const void *>(value + offset);
  return true;
}

template <typename Value>
bool ReadValue(const CampaignRootAccessV1 &access, const void *base,
               std::size_t offset, Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

bool ReadNativeCountyTitleKey(const CampaignRootAccessV1 &access,
                              const void *title_template,
                              std::string &output) noexcept {
  output.clear();
  const void *native_string = nullptr;
  if (!CheckedAddress(title_template, kLandedTitleTemplateKeyOffset,
                      native_string)) return false;
  if (access.read_string != nullptr) {
    return access.read_string(access.context, native_string, output) &&
           game::IsCanonicalCountyTitleKeyV1(output);
  }
  // The same guarded MSVC string decoding used by the exact title-map reader.
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  if (!ReadValue(access, native_string, 0x10, size) ||
      !ReadValue(access, native_string, 0x18, capacity) || size == 0 ||
      size > capacity || size > 1024) return false;
  const void *bytes = native_string;
  if (capacity > 15 &&
      (!ReadValue(access, native_string, 0, bytes) || bytes == nullptr)) {
    return false;
  }
  try {
    output.resize(static_cast<std::size_t>(size));
  } catch (...) {
    output.clear();
    return false;
  }
  if (!ReadBytes(access, bytes, output.data(), output.size()) ||
      !game::IsCanonicalCountyTitleKeyV1(output)) {
    output.clear();
    return false;
  }
  return true;
}

template <typename Value>
bool ReadSlot(const CampaignRootAccessV1 &access, const Value *slot,
              Value &output) noexcept {
  return ReadBytes(access, slot, &output, sizeof(output));
}

void *ResolveComponent(const CampaignRootAccessV1 &access,
                       void *const *storage_slot,
                       void *const *fallback_slot, std::int32_t full_id,
                       std::size_t identity_offset,
                       std::string_view *resolver_failure = nullptr) noexcept {
  if (resolver_failure != nullptr) *resolver_failure = {};
  const auto unavailable = [resolver_failure](std::string_view guard) noexcept -> void * {
    if (resolver_failure != nullptr) *resolver_failure = guard;
    return nullptr;
  };
  if (full_id <= 0) return unavailable("nonpositive_full_id");
  void *storage = nullptr;
  void *fallback = nullptr;
  if (!ReadSlot(access, storage_slot, storage)) return unavailable("storage_slot_read");
  if (!ReadSlot(access, fallback_slot, fallback)) return unavailable("fallback_slot_read");
  if (storage == nullptr) return unavailable("storage_null");
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!ReadValue(access, storage, kStorageSlotsOffset, slots)) return unavailable("slots_read");
  if (!ReadValue(access, storage, kStorageCapacityOffset, capacity)) return unavailable("capacity_read");
  if (slots == nullptr) return unavailable("slots_null");
  if (capacity <= 0) return unavailable("capacity_nonpositive");
  if (capacity > kMaximumComponentSlots) return unavailable("capacity_limit");
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return unavailable("index_out_of_range");
  void *object = nullptr;
  const auto offset = static_cast<std::size_t>(index) * kStorageSlotStride + kStorageObjectOffset;
  std::int32_t observed_id = -1;
  if (!ReadValue(access, slots, offset, object)) return unavailable("object_read");
  if (object == nullptr) return unavailable("object_null");
  if (object == fallback) return unavailable("object_fallback");
  if (!ReadValue(access, object, identity_offset, observed_id)) return unavailable("identity_read");
  if (observed_id != full_id) return unavailable("generation_mismatch");
  return object;
}

bool InvokeResolver(NativeCampaignRootCharacterResolverV1 resolver,
                    void *character, void *&output) noexcept {
  output = nullptr;
#if defined(_MSC_VER)
  __try {
    output = resolver(character);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = resolver(character);
  return true;
#endif
}

bool InvokeProvinceHolderCharacterId(
    NativeCampaignRootProvinceHolderCharacterIdV1 resolver, void *province,
    std::int32_t &output) noexcept {
  output = -1;
  std::int32_t *returned = nullptr;
#if defined(_MSC_VER)
  __try {
    returned = resolver(province, &output);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = -1;
    return false;
  }
#else
  returned = resolver(province, &output);
#endif
  return returned == &output;
}

std::string_view TierKey(std::int32_t raw) noexcept {
  switch (raw) {
  case 1:
    return "barony";
  case 2:
    return "county";
  case 3:
    return "duchy";
  case 4:
    return "kingdom";
  case 5:
    return "empire";
  case 6:
    return "hegemony";
  default:
    return {};
  }
}

bool ReadPrimaryTitleSuccession(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access, ObservationV1 &output) noexcept {
  output.primary_title_succession_character_ids.clear();
  if (output.primary_title_pointer == nullptr) {
    return !output.primary_title.has_value();
  }
  void *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  if (!ReadValue(access, output.primary_title_pointer,
                 kLandedTitleSuccessionDataOffset, data) ||
      !ReadValue(access, output.primary_title_pointer,
                 kLandedTitleSuccessionCapacityOffset, capacity) ||
      !ReadValue(access, output.primary_title_pointer,
                 kLandedTitleSuccessionCountOffset, count) ||
      capacity < 0 || count < 0 || count > capacity ||
      count > kMaximumTitleSuccessors || (count > 0 && data == nullptr)) {
    return false;
  }
  try {
    output.primary_title_succession_character_ids.reserve(
        static_cast<std::size_t>(count));
  } catch (...) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    std::int32_t character_id = -1;
    if (!ReadValue(access, data,
                   static_cast<std::size_t>(index) * sizeof(character_id),
                   character_id) ||
        character_id <= 0 || character_id == output.player_character_id ||
        ResolveComponent(access, environment.character_storage_slot,
                         environment.character_fallback_slot, character_id,
                         kCharacterIdentityOffset) == nullptr ||
        std::find(output.primary_title_succession_character_ids.begin(),
                  output.primary_title_succession_character_ids.end(),
                  character_id) !=
            output.primary_title_succession_character_ids.end()) {
      return false;
    }
    output.primary_title_succession_character_ids.push_back(character_id);
  }
  return true;
}

bool ReadHeldTitlePartition(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access, void *land_state,
    ObservationV1 &output,
    HeldTitlePartitionFailure12002 *failure_diagnostic) noexcept {
  output.held_title_partition.clear();
  HeldTitlePartitionFailure12002 detail{};
  if (failure_diagnostic != nullptr) detail = *failure_diagnostic;
  const auto fail = [&detail, failure_diagnostic](std::string_view guard) noexcept {
    detail.guard = guard;
    if (failure_diagnostic != nullptr) *failure_diagnostic = detail;
    return false;
  };
  if (land_state == nullptr) {
    if (output.primary_title.has_value()) return fail("land_state_null_with_primary");
    return true;
  }
  void *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  if (!ReadValue(access, land_state, kLandStateHeldTitleIdsOffset, data)) return fail("held_data_read");
  if (!ReadValue(access, land_state, kLandStateHeldTitleIdsOffset + kVectorCapacityOffset, capacity)) return fail("held_capacity_read");
  detail.held_capacity = capacity;
  if (!ReadValue(access, land_state, kLandStateHeldTitleIdsOffset + kVectorCountOffset, count)) return fail("held_count_read");
  detail.held_count = count;
  detail.held_count_observed = true;
  if (capacity < 0) return fail("held_capacity_negative");
  if (count < 0) return fail("held_count_negative");
  if (count > capacity) return fail("held_count_exceeds_capacity");
  if (count > kMaximumHeldTitles) return fail("held_count_exceeds_limit");
  if (count > 0 && data == nullptr) return fail("held_data_null_nonempty");
  try {
    output.held_title_partition.reserve(static_cast<std::size_t>(count));
  } catch (...) {
    return fail("held_partition_reserve_exception");
  }
  std::vector<std::int32_t> seen_title_ids;
  try {
    seen_title_ids.reserve(static_cast<std::size_t>(count));
  } catch (...) {
    return fail("seen_title_reserve_exception");
  }
  for (std::int32_t index = 0; index < count; ++index) {
    detail.index = index;
    detail.title_id = detail.holder_id = detail.tier_raw = -1;
    detail.successor_count = detail.successor_capacity = detail.first_heir_id = -1;
    detail.capital_province_id = -1;
    detail.capital_getter_attempted = detail.capital_getter_completed = false;
    detail.capital_getter_return_address = 0;
    detail.capital_getter_return_nonnull = false;
    detail.capital_type_tag_read_attempted = detail.capital_type_tag_observed = false;
    detail.capital_type_tag = 0;
    detail.capital_no_province_by_stock_type_tag_observed = false;
    detail.capital_no_province_by_stock_type_tag = false;
    detail.landless_type_read_attempted = detail.landless_type_observed = false;
    detail.landless_type_value = 0;
    detail.noble_family_read_attempted = detail.noble_family_observed = false;
    detail.noble_family_value = 0;
    detail.children_count_read_attempted = detail.children_count_observed = false;
    detail.children_count = -1;
    detail.title_key_read_attempted = detail.title_key_observed = false;
    detail.resolver_guard = {};
    detail.title_id_observed = detail.successor_count_observed = detail.capital_province_id_observed = false;
    std::int32_t title_id = -1;
    if (!ReadValue(access, data, static_cast<std::size_t>(index) * sizeof(title_id), title_id)) return fail("title_id_read");
    detail.title_id = title_id;
    detail.title_id_observed = true;
    if (title_id <= 0) return fail("title_id_nonpositive");
    if (std::find(seen_title_ids.begin(), seen_title_ids.end(), title_id) != seen_title_ids.end()) return fail("title_id_duplicate");
    seen_title_ids.push_back(title_id);
    void *title = ResolveComponent(access, environment.landed_title_storage_slot,
        environment.landed_title_fallback_slot, title_id, kLandedTitleIdentityOffset,
        &detail.resolver_guard);
    void *title_template = nullptr;
    std::int32_t holder_character_id = -1;
    std::int32_t tier_raw = 0;
    if (title == nullptr) return fail("title_component_unavailable");
    if (!ReadValue(access, title, kLandedTitleHolderCharacterIdOffset, holder_character_id)) return fail("title_holder_read");
    detail.holder_id = holder_character_id;
    if (holder_character_id != output.player_character_id) return fail("title_holder_not_player");
    if (!ReadValue(access, title, kLandedTitleTemplateOffset, title_template)) return fail("title_template_read");
    if (title_template == nullptr) return fail("title_template_null");
    if (!ReadValue(access, title_template, kLandedTitleTierOffset, tier_raw)) return fail("title_tier_read");
    detail.tier_raw = tier_raw;
    if (TierKey(tier_raw).empty()) return fail("title_tier_unknown");
    // Exactly the original barony validation/exclusion order; tier6 is accepted.
    if (tier_raw < 2) continue;
    void *successor_data = nullptr;
    std::int32_t successor_capacity = 0;
    std::int32_t successor_count = 0;
    if (!ReadValue(access, title, kLandedTitleSuccessionDataOffset, successor_data)) return fail("successor_data_read");
    if (!ReadValue(access, title, kLandedTitleSuccessionCapacityOffset, successor_capacity)) return fail("successor_capacity_read");
    detail.successor_capacity = successor_capacity;
    if (!ReadValue(access, title, kLandedTitleSuccessionCountOffset, successor_count)) return fail("successor_count_read");
    detail.successor_count = successor_count;
    detail.successor_count_observed = true;
    if (successor_capacity < 0) return fail("successor_capacity_negative");
    if (successor_count < 0) return fail("successor_count_negative");
    if (successor_count > successor_capacity) return fail("successor_count_exceeds_capacity");
    if (successor_count > kMaximumTitleSuccessors) return fail("successor_count_exceeds_limit");
    if (successor_count > 0 && successor_data == nullptr) return fail("successor_data_null_nonempty");
    std::optional<std::int32_t> first_heir_character_id;
    if (successor_count > 0) {
      std::int32_t character_id = -1;
      if (!ReadValue(access, successor_data, 0, character_id)) return fail("first_heir_read");
      detail.first_heir_id = character_id;
      if (character_id <= 0) return fail("first_heir_nonpositive");
      if (character_id == output.player_character_id) return fail("first_heir_is_player");
      if (ResolveComponent(access, environment.character_storage_slot,
              environment.character_fallback_slot, character_id, kCharacterIdentityOffset,
              &detail.resolver_guard) == nullptr) return fail("first_heir_component_unavailable");
      first_heir_character_id = character_id;
    }
    std::optional<std::int32_t> capital_province_id;
    bool landless_noble_family_no_province = false;
    std::string native_title_key;
    if (tier_raw == 2) {
      void *capital_province = nullptr;
      std::int32_t province_id = -1;
      detail.capital_getter_attempted = true;
      detail.capital_getter_completed = InvokeResolver(environment.title_province, title, capital_province);
      detail.capital_getter_return_address = static_cast<std::uint64_t>(reinterpret_cast<std::uintptr_t>(capital_province));
      detail.capital_getter_return_nonnull = capital_province != nullptr;
      if (!detail.capital_getter_completed) return fail("county_capital_getter_failed");
      if (capital_province == nullptr) return fail("county_capital_null");
      const auto observe_capital_type_tag = [&]() noexcept {
        detail.capital_type_tag_read_attempted = true;
        std::uint32_t province_tag = 0;
        if (!ReadValue(access, capital_province, 0x85C, province_tag)) return false;
        detail.capital_type_tag_observed = true;
        detail.capital_type_tag = province_tag;
        detail.capital_no_province_by_stock_type_tag_observed = true;
        detail.capital_no_province_by_stock_type_tag = province_tag != 0x50726F76U;
        return true;
      };
      const auto fail_with_capital_type_tag = [&](std::string_view original_guard) noexcept {
        if (failure_diagnostic != nullptr) observe_capital_type_tag();
        return fail(original_guard);
      };
      if (!ReadValue(access, capital_province, kProvinceIdentityOffset, province_id)) return fail_with_capital_type_tag("county_capital_id_read");
      detail.capital_province_id = province_id;
      detail.capital_province_id_observed = true;
      if (province_id > 0) {
        // Geographic counties keep the original positive-ID path and reads.
        capital_province_id = province_id;
      } else {
        if (province_id != 0) return fail_with_capital_type_tag("county_capital_id_nonpositive");
        // Stock noble-family counties have no barony children and legitimately
        // return the Null Province.  Every condition is an actual native read;
        // ordinary Null, unknown tags and malformed titles still fail closed.
        if (!observe_capital_type_tag() || detail.capital_type_tag != 0x4E756C6CU)
          return fail("county_capital_id_nonpositive");
        std::uint8_t landless_type = 0;
        detail.landless_type_read_attempted = true;
        if (!ReadValue(access, title, kLandedTitleLandlessTypeOffset, landless_type))
          return fail("county_landless_type_read");
        detail.landless_type_observed = true;
        detail.landless_type_value = landless_type;
        if (landless_type != 1) return fail("county_capital_id_nonpositive");
        std::uint8_t noble_family = 0;
        detail.noble_family_read_attempted = true;
        if (!ReadValue(access, title, kLandedTitleNobleFamilyOffset, noble_family))
          return fail("county_noble_family_read");
        detail.noble_family_observed = true;
        detail.noble_family_value = noble_family;
        if (noble_family != 1) return fail("county_capital_id_nonpositive");
        std::int32_t children_count = -1;
        detail.children_count_read_attempted = true;
        if (!ReadValue(access, title, kLandedTitleChildrenCountOffset, children_count))
          return fail("county_children_count_read");
        detail.children_count_observed = true;
        detail.children_count = children_count;
        if (children_count != 0) return fail("county_capital_id_nonpositive");
        detail.title_key_read_attempted = true;
        if (!ReadNativeCountyTitleKey(access, title_template, native_title_key))
          return fail("county_no_province_title_key_read");
        detail.title_key_observed = true;
        landless_noble_family_no_province = true;
      }
    }
    try {
      output.held_title_partition.push_back({
          {title_id, tier_raw, std::string(TierKey(tier_raw))},
          first_heir_character_id, capital_province_id,
          output.primary_title.has_value() && output.primary_title->title_id == title_id,
          landless_noble_family_no_province, std::move(native_title_key)});
    } catch (...) {
      return fail("held_partition_push_exception");
    }
  }
  std::sort(output.held_title_partition.begin(), output.held_title_partition.end(),
            [](const auto &left, const auto &right) { return left.title.title_id < right.title.title_id; });
  if (!output.primary_title.has_value()) {
    if (!output.held_title_partition.empty()) return fail("partition_nonempty_without_primary");
    return true;
  }
  if (output.primary_title->tier_raw == 1) {
    if (!output.held_title_partition.empty()) return fail("partition_nonempty_for_barony_primary");
    return true;
  }
  const auto matches = std::count_if(output.held_title_partition.begin(), output.held_title_partition.end(),
                                   [](const auto &row) { return row.primary; });
  detail.primary_match_count = static_cast<std::int32_t>(matches);
  if (matches != 1) return fail("primary_match_count_not_one");
  return true;
}

bool ReadDirectLandedVassals(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access, ObservationV1 &output) noexcept {
  void *storage = nullptr;
  void *character_fallback = nullptr;
  void *title_fallback = nullptr;
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!ReadSlot(access, environment.character_storage_slot, storage) ||
      !ReadSlot(access, environment.character_fallback_slot,
                character_fallback) ||
      !ReadSlot(access, environment.landed_title_fallback_slot,
                title_fallback) ||
      storage == nullptr ||
      !ReadValue(access, storage, kStorageSlotsOffset, slots) ||
      !ReadValue(access, storage, kStorageCapacityOffset, capacity) ||
      slots == nullptr || capacity <= 0 || capacity > kMaximumComponentSlots) {
    return false;
  }

  output.direct_landed_vassal_character_ids.clear();
  for (std::int32_t index = 0; index < capacity; ++index) {
    void *character = nullptr;
    const auto slot_offset = static_cast<std::size_t>(index) *
                                 kStorageSlotStride +
                             kStorageObjectOffset;
    if (!ReadValue(access, slots, slot_offset, character)) {
      return false;
    }
    if (character == nullptr || character == character_fallback ||
        character == output.player_character) {
      continue;
    }

    std::int32_t character_id = -1;
    if (!ReadValue(access, character, kCharacterIdentityOffset,
                   character_id)) {
      return false;
    }
    // Component storage capacity includes reusable slots. A non-null row can
    // still carry an object from another generation; stock character scans in
    // this exact build reject that row and continue. It is not a readable
    // member of the current Character store generation.
    if (character_id <= 0 ||
        (static_cast<std::uint32_t>(character_id) & 0x00FFFFFFU) !=
            static_cast<std::uint32_t>(index)) {
      continue;
    }
    void *death = nullptr;
    if (!ReadValue(access, character, kCharacterDeathMarkerOffset, death)) {
      return false;
    }
    if (death != nullptr) {
      continue;
    }

    void *liege = nullptr;
    if (!InvokeResolver(environment.immediate_liege, character, liege)) {
      return false;
    }
    if (liege != output.player_character) {
      continue;
    }

    void *primary_title = nullptr;
    if (!InvokeResolver(environment.primary_title, character, primary_title)) {
      return false;
    }
    if (primary_title == nullptr || primary_title == title_fallback) {
      continue;
    }
    std::int32_t title_id = -1;
    if (!ReadValue(access, primary_title, kLandedTitleIdentityOffset,
                   title_id) ||
        ResolveComponent(access, environment.landed_title_storage_slot,
                         environment.landed_title_fallback_slot, title_id,
                         kLandedTitleIdentityOffset) != primary_title) {
      return false;
    }
    try {
      output.direct_landed_vassal_character_ids.push_back(character_id);
    } catch (...) {
      return false;
    }
  }
  std::sort(output.direct_landed_vassal_character_ids.begin(),
            output.direct_landed_vassal_character_ids.end());
  return std::adjacent_find(
             output.direct_landed_vassal_character_ids.begin(),
             output.direct_landed_vassal_character_ids.end()) ==
         output.direct_landed_vassal_character_ids.end();
}

bool CharacterBelongsToPlayerSubrealm(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access, void *character,
    void *character_fallback, void *player_character, bool &belongs) noexcept {
  belongs = false;
  void *current = character;
  for (std::int32_t depth = 0; depth < kMaximumLiegeDepth; ++depth) {
    if (current == player_character) {
      belongs = true;
      return true;
    }
    if (current == nullptr || current == character_fallback) {
      return true;
    }
    std::int32_t current_id = -1;
    if (!ReadValue(access, current, kCharacterIdentityOffset, current_id) ||
        ResolveComponent(access, environment.character_storage_slot,
                         environment.character_fallback_slot, current_id,
                         kCharacterIdentityOffset) != current) {
      return false;
    }
    void *liege = nullptr;
    if (!InvokeResolver(environment.immediate_liege, current, liege)) {
      return false;
    }
    if (liege == nullptr || liege == character_fallback || liege == current) {
      return true;
    }
    current = liege;
  }
  return false;
}

struct ProvinceObservationV1 {
  void *province = nullptr;
  std::int32_t holder_character_id = -1;
  bool belongs_to_player_subrealm = false;
};
bool ReadAdjacentExternalProvinceHolders(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access, ObservationV1 &output) noexcept {
  void *province_array = nullptr;
  std::int32_t province_count = 0;
  void *character_fallback = nullptr;
  if (!ReadValue(access, output.game_data, kGameDataProvinceArrayOffset,
                 province_array) ||
      !ReadValue(access, output.game_data, kGameDataProvinceCountOffset,
                 province_count) ||
      !ReadSlot(access, environment.character_fallback_slot,
                character_fallback) ||
      province_array == nullptr || province_count <= 0 ||
      province_count > kMaximumProvinces) {
    return false;
  }

  std::vector<ProvinceObservationV1> provinces;
  try {
    provinces.resize(static_cast<std::size_t>(province_count));
  } catch (...) {
    return false;
  }
  for (std::int32_t index = 0; index < province_count; ++index) {
    void *province = nullptr;
    if (!ReadValue(access, province_array,
                   static_cast<std::size_t>(index) * sizeof(void *),
                   province)) {
      return false;
    }
    if (province == nullptr) {
      continue;
    }
    std::int32_t observed_province_id = -1;
    std::int32_t holder_character_id = -1;
    if (!ReadValue(access, province, kProvinceIdentityOffset,
                   observed_province_id) ||
        observed_province_id != index ||
        !InvokeProvinceHolderCharacterId(
            environment.province_holder_character_id, province,
            holder_character_id)) {
      return false;
    }
    auto &observed = provinces[static_cast<std::size_t>(index)];
    observed.province = province;
    if (holder_character_id == -1) {
      continue;
    }
    if (holder_character_id <= 0) {
      return false;
    }
    void *holder =
        ResolveComponent(access, environment.character_storage_slot,
                         environment.character_fallback_slot,
                         holder_character_id, kCharacterIdentityOffset);
    void *death = nullptr;
    if (holder == nullptr ||
        !ReadValue(access, holder, kCharacterDeathMarkerOffset, death) ||
        death != nullptr ||
        !CharacterBelongsToPlayerSubrealm(
            environment, access, holder, character_fallback,
            output.player_character, observed.belongs_to_player_subrealm)) {
      return false;
    }
    observed.holder_character_id = holder_character_id;
  }

  output.adjacent_external_province_holder_character_ids.clear();
  for (const auto &origin : provinces) {
    if (origin.province == nullptr || origin.holder_character_id <= 0 ||
        !origin.belongs_to_player_subrealm) {
      continue;
    }
    void *map_node = nullptr;
    void *adjacency_rows = nullptr;
    std::int32_t adjacency_count = 0;
    if (!ReadValue(access, origin.province, kProvinceMapNodeOffset, map_node) ||
        map_node == nullptr ||
        !ReadValue(access, map_node, kMapNodeAdjacencyDataOffset,
                   adjacency_rows) ||
        !ReadValue(access, map_node, kMapNodeAdjacencyCountOffset,
                   adjacency_count) ||
        adjacency_count < 0 || adjacency_count > kMaximumAdjacencyRows ||
        (adjacency_count > 0 && adjacency_rows == nullptr)) {
      return false;
    }
    for (std::int32_t row_index = 0; row_index < adjacency_count; ++row_index) {
      const auto row_offset =
          static_cast<std::size_t>(row_index) * kAdjacencyRowStride;
      std::int32_t raw_kind = -1;
      std::int32_t target_province_id = -1;
      if (!ReadValue(access, adjacency_rows,
                     row_offset + kAdjacencyRowKindOffset, raw_kind) ||
          !ReadValue(access, adjacency_rows,
                     row_offset + kAdjacencyRowTargetProvinceIdOffset,
                     target_province_id) ||
          raw_kind < 0 || raw_kind > 3 || target_province_id <= 0 ||
          target_province_id >= province_count) {
        return false;
      }
      const auto &target =
          provinces[static_cast<std::size_t>(target_province_id)];
      if (target.province == nullptr) {
        return false;
      }
      if (target.holder_character_id <= 0 ||
          target.belongs_to_player_subrealm) {
        continue;
      }
      try {
        output.adjacent_external_province_holder_character_ids.push_back(
            target.holder_character_id);
      } catch (...) {
        return false;
      }
    }
  }
  std::sort(output.adjacent_external_province_holder_character_ids.begin(),
            output.adjacent_external_province_holder_character_ids.end());
  output.adjacent_external_province_holder_character_ids.erase(
      std::unique(
          output.adjacent_external_province_holder_character_ids.begin(),
          output.adjacent_external_province_holder_character_ids.end()),
      output.adjacent_external_province_holder_character_ids.end());
  return true;
}

bool ReadRelatedCharacterContext(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access, const ObservationV1 &root,
    std::int32_t character_id, std::string_view relationship_role,
    game::CampaignRootRelatedCharacterV1 &output) noexcept {
  output = {};
  void *character = ResolveComponent(
      access, environment.character_storage_slot,
      environment.character_fallback_slot, character_id,
      kCharacterIdentityOffset);
  void *death = nullptr;
  if (character == nullptr ||
      !ReadValue(access, character, kCharacterDeathMarkerOffset, death) ||
      death != nullptr) {
    return false;
  }

  void *title_fallback = nullptr;
  void *primary_title = nullptr;
  std::int32_t title_id = -1;
  void *title_template = nullptr;
  std::int32_t tier_raw = 0;
  if (!ReadSlot(access, environment.landed_title_fallback_slot,
                title_fallback) ||
      !InvokeResolver(environment.primary_title, character, primary_title) ||
      primary_title == nullptr || primary_title == title_fallback ||
      !ReadValue(access, primary_title, kLandedTitleIdentityOffset,
                 title_id) ||
      ResolveComponent(access, environment.landed_title_storage_slot,
                       environment.landed_title_fallback_slot, title_id,
                       kLandedTitleIdentityOffset) != primary_title ||
      !ReadValue(access, primary_title, kLandedTitleTemplateOffset,
                 title_template) ||
      title_template == nullptr ||
      !ReadValue(access, title_template, kLandedTitleTierOffset, tier_raw)) {
    return false;
  }
  const auto tier_key = TierKey(tier_raw);
  if (tier_key.empty()) {
    return false;
  }

  void *capital = nullptr;
  if (!InvokeResolver(environment.capital_province, character, capital)) {
    return false;
  }
  if (capital != nullptr) {
    std::uint32_t province_tag = 0;
    if (!ReadValue(access, capital, 0x85C, province_tag)) return false;
    if (province_tag != 0x50726F76U) capital = nullptr;
  }
  if (capital != nullptr) {
    std::int32_t province_id = -1;
    void *province_array = nullptr;
    std::int32_t province_count = 0;
    void *indexed = nullptr;
    if (!ReadValue(access, capital, kProvinceIdentityOffset, province_id) ||
        province_id <= 0 ||
        !ReadValue(access, root.game_data, kGameDataProvinceArrayOffset,
                   province_array) ||
        !ReadValue(access, root.game_data, kGameDataProvinceCountOffset,
                   province_count) ||
        province_array == nullptr || province_count <= 0 ||
        province_count > kMaximumProvinces ||
        province_id >= province_count ||
        !ReadValue(access, province_array,
                   static_cast<std::size_t>(province_id) * sizeof(void *),
                   indexed) ||
        indexed != capital) {
      return false;
    }
    output.capital_province_id = province_id;
  }

  void *character_fallback = nullptr;
  void *immediate_liege = nullptr;
  void *top_liege = nullptr;
  if (!ReadSlot(access, environment.character_fallback_slot,
                character_fallback) ||
      !InvokeResolver(environment.immediate_liege, character,
                      immediate_liege) ||
      !InvokeResolver(environment.top_liege, character, top_liege)) {
    return false;
  }
  if (immediate_liege != nullptr && immediate_liege != character_fallback &&
      immediate_liege != character) {
    std::int32_t immediate_liege_id = -1;
    if (!ReadValue(access, immediate_liege, kCharacterIdentityOffset,
                   immediate_liege_id) ||
        ResolveComponent(access, environment.character_storage_slot,
                         environment.character_fallback_slot,
                         immediate_liege_id, kCharacterIdentityOffset) !=
            immediate_liege) {
      return false;
    }
    output.immediate_liege_character_id = immediate_liege_id;
  }
  if (top_liege == nullptr || top_liege == character_fallback ||
      !ReadValue(access, top_liege, kCharacterIdentityOffset,
                 output.top_liege_character_id) ||
      ResolveComponent(access, environment.character_storage_slot,
                       environment.character_fallback_slot,
                       output.top_liege_character_id,
                       kCharacterIdentityOffset) != top_liege) {
    return false;
  }
  output.independent = !output.immediate_liege_character_id.has_value();
  if ((output.independent && output.top_liege_character_id != character_id) ||
      (!output.independent && output.top_liege_character_id == character_id)) {
    return false;
  }

  if (relationship_role == "direct_landed_vassal") {
    if (output.immediate_liege_character_id != root.player_character_id ||
        output.top_liege_character_id != root.top_liege_character_id) {
      return false;
    }
  } else if (relationship_role ==
             "adjacent_external_province_holder") {
    bool belongs = false;
    if (!CharacterBelongsToPlayerSubrealm(
            environment, access, character, character_fallback,
            root.player_character, belongs) ||
        belongs) {
      return false;
    }
  } else {
    return false;
  }

  try {
    output.character_id = character_id;
    output.relationship_role.assign(relationship_role);
    output.primary_title =
        {title_id, tier_raw, std::string(tier_key)};
  } catch (...) {
    output = {};
    return false;
  }
  return true;
}

bool ReadRelatedCharacterContexts(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access, ObservationV1 &output) noexcept {
  output.related_character_contexts.clear();
  try {
    output.related_character_contexts.reserve(
        output.direct_landed_vassal_character_ids.size() +
        output.adjacent_external_province_holder_character_ids.size());
  } catch (...) {
    return false;
  }
  for (const auto character_id :
       output.direct_landed_vassal_character_ids) {
    game::CampaignRootRelatedCharacterV1 related{};
    if (!ReadRelatedCharacterContext(
            environment, access, output, character_id,
            "direct_landed_vassal", related)) {
      return false;
    }
    try {
      output.related_character_contexts.push_back(std::move(related));
    } catch (...) {
      return false;
    }
  }
  for (const auto character_id :
       output.adjacent_external_province_holder_character_ids) {
    game::CampaignRootRelatedCharacterV1 related{};
    if (!ReadRelatedCharacterContext(
            environment, access, output, character_id,
            "adjacent_external_province_holder", related)) {
      return false;
    }
    try {
      output.related_character_contexts.push_back(std::move(related));
    } catch (...) {
      return false;
    }
  }
  std::sort(output.related_character_contexts.begin(),
            output.related_character_contexts.end(),
            [](const auto &left, const auto &right) {
              return left.character_id < right.character_id;
            });
  return std::adjacent_find(
             output.related_character_contexts.begin(),
             output.related_character_contexts.end(),
             [](const auto &left, const auto &right) {
               return left.character_id == right.character_id;
             }) == output.related_character_contexts.end();
}

} // namespace

void BindNonwarRealm12002(CampaignRootNativeEnvironmentV1 &environment,
                         std::uintptr_t module_base) noexcept {
  if (!environment.exact_build_admitted || module_base == 0) return;
  environment.title_province = reinterpret_cast<NativeCampaignRootCharacterResolverV1>(
      module_base + kNonwarRealmTitleProvinceRva);
  environment.province_holder_character_id =
      reinterpret_cast<ck3_11906::NativeCampaignRootProvinceHolderCharacterIdV1>(
          module_base + kNonwarRealmProvinceHolderCharacterIdRva);
}

bool ReadNonwarRealmProjection12002(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access,
    const NonwarRealmInput12002 &input,
    NonwarRealmProjection12002 &output,
    std::string_view &failure,
    HeldTitlePartitionFailure12002 *failure_diagnostic) noexcept {
  output = {};
  if (failure_diagnostic != nullptr) {
    const auto sample = failure_diagnostic->sample;
    *failure_diagnostic = {};
    failure_diagnostic->sample = sample;
    failure_diagnostic->actor_id = input.player_character_id;
    failure_diagnostic->primary_title_id = input.primary_title ? input.primary_title->title_id : -1;
  }
  try {
    if (!environment.exact_build_admitted ||
        (!environment.offline_fixture_function_overrides &&
         (environment.module_base == 0 ||
          reinterpret_cast<std::uintptr_t>(environment.title_province) !=
              environment.module_base + kNonwarRealmTitleProvinceRva ||
          reinterpret_cast<std::uintptr_t>(environment.province_holder_character_id) !=
              environment.module_base + kNonwarRealmProvinceHolderCharacterIdRva)) ||
        environment.title_province == nullptr ||
        environment.province_holder_character_id == nullptr ||
        environment.primary_title == nullptr ||
        environment.capital_province == nullptr ||
        environment.immediate_liege == nullptr ||
        environment.top_liege == nullptr ||
        access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      failure = "unsupported_build";
      return false;
    }
    if (input.game_data == nullptr || input.player_character == nullptr ||
        input.player_character_id <= 0 ||
        ResolveComponent(access, environment.character_storage_slot,
                         environment.character_fallback_slot,
                         input.player_character_id, kCharacterIdentityOffset) !=
            input.player_character) {
      failure = "player_character_generation_mismatch";
      return false;
    }
    ObservationV1 observed{};
    static_cast<NonwarRealmInput12002 &>(observed) = input;
    void *land_state = nullptr;
    if (!ReadValue(access, input.player_character,
                   kNonwarRealmCharacterLandStateOffset, land_state)) {
      failure = "held_title_partition_unavailable";
      if (failure_diagnostic != nullptr) failure_diagnostic->guard = "player_land_state_read";
      return false;
    }
    if (!ReadPrimaryTitleSuccession(environment, access, observed)) {
      failure = "primary_title_succession_unavailable";
      return false;
    }
    if (!ReadHeldTitlePartition(environment, access, land_state, observed, failure_diagnostic)) {
      failure = "held_title_partition_unavailable";
      return false;
    }
    if (!ReadDirectLandedVassals(environment, access, observed)) {
      failure = "direct_landed_vassals_unavailable";
      return false;
    }
    if (!ReadAdjacentExternalProvinceHolders(environment, access, observed)) {
      failure = "adjacent_external_province_holders_unavailable";
      return false;
    }
    if (!ReadRelatedCharacterContexts(environment, access, observed)) {
      failure = "related_character_contexts_unavailable";
      return false;
    }
    output = std::move(static_cast<NonwarRealmProjection12002 &>(observed));
    failure = {};
    return true;
  } catch (...) {
    output = {};
    failure = "internal_error";
    return false;
  }
}
} // namespace xar::ck3_12002
