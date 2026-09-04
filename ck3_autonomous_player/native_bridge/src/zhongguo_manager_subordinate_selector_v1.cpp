#include "xar_bridge/zhongguo_manager_subordinate_selector_v1.hpp"

#include <windows.h>

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace xar::ck3_11906 {
namespace {

constexpr std::int32_t kMaximumComponents = 4'194'304;
constexpr std::int32_t kMaximumContracts = 65'536;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kCharacterExtensionOffset = 0x1B8;
constexpr std::size_t kCharacterDeathMarkerOffset = 0x1C8;
constexpr std::size_t kExtensionContractDataOffset = 0x248;
constexpr std::size_t kExtensionContractCountOffset = 0x254;
constexpr std::size_t kContractIdentityOffset = 0x08;
constexpr std::size_t kContractSubjectOffset = 0x20;
constexpr std::size_t kContractLiegeOffset = 0x28;
constexpr std::size_t kTitleIdentityOffset = 0x10;
constexpr std::size_t kTitleTemplateOffset = 0x160;
constexpr std::size_t kTitleTierOffset = 0x5C;
constexpr std::size_t kGovernmentKeyOffset = 0x18;
constexpr std::size_t kMsvcStringSizeOffset = 0x10;
constexpr std::size_t kMsvcStringCapacityOffset = 0x18;
constexpr std::size_t kMsvcStringInlineCapacity = 0x0F;
constexpr std::size_t kMaximumStableKeyBytes = 1'024;

struct DirectSubjectV1 {
  std::int32_t contract_id = -1;
  std::int32_t character_id = -1;
  void *character = nullptr;
};

struct ManagerEligibilityV1 {
  bool eligible = false;
  std::int32_t primary_title_id = -1;
  std::int32_t tier_raw = 0;
  std::string tier_key;
  std::string government_key;
};

bool GuardedDirectRead(const void *address, void *output,
                       std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) return false;
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

bool ReadBytes(const ZhongguoManagerSubordinateSelectorAccessV1 &access,
               const void *address, void *output, std::size_t size) noexcept {
  return access.read_memory != nullptr
             ? access.read_memory(access.context, address, output, size)
             : GuardedDirectRead(address, output, size);
}

template <typename Value>
bool ReadValue(const ZhongguoManagerSubordinateSelectorAccessV1 &access,
               const void *base, std::size_t offset, Value &output) noexcept {
  const auto value = reinterpret_cast<std::uintptr_t>(base);
  if (base == nullptr ||
      offset > std::numeric_limits<std::uintptr_t>::max() - value) {
    return false;
  }
  return ReadBytes(access, reinterpret_cast<const void *>(value + offset),
                   &output, sizeof(output));
}

template <typename Value>
bool ReadSlot(const ZhongguoManagerSubordinateSelectorAccessV1 &access,
              Value *const *slot, Value *&output) noexcept {
  return ReadBytes(access, slot, &output, sizeof(output));
}

void *ResolveComponent(
    const ZhongguoManagerSubordinateSelectorAccessV1 &access,
    void *const *storage_slot, void *const *fallback_slot,
    std::int32_t full_id, std::size_t identity_offset) noexcept {
  if (full_id <= 0) return nullptr;
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
      slots == nullptr || capacity <= 0 || capacity > kMaximumComponents) {
    return nullptr;
  }
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *object = nullptr;
  std::int32_t observed = -1;
  if (!ReadValue(access, slots,
                 static_cast<std::size_t>(index) * kStorageSlotStride +
                     kStorageObjectOffset,
                 object) ||
      object == nullptr || object == fallback ||
      !ReadValue(access, object, identity_offset, observed) ||
      observed != full_id) {
    return nullptr;
  }
  return object;
}

bool InvokeCharacterResolver(NativeZhongguoAiCaseCharacterResolverV1 resolver,
                             void *character, void *&output) noexcept {
  output = nullptr;
  if (resolver == nullptr || character == nullptr) return false;
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

bool InvokeIsHuman(NativeZhongguoAiCaseIsHumanPlayerV1 resolver,
                   std::int32_t character_id, bool &output) noexcept {
  output = false;
  if (resolver == nullptr) return false;
#if defined(_MSC_VER)
  __try {
    output = resolver(character_id);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  output = resolver(character_id);
  return true;
#endif
}

bool ReadNativeString(
    const ZhongguoManagerSubordinateSelectorAccessV1 &access,
    const void *native_string, std::string &output) noexcept {
  std::size_t size = 0;
  std::size_t capacity = 0;
  if (!ReadValue(access, native_string, kMsvcStringSizeOffset, size) ||
      !ReadValue(access, native_string, kMsvcStringCapacityOffset, capacity) ||
      size > capacity || size > kMaximumStableKeyBytes) {
    return false;
  }
  const char *data = static_cast<const char *>(native_string);
  if (capacity > kMsvcStringInlineCapacity &&
      !ReadValue(access, native_string, 0, data)) {
    return false;
  }
  if (size > 0 && data == nullptr) return false;
  try {
    output.assign(size, '\0');
  } catch (...) {
    return false;
  }
  return size == 0 || ReadBytes(access, data, output.data(), size);
}

std::string_view TierKey(std::int32_t raw) noexcept {
  switch (raw) {
  case 3: return "duchy";
  case 4: return "kingdom";
  case 5: return "empire";
  case 6: return "hegemony";
  default: return {};
  }
}

bool EnvironmentIsExact(
    const ZhongguoManagerSubordinateSelectorNativeEnvironmentV1 &environment)
    noexcept {
  const auto &eligible = environment.eligibility;
  const auto &variables = eligible.variables;
  if (!variables.exact_build_admitted) return false;
  if (variables.offline_fixture_function_overrides) {
    return variables.module_base == 0 &&
           environment.subject_contract_storage_slot == nullptr &&
           environment.subject_contract_fallback_slot == nullptr;
  }
  if (variables.module_base == 0 ||
      variables.character_storage_slot == nullptr ||
      variables.character_fallback_slot == nullptr ||
      eligible.landed_title_storage_slot == nullptr ||
      eligible.landed_title_fallback_slot == nullptr ||
      eligible.government_fallback_slot == nullptr ||
      eligible.primary_title == nullptr || eligible.immediate_liege == nullptr ||
      eligible.government == nullptr || eligible.is_human_player == nullptr ||
      environment.subject_contract_storage_slot == nullptr ||
      environment.subject_contract_fallback_slot == nullptr) {
    return false;
  }
  const auto base = variables.module_base;
  return reinterpret_cast<std::uintptr_t>(variables.character_storage_slot) ==
             base + kZhongguoCharacterStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(variables.character_fallback_slot) ==
             base + kZhongguoCharacterFallbackSlotRva &&
         reinterpret_cast<std::uintptr_t>(eligible.landed_title_storage_slot) ==
             base + kZhongguoAiCaseLandedTitleStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(eligible.landed_title_fallback_slot) ==
             base + kZhongguoAiCaseLandedTitleFallbackSlotRva &&
         reinterpret_cast<std::uintptr_t>(eligible.government_fallback_slot) ==
             base + kZhongguoAiCaseGovernmentFallbackSlotRva &&
         reinterpret_cast<std::uintptr_t>(eligible.primary_title) ==
             base + kZhongguoAiCasePrimaryTitleRva &&
         reinterpret_cast<std::uintptr_t>(eligible.immediate_liege) ==
             base + kZhongguoAiCaseImmediateLiegeRva &&
         reinterpret_cast<std::uintptr_t>(eligible.government) ==
             base + kZhongguoAiCaseGovernmentRva &&
         reinterpret_cast<std::uintptr_t>(eligible.is_human_player) ==
             base + kZhongguoAiCaseIsHumanPlayerRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.subject_contract_storage_slot) ==
             base + kZhongguoSubjectContractStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.subject_contract_fallback_slot) ==
             base + kZhongguoSubjectContractFallbackSlotRva;
}

bool ReadDirectSubjects(
    const ZhongguoManagerSubordinateSelectorNativeEnvironmentV1 &environment,
    const ZhongguoManagerSubordinateSelectorAccessV1 &access, void *owner,
    std::vector<DirectSubjectV1> &output) noexcept {
  output.clear();
  void *extension = nullptr;
  if (!ReadValue(access, owner, kCharacterExtensionOffset, extension)) {
    return false;
  }
  if (extension == nullptr) return true;
  void *data = nullptr;
  std::int32_t count = 0;
  if (!ReadValue(access, extension, kExtensionContractDataOffset, data) ||
      !ReadValue(access, extension, kExtensionContractCountOffset, count) ||
      count < 0 || count > kMaximumContracts ||
      (count != 0 && data == nullptr)) {
    return false;
  }
  void *character_fallback = nullptr;
  if (!ReadSlot(access,
                environment.eligibility.variables.character_fallback_slot,
                character_fallback)) {
    return false;
  }
  try {
    output.reserve(static_cast<std::size_t>(count));
  } catch (...) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    std::int32_t contract_id = -1;
    if (!ReadValue(access, data,
                   static_cast<std::size_t>(index) * sizeof(contract_id),
                   contract_id)) {
      return false;
    }
    void *const contract = ResolveComponent(
        access, environment.subject_contract_storage_slot,
        environment.subject_contract_fallback_slot, contract_id,
        kContractIdentityOffset);
    void *subject = nullptr;
    void *liege = nullptr;
    if (contract == nullptr ||
        !ReadValue(access, contract, kContractSubjectOffset, subject) ||
        !ReadValue(access, contract, kContractLiegeOffset, liege) ||
        subject == nullptr || liege != owner) {
      return false;
    }
    std::int32_t subject_id = -1;
    if (!ReadValue(access, subject, kCharacterIdentityOffset, subject_id) ||
        ResolveComponent(
            access, environment.eligibility.variables.character_storage_slot,
            environment.eligibility.variables.character_fallback_slot,
            subject_id, kCharacterIdentityOffset) != subject) {
      return false;
    }
    void *immediate_liege = nullptr;
    if (!InvokeCharacterResolver(environment.eligibility.immediate_liege,
                                 subject, immediate_liege)) {
      return false;
    }
    if (immediate_liege != owner) {
      if (immediate_liege != nullptr &&
          immediate_liege != character_fallback) {
        std::int32_t other_liege_id = -1;
        if (!ReadValue(access, immediate_liege, kCharacterIdentityOffset,
                       other_liege_id) ||
            ResolveComponent(
                access,
                environment.eligibility.variables.character_storage_slot,
                environment.eligibility.variables.character_fallback_slot,
                other_liege_id, kCharacterIdentityOffset) != immediate_liege) {
          return false;
        }
      }
      continue;
    }
    output.push_back({contract_id, subject_id, subject});
  }
  return true;
}

