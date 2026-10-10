#pragma once

#include "xar_bridge/player_lifestyle_window_candidates_v1.hpp"
#include "xar_bridge/lifestyle_trigger_frontier_types_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kStockPerkLegalityKeyV1 =
    "g2_player_lifestyle_stock_perk_legality_v1";
inline constexpr std::string_view kStockPerkLegalityExeSha256V1 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kStockPerkLegalityTargetV1 =
    "cutting_corners_perk";
inline constexpr std::string_view kStockPerkLegalityFollowupTargetV1 =
    "professional_workforce_perk";
inline constexpr std::string_view kStockPerkLegalityNextTargetV1 =
    "centralization_perk";
inline constexpr std::string_view kStockPerkLegalityCollectTaxesTargetV1 =
    "tax_man_perk";
inline constexpr std::string_view kStockPerkLegalityLifestyleV1 =
    "stewardship_lifestyle";
inline constexpr std::string_view kDiplomacyThoughtfulPerkV1 =
    "thoughtful_perk";
inline constexpr std::string_view kDiplomacyThoughtfulLifestyleV1 =
    "diplomacy_lifestyle";
inline constexpr std::string_view kMartialServeTheCrownPerkV1 =
    "serve_the_crown_perk";
inline constexpr std::string_view kMartialPerkLifestyleV1 =
    "martial_lifestyle";

struct StockPerkLegalityFrameV1 {
  std::array<char, 64> episode_run_id{};
  std::array<char, 48> snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t played_character_id = 0xFFFFFFFFU;
  std::uintptr_t played_character = 0;
  bool paused = false;
  bool map_ready = false;
  bool played_character_alive = false;
  bool storage_round_trip = false;

  friend bool operator==(const StockPerkLegalityFrameV1 &,
                         const StockPerkLegalityFrameV1 &) = default;
};

struct StockPerkLegalityPlayerStateV1 {
  game::PlayerLifestyleWindowStableKeyV1 target_lifestyle_key{};
  std::int64_t target_xp_total_raw = -1;
  std::int64_t target_xp_within_level_raw = -1;
  std::int32_t target_xp_per_level = -1;
  std::int32_t unspent_perk_points = -1;
  std::int32_t used_perk_points = -1;
  bool owned_perk_state_known = false;
  bool target_perk_owned = false;

  friend bool operator==(const StockPerkLegalityPlayerStateV1 &,
                         const StockPerkLegalityPlayerStateV1 &) = default;
};

using StockPerkCaptureFrameV1 = bool (*)(void *,
                                         StockPerkLegalityFrameV1 &) noexcept;
using StockPerkReadMemoryV1 = bool (*)(void *, std::uintptr_t, void *,
                                       std::size_t) noexcept;
using StockPerkReadPlayerStateV1 = bool (*)(
    void *, const StockPerkLegalityFrameV1 &, std::uintptr_t target_lifestyle,
    StockPerkLegalityPlayerStateV1 &) noexcept;
using StockPerkReadTargetPlayerStateV1 = bool (*)(
    void *, const StockPerkLegalityFrameV1 &, std::uintptr_t target_lifestyle,
    std::string_view target_key, StockPerkLegalityPlayerStateV1 &) noexcept;
using StockPerkProbeMainThreadV1 = bool (*)(void *) noexcept;
using StockPerkGetDatabaseV1 = void *(*)();
using StockPerkValidateCommandV1 = bool (*)(void *, void *);

struct StockPerkLegalityEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_exe_sha256{};
  std::uintptr_t module_base = 0;
  bool offline_fixture = false;
  StockPerkGetDatabaseV1 get_character_perk_database = nullptr;
  StockPerkValidateCommandV1 validate_perk_command = nullptr;
};

struct StockPerkLegalitySourceQueryMetadataV1 {
  std::optional<std::uint64_t> frame_identity{};
  std::optional<std::uint64_t> query_sequence{};
  std::optional<bool> mailbox_before_accepted{}, mailbox_after_accepted{};
  std::optional<std::uint32_t> module_image_size{}, module_time_date_stamp{};
  bool caller_snapshot_confirmed = false;
  friend bool operator==(const StockPerkLegalitySourceQueryMetadataV1 &,
                         const StockPerkLegalitySourceQueryMetadataV1 &) = default;
};

