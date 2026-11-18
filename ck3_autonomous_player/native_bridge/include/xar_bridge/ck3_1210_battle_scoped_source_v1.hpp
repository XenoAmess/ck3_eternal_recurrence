#pragma once
#include "xar_bridge/ck3_1210_scoped_image_roots_v1.hpp"
#include "xar_bridge/ck3_1210_battle_candidate_v1.hpp"

namespace xar::ck3_1210 {
namespace battle_scoped_source_detail_v1 {
struct Access {
  const Scoped1210ImageSourceV1 &source;
  const CoreSnapshotPrefix &expected;
  const Scoped1210SourceAccessV1 &access;
  Scoped1210ManagerRootsV1 unit_owner{};
  static bool Copy(void *context, const void *from, void *to,
      std::size_t size) noexcept {
    const auto &a = *static_cast<const Access *>(context);
    return a.access.copy != nullptr &&
        a.access.copy(a.access.context, from, to, size);
  }
  static bool Frame(void *context) noexcept {
    const auto &a = *static_cast<const Access *>(context);
    Scoped1210ManagerRootsV1 current{};
    return ResolveScoped1210ManagerV1(a.source, a.expected, a.access,
        Scoped1210ManagerKindV1::unit, current) && current == a.unit_owner;
  }
};
} // namespace battle_scoped_source_detail_v1

// Actual image-source seam over slot32's narrow candidate reader. The owner
// supplies its existing Core identity/custody validator, not a new bool lease.
// Root slots and binder are derived here from the selected exact descriptor;
// callers cannot inject three unrelated registry-slot pointers at this entry.
// Known Unit manager/global/VT ownership is checked at every reader frame gate.
// Combat/Army owning-manager identity and complete Battle state remain UNKNOWN.
inline bool ReadBattleCandidateFromScoped1210ImageV1(
    const Scoped1210ImageSourceV1 &source, const CoreSnapshotPrefix &expected,
    std::int32_t subject_public_cunit_id, BattleCandidateObservationV1 &output,
    const Scoped1210SourceAccessV1 &access) noexcept {
  output = {};
  battle_scoped_source_detail_v1::Access current{source, expected, access, {}};
  if (!ResolveScoped1210ManagerV1(source, expected, access,
          Scoped1210ManagerKindV1::unit, current.unit_owner)) return false;
  // Root validation already checked the adapter triple and full Core bundle.
  const auto binding = BindBattleCandidateImageV1(
      source.image_base, source.descriptor->executable_sha256);
  return ReadBattleCandidateV1(binding, subject_public_cunit_id,
      expected.played_character_id, output,
      {&current, &battle_scoped_source_detail_v1::Access::Copy,
          &battle_scoped_source_detail_v1::Access::Frame});
}
} // namespace xar::ck3_1210
