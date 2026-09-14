#pragma once

#include "xar_bridge/player_lifestyle_window_candidates_v1.hpp"

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::uintptr_t kLifestyleWindowRttiDynamicCastRvaV1 =
    0x3E631F4;
inline constexpr std::uintptr_t kLifestyleWindowIdlerTypeDescriptorRvaV1 =
    0x501EF28;
inline constexpr std::uintptr_t kLifestyleWindowIdlerGfxTypeDescriptorRvaV1 =
    0x501EF50;
inline constexpr std::uintptr_t kLifestyleWindowCharacterStorageSlotRvaV1 =
    0x570C130;
inline constexpr std::uintptr_t kLifestyleWindowCharacterFallbackSlotRvaV1 =
    0x570C138;
inline constexpr std::uintptr_t kLifestyleWindowPlayedCharacterIdGlobalRvaV1 =
    0x4FE7EE0;
inline constexpr std::size_t kLifestyleWindowStorageSlotsOffsetV1 = 0x20;
inline constexpr std::size_t kLifestyleWindowStorageCapacityOffsetV1 = 0x2C;
inline constexpr std::size_t kLifestyleWindowStorageSlotStrideV1 = 0x10;
inline constexpr std::size_t kLifestyleWindowStorageObjectOffsetV1 = 0x08;
inline constexpr std::size_t kLifestyleWindowCharacterIdentityOffsetV1 = 0x18;

inline constexpr std::uintptr_t kLifestyleWindowCharacterPerkDatabaseRvaV1 =
    0x88EC20;
inline constexpr std::size_t kLifestyleWindowDatabaseSpanOffsetV1 = 0x68;
inline constexpr std::size_t kLifestyleWindowStableKeyOffsetV1 = 0x18;
inline constexpr std::size_t kLifestyleWindowFocusLifestyleOffsetV1 = 0x880;
inline constexpr std::size_t kLifestyleWindowPerkLifestyleOffsetV1 = 0x468;
inline constexpr std::uintptr_t
    kLifestyleWindowCanSelectFocusEvaluatorSlotRvaV1 = 0x4323C10;
inline constexpr std::uintptr_t
    kLifestyleWindowCanSelectFocusEvaluatorTargetRvaV1 = 0x25DF570;
inline constexpr std::uintptr_t
    kLifestyleWindowCanSelectPerkEvaluatorSlotRvaV1 = 0x4323A80;
inline constexpr std::uintptr_t
    kLifestyleWindowCanSelectPerkEvaluatorTargetRvaV1 = 0x25DFAF0;

inline constexpr std::int32_t kLifestyleWindowMaximumContainerRowsV1 = 64;
inline constexpr std::int32_t kLifestyleWindowMaximumStorageSlotsV1 =
    0x01000000;

using PlayerLifestyleWindowReadMemoryV1 = bool (*)(
    void *context, std::uintptr_t address, void *output,
    std::size_t size) noexcept;

using PlayerLifestyleWindowRttiDynamicCastV1 = void *(*)(
    void *source, std::int32_t vf_delta, void *source_type,
    void *target_type, std::int32_t is_reference);
using PlayerLifestyleWindowGetDatabaseV1 = void *(*)();
using PlayerLifestyleWindowFinalEvaluatorV1 = bool (*)(
    void *window, void *definition);

struct PlayerLifestyleWindowSourceAdapterEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  bool offline_fixture = false;
  PlayerLifestyleWindowRttiDynamicCastV1 rtti_dynamic_cast = nullptr;
  PlayerLifestyleWindowGetDatabaseV1 character_perk_database = nullptr;
  PlayerLifestyleWindowFinalEvaluatorV1 can_select_focus = nullptr;
  PlayerLifestyleWindowFinalEvaluatorV1 can_select_perk = nullptr;
  PlayerLifestyleWindowFinalEvaluatorV1 can_select_perk_ignore_cost = nullptr;
};

struct PlayerLifestyleWindowSourceAdapterAccessV1 {
  void *context = nullptr;
  PlayerLifestyleWindowReadMemoryV1 read_memory = nullptr;
};

struct PlayerLifestyleWindowSourceAdapterStateV1 {
  std::atomic<std::uint64_t> root_acquisition_serial{0};
};

PlayerLifestyleWindowSourceAdapterEnvironmentV1
BindPlayerLifestyleWindowSourceAdapterEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

bool PlayerLifestyleWindowSourceAdapterEnvironmentReadyV1(
    const PlayerLifestyleWindowSourceAdapterEnvironmentV1
        &environment) noexcept;

// This function is a compatible source producer for the LIFE4 semantic core.
// Every call starts at the exact global root and retains no native pointer.
// The caller must already be on application-main in one paused transaction.
PlayerLifestyleWindowSourceReadResultV1
ReadPlayerLifestyleWindowSourceAdapterV1(
    PlayerLifestyleWindowSourceAdapterStateV1 &state,
    const PlayerLifestyleWindowSourceAdapterEnvironmentV1 &environment,
    const PlayerLifestyleWindowSourceAdapterAccessV1 &access,
    std::uintptr_t requested_module_base,
    std::uint32_t played_character_id,
    PlayerLifestyleWindowSourceSampleV1 &output) noexcept;

} // namespace xar::ck3_11906