bool ObserveManagerEligibility(
    const ZhongguoManagerSubordinateSelectorNativeEnvironmentV1 &environment,
    const ZhongguoManagerSubordinateSelectorAccessV1 &access,
    const DirectSubjectV1 &candidate, ManagerEligibilityV1 &output) noexcept {
  output = {};
  void *death = nullptr;
  bool human = false;
  if (!ReadValue(access, candidate.character, kCharacterDeathMarkerOffset,
                 death) ||
      !InvokeIsHuman(environment.eligibility.is_human_player,
                     candidate.character_id, human)) {
    return false;
  }
  if (death != nullptr || human) return true;

  void *title = nullptr;
  void *title_fallback = nullptr;
  if (!ReadSlot(access, environment.eligibility.landed_title_fallback_slot,
                title_fallback) ||
      !InvokeCharacterResolver(environment.eligibility.primary_title,
                               candidate.character, title)) {
    return false;
  }
  if (title == nullptr || title == title_fallback ||
      !ReadValue(access, title, kTitleIdentityOffset,
                 output.primary_title_id) ||
      ResolveComponent(access,
                       environment.eligibility.landed_title_storage_slot,
                       environment.eligibility.landed_title_fallback_slot,
                       output.primary_title_id, kTitleIdentityOffset) != title) {
    return title == nullptr || title == title_fallback;
  }
  void *title_template = nullptr;
  if (!ReadValue(access, title, kTitleTemplateOffset, title_template) ||
      title_template == nullptr ||
      !ReadValue(access, title_template, kTitleTierOffset, output.tier_raw)) {
    return false;
  }
  const auto tier_key = TierKey(output.tier_raw);
  if (tier_key.empty()) return true;
  output.tier_key.assign(tier_key);

  void *government = nullptr;
  void *government_fallback = nullptr;
  if (!ReadSlot(access, environment.eligibility.government_fallback_slot,
                government_fallback) ||
      !InvokeCharacterResolver(environment.eligibility.government,
                               candidate.character, government)) {
    return false;
  }
  if (government == nullptr || government == government_fallback) return true;
  const auto address = reinterpret_cast<const void *>(
      reinterpret_cast<std::uintptr_t>(government) + kGovernmentKeyOffset);
  if (!ReadNativeString(access, address, output.government_key)) return false;
  output.eligible = output.government_key == "celestial_government";
  return true;
}

