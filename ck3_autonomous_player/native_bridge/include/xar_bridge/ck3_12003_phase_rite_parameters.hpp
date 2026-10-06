#pragma once

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/phase_rite_parameters_v1.hpp"
#include "xar_bridge/rite_boolean_parameters_copy.hpp"

namespace xar::ck3_12003::phase_rite {
struct Bindings {
  bool enabled = false;
  ck3_12002::religion::ObjectGetter character_rite = nullptr;
  ck3_12002::religion::ObjectGetter character_faith = nullptr;
  ck3_12002::religion::ObjectGetter rite_faith = nullptr;
  ck3_12002::religion::doctrine12002::TenetParameterBindings parameters;
};

inline Bindings BindImage(std::uintptr_t base, std::string_view sha) noexcept {
  if (!base || sha != ck3_12003::kExecutableSha256) return {};
  namespace religion = ck3_12002::religion;
  using Getter = religion::ObjectGetter;
  using Membership = religion::doctrine12002::BooleanParameterMembership;
  using Key = religion::doctrine12002::ParameterTokenKey;
  Bindings result{};
  result.enabled = true;
  result.character_rite = reinterpret_cast<Getter>(base + religion::kCharacterRiteRva);
  result.character_faith = reinterpret_cast<Getter>(base + religion::kCharacterFaithRva);
  result.rite_faith = reinterpret_cast<Getter>(base + religion::kRiteFaithRva);
  result.parameters = {true,
      reinterpret_cast<Membership>(base + religion::doctrine12002::kBooleanParameterMembershipRva),
      reinterpret_cast<Key>(base + religion::doctrine12002::kParameterTokenKeyRva)};
  return result;
}

// The owning combat collector already resolved and validated Character. A
// disabled legacy provider leaves the optional leaf missing; a failed actual
// Rite read returns its own unavailable status without changing base readiness.
inline std::optional<game::PhaseRiteParametersV1> Read(
    const Bindings &b, void *character, std::uint32_t character_id) {
  if (!b.enabled || !character) return std::nullopt;
  namespace religion = ck3_12002::religion;
  namespace parameters = religion::doctrine12002;
  using parameters::detail::LoadRiteBoolean;
  game::PhaseRiteParametersV1 out{};
  out.source_character_id = character_id;
  out.raw_adopted_rite_id = LoadRiteBoolean<std::uint32_t>(character, religion::kCharacterRiteIdOffset);
  const auto fail = [&](std::string reason) {
    out.status = game::PhaseRiteParameterStatusV1::unavailable;
    out.boolean_parameters_complete = false;
    out.boolean_parameter_keys.clear();
    out.unavailable_reason = std::move(reason);
    return std::optional<game::PhaseRiteParametersV1>{out};
  };
  if (LoadRiteBoolean<std::uint32_t>(character, 0x18) != character_id)
    return fail("source_character_changed");
  if (out.raw_adopted_rite_id == religion::kAbsentReference) {
    out.status = game::PhaseRiteParameterStatusV1::absent;
    return out;
  }
  if (!b.parameters.enabled || !b.parameters.contains_boolean_parameter ||
      !b.parameters.parameter_key || !b.character_rite || !b.character_faith || !b.rite_faith)
    return fail("phase_rite_bindings_unavailable");
  void *rite = b.character_rite(character);
  if (!rite || LoadRiteBoolean<std::uint32_t>(rite, religion::kReferenceIdentityOffset) != out.raw_adopted_rite_id)
    return fail("rite_unavailable");
  out.rite_id = out.raw_adopted_rite_id;
  const auto faith_id = LoadRiteBoolean<std::uint32_t>(rite, religion::kRiteFaithIdOffset);
  if (faith_id != religion::kAbsentReference) {
    void *faith = b.rite_faith(rite);
    if (!faith || LoadRiteBoolean<std::uint32_t>(faith, religion::kReferenceIdentityOffset) != faith_id ||
        b.character_faith(character) != faith)
      return fail("faith_unavailable");
    out.faith_id = faith_id;
  }
  parameters::RiteBooleanParameters copied{};
  auto reason = parameters::detail::CopyRiteBooleanParameters(b.parameters, rite, *out.rite_id, copied);
  if (!reason.empty()) return fail(std::move(reason));
  if (LoadRiteBoolean<std::uint32_t>(character, 0x18) != character_id ||
      LoadRiteBoolean<std::uint32_t>(character, religion::kCharacterRiteIdOffset) != out.raw_adopted_rite_id ||
      LoadRiteBoolean<std::uint32_t>(rite, religion::kRiteFaithIdOffset) != faith_id)
    return fail("source_identity_changed");
  for (auto &value : copied.parameters) out.boolean_parameter_keys.push_back(std::move(value.key));
  out.boolean_parameters_complete = true;
  out.status = game::PhaseRiteParameterStatusV1::available;
  return out;
}
} // namespace xar::ck3_12003::phase_rite
