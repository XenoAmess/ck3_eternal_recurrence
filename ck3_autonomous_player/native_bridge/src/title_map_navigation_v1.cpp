#include "xar_bridge/title_map_navigation_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kMaximumStableKeyBytes = 1'024;
constexpr std::size_t kMsvcStringInlineCapacity = 15;
constexpr std::size_t kGameStateGameDataOffset = 0xA0;
constexpr std::size_t kComponentStorageSlotsOffset = 0x20;
constexpr std::size_t kComponentStorageCapacityOffset = 0x2C;
constexpr std::size_t kComponentStorageSlotStride = 0x10;
constexpr std::size_t kComponentStorageSlotObjectOffset = 0x08;
constexpr std::size_t kLandedTitleIdentityOffset = 0x10;
constexpr std::size_t kLandedTitleTemplateOffset = 0x160;
constexpr std::size_t kLandedTitleTemplateKeyOffset = 0x18;
constexpr std::size_t kLandedTitleTemplateTierOffset = 0x5C;
constexpr std::size_t kProvinceIdentityOffset = 0x10;
constexpr std::size_t kGameDataProvinceArrayOffset = 0x140;
constexpr std::size_t kGameDataProvinceCountOffset = 0x14C;
constexpr std::int32_t kMaximumComponentSlots = 4'194'304;
constexpr std::int32_t kMaximumProvinceCount = 1'048'576;

struct NativeMsvcStringV1 {
  union Storage {
    std::array<char, 16> inline_bytes;
    const char *heap_bytes;

    constexpr Storage() : inline_bytes{} {}
  } storage;
  std::uint64_t size = 0;
  std::uint64_t capacity = kMsvcStringInlineCapacity;
};

static_assert(sizeof(NativeMsvcStringV1) == 32);
static_assert(offsetof(NativeMsvcStringV1, size) == 0x10);
static_assert(offsetof(NativeMsvcStringV1, capacity) == 0x18);

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

bool ReadBytes(const TitleMapNavigationAccessV1 &access,
               const void *address, void *output,
               std::size_t size) noexcept {
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
bool ReadValue(const TitleMapNavigationAccessV1 &access,
               const void *base, std::size_t offset,
               Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

template <typename Value>
bool ReadSlot(const TitleMapNavigationAccessV1 &access,
              const Value *slot, Value &output) noexcept {
  return ReadBytes(access, slot, &output, sizeof(output));
}

bool ReadNativeString(const TitleMapNavigationAccessV1 &access,
                      const void *native_string,
                      std::string &output) noexcept {
  output.clear();
  if (native_string == nullptr) {
    return false;
  }
  if (access.read_string != nullptr) {
    return access.read_string(access.context, native_string, output) &&
           IsCanonicalLandedTitleKeyV1(output);
  }

  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  if (!ReadValue(access, native_string, 0x10, size) ||
      !ReadValue(access, native_string, 0x18, capacity) || size == 0 ||
      size > capacity || size > kMaximumStableKeyBytes) {
    return false;
  }
  const void *bytes = native_string;
  if (capacity > kMsvcStringInlineCapacity &&
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
      !IsCanonicalLandedTitleKeyV1(output)) {
    output.clear();
    return false;
  }
  return true;
}

bool EnvironmentIsExact(
    const TitleMapNavigationNativeEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted ||
      environment.game_state_slot == nullptr ||
      environment.landed_title_storage_slot == nullptr ||
      environment.landed_title_fallback_slot == nullptr ||
      environment.resolve_landed_title_by_key == nullptr ||
      environment.resolve_title_province == nullptr) {
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
             base + kTitleMapGameStateSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.landed_title_storage_slot) ==
             base + kTitleMapLandedTitleStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.landed_title_fallback_slot) ==
             base + kTitleMapLandedTitleFallbackSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.resolve_landed_title_by_key) ==
             base + kTitleMapResolveLandedTitleByKeyRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.resolve_title_province) ==
             base + kTitleMapResolveTitleProvinceRva;
}

void *ResolveComponent(const TitleMapNavigationAccessV1 &access,
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
  if (!ReadValue(access, storage, kComponentStorageSlotsOffset, slots) ||
      !ReadValue(access, storage, kComponentStorageCapacityOffset, capacity) ||
      slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentSlots) {
    return nullptr;
  }
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *candidate = nullptr;
  const auto slot_offset = static_cast<std::size_t>(index) *
                               kComponentStorageSlotStride +
                           kComponentStorageSlotObjectOffset;
  std::int32_t observed_id = -1;
  if (!ReadValue(access, slots, slot_offset, candidate) ||
      candidate == nullptr || candidate == fallback ||
      !ReadValue(access, candidate, identity_offset, observed_id) ||
      observed_id != full_id) {
    return nullptr;
  }
  return candidate;
}

