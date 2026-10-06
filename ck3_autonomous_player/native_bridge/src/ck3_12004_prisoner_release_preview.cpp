#include "xar_bridge/ck3_12004_prisoner_release_preview.hpp"

namespace xar::ck3_12004 {

PrisonerReleasePreviewBindings12004 BindPrisonerReleasePreview12004(
    std::uintptr_t base, std::string_view actual_sha) noexcept {
  PrisonerReleasePreviewBindings12004 b{};
  const auto shared = BindInteractionContext12004(base, actual_sha);
  if (!shared.enabled) return b;
  b.module_base = base;
  b.gift.module_base = base;
  b.gift.interaction = shared.context;
  b.gift.get_database = shared.get_database;
  b.gift.stable_hash = shared.stable_hash;
  b.gift.lookup_definition = shared.lookup_definition;
  b.gift.construct_two_role = shared.construct_two_role;
  b.get_script_identifier_table = shared.get_script_identifier_table;
  b.lookup_script_identifier_id = shared.lookup_script_identifier_id;
  b.clear_local_options = shared.clear_local_options;
  b.gift.enabled = true;
  b.enabled = true;
  return b;
}

bool ReadPrisonerReleasePreview12004(const PrisonerReleasePreviewBindings12004 &b,
    const PrisonerReleasePreviewAccess12004 &access, std::uint32_t jailer,
    std::uint32_t prisoner, PrisonerReleasePreview12004 &output) noexcept {
  // Software observer only: all native entry pointers come from the actual .4
  // binder above. The recorded .4 member-operand witnesses close the unchanged
  // definition/context layouts, and the parent custody receipt closes the
  // shared core slots and prison relation used by this algorithm.
  return ck3_12003::ReadPrisonerReleasePreview12003(b, access, jailer, prisoner, output);
}

std::string SerializePrisonerReleasePreview12004(
    const PrisonerReleasePreview12004 &output) {
  return ck3_12003::SerializePrisonerReleasePreview12003(output);
}

} // namespace xar::ck3_12004
