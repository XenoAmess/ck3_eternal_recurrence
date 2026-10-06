#include "xar_bridge/ck3_12004_religion_parameter_bindings.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"

namespace xar::ck3_12004::religion {
namespace {
namespace doctrine = ck3_12002::religion::doctrine12002;

// The complete actual .4 FaithHeresyThreshold leaf consumes this scalar.
// Its main-Rite adjustment at +7F8 is independent of the current Rite.
constexpr std::uintptr_t kFaithHeresyThresholdDefineRva12004 = 0x5C68D88;
constexpr std::uintptr_t kPersonalParameterCollectionGetterRva12004 = 0x28BD070;

// Actual .4 constructor/consumer operands close these shared software layouts.
// The proof is the finite parameter source packet, not the legacy type name.
static_assert(doctrine::kRiteNumericSpecialOffset +
    doctrine::kNumericMinimumFervorOffset == 0x7DC);
static_assert(doctrine::kRiteNumericSpecialOffset +
    doctrine::kNumericHolySiteGainOffset == 0x7E0);
static_assert(doctrine::kRiteNumericSpecialOffset +
    doctrine::kNumericFervorGainOffset == 0x7E8);
static_assert(doctrine::kRiteNumericSpecialOffset +
    doctrine::kNumericHeresyProtectionOffset == 0x7F0);
static_assert(doctrine::kRiteNumericSpecialOffset +
    doctrine::kNumericHeresyThresholdOffset == 0x7F8);
static_assert(doctrine::kPersonalParameterCharacterExtensionOffset == 0x1C8);
static_assert(doctrine::kPersonalParameterOwnedTenetsOffset == 0x88);
static_assert(doctrine::kPersonalParameterDefinitionSetOffset == 0x740);
static_assert(doctrine::kPersonalParameterSupportedSetOffset == 0xF20);

bool Admitted(std::uintptr_t base, std::string_view sha) noexcept {
  return base != 0 && sha == ck3_12004::kExecutableSha256;
}

enum class FrameFailure { none, bindings, played, paused };
FrameFailure SelectPlayedFrame(const ContextBindings &b,
    CoreSnapshotPrefix &frame) noexcept {
  if (!b.enabled || !b.core.enabled) return FrameFailure::bindings;
#if defined(_WIN32) && defined(_MSC_VER)
  __try {
#endif
    if (!ck3_12004::ReadCoreSnapshot(b.core, frame) || !frame.map_ready ||
        !frame.has_played_character || !frame.played_character_alive ||
        !ck3_12004::ResolveCoreCharacter(b.core, frame.played_character_id))
      return FrameFailure::played;
    return frame.clock.paused ? FrameFailure::none : FrameFailure::paused;
#if defined(_WIN32) && defined(_MSC_VER)
  } __except (1) { return FrameFailure::played; }
#endif
}

const char *FrameReason(FrameFailure failure) noexcept {
  return failure == FrameFailure::bindings ? "bindings_unavailable" :
      failure == FrameFailure::paused ? "frame_not_paused" :
      "played_character_unavailable";
}

template<class Context> void Stamp(Context &out, std::uint64_t epoch,
    const CoreSnapshotPrefix &frame) noexcept {
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id =
      static_cast<decltype(out.played_character_id)>(frame.played_character_id);
}
} // namespace

NumericSpecialBindings BindNumericSpecialParametersImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  return {Admitted(base, sha)};
}

FaithNumericFinalBindings BindFaithNumericFinalImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  if (!Admitted(base, sha)) return {};
  return {true,
      reinterpret_cast<doctrine::FaithHeresyThresholdGetter>(
          base + profile::kFaithHeresyThresholdRva),
      reinterpret_cast<const std::int64_t *>(
          base + kFaithHeresyThresholdDefineRva12004)};
}

PersonalParameterBindings BindPersonalParametersImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  if (!Admitted(base, sha)) return {};
  return {true,
      reinterpret_cast<const void *const *>(base + profile::kTenetDatabaseSlotRva),
      reinterpret_cast<doctrine::PersonalParameterCollectionGetter>(
          base + kPersonalParameterCollectionGetterRva12004),
      reinterpret_cast<doctrine::BooleanParameterMembership>(
          base + profile::kBooleanParameterMembershipRva),
      reinterpret_cast<doctrine::ParameterTokenKey>(
          base + profile::kParameterTokenKeyRva)};
}

bool ReadPlayedNumericSpecialParameters12004(const ContextBindings &b,
    const NumericSpecialBindings &numeric, std::uint64_t epoch,
    NumericSpecialContext &out) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto failure = SelectPlayedFrame(b, frame);
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = FrameReason(failure);
    return false;
  }
  const bool read = doctrine::ReadPlayedNumericSpecialParameters12002(
      b, numeric, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedFaithNumericFinal12004(const ContextBindings &b,
    const NumericSpecialBindings &numeric, const FaithNumericFinalBindings &final,
    std::uint64_t epoch, FaithNumericFinalContext &out) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto failure = SelectPlayedFrame(b, frame);
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = FrameReason(failure);
    return false;
  }
  const bool read = doctrine::ReadPlayedFaithNumericFinal12002(
      b, numeric, final, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedPersonalParameters12004(const ContextBindings &b,
    const PersonalParameterBindings &parameters, std::uint64_t epoch,
    PersonalParameterContext &out) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto failure = SelectPlayedFrame(b, frame);
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = FrameReason(failure);
    return false;
  }
  const bool read = doctrine::ReadPlayedPersonalParameters12002(
      b, parameters, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

std::string SerializeFaithNumericFinal12004(const FaithNumericFinalContext &out) {
  auto result = game::Render12004BuildIdentity(
      doctrine::SerializeFaithNumericFinal12002(out),
      game::Ck3_12004AdapterDescriptor());
  constexpr std::string_view old_getter = "\"native_getter_rva\":\"0x2440920\"";
  constexpr std::string_view actual_getter = "\"native_getter_rva\":\"0x2440900\"";
  const auto position = result.find(old_getter);
  if (position != std::string::npos)
    result.replace(position, old_getter.size(), actual_getter);
  return result;
}

} // namespace xar::ck3_12004::religion
