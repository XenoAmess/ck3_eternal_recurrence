// Include once after the release reader's closing namespace. Reuse its
// full-ID/custody helpers; no resolver, interaction context or command added.
#include "xar_bridge/ck3_12003_prisoner_native_kinship.hpp"
#include "xar_bridge/ck3_12002_family_obligations_break_penalty.hpp"

namespace xar::ck3_12003 {
namespace {
struct NativeKinshipSample12003 {
  NativeSample custody{};
  bool close_family = false;
  bool close_or_extended_family = false;
  friend bool operator==(const NativeKinshipSample12003 &,
      const NativeKinshipSample12003 &) = default;
};
bool ReadNativeKinshipSample12003(const PrisonerNativeKinshipBindings12003 &b,
    const PrisonerNativeKinshipAccess12003 &access, std::uint32_t jailer,
    std::uint32_t prisoner, NativeKinshipSample12003 &out) {
  PrisonerReleasePreviewBindings12003 custody_binding{};
  custody_binding.module_base = b.module_base;
  if (!ReadCustody(custody_binding, access, jailer, prisoner, out.custody)) return false;
  auto *subject = reinterpret_cast<void *>(out.custody.prisoner);
  auto *target = reinterpret_cast<void *>(out.custody.jailer);
  out.close_family = b.close_family(subject, target);
  out.close_or_extended_family = b.close_or_extended_family(subject, target);
  return true;
}
} // namespace
PrisonerNativeKinshipBindings12003 BindPrisonerNativeKinship12003(
    std::uintptr_t base, std::string_view actual_sha) noexcept {
  PrisonerNativeKinshipBindings12003 b{};
  if (!base || actual_sha != kExecutableSha256) return b;
  // Existing .3 reuse PASS; use constants without invoking the penalty binder.
  b.module_base = base;
  b.close_family = reinterpret_cast<PrisonerKinshipPredicate12003>(
      base + ck3_12002::family_break_penalty::kCloseFamilyRva);
  b.close_or_extended_family = reinterpret_cast<PrisonerKinshipPredicate12003>(
      base + ck3_12002::family_break_penalty::kCloseOrExtendedFamilyRva);
  b.enabled = true;
  return b;
}
bool ReadPrisonerNativeKinship12003(const PrisonerNativeKinshipBindings12003 &b,
    const PrisonerNativeKinshipAccess12003 &access, std::uint32_t jailer,
    std::uint32_t prisoner, std::uint32_t ordinal,
    PrisonerNativeKinship12003 &output) noexcept {
  output = {};
  try {
    const auto fail = [&output](std::string_view reason) {
      output.available = false;
      output.unavailable_reason.assign(reason);
      return false;
    };
    if (!b.enabled || !b.module_base || !b.close_family || !b.close_or_extended_family ||
        !access.capture_frame || !access.read_memory)
      return fail("native_bindings_unavailable");
    if (!access.current_thread_id ||
        access.current_thread_id != access.application_main_thread_id)
      return fail("application_main_thread_required");
    if (!jailer || !prisoner || jailer == prisoner ||
        ordinal >= bridge::kPlayerPrisonerMaximumRowsV1)
      return fail("invalid_roles_or_ordinal");
    bridge::PlayerPrisonerFrameV1 before{};
    if (!access.capture_frame(access.context, before)) return fail("frame_unavailable");
    if (!before.paused) return fail("not_paused");
    if (!before.map_ready || !before.played_character_alive ||
        !before.played_character_identity_round_trip || !before.public_revision ||
        !before.native_revision || !before.proof_epoch ||
        static_cast<std::uint32_t>(before.played_character_id) != jailer)
      return fail("player_unavailable");
    NativeKinshipSample12003 first{}, second{};
    if (!ReadNativeKinshipSample12003(b, access, jailer, prisoner, first) ||
        !ReadNativeKinshipSample12003(b, access, jailer, prisoner, second))
      return fail("custody_relation_unverified");
    if (first != second) return fail("native_sample_drift");
    bridge::PlayerPrisonerFrameV1 after{};
    if (!access.capture_frame(access.context, after)) return fail("frame_unavailable");
    if (before != after) return fail("frame_drift");
    output.frame = before;
    output.source_ordinal = ordinal;
    output.jailer_character_id = jailer;
    output.prisoner_character_id = prisoner;
    output.is_close_family_of_played_character = first.close_family;
    output.is_close_or_extended_family_of_played_character = first.close_or_extended_family;
    output.unavailable_reason.clear();
    output.available = true;
    return true;
  } catch (...) {
    output = {};
    output.unavailable_reason = "native_evaluation_unavailable";
    return false;
  }
}
} // namespace xar::ck3_12003
