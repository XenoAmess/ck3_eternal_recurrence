#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class CharacterInteractionPreviewStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class CharacterInteractionPreviewFailureV1 : std::uint32_t {
  none = 0,
  invalid_request,
  interaction_not_allowlisted,
  exact_build_not_admitted,
  native_bindings_unavailable,
  application_main_thread_required,
  frame_capture_failed,
  snapshot_identity_mismatch,
  revision_drift,
  date_drift,
  not_paused,
  player_unavailable,
  definition_lookup_failed,
  definition_identity_mismatch,
  actor_lookup_failed,
  recipient_lookup_failed,
  character_identity_mismatch,
  character_not_alive,
  context_construction_failed,
  context_refresh_failed,
  context_finalize_failed,
  can_send_evaluation_failed,
  cost_evaluation_failed,
  acceptance_evaluation_failed,
  acceptance_invariant_failed,
  context_cleanup_failed,
  native_sample_drift,
};

enum class CharacterInteractionAcceptanceKindV1 : std::uint32_t {
  unavailable = 0,
  auto_accept = 1,
  ai_final = 2,
  human_pending = 3,
};

inline constexpr std::size_t kCharacterInteractionPreviewCostCountV1 = 10;
inline constexpr std::int64_t kCharacterInteractionPreviewRawScaleV1 = 100'000;
inline constexpr std::size_t kCharacterInteractionPreviewSnapshotIdCapacityV1 =
    48;

struct CharacterInteractionPreviewDefinitionV1 {
  std::string canonical_key;
  std::uint32_t deterministic_key_hash = 0;
  std::int32_t runtime_ordinal = -1;

  friend bool operator==(const CharacterInteractionPreviewDefinitionV1 &,
                         const CharacterInteractionPreviewDefinitionV1 &) =
      default;
};

struct CharacterInteractionPreviewRolesV1 {
  std::int32_t actor_character_id = -1;
  std::int32_t recipient_character_id = -1;

  friend bool operator==(const CharacterInteractionPreviewRolesV1 &,
                         const CharacterInteractionPreviewRolesV1 &) =
      default;
};

struct CharacterInteractionPreviewCostsV1 {
  std::int64_t raw_scale = kCharacterInteractionPreviewRawScaleV1;
  std::array<std::int64_t, kCharacterInteractionPreviewCostCountV1> raw{};

  friend bool operator==(const CharacterInteractionPreviewCostsV1 &,
                         const CharacterInteractionPreviewCostsV1 &) =
      default;
};

struct CharacterInteractionPreviewAcceptanceV1 {
  CharacterInteractionAcceptanceKindV1 kind =
      CharacterInteractionAcceptanceKindV1::unavailable;
  bool recipient_is_ai = false;
  bool auto_accept = false;
  bool intermediary_present = false;
  bool intermediary_raw_present = false;
  std::int64_t intermediary_raw = 0;
  bool recipient_raw_present = false;
  std::int64_t recipient_raw = 0;
  bool final_status_present = false;
  std::int32_t final_status_raw = -1;
  bool would_accept_now_present = false;
  bool would_accept_now = false;

  friend bool operator==(const CharacterInteractionPreviewAcceptanceV1 &,
                         const CharacterInteractionPreviewAcceptanceV1 &) =
      default;
};

struct CharacterInteractionPreviewReadinessV1 {
  bool definition_ready = false;
  bool actor_ready = false;
  bool recipient_ready = false;
  bool finalized_context_ready = false;
  bool can_send_ready = false;
  bool costs_ready = false;
  bool acceptance_ready = false;
  bool same_frame_ready = false;

  friend bool operator==(const CharacterInteractionPreviewReadinessV1 &,
                         const CharacterInteractionPreviewReadinessV1 &) =
      default;
};

struct CharacterInteractionPreviewV1 {
  CharacterInteractionPreviewStatusV1 status =
      CharacterInteractionPreviewStatusV1::unavailable;
  CharacterInteractionPreviewFailureV1 unavailable_reason =
      CharacterInteractionPreviewFailureV1::none;
  std::array<char, kCharacterInteractionPreviewSnapshotIdCapacityV1>
      snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  CharacterInteractionPreviewDefinitionV1 definition{};
  CharacterInteractionPreviewRolesV1 roles{};
  bool can_send = false;
  CharacterInteractionPreviewCostsV1 costs{};
  CharacterInteractionPreviewAcceptanceV1 acceptance{};
  CharacterInteractionPreviewReadinessV1 readiness{};
};

enum class ReadCharacterInteractionPreviewResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kCharacterInteractionPreviewPrivateKeyV1 =
    "character_interaction_preview_v1";
inline constexpr std::string_view kCharacterInteractionPreviewGameVersionV1 =
    "1.19.0.6";
inline constexpr std::string_view
    kCharacterInteractionPreviewExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

inline constexpr std::uintptr_t
    kCharacterInteractionPreviewCharacterStorageSlotRvaV1 = 0x570C130;
inline constexpr std::uintptr_t
    kCharacterInteractionPreviewDatabaseGetterRvaV1 = 0x831890;
inline constexpr std::uintptr_t
    kCharacterInteractionPreviewStableKeyHashRvaV1 = 0x3B8B000;
inline constexpr std::uintptr_t
    kCharacterInteractionPreviewDefinitionLookupRvaV1 = 0x997930;
inline constexpr std::uintptr_t
    kCharacterInteractionPreviewConstructContextRvaV1 = 0x2C3EE50;
inline constexpr std::uintptr_t
    kCharacterInteractionPreviewRefreshContextRvaV1 = 0x2C40950;
inline constexpr std::uintptr_t
    kCharacterInteractionPreviewFinalizeContextRvaV1 = 0x2C40B20;
inline constexpr std::uintptr_t
    kCharacterInteractionPreviewCanSendRvaV1 = 0x2C43F00;
inline constexpr std::uintptr_t
    kCharacterInteractionPreviewCostEvaluatorRvaV1 = 0x2CDB7B0;
inline constexpr std::uintptr_t
    kCharacterInteractionPreviewAutoAcceptEvaluatorRvaV1 = 0x334C510;
inline constexpr std::uintptr_t
    kCharacterInteractionPreviewIntermediaryRawRvaV1 = 0x2C44220;
inline constexpr std::uintptr_t
    kCharacterInteractionPreviewRecipientRawRvaV1 = 0x2C44320;
inline constexpr std::uintptr_t
    kCharacterInteractionPreviewOuterFinalRvaV1 = 0x2C43B40;
inline constexpr std::uintptr_t
    kCharacterInteractionPreviewDestroyContextRvaV1 = 0x2C3F380;

struct CharacterInteractionPreviewFrameV1 {
  std::array<char, game::kCharacterInteractionPreviewSnapshotIdCapacityV1>
      snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;
  bool has_played_character = false;
  bool played_character_alive = false;
  std::int32_t played_character_id = -1;

  friend bool operator==(const CharacterInteractionPreviewFrameV1 &,
                         const CharacterInteractionPreviewFrameV1 &) =
      default;
};

struct CharacterInteractionPreviewEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  bool offline_fixture = false;
  std::uintptr_t character_storage_slot = 0;
  std::uintptr_t database_getter = 0;
  std::uintptr_t stable_key_hash = 0;
  std::uintptr_t definition_lookup = 0;
  std::uintptr_t construct_context = 0;
  std::uintptr_t refresh_context = 0;
  std::uintptr_t finalize_context = 0;
  std::uintptr_t can_send = 0;
  std::uintptr_t cost_evaluator = 0;
  std::uintptr_t auto_accept_evaluator = 0;
  std::uintptr_t intermediary_raw = 0;
  std::uintptr_t recipient_raw = 0;
  std::uintptr_t outer_final = 0;
  std::uintptr_t destroy_context = 0;
};

using CaptureCharacterInteractionPreviewFrameV1 = bool (*)(
    void *context, CharacterInteractionPreviewFrameV1 &output) noexcept;
using IsCharacterInteractionPreviewMainThreadV1 =
    bool (*)(void *context) noexcept;
using ReadCharacterInteractionPreviewMemoryV1 = bool (*)(
    void *context, std::uintptr_t address, void *output,
    std::size_t size) noexcept;
using InvokeCharacterInteractionPreviewStableHashV1 = bool (*)(
    void *context, std::uintptr_t function, void *database,
    std::string_view key, std::int32_t &output) noexcept;
