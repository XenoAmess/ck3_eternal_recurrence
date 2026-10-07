#include "xar_bridge/ck3_12003_title_properties_leaf.hpp"
#include "xar_bridge/ck3_12004_confucian_title_profile.hpp"
#include "xar_bridge/ck3_12004_title_holder.hpp"

#include <bit>
#include <cstring>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::title_properties {
namespace {

template <typename T>
bool Load(const void *object, std::size_t offset, T &value) noexcept {
  if (object == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
                sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

void *Resolve(const Bindings &bindings, std::uint32_t id) noexcept {
  if (id == UINT32_MAX) return nullptr;
#if defined(_MSC_VER)
  __try {
#endif
    // Component retains the complete generation bits and treats only -1 as
    // absent. A high-bit FullID remains an ID, never a negative-index shortcut.
    return ck3_12002::ResolveObjectiveTitle(bindings.title_holder.provinces,
                                          std::bit_cast<std::int32_t>(id));
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
#endif
}

struct Sample {
  std::uintptr_t vptr = 0;
  std::uint32_t full_id = UINT32_MAX;
  std::uint8_t destroy = 0, no_claims = 0, definitive = 0, follows = 0;
};

bool Capture(const Bindings &bindings, const void *title,
             std::uint32_t requested, Sample &sample) noexcept {
  return Load(title, 0, sample.vptr) &&
      sample.vptr == bindings.image_base + bindings.primary_title_vtable_rva &&
      Load(title, kTitleFullIdOffset, sample.full_id) &&
      sample.full_id == requested &&
      Load(title, kNativeDestroyIfInvalidHeirOffset, sample.destroy) &&
      Load(title, kNativeNoAutomaticClaimsOffset, sample.no_claims) &&
      Load(title, kNativeDefinitiveFormOffset, sample.definitive) &&
      Load(title, kNativeAlwaysFollowsPrimaryHeirOffset, sample.follows) &&
      sample.destroy <= 1 && sample.no_claims <= 1 &&
      sample.definitive <= 1 && sample.follows <= 1;
}

bool Same(const Sample &a, const Sample &b) noexcept {
  return a.vptr == b.vptr && a.full_id == b.full_id &&
      a.destroy == b.destroy && a.no_claims == b.no_claims &&
      a.definitive == b.definitive && a.follows == b.follows;
}

} // namespace

Bindings BindImage(std::uintptr_t image_base,
                   std::string_view executable_sha256) noexcept {
  Bindings bindings{};
  if (image_base == 0) return bindings;
  if (executable_sha256 == ck3_12004::kExecutableSha256) {
    bindings.title_holder = ck3_12004::BindTitleHolderImageV1(
        image_base, executable_sha256);
    bindings.actual4 = true;
    bindings.primary_title_vtable_rva =
        ck3_12004::confucian_titles::kCLandedTitlePrimaryVtableRva;
  } else if (executable_sha256 == kExecutableSha256) {
    bindings.title_holder = BindTitleHolderImageV1(image_base, executable_sha256);
  } else {
    return bindings;
  }
  if (!bindings.title_holder.enabled ||
      !bindings.title_holder.provinces.enabled) return bindings;
  bindings.enabled = true;
  bindings.image_base = image_base;
  return bindings;
}

bool Read(const Bindings &bindings, const game::Snapshot &frame,
          std::uint32_t requested, Observation &output) noexcept {
  output = {};
  output.date_raw = frame.date_raw;
  output.actor_character_id = frame.played_character_id;
  output.requested_title_full_id = requested;
  const auto fail = [&output](std::string_view reason) {
    output.unavailable_reason = reason;
    return false;
  };
  if (!bindings.enabled || bindings.image_base == 0 ||
      !bindings.title_holder.enabled ||
      !bindings.title_holder.provinces.enabled)
    return fail("title_properties_bindings_unavailable");
  if (!frame.paused || !frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive)
    return fail("paused_player_frame_unavailable");
  if (requested == UINT32_MAX) return fail("title_reference_absent");
  void *title = Resolve(bindings, requested);
  if (title == nullptr) return fail("title_generation_unavailable");
  Sample first{}, second{};
  if (!Capture(bindings, title, requested, first))
    return fail("title_type_or_boolean_fields_unavailable");
  if (Resolve(bindings, requested) != title ||
      !Capture(bindings, title, requested, second) || !Same(first, second) ||
      Resolve(bindings, requested) != title)
    return fail("title_properties_identity_or_values_changed");
  output.destroy_if_invalid_heir = first.destroy != 0;
  output.no_automatic_claims = first.no_claims != 0;
  output.definitive_form = first.definitive != 0;
  output.always_follows_primary_heir = first.follows != 0;
  output.available = true;
  output.unavailable_reason = {};
  return true;
}

} // namespace xar::ck3_12003::title_properties
