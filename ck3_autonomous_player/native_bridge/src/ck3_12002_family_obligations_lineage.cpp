#include "xar_bridge/ck3_12002_family_obligations_lineage.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include <cstring>

namespace xar::ck3_12002::family_obligations_lineage {
namespace {
template <typename T> void Store(void *object, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
bool Fail(std::string_view *reason, std::string_view value) noexcept {
  if (reason != nullptr) *reason = value;
  return false;
}
bool Frame(const Bindings &b, CoreSnapshotPrefix &out) noexcept {
  return ReadCoreSnapshot(b.family.context.core, out) && out.clock.paused &&
      out.map_ready && out.has_played_character && out.played_character_alive;
}
} // namespace

Bindings BindImage(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings out{};
  out.family = BindFamilyImage(base, sha);
  out.projection = BindFamilyProjectionImage(base, sha);
  if (!out.family.enabled || !out.projection.exact_build_admitted) return out;
  out.enabled = true;
  out.native_preview_parent = reinterpret_cast<ReadChildHousePreviewParent>(
      base + kNativeChildHousePreviewParentRva);
  out.native_offer_vtable = base + kNativeMarriageMatchOfferVtableRva;
  return out;
}

bool Read(const Bindings &b, std::int32_t subject, std::int32_t candidate,
          bool request_matrilineal, Snapshot &out,
          std::string_view *reason) noexcept {
  out = {};
  if (reason != nullptr) *reason = {};
  if (!b.enabled || !b.family.enabled || b.native_preview_parent == nullptr ||
      b.native_offer_vtable == 0 || b.family.read_boolean_option == nullptr ||
      b.family.matrilineal_option == nullptr)
    return Fail(reason, "native_child_house_preview_binding_unavailable");
  CoreSnapshotPrefix before{};
  if (!Frame(b, before)) return Fail(reason, "paused_played_frame_unavailable");
  if (subject == -1 || candidate == -1 || subject == candidate)
    return Fail(reason, "invalid_marriage_pair");

  FamilyPairContextV1 context{};
  if (!PrepareFamilyPairContextV1(b.family, before.played_character_id,
                                  subject, candidate, context))
    return Fail(reason, "native_marriage_pair_context_unavailable");
  struct Lease {
    const FamilyBindings &b; FamilyPairContextV1 &c;
    ~Lease() { DestroyFamilyPairContextV1(b, c); }
  } lease{b.family, context};
  if (request_matrilineal) {
    if (!SelectFamilyMatrilinealOptionV1(b.projection, context.bytes.data()))
      return Fail(reason, "native_matrilineal_option_unavailable");
    b.family.context.refresh(context.bytes.data(), true);
    b.family.context.finalize(context.bytes.data());
  }
  FamilyPairTermsV1 terms{};
  if (!ReadFamilyPairTermsV1(b.family, subject, candidate, context, terms))
    return Fail(reason, "native_marriage_final_terms_unavailable");
  const bool selected = b.family.read_boolean_option(context.bytes.data(),
                                                     *b.family.matrilineal_option);

  Snapshot result{};
  if (!ReadSelectedPairPreview(b.family.context.core, b,
          before.played_character_id, before.clock.date_raw, subject, candidate,
          selected, terms.effective_matrilineal_if_accepted,
          terms.complete_can_send, result, reason)) return false;
  result.requested_matrilineal_option = request_matrilineal;
  CoreSnapshotPrefix after{};
  if (!Frame(b, after) || after.played_character_id != before.played_character_id ||
      after.clock.date_raw != before.clock.date_raw)
    return Fail(reason, "native_child_house_preview_frame_changed");
  out = result;
  return true;
}

bool ReadSelectedPairPreview(
    const CoreBindings &core, const Bindings &b, std::int32_t played,
    std::int64_t date_raw, std::int32_t subject, std::int32_t candidate,
    bool selected, bool effective, bool can_send, Snapshot &out,
    std::string_view *reason) noexcept {
  out = {};
  if (reason != nullptr) *reason = {};
  if (!b.enabled || b.native_preview_parent == nullptr ||
      b.native_offer_vtable == 0)
    return Fail(reason, "native_child_house_preview_binding_unavailable");
  if (subject == -1 || candidate == -1 || subject == candidate)
    return Fail(reason, "invalid_marriage_pair");

  // The native offer initializer copies these exact secondary IDs at
  // 1373318/1373323 and caches the selected option at 1373C43. The detached
  // offer's +8 is null, selecting the native cached-option branch at 1375418.
  // The getter uses no other object field and does not initialize/destruct a
  // MatchOffer vector or operate a GUI window.
  alignas(8) std::array<std::byte, 0x88> offer{};
  Store(offer.data(), 0, b.native_offer_vtable);
  Store(offer.data(), 0x28, subject);
  Store(offer.data(), 0x2C, candidate);
  Store(offer.data(), 0x80, selected);
  void *parent = b.native_preview_parent(offer.data());
  void *subject_object = ResolveCoreCharacter(core, subject);
  void *candidate_object = ResolveCoreCharacter(core, candidate);
  if (parent == nullptr || (parent != subject_object && parent != candidate_object))
    return Fail(reason, "native_child_house_preview_parent_unavailable");
  Snapshot result{};
  result.played_character_id = played;
  result.date_raw = date_raw;
  result.subject_character_id = subject;
  result.candidate_character_id = candidate;
  result.selected_matrilineal_option = selected;
  result.effective_matrilineal_if_accepted = effective;
  result.complete_can_send = can_send;
  result.native_selected_parent_character_id = parent == subject_object ? subject : candidate;
  if (!family_value::ReadCharacterLineage(b.family.values, parent,
                                         result.native_preview_lineage, reason)) return false;
  result.available = true;
  out = result;
  return true;
}

} // namespace xar::ck3_12002::family_obligations_lineage
#endif