struct StockPerkLegalitySourceReadFrameV1 {
  std::string executable_sha256;
  std::uintptr_t module_base = 0;
  std::string snapshot_identity;
  std::optional<std::uint64_t> frame_identity{};
  std::optional<std::uint64_t> query_sequence{};
  std::optional<bool> mailbox_before_accepted{}, mailbox_after_accepted{};
  std::optional<std::uint32_t> module_image_size{}, module_time_date_stamp{};
  std::uint64_t public_revision = 0, native_revision = 0, proof_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t played_character_id = 0xFFFFFFFFU;
  std::string caller_domain;
  bool caller_snapshot_confirmed = false;
  friend bool operator==(const StockPerkLegalitySourceReadFrameV1 &,
                         const StockPerkLegalitySourceReadFrameV1 &) = default;
};

struct StockPerkLegalitySourceInputsV1 {
  std::uintptr_t command_identity = 0;
  std::optional<std::uintptr_t> registry_identity{};
  std::optional<std::uint32_t> requested_full_character_id_u32{};
  std::optional<std::uint32_t> registry_capacity_u32{};
  std::optional<std::uintptr_t> indexed_character_identity{};
  std::optional<std::uint32_t> indexed_character_full_id_u32{};
  std::optional<bool> used_fallback{};
  std::optional<std::uintptr_t> selected_character_identity{};
  std::optional<std::uint32_t> selected_character_magic_u32{};
  std::optional<std::uint32_t> selected_character_full_id_u32{};
  std::optional<std::uint64_t> selected_character_field_1d0_u64{};
  std::optional<std::uintptr_t> selected_perk_identity{};
  std::optional<std::uint32_t> selected_perk_magic_u32{};
  std::optional<bool> prefix_admitted{};
  std::string unavailable_reason;
  friend bool operator==(const StockPerkLegalitySourceInputsV1 &,
                         const StockPerkLegalitySourceInputsV1 &) = default;
};

struct StockPerkLegalitySourceTailV1 {
  std::optional<bool> value{};
  std::string unavailable_reason;
  friend bool operator==(const StockPerkLegalitySourceTailV1 &,
                         const StockPerkLegalitySourceTailV1 &) = default;
};

struct StockPerkLegalitySourceTruthTraceV1 {
  std::uintptr_t selected_perk_identity = 0;
  std::optional<std::uintptr_t> compiled_trigger_receiver_identity{};
  std::optional<std::uint16_t> context_root_word{};
  std::optional<std::uint64_t> context_full_id_payload{};
  std::optional<std::uint8_t> evaluation_flag_raw_u8{};
  std::optional<std::uintptr_t> trigger_vtable_raw{};
  std::optional<std::uintptr_t> root_kind_getter_slot58_raw{};
  std::optional<std::uintptr_t> root_mask_getter_slot60_raw{};
  std::optional<std::uintptr_t> final_evaluator_slotc8_raw{};
  std::optional<std::uint8_t> source_projected_returned_raw_u8{};
  std::optional<bool> value{};
  bool context_projection_available = false;
  bool copied_frame_ready = false;
  bool input_leaf_ready = false;
  bool child_source_value_ready = false;
  bool native_callback_executed = false;
  bool actual_trigger_evaluation_observed = false;
  std::string unavailable_reason;
  friend bool operator==(const StockPerkLegalitySourceTruthTraceV1 &,
                         const StockPerkLegalitySourceTruthTraceV1 &) = default;
};

// Copied current-query child observations. Native parent legality is independent.
// Copied pointer identities never authorize later native use of their objects.
struct StockPerkLegalitySourcePacketV1 {
  StockPerkLegalitySourceReadFrameV1 read_frame{};
  std::string target_key;
  std::optional<std::uintptr_t> current_thread_tls_array_identity{};
  StockPerkLegalitySourceInputsV1 inputs{};
  std::optional<StockPerkLegalitySourceTailV1> tail{};
  std::optional<StockPerkLegalitySourceTruthTraceV1> truth_trace{};
  std::optional<bool> value{};
  std::string unavailable_reason;
  std::optional<bool> native_can_select_before{};
  std::optional<bool> native_can_select_after{};
  bool repeated_source_match = false;
  friend bool operator==(const StockPerkLegalitySourcePacketV1 &,
                         const StockPerkLegalitySourcePacketV1 &) = default;
};

using StockPerkCaptureSourceQueryMetadataV1 = bool (*)(
    void *, StockPerkLegalitySourceQueryMetadataV1 &) noexcept;
using StockPerkCaptureSourceTlsArrayV1 = bool (*)(void *, std::uintptr_t &) noexcept;

