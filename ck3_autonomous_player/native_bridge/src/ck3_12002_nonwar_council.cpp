#include "xar_bridge/ck3_12002_nonwar_council.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <utility>

namespace xar::ck3_12002 {
namespace {

constexpr std::size_t kTaskIdentity = 0x10;
constexpr std::size_t kTaskType = 0x18;
constexpr std::size_t kTaskProgress = 0x20;
constexpr std::size_t kTaskFrozen = 0x39;
constexpr std::size_t kTaskScopes = 0x40;
constexpr std::size_t kTaskPositionType = 0x40;
constexpr std::size_t kTaskKind = 0x48;
constexpr std::size_t kTaskProgressKind = 0x54;
constexpr std::int64_t kScale = 100'000;
constexpr std::int64_t kPercentageMaximum = 10'000'000;
constexpr std::array<std::string_view, 5> kCoreKeys{
    "councillor_chancellor", "councillor_steward", "councillor_marshal",
    "councillor_spymaster", "councillor_court_chaplain"};

bool ReadBytes(const CampaignRootAccessV1 &access, const void *address,
               void *output, std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) return false;
  if (access.read_memory != nullptr)
    return access.read_memory(access.context, address, output, size);
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

bool Address(const void *base, std::size_t offset,
             const void *&output) noexcept {
  const auto value = reinterpret_cast<std::uintptr_t>(base);
  if (base == nullptr || offset > (std::numeric_limits<std::uintptr_t>::max)() - value)
    return false;
  output = reinterpret_cast<const void *>(value + offset);
  return true;
}

template <typename T>
bool Read(const CampaignRootAccessV1 &access, const void *base,
          std::size_t offset, T &output) noexcept {
  const void *address = nullptr;
  return Address(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

bool ReadKey(const CampaignRootAccessV1 &access, const void *object,
             std::string &output) noexcept {
  const void *key = nullptr;
  if (!Address(object, 0x18, key)) return false;
  if (access.read_string != nullptr)
    return access.read_string(access.context, key, output) &&
           !output.empty() && output.size() <= 1'024;
  std::size_t size = 0, capacity = 0;
  if (!Read(access, key, 0x10, size) || !Read(access, key, 0x18, capacity) ||
      size == 0 || size > capacity || size > 1'024) return false;
  const void *bytes = key;
  if (capacity > 0x0F && (!Read(access, key, 0, bytes) || bytes == nullptr))
    return false;
  try { output.resize(size); } catch (...) { return false; }
  return ReadBytes(access, bytes, output.data(), size) &&
         std::none_of(output.begin(), output.end(), [](unsigned char c) {
           return c == 0 || c < 0x20U;
         });
}

void *Resolve(const CampaignRootAccessV1 &access, void **storage_slot,
              void **fallback_slot, std::int32_t id,
              std::size_t identity_offset) noexcept {
  if (id <= 0) return nullptr;
  void *storage = nullptr, *fallback = nullptr, *slots = nullptr, *object = nullptr;
  std::int32_t capacity = 0, observed = -1;
  if (!Read(access, storage_slot, 0, storage) ||
      !Read(access, fallback_slot, 0, fallback) || storage == nullptr ||
      !Read(access, storage, 0x20, slots) || slots == nullptr ||
      !Read(access, storage, 0x2C, capacity) || capacity <= 0 ||
      capacity > 4'194'304) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity) ||
      !Read(access, slots, static_cast<std::size_t>(index) * 0x10 + 0x08, object) ||
      object == nullptr || object == fallback ||
      !Read(access, object, identity_offset, observed) || observed != id)
    return nullptr;
  return object;
}

bool EnvironmentExact(const CampaignRootNativeEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted ||
      environment.character_storage_slot == nullptr ||
      environment.character_fallback_slot == nullptr ||
      environment.active_council_task_storage_slot == nullptr ||
      environment.active_council_task_fallback_slot == nullptr ||
      environment.council_value_progress_current == nullptr ||
      environment.council_value_progress_maximum == nullptr) return false;
  if (environment.offline_fixture_function_overrides) return true;
  const auto base = environment.module_base;
  return base != 0 &&
      reinterpret_cast<std::uintptr_t>(environment.active_council_task_storage_slot) ==
          base + kCampaignRootActiveCouncilTaskStorageSlotRva &&
      reinterpret_cast<std::uintptr_t>(environment.active_council_task_fallback_slot) ==
          base + kCampaignRootActiveCouncilTaskFallbackSlotRva &&
      reinterpret_cast<std::uintptr_t>(environment.council_value_progress_current) ==
          base + kCampaignRootCouncilValueProgressCurrentRva &&
      reinterpret_cast<std::uintptr_t>(environment.council_value_progress_maximum) ==
          base + kCampaignRootCouncilValueProgressMaximumRva;
}

bool ValueProgress(ck3_11906::NativeCampaignRootCouncilValueProgressV1 function,
                   void *type, void *scopes, std::int64_t &output) noexcept {
  std::int64_t *returned = nullptr;
#if defined(_MSC_VER)
  __try { returned = function(type, &output, scopes); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  returned = function(type, &output, scopes);
#endif
  return returned == &output;
}

// TaskType's own builder constructs the ScriptContext from the original scopes.
constexpr std::uintptr_t kTaskOwnerModifierBuilderRva = 0x31ABE10;
constexpr std::uintptr_t kEvaluatedModifierValueRva = 0x2303700;
constexpr std::uintptr_t kEvaluatedModifierDestructorRva = 0x9F24F0;
constexpr std::uint16_t kMonthlyPietyModifierId = 0x61;

bool TaskOwnerMonthlyPiety(std::uintptr_t module_base, void *type,
                          const void *scopes, std::int64_t &output) noexcept {
  if (module_base == 0) return false;
  using Builder = void *(__fastcall *)(const void *, void *, const void *);
  using Value = std::int64_t *(__fastcall *)(const void *, std::int64_t *,
                                           std::uint16_t);
  using Destroy = void(__fastcall *)(void *);
  const auto builder = reinterpret_cast<Builder>(module_base + kTaskOwnerModifierBuilderRva);
  const auto value = reinterpret_cast<Value>(module_base + kEvaluatedModifierValueRva);
  const auto destroy = reinterpret_cast<Destroy>(module_base + kEvaluatedModifierDestructorRva);
  alignas(8) std::byte modifier[0x1C0]{};
  bool read = false;
#if defined(_MSC_VER)
  __try {
#endif
    if (builder(type, modifier, scopes) != modifier) return false;
    read = value(modifier, &output, kMonthlyPietyModifierId) == &output;
    destroy(modifier);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
  return read;
}

bool ProvinceValid(const CampaignRootNativeEnvironmentV1 &environment,
                   const CampaignRootAccessV1 &access, std::int32_t id) noexcept {
  void *state = nullptr, *data = nullptr, *array = nullptr, *province = nullptr;
  std::int32_t count = 0, observed = -1;
  std::uint32_t tag = 0;
  return id > 0 && Read(access, environment.game_state_slot, 0, state) &&
         Read(access, state, 0xA0, data) &&
         Read(access, data, 0x140, array) && array != nullptr &&
         Read(access, data, 0x14C, count) && count > 0 && count <= 65'536 &&
         id < count && Read(access, array, static_cast<std::size_t>(id) * 8, province) &&
         province != nullptr && Read(access, province, 0x10, observed) && observed == id &&
         Read(access, province, 0x85C, tag) && tag == 0x50726F76U;
}

bool Position(const CampaignRootNativeEnvironmentV1 &environment,
              const CampaignRootAccessV1 &access, void *character,
              std::int32_t character_id, void *task,
              game::CampaignRootCouncilPositionV1 &output) noexcept {
  void *type = nullptr, *position_type = nullptr;
  std::int32_t incumbent = -1, owner = -1, kind = -1, progress_kind = -1;
  std::uint8_t frozen = 0;
  if (!Read(access, task, kTaskType, type) || type == nullptr ||
      !Read(access, type, kTaskPositionType, position_type) || position_type == nullptr ||
      !ReadKey(access, position_type, output.position_key) ||
      !Read(access, task, kTaskScopes, incumbent) ||
      !Read(access, task, kTaskScopes + 4, owner) || incumbent < -1 ||
      owner != character_id ||
      Resolve(access, environment.character_storage_slot,
              environment.character_fallback_slot, owner, 0x18) != character)
    return false;
  if (incumbent <= 0) return true;
  if (!ReadKey(access, type, output.task_key.emplace()) ||
      Resolve(access, environment.character_storage_slot,
              environment.character_fallback_slot, incumbent, 0x18) == nullptr ||
      !Read(access, type, kTaskKind, kind) || kind < 0 || kind > 2 ||
      !Read(access, type, kTaskProgressKind, progress_kind) || progress_kind < 0 ||
      progress_kind > 2 || !Read(access, task, kTaskFrozen, frozen) || frozen > 1)
    return false;
  output.incumbent_character_id = incumbent;
  output.task_type = static_cast<game::CampaignRootCouncilTaskTypeV1>(kind);
  output.frozen = frozen != 0;
  if (kind != 0) {
    std::uint16_t tag = 0;
    std::int32_t target = -1;
    if (!Read(access, task, kTaskScopes + 8, tag) ||
        !Read(access, task, kTaskScopes + 0x10, target)) return false;
    if (kind == 1) {
      if (tag != 8 || !ProvinceValid(environment, access, target)) return false;
      output.target = game::CampaignRootCouncilTargetV1{target, std::nullopt};
    } else {
      if (tag != 4 || Resolve(access, environment.character_storage_slot,
          environment.character_fallback_slot, target, 0x18) == nullptr) return false;
      output.target = game::CampaignRootCouncilTargetV1{std::nullopt, target};
    }
  }
  game::CampaignRootCouncilProgressV1 progress{};
  progress.kind = static_cast<game::CampaignRootCouncilProgressKindV1>(progress_kind);
  if (progress_kind != 0) {
    std::int64_t current = 0, maximum = kPercentageMaximum;
    if (progress_kind == 1) {
      if (!Read(access, task, kTaskProgress, current)) return false;
    } else {
      const void *scopes = nullptr;
      if (!Address(task, kTaskScopes, scopes) ||
          !ValueProgress(environment.council_value_progress_current, type,
              const_cast<void *>(scopes), current) ||
          !ValueProgress(environment.council_value_progress_maximum, type,
              const_cast<void *>(scopes), maximum)) return false;
    }
    if (current < 0 || maximum <= 0 || current > maximum) return false;
    progress.current = game::FixedPointValue{current, kScale};
    progress.maximum = game::FixedPointValue{maximum, kScale};
  }
  output.progress = progress;
  const void *scopes = nullptr;
  std::int64_t piety_raw = 0;
  if (environment.task_owner_monthly_piety != nullptr &&
      Address(task, kTaskScopes, scopes) &&
      environment.task_owner_monthly_piety(environment.module_base, type,
                                            scopes, piety_raw)) {
    output.task_owner_monthly_piety_v1 = game::FixedPointValue{piety_raw, kScale};
  }
  return true;
}

bool KeyLess(std::string_view left, std::string_view right) noexcept {
  return std::lexicographical_compare(left.begin(), left.end(), right.begin(), right.end(),
      [](char a, char b) { return static_cast<unsigned char>(a) < static_cast<unsigned char>(b); });
}

} // namespace

void BindNonwarCouncil12002(CampaignRootNativeEnvironmentV1 &environment,
                           std::uintptr_t module_base) noexcept {
  environment.task_owner_monthly_piety = &TaskOwnerMonthlyPiety;
  environment.active_council_task_storage_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootActiveCouncilTaskStorageSlotRva);
  environment.active_council_task_fallback_slot = reinterpret_cast<void **>(
      module_base + kCampaignRootActiveCouncilTaskFallbackSlotRva);
  environment.council_value_progress_current = reinterpret_cast<
      ck3_11906::NativeCampaignRootCouncilValueProgressV1>(
          module_base + kCampaignRootCouncilValueProgressCurrentRva);
  environment.council_value_progress_maximum = reinterpret_cast<
      ck3_11906::NativeCampaignRootCouncilValueProgressV1>(
          module_base + kCampaignRootCouncilValueProgressMaximumRva);
}

bool ReadNonwarCouncilProjection12002(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access, void *character,
    std::int32_t character_id, bool standard_scope_admitted,
    game::CampaignRootCouncilV1 &output, std::string_view &failure) noexcept {
  output = {};
  output.coverage_key = "standard_landed_non_nomadic_core_v1";
  output.owner_character_id = character_id;
  failure = "council_unavailable";
  if (!standard_scope_admitted) {
    output.unavailable_reason = "outside_standard_landed_non_nomadic_core_scope";
    return true;
  }
  if (!EnvironmentExact(environment) || character == nullptr ||
      Resolve(access, environment.character_storage_slot,
              environment.character_fallback_slot, character_id, 0x18) != character)
    return false;
  void *extension = nullptr, *ids = nullptr;
  std::int32_t count = 0;
  if (!Read(access, character, kNonwarCouncilCharacterExtensionOffset12002, extension) ||
      extension == nullptr || !Read(access, extension, kNonwarCouncilTaskIdsOffset12002, ids) ||
      !Read(access, extension, kNonwarCouncilTaskCountOffset12002, count) ||
      count < 0 || count > 4'096 || (count > 0 && ids == nullptr)) return false;
  try {
    output.positions.reserve(static_cast<std::size_t>(count) + kCoreKeys.size());
    for (std::int32_t index = 0; index < count; ++index) {
      std::int32_t id = -1;
      if (!Read(access, ids, static_cast<std::size_t>(index) * 4, id)) return false;
      void *task = Resolve(access, environment.active_council_task_storage_slot,
          environment.active_council_task_fallback_slot, id, kTaskIdentity);
      game::CampaignRootCouncilPositionV1 position{};
      if (task == nullptr || !Position(environment, access, character, character_id, task, position) ||
          std::any_of(output.positions.begin(), output.positions.end(), [&](const auto &row) {
            return row.position_key == position.position_key;
          })) return false;
      output.positions.push_back(std::move(position));
    }
    for (const auto key : kCoreKeys)
      if (std::none_of(output.positions.begin(), output.positions.end(), [&](const auto &row) {
            return row.position_key == key;
          })) {
        game::CampaignRootCouncilPositionV1 row{};
        row.position_key.assign(key);
        output.positions.push_back(std::move(row));
      }
    std::sort(output.positions.begin(), output.positions.end(), [](const auto &a, const auto &b) {
      return KeyLess(a.position_key, b.position_key);
    });
  } catch (...) { return false; }
  if (Resolve(access, environment.character_storage_slot,
      environment.character_fallback_slot, character_id, 0x18) != character) return false;
  output.status = game::CampaignRootCouncilStatusV1::available;
  output.unavailable_reason.clear();
  failure = {};
  return true;
}

} // namespace xar::ck3_12002