using InvokeCharacterInteractionPreviewPointerGetterV1 = bool (*)(
    void *context, std::uintptr_t function, void *&output) noexcept;
using InvokeCharacterInteractionPreviewDefinitionLookupV1 = bool (*)(
    void *context, std::uintptr_t function, void *database,
    std::int32_t key_hash, void *&output) noexcept;
using InvokeCharacterInteractionPreviewConstructV1 = bool (*)(
    void *context, std::uintptr_t function, void *context_storage,
    void *definition, std::int32_t actor_character_id,
    std::int32_t recipient_character_id, void *&output) noexcept;
using InvokeCharacterInteractionPreviewContextStepV1 = bool (*)(
    void *context, std::uintptr_t function, void *interaction_context) noexcept;
using InvokeCharacterInteractionPreviewCanSendV1 = bool (*)(
    void *context, std::uintptr_t function, void *interaction_context,
    bool &output) noexcept;
using InvokeCharacterInteractionPreviewCostsV1 = bool (*)(
    void *context, std::uintptr_t function, void *interaction_context,
    std::array<std::int64_t, game::kCharacterInteractionPreviewCostCountV1>
        &output) noexcept;
using InvokeCharacterInteractionPreviewAcceptanceV1 = bool (*)(
    void *context, std::uintptr_t auto_accept_function,
    std::uintptr_t intermediary_raw_function,
    std::uintptr_t recipient_raw_function, std::uintptr_t outer_final_function,
    void *interaction_context,
    game::CharacterInteractionPreviewAcceptanceV1 &output) noexcept;

struct CharacterInteractionPreviewAccessV1 {
  // Native invokers are supplied only by a private application-main adapter.
  // invoke_refresh fixes the native refresh argument to true; invoke_costs
  // evaluates definition+0x38 against context+0x08; invoke_acceptance owns the
  // auto-accept/raw/outer ordering and returns no borrowed native pointer.
  void *context = nullptr;
  CaptureCharacterInteractionPreviewFrameV1 capture_frame = nullptr;
  IsCharacterInteractionPreviewMainThreadV1 is_main_thread = nullptr;
  ReadCharacterInteractionPreviewMemoryV1 read_memory = nullptr;
  InvokeCharacterInteractionPreviewStableHashV1 invoke_stable_hash = nullptr;
  InvokeCharacterInteractionPreviewPointerGetterV1 invoke_database_getter =
      nullptr;
  InvokeCharacterInteractionPreviewDefinitionLookupV1
      invoke_definition_lookup = nullptr;
  InvokeCharacterInteractionPreviewConstructV1 invoke_construct = nullptr;
  InvokeCharacterInteractionPreviewContextStepV1 invoke_refresh = nullptr;
  InvokeCharacterInteractionPreviewContextStepV1 invoke_finalize = nullptr;
  InvokeCharacterInteractionPreviewCanSendV1 invoke_can_send = nullptr;
  InvokeCharacterInteractionPreviewCostsV1 invoke_costs = nullptr;
  InvokeCharacterInteractionPreviewAcceptanceV1 invoke_acceptance = nullptr;
  InvokeCharacterInteractionPreviewContextStepV1 invoke_destroy = nullptr;
};

struct CharacterInteractionPreviewRequestV1 {
  std::string_view expected_snapshot_id{};
  std::uint64_t expected_public_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::int32_t expected_date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::int32_t recipient_character_id = -1;
  std::string_view interaction_key{};
};

CharacterInteractionPreviewEnvironmentV1
BindCharacterInteractionPreviewEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

game::ReadCharacterInteractionPreviewResultV1 ReadCharacterInteractionPreviewV1(
    const CharacterInteractionPreviewEnvironmentV1 &environment,
    const CharacterInteractionPreviewAccessV1 &access,
    const CharacterInteractionPreviewRequestV1 &request,
    game::CharacterInteractionPreviewV1 &output) noexcept;

std::string_view CharacterInteractionPreviewFailureKeyV1(
    game::CharacterInteractionPreviewFailureV1 reason) noexcept;

std::string SerializeCharacterInteractionPreviewV1(
    const game::CharacterInteractionPreviewV1 &preview);

} // namespace xar::ck3_11906
