#include "xar_bridge/ck3_12003_player_rite_virtue_sin_profile.hpp"

#include <cstring>
#include <sstream>

namespace xar::ck3_12002::religion::rite_virtue_sin_profile12003 {
namespace {
template <typename T> T Load(const void *source, std::size_t offset = 0) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(source) + offset, sizeof(value));
  return value;
}
template <typename T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
} // namespace

Bindings BindPlayerRiteVirtueSinProfileImage12003(
    std::uintptr_t base, const game::AdapterDescriptor &descriptor) noexcept {
  Bindings b;
  if (base == 0 || !game::IsCk3_12003Descriptor(descriptor)) return b;
  b.enabled = true;
  b.trait_database = reinterpret_cast<TraitDatabase>(base + kTraitDatabaseRva);
  b.trait_lookup = reinterpret_cast<TraitLookup>(base + kTraitLookupRva);
  b.character_rite = reinterpret_cast<CharacterRite>(base + kCharacterRiteRva);
  b.trait_classification = reinterpret_cast<TraitClassification>(base + kTraitClassificationRva);
  return b;
}

bool ReadPlayerRiteVirtueSinProfile12003(const Bindings &b, void *actor,
    const religion::Context &current, Profile &out) noexcept {
  out = {};
  out.capture_epoch = current.capture_epoch;
  out.date_raw = current.date_raw;
  out.played_character_id = current.played_character_id;
  if (!b.enabled || !b.trait_database || !b.trait_lookup ||
      !b.character_rite || !b.trait_classification) return false;
  if (!actor || current.played_character_id <= 0 ||
      Load<std::int32_t>(actor, 0x18) != current.played_character_id) {
    out.unavailable_reason = "played_character_unavailable"; return false;
  }
  try {
    auto *rite = b.character_rite(actor);
    if (!rite) { out.unavailable_reason = "rite_unavailable"; return false; }
    const auto rite_id = Load<std::uint32_t>(rite, 0x8);
    if (rite_id != Load<std::uint32_t>(actor, religion::kCharacterRiteIdOffset)) {
      out.unavailable_reason = "rite_identity_mismatch"; return false;
    }
    const auto count = Load<std::int32_t>(actor, kCharacterTraitCountOffset);
    const auto *rows = Load<const std::int32_t *>(actor, kCharacterTraitRowsOffset);
    if (count < 0 || (count != 0 && !rows)) {
      out.unavailable_reason = "trait_rows_unavailable"; return false;
    }
    auto *database = b.trait_database();
    if (!database) { out.unavailable_reason = "trait_database_unavailable"; return false; }
    std::vector<TraitRow> observed;
    std::int32_t virtues = 0, sins = 0;
    for (std::int32_t i = 0; i < count; ++i) {
      const auto trait_id = Load<std::int32_t>(rows, static_cast<std::size_t>(i) * 4);
      auto *trait = b.trait_lookup(database, trait_id);
      if (!trait) { out.unavailable_reason = "trait_definition_unavailable"; return false; }
      void *record = nullptr;
      const auto kind = b.trait_classification(trait,
          static_cast<std::byte *>(rite) + kRiteEffectiveTraitMapOffset, &record);
      if (kind < 0 || kind > 2 || (kind != 0 && !record)) {
        out.unavailable_reason = "trait_classification_unavailable"; return false;
      }
      TraitRow row{trait_id, kind, std::nullopt, std::nullopt};
      if (record) {
        // Different native consumer inputs. Neither is a final opinion or a
        // monthly piety reward, and this reader does not combine them.
        row.opinion_weight_input_raw = Load<std::int64_t>(record, 0x18);
        row.owner_modifier_scale_input_raw = Load<std::int64_t>(record, 0x20);
      }
      virtues += kind == 1 ? 1 : 0;
      sins += kind == 2 ? 1 : 0;
      observed.push_back(row);
    }
    out.rite_id = rite_id;
    out.trait_count = count;
    out.num_virtuous_traits = virtues;
    out.num_sinful_traits = sins;
    out.traits = std::move(observed);
    out.available = true;
    out.unavailable_reason.clear();
    return true;
  } catch (...) { out.unavailable_reason = "trait_profile_copy_exception"; return false; }
}

std::string SerializePlayerRiteVirtueSinProfile12003(const Profile &p) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":\"ck3_12003_player_rite_virtue_sin_profile_v1\",\"read_only\":true,\"available\":"
      << p.available << ",\"unavailable_reason\":";
  if (p.available) out << "null";
  else out << '\"' << p.unavailable_reason << '\"';
  out << ",\"capture_epoch\":" << p.capture_epoch << ",\"date_raw\":" << p.date_raw
      << ",\"played_character_id\":" << p.played_character_id
      << ",\"rite_id\":" << Number(p.rite_id)
      << ",\"trait_count\":" << Number(p.trait_count)
      << ",\"num_virtuous_traits\":" << Number(p.num_virtuous_traits)
      << ",\"num_sinful_traits\":" << Number(p.num_sinful_traits)
      << ",\"traits\":[";
  bool first = true;
  for (const auto &row : p.traits) {
    if (!first) out << ',';
    first = false;
    out << "{\"trait_id\":" << row.trait_id << ",\"classification\":" << row.classification
        << ",\"opinion_weight_input_raw\":" << Number(row.opinion_weight_input_raw)
        << ",\"owner_modifier_scale_input_raw\":" << Number(row.owner_modifier_scale_input_raw) << '}';
  }
  out << "],\"scope\":\"current-played-character-current-rite\",\"counts_are_unweighted\":true} " ;
  return out.str();
}

} // namespace xar::ck3_12002::religion::rite_virtue_sin_profile12003
