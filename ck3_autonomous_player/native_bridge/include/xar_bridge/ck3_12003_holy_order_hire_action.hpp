#pragma once

#include "xar_bridge/ck3_12002_commands.hpp"
#include "xar_bridge/ck3_12003_player_holy_order_context.hpp"

#include <cstddef>

namespace xar::ck3_12003::religion::holy_order {

inline constexpr std::uintptr_t kHirePrimaryVtableRva = 0x476D9C8;
inline constexpr std::uintptr_t kHireSecondaryVtableRva = 0x476D998;
inline constexpr std::uintptr_t kHireCanExecuteRva = 0x2994810;
inline constexpr std::uint32_t kOrdinaryHireMode = 3;
inline constexpr std::uint32_t kHireChannelFlags = 0x0E;

// Inline source in CCC767..CCC803. The native clone 2995660..29956E2
// allocates 0x30, initializes both interfaces and returns one owning void*.
struct HireMode3Source {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t metadata_byte = 0;
  std::array<std::byte, 3> unused_prefix{};
  std::uint32_t metadata_word_0 = 0;
  std::uint32_t metadata_word_1 = 0;
  std::uint32_t metadata_word_2 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::uint32_t played_character_full_id = 0;
  std::uint32_t holy_order_full_id = 0;
  std::uint32_t mode = kOrdinaryHireMode;
  std::array<std::byte, 4> unused_tail{};
};
static_assert(sizeof(std::uintptr_t) == 8);
static_assert(sizeof(HireMode3Source) == 0x30);
static_assert(offsetof(HireMode3Source, metadata_byte) == 0x08);
static_assert(offsetof(HireMode3Source, metadata_word_0) == 0x0C);
static_assert(offsetof(HireMode3Source, metadata_word_1) == 0x10);
static_assert(offsetof(HireMode3Source, metadata_word_2) == 0x14);
static_assert(offsetof(HireMode3Source, secondary_vtable) == 0x18);
static_assert(offsetof(HireMode3Source, played_character_full_id) == 0x20);
static_assert(offsetof(HireMode3Source, holy_order_full_id) == 0x24);
static_assert(offsetof(HireMode3Source, mode) == 0x28);

using HireCommandValidator = bool (*)(const void *, void *);
struct HireActionBindings {
  bool enabled = false;
  Bindings context;
  ck3_12002::CommandBindings commands;
  std::uintptr_t primary_vtable = 0;
  std::uintptr_t secondary_vtable = 0;
  HireCommandValidator validate_source = nullptr;
};
enum class HireActionStatus { unavailable, rejected, submitted, already_hired };
struct HireActionResult {
  HireActionStatus status = HireActionStatus::unavailable;
  std::string unavailable_reason = "not_sampled";
  std::int32_t actor_character_id = -1;
  std::uint32_t holy_order_id = UINT32_MAX;
  bool holy_order_resolved = false;
  std::optional<std::uint32_t> prior_employer_character_id;
  Context prior_context;
  bool native_command_validation_observable = false;
  bool native_command_valid = false;
  bool command_submitted = false;
  bool verification_pending = false;
};
HireActionBindings BindHolyOrderHireActionImage12003(
    std::uintptr_t, std::string_view executable_sha256) noexcept;
// Actor comes from the admitted current-player envelope. Fixed ordinary mode3
// is the only action. No UI callback/camera call, no caller actor or war ID.
// Submission ACK cannot credit employer, resource payment or public CUnitID.
HireActionStatus ApplyHolyOrderHire12003(const HireActionBindings &,
    void *actual_player, std::int32_t player_id, std::uint32_t full_order_id,
    std::int32_t date_raw, std::uint64_t capture_epoch, HireActionResult &) noexcept;

} // namespace xar::ck3_12003::religion::holy_order
