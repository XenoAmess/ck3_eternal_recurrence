#include "xar_bridge/ck3_12002_family_obligations_break_penalty.hpp"

#include <algorithm>
#include <cstring>

namespace xar::ck3_12002::family_break_penalty {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset, sizeof(T));
  return result;
}

bool Character(void *object) noexcept {
  return object && Load<std::uint32_t>(object, 0x1C) == 0x43686172 &&
         Load<std::int32_t>(object, 0x18) >= 0 &&
         !Load<void *>(object, 0x1D0);
}

bool KeyEquals(const void *object, std::size_t offset, std::string_view key) noexcept {
  if (!object) return false;
  const auto *str = static_cast<const std::byte *>(object) + offset;
  const auto size = Load<std::size_t>(str, 0x10);
  const auto capacity = Load<std::size_t>(str, 0x18);
  if (size != key.size() || size > capacity) return false;
  const char *data = capacity < 16 ? reinterpret_cast<const char *>(str)
                                 : Load<const char *>(str, 0);
  return data && std::memcmp(data, key.data(), size) == 0;
}

bool HasGrandPromise(const Bindings &b, void *character, bool &present) noexcept {
  std::int32_t id = -1;
  present = false;
  if (!ResolvePhaseVariableIdentifier(b.identifiers, "promised_grand_wedding_by", id) ||
      !b.identifiers.variable_context) return false;
  const PhaseVariableTarget target{4, {}, Load<std::int32_t>(character, 0x18)};
  const auto *context = b.identifiers.variable_context(&target);
  if (!context) return false;
  const auto *data = Load<const std::byte *>(context, 0x10);
  const auto count = Load<std::int32_t>(context, 0x1C);
  if (count < 0 || count > 65536 || (count && !data)) return false;
  for (std::int32_t i = 0; i < count; ++i) {
    if (Load<std::int32_t>(data, static_cast<std::size_t>(i) * 0x20 + 8) != id) continue;
    if (present) return false;
    present = true;
  }
  return true;
}

bool AcceptedSameSexRule(const Bindings &b, bool &selected) noexcept {
  selected = false;
  const auto &d = b.identifiers;
  constexpr std::string_view key = "accepted_same_sex_marriage";
  if (!d.enabled || !d.rule_token_registry || !*d.rule_token_registry ||
      !d.rule_token_fallback || !d.hash_rule_key || !d.lookup_rule_token ||
      !d.rule_service || !*d.rule_service) return false;
  auto *registry = *d.rule_token_registry;
  const auto hash = d.hash_rule_key(registry, key.data(), static_cast<std::uint32_t>(key.size()));
  auto *token = d.lookup_rule_token(registry, hash);
  if (!token || token == *d.rule_token_fallback || !KeyEquals(token, 0x18, key)) return false;
  auto *service = *d.rule_service;
  auto *vtable = Load<const void *>(service, 0);
  if (!vtable) return false;
  const auto read = Load<void *(*)(void *)>(vtable, 0x10);
  if (!read) return false;
  const auto *selections = read(service);
  if (!selections) return false;
  const auto *data = Load<const void *>(selections, 8);
  const auto count = Load<std::int32_t>(selections, 0x14);
  if (count < 0 || count > 65536 || (count && !data)) return false;
  for (std::int32_t i = 0; i < count; ++i)
    if (Load<void *>(data, static_cast<std::size_t>(i) * 8) == token) selected = true;
  return true;
}

bool AllowsSameSex(const Bindings &b, void *character, bool rule,
                   bool &allowed) noexcept {
  allowed = false;
  if (!rule) return true;
  if (!b.character_rite || !b.parameter_set_contains) return false;
  std::int32_t id = -1;
  if (!ResolvePhaseScriptIdentifier(b.identifiers, "homosexuality_accepted", id)) return false;
  const auto *rite = b.character_rite(character);
  if (!rite) return false;
  allowed = b.parameter_set_contains(static_cast<const std::byte *>(rite) +
                                        kRiteParameterSetOffset, &id);
  return true;
}

bool ProperReason(const Bindings &b, void *first, void *second,
                  bool &proper) noexcept {
  proper = false;
  if (!b.traits.get_trait_database || !b.traits.character_has_trait ||
      !b.has_trait_flag) return false;
  const auto *database = b.traits.get_trait_database();
  const auto *eunuch = phase_character::FindUniqueTraitDefinition(database, "eunuch_1");
  const auto *beardless = phase_character::FindUniqueTraitDefinition(database, "beardless_eunuch");
  std::int32_t cannot_marry = -1;
  if (!eunuch || !beardless ||
      !ResolvePhaseScriptIdentifier(b.identifiers, "can_not_marry", cannot_marry)) return false;
  proper = b.traits.character_has_trait(first, eunuch) ||
           b.traits.character_has_trait(first, beardless) ||
           b.traits.character_has_trait(second, eunuch) ||
           b.traits.character_has_trait(second, beardless) ||
           b.has_trait_flag(first, &cannot_marry) ||
           b.has_trait_flag(second, &cannot_marry);
  if (proper) return true;
  const auto first_sex = Load<std::uint8_t>(first, family_value::kCharacterSexSelectorOffset);
  const auto second_sex = Load<std::uint8_t>(second, family_value::kCharacterSexSelectorOffset);
  if (first_sex > 1 || second_sex > 1) return false;
  if (first_sex != second_sex) return true;
  bool rule = false, first_allowed = false, second_allowed = false;
  if (!AcceptedSameSexRule(b, rule) || !AllowsSameSex(b, first, rule, first_allowed) ||
      !AllowsSameSex(b, second, rule, second_allowed)) return false;
  proper = !first_allowed || !second_allowed;
  return true;
}

