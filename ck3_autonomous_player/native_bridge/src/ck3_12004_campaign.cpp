#include "xar_bridge/ck3_12004_campaign.hpp"

#include "xar_bridge/ck3_12002_nonwar_metrics.hpp"
#include "xar_bridge/ck3_12002_nonwar_council.hpp"
#include "xar_bridge/ck3_12002_nonwar_realm.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <charconv>
#include <optional>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <utility>
#include <vector>

namespace xar::ck3_12004 {
using ck3_12002::NativeCampaignRootCharacterResolverV1;
using ck3_12002::NativeCampaignRootScriptIdentifierNameV1;
using ck3_12002::NonwarMetricsProjection12002;
using ck3_12002::NonwarRealmInput12002;
using ck3_12002::NonwarRealmProjection12002;
using ck3_12002::HeldTitlePartitionFailure12002;

namespace campaign_root_detail {
bool ReadMetricsProjection(const CampaignRootNativeEnvironmentV1&,
    const CampaignRootAccessV1&, void*, NonwarMetricsProjection12002&,
    std::string_view&) noexcept;
bool ReadRealmProjection(const CampaignRootNativeEnvironmentV1&,
    const CampaignRootAccessV1&, const NonwarRealmInput12002&,
    NonwarRealmProjection12002&, std::string_view&,
    HeldTitlePartitionFailure12002*) noexcept;
bool ReadCouncilProjection(const CampaignRootNativeEnvironmentV1&,
    const CampaignRootAccessV1&, void*, std::int32_t, bool,
    game::CampaignRootCouncilV1&, std::string_view&) noexcept;
void PopulateEnvironment(CampaignRootNativeEnvironmentV1&,
    std::uintptr_t) noexcept;
} // namespace campaign_root_detail

namespace {

constexpr std::size_t kGameStateGameDataOffset = 0xA0;
constexpr std::size_t kJominiPlayersOffset = 0x18;
constexpr std::size_t kPlayersLocalPlayerIdOffset = 0x1F0;
constexpr std::size_t kGameDataPlayerManagerOffset = 0x222E8;
constexpr std::size_t kPlayerManagerEntriesOffset = 0x58;
constexpr std::size_t kPlayerManagerCountOffset = 0x64;
constexpr std::size_t kPlayerEntryCharacterIdOffset = 0xB0;
constexpr std::size_t kPlayerEntryPlayerIdOffset = 0xD8;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kCharacterDeathMarkerOffset = 0x1D0;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::size_t kLandedTitleIdentityOffset = 0x10;
constexpr std::size_t kLandedTitleTemplateOffset = 0x48;
constexpr std::size_t kLandedTitleTierOffset = 0x64;
constexpr std::size_t kProvinceIdentityOffset = 0x10;
constexpr std::size_t kProvinceTypeTagOffset = 0x85C;
constexpr std::uint32_t kProvinceTypeTag = 0x50726F76U;
constexpr std::size_t kGameDataProvinceArrayOffset = 0x140;
constexpr std::size_t kGameDataProvinceCountOffset = 0x14C;
constexpr std::size_t kGovernmentKeyOffset = 0x18;
constexpr std::size_t kGovernmentFlagsOffset = 0x50;
constexpr std::size_t kSpanCountOffset = 0x0C;
constexpr std::size_t kSelectedRuleTokenDataOffset = 0x08;
constexpr std::size_t kSelectedRuleTokenCountOffset = 0x14;
constexpr std::size_t kRuleSettingTokenKeyOffset = 0x18;
constexpr std::size_t kMsvcStringSizeOffset = 0x10;
constexpr std::size_t kMsvcStringCapacityOffset = 0x18;
constexpr std::size_t kMsvcStringInlineCapacity = 0x0F;
constexpr std::int32_t kMaximumComponentSlots = 4'194'304;
constexpr std::int32_t kMaximumPlayerEntries = 1'024;
constexpr std::int32_t kMaximumGovernmentFlags = 4'096;
constexpr std::int32_t kMaximumSelectedRuleTokens = 16'384;
constexpr std::size_t kMaximumStableKeyBytes = 1'024;

bool Utf8BytewiseLess(std::string_view left,
                      std::string_view right) noexcept {
  return std::lexicographical_compare(
      left.begin(), left.end(), right.begin(), right.end(),
      [](char left_byte, char right_byte) noexcept {
        return static_cast<unsigned char>(left_byte) <
               static_cast<unsigned char>(right_byte);
      });
}

struct ObservationV1 {
  std::int32_t local_player_id = -1;
  std::int32_t player_character_id = -1;
  bool player_character_alive = false;
  NonwarMetricsProjection12002 metrics;
  game::CampaignRootCouncilV1 council;
  NonwarRealmProjection12002 realm;
  std::optional<game::CampaignRootTitleV1> primary_title;
  std::optional<std::int32_t> capital_province_id;
  std::optional<std::int32_t> immediate_liege_character_id;
  std::int32_t top_liege_character_id = -1;
  bool independent = false;
  std::optional<game::CampaignRootGovernmentV1> government;
  std::vector<std::string> selected_game_rule_tokens;
  std::int32_t native_selected_game_rule_token_count = 0;
  bool selected_game_rule_tokens_available = false;

  void *game_data = nullptr;
  void *player_character = nullptr;
  void *primary_title_pointer = nullptr;
  void *capital_province_pointer = nullptr;
  void *immediate_liege_pointer = nullptr;
  void *top_liege_pointer = nullptr;
  void *government_pointer = nullptr;
  void *government_flags_data = nullptr;
  void *selection_service = nullptr;
  void *selected_rule_set = nullptr;
  void *selected_rule_data = nullptr;
  std::vector<void *> selected_rule_token_pointers;
  std::vector<std::string> selected_rule_tokens_native_order;

