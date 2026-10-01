#pragma once

#include "xar_bridge/ck3_12002_sway_state.hpp"

#include <string>

namespace xar::ck3_12002 {

// Native current roll input, Q100000 percentage points. The returned pointer
// is the caller's output buffer; this getter does not report a completed roll.
using SwayCompletionSuccessChance12002 = std::int64_t *(*)(
    const void *scheme, std::int64_t *output);
inline constexpr std::uintptr_t kSwayCompletionSuccessChanceRva12002 = 0x2A4A400;
inline constexpr std::int64_t kSwayCompletionSuccessChanceScale12002 = 100000;
using SwayCompletionCanContinue12002 = bool (*)(const void *scheme,
    std::int32_t mode, std::int32_t validate_linked_activity);
inline constexpr std::uintptr_t kSwayCompletionCanContinueRva12002 = 0x2A4FFA0;

struct SwayCompletionBindings12002 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  CoreBindings core{};
  SwayCompletionSuccessChance12002 success_chance = nullptr;
  SwayCompletionCanContinue12002 can_continue = nullptr;
};

SwayCompletionBindings12002 BindSwayCompletionImage12002(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

struct SwayCompletionRequestV1 {
  std::uint64_t expected_revision = 0;
  std::int32_t actor_character_id = -1;
  std::int32_t target_character_id = -1;
  std::uint32_t scheme_id = 0xFFFFFFFFu;
  friend bool operator==(const SwayCompletionRequestV1 &,
                         const SwayCompletionRequestV1 &) = default;
};

struct SwayCompletionStateV1 {
  bool available = false;
  std::string unavailable_reason;
  SwayCompletionRequestV1 request{};
  std::int32_t date_raw = 0;
  bool instance_source_observed = false;
  bool instance_present = false;
  bool storage_slot_reused = false;
  bool exact_instance_join_ready = false;
  std::uint32_t scheme_instance_generation = 0;
  // The native terminal path clears this owner to FFFFFFFF. It is an observed
  // raw marker, rather than an assertion that the former owner is still stored.
  std::uint32_t native_owner_raw = 0xFFFFFFFFu;
  bool owner_matches_actor = false;
  bool owner_cleared = false;
  bool native_status_observed = false;
  std::int32_t native_status_raw = 2;
  std::string native_status_key = "unobserved";
  // Native status 1 is named "invalidated" and is also used by manual cancel
  // and authored end_scheme. It proves termination, but cannot establish cause.
  bool native_terminal_state_observed = false;
  bool native_success_chance_observed = false;
  std::int64_t native_success_chance_raw = 0;
  std::int64_t native_success_chance_scale = kSwayCompletionSuccessChanceScale12002;
  // Complete current native validity, with the same mode/activity arguments
  // as manager PreUpdate. A false result is not a historical ending reason.
  bool native_can_continue_observed = false;
  bool native_can_continue = false;
  bool terminal_cause_observed = false;
  std::string terminal_cause = "unknown";
  friend bool operator==(const SwayCompletionStateV1 &,
                         const SwayCompletionStateV1 &) = default;
};

// Readonly, one paused application-owner-thread query. The current native row
// remains observable only until manager purge. Its absence is published as an
// absence fact and never substituted for a completed or cancelled result.
bool ReadSwayCompletion12002(const SwayCompletionBindings12002 &bindings,
    const SwayCompletionRequestV1 &request, SwayCompletionStateV1 &output) noexcept;

} // namespace xar::ck3_12002