ZhongguoManagerSubordinateObservationResultV1 ObserveSelectionNative(
    const ZhongguoManagerSubordinateSelectorNativeEnvironmentV1 &environment,
    const ZhongguoManagerSubordinateSelectorAccessV1 &access,
    std::int32_t player_id,
    game::ZhongguoManagerSubordinateSelectionV1 &output) noexcept {
  output = {};
  void *const player = ResolveComponent(
      access, environment.eligibility.variables.character_storage_slot,
      environment.eligibility.variables.character_fallback_slot, player_id,
      kCharacterIdentityOffset);
  if (player == nullptr) {
    return ZhongguoManagerSubordinateObservationResultV1::unavailable;
  }
  std::vector<DirectSubjectV1> managers;
  if (!ReadDirectSubjects(environment, access, player, managers)) {
    return ZhongguoManagerSubordinateObservationResultV1::unavailable;
  }
  bool eligible_manager_seen = false;
  for (const auto &manager : managers) {
    ManagerEligibilityV1 eligibility;
    if (!ObserveManagerEligibility(environment, access, manager,
                                   eligibility)) {
      return ZhongguoManagerSubordinateObservationResultV1::unavailable;
    }
    if (!eligibility.eligible) continue;
    eligible_manager_seen = true;
    std::vector<DirectSubjectV1> subordinates;
    if (!ReadDirectSubjects(environment, access, manager.character,
                            subordinates)) {
      return ZhongguoManagerSubordinateObservationResultV1::unavailable;
    }
    if (subordinates.empty()) continue;
    output.manager_character_id = manager.character_id;
    output.subordinate_character_id = subordinates.front().character_id;
    output.manager_contract_id = manager.contract_id;
    output.subordinate_contract_id = subordinates.front().contract_id;
    output.manager_primary_title_id = eligibility.primary_title_id;
    output.manager_primary_title_tier_raw = eligibility.tier_raw;
    output.manager_primary_title_tier_key = std::move(eligibility.tier_key);
    output.manager_government_key = std::move(eligibility.government_key);
    return ZhongguoManagerSubordinateObservationResultV1::available;
  }
  return eligible_manager_seen
             ? ZhongguoManagerSubordinateObservationResultV1::
                   bounded_ai_manager_has_no_direct_subordinate
             : ZhongguoManagerSubordinateObservationResultV1::
                   no_bounded_ai_direct_manager;
}

