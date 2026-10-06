#pragma once

#include "xar_bridge/ck3_12002.hpp"

#include <string>
#include <vector>

namespace xar::ck3_12002::religion_conversion_rite {

inline constexpr std::uintptr_t kFaithAndRitePrimaryVtableRva = 0x4770340;
inline constexpr std::uintptr_t kFaithAndRiteSecondaryVtableRva = 0x47703D8;
inline constexpr std::uintptr_t kFaithAndRiteValidateRva = 0x29A34C0;
inline constexpr std::uintptr_t kRiteRulesGateRva = 0x1D63700;
inline constexpr std::uintptr_t kRiteStorageSlotRva = 0x5D1E2F8;
inline constexpr std::uintptr_t kCharacterFaithGetterRva = 0x289E750;
inline constexpr std::uintptr_t kFaithRitesGetterRva = 0xB801B0;

// Exact stack value used by FaithConversionWindow.CanConvertFaithAndRite.
// This module only calls the validator. It never queues or executes this value.
struct alignas(8) FaithAndRiteConversionCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 15> reserved{};
  std::uintptr_t secondary_vtable = 0;
  std::int32_t actor_id = -1;
  std::uint32_t target_rite_id = 0xFFFFFFFFU;
  std::uint8_t pay_piety = 1;
  std::array<std::byte, 7> tail{};
};
static_assert(sizeof(FaithAndRiteConversionCommand) == 0x30);
static_assert(offsetof(FaithAndRiteConversionCommand, actor_id) == 0x20);
static_assert(offsetof(FaithAndRiteConversionCommand, target_rite_id) == 0x24);
static_assert(offsetof(FaithAndRiteConversionCommand, pay_piety) == 0x28);

using Validate = bool (*)(const FaithAndRiteConversionCommand *, void *reasons);
using ObjectGetter = void *(*)(void *);
using ContainerGetter = const void *(*)(void *);
using ReadOnlyValueFactory = FaithAndRiteConversionCommand (*)(
    std::uintptr_t, std::int32_t, std::uint32_t, bool) noexcept;
struct Bindings {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  CoreBindings core{};
  void **rite_storage_slot = nullptr;
  Validate validate = nullptr;
  ObjectGetter character_faith = nullptr;
  ContainerGetter faith_rites = nullptr;
  // A later exact-build binder supplies its independently proved value vptrs.
  // The absent callback preserves this build's original factory behavior.
  ReadOnlyValueFactory read_only_value_factory = nullptr;
};

enum class Failure {
  none,
  bindings_unavailable,
  played_character_unavailable,
  frame_not_paused,
  current_rite_unavailable,
  target_rite_unavailable,
  faith_unavailable,
  rites_unavailable,
  state_changed,
};

struct Preview {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::uint32_t current_rite_id = 0xFFFFFFFFU;
  std::uint32_t target_rite_id = 0xFFFFFFFFU;
  std::uint32_t current_faith_id = 0xFFFFFFFFU;
  std::uint32_t target_faith_id = 0xFFFFFFFFU;
  bool same_faith = false;
  // The native entry-button getter additionally checks this difference.
  // Rite.IsVisibleInGui is a separate UI gate and is not inferred here.
  bool different_from_current_rite = false;
  bool validator_without_payment = false;
  bool validator_with_payment = false;
};

struct FaithRites {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::uint32_t faith_id = 0xFFFFFFFFU;
  // Native association order, including the current Rite. Membership is not
  // a conversion verdict; evaluate each chosen ID through ReadRitePreview.
  std::vector<std::uint32_t> rite_ids;
};

Bindings BindRiteConversionImage12002(std::uintptr_t module_base,
                                    std::string_view executable_sha256) noexcept;
FaithAndRiteConversionCommand MakeReadOnlyConvertRiteValue12002(std::uintptr_t module_base,
                                                   std::int32_t actor_id,
                                                   std::uint32_t target_rite_id,
                                                   bool pay_piety) noexcept;
// Only called by the existing application-main owner on a paused snapshot.
bool ReadRitePreview12002(const Bindings &, std::uint64_t capture_epoch,
                         std::uint32_t target_rite_id, Preview &) noexcept;
bool ReadCurrentFaithRites12002(const Bindings &, std::uint64_t capture_epoch,
                               FaithRites &) noexcept;
const char *RiteConversionFailureKey(Failure) noexcept;
std::string SerializeRitePreview12002(const Preview &);
std::string SerializeCurrentFaithRites12002(const FaithRites &);

} // namespace xar::ck3_12002::religion_conversion_rite
