#pragma once
#include "xar_bridge/ck3_12004_actual_loss_writer_journal.hpp"
#include "xar_bridge/ck3_12004_person_following_2922680.hpp"
#include <array>
#include <atomic>
#include <string>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kPersonTitleTailWrapperRva12004 = 0x291B3B0;
inline constexpr std::uintptr_t kPersonTitleTailReturnRva12004 = 0x291EBEF;
inline constexpr std::size_t kPersonTitleTailPatchBytes12004 = 15;
inline constexpr char kPersonTitleTailCaptureSchema12004[] =
    "xar.ck3.person-native-title-tail-capture-12004-v1";
using PersonTitleTailOriginal12004 = std::uintptr_t(__fastcall *)(void *, void *);

struct PersonTitleTailCaptureBindings12004 {
  PersonCarrierDirect12004Bindings memory{};
  void **game_state_slot = nullptr;
};
struct PersonTitleTailCapture12004DTO {
  std::string build_version;
  std::string executable_sha256;
  bool configured = false;
  bool capture_observed = false;
  bool ready = false;
  std::string reason;
  std::uint64_t capture_sequence = 0;
  std::optional<std::int32_t> capture_date_raw;
  std::optional<std::uint32_t> character_id;
  std::optional<std::uintptr_t> character_identity;
  std::optional<std::uintptr_t> model_identity;
  std::optional<std::uintptr_t> source_return_rva;
  std::optional<std::uintptr_t> inline_destination_identity;
  PersonFollowing2922680Pc prepared_pc;
  PersonFollowing2922680Pc model_aggregate_pc;
  std::int64_t weight_q100000 = 100000;
  bool actual_model_write_performed = false;
  bool full_helper_ready = false;
  friend bool operator==(const PersonTitleTailCapture12004DTO &,
                         const PersonTitleTailCapture12004DTO &) = default;
};
struct PersonTitleTailCaptureInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  PersonTitleTailCaptureBindings12004 bindings{};
  std::uintptr_t wrapper_target_override = 0;
  void *memory_context = nullptr;
  ActualLossWriterVirtualAllocV1 virtual_alloc_override = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free_override = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect_override = nullptr;
  ActualLossWriterFlushV1 flush_instruction_cache_override = nullptr;
};
struct PersonTitleTailCaptureDetourState12004 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{0};
  std::uintptr_t wrapper_target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kPersonTitleTailPatchBytes12004> original{};
  void *memory_context = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect = nullptr;
  ActualLossWriterFlushV1 flush_instruction_cache = nullptr;
};
PersonTitleTailCaptureBindings12004 BindPersonTitleTailCaptureImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool InstallPersonTitleTailCapture12004(
    PersonTitleTailCaptureDetourState12004 &state,
    const PersonTitleTailCaptureInstallEnvironment12004 &environment,
    std::string_view executable_sha256) noexcept;
bool UninstallPersonTitleTailCapture12004(
    PersonTitleTailCaptureDetourState12004 &state,
    bool primary_thread_suspended_proven) noexcept;
// Fixture calls the exact production observer on its declared synthetic graph.
// No wire input supplies a capture record or caller address.
bool InitializePersonTitleTailCaptureFixture12004(
    const PersonTitleTailCaptureBindings12004 &bindings,
    PersonTitleTailOriginal12004 original) noexcept;
void ObservePersonTitleTailCapture12004(
    std::uintptr_t model, std::uintptr_t source_pc,
    std::uintptr_t caller_return_address) noexcept;
PersonTitleTailCapture12004DTO ReadPersonTitleTailCaptureForCharacter12004(
    std::uintptr_t actual_character, std::uint32_t full_character_id) noexcept;
std::string SerializePersonTitleTailCapture12004(
    const PersonTitleTailCapture12004DTO &dto);
extern "C" __declspec(noinline) std::uintptr_t __fastcall
XarPersonTitleTailHook12004V1(void *model, void *source_pc) noexcept;
} // namespace xar::ck3_12004
