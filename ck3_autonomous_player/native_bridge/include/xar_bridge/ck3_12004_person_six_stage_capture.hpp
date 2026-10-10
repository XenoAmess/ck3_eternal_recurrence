#pragma once
#include "xar_bridge/ck3_12004_actual_loss_writer_journal.hpp"
#include "xar_bridge/ck3_12004_person_following_2922680.hpp"
#include <array>
#include <atomic>
#include <span>
#include <string>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kPersonSixStageCountRva12004 = 0x2BA95C0;
inline constexpr std::uintptr_t kPersonSixStageReturnRva12004 = 0x291CEA9;
inline constexpr std::uintptr_t kPersonSixStageAppendRva12004 = 0x2438830;
inline constexpr std::uintptr_t kPersonSixStageFirstAppendReturnRva12004 = 0x291CEC9;
inline constexpr std::uintptr_t kPersonSixStageSecondAppendReturnRva12004 = 0x291CEFB;
inline constexpr std::size_t kPersonSixStagePatchBytes12004 = 16;
// The append anchor is supplied from the held whole-instruction prologue.
inline constexpr std::size_t kPersonSixStageAppendPatchBytes12004 = 15;
inline constexpr std::size_t kPersonSixStageCount12004 = 6;
inline constexpr char kPersonSixStageCaptureSchema12004[] =
    "xar.ck3.person-native-six-stage-capture-12004-v1";
inline constexpr char kPersonSixStageQuerySchema12004[] =
    "xar.ck3.person-native-six-stage-query-12004-v1";
using PersonSixStageOriginal12004 =
    std::uintptr_t(__fastcall *)(void *, void *, std::uint32_t);
using PersonSixStageAppendOriginal12004 =
    std::uintptr_t(__fastcall *)(void *, void *, std::int64_t);