std::int64_t OrdinaryUnits(std::int32_t tier) noexcept {
  switch (tier) {
  case 0: return 0;
  case 1: return 35;
  case 2: return 75;
  case 3: return 150;
  case 4: return 350;
  case 5: return 750;
  default: return 1500;
  }
}
std::int64_t GrandUnits(std::int32_t tier) noexcept {
  switch (tier) {
  case 0: return 35;
  case 1: return 75;
  case 2: return 150;
  case 3: return 350;
  case 4: return 750;
  default: return 1500;
  }
}
} // namespace

Bindings BindFamilyBreakPenaltyImage(std::uintptr_t base,
                                    std::string_view sha256) noexcept {
  Bindings b;
  if (!base || sha256 != kExecutableSha256) return b;
  b.enabled = true;
  b.lineage = family_value::BindImage(base, sha256);
  b.traits = phase_character::BindImage(base, sha256);
  b.identifiers = BindPhaseDefinitionsImage(base, sha256);
  b.highest_tier = reinterpret_cast<HighestTier>(base + kHighestTierRva);
  b.matchmaker = reinterpret_cast<Matchmaker>(base + kMatchmakerRva);
  b.close_family = reinterpret_cast<FamilyPredicate>(base + kCloseFamilyRva);
  b.close_or_extended_family = reinterpret_cast<FamilyPredicate>(base + kCloseOrExtendedFamilyRva);
  b.has_trait_flag = reinterpret_cast<TraitFlag>(base + kTraitFlagRva);
  b.yields_alliance = reinterpret_cast<YieldsAlliance>(base + kYieldsAllianceRva);
  b.character_rite = reinterpret_cast<CharacterRite>(base + kCharacterRiteRva);
  b.parameter_set_contains = reinterpret_cast<ParameterSetContains>(base + kRiteParameterSetContainsRva);
  return b;
}

bool ReadFamilyBreakPenalty(const Bindings &b, void *actor, void *rejecting,
                            void *rejected, Penalty &out) noexcept {
  out = {};
  if (!b.enabled || !Character(actor) || !Character(rejecting) || !Character(rejected) ||
      !b.highest_tier || !b.matchmaker || !b.close_family ||
      !b.close_or_extended_family || !b.yields_alliance) return false;
  Penalty p;
  if (!ProperReason(b, rejecting, rejected, p.proper_reason)) return false;
  bool first_grand = false, second_grand = false;
  if (!HasGrandPromise(b, rejecting, first_grand) ||
      !HasGrandPromise(b, rejected, second_grand)) return false;
  p.grand_wedding_promised = first_grand || second_grand;
  auto *matchmaker = b.matchmaker(rejected);
  if (!Character(matchmaker)) return false;
  auto *owner = matchmaker != rejected &&
                        ((!p.proper_reason && p.grand_wedding_promised) ||
                         b.close_or_extended_family(matchmaker, rejected))
                    ? matchmaker : rejected;
  p.rejected_owner_character_id = Load<std::int32_t>(owner, 0x18);
  const auto first_tier = b.highest_tier(rejected), second_tier = b.highest_tier(owner);
  if (first_tier < 0 || first_tier > 6 || second_tier < 0 || second_tier > 6) return false;
  p.highest_rejected_tier = std::max(first_tier, second_tier);
  if (!p.proper_reason) {
    if (p.grand_wedding_promised) {
      p.stock_prestige_effect_raw = -GrandUnits(p.highest_rejected_tier) * 100000;
      p.stock_prestige_level_effect = -1;
    } else {
      family_value::Lineage actor_lineage, first_lineage, second_lineage;
      if (!family_value::ReadCharacterLineage(b.lineage, actor, actor_lineage) ||
          !family_value::ReadCharacterLineage(b.lineage, rejecting, first_lineage) ||
          !family_value::ReadCharacterLineage(b.lineage, rejected, second_lineage)) return false;
      const bool same_dynasty = actor_lineage.dynasty_id >= 0 &&
          (actor_lineage.dynasty_id == first_lineage.dynasty_id ||
           actor_lineage.dynasty_id == second_lineage.dynasty_id);
      // CYieldsAlliance itself also rejects unlanded actor/target before its
      // 4-character leaf. Do not bypass those native wrapper prerequisites.
      p.yields_alliance = Load<void *>(actor, 0x1C0) && Load<void *>(owner, 0x1C0) &&
          b.yields_alliance(actor, owner, rejecting, rejected);
      p.native_yields_alliance_evaluated = true;
      p.ordinary_prestige_relevant = b.close_family(rejected, actor) ||
          b.close_family(rejecting, actor) || same_dynasty || p.yields_alliance;
      if (p.ordinary_prestige_relevant)
        p.stock_prestige_effect_raw = -OrdinaryUnits(p.highest_rejected_tier) * 100000;
    }
  }
  p.resource_penalty_available = true;
  p.unavailable_reason = {};
  out = p;
  return true;
}
} // namespace xar::ck3_12002::family_break_penalty