bool MakeNativeMsvcString(std::string_view key,
                          NativeMsvcStringV1 &output) noexcept {
  output = {};
  output.size = key.size();
  if (key.size() <= kMsvcStringInlineCapacity) {
    std::copy(key.begin(), key.end(), output.storage.inline_bytes.begin());
    output.storage.inline_bytes[key.size()] = '\0';
    return true;
  }
  output.storage.heap_bytes = key.data();
  output.capacity = key.size();
  return key.data()[key.size()] == '\0';
}

bool InvokeTitleResolver(NativeResolveLandedTitleByKeyV1 resolver,
                         const NativeMsvcStringV1 &key,
                         void *&output) noexcept {
  output = nullptr;
#if defined(_MSC_VER)
  __try {
    output = resolver(&key);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = resolver(&key);
  return true;
#endif
}

bool InvokeProvinceResolver(NativeResolveTitleProvinceV1 resolver,
                            void *landed_title,
                            void *&output) noexcept {
  output = nullptr;
#if defined(_MSC_VER)
  __try {
    output = resolver(landed_title);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = resolver(landed_title);
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

bool ResolveProvinceRoundTrip(
    const TitleMapNavigationNativeEnvironmentV1 &environment,
    const TitleMapNavigationAccessV1 &access, void *province,
    std::int32_t province_id) noexcept {
  if (province == nullptr || province_id <= 0) {
    return false;
  }
  void *game_state = nullptr;
  void *game_data = nullptr;
  void *provinces = nullptr;
  std::int32_t province_count = 0;
  void *round_trip = nullptr;
  std::int32_t round_trip_id = -1;
  return ReadSlot(access, environment.game_state_slot, game_state) &&
         game_state != nullptr &&
         ReadValue(access, game_state, kGameStateGameDataOffset, game_data) &&
         game_data != nullptr &&
         ReadValue(access, game_data, kGameDataProvinceArrayOffset,
                   provinces) &&
         ReadValue(access, game_data, kGameDataProvinceCountOffset,
                   province_count) &&
         provinces != nullptr && province_count > 1 &&
         province_count <= kMaximumProvinceCount &&
         province_id < province_count &&
         ReadValue(access, provinces,
                   static_cast<std::size_t>(province_id) * sizeof(void *),
                   round_trip) &&
         round_trip == province &&
         ReadValue(access, round_trip, kProvinceIdentityOffset,
                   round_trip_id) &&
         round_trip_id == province_id;
}

} // namespace

TitleMapNavigationNativeEnvironmentV1 BindTitleMapNavigationNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  TitleMapNavigationNativeEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = exact_build_admitted;
  if (module_base == 0) {
    return output;
  }
  output.game_state_slot = reinterpret_cast<void **>(
      module_base + kTitleMapGameStateSlotRva);
  output.landed_title_storage_slot = reinterpret_cast<void **>(
      module_base + kTitleMapLandedTitleStorageSlotRva);
  output.landed_title_fallback_slot = reinterpret_cast<void **>(
      module_base + kTitleMapLandedTitleFallbackSlotRva);
  output.resolve_landed_title_by_key =
      reinterpret_cast<NativeResolveLandedTitleByKeyV1>(
          module_base + kTitleMapResolveLandedTitleByKeyRva);
  output.resolve_title_province =
      reinterpret_cast<NativeResolveTitleProvinceV1>(
          module_base + kTitleMapResolveTitleProvinceRva);
  return output;
}

bool IsCanonicalLandedTitleKeyV1(std::string_view key) noexcept {
  if (key.size() < 3 || key.size() > kMaximumStableKeyBytes ||
      key[1] != '_') {
    return false;
  }
  switch (key[0]) {
  case 'b':
  case 'c':
  case 'd':
  case 'e':
  case 'k':
    break;
  default:
    return false;
  }
  if (key[2] < 'a' || key[2] > 'z') {
    if (key[2] < '0' || key[2] > '9') {
      return false;
    }
  }
  return std::all_of(key.begin() + 3, key.end(), [](char value) noexcept {
    return (value >= 'a' && value <= 'z') ||
           (value >= '0' && value <= '9') || value == '_';
  });
}

game::ResolveLandedTitleMapAnchorResultV1 ResolveLandedTitleMapAnchorV1(
    const TitleMapNavigationNativeEnvironmentV1 &environment,
    const TitleMapNavigationAccessV1 &access,
    const TitleMapNavigationRequestV1 &request,
    game::TitleMapNavigationFrameV1 &binding,
    game::LandedTitleMapAnchorV1 &output) noexcept {
  using Result = game::ResolveLandedTitleMapAnchorResultV1;
  binding = {};
  output = {};
  try {
    if (!EnvironmentIsExact(environment)) {
      return Result::unsupported_build;
    }
    if (access.capture_frame == nullptr || access.is_owning_thread == nullptr ||
        !access.is_owning_thread(access.context)) {
      return Result::requires_owning_thread;
    }
    if (!IsCanonicalLandedTitleKeyV1(request.title_key)) {
      return Result::internal_error;
    }
    if (!access.capture_frame(access.context, binding) ||
        binding.snapshot_revision != request.expected_snapshot_revision) {
      return Result::state_changed;
    }
    if (!binding.paused) {
      return Result::requires_paused;
    }
    if (!binding.map_ready) {
      return Result::map_not_ready;
    }

    void *title = nullptr;
    bool resolver_invoked = false;
    if (environment.offline_fixture_function_overrides) {
      resolver_invoked = access.resolve_title_fixture != nullptr &&
                         access.resolve_title_fixture(
                             access.context, request.title_key, title);
    } else {
      NativeMsvcStringV1 native_key{};
      if (!MakeNativeMsvcString(request.title_key, native_key)) {
        return Result::internal_error;
      }
      resolver_invoked = InvokeTitleResolver(
          environment.resolve_landed_title_by_key, native_key, title);
    }
    if (!resolver_invoked) {
      return Result::internal_error;
    }

    void *fallback = nullptr;
    if (!ReadSlot(access, environment.landed_title_fallback_slot, fallback)) {
      return Result::state_changed;
    }
    if (title == nullptr || title == fallback) {
      return Result::title_key_not_found;
    }

    std::int32_t title_id = -1;
    if (!ReadValue(access, title, kLandedTitleIdentityOffset, title_id) ||
        ResolveComponent(access, environment.landed_title_storage_slot,
                         environment.landed_title_fallback_slot, title_id,
                         kLandedTitleIdentityOffset) != title) {
      return Result::title_generation_mismatch;
    }
    void *title_template = nullptr;
    std::int32_t tier_raw = 0;
    std::string observed_key;
    if (!ReadValue(access, title, kLandedTitleTemplateOffset,
                   title_template) ||
        title_template == nullptr ||
        !ReadNativeString(
            access,
            static_cast<const std::byte *>(title_template) +
                kLandedTitleTemplateKeyOffset,
            observed_key) ||
        observed_key != request.title_key ||
        !ReadValue(access, title_template,
                   kLandedTitleTemplateTierOffset, tier_raw)) {
      return Result::title_generation_mismatch;
    }
    const auto tier_key = TierKey(tier_raw);
    if (tier_key.empty()) {
      return Result::title_not_centerable;
    }

    void *province = nullptr;
    bool province_invoked = false;
    if (environment.offline_fixture_function_overrides) {
      province_invoked = access.resolve_province_fixture != nullptr &&
                         access.resolve_province_fixture(
                             access.context, title, province);
    } else {
      province_invoked = InvokeProvinceResolver(
          environment.resolve_title_province, title, province);
    }
    if (!province_invoked) {
      return Result::internal_error;
    }
    std::int32_t province_id = -1;
    if (province != nullptr &&
        (!ReadValue(access, province, kProvinceIdentityOffset, province_id) ||
         !ResolveProvinceRoundTrip(environment, access, province,
                                   province_id))) {
      return Result::title_generation_mismatch;
    }

    game::TitleMapNavigationFrameV1 ending{};
    if (!access.capture_frame(access.context, ending) || ending != binding) {
      return Result::state_changed;
    }
    output.key = request.title_key;
    output.title_id = title_id;
    output.tier_raw = tier_raw;
    output.tier_key.assign(tier_key);
    if (province != nullptr) {
      output.capital_province_id = province_id;
    }
    output.native_title = title;
    output.native_capital_province = province;
    return Result::resolved;
  } catch (...) {
    binding = {};
    output = {};
    return Result::internal_error;
  }
}

std::string_view TitleMapNavigationRejectionCodeV1(
    game::ResolveLandedTitleMapAnchorResultV1 result) noexcept {
  using Result = game::ResolveLandedTitleMapAnchorResultV1;
  switch (result) {
  case Result::resolved:
    return {};
  case Result::unsupported_build:
    return "unsupported_build";
  case Result::requires_owning_thread:
    return "requires_owning_thread";
  case Result::requires_paused:
    return "requires_paused";
  case Result::map_not_ready:
    return "map_not_ready";
  case Result::title_key_not_found:
    return "title_key_not_found";
  case Result::title_generation_mismatch:
    return "title_generation_mismatch";
  case Result::title_not_centerable:
    return "title_not_centerable";
  case Result::state_changed:
    return "state_changed";
  case Result::internal_error:
    return "internal_error";
  }
  return "internal_error";
}

} // namespace xar::ck3_11906
