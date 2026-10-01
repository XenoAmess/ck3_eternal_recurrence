#include "xar_bridge/ck3_12002_claim_terms.hpp"

#include <algorithm>
#include <cstring>
#include <string>
#include <utility>
#include <vector>

namespace xar::ck3_12002 {
namespace {
template <typename T>
T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

void *ResolveClaimant(const CoreBindings &bindings,
                     std::int32_t id) noexcept {
  if (id == -1 || bindings.character_storage_slot == nullptr) {
    return nullptr;
  }
  void *const storage = *bindings.character_storage_slot;
  if (storage == nullptr) {
    return nullptr;
  }
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  void *const slots = Load<void *>(storage, 0x20);
  if (slots == nullptr || capacity <= 0 || capacity > 1'000'000 ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *const character = Load<void *>(slots, index * 0x10ULL + 8);
  return character != nullptr && Load<std::int32_t>(character, 0x18) == id
             ? character
             : nullptr;
}

bool ReadCasusBelliKey(const void *type, std::string &output) noexcept {
  output.clear();
  if (type == nullptr) {
    return false;
  }
  const auto *const text = static_cast<const std::byte *>(type) + 0x18;
  const auto size = Load<std::size_t>(text, 0x10);
  const auto capacity = Load<std::size_t>(text, 0x18);
  if (size == 0 || size > capacity || size > 1'024) {
    return false;
  }
  const char *const data = capacity <= 15
                              ? reinterpret_cast<const char *>(text)
                              : Load<const char *>(text, 0);
  if (data == nullptr) {
    return false;
  }
  output.assign(data, size);
  return true;
}

bool ReadClaimRow(const ClaimTermsBindings &bindings, void *claimant,
                  void *title, std::int32_t title_id,
                  game::WarClaimSnapshot &output) noexcept {
  output = {};
  ClaimTermsStorage storage{};
  void *const claim = storage.bytes.data();
  void *const returned = bindings.read_character_claim(claim, claimant, title);
  const auto present = Load<std::uint8_t>(claim, kClaimTermsPresentOffset);
  if (returned != claim || present > 1) {
    return false;
  }
  output.title_id = title_id;
  output.present = present != 0;
  if (!output.present) {
    output.state = "absent";
    return true;
  }
  auto **const vtable = Load<void **>(claim, 0);
  if (reinterpret_cast<std::uintptr_t>(vtable) !=
          bindings.character_claim_vtable ||
      vtable == nullptr || vtable[0] == nullptr) {
    return false;
  }
  const auto strong = Load<std::uint8_t>(claim, kClaimTermsStrongOffset);
  const auto implicit = Load<std::uint8_t>(claim, kClaimTermsImplicitOffset);
  const bool valid = strong <= 1 && implicit <= 1 &&
                     Load<std::int32_t>(claim, kClaimTermsTitleIdOffset) == title_id;
  if (valid) {
    output.strong = strong != 0;
    output.implicit = implicit != 0;
    output.state = output.strong
                       ? (output.implicit ? "strong_implicit" : "strong_explicit")
                       : (output.implicit ? "weak_implicit" : "weak_explicit");
  }
  // Native scalar destructor frees its object only when delete_flags & 1.
  // This is our stack temporary; it is destroyed with zero and never freed.
  using DestroyClaim = void *(*)(void *, std::int32_t);
  reinterpret_cast<DestroyClaim>(vtable[0])(
      claim, kClaimTermsDestructorDeleteFlags);
  return valid;
}
} // namespace

ClaimTermsBindings BindClaimTermsImage(std::uintptr_t image_base,
                                      std::string_view sha256) noexcept {
  ClaimTermsBindings bindings{};
  if (image_base == 0 || sha256 != kExecutableSha256) {
    return bindings;
  }
  bindings.enabled = true;
  bindings.core = BindCoreImage(image_base, sha256);
  bindings.world = BindWorldImage(image_base, sha256);
  bindings.provinces = BindProvinceImage(image_base, sha256);
  bindings.read_character_claim = reinterpret_cast<ReadCharacterClaim12002>(
      image_base + kClaimTermsGetterRva);
  bindings.character_claim_vtable = image_base + kClaimTermsClaimVtableRva;
  return bindings;
}

game::ReadWarTerminationTermsResult ReadWarTerminationTerms(
    const ClaimTermsBindings &bindings, std::int32_t war_id,
    game::WarTerminationTermsSnapshot &output) noexcept {
  using Result = game::ReadWarTerminationTermsResult;
  output = {};
  if (!bindings.enabled || !bindings.core.enabled || !bindings.world.enabled ||
      !bindings.provinces.enabled || bindings.read_character_claim == nullptr ||
      bindings.character_claim_vtable == 0 ||
      bindings.world.contains_war_participant == nullptr) {
    return Result::unavailable;
  }
  CoreSnapshotPrefix before{};
  if (!ReadCoreSnapshot(bindings.core, before)) {
    return Result::unavailable;
  }
  if (!before.clock.paused) {
    return Result::requires_paused;
  }
  if (!before.has_played_character || !before.played_character_alive) {
    return Result::no_played_character;
  }
  void *const war = ResolveWar(bindings.world, war_id);
  if (war == nullptr) {
    return Result::war_not_found;
  }
  const auto *const bytes = static_cast<const std::byte *>(war);
  const bool attacking = bindings.world.contains_war_participant(
      bytes + kWorldWarAttackersOffset, before.played_character_id);
  const bool defending = bindings.world.contains_war_participant(
      bytes + kWorldWarDefendersOffset, before.played_character_id);
  if (!attacking && !defending) {
    return Result::player_not_participant;
  }
  if (attacking && defending) {
    return Result::unavailable;
  }
  void *const type = Load<void *>(war, kWorldWarCasusBelliOffset);
  const auto type_index = type == nullptr ? -1 : Load<std::int32_t>(type, 0x10);
  std::string type_key;
  if (type_index < 0 || type_index >= 10'000 ||
      !ReadCasusBelliKey(type, type_key)) {
    return Result::unavailable;
  }
  output.war_id = war_id;
  output.active_casus_belli_database_index = type_index;
  output.active_casus_belli_key = type_key;
  if (type_key != "claim_cb") {
    if (ResolveWar(bindings.world, war_id) != war ||
        Load<void *>(war, kWorldWarCasusBelliOffset) != type) {
      output = {};
      return Result::unavailable;
    }
    return Result::unsupported_casus_belli;
  }
  const auto claimant_id = Load<std::int32_t>(war, kWorldWarClaimantOffset);
  void *const claimant = ResolveClaimant(bindings.core, claimant_id);
  if (claimant == nullptr ||
      !ReadWarTargetTitleIds(war, output.target_title_ids) ||
      output.target_title_ids.empty()) {
    output = {};
    return Result::unavailable;
  }
  std::vector<void *> titles;
  titles.reserve(output.target_title_ids.size());
  for (std::size_t index = 0; index < output.target_title_ids.size(); ++index) {
    const auto id = output.target_title_ids[index];
    if (std::find(output.target_title_ids.begin(),
                  output.target_title_ids.begin() + index, id) !=
        output.target_title_ids.begin() + index) {
      output = {};
      return Result::unavailable;
    }
    void *const title = ResolveObjectiveTitle(bindings.provinces, id);
    if (title == nullptr) {
      output = {};
      return Result::unavailable;
    }
    titles.push_back(title);
  }
  output.claimant_character_id = claimant_id;
  output.claims.reserve(titles.size());
  for (std::size_t index = 0; index < titles.size(); ++index) {
    game::WarClaimSnapshot row{};
    if (!ReadClaimRow(bindings, claimant, titles[index],
                      output.target_title_ids[index], row)) {
      output = {};
      return Result::unavailable;
    }
    output.claims.push_back(std::move(row));
  }
  std::vector<std::int32_t> targets_after;
  std::string key_after;
  CoreSnapshotPrefix after{};
  bool stable = ResolveWar(bindings.world, war_id) == war &&
                Load<void *>(war, kWorldWarCasusBelliOffset) == type &&
                Load<std::int32_t>(type, 0x10) == type_index &&
                ReadCasusBelliKey(type, key_after) && key_after == type_key &&
                Load<std::int32_t>(war, kWorldWarClaimantOffset) == claimant_id &&
                ResolveClaimant(bindings.core, claimant_id) == claimant &&
                ReadWarTargetTitleIds(war, targets_after) &&
                targets_after == output.target_title_ids &&
                ReadCoreSnapshot(bindings.core, after) && after.clock.paused &&
                after.clock.date_raw == before.clock.date_raw &&
                after.played_character_id == before.played_character_id;
  for (std::size_t index = 0; stable && index < titles.size(); ++index) {
    stable = ResolveObjectiveTitle(bindings.provinces,
                                   output.target_title_ids[index]) == titles[index];
  }
  if (!stable) {
    output = {};
    return Result::unavailable;
  }
  // These dispositions are the preserved narrow claim_cb contract. Crozier's
  // frozen 00_claim.txt still transfers conquest_claim with add_claim_on_loss,
  // strengthens weak claims on white peace and removes target claims on defeat.
  output.attacker_victory = {"transfer_to_claimant_via_conquest_claim",
                             "resolve_with_add_claim_on_loss"};
  output.white_peace = {"unchanged", "retain_and_strengthen_weak"};
  output.attacker_defeat = {"unchanged", "remove_declared_target_claims"};
  return Result::available;
}

} // namespace xar::ck3_12002
