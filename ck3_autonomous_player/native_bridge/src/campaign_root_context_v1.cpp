#include "xar_bridge/campaign_root_context_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <utility>
#include <vector>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kGameStateGameDataOffset = 0xA0;
constexpr std::size_t kJominiPlayersOffset = 0x18;
constexpr std::size_t kPlayersLocalPlayerIdOffset = 0x1F0;
constexpr std::size_t kGameDataPlayerManagerOffset = 0x1D4F0;
constexpr std::size_t kPlayerManagerEntriesOffset = 0x58;
constexpr std::size_t kPlayerManagerCountOffset = 0x64;
constexpr std::size_t kPlayerEntryCharacterIdOffset = 0xB0;
constexpr std::size_t kPlayerEntryPlayerIdOffset = 0xD8;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kCharacterDeathMarkerOffset = 0x1C8;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::size_t kLandedTitleIdentityOffset = 0x10;
constexpr std::size_t kLandedTitleTemplateOffset = 0x160;
constexpr std::size_t kLandedTitleTierOffset = 0x5C;
constexpr std::size_t kProvinceIdentityOffset = 0x10;
constexpr std::size_t kGameDataProvinceArrayOffset = 0x140;
constexpr std::size_t kGameDataProvinceCountOffset = 0x14C;
constexpr std::size_t kGovernmentKeyOffset = 0x18;
constexpr std::size_t kGovernmentFlagsOffset = 0x48;
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
  std::optional<game::CampaignRootTitleV1> primary_title;
  std::optional<std::int32_t> capital_province_id;
  std::optional<std::int32_t> immediate_liege_character_id;
  std::int32_t top_liege_character_id = -1;
  bool independent = false;
  std::optional<game::CampaignRootGovernmentV1> government;
  std::vector<std::string> selected_game_rule_tokens;
  std::int32_t native_selected_game_rule_token_count = 0;

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
  if (!environment.exact_build_admitted ||
      environment.game_state_slot == nullptr ||
      environment.jomini_state_slot == nullptr ||
      environment.character_storage_slot == nullptr ||
      environment.character_fallback_slot == nullptr ||
      environment.landed_title_storage_slot == nullptr ||
      environment.landed_title_fallback_slot == nullptr ||
      environment.government_fallback_slot == nullptr ||
      environment.game_rule_selection_service_slot == nullptr ||
      environment.game_rule_token_fallback_slot == nullptr ||
      environment.primary_title == nullptr ||
      environment.capital_province == nullptr ||
      environment.immediate_liege == nullptr ||
      environment.top_liege == nullptr || environment.government == nullptr ||
      environment.script_identifier_name == nullptr) {
    return false;
  }
  if (environment.offline_fixture_function_overrides) {
    return true;
  }
  if (environment.module_base == 0) {
    return false;
  }
  const auto base = environment.module_base;
  return reinterpret_cast<std::uintptr_t>(environment.game_state_slot) ==
             base + kCampaignRootGameStateSlotRva &&
         reinterpret_cast<std::uintptr_t>(environment.jomini_state_slot) ==
             base + kCampaignRootJominiStateSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.character_storage_slot) ==
             base + kCampaignRootCharacterStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.character_fallback_slot) ==
             base + kCampaignRootCharacterFallbackSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.landed_title_storage_slot) ==
             base + kCampaignRootLandedTitleStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.landed_title_fallback_slot) ==
             base + kCampaignRootLandedTitleFallbackSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.government_fallback_slot) ==
             base + kCampaignRootGovernmentFallbackSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.game_rule_selection_service_slot) ==
             base + kCampaignRootGameRuleSelectionServiceSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.game_rule_token_fallback_slot) ==
             base + kCampaignRootGameRuleTokenFallbackSlotRva &&
         reinterpret_cast<std::uintptr_t>(environment.primary_title) ==
             base + kCampaignRootPrimaryTitleRva &&
         reinterpret_cast<std::uintptr_t>(environment.capital_province) ==
             base + kCampaignRootCapitalProvinceRva &&
         reinterpret_cast<std::uintptr_t>(environment.immediate_liege) ==
             base + kCampaignRootImmediateLiegeRva &&
         reinterpret_cast<std::uintptr_t>(environment.top_liege) ==
             base + kCampaignRootTopLiegeRva &&
         reinterpret_cast<std::uintptr_t>(environment.government) ==
             base + kCampaignRootGovernmentRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.script_identifier_name) ==
             base + kCampaignRootScriptIdentifierNameRva;
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

