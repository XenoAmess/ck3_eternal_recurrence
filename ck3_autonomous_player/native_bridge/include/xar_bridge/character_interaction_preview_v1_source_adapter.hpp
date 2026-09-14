#pragma once

#include "xar_bridge/character_interaction_preview_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kCharacterInteractionPreviewSourceAdapterPrivateKeyV1 =
        "character_interaction_preview_v1_source_adapter";
inline constexpr std::uintptr_t
    kCharacterInteractionPreviewHumanPlayerPredicateRvaV1 = 0x28BCEB0;

using CharacterInteractionPreviewAdapterGetDatabaseV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *&output) noexcept;
using CharacterInteractionPreviewAdapterHashStableKeyV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *database,
    std::string_view key, std::int32_t &output) noexcept;
using CharacterInteractionPreviewAdapterLookupDefinitionV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *database,
    std::int32_t key_hash, void *&output) noexcept;
using CharacterInteractionPreviewAdapterConstructContextV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *context_storage,
    void *definition, std::int32_t actor_character_id,
    std::int32_t recipient_character_id, void *&output) noexcept;
using CharacterInteractionPreviewAdapterRefreshContextV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *interaction_context,
    bool refresh) noexcept;
using CharacterInteractionPreviewAdapterContextStepV1 = bool (*)(
    void *context, std::uintptr_t module_base,
    void *interaction_context) noexcept;
using CharacterInteractionPreviewAdapterCanSendV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *interaction_context,
    bool &output) noexcept;
using CharacterInteractionPreviewAdapterCostsV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *interaction_context,
    std::array<std::int64_t, game::kCharacterInteractionPreviewCostCountV1>
        &output) noexcept;
using CharacterInteractionPreviewAdapterTriggerV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *trigger,
    const void *event_target_scope, bool &output) noexcept;
using CharacterInteractionPreviewAdapterRawAcceptanceV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *interaction_context,
    std::int64_t &output) noexcept;
using CharacterInteractionPreviewAdapterOuterAcceptanceV1 = bool (*)(
    void *context, std::uintptr_t module_base, void *interaction_context,
    std::int32_t &status) noexcept;
using CharacterInteractionPreviewAdapterHumanPlayerV1 = bool (*)(
    void *context, std::uintptr_t module_base,
    std::int32_t character_id, bool &output) noexcept;
using CharacterInteractionPreviewAdapterReadMemoryV1 = bool (*)(
    void *context, const void *address, void *output,
    std::size_t size) noexcept;

struct CharacterInteractionPreviewSourceOperationsV1 {
  CharacterInteractionPreviewAdapterGetDatabaseV1 get_database = nullptr;
  CharacterInteractionPreviewAdapterHashStableKeyV1 hash_stable_key = nullptr;
  CharacterInteractionPreviewAdapterLookupDefinitionV1 lookup_definition =
      nullptr;
  CharacterInteractionPreviewAdapterConstructContextV1 construct_context =
      nullptr;
  CharacterInteractionPreviewAdapterRefreshContextV1 refresh_context =
      nullptr;
  CharacterInteractionPreviewAdapterContextStepV1 finalize_context = nullptr;
  CharacterInteractionPreviewAdapterCanSendV1 can_send = nullptr;
  CharacterInteractionPreviewAdapterCostsV1 evaluate_costs = nullptr;
  CharacterInteractionPreviewAdapterTriggerV1 evaluate_trigger = nullptr;
  CharacterInteractionPreviewAdapterRawAcceptanceV1 intermediary_raw =
      nullptr;
  CharacterInteractionPreviewAdapterRawAcceptanceV1 recipient_raw = nullptr;
  CharacterInteractionPreviewAdapterOuterAcceptanceV1 outer_final = nullptr;
  CharacterInteractionPreviewAdapterHumanPlayerV1 is_human_player = nullptr;
  CharacterInteractionPreviewAdapterContextStepV1 destroy_context = nullptr;
  CharacterInteractionPreviewAdapterReadMemoryV1 read_memory = nullptr;
};

struct CharacterInteractionPreviewSourceEnvironmentV1 {
  bool adapter_enabled = false;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  CharacterInteractionPreviewSourceOperationsV1 operations{};

  void *upstream_context = nullptr;
  CaptureCharacterInteractionPreviewFrameV1 capture_frame = nullptr;
  IsCharacterInteractionPreviewMainThreadV1 is_main_thread = nullptr;
};

struct CharacterInteractionPreviewSourceStateV1 {
  std::uintptr_t module_base = 0;
  void *operation_context = nullptr;
  CharacterInteractionPreviewSourceOperationsV1 operations{};
  void *upstream_context = nullptr;
  CaptureCharacterInteractionPreviewFrameV1 upstream_capture_frame = nullptr;
  IsCharacterInteractionPreviewMainThreadV1 upstream_is_main_thread = nullptr;
  CharacterInteractionPreviewEnvironmentV1 core_environment{};
  CharacterInteractionPreviewAccessV1 core_access{};
  void *active_owned_context = nullptr;
  std::uint64_t completed_context_count = 0;
  bool attached = false;
  bool context_active = false;
  bool terminal_cleanup_failure = false;
};

// Builds only a private source adapter. When no operations are supplied, the
// exact 1.19.0.6 function addresses are used. Tests must supply either a full
// operation table or no overrides; partial tables are rejected.
bool BindCharacterInteractionPreviewSourceAdapterV1(
    const CharacterInteractionPreviewSourceEnvironmentV1 &environment,
    CharacterInteractionPreviewSourceStateV1 &state) noexcept;

game::ReadCharacterInteractionPreviewResultV1
ReadCharacterInteractionPreviewFromSourceAdapterV1(
    CharacterInteractionPreviewSourceStateV1 &state,
    const CharacterInteractionPreviewRequestV1 &request,
    game::CharacterInteractionPreviewV1 &output) noexcept;

} // namespace xar::ck3_11906
