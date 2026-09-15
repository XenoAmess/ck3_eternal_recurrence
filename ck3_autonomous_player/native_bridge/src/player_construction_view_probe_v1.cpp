#include "player_construction_view_probe_v1.hpp"

#include <limits>

namespace xar::ck3::shared {
namespace {

constexpr std::uintptr_t kHandlerVtableRva = 0x40AF630U;
constexpr std::uintptr_t kHoldingViewVtableRva = 0x4131618U;
constexpr std::uintptr_t kHandlerHoldingViewOffset = 0xD0U;
constexpr std::uintptr_t kHoldingViewOwnerOffset = 0xD0U;
constexpr std::uintptr_t kPotentialBuildingsDataOffset = 0x118U;
constexpr std::uintptr_t kPotentialBuildingsCapacityOffset = 0x120U;
constexpr std::uintptr_t kPotentialBuildingsCountOffset = 0x124U;

bool Add(std::uintptr_t base, std::uintptr_t offset,
         std::uintptr_t& result) noexcept {
  if (base == 0U || offset >
                        std::numeric_limits<std::uintptr_t>::max() - base) {
    return false;
  }
  result = base + offset;
  return true;
}

template <typename T>
bool Read(const PlayerConstructionViewProbeSourceV1& source,
          std::uintptr_t base, std::uintptr_t offset, T& result) noexcept {
  std::uintptr_t address = 0U;
  return Add(base, offset, address) &&
         source.read_memory(source.read_context, address, &result,
                            sizeof(result));
}

PlayerConstructionViewProbeResultV1 Failed(
    PlayerConstructionViewProbeFailureV1 reason) noexcept {
  PlayerConstructionViewProbeResultV1 result{};
  result.failure = reason;
  return result;
}

}  // namespace

PlayerConstructionViewProbeResultV1 ProbePlayerConstructionViewCacheV1(
    const PlayerConstructionViewProbeAdmissionV1& admission,
    const PlayerConstructionViewProbeSourceV1& source) noexcept {
  if (!admission.exact_build_admitted || admission.module_base == 0U) {
    return Failed(PlayerConstructionViewProbeFailureV1::exact_build);
  }
  if (!admission.application_main_thread) {
    return Failed(PlayerConstructionViewProbeFailureV1::application_main);
  }
  if (!admission.session_live) {
    return Failed(PlayerConstructionViewProbeFailureV1::session);
  }
  if (source.resolve_owner == nullptr || source.read_memory == nullptr) {
    return Failed(PlayerConstructionViewProbeFailureV1::owner_path);
  }

  PlayerConstructionViewResolvedOwnerV1 owner{};
  if (!source.resolve_owner(source.owner_context, admission.module_base,
                            owner) ||
      owner.root == 0U || owner.idler_base == 0U ||
      owner.idler_gfx == 0U || owner.handler == 0U ||
      !owner.exact_idler_rtti_cast) {
    return Failed(PlayerConstructionViewProbeFailureV1::owner_path);
  }

  std::uintptr_t handler_vtable = 0U;
  std::uintptr_t expected_handler_vtable = 0U;
  if (!Add(admission.module_base, kHandlerVtableRva,
           expected_handler_vtable) ||
      !Read(source, owner.handler, 0U, handler_vtable)) {
    return Failed(PlayerConstructionViewProbeFailureV1::source_read);
  }
  if (handler_vtable != expected_handler_vtable) {
    return Failed(PlayerConstructionViewProbeFailureV1::owner_path);
  }

  std::uintptr_t view = 0U;
  if (!Read(source, owner.handler, kHandlerHoldingViewOffset, view)) {
    return Failed(PlayerConstructionViewProbeFailureV1::source_read);
  }
  if (view == 0U) {
    return Failed(PlayerConstructionViewProbeFailureV1::view_missing);
  }

  std::uintptr_t expected_view_vtable = 0U;
  std::uintptr_t view_vtable = 0U;
  std::uintptr_t round_trip_handler = 0U;
  if (!Add(admission.module_base, kHoldingViewVtableRva,
           expected_view_vtable) ||
      !Read(source, view, 0U, view_vtable) ||
      !Read(source, view, kHoldingViewOwnerOffset, round_trip_handler)) {
    return Failed(PlayerConstructionViewProbeFailureV1::source_read);
  }
  if (view_vtable != expected_view_vtable ||
      round_trip_handler != owner.handler) {
    return Failed(PlayerConstructionViewProbeFailureV1::view_identity);
  }

  std::uintptr_t data = 0U;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  if (!Read(source, view, kPotentialBuildingsDataOffset, data) ||
      !Read(source, view, kPotentialBuildingsCapacityOffset, capacity) ||
      !Read(source, view, kPotentialBuildingsCountOffset, count)) {
    return Failed(PlayerConstructionViewProbeFailureV1::source_read);
  }
  if (count < 0 || capacity < count || capacity < 0 ||
      (count > 0 && data == 0U)) {
    return Failed(PlayerConstructionViewProbeFailureV1::candidate_span);
  }

  PlayerConstructionViewProbeResultV1 result{};
  result.view_present = true;
  result.candidate_capacity = capacity;
  result.cached_candidate_count = count;
  result.status = count == 0
                      ? PlayerConstructionViewProbeStatusV1::
                            view_candidate_cache_empty
                      : PlayerConstructionViewProbeStatusV1::
                            view_candidate_cache_present;
  bool effective_visible = false;
  if (source.read_holding_view_visibility != nullptr &&
      source.read_holding_view_visibility(
          source.visibility_context, admission.module_base,
          effective_visible)) {
    result.holding_view_visibility =
        effective_visible
            ? PlayerConstructionHoldingViewVisibilityV1::visible
            : PlayerConstructionHoldingViewVisibilityV1::hidden;
  }
  return result;
}

}  // namespace xar::ck3::shared