  friend bool operator==(const ObservationV1 &,
                         const ObservationV1 &) = default;
};

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

template <typename Value>
bool ReadSlot(const CampaignRootAccessV1 &access, const Value *slot,
              Value &output) noexcept {
  return ReadBytes(access, slot, &output, sizeof(output));
}

bool ReadNativeString(const CampaignRootAccessV1 &access,
                      const void *native_string,
                      std::string &output) noexcept {
  output.clear();
  if (native_string == nullptr) {
    return false;
  }
  if (access.read_string != nullptr) {
    return access.read_string(access.context, native_string, output) &&
           !output.empty() && output.size() <= kMaximumStableKeyBytes;
  }

  std::size_t size = 0;
  std::size_t capacity = 0;
  if (!ReadValue(access, native_string, kMsvcStringSizeOffset, size) ||
      !ReadValue(access, native_string, kMsvcStringCapacityOffset, capacity) ||
      size == 0 || size > capacity || size > kMaximumStableKeyBytes) {
    return false;
  }
  const void *bytes = native_string;
  if (capacity > kMsvcStringInlineCapacity) {
    if (!ReadValue(access, native_string, 0, bytes) || bytes == nullptr) {
      return false;
    }
  }
  try {
    output.resize(size);
  } catch (...) {
    output.clear();
    return false;
  }
  if (!ReadBytes(access, bytes, output.data(), size)) {
    output.clear();
    return false;
  }
  return std::none_of(output.begin(), output.end(), [](unsigned char value) {
    return value == 0 || value < 0x20U;
  });
}

bool EnvironmentIsExact(
    const CampaignRootNativeEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted || environment.game_state_slot == nullptr ||
      environment.jomini_state_slot == nullptr ||
      environment.character_storage_slot == nullptr ||
      environment.character_fallback_slot == nullptr ||
      environment.landed_title_storage_slot == nullptr ||
      environment.landed_title_fallback_slot == nullptr ||
      environment.government_fallback_slot == nullptr ||
      environment.active_council_task_storage_slot == nullptr ||
      environment.active_council_task_fallback_slot == nullptr ||
      environment.game_rule_selection_service_slot == nullptr ||
      environment.game_rule_token_fallback_slot == nullptr ||
      environment.monthly_gold_income == nullptr ||
      environment.health == nullptr ||
      environment.domain_size == nullptr ||
      environment.domain_limit == nullptr ||
      environment.council_value_progress_current == nullptr ||
      environment.council_value_progress_maximum == nullptr ||
      environment.primary_title == nullptr ||
      environment.title_province == nullptr ||
      environment.capital_province == nullptr ||
      environment.immediate_liege == nullptr ||
      environment.top_liege == nullptr ||
      environment.government == nullptr ||
      environment.province_holder_character_id == nullptr ||
      environment.script_identifier_name == nullptr) return false;
  // Retain the existing caller-owned fixture contract; production binders leave
  // this flag false and always compare independently populated actual4 pointers.
  if (environment.offline_fixture_function_overrides) return true;
  const auto expected = BindCampaignRootNativeEnvironmentV1(
      environment.module_base, kExecutableSha256);
  return expected.exact_build_admitted &&
      environment.game_state_slot == expected.game_state_slot &&
      environment.jomini_state_slot == expected.jomini_state_slot &&
      environment.character_storage_slot == expected.character_storage_slot &&
      environment.character_fallback_slot == expected.character_fallback_slot &&
      environment.landed_title_storage_slot == expected.landed_title_storage_slot &&
      environment.landed_title_fallback_slot == expected.landed_title_fallback_slot &&
      environment.government_fallback_slot == expected.government_fallback_slot &&
      environment.active_council_task_storage_slot == expected.active_council_task_storage_slot &&
      environment.active_council_task_fallback_slot == expected.active_council_task_fallback_slot &&
      environment.game_rule_selection_service_slot == expected.game_rule_selection_service_slot &&
      environment.game_rule_token_fallback_slot == expected.game_rule_token_fallback_slot &&
      environment.monthly_gold_income == expected.monthly_gold_income &&
      environment.max_monthly_maintenance == expected.max_monthly_maintenance &&
      environment.health == expected.health &&
      environment.domain_size == expected.domain_size &&
      environment.domain_limit == expected.domain_limit &&
      environment.council_value_progress_current == expected.council_value_progress_current &&
      environment.council_value_progress_maximum == expected.council_value_progress_maximum &&
      environment.primary_title == expected.primary_title &&
      environment.title_province == expected.title_province &&
      environment.capital_province == expected.capital_province &&
      environment.immediate_liege == expected.immediate_liege &&
      environment.top_liege == expected.top_liege &&
      environment.government == expected.government &&
      environment.province_holder_character_id == expected.province_holder_character_id &&
      environment.script_identifier_name == expected.script_identifier_name &&
      environment.monthly_piety == expected.monthly_piety &&
      environment.task_owner_monthly_piety == expected.task_owner_monthly_piety;
}

void SetUnavailable(game::CampaignRootContextV1 &output,
                    std::string_view reason) {
  const auto revision = output.snapshot_revision;
  const auto date_raw = output.date_raw;
  output = {};
  output.snapshot_revision = revision;
  output.date_raw = date_raw;
  output.status = game::CampaignRootContextStatusV1::unavailable;
  output.unavailable_reason.assign(reason);
}

void *ResolveComponent(const CampaignRootAccessV1 &access,
                       void *const *storage_slot,
                       void *const *fallback_slot, std::int32_t full_id,
                       std::size_t identity_offset) noexcept {
  if (full_id <= 0) {
    return nullptr;
  }
  void *storage = nullptr;
  void *fallback = nullptr;
  if (!ReadSlot(access, storage_slot, storage) ||
      !ReadSlot(access, fallback_slot, fallback) || storage == nullptr) {
    return nullptr;
  }
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!ReadValue(access, storage, kStorageSlotsOffset, slots) ||
      !ReadValue(access, storage, kStorageCapacityOffset, capacity) ||
      slots == nullptr || capacity <= 0 || capacity > kMaximumComponentSlots) {
    return nullptr;
  }
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *object = nullptr;
  const auto offset = static_cast<std::size_t>(index) * kStorageSlotStride +
                      kStorageObjectOffset;
  std::int32_t observed_id = -1;
  if (!ReadValue(access, slots, offset, object) || object == nullptr ||
      object == fallback ||
      !ReadValue(access, object, identity_offset, observed_id) ||
      observed_id != full_id) {
    return nullptr;
  }
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

bool InvokeIdentifierName(
    NativeCampaignRootScriptIdentifierNameV1 resolver,
    std::int32_t identifier, const std::string *&output) noexcept {
  output = nullptr;
#if defined(_MSC_VER)
  __try {
    output = resolver(identifier);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = resolver(identifier);
  return true;
#endif
}

using SelectedRuleSetResolverV1 = void *(*)(void *service);

bool InvokeSelectedRuleSet(const CampaignRootAccessV1 &access, void *service,
                           void *&output) noexcept {
  output = nullptr;
  void *vtable = nullptr;
  SelectedRuleSetResolverV1 resolver = nullptr;
  if (!ReadValue(access, service, 0, vtable) || vtable == nullptr ||
      !ReadValue(access, vtable, 0x10, resolver) || resolver == nullptr) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    output = resolver(service);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = resolver(service);
  return true;
#endif
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

bool ReadPlayerIdentity(const CampaignRootNativeEnvironmentV1 &environment,
                        const CampaignRootAccessV1 &access,
                        ObservationV1 &output) noexcept {
  void *game_state = nullptr;
  void *jomini_state = nullptr;
  if (!ReadSlot(access, environment.game_state_slot, game_state) ||
      !ReadSlot(access, environment.jomini_state_slot, jomini_state) ||
      game_state == nullptr || jomini_state == nullptr ||
      !ReadValue(access, game_state, kGameStateGameDataOffset,
                 output.game_data) ||
      output.game_data == nullptr) {
    return false;
  }
  void *players = nullptr;
  if (!ReadValue(access, jomini_state, kJominiPlayersOffset, players) ||
      players == nullptr ||
      !ReadValue(access, players, kPlayersLocalPlayerIdOffset,
                 output.local_player_id) ||
      output.local_player_id < 0) {
    return false;
  }

  const void *manager = nullptr;
  if (!CheckedAddress(output.game_data, kGameDataPlayerManagerOffset,
                      manager)) {
    return false;
  }
  void *entries = nullptr;
  std::int32_t count = 0;
  if (!ReadValue(access, manager, kPlayerManagerEntriesOffset, entries) ||
      !ReadValue(access, manager, kPlayerManagerCountOffset, count) ||
      count <= 0 || count > kMaximumPlayerEntries || entries == nullptr) {
    return false;
  }
  std::int32_t matches = 0;
  for (std::int32_t index = 0; index < count; ++index) {
    void *entry = nullptr;
    std::int32_t player_id = -1;
    if (!ReadValue(access, entries, static_cast<std::size_t>(index) * 8,
                   entry)) {
      return false;
    }
    if (entry == nullptr) {
      continue;
    }
    if (!ReadValue(access, entry, kPlayerEntryPlayerIdOffset, player_id)) {
      return false;
    }
    if (player_id != output.local_player_id) {
      continue;
    }
    if (!ReadValue(access, entry, kPlayerEntryCharacterIdOffset,
                   output.player_character_id) ||
        output.player_character_id <= 0) {
      return false;
    }
    ++matches;
  }
  if (matches != 1) {
    return false;
  }
  output.player_character = ResolveComponent(
      access, environment.character_storage_slot,
      environment.character_fallback_slot, output.player_character_id,
      kCharacterIdentityOffset);
  if (output.player_character == nullptr) {
    return false;
  }
  void *death = nullptr;
  if (!ReadValue(access, output.player_character,
                 kCharacterDeathMarkerOffset, death)) {
    return false;
  }
  output.player_character_alive = death == nullptr;
  return true;
}

bool ReadPrimaryTitle(const CampaignRootNativeEnvironmentV1 &environment,
                      const CampaignRootAccessV1 &access,
                      ObservationV1 &output) noexcept {
  void *fallback = nullptr;
  if (!ReadSlot(access, environment.landed_title_fallback_slot, fallback) ||
      !InvokeResolver(environment.primary_title, output.player_character,
                      output.primary_title_pointer)) {
    return false;
  }
  if (output.primary_title_pointer == nullptr ||
      output.primary_title_pointer == fallback) {
    output.primary_title_pointer = nullptr;
    output.primary_title.reset();
    return true;
  }
  std::int32_t title_id = -1;
  void *title_template = nullptr;
  std::int32_t tier_raw = 0;
  if (!ReadValue(access, output.primary_title_pointer,
                 kLandedTitleIdentityOffset, title_id) ||
      ResolveComponent(access, environment.landed_title_storage_slot,
                       environment.landed_title_fallback_slot, title_id,
                       kLandedTitleIdentityOffset) !=
          output.primary_title_pointer ||
      !ReadValue(access, output.primary_title_pointer,
                 kLandedTitleTemplateOffset, title_template) ||
      title_template == nullptr ||
      !ReadValue(access, title_template, kLandedTitleTierOffset, tier_raw)) {
    return false;
  }
  const auto key = TierKey(tier_raw);
  if (key.empty()) {
    return false;
  }
  output.primary_title =
      game::CampaignRootTitleV1{title_id, tier_raw, std::string(key)};
  return true;
}

bool ReadCapital(const CampaignRootNativeEnvironmentV1 &environment,
                 const CampaignRootAccessV1 &access,
                 ObservationV1 &output) noexcept {
  if (!InvokeResolver(environment.capital_province, output.player_character,
                      output.capital_province_pointer)) {
    return false;
  }
  if (output.capital_province_pointer == nullptr) {
    output.capital_province_id.reset();
    return true;
  }
  // Native title bounds applies this same tag check after the capital
  // resolver. Its canonical no-province object is an observed absence.
  std::uint32_t province_tag = 0;
  if (!ReadValue(access, output.capital_province_pointer,
                 kProvinceTypeTagOffset, province_tag)) {
    return false;
  }
  if (province_tag != kProvinceTypeTag) {
    output.capital_province_pointer = nullptr;
    output.capital_province_id.reset();
    return true;
  }
  std::int32_t province_id = -1;
  void *provinces = nullptr;
  std::int32_t count = 0;
  void *indexed = nullptr;
  if (!ReadValue(access, output.capital_province_pointer,
                 kProvinceIdentityOffset, province_id) ||
      province_id <= 0 ||
      !ReadValue(access, output.game_data, kGameDataProvinceArrayOffset,
                 provinces) ||
      !ReadValue(access, output.game_data, kGameDataProvinceCountOffset,
                 count) ||
      provinces == nullptr || count <= 0 || province_id >= count ||
      !ReadValue(access, provinces,
                 static_cast<std::size_t>(province_id) * 8, indexed) ||
      indexed != output.capital_province_pointer) {
    return false;
  }
  output.capital_province_id = province_id;
  return true;
}

bool ReadLieges(const CampaignRootNativeEnvironmentV1 &environment,
                const CampaignRootAccessV1 &access,
                ObservationV1 &output) noexcept {
  void *fallback = nullptr;
  if (!ReadSlot(access, environment.character_fallback_slot, fallback) ||
      !InvokeResolver(environment.immediate_liege, output.player_character,
                      output.immediate_liege_pointer) ||
      !InvokeResolver(environment.top_liege, output.player_character,
                      output.top_liege_pointer)) {
    return false;
  }
  if (output.immediate_liege_pointer == nullptr ||
      output.immediate_liege_pointer == fallback ||
      output.immediate_liege_pointer == output.player_character) {
    output.immediate_liege_pointer = nullptr;
    output.immediate_liege_character_id.reset();
  } else {
    std::int32_t immediate_id = -1;
    if (!ReadValue(access, output.immediate_liege_pointer,
                   kCharacterIdentityOffset, immediate_id) ||
        ResolveComponent(access, environment.character_storage_slot,
                         environment.character_fallback_slot, immediate_id,
                         kCharacterIdentityOffset) !=
            output.immediate_liege_pointer) {
      return false;
    }
    output.immediate_liege_character_id = immediate_id;
  }
  if (output.top_liege_pointer == nullptr ||
      output.top_liege_pointer == fallback ||
      !ReadValue(access, output.top_liege_pointer, kCharacterIdentityOffset,
                 output.top_liege_character_id) ||
      ResolveComponent(access, environment.character_storage_slot,
                       environment.character_fallback_slot,
                       output.top_liege_character_id,
                       kCharacterIdentityOffset) != output.top_liege_pointer) {
    return false;
  }
  output.independent = !output.immediate_liege_character_id.has_value();
  return output.independent
             ? output.top_liege_character_id == output.player_character_id
             : output.top_liege_character_id != output.player_character_id;
}

bool ReadGovernment(const CampaignRootNativeEnvironmentV1 &environment,
                    const CampaignRootAccessV1 &access,
                    ObservationV1 &output) noexcept {
  void *fallback = nullptr;
  if (!ReadSlot(access, environment.government_fallback_slot, fallback) ||
      !InvokeResolver(environment.government, output.player_character,
                      output.government_pointer)) {
    return false;
  }
  if (output.government_pointer == nullptr ||
      output.government_pointer == fallback) {
    output.government_pointer = nullptr;
    output.government_flags_data = nullptr;
    output.government.reset();
    return true;
  }
  game::CampaignRootGovernmentV1 government{};
  const void *key_address = nullptr;
  if (!CheckedAddress(output.government_pointer, kGovernmentKeyOffset,
                      key_address) ||
      !ReadNativeString(access, key_address, government.key) ||
      !ReadValue(access, output.government_pointer, kGovernmentFlagsOffset,
                 output.government_flags_data) ||
      !ReadValue(access, output.government_pointer,
                 kGovernmentFlagsOffset + kSpanCountOffset,
                 government.native_flag_count) ||
      government.native_flag_count < 0 ||
      government.native_flag_count > kMaximumGovernmentFlags ||
      (government.native_flag_count > 0 &&
       output.government_flags_data == nullptr)) {
    return false;
  }
  try {
    government.flags.reserve(
        static_cast<std::size_t>(government.native_flag_count));
  } catch (...) {
    return false;
  }
  std::int32_t previous_identifier = std::numeric_limits<std::int32_t>::min();
  for (std::int32_t index = 0; index < government.native_flag_count; ++index) {
    std::int32_t identifier = -1;
    const std::string *name = nullptr;
    std::string copied;
    if (!ReadValue(access, output.government_flags_data,
                   static_cast<std::size_t>(index) * sizeof(identifier),
                   identifier) ||
        identifier < previous_identifier ||
        !InvokeIdentifierName(environment.script_identifier_name, identifier,
                              name) ||
        name == nullptr || !ReadNativeString(access, name, copied)) {
      return false;
    }
    previous_identifier = identifier;
    try {
      government.flags.push_back(std::move(copied));
    } catch (...) {
      return false;
    }
  }
  std::sort(government.flags.begin(), government.flags.end(),
            Utf8BytewiseLess);
  output.government = std::move(government);
  return true;
}

bool ReadSelectedRuleTokens(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access, ObservationV1 &output) noexcept {
  void *fallback = nullptr;
  if (!ReadSlot(access, environment.game_rule_selection_service_slot,
                output.selection_service) ||
      !ReadSlot(access, environment.game_rule_token_fallback_slot, fallback) ||
      output.selection_service == nullptr ||
      !InvokeSelectedRuleSet(access, output.selection_service,
                             output.selected_rule_set) ||
      output.selected_rule_set == nullptr ||
      !ReadValue(access, output.selected_rule_set,
                 kSelectedRuleTokenDataOffset, output.selected_rule_data) ||
      !ReadValue(access, output.selected_rule_set,
                 kSelectedRuleTokenCountOffset,
                 output.native_selected_game_rule_token_count) ||
      output.native_selected_game_rule_token_count < 0 ||
      output.native_selected_game_rule_token_count >
          kMaximumSelectedRuleTokens ||
      (output.native_selected_game_rule_token_count > 0 &&
       output.selected_rule_data == nullptr)) {
    return false;
  }
  try {
    const auto count = static_cast<std::size_t>(
        output.native_selected_game_rule_token_count);
    output.selected_rule_token_pointers.reserve(count);
    output.selected_rule_tokens_native_order.reserve(count);
  } catch (...) {
    return false;
  }
  for (std::int32_t index = 0;
       index < output.native_selected_game_rule_token_count; ++index) {
    void *token = nullptr;
    std::string key;
    const void *key_address = nullptr;
    if (!ReadValue(access, output.selected_rule_data,
                   static_cast<std::size_t>(index) * 8, token) ||
        token == nullptr || token == fallback ||
        !CheckedAddress(token, kRuleSettingTokenKeyOffset, key_address) ||
        !ReadNativeString(access, key_address, key)) {
      return false;
    }
    try {
      output.selected_rule_token_pointers.push_back(token);
      output.selected_rule_tokens_native_order.push_back(key);
    } catch (...) {
      return false;
    }
  }
  output.selected_game_rule_tokens =
      output.selected_rule_tokens_native_order;
  std::sort(output.selected_game_rule_tokens.begin(),
            output.selected_game_rule_tokens.end(), Utf8BytewiseLess);
  return true;
}

bool CouncilScopeIsAdmitted(const ObservationV1 &output) noexcept {
  if (!output.primary_title || !output.government) {
    return false;
  }
  const auto &flags = output.government->flags;
  return std::find(flags.begin(), flags.end(),
                   "government_is_landless_adventurer") == flags.end() &&
         std::find(flags.begin(), flags.end(), "government_is_nomadic") ==
             flags.end() &&
         std::find(flags.begin(), flags.end(), "government_is_celestial") ==
             flags.end();
}

// Exact Crozier numeric GetPietyBalance entry. The engine reads Character* at
// scope+0 and tag0 at+8; the remaining bytes are only our local zero storage.

bool ReadMonthlyPiety(const CampaignRootNativeEnvironmentV1 &environment,
                      void *character, game::FixedPointValue &output) noexcept {
  if (environment.monthly_piety == nullptr) {
    return false;
  }
  alignas(void *) std::byte scope[16]{};
  std::memcpy(scope, &character, sizeof(character));
  std::int64_t raw = 0;
#if defined(_MSC_VER)
  __try {
    if (environment.monthly_piety(scope, &raw, nullptr) != &raw) {
      return false;
    }
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  if (environment.monthly_piety(scope, &raw, nullptr) != &raw) {
    return false;
  }
#endif
  output = {raw, 100'000};
  return true;
}

bool ReadObservation(const CampaignRootNativeEnvironmentV1 &environment,
                     const CampaignRootAccessV1 &access,
                     ObservationV1 &output,
                     std::string_view &failure,
                     HeldTitlePartitionFailure12002 *failure_diagnostic) noexcept {
  output = {};
  if (!ReadPlayerIdentity(environment, access, output)) {
    failure = "player_identity_unavailable";
    return false;
  }
  if (!campaign_root_detail::ReadMetricsProjection(environment, access, output.player_character,
                             output.metrics, failure)) {
    return false;
  }
  if (!ReadPrimaryTitle(environment, access, output)) {
    failure = "primary_title_unavailable";
    return false;
  }
  if (!ReadCapital(environment, access, output)) {
    failure = "capital_unavailable";
    return false;
  }
  if (!ReadLieges(environment, access, output)) {
    failure = "lieges_unavailable";
    return false;
  }
  if (!ReadGovernment(environment, access, output)) {
    failure = "government_flags_unavailable";
    return false;
  }
  if (!campaign_root_detail::ReadCouncilProjection(
          environment, access, output.player_character,
          output.player_character_id, CouncilScopeIsAdmitted(output),
          output.council, failure)) {
    return false;
  }
  const NonwarRealmInput12002 realm_input{
      output.game_data, output.player_character, output.player_character_id,
      output.primary_title_pointer, output.primary_title,
      output.top_liege_character_id};
  if (!campaign_root_detail::ReadRealmProjection(
          environment, access, realm_input, output.realm, failure, failure_diagnostic)) {
    return false;
  }
  output.selected_game_rule_tokens_available =
      ReadSelectedRuleTokens(environment, access, output);
  if (!output.selected_game_rule_tokens_available) {
    output.selection_service = nullptr;
    output.selected_rule_set = nullptr;
    output.selected_rule_data = nullptr;
    output.selected_rule_token_pointers.clear();
    output.selected_rule_tokens_native_order.clear();
    output.selected_game_rule_tokens.clear();
    output.native_selected_game_rule_token_count = 0;
  }
  return true;
}

} // namespace

CampaignRootNativeEnvironmentV1 BindCampaignRootNativeEnvironmentV1(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  CampaignRootNativeEnvironmentV1 output{};
  if (!module_base || executable_sha256 != kExecutableSha256) return output;
  output.module_base = module_base;
  campaign_root_detail::PopulateEnvironment(output, module_base);
  output.exact_build_admitted = true;
  return output;
}

bool ReadCampaignRootTargetingFactionCountV1(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access,
    std::int32_t expected_player_character_id,
    std::int32_t &output) noexcept {
  output = 0;
  try {
    if (!environment.exact_build_admitted ||
        (environment.module_base == 0 &&
         !environment.offline_fixture_function_overrides) ||
        expected_player_character_id <= 0 || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      return false;
    }
    ObservationV1 observed{};
    void *land_state = nullptr;
    std::int32_t count = 0;
    if (!ReadPlayerIdentity(environment, access, observed) ||
        observed.player_character_id != expected_player_character_id ||
        !ReadValue(access, observed.player_character,
                   ck3_12002::kCampaignRootCharacterLandStateOffset12002, land_state) ||
        (land_state != nullptr &&
         (!ReadValue(access, land_state,
                     ck3_12002::kCampaignRootTargetingFactionCountOffset12002, count) ||
          count < 0)) ||
        ResolveComponent(access, environment.character_storage_slot,
                         environment.character_fallback_slot,
                         expected_player_character_id,
                         kCharacterIdentityOffset) != observed.player_character) {
      return false;
    }
    output = count;
    return true;
  } catch (...) {
    return false;
  }
}

game::ReadCampaignRootContextResultV1 ReadCampaignRootContextV1(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access,
    const CampaignRootContextRequestV1 &request,
    game::CampaignRootContextV1 &output,
    HeldTitlePartitionFailure12002 *failure_diagnostic) noexcept {
  if (failure_diagnostic != nullptr) *failure_diagnostic = {};
  output = {};
  output.snapshot_revision = request.expected_snapshot_revision;
  try {
    if (request.expected_snapshot_revision == 0 ||
        access.capture_frame == nullptr || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      SetUnavailable(output, "requires_application_main");
      return game::ReadCampaignRootContextResultV1::unavailable;
    }
    game::CampaignRootFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      SetUnavailable(output, "state_changed");
      return game::ReadCampaignRootContextResultV1::unavailable;
    }
    output.snapshot_revision = before.snapshot_revision;
    output.date_raw = before.date_raw;
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      SetUnavailable(output, "state_changed");
      return game::ReadCampaignRootContextResultV1::unavailable;
    }
    if (!before.paused) {
      SetUnavailable(output, "requires_paused");
      return game::ReadCampaignRootContextResultV1::unavailable;
    }
    if (!before.map_ready || !before.has_played_character ||
        before.played_character_id <= 0) {
      SetUnavailable(output, "map_not_ready");
      return game::ReadCampaignRootContextResultV1::unavailable;
    }
    if (!EnvironmentIsExact(environment)) {
      SetUnavailable(output, "unsupported_build");
      return game::ReadCampaignRootContextResultV1::unavailable;
    }

    ObservationV1 first{};
    ObservationV1 second{};
    std::string_view failure = "internal_error";
    if (failure_diagnostic != nullptr) failure_diagnostic->sample = 1;
    if (!ReadObservation(environment, access, first, failure, failure_diagnostic)) {
      SetUnavailable(output, failure);
      return game::ReadCampaignRootContextResultV1::unavailable;
    }
    if (first.player_character_id != before.played_character_id ||
        first.player_character_alive != before.played_character_alive) {
      SetUnavailable(output, "player_character_generation_mismatch");
      return game::ReadCampaignRootContextResultV1::unavailable;
    }
    game::FixedPointValue first_piety{};
    const bool first_piety_available =
        ReadMonthlyPiety(environment, first.player_character, first_piety);
    failure = "internal_error";
    if (failure_diagnostic != nullptr) failure_diagnostic->sample = 2;
    if (!ReadObservation(environment, access, second, failure, failure_diagnostic)) {
      SetUnavailable(output, failure);
      return game::ReadCampaignRootContextResultV1::unavailable;
    }
    game::FixedPointValue second_piety{};
    const bool second_piety_available =
        ReadMonthlyPiety(environment, second.player_character, second_piety);
    game::CampaignRootFrameV1 after{};
    if (!access.capture_frame(access.context, after) || after != before ||
        second != first) {
      SetUnavailable(output, "state_changed");
      return game::ReadCampaignRootContextResultV1::unavailable;
    }

    output.status = game::CampaignRootContextStatusV1::available;
    output.local_player_id = first.local_player_id;
    output.player_character_id = first.player_character_id;
    output.player_character_alive = first.player_character_alive;
    output.player_monthly_gold_income = {
        first.metrics.monthly_gold_income_raw, 100'000};
    if (first_piety_available && second_piety_available &&
        first_piety == second_piety) {
      output.player_monthly_piety_v1 = first_piety;
    }
    output.player_health = {first.metrics.health_raw, 100'000};
    output.player_legitimacy_v1 = std::move(first.metrics.legitimacy);
    output.player_max_monthly_gold_maintenance_v1 =
        std::move(first.metrics.max_monthly_gold_maintenance);
    output.player_domain_size = first.metrics.domain_size;
    output.player_domain_limit = first.metrics.domain_limit;
    output.player_targeting_faction_count =
        first.metrics.targeting_faction_count;
    output.council = std::move(first.council);
    output.primary_title = std::move(first.primary_title);
    output.primary_title_succession_character_ids =
        std::move(first.realm.primary_title_succession_character_ids);
    output.held_title_partition = std::move(first.realm.held_title_partition);
    output.capital_province_id = first.capital_province_id;
    output.immediate_liege_character_id =
        first.immediate_liege_character_id;
    output.top_liege_character_id = first.top_liege_character_id;
    output.independent = first.independent;
    output.direct_landed_vassal_character_ids =
        std::move(first.realm.direct_landed_vassal_character_ids);
    output.adjacent_external_province_holder_character_ids =
        std::move(first.realm.adjacent_external_province_holder_character_ids);
    output.related_character_contexts =
        std::move(first.realm.related_character_contexts);
    output.government = std::move(first.government);
    output.selected_game_rule_tokens =
        std::move(first.selected_game_rule_tokens);
    output.native_selected_game_rule_token_count =
        first.native_selected_game_rule_token_count;
    output.readiness.player_identity_ready = true;
    output.readiness.player_monthly_gold_income_ready = true;
    output.readiness.player_health_ready = true;
    output.readiness.player_domain_ready = true;
    output.readiness.player_targeting_factions_ready = true;
    output.readiness.primary_title_ready = true;
    output.readiness.primary_title_succession_ready = true;
    output.readiness.held_title_partition_ready = true;
    output.readiness.council_ready =
        output.council->status == game::CampaignRootCouncilStatusV1::available;
    output.readiness.capital_ready = true;
    output.readiness.lieges_ready = true;
    output.readiness.direct_landed_vassals_ready = true;
    output.readiness.adjacent_external_province_holders_ready = true;
    output.readiness.related_character_contexts_ready = true;
    output.readiness.government_ready = true;
    output.readiness.selected_game_rule_tokens_ready =
        first.selected_game_rule_tokens_available;
    output.readiness.same_frame_ready = true;
    output.readiness.ready = first.selected_game_rule_tokens_available;
    output.unavailable_reason.clear();
    return game::ReadCampaignRootContextResultV1::available;
  } catch (...) {
    SetUnavailable(output, "internal_error");
    return game::ReadCampaignRootContextResultV1::unavailable;
  }
}

} // namespace xar::ck3_12004

namespace xar::ck3_12004::campaign_root_detail {
// External parent integration fragment; insert inside xar::ck3_12004::campaign_root_detail.
// Caller has admitted actual4 and constructed an empty software Environment.
// Capital/top-liege and realm fields are merged from the sibling's saved proof.
void PopulateEnvironment(
    ck3_12002::CampaignRootNativeEnvironmentV1 &environment,
    std::uintptr_t base) noexcept {
  environment.module_base = base;
  environment.game_state_slot = reinterpret_cast<void **>(base + kGameStateSlotRva);
  environment.jomini_state_slot = reinterpret_cast<void **>(base + kJominiStateSlotRva);
  environment.character_storage_slot =
      reinterpret_cast<void **>(base + kCharacterStorageSlotRva);
  // Actual4 Core/Faction binding, held title resolution and shared collections.
  environment.character_fallback_slot = reinterpret_cast<void **>(base + 0x5C67570);
  environment.landed_title_storage_slot = reinterpret_cast<void **>(base + 0x5D1DAF8);
  environment.landed_title_fallback_slot = reinterpret_cast<void **>(base + 0x5D1DAE0);
  environment.primary_title = reinterpret_cast<decltype(environment.primary_title)>(
      base + 0x289DA10);
  environment.immediate_liege = reinterpret_cast<decltype(environment.immediate_liege)>(
      base + 0x28BFC50);

  // cash-terms-native/first01: complete1520B income and828B ten-slot getter.
  environment.monthly_gold_income =
      reinterpret_cast<decltype(environment.monthly_gold_income)>(base + 0x2BCA940);
  environment.max_monthly_maintenance =
      reinterpret_cast<decltype(environment.max_monthly_maintenance)>(base + 0x2C152B0);
  // Sole campaign-root-metrics-council/first01 complete callback proof.
  environment.health = reinterpret_cast<decltype(environment.health)>(base + 0x28C64E0);
  environment.domain_size =
      reinterpret_cast<decltype(environment.domain_size)>(base + 0x28B71E0);
  environment.domain_limit =
      reinterpret_cast<decltype(environment.domain_limit)>(base + 0x28B71B0);

  // Saved active-task314B source proves these slots independently unchanged.
  environment.active_council_task_storage_slot =
      reinterpret_cast<void **>(base + 0x5D1DEA0);
  environment.active_council_task_fallback_slot =
      reinterpret_cast<void **>(base + 0x5D1DDF8);
  environment.council_value_progress_current =
      reinterpret_cast<decltype(environment.council_value_progress_current)>(base + 0x31AB500);
  environment.council_value_progress_maximum =
      reinterpret_cast<decltype(environment.council_value_progress_maximum)>(base + 0x31AB820);

  // Typed actual4 Government resolver/key/flags and complete script-name body.
  environment.government_fallback_slot = reinterpret_cast<void **>(base + 0x5D1E2A8);
  environment.government = reinterpret_cast<decltype(environment.government)>(
      base + 0x28C2DF0);
  environment.script_identifier_name =
      reinterpret_cast<decltype(environment.script_identifier_name)>(base + 0x3F4F8E0);
  // Selected service+10/list8/count14: exact39B shared family source-use proof.
  environment.game_rule_selection_service_slot =
      reinterpret_cast<void **>(base + 0x5CB3D78);
  environment.game_rule_token_fallback_slot =
      reinterpret_cast<void **>(base + 0x5D37A70);

  environment.title_province = reinterpret_cast<decltype(environment.title_province)>(base + 0x230F8E0);
  environment.capital_province = reinterpret_cast<decltype(environment.capital_province)>(base + 0x28B1CB0);
  environment.top_liege = reinterpret_cast<decltype(environment.top_liege)>(base + 0x28BFD80);
  environment.province_holder_character_id = reinterpret_cast<decltype(environment.province_holder_character_id)>(base + 0x247D010);

  // The .2 software helper embeds unheld actual4 native addresses. Preserve
  // existing optional absence; do not install that helper or a guessed getter.
  environment.monthly_piety = nullptr;
  environment.task_owner_monthly_piety = nullptr;
}

// Insert inside xar::ck3_12004::campaign_root_detail; includes mirror the old metrics TU:
// <cstring>, <limits>, <windows.h> under _MSC_VER and old metrics header.

bool MetricsDirectRead(const void *address, void *output,
                       std::size_t size) noexcept {
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

template <typename T>
bool MetricsRead(const ck3_12002::CampaignRootAccessV1 &access,
                 const void *base, std::size_t offset, T &output) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(base);
  if (base == nullptr ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - address)
    return false;
  const auto *source = reinterpret_cast<const void *>(address + offset);
  if (access.read_memory != nullptr)
    return access.read_memory(access.context, source, &output, sizeof(output));
  return MetricsDirectRead(source, &output, sizeof(output));
}

bool MetricsIncome(ck3_11906::NativeCampaignRootMonthlyGoldIncomeV1 function,
                   void *character, std::int64_t &output) noexcept {
#if defined(_MSC_VER)
  __try {
    return function(&output, character, nullptr, nullptr) == &output;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  return function(&output, character, nullptr, nullptr) == &output;
#endif
}

bool MetricsHealth(ck3_11906::NativeCampaignRootCharacterFixedPointV1 function,
                   void *character, std::int64_t &output) noexcept {
#if defined(_MSC_VER)
  __try {
    return function(character, &output) == &output;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  return function(character, &output) == &output;
#endif
}

bool MetricsInteger(ck3_11906::NativeCampaignRootCharacterInt32V1 function,
                    void *character, std::int32_t &output) noexcept {
#if defined(_MSC_VER)
  __try {
    output = function(character);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  output = function(character);
  return true;
#endif
}

bool ReadMetricsProjection(
    const ck3_12002::CampaignRootNativeEnvironmentV1 &environment,
    const ck3_12002::CampaignRootAccessV1 &access, void *character,
    ck3_12002::NonwarMetricsProjection12002 &output,
    std::string_view &failure) noexcept {
  output = {};
  failure = {};
  if (character == nullptr || environment.monthly_gold_income == nullptr ||
      environment.health == nullptr || environment.domain_size == nullptr ||
      environment.domain_limit == nullptr) {
    failure = "nonwar_metrics_environment_unavailable";
    return false;
  }
  if (!MetricsIncome(environment.monthly_gold_income, character,
                     output.monthly_gold_income_raw)) {
    failure = "player_monthly_gold_income_unavailable";
    return false;
  }
  if (!MetricsHealth(environment.health, character, output.health_raw)) {
    failure = "player_health_unavailable";
    return false;
  }
  output.max_monthly_gold_maintenance =
      ck3_12002::ReadOptionalMaxMonthlyGoldMaintenance12003(
          environment.max_monthly_maintenance, character);
  if (!MetricsInteger(environment.domain_size, character, output.domain_size) ||
      !MetricsInteger(environment.domain_limit, character, output.domain_limit) ||
      output.domain_size < 0 || output.domain_limit < 1) {
    failure = "player_domain_unavailable";
    return false;
  }
  void *land_state = nullptr;
  if (!MetricsRead(access, character, 0x1C0, land_state) ||
      (land_state != nullptr &&
       (!MetricsRead(access, land_state, 0x12C, output.targeting_faction_count) ||
        output.targeting_faction_count < 0))) {
    failure = "player_targeting_factions_unavailable";
    return false;
  }
  // Character1C8/data28 source is not yet admitted for this actual image.
  // Keep the optional diagnostic precise and do not read those raw offsets.
  output.legitimacy.unavailable_reason =
      "actual4_legitimacy_field_source_unavailable";
  return true;
}

// External parent fragment; insert in xar::ck3_12004::campaign_root_detail.
// Current common provider preserves Council's precise optional unsupported state.
// Returned PositionType raw CString key18 lacks an actual typed source witness.
// No native object/key/memory is read by this branch. The full copied software
// implementation is retained in ReadCouncilProjection-deferred-source.txt.
bool ReadCouncilProjection(
    const ck3_12002::CampaignRootNativeEnvironmentV1 &,
    const ck3_12002::CampaignRootAccessV1 &, void *,
    std::int32_t character_id, bool standard_scope_admitted,
    game::CampaignRootCouncilV1 &output, std::string_view &failure) noexcept {
  output = {};
  output.coverage_key = "standard_landed_non_nomadic_core_v1";
  output.owner_character_id = character_id;
  failure = "council_unavailable";
  output.unavailable_reason = standard_scope_admitted
      ? "actual4_council_position_key_source_unavailable"
      : "outside_standard_landed_non_nomadic_core_scope";
  return true;
}

} // namespace xar::ck3_12004::campaign_root_detail

// Source6f37a4f6750403b60e203749adb1c24e9a78134d; full software realm.
// Paste physically after the parent TU's namespace xar::ck3_12004 closes.
// Parent owns actual4 PopulateEnvironment and all native proof bindings.
namespace xar::ck3_12004::campaign_root_detail {
using ck3_12002::NonwarRealmInput12002;
using ck3_12002::NonwarRealmProjection12002;
using ck3_12002::HeldTitlePartitionFailure12002;
namespace realm_detail {
using ck3_12002::NativeCampaignRootCharacterResolverV1;
constexpr std::size_t kCharacterLandStateOffset = 0x1C0;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kCharacterDeathMarkerOffset = 0x1D0;
constexpr std::size_t kLandStateHeldTitleIdsOffset = 0x1E0;
constexpr std::size_t kVectorCapacityOffset = 0x08;
constexpr std::size_t kVectorCountOffset = 0x0C;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::size_t kLandedTitleIdentityOffset = 0x10;
constexpr std::size_t kLandedTitleTemplateOffset = 0x48;
constexpr std::size_t kLandedTitleTierOffset = 0x64;
// Existing noble-family subtype operands, retained pending the finite
// actual4 source-use proof ledger. No preferred-capital substitution.
constexpr std::size_t kLandedTitleSuccessionDataOffset = 0x150;
constexpr std::size_t kLandedTitleSuccessionCapacityOffset = 0x158;
constexpr std::size_t kLandedTitleSuccessionCountOffset = 0x15C;
constexpr std::size_t kLandedTitleHolderCharacterIdOffset = 0x128;
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
        // Actual4 CTitle+30/+32 source-use proof is not yet held.
        // Geographic counties above already retain their complete partition.
        return fail("actual4_county_no_province_subtype_source_unavailable");
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

} // namespace realm_detail

bool ReadRealmProjection(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access,
    const NonwarRealmInput12002 &input,
    NonwarRealmProjection12002 &output,
    std::string_view &failure,
    HeldTitlePartitionFailure12002 *failure_diagnostic) noexcept {
  using namespace realm_detail;
  output = {};
  if (failure_diagnostic != nullptr) {
    const auto sample = failure_diagnostic->sample;
    *failure_diagnostic = {};
    failure_diagnostic->sample = sample;
    failure_diagnostic->actor_id = input.player_character_id;
    failure_diagnostic->primary_title_id = input.primary_title ? input.primary_title->title_id : -1;
  }
  try {
    const auto expected = ck3_12004::BindCampaignRootNativeEnvironmentV1(
        environment.module_base, ck3_12004::kExecutableSha256);
    if (!environment.exact_build_admitted ||
        (!environment.offline_fixture_function_overrides &&
         (environment.module_base == 0 ||
          environment.title_province != expected.title_province ||
          environment.province_holder_character_id !=
              expected.province_holder_character_id)) ||
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
                   kCharacterLandStateOffset, land_state)) {
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
} // namespace xar::ck3_12004::campaign_root_detail

namespace xar::ck3_12004::campaign_root_wire_detail {
namespace {
constexpr std::uintptr_t kCampaignRootMonthlyGoldIncomeRva = 0x2BCA940;
constexpr std::uintptr_t kCampaignRootHealthRva = 0x28C64E0;
constexpr std::uintptr_t kCampaignRootDomainSizeRva = 0x28B71E0;
constexpr std::uintptr_t kCampaignRootDomainLimitRva = 0x28B71B0;
constexpr std::uintptr_t kCampaignRootHasTargetingFactionTriggerRva = 0x2B250B0;
constexpr std::uintptr_t kCampaignRootCouncilPositionLookupRva = 0x2684EE0;
constexpr std::uintptr_t kCampaignRootCouncilActiveTaskIdsEnumeratorRva = 0x2916CC0;
constexpr std::uintptr_t kCampaignRootActiveCouncilTaskStorageSlotRva = 0x5D1DEA0;
constexpr std::uintptr_t kCampaignRootCouncilValueProgressCurrentRva = 0x31AB500;
constexpr std::uintptr_t kCampaignRootCouncilValueProgressMaximumRva = 0x31AB820;
constexpr std::uintptr_t kCampaignRootPrimaryTitleRva = 0x289DA10;
constexpr std::uintptr_t kNonwarRealmHeldTitlesOffset = 0x1E0;
constexpr std::uintptr_t kNonwarRealmTitleProvinceRva = 0x230F8E0;
constexpr std::uintptr_t kCampaignRootCapitalProvinceRva = 0x28B1CB0;
constexpr std::uintptr_t kCampaignRootImmediateLiegeRva = 0x28BFC50;
constexpr std::uintptr_t kCampaignRootTopLiegeRva = 0x28BFD80;
constexpr std::uintptr_t kCampaignRootGovernmentRva = 0x28C2DF0;
constexpr std::uintptr_t kNonwarRealmProvinceHolderCharacterIdRva = 0x247D010;
constexpr std::uintptr_t kCampaignRootGameRuleSelectionServiceSlotRva = 0x5CB3D78;
constexpr std::string_view kCampaignRootContextV1ExecutableSha256 = kExecutableSha256;
constexpr std::string_view kCampaignRootContextV1BackendId = "ck3-1.20.0.4-native-campaign-root-context-v1";

template <typename Value>
bool AppendNumber(std::string &output, Value value) {
  std::array<char, 32> buffer{};
  const auto encoded =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (encoded.ec != std::errc{}) {
    return false;
  }
  output.append(buffer.data(), encoded.ptr);
  return true;
}

void AppendJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(character));
    } else if (character < 0x20U) {
      output += "\\u00";
      output.push_back(hex[(character >> 4U) & 0x0FU]);
      output.push_back(hex[character & 0x0FU]);
    } else {
      output.push_back(static_cast<char>(character));
    }
  }
  output.push_back('"');
}

bool ValidToken(std::string_view value) noexcept {
  return !value.empty() && value.size() <= 1'024 &&
         std::none_of(value.begin(), value.end(), [](unsigned char character) {
           return character == 0 || character < 0x20U;
         });
}

bool ReadinessAll(const game::CampaignRootReadinessV1 &value,
                  bool expected) noexcept {
  return value.player_identity_ready == expected &&
         value.player_monthly_gold_income_ready == expected &&
         value.player_health_ready == expected &&
         value.player_domain_ready == expected &&
         value.player_targeting_factions_ready == expected &&
         value.primary_title_ready == expected &&
         value.primary_title_succession_ready == expected &&
         value.held_title_partition_ready == expected &&
         value.capital_ready == expected && value.lieges_ready == expected &&
         value.direct_landed_vassals_ready == expected &&
         value.adjacent_external_province_holders_ready == expected &&
         value.related_character_contexts_ready == expected &&
         value.government_ready == expected &&
         value.selected_game_rule_tokens_ready == expected &&
         value.same_frame_ready == expected && value.ready == expected;
}

bool ValidAvailableReadiness(
    const game::CampaignRootReadinessV1 &value) noexcept {
  return value.player_identity_ready &&
         value.player_monthly_gold_income_ready && value.player_health_ready &&
         value.player_domain_ready && value.player_targeting_factions_ready &&
         value.primary_title_ready && value.primary_title_succession_ready &&
         value.held_title_partition_ready && value.capital_ready &&
         value.lieges_ready && value.direct_landed_vassals_ready &&
         value.adjacent_external_province_holders_ready &&
         value.related_character_contexts_ready && value.government_ready &&
         value.same_frame_ready &&
         value.ready == value.selected_game_rule_tokens_ready;
}

std::string_view CouncilTaskTypeKey(
    game::CampaignRootCouncilTaskTypeV1 value) noexcept {
  switch (value) {
  case game::CampaignRootCouncilTaskTypeV1::general:
    return "general";
  case game::CampaignRootCouncilTaskTypeV1::county:
    return "county";
  case game::CampaignRootCouncilTaskTypeV1::court:
    return "court";
  }
  return {};
}

std::string_view CouncilProgressKindKey(
    game::CampaignRootCouncilProgressKindV1 value) noexcept {
  switch (value) {
  case game::CampaignRootCouncilProgressKindV1::infinite:
    return "infinite";
  case game::CampaignRootCouncilProgressKindV1::percentage:
    return "percentage";
  case game::CampaignRootCouncilProgressKindV1::value:
    return "value";
  }
  return {};
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

bool ValidUnavailableReason(std::string_view reason) noexcept {
  constexpr std::array<std::string_view, 23> reasons = {
      "unsupported_build",
      "requires_application_main",
      "requires_paused",
      "map_not_ready",
      "player_identity_unavailable",
      "player_character_generation_mismatch",
      "player_monthly_gold_income_unavailable",
      "player_health_unavailable",
      "player_domain_unavailable",
      "player_targeting_factions_unavailable",
      "primary_title_unavailable",
      "primary_title_succession_unavailable",
      "held_title_partition_unavailable",
      "capital_unavailable",
      "lieges_unavailable",
      "direct_landed_vassals_unavailable",
      "adjacent_external_province_holders_unavailable",
      "related_character_contexts_unavailable",
      "government_flags_unavailable",
      "council_unavailable",
      "selected_game_rule_tokens_unavailable",
      "state_changed",
      "internal_error",
  };
  return std::find(reasons.begin(), reasons.end(), reason) != reasons.end();
}

bool Utf8BytewiseLess(std::string_view left,
                      std::string_view right) noexcept {
  return std::lexicographical_compare(
      left.begin(), left.end(), right.begin(), right.end(),
      [](char left_byte, char right_byte) noexcept {
        return static_cast<unsigned char>(left_byte) <
               static_cast<unsigned char>(right_byte);
      });
}

bool SortedTokens(const std::vector<std::string> &values) noexcept {
  return std::is_sorted(values.begin(), values.end(), Utf8BytewiseLess) &&
         std::all_of(values.begin(), values.end(), [](const auto &value) {
           return ValidToken(value);
         });
}

bool ValidCharacterIds(const std::vector<std::int32_t> &values,
                       std::int32_t player_character_id) noexcept {
  return std::is_sorted(values.begin(), values.end()) &&
         std::adjacent_find(values.begin(), values.end()) == values.end() &&
         std::all_of(values.begin(), values.end(),
                     [player_character_id](std::int32_t value) {
                       return value > 0 && value != player_character_id;
                     });
}

bool ValidSuccessionIds(const std::vector<std::int32_t> &values,
                        std::int32_t player_character_id) noexcept {
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (values[index] <= 0 || values[index] == player_character_id ||
        std::find(values.begin(), values.begin() + index, values[index]) !=
            values.begin() + index) {
      return false;
    }
  }
  return true;
}

bool ValidHeldTitlePartition(
    const std::vector<game::CampaignRootHeldTitleSuccessionV1> &values,
    const std::optional<game::CampaignRootTitleV1> &primary_title,
    const std::vector<std::int32_t> &primary_title_successors,
    std::int32_t player_character_id) noexcept {
  if (!std::is_sorted(values.begin(), values.end(),
                      [](const auto &left, const auto &right) {
                        return left.title.title_id < right.title.title_id;
                      })) {
    return false;
  }
  std::int32_t previous_title_id = -1;
  std::size_t primary_count = 0;
  for (const auto &value : values) {
    if (value.title.title_id <= 0 ||
        value.title.title_id == previous_title_id ||
        value.title.tier_raw < 2 || value.title.tier_raw > 6 ||
        TierKey(value.title.tier_raw) != value.title.tier_key ||
        !game::HasValidCampaignRootHeldTitleCapitalV1(value) ||
        (value.capital_province_id.has_value() &&
         *value.capital_province_id <= 0) ||
        (value.first_heir_character_id.has_value() &&
         (*value.first_heir_character_id <= 0 ||
          *value.first_heir_character_id == player_character_id)) ||
        (value.primary &&
         (!primary_title.has_value() || value.title != *primary_title ||
          value.first_heir_character_id !=
              (primary_title_successors.empty()
                   ? std::optional<std::int32_t>{}
                   : std::optional<std::int32_t>{
                         primary_title_successors.front()})))) {
      return false;
    }
    primary_count += value.primary ? 1U : 0U;
    previous_title_id = value.title.title_id;
  }
  if (!primary_title.has_value() || primary_title->tier_raw == 1) {
    return values.empty();
  }
  return primary_count == 1;
}

bool ValidCouncilProgress(
    const game::CampaignRootCouncilProgressV1 &progress) noexcept {
  const auto kind = CouncilProgressKindKey(progress.kind);
  if (kind.empty()) {
    return false;
  }
  if (progress.kind ==
      game::CampaignRootCouncilProgressKindV1::infinite) {
    return !progress.current.has_value() && !progress.maximum.has_value();
  }
  return progress.current.has_value() && progress.maximum.has_value() &&
         progress.current->scale == 100'000 &&
         progress.maximum->scale == 100'000 &&
         progress.current->raw >= 0 && progress.maximum->raw > 0 &&
         progress.current->raw <= progress.maximum->raw &&
         (progress.kind !=
              game::CampaignRootCouncilProgressKindV1::percentage ||
          progress.maximum->raw == 10'000'000);
}

bool ValidCouncil(const game::CampaignRootCouncilV1 &council,
                  std::int32_t player_character_id) noexcept {
  constexpr std::array<std::string_view, 5> core_keys{
      "councillor_chancellor", "councillor_steward",
      "councillor_marshal", "councillor_spymaster",
      "councillor_court_chaplain"};
  if (council.coverage_key != "standard_landed_non_nomadic_core_v1" ||
      council.owner_character_id != player_character_id ||
      council.auxiliary_vacancies_complete) {
    return false;
  }
  if (council.status == game::CampaignRootCouncilStatusV1::unavailable) {
    return council.positions.empty() &&
           (council.unavailable_reason ==
                "outside_standard_landed_non_nomadic_core_scope" ||
            council.unavailable_reason ==
                "actual4_council_position_key_source_unavailable");
  }
  if (council.status != game::CampaignRootCouncilStatusV1::available ||
      !council.unavailable_reason.empty() ||
      council.positions.size() < core_keys.size() ||
      !std::is_sorted(council.positions.begin(), council.positions.end(),
                      [](const auto &left, const auto &right) {
                        return Utf8BytewiseLess(left.position_key,
                                                right.position_key);
                      })) {
    return false;
  }
  std::string_view previous;
  for (const auto &position : council.positions) {
    if (!ValidToken(position.position_key) ||
        (!previous.empty() && previous == position.position_key)) {
      return false;
    }
    previous = position.position_key;
    const bool vacant = !position.incumbent_character_id.has_value();
    if (vacant) {
      if (position.task_key.has_value() || position.task_type.has_value() ||
          position.target.has_value() || position.frozen.has_value() ||
          position.progress.has_value()) {
        return false;
      }
      continue;
    }
    if (*position.incumbent_character_id <= 0 ||
        !position.task_key.has_value() ||
        !ValidToken(*position.task_key) ||
        !position.task_type.has_value() ||
        CouncilTaskTypeKey(*position.task_type).empty() ||
        !position.frozen.has_value() || !position.progress.has_value() ||
        !ValidCouncilProgress(*position.progress)) {
      return false;
    }
    if (*position.task_type ==
        game::CampaignRootCouncilTaskTypeV1::general) {
      if (position.target.has_value()) {
        return false;
      }
    } else if (!position.target.has_value() ||
               (*position.task_type ==
                    game::CampaignRootCouncilTaskTypeV1::county &&
                (!position.target->province_id.has_value() ||
                 *position.target->province_id <= 0 ||
                 position.target->character_id.has_value())) ||
               (*position.task_type ==
                    game::CampaignRootCouncilTaskTypeV1::court &&
                (!position.target->character_id.has_value() ||
                 *position.target->character_id <= 0 ||
                 position.target->province_id.has_value()))) {
      return false;
    }
  }
  return std::all_of(core_keys.begin(), core_keys.end(),
                     [&council](std::string_view key) {
                       return std::count_if(
                                  council.positions.begin(),
                                  council.positions.end(),
                                  [key](const auto &position) {
                                    return position.position_key == key;
                                  }) == 1;
                     });
}

bool ValidRelatedCharacters(
    const std::vector<game::CampaignRootRelatedCharacterV1> &values,
    std::int32_t player_character_id,
    std::int32_t player_top_liege_character_id,
    const std::vector<std::int32_t> &direct_vassals,
    const std::vector<std::int32_t> &adjacent_holders) noexcept {
  if (values.size() != direct_vassals.size() + adjacent_holders.size() ||
      !std::is_sorted(values.begin(), values.end(),
                      [](const auto &left, const auto &right) {
                        return left.character_id < right.character_id;
                      })) {
    return false;
  }
  std::int32_t previous_id = -1;
  for (const auto &value : values) {
    if (value.character_id <= 0 || value.character_id == previous_id ||
        value.primary_title.title_id <= 0 ||
        TierKey(value.primary_title.tier_raw) !=
            value.primary_title.tier_key ||
        (value.capital_province_id.has_value() &&
         *value.capital_province_id <= 0) ||
        value.top_liege_character_id <= 0 ||
        value.independent !=
            !value.immediate_liege_character_id.has_value() ||
        (value.immediate_liege_character_id.has_value() &&
         (*value.immediate_liege_character_id <= 0 ||
          *value.immediate_liege_character_id == value.character_id)) ||
        (value.independent &&
         value.top_liege_character_id != value.character_id) ||
        (!value.independent &&
         value.top_liege_character_id == value.character_id)) {
      return false;
    }
    const bool direct = std::binary_search(
        direct_vassals.begin(), direct_vassals.end(), value.character_id);
    const bool adjacent = std::binary_search(
        adjacent_holders.begin(), adjacent_holders.end(), value.character_id);
    if (direct == adjacent ||
        (direct &&
         (value.relationship_role != "direct_landed_vassal" ||
          value.immediate_liege_character_id != player_character_id ||
          value.top_liege_character_id != player_top_liege_character_id)) ||
        (adjacent && value.relationship_role !=
                         "adjacent_external_province_holder")) {
      return false;
    }
    previous_id = value.character_id;
  }
  return true;
}

bool ValidAvailable(const game::CampaignRootContextV1 &context) noexcept {
  if (context.snapshot_revision == 0 ||
      !context.local_player_id.has_value() || *context.local_player_id < 0 ||
      !context.player_character_id.has_value() ||
      *context.player_character_id <= 0 ||
      !context.player_character_alive.has_value() ||
      !context.player_monthly_gold_income.has_value() ||
      context.player_monthly_gold_income->scale != 100'000 ||
      (context.player_max_monthly_gold_maintenance_v1.has_value() &&
       (context.player_max_monthly_gold_maintenance_v1->value.has_value()
            ? (context.player_max_monthly_gold_maintenance_v1->value->scale !=
                   100'000 ||
               context.player_max_monthly_gold_maintenance_v1->value->raw < 0 ||
               !context.player_max_monthly_gold_maintenance_v1->unavailable_reason.empty())
            : (context.player_max_monthly_gold_maintenance_v1->unavailable_reason !=
                   "getter_unavailable" &&
               context.player_max_monthly_gold_maintenance_v1->unavailable_reason !=
                   "getter_failed" &&
               context.player_max_monthly_gold_maintenance_v1->unavailable_reason !=
                   "amount_invalid"))) ||
      !context.player_health.has_value() ||
      context.player_health->scale != 100'000 ||
      !context.player_legitimacy_v1.has_value() ||
      (context.player_legitimacy_v1->value.has_value()
           ? (context.player_legitimacy_v1->value->scale != 100'000 ||
              context.player_legitimacy_v1->value->raw < 0 ||
              !context.player_legitimacy_v1->unavailable_reason.empty())
           : (context.player_legitimacy_v1->unavailable_reason !=
                  "data_pointer_unreadable" &&
              context.player_legitimacy_v1->unavailable_reason !=
                  "data_absent" &&
              context.player_legitimacy_v1->unavailable_reason !=
                  "balance_unreadable" &&
              context.player_legitimacy_v1->unavailable_reason !=
                  "balance_invalid" &&
               context.player_legitimacy_v1->unavailable_reason !=
                   "actual4_legitimacy_field_source_unavailable")) ||
      !context.player_domain_size.has_value() ||
      *context.player_domain_size < 0 ||
      !context.player_domain_limit.has_value() ||
      *context.player_domain_limit < 1 ||
      !context.player_targeting_faction_count.has_value() ||
      *context.player_targeting_faction_count < 0 ||
      !context.council.has_value() ||
      !context.top_liege_character_id.has_value() ||
      *context.top_liege_character_id <= 0 ||
      !context.independent.has_value() ||
      context.native_selected_game_rule_token_count < 0 ||
      static_cast<std::size_t>(
          context.native_selected_game_rule_token_count) !=
          context.selected_game_rule_tokens.size() ||
      !SortedTokens(context.selected_game_rule_tokens) ||
      !ValidSuccessionIds(
          context.primary_title_succession_character_ids,
          *context.player_character_id) ||
      !ValidHeldTitlePartition(context.held_title_partition,
                               context.primary_title,
                               context.primary_title_succession_character_ids,
                               *context.player_character_id) ||
      !ValidCouncil(*context.council, *context.player_character_id) ||
      !ValidCharacterIds(context.direct_landed_vassal_character_ids,
                         *context.player_character_id) ||
      !ValidCharacterIds(
          context.adjacent_external_province_holder_character_ids,
          *context.player_character_id) ||
      std::any_of(
          context.adjacent_external_province_holder_character_ids.begin(),
          context.adjacent_external_province_holder_character_ids.end(),
          [&context](std::int32_t character_id) {
            return std::binary_search(
                context.direct_landed_vassal_character_ids.begin(),
                context.direct_landed_vassal_character_ids.end(),
                character_id);
          }) ||
      !ValidRelatedCharacters(
          context.related_character_contexts, *context.player_character_id,
          *context.top_liege_character_id,
          context.direct_landed_vassal_character_ids,
          context.adjacent_external_province_holder_character_ids) ||
      !ValidAvailableReadiness(context.readiness) ||
      !context.unavailable_reason.empty()) {
    return false;
  }
  if (context.readiness.council_ready !=
      (context.council->status ==
       game::CampaignRootCouncilStatusV1::available)) {
    return false;
  }
  if (!context.readiness.selected_game_rule_tokens_ready &&
      (!context.selected_game_rule_tokens.empty() ||
       context.native_selected_game_rule_token_count != 0)) {
    return false;
  }
  if (context.primary_title.has_value()) {
    const auto &title = *context.primary_title;
    if (title.title_id <= 0 || TierKey(title.tier_raw) != title.tier_key) {
      return false;
    }
  }
  if (!context.primary_title.has_value() &&
      !context.primary_title_succession_character_ids.empty()) {
    return false;
  }
  if (context.capital_province_id.has_value() &&
      *context.capital_province_id <= 0) {
    return false;
  }
  if (context.immediate_liege_character_id.has_value() &&
      (*context.immediate_liege_character_id <= 0 ||
       *context.immediate_liege_character_id ==
           *context.player_character_id)) {
    return false;
  }
  if (*context.independent !=
          !context.immediate_liege_character_id.has_value() ||
      (*context.independent &&
       *context.top_liege_character_id != *context.player_character_id) ||
      (!*context.independent &&
       *context.top_liege_character_id == *context.player_character_id)) {
    return false;
  }
  if (context.government.has_value()) {
    const auto &government = *context.government;
    if (!ValidToken(government.key) || government.native_flag_count < 0 ||
        static_cast<std::size_t>(government.native_flag_count) !=
            government.flags.size() ||
        !SortedTokens(government.flags)) {
      return false;
    }
  }
  return true;
}

bool ValidUnavailable(const game::CampaignRootContextV1 &context) noexcept {
  return context.snapshot_revision > 0 &&
         !context.local_player_id.has_value() &&
         !context.player_character_id.has_value() &&
         !context.player_character_alive.has_value() &&
         !context.player_monthly_gold_income.has_value() &&
         !context.player_max_monthly_gold_maintenance_v1.has_value() &&
         !context.player_health.has_value() &&
         !context.player_legitimacy_v1.has_value() &&
         !context.player_domain_size.has_value() &&
         !context.player_domain_limit.has_value() &&
         !context.player_targeting_faction_count.has_value() &&
         !context.council.has_value() &&
         !context.primary_title.has_value() &&
         context.primary_title_succession_character_ids.empty() &&
         context.held_title_partition.empty() &&
         !context.capital_province_id.has_value() &&
         !context.immediate_liege_character_id.has_value() &&
         !context.top_liege_character_id.has_value() &&
         !context.independent.has_value() && !context.government.has_value() &&
         context.direct_landed_vassal_character_ids.empty() &&
         context.adjacent_external_province_holder_character_ids.empty() &&
         context.related_character_contexts.empty() &&
         context.selected_game_rule_tokens.empty() &&
         context.native_selected_game_rule_token_count == 0 &&
         !context.readiness.council_ready &&
         ReadinessAll(context.readiness, false) &&
         ValidUnavailableReason(context.unavailable_reason);
}

bool AppendStringArray(std::string &output,
                       const std::vector<std::string> &values) {
  output.push_back('[');
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    AppendJsonString(output, values[index]);
  }
  output.push_back(']');
  return true;
}

bool AppendIntegerArray(std::string &output,
                        const std::vector<std::int32_t> &values) {
  output.push_back('[');
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    if (!AppendNumber(output, values[index])) {
      return false;
    }
  }
  output.push_back(']');
  return true;
}

void AppendOptionalInt32(std::string &output,
                         const std::optional<std::int32_t> &value) {
  if (value.has_value()) {
    (void)AppendNumber(output, *value);
  } else {
    output += "null";
  }
}

void AppendOptionalBool(std::string &output,
                        const std::optional<bool> &value) {
  if (!value.has_value()) {
    output += "null";
  } else {
    output += *value ? "true" : "false";
  }
}

bool AppendRelatedCharacters(
    std::string &output,
    const std::vector<game::CampaignRootRelatedCharacterV1> &values) {
  output.push_back('[');
  for (std::size_t index = 0; index < values.size(); ++index) {
    const auto &value = values[index];
    if (index != 0) {
      output.push_back(',');
    }
    output += "{\"character_id\":";
    if (!AppendNumber(output, value.character_id)) {
      return false;
    }
    output += ",\"relationship_role\":";
    AppendJsonString(output, value.relationship_role);
    output += ",\"primary_title\":{\"title_id\":";
    if (!AppendNumber(output, value.primary_title.title_id)) {
      return false;
    }
    output += ",\"tier_raw\":";
    if (!AppendNumber(output, value.primary_title.tier_raw)) {
      return false;
    }
    output += ",\"tier_key\":";
    AppendJsonString(output, value.primary_title.tier_key);
    output += "},\"capital_province_id\":";
    AppendOptionalInt32(output, value.capital_province_id);
    output += ",\"immediate_liege_character_id\":";
    AppendOptionalInt32(output, value.immediate_liege_character_id);
    output += ",\"top_liege_character_id\":";
    if (!AppendNumber(output, value.top_liege_character_id)) {
      return false;
    }
    output += ",\"independent\":";
    output += value.independent ? "true" : "false";
    output.push_back('}');
  }
  output.push_back(']');
  return true;
}

bool AppendFixedPoint(std::string &output,
                      const std::optional<game::FixedPointValue> &value) {
  if (!value.has_value()) {
    output += "null";
    return true;
  }
  output += "{\"raw\":";
  if (!AppendNumber(output, value->raw)) {
    return false;
  }
  output += ",\"scale\":";
  if (!AppendNumber(output, value->scale)) {
    return false;
  }
  output.push_back('}');
  return true;
}

bool AppendCouncil(std::string &output,
                   const game::CampaignRootCouncilV1 &council) {
  output += "{\"status\":\"";
  output += council.status == game::CampaignRootCouncilStatusV1::available
                ? "available"
                : "unavailable";
  output += "\",\"coverage_key\":";
  AppendJsonString(output, council.coverage_key);
  output += ",\"owner_character_id\":";
  if (!AppendNumber(output, council.owner_character_id)) {
    return false;
  }
  output += ",\"positions\":[";
  for (std::size_t index = 0; index < council.positions.size(); ++index) {
    const auto &position = council.positions[index];
    if (index != 0) {
      output.push_back(',');
    }
    output += "{\"position_key\":";
    AppendJsonString(output, position.position_key);
    output += ",\"incumbent_character_id\":";
    AppendOptionalInt32(output, position.incumbent_character_id);
    output += ",\"task_key\":";
    if (position.task_key.has_value()) {
      AppendJsonString(output, *position.task_key);
    } else {
      output += "null";
    }
    output += ",\"task_type\":";
    if (position.task_type.has_value()) {
      AppendJsonString(output, CouncilTaskTypeKey(*position.task_type));
    } else {
      output += "null";
    }
    output += ",\"target\":";
    if (!position.target.has_value()) {
      output += "null";
    } else if (position.target->province_id.has_value()) {
      output += "{\"kind\":\"province\",\"province_id\":";
      if (!AppendNumber(output, *position.target->province_id)) {
        return false;
      }
      output.push_back('}');
    } else {
      output += "{\"kind\":\"character\",\"character_id\":";
      if (!AppendNumber(output, *position.target->character_id)) {
        return false;
      }
      output.push_back('}');
    }
    output += ",\"frozen\":";
    AppendOptionalBool(output, position.frozen);
    output += ",\"progress\":";
    if (!position.progress.has_value()) {
      output += "null";
    } else {
      output += "{\"kind\":";
      AppendJsonString(output,
                       CouncilProgressKindKey(position.progress->kind));
      output += ",\"current\":";
      if (!AppendFixedPoint(output, position.progress->current)) {
        return false;
      }
      output += ",\"maximum\":";
      if (!AppendFixedPoint(output, position.progress->maximum)) {
        return false;
      }
      output.push_back('}');
    }
    output += ",\"task_owner_monthly_piety_v1\":";
    if (!position.task_owner_monthly_piety_v1.has_value()) {
      output += "{\"status\":\"unavailable\",\"value\":null,"
                "\"unavailable_reason\":\"task_owner_monthly_piety_unavailable\"}";
    } else {
      output += "{\"status\":\"available\",\"value\":";
      if (!AppendFixedPoint(output, position.task_owner_monthly_piety_v1)) return false;
      output += ",\"unavailable_reason\":null}";
    }
    output.push_back('}');
  }
  output += "],\"auxiliary_vacancies_complete\":";
  output += council.auxiliary_vacancies_complete ? "true" : "false";
  output += ",\"unavailable_reason\":";
  if (council.unavailable_reason.empty()) {
    output += "null";
  } else {
    AppendJsonString(output, council.unavailable_reason);
  }
  output.push_back('}');
  return true;
}

void AppendReadiness(std::string &output,
                     const game::CampaignRootReadinessV1 &value) {
  output += "{\"player_identity_ready\":";
  output += value.player_identity_ready ? "true" : "false";
  output += ",\"player_monthly_gold_income_ready\":";
  output += value.player_monthly_gold_income_ready ? "true" : "false";
  output += ",\"player_health_ready\":";
  output += value.player_health_ready ? "true" : "false";
  output += ",\"player_domain_ready\":";
  output += value.player_domain_ready ? "true" : "false";
  output += ",\"player_targeting_factions_ready\":";
  output += value.player_targeting_factions_ready ? "true" : "false";
  output += ",\"primary_title_ready\":";
  output += value.primary_title_ready ? "true" : "false";
  output += ",\"primary_title_succession_ready\":";
  output += value.primary_title_succession_ready ? "true" : "false";
  output += ",\"held_title_partition_ready\":";
  output += value.held_title_partition_ready ? "true" : "false";
  output += ",\"council_ready\":";
  output += value.council_ready ? "true" : "false";
  output += ",\"capital_ready\":";
  output += value.capital_ready ? "true" : "false";
  output += ",\"lieges_ready\":";
  output += value.lieges_ready ? "true" : "false";
  output += ",\"direct_landed_vassals_ready\":";
  output += value.direct_landed_vassals_ready ? "true" : "false";
  output += ",\"adjacent_external_province_holders_ready\":";
  output +=
      value.adjacent_external_province_holders_ready ? "true" : "false";
  output += ",\"related_character_contexts_ready\":";
  output += value.related_character_contexts_ready ? "true" : "false";
  output += ",\"government_ready\":";
  output += value.government_ready ? "true" : "false";
  output += ",\"selected_game_rule_tokens_ready\":";
  output += value.selected_game_rule_tokens_ready ? "true" : "false";
  output += ",\"same_frame_ready\":";
  output += value.same_frame_ready ? "true" : "false";
  output += ",\"ready\":";
  output += value.ready ? "true" : "false";
  output.push_back('}');
}

void AppendHexBinding(std::string &output, std::string_view key,
                      std::uintptr_t value) {
  output.push_back(',');
  AppendJsonString(output, key);
  output += ":\"0x";
  std::array<char, 2 * sizeof(value)> buffer{};
  const auto encoded = std::to_chars(buffer.data(), buffer.data() + buffer.size(),
                                     value, 16);
  for (auto cursor = buffer.data(); cursor != encoded.ptr; ++cursor) {
    output.push_back(*cursor >= 'a' && *cursor <= 'f'
                         ? static_cast<char>(*cursor - 'a' + 'A') : *cursor);
  }
  output.push_back('"');
}

void AppendProvenance(std::string &output) {
  output += "{\"game_version\":\"1.20.0.4\",";
  output += "\"executable_sha256\":\"";
  output += kCampaignRootContextV1ExecutableSha256;
  output += "\",\"backend_id\":\"";
  output += kCampaignRootContextV1BackendId;
  output.push_back('"');
  AppendHexBinding(output, "monthly_gold_income_rva", kCampaignRootMonthlyGoldIncomeRva);
  AppendHexBinding(output, "character_health_rva", kCampaignRootHealthRva);
  AppendHexBinding(output, "domain_size_rva", kCampaignRootDomainSizeRva);
  AppendHexBinding(output, "domain_limit_rva", kCampaignRootDomainLimitRva);
  AppendHexBinding(output, "has_targeting_faction_trigger_rva", kCampaignRootHasTargetingFactionTriggerRva);
  AppendHexBinding(output, "council_position_lookup_rva", kCampaignRootCouncilPositionLookupRva);
  AppendHexBinding(output, "council_active_task_ids_enumerator_rva", kCampaignRootCouncilActiveTaskIdsEnumeratorRva);
  AppendHexBinding(output, "council_active_task_storage_slot_rva", kCampaignRootActiveCouncilTaskStorageSlotRva);
  AppendHexBinding(output, "council_value_progress_current_rva", kCampaignRootCouncilValueProgressCurrentRva);
  AppendHexBinding(output, "council_value_progress_maximum_rva", kCampaignRootCouncilValueProgressMaximumRva);
  AppendHexBinding(output, "primary_title_rva", kCampaignRootPrimaryTitleRva);
  AppendHexBinding(output, "held_title_ids_offset", kNonwarRealmHeldTitlesOffset);
  AppendHexBinding(output, "title_province_rva", kNonwarRealmTitleProvinceRva);
  AppendHexBinding(output, "capital_province_rva", kCampaignRootCapitalProvinceRva);
  AppendHexBinding(output, "immediate_liege_rva", kCampaignRootImmediateLiegeRva);
  AppendHexBinding(output, "top_liege_rva", kCampaignRootTopLiegeRva);
  AppendHexBinding(output, "government_rva", kCampaignRootGovernmentRva);
  AppendHexBinding(output, "province_holder_character_id_rva", kNonwarRealmProvinceHolderCharacterIdRva);
  AppendHexBinding(output, "selected_game_rule_service_slot_rva", kCampaignRootGameRuleSelectionServiceSlotRva);
  output.push_back('}');
}

} // namespace

std::string SerializeCampaignRootContextV1(
    const game::CampaignRootContextV1 &context) {
  const bool available =
      context.status == game::CampaignRootContextStatusV1::available;
  if ((available && !ValidAvailable(context)) ||
      (!available && !ValidUnavailable(context))) {
    return {};
  }

  std::string output;
  output.reserve(1'024 + context.selected_game_rule_tokens.size() * 48 +
                 context.related_character_contexts.size() * 256);
  output += "{\"schema_version\":1,\"status\":\"";
  output += available ? "available" : "unavailable";
  output += "\",\"snapshot_revision\":";
  if (!AppendNumber(output, context.snapshot_revision)) {
    return {};
  }
  output += ",\"date_raw\":";
  if (!AppendNumber(output, context.date_raw)) {
    return {};
  }
  output += ",\"local_player_id\":";
  AppendOptionalInt32(output, context.local_player_id);
  output += ",\"player_character_id\":";
  AppendOptionalInt32(output, context.player_character_id);
  output += ",\"player_character_alive\":";
  AppendOptionalBool(output, context.player_character_alive);
  output += ",\"player_monthly_gold_income\":";
  if (!context.player_monthly_gold_income.has_value()) {
    output += "null";
  } else {
    output += "{\"raw\":";
    if (!AppendNumber(output, context.player_monthly_gold_income->raw)) {
      return {};
    }
    output += ",\"scale\":";
    if (!AppendNumber(output, context.player_monthly_gold_income->scale)) {
      return {};
    }
    output.push_back('}');
  }
  output += ",\"player_monthly_piety_v1\":";
  if (!available) {
    output += "null";
  } else if (!context.player_monthly_piety_v1.has_value()) {
    output += "{\"status\":\"unavailable\",\"value\":null,"
              "\"unavailable_reason\":\"monthly_piety_unavailable\"}";
  } else {
    output += "{\"status\":\"available\",\"value\":{\"raw\":";
    if (!AppendNumber(output, context.player_monthly_piety_v1->raw)) {
      return {};
    }
    output += ",\"scale\":";
    if (!AppendNumber(output, context.player_monthly_piety_v1->scale)) {
      return {};
    }
    output += "},\"unavailable_reason\":null}";
  }
  output += ",\"player_health\":";
  if (!context.player_health.has_value()) {
    output += "null";
  } else {
    output += "{\"raw\":";
    if (!AppendNumber(output, context.player_health->raw)) {
      return {};
    }
    output += ",\"scale\":";
    if (!AppendNumber(output, context.player_health->scale)) {
      return {};
    }
    output.push_back('}');
  }
  output += ",\"player_legitimacy_v1\":";
  if (!context.player_legitimacy_v1.has_value()) {
    output += "null";
  } else if (context.player_legitimacy_v1->value.has_value()) {
    output += "{\"status\":\"available\",\"value\":{\"raw\":";
    if (!AppendNumber(output, context.player_legitimacy_v1->value->raw)) {
      return {};
    }
    output += ",\"scale\":100000},\"unavailable_reason\":null}";
  } else {
    output += "{\"status\":\"unavailable\",\"value\":null,"
              "\"unavailable_reason\":";
    AppendJsonString(output,
                     context.player_legitimacy_v1->unavailable_reason);
    output.push_back('}');
  }
  if (!available) {
    output += ",\"player_max_monthly_gold_maintenance_v1\":null";
  } else if (context.player_max_monthly_gold_maintenance_v1.has_value()) {
    output += ",\"player_max_monthly_gold_maintenance_v1\":";
    const auto &maintenance = *context.player_max_monthly_gold_maintenance_v1;
    if (maintenance.value.has_value()) {
      output += "{\"status\":\"available\",\"value\":{\"raw\":";
      if (!AppendNumber(output, maintenance.value->raw)) return {};
      output += ",\"scale\":100000},\"unavailable_reason\":null}";
    } else {
      output += "{\"status\":\"unavailable\",\"value\":null,"
                "\"unavailable_reason\":";
      AppendJsonString(output, maintenance.unavailable_reason);
      output.push_back('}');
    }
  }
  output += ",\"player_domain_size\":";
  AppendOptionalInt32(output, context.player_domain_size);
  output += ",\"player_domain_limit\":";
  AppendOptionalInt32(output, context.player_domain_limit);
  output += ",\"player_targeting_faction_count\":";
  AppendOptionalInt32(output, context.player_targeting_faction_count);
  output += ",\"council\":";
  if (!context.council.has_value()) {
    output += "null";
  } else if (!AppendCouncil(output, *context.council)) {
    return {};
  }
  output += ",\"primary_title\":";
  if (!context.primary_title.has_value()) {
    output += "null";
  } else {
    output += "{\"title_id\":";
    if (!AppendNumber(output, context.primary_title->title_id)) {
      return {};
    }
    output += ",\"tier_raw\":";
    if (!AppendNumber(output, context.primary_title->tier_raw)) {
      return {};
    }
    output += ",\"tier_key\":";
    AppendJsonString(output, context.primary_title->tier_key);
    output.push_back('}');
  }
  output += ",\"primary_title_succession_character_ids\":";
  if (!AppendIntegerArray(
          output, context.primary_title_succession_character_ids)) {
    return {};
  }
  output += ",\"held_title_partition\":[";
  for (std::size_t index = 0; index < context.held_title_partition.size();
       ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    const auto &row = context.held_title_partition[index];
    output += "{\"title\":{\"title_id\":";
    if (!AppendNumber(output, row.title.title_id)) {
      return {};
    }
    output += ",\"tier_raw\":";
    if (!AppendNumber(output, row.title.tier_raw)) {
      return {};
    }
    output += ",\"tier_key\":";
    AppendJsonString(output, row.title.tier_key);
    output += "},\"first_heir_character_id\":";
    AppendOptionalInt32(output, row.first_heir_character_id);
    output += ",\"capital_province_id\":";
    AppendOptionalInt32(output, row.capital_province_id);
    if (row.landless_noble_family_no_province) {
      output += ",\"capital_province_kind\":\"landless_noble_family_no_province\"";
      output += ",\"title_key\":";
      AppendJsonString(output, row.native_title_key);
    }
    output += ",\"primary\":";
    output += row.primary ? "true" : "false";
    output.push_back('}');
  }
  output.push_back(']');
  output += ",\"capital_province_id\":";
  AppendOptionalInt32(output, context.capital_province_id);
  output += ",\"immediate_liege_character_id\":";
  AppendOptionalInt32(output, context.immediate_liege_character_id);
  output += ",\"top_liege_character_id\":";
  AppendOptionalInt32(output, context.top_liege_character_id);
  output += ",\"independent\":";
  AppendOptionalBool(output, context.independent);
  output += ",\"direct_landed_vassal_character_ids\":";
  if (!AppendIntegerArray(output,
                          context.direct_landed_vassal_character_ids)) {
    return {};
  }
  output += ",\"adjacent_external_province_holder_character_ids\":";
  if (!AppendIntegerArray(
          output,
          context.adjacent_external_province_holder_character_ids)) {
    return {};
  }
  output += ",\"related_character_contexts\":";
  if (!AppendRelatedCharacters(output, context.related_character_contexts)) {
    return {};
  }
  output += ",\"government\":";
  if (!context.government.has_value()) {
    output += "null";
  } else {
    output += "{\"key\":";
    AppendJsonString(output, context.government->key);
    output += ",\"flags\":";
    (void)AppendStringArray(output, context.government->flags);
    output += ",\"native_flag_count\":";
    if (!AppendNumber(output, context.government->native_flag_count)) {
      return {};
    }
    output.push_back('}');
  }
  output += ",\"selected_game_rule_tokens\":";
  (void)AppendStringArray(output, context.selected_game_rule_tokens);
  output += ",\"native_selected_game_rule_token_count\":";
  if (!AppendNumber(output,
                    context.native_selected_game_rule_token_count)) {
    return {};
  }
  output += ",\"readiness\":";
  AppendReadiness(output, context.readiness);
  output += ",\"unavailable_reason\":";
  if (available) {
    output += "null";
  } else {
    AppendJsonString(output, context.unavailable_reason);
  }
  output += ",\"provenance\":";
  AppendProvenance(output);
  output.push_back('}');
  return output;
}

} // namespace xar::ck3_12004::campaign_root_wire_detail

namespace xar::ck3_12004 {
std::string SerializeCampaignRootContextV1(
    const game::CampaignRootContextV1& context) {
  return campaign_root_wire_detail::SerializeCampaignRootContextV1(context);
}
} // namespace xar::ck3_12004