ZhongguoManagerSubordinateObservationResultV1 ObserveSelection(
    const ZhongguoManagerSubordinateSelectorNativeEnvironmentV1 &environment,
    const ZhongguoManagerSubordinateSelectorAccessV1 &access,
    std::int32_t player_id,
    game::ZhongguoManagerSubordinateSelectionV1 &output) noexcept {
  if (environment.eligibility.variables.offline_fixture_function_overrides) {
    return access.observe_selection == nullptr
               ? ZhongguoManagerSubordinateObservationResultV1::unavailable
               : access.observe_selection(access.context, player_id, output);
  }
  return ObserveSelectionNative(environment, access, player_id, output);
}

bool ValidNonce(std::string_view value) noexcept {
  if (value.empty() || value.size() > 64) return false;
  for (std::size_t index = 0; index < value.size(); ++index) {
    const char character = value[index];
    const bool alpha = (character >= 'a' && character <= 'z') ||
                       (character >= 'A' && character <= 'Z');
    const bool digit = character >= '0' && character <= '9';
    const bool punctuation = character == '.' || character == '_' ||
                             character == ':' || character == '-';
    if ((!alpha && !digit && !punctuation) ||
        (index == 0 && !alpha && !digit)) {
      return false;
    }
  }
  return true;
}