struct PersonSixStageCaptureBindings12004 {
  PersonCarrierDirect12004Bindings memory{};
  void **game_state_slot = nullptr;
};
struct PersonSixStageCaptureStage12004 {
  std::uint32_t index = 0;
  bool observed = false;
  std::optional<std::int32_t> raw_count_i32;
  bool first_append_observed = false;
  bool second_append_observed = false;
  PersonFollowing2922680Pc first_pc;
  PersonFollowing2922680Pc second_pc;
  friend bool operator==(const PersonSixStageCaptureStage12004 &,
                         const PersonSixStageCaptureStage12004 &) = default;
};
struct PersonSixStagePreAggregate12004 {
  bool observed = false;
  PersonFollowing2922680Pc pc;
  friend bool operator==(const PersonSixStagePreAggregate12004 &,
                         const PersonSixStagePreAggregate12004 &) = default;
};
struct PersonSixStageBasePointInputs12004 {
  std::array<bool, kPersonSixStageCount12004> observed{};
  std::array<std::optional<std::int32_t>, kPersonSixStageCount12004> values_i32{};
  bool ready = false;
  std::string reason = "base_point_unobserved";
  friend bool operator==(const PersonSixStageBasePointInputs12004 &,
                         const PersonSixStageBasePointInputs12004 &) = default;
};
struct PersonSixStagePietyCategory12004 {
  bool observed = false;
  bool ready = false;
  std::string reason = "piety_category_unobserved";
  std::optional<std::uint16_t> property_key_u16;
  std::optional<std::uintptr_t> extension_identity;
  std::optional<std::int64_t> score_q64;
  std::optional<std::int32_t> cap_i32;
  std::optional<std::int32_t> threshold_count_i32;
  std::vector<std::int64_t> thresholds_used_q64;
  std::optional<std::int32_t> category_i32;
  friend bool operator==(const PersonSixStagePietyCategory12004 &,
                         const PersonSixStagePietyCategory12004 &) = default;
};
struct PersonSixStageClassifiedPietyRow12004 {
  std::uint32_t native_index = 0;
  bool ready = false;
  std::string reason;
  std::optional<std::uintptr_t> pc_identity;
  std::optional<std::int32_t> pc_count_i32;
  std::string lookup_selection = "unavailable";
  std::optional<std::uint32_t> selected_index_u32;
  std::optional<std::int64_t> raw_value_q64;
  std::optional<std::int64_t> scale_q64;
  friend bool operator==(const PersonSixStageClassifiedPietyRow12004 &,
                         const PersonSixStageClassifiedPietyRow12004 &) = default;
};
struct PersonSixStageClassifiedPietyStage12004 {
  std::uint32_t index = 0;
  bool observed = false;
  bool ready = false;
  std::string reason = "classified_piety_unobserved";
  std::optional<std::uint16_t> property_key_u16;
  std::optional<std::int32_t> row_count_i32;
  std::optional<std::uintptr_t> row_array_identity;
  std::vector<PersonSixStageClassifiedPietyRow12004> rows;
  friend bool operator==(const PersonSixStageClassifiedPietyStage12004 &,
                         const PersonSixStageClassifiedPietyStage12004 &) = default;
};
struct PersonPreparationModel12004 {
  bool observed = false;
  bool ready = false;
  std::string reason;
  std::optional<std::uintptr_t> model_identity;
  std::optional<std::uintptr_t> owner_character_identity;
  std::optional<std::uint32_t> owner_character_id;
  std::optional<bool> owner_matches_capture;
  friend bool operator==(const PersonPreparationModel12004 &,
                         const PersonPreparationModel12004 &) = default;
};
struct PersonSixStageCapture12004DTO {
  std::string build_version;
  std::string executable_sha256;
  bool configured = false;
  bool capture_observed = false;
  bool capture_complete = false;
  bool ready = false;
  bool raw_counts_ready = false;
  PersonSixStageBasePointInputs12004 base_point_inputs;
  std::array<PersonSixStagePietyCategory12004, kPersonSixStageCount12004>
      piety_category_inputs{};
  std::array<PersonSixStageClassifiedPietyStage12004, kPersonSixStageCount12004>
      classified_piety_inputs{};
  PersonPreparationModel12004 preparation_model;
  PersonSixStagePreAggregate12004 pre_six_aggregate;
  PersonSixStagePreAggregate12004 post_six_aggregate;
  bool aggregate_postimage_inputs_ready = false;
  bool aggregate_postimage_comparison_ready = false;
  std::string reason;
  std::uint64_t capture_sequence = 0;
  std::optional<std::int32_t> capture_date_raw;
  std::optional<std::uint32_t> capture_thread_id;
  std::optional<std::uint32_t> query_thread_id;
  std::optional<std::uint32_t> character_id;
  std::optional<std::uintptr_t> character_identity;
  std::optional<std::uintptr_t> context_identity;
  std::optional<std::uintptr_t> source_return_rva;
  std::array<PersonSixStageCaptureStage12004, kPersonSixStageCount12004> stages{};
  bool actual_model_write_performed = false;
  bool full_helper_ready = false;
  bool historical_capture = true;
  friend bool operator==(const PersonSixStageCapture12004DTO &,
                         const PersonSixStageCapture12004DTO &) = default;
};
struct PersonSixStageQuery12004DTO {
  std::uint64_t snapshot_revision = 0;
  std::int64_t observed_date_raw = 0;
  std::vector<PersonSixStageCapture12004DTO> character_captures;
  friend bool operator==(const PersonSixStageQuery12004DTO &,
                         const PersonSixStageQuery12004DTO &) = default;
};
struct PersonSixStageCaptureInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  PersonSixStageCaptureBindings12004 bindings{};
  std::uintptr_t count_target_override = 0;
  std::uintptr_t append_target_override = 0;
  void *memory_context = nullptr;
  ActualLossWriterVirtualAllocV1 virtual_alloc_override = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free_override = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect_override = nullptr;
  ActualLossWriterFlushV1 flush_instruction_cache_override = nullptr;
};
struct PersonSixStageCaptureDetourState12004 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{0};
  std::uintptr_t count_target = 0;
  std::uintptr_t append_target = 0;
  void *count_trampoline = nullptr;
  void *append_trampoline = nullptr;
  std::array<std::uint8_t, kPersonSixStagePatchBytes12004> original{};
  std::array<std::uint8_t, kPersonSixStageAppendPatchBytes12004> append_original{};
  void *memory_context = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect = nullptr;
  ActualLossWriterFlushV1 flush_instruction_cache = nullptr;
};
PersonSixStageCaptureBindings12004 BindPersonSixStageCaptureImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool InstallPersonSixStageCapture12004(
    PersonSixStageCaptureDetourState12004 &state,
    const PersonSixStageCaptureInstallEnvironment12004 &environment,
    std::string_view executable_sha256) noexcept;