bool ReadObservation(const CampaignRootNativeEnvironmentV1 &environment,
                     const CampaignRootAccessV1 &access,
                     ObservationV1 &output,
                     std::string_view &failure) noexcept {
  output = {};
  if (!ReadPlayerIdentity(environment, access, output)) {
    failure = "player_identity_unavailable";
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
  if (!ReadSelectedRuleTokens(environment, access, output)) {
    failure = "selected_game_rule_tokens_unavailable";
    return false;
  }
  return true;
}

} // namespace

CampaignRootNativeEnvironmentV1 BindCampaignRootNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  CampaignRootNativeEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = exact_build_admitted;
  if (module_base == 0 || !exact_build_admitted) {
    return output;
  }
  output.game_state_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootGameStateSlotRva);
  output.jomini_state_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootJominiStateSlotRva);
  output.character_storage_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootCharacterStorageSlotRva);
  output.character_fallback_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootCharacterFallbackSlotRva);
  output.landed_title_storage_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootLandedTitleStorageSlotRva);
  output.landed_title_fallback_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootLandedTitleFallbackSlotRva);
  output.government_fallback_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootGovernmentFallbackSlotRva);
  output.game_rule_selection_service_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootGameRuleSelectionServiceSlotRva);
  output.game_rule_token_fallback_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootGameRuleTokenFallbackSlotRva);
  output.primary_title = reinterpret_cast<
      NativeCampaignRootCharacterResolverV1>(
      module_base + kCampaignRootPrimaryTitleRva);
  output.capital_province = reinterpret_cast<
      NativeCampaignRootCharacterResolverV1>(
      module_base + kCampaignRootCapitalProvinceRva);
  output.immediate_liege = reinterpret_cast<
      NativeCampaignRootCharacterResolverV1>(
      module_base + kCampaignRootImmediateLiegeRva);
  output.top_liege = reinterpret_cast<
      NativeCampaignRootCharacterResolverV1>(
      module_base + kCampaignRootTopLiegeRva);
  output.government = reinterpret_cast<
      NativeCampaignRootCharacterResolverV1>(
      module_base + kCampaignRootGovernmentRva);
  output.script_identifier_name = reinterpret_cast<
      NativeCampaignRootScriptIdentifierNameV1>(
      module_base + kCampaignRootScriptIdentifierNameRva);
  return output;
}

game::ReadCampaignRootContextResultV1 ReadCampaignRootContextV1(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access,
    const CampaignRootContextRequestV1 &request,
    game::CampaignRootContextV1 &output) noexcept {
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
    if (!ReadObservation(environment, access, first, failure)) {
      SetUnavailable(output, failure);
      return game::ReadCampaignRootContextResultV1::unavailable;
    }
    if (first.player_character_id != before.played_character_id ||
        first.player_character_alive != before.played_character_alive) {
      SetUnavailable(output, "player_character_generation_mismatch");
      return game::ReadCampaignRootContextResultV1::unavailable;
    }
    failure = "internal_error";
    if (!ReadObservation(environment, access, second, failure)) {
      SetUnavailable(output, failure);
      return game::ReadCampaignRootContextResultV1::unavailable;
    }
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
    output.primary_title = std::move(first.primary_title);
    output.capital_province_id = first.capital_province_id;
    output.immediate_liege_character_id =
        first.immediate_liege_character_id;
    output.top_liege_character_id = first.top_liege_character_id;
    output.independent = first.independent;
    output.government = std::move(first.government);
    output.selected_game_rule_tokens =
        std::move(first.selected_game_rule_tokens);
    output.native_selected_game_rule_token_count =
        first.native_selected_game_rule_token_count;
    output.readiness = {true, true, true, true, true, true, true, true};
    output.unavailable_reason.clear();
    return game::ReadCampaignRootContextResultV1::available;
  } catch (...) {
    SetUnavailable(output, "internal_error");
    return game::ReadCampaignRootContextResultV1::unavailable;
  }
}

} // namespace xar::ck3_11906
