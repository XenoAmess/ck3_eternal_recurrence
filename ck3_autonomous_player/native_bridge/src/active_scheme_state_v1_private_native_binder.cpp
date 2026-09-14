#include "xar_bridge/active_scheme_state_v1_private_native_binder.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace xar::bridge {
namespace {

constexpr std::uintptr_t kManagerStorageOffset = 0x20;
constexpr std::uintptr_t kStorageBlockTableOffset = 0x08;
constexpr std::uintptr_t kStorageSlotsOffset = 0x20;
constexpr std::uintptr_t kStorageCapacityOffset = 0x2C;
constexpr std::uintptr_t kStorageActiveCountOffset = 0x3C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageSlotObjectOffset = 0x08;
constexpr std::size_t kSchemeBlockLength = 0x400;
constexpr std::size_t kSchemeSize = 0x358;
constexpr std::int32_t kMaximumStorageCapacity = 1 << 20;

constexpr std::uintptr_t kSchemeIdentityOffset = 0x10;
constexpr std::uintptr_t kSchemeTypeOffset = 0x20;
constexpr std::uintptr_t kSchemeOwnerOffset = 0x2C;
constexpr std::uintptr_t kSchemeTargetKindOffset = 0x30;
constexpr std::uintptr_t kSchemeTargetIdOffset = 0x34;
constexpr std::uintptr_t kSchemeProgressOffset = 0x78;
constexpr std::uintptr_t kSchemeExposedOffset = 0x27C;
constexpr std::uintptr_t kSchemeSuccessBaseOffset = 0x288;
constexpr std::uintptr_t kSchemePhasesElapsedOffset = 0x294;
constexpr std::uintptr_t kSchemeOpportunityChargesOffset = 0x298;
constexpr std::uintptr_t kSchemeBreachesOffset = 0x29C;
constexpr std::uintptr_t kSchemeFrozenOffset = 0x2A8;
constexpr std::uintptr_t kSchemeProgressGoalOffset = 0x350;

constexpr std::uintptr_t kSchemeTypeKeyOffset = 0x18;
constexpr std::uintptr_t kSchemeTypePhasesPerOpportunityOffset = 0x9B8;
constexpr std::uintptr_t kSchemeTypeMaximumBreachesOffset = 0x9BC;
constexpr std::uintptr_t kSchemeTypeIsBasicOffset = 0xB4E;

constexpr std::uintptr_t kCharacterStorageSlotRva = 0x570C130;
constexpr std::uintptr_t kCharacterFallbackSlotRva = 0x570C138;
constexpr std::uintptr_t kTitleFallbackSlotRva = 0x570C1F8;
constexpr std::uintptr_t kTitleStorageSlotRva = 0x570C210;
constexpr std::uintptr_t kComponentSlotsOffset = 0x20;
constexpr std::uintptr_t kComponentCapacityOffset = 0x2C;
constexpr std::size_t kComponentSlotStride = 0x10;
constexpr std::size_t kComponentSlotObjectOffset = 0x08;
constexpr std::uintptr_t kCharacterIdentityOffset = 0x18;
constexpr std::uintptr_t kTitleIdentityOffset = 0x10;

constexpr std::uintptr_t kReadSuccessComponentsRva = 0x276ED50;
constexpr std::uintptr_t kReadSecrecyRva = 0x276EF50;
constexpr std::uintptr_t kReadSecretFlagRva = 0x2771530;
constexpr std::int64_t kFixedPointScale = 100'000;
constexpr std::size_t kMsvcStringSizeOffset = 0x10;
constexpr std::size_t kMsvcStringCapacityOffset = 0x18;
constexpr std::size_t kMsvcStringInlineCapacity = 0x0F;
constexpr std::uint64_t kFnvOffset = 1469598103934665603ULL;
constexpr std::uint64_t kFnvPrime = 1099511628211ULL;

using State = ActiveSchemeStateV1PrivateNativeBindingState;
using Root = ActiveSchemeStateV1PrivateSourceRoot;
using Container = ActiveSchemeStateV1PrivateSourceContainer;
using Row = ActiveSchemeStateV1PrivateCapturedRow;
using ValueStatus = ActiveSchemeStateV1PrivateValueStatus;

static_assert(sizeof(void *) == 8,
              "active scheme native binder is x64-only");

bool CheckedAddress(std::uintptr_t base, std::size_t offset,
                    const void *&output) noexcept {
  if (base == 0 ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    output = nullptr;
    return false;
  }
  output = reinterpret_cast<const void *>(base + offset);
  return true;
}

bool DirectReadMemory(void *, const void *address, void *output,
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

template <typename T>
bool Read(const State &state, std::uintptr_t base, std::size_t offset,
          T &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         state.operations.read_memory(state.operation_context, address, &output,
                                      sizeof(output));
}

bool DefaultReadStableKey(void *, const void *native_string, char *output,
                          std::size_t output_capacity) noexcept {
  if (native_string == nullptr || output == nullptr || output_capacity < 2) {
    return false;
  }
  output[0] = '\0';
  std::size_t size = 0;
  std::size_t capacity = 0;
  const auto address = reinterpret_cast<std::uintptr_t>(native_string);
  if (!DirectReadMemory(nullptr,
                        reinterpret_cast<const void *>(
                            address + kMsvcStringSizeOffset),
                        &size, sizeof(size)) ||
      !DirectReadMemory(nullptr,
                        reinterpret_cast<const void *>(
                            address + kMsvcStringCapacityOffset),
                        &capacity, sizeof(capacity)) ||
      size == 0 || size > capacity || size >= output_capacity) {
    return false;
  }
  const void *bytes = native_string;
  if (capacity > kMsvcStringInlineCapacity &&
      (!DirectReadMemory(nullptr, native_string, &bytes, sizeof(bytes)) ||
       bytes == nullptr)) {
    return false;
  }
  if (!DirectReadMemory(nullptr, bytes, output, size)) return false;
  output[size] = '\0';
  return std::none_of(output, output + size, [](unsigned char value) {
    return value == 0 || value < 0x20U;
  });
}

#if defined(_MSC_VER)
#define XAR_SCHEME_BINDER_FASTCALL __fastcall
#else
#define XAR_SCHEME_BINDER_FASTCALL
#endif

struct SuccessComponents {
  std::int64_t additive = 0;
  std::int64_t growth = 0;
  std::int64_t maximum = 0;
};

using ReadSuccessComponents = SuccessComponents *(
    XAR_SCHEME_BINDER_FASTCALL *)(const void *scheme,
                                  SuccessComponents *output, const void *,
                                  const void *);
using ReadSecrecy = std::int32_t(XAR_SCHEME_BINDER_FASTCALL *)(
    const void *scheme, std::int32_t option);
using ReadSecretFlag = bool(XAR_SCHEME_BINDER_FASTCALL *)(
    const void *scheme);

#undef XAR_SCHEME_BINDER_FASTCALL

bool ExactPercent(std::int64_t raw, std::int32_t &output) noexcept {
  if (raw < 0 || raw > 100 * kFixedPointScale ||
      raw % kFixedPointScale != 0) {
    output = 0;
    return false;
  }
  output = static_cast<std::int32_t>(raw / kFixedPointScale);
  return true;
}

bool DefaultReadSuccess(void *, std::uintptr_t module_base,
                        const void *scheme, std::int32_t &success,
                        std::int32_t &maximum) noexcept {
  success = 0;
  maximum = 0;
  if (module_base == 0 || scheme == nullptr) return false;
  SuccessComponents components{};
  std::int64_t base = 0;
  SuccessComponents *returned = nullptr;
#if defined(_MSC_VER)
  __try {
    returned = reinterpret_cast<ReadSuccessComponents>(
        module_base + kReadSuccessComponentsRva)(scheme, &components, nullptr,
                                                  nullptr);
    std::memcpy(&base,
                static_cast<const std::byte *>(scheme) +
                    kSchemeSuccessBaseOffset,
                sizeof(base));
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  returned = reinterpret_cast<ReadSuccessComponents>(
      module_base + kReadSuccessComponentsRva)(scheme, &components, nullptr,
                                                nullptr);
  std::memcpy(&base,
              static_cast<const std::byte *>(scheme) +
                  kSchemeSuccessBaseOffset,
              sizeof(base));
#endif
  if (returned != &components ||
      components.additive >
          (std::numeric_limits<std::int64_t>::max)() - base) {
    return false;
  }
  const auto success_raw =
      (std::min)(base + components.additive, components.maximum);
  return ExactPercent(success_raw, success) &&
         ExactPercent(components.maximum, maximum) && success <= maximum;
}

bool DefaultReadSecrecy(void *, std::uintptr_t module_base,
                        const void *scheme,
                        std::int32_t &secrecy) noexcept {
  secrecy = 0;
  if (module_base == 0 || scheme == nullptr) return false;
#if defined(_MSC_VER)
  __try {
    secrecy = reinterpret_cast<ReadSecrecy>(module_base + kReadSecrecyRva)(
        scheme, 0);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  secrecy = reinterpret_cast<ReadSecrecy>(module_base + kReadSecrecyRva)(
      scheme, 0);
  return true;
#endif
}

bool DefaultReadSecretFlag(void *, std::uintptr_t module_base,
                           const void *scheme,
                           bool &is_secret) noexcept {
  is_secret = false;
  if (module_base == 0 || scheme == nullptr) return false;
#if defined(_MSC_VER)
  __try {
    is_secret = reinterpret_cast<ReadSecretFlag>(
        module_base + kReadSecretFlagRva)(scheme);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  is_secret = reinterpret_cast<ReadSecretFlag>(
      module_base + kReadSecretFlagRva)(scheme);
  return true;
#endif
}

ActiveSchemeStateV1PrivateNativeOperations DefaultOperations() noexcept {
  return {&DirectReadMemory, &DefaultReadStableKey, &DefaultReadSuccess,
          &DefaultReadSecrecy, &DefaultReadSecretFlag};
}

bool Complete(const ActiveSchemeStateV1PrivateNativeOperations &ops) noexcept {
  return ops.read_memory != nullptr && ops.read_stable_key != nullptr &&
         ops.read_success != nullptr && ops.read_secrecy != nullptr &&
         ops.read_secret_flag != nullptr;
}

bool AnyOverride(
    const ActiveSchemeStateV1PrivateNativeOperations &ops) noexcept {
  return ops.read_memory != nullptr || ops.read_stable_key != nullptr ||
         ops.read_success != nullptr || ops.read_secrecy != nullptr ||
         ops.read_secret_flag != nullptr;
}

bool VerifyExactImage(const State &state) noexcept {
  std::array<std::uint8_t, 16> observed{};
  for (const auto &signature :
       kActiveSchemeStateV1PrivateNativeSignatures) {
    observed.fill(0);
    if (!state.operations.read_memory(
            state.operation_context,
            reinterpret_cast<const void *>(state.module_base + signature.rva),
            observed.data(), signature.size) ||
        !std::equal(observed.begin(), observed.begin() + signature.size,
                    signature.bytes.begin())) {
      return false;
    }
  }
  for (const auto &slot : kActiveSchemeStateV1PrivateNativeSlots) {
    std::uintptr_t observed_function = 0;
    if (!state.operations.read_memory(
            state.operation_context,
            reinterpret_cast<const void *>(state.module_base + slot.slot_rva),
            &observed_function, sizeof(observed_function)) ||
        observed_function != state.module_base + slot.function_rva) {
      return false;
    }
  }
  return true;
}

std::uint64_t HashValue(std::uint64_t hash, std::uint64_t value) noexcept {
  for (unsigned shift = 0; shift != 64; shift += 8) {
    hash ^= (value >> shift) & 0xFFU;
    hash *= kFnvPrime;
  }
  return hash;
}

bool ValidateVtable(const State &state, std::uintptr_t object,
                    std::uintptr_t expected_rva) noexcept {
  std::uintptr_t vtable = 0;
  return Read(state, object, 0, vtable) &&
         vtable == state.module_base + expected_rva;
}

bool ResolveRootInternal(const State &state, Root &output) noexcept {
  output = {};
  std::uintptr_t application = 0;
  if (!Read(state, state.module_base,
            kActiveSchemeStateV1PrivateApplicationSlotRva, application) ||
      application == 0 ||
      kActiveSchemeStateV1PrivateManagerOffset >
          (std::numeric_limits<std::uintptr_t>::max)() - application) {
    return false;
  }
  const auto manager =
      application + kActiveSchemeStateV1PrivateManagerOffset;
  std::uintptr_t storage = 0;
  if (!ValidateVtable(state, manager,
                      kActiveSchemeStateV1PrivateManagerVtableRva) ||
      !Read(state, manager, kManagerStorageOffset, storage) || storage == 0 ||
      !ValidateVtable(state, storage,
                      kActiveSchemeStateV1PrivateStorageVtableRva)) {
    return false;
  }
  auto generation = HashValue(kFnvOffset, manager);
  generation = HashValue(generation, storage);
  if (generation == 0) generation = 1;
  output.identity_round_trip = true;
  output.native_address = manager;
  output.identity = manager;
  output.generation = generation;
  return true;
}

struct Enumeration {
  std::size_t player_count = 0;
  std::uint64_t generation = kFnvOffset;
  std::uintptr_t selected_scheme = 0;
  std::uint32_t selected_identity = 0;
};

bool Enumerate(const State &state, std::uintptr_t storage,
               std::int64_t owner_character_id, std::size_t selected_index,
               bool select_row, Enumeration &output) noexcept {
  output = {};
  output.generation = HashValue(kFnvOffset,
                                static_cast<std::uint64_t>(owner_character_id));
  std::uintptr_t block_table = 0;
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  std::int32_t active_count = 0;
  if (!ValidateVtable(state, storage,
                      kActiveSchemeStateV1PrivateStorageVtableRva) ||
      !Read(state, storage, kStorageBlockTableOffset, block_table) ||
      !Read(state, storage, kStorageSlotsOffset, slots) ||
      !Read(state, storage, kStorageCapacityOffset, capacity) ||
      !Read(state, storage, kStorageActiveCountOffset, active_count) ||
      block_table == 0 || slots == 0 || capacity <= 0 ||
      capacity > kMaximumStorageCapacity || active_count < 0 ||
      active_count > capacity) {
    return false;
  }

  std::int32_t observed_active = 0;
  for (std::int32_t index = 0; index < capacity; ++index) {
    std::uintptr_t scheme = 0;
    if (!Read(state, slots,
              static_cast<std::size_t>(index) * kStorageSlotStride +
                  kStorageSlotObjectOffset,
              scheme)) {
      return false;
    }
    if (scheme == 0) continue;
    ++observed_active;
    std::uintptr_t block = 0;
    const auto block_index = static_cast<std::size_t>(index) /
                             kSchemeBlockLength;
    if (!Read(state, block_table, block_index * sizeof(std::uintptr_t),
              block) ||
        block == 0) {
      return false;
    }
    const auto within_block = static_cast<std::size_t>(index) &
                              (kSchemeBlockLength - 1);
    if (within_block >
        ((std::numeric_limits<std::uintptr_t>::max)() - block) /
            kSchemeSize) {
      return false;
    }
    const auto expected_scheme = block + within_block * kSchemeSize;
    std::uint32_t identity = 0;
    std::int32_t owner = 0;
    if (scheme != expected_scheme ||
        !ValidateVtable(state, scheme,
                        kActiveSchemeStateV1PrivateActiveSchemeVtableRva) ||
        !Read(state, scheme, kSchemeIdentityOffset, identity) ||
        (identity & 0x00FFFFFFU) != static_cast<std::uint32_t>(index) ||
        (identity >> 24U) == 0 ||
        !Read(state, scheme, kSchemeOwnerOffset, owner)) {
      return false;
    }
    if (owner != owner_character_id) continue;
    if (output.player_count == selected_index && select_row) {
      output.selected_scheme = scheme;
      output.selected_identity = identity;
    }
    ++output.player_count;
    if (output.player_count > kActiveSchemeStateV1PrivateMaximumRows) {
      return false;
    }
    output.generation = HashValue(output.generation, identity);
  }
  if (observed_active != active_count ||
      (select_row && output.selected_scheme == 0)) {
    return false;
  }
  output.generation = HashValue(output.generation,
                                static_cast<std::uint64_t>(output.player_count));
  if (output.generation == 0) output.generation = 1;
  return true;
}

bool ResolveStorage(const State &state, const Root &root,
                    std::uintptr_t &storage) noexcept {
  storage = 0;
  Root current{};
  return ResolveRootInternal(state, current) &&
         current.native_address == root.native_address &&
         current.identity == root.identity &&
         current.generation == root.generation &&
         Read(state, current.native_address, kManagerStorageOffset, storage) &&
         storage != 0;
}

bool ResolveContainerInternal(const State &state, const Root &root,
                              std::int64_t owner_character_id,
                              Container &output) noexcept {
  output = {};
  std::uintptr_t storage = 0;
  Enumeration enumeration{};
  if (!ResolveStorage(state, root, storage) ||
      !Enumerate(state, storage, owner_character_id, 0, false,
                 enumeration)) {
    return false;
  }
  output.identity_round_trip = true;
  output.native_address = storage;
  output.identity = storage;
  output.generation = enumeration.generation;
  output.owner_character_id = owner_character_id;
  output.row_count = enumeration.player_count;
  return true;
}

bool ResolveComponent(const State &state, std::uintptr_t storage_slot_rva,
                      std::uintptr_t fallback_slot_rva,
                      std::uint32_t full_identity,
                      std::uintptr_t identity_offset) noexcept {
  std::uintptr_t storage = 0;
  std::uintptr_t fallback = 0;
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  if (!Read(state, state.module_base, storage_slot_rva, storage) ||
      !Read(state, state.module_base, fallback_slot_rva, fallback) ||
      storage == 0 ||
      !Read(state, storage, kComponentSlotsOffset, slots) ||
      !Read(state, storage, kComponentCapacityOffset, capacity) ||
      slots == 0 || capacity <= 0 || capacity > kMaximumStorageCapacity) {
    return false;
  }
  const auto index = full_identity & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return false;
  std::uintptr_t object = 0;
  std::uint32_t observed_identity = 0;
  return Read(state, slots,
              static_cast<std::size_t>(index) * kComponentSlotStride +
                  kComponentSlotObjectOffset,
              object) &&
         object != 0 && object != fallback &&
         Read(state, object, identity_offset, observed_identity) &&
         observed_identity == full_identity;
}

template <std::size_t Size>
bool CopyLiteral(std::array<char, Size> &output,
                 std::string_view literal) noexcept {
  output.fill('\0');
  if (literal.empty() || literal.size() >= Size) return false;
  std::copy(literal.begin(), literal.end(), output.begin());
  return true;
}

template <typename T>
void SetAvailable(ActiveSchemeStateV1PrivateValue<T> &output,
                  T value) noexcept {
  output.status = ValueStatus::available;
  output.value = value;
}

bool ReadCapturedRow(const State &state, std::uintptr_t scheme,
                     std::uint32_t identity, std::int64_t owner_character_id,
                     Row &output) noexcept {
  output = {};
  std::uint32_t observed_identity = 0;
  std::int32_t observed_owner = 0;
  std::uintptr_t type = 0;
  if (!ValidateVtable(state, scheme,
                      kActiveSchemeStateV1PrivateActiveSchemeVtableRva) ||
      !Read(state, scheme, kSchemeIdentityOffset, observed_identity) ||
      observed_identity != identity ||
      !Read(state, scheme, kSchemeOwnerOffset, observed_owner) ||
      observed_owner != owner_character_id ||
      !Read(state, scheme, kSchemeTypeOffset, type) || type == 0 ||
      !ValidateVtable(state, type,
                      kActiveSchemeStateV1PrivateSchemeTypeVtableRva) ||
      !state.operations.read_stable_key(
          state.operation_context,
          reinterpret_cast<const void *>(type + kSchemeTypeKeyOffset),
          output.scheme_type_key.data(), output.scheme_type_key.size())) {
    return false;
  }

  bool is_basic = false;
  if (!Read(state, type, kSchemeTypeIsBasicOffset, is_basic)) return false;
  const std::string_view type_key{output.scheme_type_key.data()};
  if (type_key == "sway") {
    if (!is_basic || !CopyLiteral(output.category_key, "personal"))
      return false;
  } else if (type_key == "murder") {
    if (is_basic || !CopyLiteral(output.category_key, "hostile")) return false;
  } else {
    return false;
  }

  std::int32_t target_kind = -1;
  std::uint32_t target_identity = 0;
  if (!Read(state, scheme, kSchemeTargetKindOffset, target_kind) ||
      !Read(state, scheme, kSchemeTargetIdOffset, target_identity) ||
      target_identity == 0) {
    return false;
  }
  if (target_kind == 0) {
    if (!ResolveComponent(state, kCharacterStorageSlotRva,
                          kCharacterFallbackSlotRva, target_identity,
                          kCharacterIdentityOffset)) {
      return false;
    }
    output.target_kind = ActiveSchemeStateV1PrivateTargetKind::character;
  } else if (target_kind == 1) {
    if (!ResolveComponent(state, kTitleStorageSlotRva,
                          kTitleFallbackSlotRva, target_identity,
                          kTitleIdentityOffset)) {
      return false;
    }
    output.target_kind = ActiveSchemeStateV1PrivateTargetKind::title;
  } else {
    return false;
  }

  bool is_secret = false;
  bool is_exposed = false;
  std::uint8_t frozen_state = 0;
  std::int32_t progress = 0;
  std::int32_t progress_goal = 0;
  if (!state.operations.read_secret_flag(state.operation_context,
                                         state.module_base,
                                         reinterpret_cast<const void *>(scheme),
                                         is_secret) ||
      !Read(state, scheme, kSchemeExposedOffset, is_exposed) ||
      !Read(state, scheme, kSchemeFrozenOffset, frozen_state) ||
      frozen_state > 1 ||
      !Read(state, scheme, kSchemeProgressOffset, progress) ||
      !Read(state, scheme, kSchemeProgressGoalOffset, progress_goal)) {
    return false;
  }

  output.scheme_identity_round_trip = true;
  output.scheme_instance_id = identity;
  output.scheme_instance_generation = identity >> 24U;
  output.owner_character_id = owner_character_id;
  output.target_identity_round_trip = true;
  output.target_id = target_identity;
  output.definition_flags_verified = true;
  output.is_basic = is_basic;
  output.is_secret = is_secret;
  output.is_exposed = is_exposed;
  output.is_frozen = frozen_state == 1;
  SetAvailable(output.progress, progress);
  SetAvailable(output.progress_goal, progress_goal);
  if (is_basic) return true;

  std::int32_t success = 0;
  std::int32_t maximum_success = 0;
  std::int32_t secrecy = 0;
  std::int32_t opportunities = 0;
  std::int32_t breaches = 0;
  std::int32_t maximum_breaches = 0;
  std::int32_t phases_per_opportunity = 0;
  std::int32_t phases_elapsed = 0;
  if (!state.operations.read_success(
          state.operation_context, state.module_base,
          reinterpret_cast<const void *>(scheme), success, maximum_success) ||
      !state.operations.read_secrecy(
          state.operation_context, state.module_base,
          reinterpret_cast<const void *>(scheme), secrecy) ||
      !Read(state, scheme, kSchemeOpportunityChargesOffset, opportunities) ||
      !Read(state, scheme, kSchemeBreachesOffset, breaches) ||
      !Read(state, type, kSchemeTypeMaximumBreachesOffset,
            maximum_breaches) ||
      !Read(state, type, kSchemeTypePhasesPerOpportunityOffset,
            phases_per_opportunity) ||
      !Read(state, scheme, kSchemePhasesElapsedOffset, phases_elapsed) ||
      phases_elapsed > phases_per_opportunity) {
    return false;
  }
  SetAvailable(output.success_chance, success);
  SetAvailable(output.maximum_success_chance, maximum_success);
  SetAvailable(output.secrecy, secrecy);
  SetAvailable(output.opportunity_charges, opportunities);
  SetAvailable(output.breaches, breaches);
  SetAvailable(output.maximum_breaches, maximum_breaches);
  SetAvailable(output.phases_remaining_until_opportunity,
               phases_per_opportunity - phases_elapsed);
  return true;
}

bool CaptureFrameThunk(
    void *context,
    ActiveSchemeStateV1PrivateSourceFrame &output) noexcept {
  auto &state = *static_cast<State *>(context);
  return state.attached && state.upstream_capture_frame != nullptr &&
         state.upstream_capture_frame(state.upstream_context, output);
}

bool ResolveRootThunk(void *context, std::int64_t,
                      Root &output) noexcept {
  auto &state = *static_cast<State *>(context);
  return state.attached && ResolveRootInternal(state, output);
}

bool ResolveContainerThunk(void *context, const Root &root,
                           std::int64_t owner_character_id,
                           Container &output) noexcept {
  auto &state = *static_cast<State *>(context);
  return state.attached && owner_character_id > 0 &&
         ResolveContainerInternal(state, root, owner_character_id, output);
}

bool ReadRowThunk(void *context, const Root &root,
                  const Container &container, std::size_t index,
                  Row &output) noexcept {
  auto &state = *static_cast<State *>(context);
  output = {};
  if (!state.attached || index >= container.row_count ||
      container.owner_character_id <= 0) {
    return false;
  }
  Container current{};
  std::uintptr_t storage = 0;
  Enumeration enumeration{};
  if (!ResolveContainerInternal(state, root, container.owner_character_id,
                                current) ||
      current.native_address != container.native_address ||
      current.identity != container.identity ||
      current.generation != container.generation ||
      current.row_count != container.row_count ||
      !ResolveStorage(state, root, storage) || storage != container.native_address ||
      !Enumerate(state, storage, container.owner_character_id, index, true,
                 enumeration) ||
      enumeration.generation != container.generation ||
      enumeration.player_count != container.row_count) {
    return false;
  }
  return ReadCapturedRow(state, enumeration.selected_scheme,
                         enumeration.selected_identity,
                         container.owner_character_id, output);
}

} // namespace

bool BindActiveSchemeStateV1PrivateNative(
    const ActiveSchemeStateV1PrivateNativeEnvironment &binding,
    ActiveSchemeStateV1PrivateNativeBindingState &state,
    ActiveSchemeStateV1PrivateSourceAccess &access) noexcept {
  if (!binding.binding_enabled || !binding.exact_build_admitted ||
      binding.admitted_executable_sha256 !=
          kActiveSchemeStateV1PrivateObserverExecutableSha256 ||
      binding.admitted_game_version !=
          kActiveSchemeStateV1PrivateNativeBinderGameVersion ||
      binding.module_base == 0 || access.capture_frame == nullptr ||
      access.context == &state || state.attached ||
      access.resolve_root != nullptr || access.resolve_container != nullptr ||
      access.read_row != nullptr) {
    return false;
  }

  ActiveSchemeStateV1PrivateNativeOperations operations{};
  if (binding.offline_fixture) {
    operations = binding.operations;
  } else {
    if (AnyOverride(binding.operations) || binding.operation_context != nullptr) {
      return false;
    }
    operations = DefaultOperations();
  }
  if (!Complete(operations)) return false;

  state = {};
  state.module_base = binding.module_base;
  state.operation_context = binding.operation_context;
  state.operations = operations;
  state.upstream_context = access.context;
  state.upstream_capture_frame = access.capture_frame;
  if (!VerifyExactImage(state)) {
    state = {};
    return false;
  }
  state.attached = true;

  access.exact_build_admitted = true;
  access.admitted_executable_sha256 =
      kActiveSchemeStateV1PrivateObserverExecutableSha256;
  access.context = &state;
  access.capture_frame = &CaptureFrameThunk;
  access.resolve_root = &ResolveRootThunk;
  access.resolve_container = &ResolveContainerThunk;
  access.read_row = &ReadRowThunk;
  return true;
}

} // namespace xar::bridge
