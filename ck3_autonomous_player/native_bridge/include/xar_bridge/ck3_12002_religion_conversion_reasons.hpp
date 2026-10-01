#pragma once

#include "xar_bridge/ck3_12002_religion_conversion_rite.hpp"

#include <optional>

namespace xar::ck3_12002::religion_conversion::reasons {

inline constexpr std::uintptr_t kNativeStringDestroyRva = 0x856050;
// Exact caller-owned native string initialized inline by 0x1516B20 and
// destroyed by 0x1516DD0. Its allocated storage belongs to the game runtime.
struct alignas(8) NativeReasonString {
  std::array<std::byte, 16> storage{};
  std::uint64_t size = 0;
  std::uint64_t capacity = 15;
};
static_assert(sizeof(NativeReasonString) == 0x20);
static_assert(offsetof(NativeReasonString, size) == 0x10);
static_assert(offsetof(NativeReasonString, capacity) == 0x18);
using NativeStringDestroy = void (*)(NativeReasonString *);

struct Bindings {
  religion_conversion_rite::Bindings rite;
  NativeStringDestroy destroy_string = nullptr;
};
enum class Failure {
  none,
  bindings_unavailable,
  played_character_unavailable,
  frame_not_paused,
  current_rite_unavailable,
  target_rite_unavailable,
  native_text_unavailable,
  state_changed,
};
struct Reasons {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::uint32_t current_rite_id = 0xFFFFFFFFU;
  std::uint32_t target_rite_id = 0xFFFFFFFFU;
  // The returned text is the native formatter's current-language output,
  // not a list of stable machine-readable reason codes.
  std::optional<bool> native_paid_validator_passes;
  std::optional<std::string> raw_native_text;
  // 0x1516B20 adds one LF if a nonempty formatter result lacks a final LF.
  std::optional<std::string> ui_blocker_text;
};
Bindings BindReligionConversionReasonsImage12002(std::uintptr_t module_base,
                                                std::string_view executable_sha256) noexcept;
// Existing paused application-main owner only. Constructs a local command
// value and invokes only the native validator with an owned reason string.
bool ReadPlayedReligionConversionReasons12002(const Bindings &,
    std::uint32_t target_rite_id, std::uint64_t capture_epoch, Reasons &) noexcept;
const char *ReligionConversionReasonsFailureKey(Failure) noexcept;
std::string SerializeReligionConversionReasons12002(const Reasons &);

} // namespace xar::ck3_12002::religion_conversion::reasons