game::ReadZhongguoManagerSubordinateSelectorResultV1 SetUnavailable(
    game::ZhongguoManagerSubordinateSelectorSnapshotV1 &output,
    std::string_view reason) {
  output.status =
      game::ZhongguoManagerSubordinateSelectorStatusV1::unavailable;
  output.selection = {};
  output.readiness.ready = false;
  output.unavailable_reason.assign(reason);
  return game::ReadZhongguoManagerSubordinateSelectorResultV1::unavailable;
}

} // namespace

ZhongguoManagerSubordinateSelectorNativeEnvironmentV1
BindZhongguoManagerSubordinateSelectorNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  ZhongguoManagerSubordinateSelectorNativeEnvironmentV1 output{};
  output.eligibility = BindZhongguoAiOwnedCaseNativeEnvironmentV1(
      module_base, exact_build_admitted);
  if (module_base == 0 || !exact_build_admitted) return output;
  output.subject_contract_storage_slot = reinterpret_cast<void **>(
      module_base + kZhongguoSubjectContractStorageSlotRva);
  output.subject_contract_fallback_slot = reinterpret_cast<void **>(
      module_base + kZhongguoSubjectContractFallbackSlotRva);
  return output;
}

game::ReadZhongguoManagerSubordinateSelectorResultV1
ReadZhongguoManagerSubordinateSelectorV1(
    const ZhongguoManagerSubordinateSelectorNativeEnvironmentV1 &environment,
    const ZhongguoManagerSubordinateSelectorAccessV1 &access,
    const ZhongguoManagerSubordinateSelectorRequestV1 &request,
    game::ZhongguoManagerSubordinateSelectorSnapshotV1 &output) noexcept {
  output = {};
  output.selector_kind.assign(kZhongguoManagerSubordinateSelectorV1Kind);
  output.request_nonce = request.request_nonce;
  output.snapshot_revision = request.expected_snapshot_revision;
  if (request.expected_snapshot_revision == 0 ||
      !ValidNonce(request.request_nonce)) {
    return SetUnavailable(output, "internal_error");
  }
  if (!EnvironmentIsExact(environment)) {
    return SetUnavailable(output, "unsupported_build");
  }
  output.readiness.exact_build_ready = true;
  if (access.is_main_thread == nullptr ||
      !access.is_main_thread(access.context)) {
    return SetUnavailable(output, "requires_application_main");
  }
  if (access.capture_frame == nullptr) {
    return SetUnavailable(output, "internal_error");
  }
  try {
    game::ZhongguoCaseFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      return SetUnavailable(output, "state_changed");
    }
    output.snapshot_revision = before.snapshot_revision;
    output.date_raw = before.date_raw;
    output.paused = before.paused;
    output.player_character_id = before.played_character_id;
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      return SetUnavailable(output, "state_changed");
    }
    if (!before.paused) return SetUnavailable(output, "requires_paused");
    if (!before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0) {
      return SetUnavailable(output, "map_not_ready");
    }
    output.readiness.player_binding_ready = true;

    game::ZhongguoManagerSubordinateSelectionV1 first{};
    game::ZhongguoManagerSubordinateSelectionV1 second{};
    const auto first_result = ObserveSelection(
        environment, access, before.played_character_id, first);
    const auto second_result = ObserveSelection(
        environment, access, before.played_character_id, second);
    game::ZhongguoCaseFrameV1 after{};
    if (!access.capture_frame(access.context, after) || before != after ||
        first_result != second_result || first != second) {
      return SetUnavailable(output, "state_changed");
    }
    output.readiness.same_frame_ready = true;
    if (first_result ==
        ZhongguoManagerSubordinateObservationResultV1::unavailable) {
      return SetUnavailable(output,
                            "native_relationship_enumeration_unavailable");
    }
    output.readiness.relationship_enumeration_ready = true;
    if (first_result == ZhongguoManagerSubordinateObservationResultV1::
                            no_bounded_ai_direct_manager) {
      return SetUnavailable(output, "no_bounded_ai_direct_manager");
    }
    output.readiness.manager_eligibility_ready = true;
    if (first_result == ZhongguoManagerSubordinateObservationResultV1::
                            bounded_ai_manager_has_no_direct_subordinate) {
      return SetUnavailable(
          output, "bounded_ai_manager_has_no_direct_subordinate");
    }
    if (first.manager_character_id <= 0 ||
        first.subordinate_character_id <= 0 ||
        first.manager_character_id == first.subordinate_character_id ||
        first.manager_contract_id <= 0 || first.subordinate_contract_id <= 0 ||
        first.manager_primary_title_id <= 0 ||
        first.manager_primary_title_tier_raw < 3 ||
        first.manager_primary_title_tier_raw > 6 ||
        TierKey(first.manager_primary_title_tier_raw) !=
            first.manager_primary_title_tier_key ||
        first.manager_government_key != "celestial_government") {
      return SetUnavailable(output,
                            "native_relationship_enumeration_unavailable");
    }
    output.selection = std::move(first);
    output.status = game::ZhongguoManagerSubordinateSelectorStatusV1::available;
    output.readiness.direct_subordinate_ready = true;
    output.readiness.ready = true;
    output.unavailable_reason.clear();
    return game::ReadZhongguoManagerSubordinateSelectorResultV1::available;
  } catch (...) {
    return SetUnavailable(output, "internal_error");
  }
}