// Successor copied targets from the live existing command. Returned values are
// owned by the separate lane proofs, never inferred from these raw identities.
struct StockPerkLegalityRawTargetsSourceV1 {
  std::string capture_scope = "unavailable";
  StockPerkLegalitySourceReadFrameV1 read_frame;
  std::string target_key;
  std::uintptr_t command_identity = 0, selected_perk_identity = 0;
  std::uint32_t requested_full_character_id = 0xFFFFFFFFU;
  std::optional<std::uintptr_t> selected_character_identity;
  std::optional<std::uint32_t> selected_character_full_id;
  std::optional<std::uintptr_t> receiver_identity, vtable_identity, vtable_rva;
  std::optional<std::uintptr_t> slot58_identity, slot60_identity, slotc8_identity;
  std::optional<std::uintptr_t> slot58_target_identity, slot60_target_identity,
      slotc8_target_identity;
  std::optional<std::uintptr_t> slot58_target_rva, slot60_target_rva,
      slotc8_target_rva;
  std::string vtable_unavailable_reason, slot58_unavailable_reason,
      slot60_unavailable_reason, slotc8_unavailable_reason;
  std::optional<std::uint16_t> source_context_root_word;
  std::optional<std::uint64_t> source_context_full_id_payload;
  bool context_is_source_projection = false;
  std::optional<xar::ck3_12004::TriggerScopeTableProviderRaw3795A6012004>
      descriptor_provider;
  bool raw_slots_copied = false, caller_before_after_confirmed = false,
      repeated_raw_match = false;
  std::optional<bool> native_before, native_after;
  std::string unavailable_reason;
};

struct StockPerkLegalityAccessV1 {
  void *context = nullptr;
  StockPerkProbeMainThreadV1 is_application_main_thread = nullptr;
  StockPerkCaptureFrameV1 capture_frame = nullptr;
  StockPerkReadMemoryV1 read_memory = nullptr;
  StockPerkReadPlayerStateV1 read_player_state = nullptr;
  StockPerkReadTargetPlayerStateV1 read_target_player_state = nullptr;
  // Optional actual-query carriers; absent inputs only limit the child source.
  StockPerkCaptureSourceQueryMetadataV1 capture_source_query_metadata = nullptr;
  StockPerkCaptureSourceTlsArrayV1 capture_source_tls_array = nullptr;
};

enum class StockPerkLegalityStatusV1 : std::uint32_t {
  unavailable_exact_build = 0,
  unavailable_binding,
  unavailable_frame,
  unavailable_player,
  unavailable_database,
  unavailable_candidate,
  unavailable_state,
  unavailable_validator,
  unavailable_drift,
  observed_native_illegal,
  observed_native_legal,
};

struct StockPerkLegalityResultV1 {
  StockPerkLegalityStatusV1 status =
      StockPerkLegalityStatusV1::unavailable_binding;
  StockPerkLegalityFrameV1 frame{};
  game::PlayerLifestyleWindowStableKeyV1 target_key{};
  game::PlayerLifestyleWindowStableKeyV1 lifestyle_key{};
  std::int32_t observed_unspent_points = -1;
  std::int32_t observed_used_points = -1;
  std::int64_t observed_target_xp_total_raw = -1;
  std::int64_t observed_target_xp_within_level_raw = -1;
  std::int32_t observed_target_xp_per_level = -1;
  bool observed_target_owned = false;
  std::int32_t scanned_database_rows = -1;
  bool validator_invoked_twice = false;
  // Valid only for the captured application-main transaction. The private
  // formal wire may use it for one immediate revalidation/submit; it must
  // never be retained across another capture or published over JSON.
  std::uintptr_t target_definition = 0;
  std::optional<StockPerkLegalitySourcePacketV1> source_packet{};
  std::optional<StockPerkLegalityRawTargetsSourceV1> raw_targets_source{};
  std::optional<xar::ck3_12004::LifestyleTriggerFrontierPacket12004> trigger_frontier_source{};
};

StockPerkLegalityEnvironmentV1 BindStockPerkLegalityEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_exe_sha256) noexcept;

// Private perk-only source. It evaluates a stock command twice, never submits
// it and never reads, opens or binds the lifestyle GUI window. Unknown input
// stays unavailable; only two matching exact native booleans are observations.
StockPerkLegalityResultV1 ReadStockPerkLegalityV1(
    const StockPerkLegalityEnvironmentV1 &environment,
    const StockPerkLegalityAccessV1 &access) noexcept;

// Exact policy targets share the private observation and typed submit contract.
// A newly admitted target still needs its own fresh same-frame native verdict.
StockPerkLegalityResultV1 ReadStockPerkLegalityV1(
    const StockPerkLegalityEnvironmentV1 &environment,
    const StockPerkLegalityAccessV1 &access,
    std::string_view target_key) noexcept;

std::string_view StockPerkLegalityStatusKeyV1(
    StockPerkLegalityStatusV1 status) noexcept;

} // namespace xar::ck3_11906