bool UninstallPersonSixStageCapture12004(
    PersonSixStageCaptureDetourState12004 &state,
    bool primary_thread_suspended_proven) noexcept;
bool InitializePersonSixStageCaptureFixture12004(
    const PersonSixStageCaptureBindings12004 &bindings,
    PersonSixStageOriginal12004 original,
    PersonSixStageAppendOriginal12004 append_original) noexcept;
// Shared production dispatch for the natural hook and its connected fixture.
// Owns context+0x68 before exact stage0, calls original once, then records result.
std::uintptr_t InvokePersonSixStageCapture12004(
    void *character, void *context, std::uint32_t index,
    std::uintptr_t caller_return_address) noexcept;
// Called after the natural callback has returned and before either append.
// Copies source data only; it never replays the callback or writes its context.
void ObservePersonSixStageCapture12004(
    std::uintptr_t character, std::uintptr_t context, std::uint32_t index,
    std::uintptr_t raw_return_bits,
    std::uintptr_t caller_return_address) noexcept;
void ObservePersonSixStageAppend12004(
    std::uintptr_t context, std::uintptr_t source_pc,
    std::int64_t weight_q100000,
    std::uintptr_t caller_return_address) noexcept;
// The paused AppThread query closes a finished natural capture on that same
// thread. Context zero selects this Character/full-ID's captured context.
void CompletePersonSixStageCapture12004(
    std::uintptr_t actual_character, std::uint32_t full_character_id,
    std::uintptr_t actual_context = 0) noexcept;
PersonSixStageCapture12004DTO ReadPersonSixStageCaptureForCharacter12004(
    std::uintptr_t actual_character, std::uint32_t full_character_id) noexcept;
// Same owned PC copier used by the historical capture, for an actual consumed
// context. This does not finish, mutate or relabel any historical capture.
PersonFollowing2922680Pc CopyPersonSixStageAggregatePc12004(
    std::uintptr_t actual_pc) noexcept;
std::string SerializePersonSixStageCapture12004(
    const PersonSixStageCapture12004DTO &dto);
// Called inside the validated paused AppThread query boundary. Each full ID is
// resolved through the qualified Character storage before any owned lookup.
PersonSixStageQuery12004DTO CollectPersonSixStageQuery12004(
    void **character_storage_slot, std::span<const std::int32_t> requested_ids,
    std::uint64_t snapshot_revision, std::int64_t observed_date_raw) noexcept;
std::string SerializePersonSixStageQuery12004(
    const PersonSixStageQuery12004DTO &dto);
extern "C" __declspec(noinline) std::uintptr_t __fastcall
XarPersonSixStageHook12004V1(void *character, void *context,
                            std::uint32_t index) noexcept;
extern "C" __declspec(noinline) std::uintptr_t __fastcall
XarPersonSixStageAppendHook12004V1(void *context, void *source_pc,
                                  std::int64_t weight_q100000) noexcept;
} // namespace xar::ck3_12004