ZhongguoBoundedAiManagerAuthorizationV1
AuthorizeZhongguoBoundedAiDirectManagerV1(
    const ZhongguoManagerSubordinateSelectorNativeEnvironmentV1 &environment,
    const ZhongguoManagerSubordinateSelectorAccessV1 &access,
    std::int32_t player_character_id, std::int32_t manager_character_id,
    std::int32_t owner_character_id) noexcept {
  if (player_character_id <= 0 || manager_character_id <= 0 ||
      owner_character_id != player_character_id ||
      manager_character_id == player_character_id ||
      !EnvironmentIsExact(environment)) {
    return ZhongguoBoundedAiManagerAuthorizationV1::dependency_unavailable;
  }
  if (environment.eligibility.variables.offline_fixture_function_overrides) {
    return access.authorize_manager_fixture == nullptr
               ? ZhongguoBoundedAiManagerAuthorizationV1::
                     dependency_unavailable
               : access.authorize_manager_fixture(
                     access.context, player_character_id,
                     manager_character_id, owner_character_id);
  }
  try {
    void *const player = ResolveComponent(
        access, environment.eligibility.variables.character_storage_slot,
        environment.eligibility.variables.character_fallback_slot,
        player_character_id, kCharacterIdentityOffset);
    if (player == nullptr) {
      return ZhongguoBoundedAiManagerAuthorizationV1::dependency_unavailable;
    }
    std::vector<DirectSubjectV1> managers;
    if (!ReadDirectSubjects(environment, access, player, managers)) {
      return ZhongguoBoundedAiManagerAuthorizationV1::dependency_unavailable;
    }
    for (const auto &candidate : managers) {
      if (candidate.character_id != manager_character_id) continue;
      ManagerEligibilityV1 eligibility;
      if (!ObserveManagerEligibility(environment, access, candidate,
                                     eligibility)) {
        return ZhongguoBoundedAiManagerAuthorizationV1::dependency_unavailable;
      }
      return eligibility.eligible
                 ? ZhongguoBoundedAiManagerAuthorizationV1::
                       authorized_direct_manager
                 : ZhongguoBoundedAiManagerAuthorizationV1::rejected;
    }
    return ZhongguoBoundedAiManagerAuthorizationV1::rejected;
  } catch (...) {
    return ZhongguoBoundedAiManagerAuthorizationV1::dependency_unavailable;
  }
}

} // namespace xar::ck3_11906
