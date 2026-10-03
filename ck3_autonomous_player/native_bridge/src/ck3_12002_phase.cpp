#include "xar_bridge/ck3_12002_phase.hpp"
#include "xar_bridge/ck3_12002.hpp"

#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <bcrypt.h>
#include <charconv>
#include <stdexcept>
#include <algorithm>
#include <cstring>
#include <limits>
#include <utility>

namespace xar::ck3_12002 {
namespace {
template <typename T> T Load(const void *p, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(T));
  return value;
}
template <typename T> void Store(void *p, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(T));
}

using NativeFree = void (*)(void *, void *, std::size_t);
bool FreePopulation(void *local) noexcept {
  void *data = Load<void *>(local, 0x38);
  if (!data) return true;
  void *allocator = Load<void *>(local, 0x48);
  if (!allocator) return false;
  void *vtable = Load<void *>(allocator, 0);
  if (!vtable) return false;
  auto release = Load<NativeFree>(vtable, 0x10);
  if (!release) return false;
  release(allocator, data, 8);
  Store<void *>(local, 0x38, nullptr);
  Store<std::int32_t>(local, 0x40, 0);
  Store<std::int32_t>(local, 0x44, 0);
  return true;
}

struct LocalCombat {
  alignas(16) std::array<std::byte, kPhaseCombatShellSize + 8> shell{};
  alignas(16) std::array<std::array<std::byte, 0x50>, 2> local{};
  DestroyPhaseSide destroy = nullptr;
  std::size_t constructed = 0;
  bool cleaned = false;
  void *side(std::size_t i) noexcept {
    return shell.data() + (i == 0 ? 0x20 : 0x368);
  }
  bool cleanup() noexcept {
    if (cleaned) return true;
    cleaned = true;
    bool okay = true;
    for (std::size_t n = constructed; n > 0; --n) destroy(side(n - 1));
    for (std::size_t n = constructed; n > 0; --n)
      okay = FreePopulation(local[n - 1].data()) && okay;
    return okay;
  }
  ~LocalCombat() { (void)cleanup(); }
};

bool AllocatePhaseLedger(void *side, const std::vector<AdvantageLedgerEntry> &entries) noexcept {
  if (entries.empty()) return true;
  if (entries.size() > 65'536 || Load<void *>(side, 0x78)) return false;
  void *allocator = Load<void *>(side, 0x88);
  void *table = allocator ? Load<void *>(allocator, 0) : nullptr;
  using Allocate = void *(*)(void *, std::size_t, std::size_t);
  auto allocate = table ? Load<Allocate>(table, 8) : nullptr;
  if (!allocate) return false;
  void *buffer = allocate(allocator, entries.size() * sizeof(AdvantageLedgerEntry), 8);
  if (!buffer) return false;
  std::memcpy(buffer, entries.data(), entries.size() * sizeof(AdvantageLedgerEntry));
  Store<void *>(side, 0x78, buffer);
  Store<std::int32_t>(side, 0x80, static_cast<std::int32_t>(entries.size()));
  Store<std::int32_t>(side, 0x84, static_cast<std::int32_t>(entries.size()));
  return true;
}

struct SourceArmy {
  const game::CombatArmyInputsSnapshot *input = nullptr;
  void *native = nullptr;
};

void AppendCanonicalInt32V3(std::string &output, std::int32_t value) {
  std::array<char, 16> buffer{};
  const auto [end, error] =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (error != std::errc{}) {
    throw std::runtime_error("candidate source integer serialization failed");
  }
  output.append(buffer.data(), end);
}

bool Sha256UpperV3(std::string_view input, std::string &output) {
  output.clear();
  if (input.size() > std::numeric_limits<ULONG>::max()) {
    return false;
  }
  BCRYPT_ALG_HANDLE algorithm = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  std::vector<std::uint8_t> object;
  std::array<std::uint8_t, 32> digest{};
  bool succeeded = false;
  do {
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM,
                                    nullptr, 0) < 0) {
      break;
    }
    DWORD object_size = 0;
    DWORD copied = 0;
    if (BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                          reinterpret_cast<PUCHAR>(&object_size),
                          sizeof(object_size), &copied, 0) < 0 ||
        object_size == 0 || copied != sizeof(object_size)) {
      break;
    }
    object.resize(object_size);
    if (BCryptCreateHash(algorithm, &hash, object.data(), object_size, nullptr,
                         0, 0) < 0 ||
        BCryptHashData(
            hash,
            reinterpret_cast<PUCHAR>(const_cast<char *>(input.data())),
            static_cast<ULONG>(input.size()), 0) < 0 ||
        BCryptFinishHash(hash, digest.data(),
                         static_cast<ULONG>(digest.size()), 0) < 0) {
      break;
    }
    succeeded = true;
  } while (false);
  if (hash != nullptr) {
    BCryptDestroyHash(hash);
  }
  if (algorithm != nullptr) {
    BCryptCloseAlgorithmProvider(algorithm, 0);
  }
  if (!succeeded) {
    return false;
  }
  constexpr char digits[] = "0123456789ABCDEF";
  output.resize(digest.size() * 2);
  for (std::size_t index = 0; index < digest.size(); ++index) {
    output[index * 2] = digits[digest[index] >> 4U];
    output[index * 2 + 1] = digits[digest[index] & 0x0FU];
  }
  return true;
}

bool CandidateSourceSequenceDigestV3(
    std::int32_t side_index,
    const std::vector<game::CombatPhaseCandidateSourceRowV3> &rows,
    std::string &output) {
  if (side_index < 0 || side_index > 1 ||
      rows.size() > static_cast<std::size_t>(65'536)) {
    return false;
  }
  std::string canonical;
  canonical.reserve(192 + rows.size() * 112);
  canonical += "{\"policy\":\"";
  canonical += "ccombat_side_commanders_then_knights_native_source_equivalence_v1";
  canonical += "\",\"side_index\":";
  AppendCanonicalInt32V3(canonical, side_index);
  canonical += ",\"ordered_sources\":[";
  for (std::size_t index = 0; index < rows.size(); ++index) {
    if (index != 0) {
      canonical += ',';
    }
    const auto &row = rows[index];
    if ((row.role != "commander" && row.role != "knight") ||
        row.source_army_id < 0 || row.character_id <= 0 ||
        (row.role == "commander" && row.source_regiment_id != -1) ||
        (row.role == "knight" && row.source_regiment_id <= 0)) {
      return false;
    }
    canonical += "{\"role\":\"";
    canonical += row.role;
    canonical += "\",\"source_army_id\":";
    AppendCanonicalInt32V3(canonical, row.source_army_id);
    canonical += ",\"source_regiment_id\":";
    if (row.source_regiment_id == -1) {
      canonical += "null";
    } else {
      AppendCanonicalInt32V3(canonical, row.source_regiment_id);
    }
    canonical += ",\"character_id\":";
    AppendCanonicalInt32V3(canonical, row.character_id);
    canonical += '}';
  }
  canonical += "]}";
  return Sha256UpperV3(canonical, output);
}


void *ResolveStored(void **slot, std::int32_t full_id,
                    std::size_t identity_offset) noexcept {
  if (!slot || !*slot || full_id < 0) return nullptr;
  void *storage = *slot;
  const auto index = static_cast<std::uint32_t>(full_id) & 0xFFFFFF;
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  if (capacity <= 0 || index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *rows = Load<void *>(storage, 0x20);
  void *object = rows ? Load<void *>(rows, static_cast<std::size_t>(index) * 0x10 + 8) : nullptr;
  return object && Load<std::int32_t>(object, identity_offset) == full_id ? object : nullptr;
}
void *ResolveEnvironmentArmy(void *context, std::int32_t id) noexcept {
  return ResolveStored(static_cast<CombatBindings *>(context)->army_internal_storage_slot, id, 0x10);
}
void *ResolveEnvironmentCharacter(void *context, std::int32_t id) noexcept {
  return ResolveStored(static_cast<CombatBindings *>(context)->character_storage_slot, id, 0x18);
}
void *ResolveEnvironmentRegiment(void *context, std::int32_t id) noexcept {
  return ResolveStored(static_cast<CombatBindings *>(context)->regiment_storage_slot, id, 0x10);
}
void *ResolveEnvironmentProvince(void *context, std::int32_t id) noexcept {
  const auto &bindings = *static_cast<CombatBindings *>(context);
  void *state = bindings.game_state_slot ? *bindings.game_state_slot : nullptr;
  void *data = state ? Load<void *>(state, 0xA0) : nullptr;
  if (!data || id <= 0 || id >= Load<std::int32_t>(data, 0x14C)) return nullptr;
  void *rows = Load<void *>(data, 0x140);
  void *province = rows ? Load<void *>(rows, static_cast<std::size_t>(id) * 8) : nullptr;
  return province && Load<std::int32_t>(province, 0x10) == id ? province : nullptr;
}
bool ReadEnvironmentGathering(void *context, std::int32_t id, bool &value) noexcept {
  void *army = ResolveEnvironmentArmy(context, id);
  if (!army) return false;
  // Native CCombat construction: 0x258664D/0x25866A2 read +0x1D0
  // and 0x2586657/0x25866AC store at each side +0x344.
  value = Load<std::int32_t>(army, 0x1D0) > 0;
  return true;
}

bool ValidateSideSources(void *side, const std::vector<SourceArmy> &armies,
                         const PhaseEnvironment &environment,
                         std::size_t side_index, NativeCombatPhaseSide &output,
                         std::string &unavailable_reason) {
  const auto fail = [&](std::string_view branch, std::string values) {
    unavailable_reason = "phase_native_candidate_source_unavailable:side=" +
        std::to_string(side_index) + ':' + std::string(branch) + ':' + values;
    return false;
  };
  void *ids = Load<void *>(side, 0x10);
  auto count = Load<std::int32_t>(side, 0x1C);
  auto capacity = Load<std::int32_t>(side, 0x18);
  if (!ids || count != static_cast<std::int32_t>(armies.size()) ||
      capacity < count || capacity > 65'536)
    return fail("army_header", "count=" + std::to_string(count) +
        ":expected=" + std::to_string(armies.size()) + ":capacity=" +
        std::to_string(capacity) + ":data_present=" + (ids ? "1" : "0"));
  for (std::size_t i = 0; i < armies.size(); ++i) {
    const auto &row = *armies[i].input;
    const auto observed_id = Load<std::int32_t>(ids, i * 4);
    if (observed_id != row.native_carmy_id)
      return fail("army_id", "index=" + std::to_string(i) + ":observed=" +
          std::to_string(observed_id) + ":expected=" + std::to_string(row.native_carmy_id));
    const auto observed_commander = Load<std::int32_t>(armies[i].native, 0x120);
    if (observed_commander != row.commander.character_id)
      return fail("commander", "army=" + std::to_string(row.army_id) +
          ":observed=" + std::to_string(observed_commander) + ":expected=" +
          std::to_string(row.commander.character_id));
    output.ordered_army_ids.push_back(row.army_id);
    if (row.commander.character_id != -1)
      output.ordered_candidates.push_back(
          {"commander", row.army_id, -1, row.commander.character_id});
  }
  void *entries = Load<void *>(side, 0x40);
  auto knight_count = Load<std::int32_t>(side, 0x4C);
  auto knight_capacity = Load<std::int32_t>(side, 0x48);
  if (knight_count < 0 || knight_count > 65'536 ||
      knight_capacity < knight_count || knight_capacity > 65'536 ||
      (knight_count && !entries))
    return fail("regiment_header", "count=" + std::to_string(knight_count) +
        ":capacity=" + std::to_string(knight_capacity) + ":data_present=" +
        (entries ? "1" : "0"));
  for (std::int32_t i = 0; i < knight_count; ++i) {
    const auto regiment = Load<std::int32_t>(entries,
                                            static_cast<std::size_t>(i) * 0x60 + 8);
    // Populate 0x264DF76 sends valid MAA and knights to the same +0x40 array.
    // Native knight source helper 0x1BA11D0 reads CArmyRegiment +0x148 and
    // 0x1BA11D6/0x1BA11D9 skips -1; the row is not necessarily a knight.
    void *native_regiment = environment.resolve_regiment ?
        environment.resolve_regiment(environment.context, regiment) : nullptr;
    const auto observed_regiment = native_regiment ?
        Load<std::int32_t>(native_regiment, 0x10) : -1;
    if (!native_regiment || observed_regiment != regiment)
      return fail("regiment_identity", "index=" + std::to_string(i) +
          ":regiment=" + std::to_string(regiment) + ":observed=" +
          std::to_string(observed_regiment) + ":rows=" + std::to_string(knight_count));
    const auto native_character = Load<std::int32_t>(native_regiment, 0x148);
    if (native_character == -1) continue;
    const game::CombatKnightSnapshot *match = nullptr;
    const game::CombatArmyInputsSnapshot *source_army = nullptr;
    for (const auto &army : armies) {
      if (!army.input->knights.available)
        return fail("knights_unavailable", "army=" + std::to_string(army.input->army_id));
      for (const auto &knight : army.input->knights.members) {
        if (knight.source_regiment_id != regiment) continue;
        if (match)
          return fail("knight_duplicate", "regiment=" + std::to_string(regiment));
        if (!knight.eligible || !knight.participant_army_membership_verified ||
            knight.army_id != army.input->native_carmy_id)
          return fail("knight_membership", "regiment=" + std::to_string(regiment) +
              ":army=" + std::to_string(knight.army_id) + ":expected=" +
              std::to_string(army.input->native_carmy_id) + ":eligible=" +
              (knight.eligible ? "1" : "0") + ":verified=" +
              (knight.participant_army_membership_verified ? "1" : "0"));
        if (knight.character_id <= 0 || knight.character_id != native_character)
          return fail("knight_character", "regiment=" + std::to_string(regiment) +
              ":observed=" + std::to_string(native_character) + ":expected=" +
              std::to_string(knight.character_id));
        match = &knight;
        source_army = army.input;
      }
    }
    if (!match)
      return fail("knight_unmatched", "index=" + std::to_string(i) +
          ":regiment=" + std::to_string(regiment) + ":character=" +
          std::to_string(native_character) + ":rows=" + std::to_string(knight_count));
    output.ordered_candidates.push_back(
        {"knight", source_army->army_id, regiment, match->character_id});
  }
  output.source_vector_equivalence = true;
  return true;
}
void AppendSigned(std::string &output, std::int64_t value) {
  std::array<char, 32> buffer{};
  const auto conversion =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (conversion.ec == std::errc{}) {
    output.append(buffer.data(), conversion.ptr);
  } else {
    output += '0';
  }
}

void AppendString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output += '\\';
      output += static_cast<char>(character);
    } else if (character < 0x20U) {
      output += "\\u00";
      output += hex[(character >> 4U) & 0x0FU];
      output += hex[character & 0x0FU];
    } else {
      output += static_cast<char>(character);
    }
  }
  output += '"';
}

void AppendNullableId(std::string &output, std::int32_t value) {
  if (value < 0) {
    output += "null";
  } else {
    AppendSigned(output, value);
  }
}

void AppendIdArray(std::string &output,
                   const std::vector<std::int32_t> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendSigned(output, values[index]);
  }
  output += ']';
}

void AppendStringArray(std::string &output,
                       const std::vector<std::string> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendString(output, values[index]);
  }
  output += ']';
}

void AppendNamedBools(std::string &output,
                      const std::vector<game::NamedBoolV3> &values) {
  output += '{';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendString(output, values[index].key);
    output += ':';
    output += values[index].value ? "true" : "false";
  }
  output += '}';
}

void AppendNamedSigned(std::string &output,
                       const std::vector<game::NamedSignedV3> &values) {
  output += '{';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendString(output, values[index].key);
    output += ':';
    AppendSigned(output, values[index].value);
  }
  output += '}';
}

void AppendOptionalId(std::string &output, const game::OptionalFullIdV3 &value) {
  output += "{\"status\":\"";
  output += value.present ? "available\",\"value\":"
                          : "absent\",\"value\":null}";
  if (value.present) {
    AppendSigned(output, value.value);
    output += '}';
  }
}

void AppendCharacter(std::string &output,
                     const game::CombatPhaseCharacterV3 &character) {
  output += "{\"character_id\":";
  AppendSigned(output, character.character_id);
  output += ",\"source_army_id\":";
  AppendSigned(output, character.source_army_id);
  output += ",\"source_regiment_id\":";
  AppendNullableId(output, character.source_regiment_id);
  output += ",\"encounter_role\":";
  AppendString(output, character.encounter_role);
  output += ",\"phase_roles\":";
  AppendStringArray(output, character.phase_roles);
  output += ",\"alive\":";
  output += character.alive ? "true" : "false";
  output += ",\"is_ai\":";
  output += character.is_ai ? "true" : "false";
  output += ",\"martial\":";
  AppendSigned(output, character.martial);
  output += ",\"learning\":";
  AppendSigned(output, character.learning);
  output += ",\"prowess\":";
  AppendSigned(output, character.prowess);
  output += ",\"traits_or_groups\":";
  AppendNamedBools(output, character.traits_or_groups);
  output += ",\"wounded_rank_raw\":";
  AppendSigned(output, character.wounded_rank_raw);
  output += ",\"fragile_bones_rank_raw\":";
  AppendSigned(output, character.fragile_bones_rank_raw);
  output += ",\"fragile_bones_xp_raw\":";
  AppendSigned(output, character.fragile_bones_xp_raw);
  output += ",\"lifestyle_blademaster_xp_raw\":";
  AppendSigned(output, character.lifestyle_blademaster_xp_raw);
  output += ",\"tourney_bow_xp_raw\":";
  AppendSigned(output, character.tourney_bow_xp_raw);
  output += ",\"tourney_foot_xp_raw\":";
  AppendSigned(output, character.tourney_foot_xp_raw);
  output += ",\"tourney_horse_xp_raw\":";
  AppendSigned(output, character.tourney_horse_xp_raw);
  output += ",\"house\":";
  AppendOptionalId(output, character.house);
  output += ",\"liege\":";
  AppendOptionalId(output, character.liege);
  output += ",\"liege_house\":";
  AppendOptionalId(output, character.liege_house);
  output += ",\"employer\":";
  AppendOptionalId(output, character.employer);
  output += ",\"dynasty\":";
  AppendOptionalId(output, character.dynasty);
  output += ",\"warfare_legacy_3\":";
  output += character.warfare_legacy_3 ? "true" : "false";
  output += ",\"stalwart_leader\":";
  output += character.stalwart_leader ? "true" : "false";
  output += ",\"culture\":";
  AppendOptionalId(output, character.culture);
  output += ",\"heritage_north_germanic\":";
  output += character.heritage_north_germanic ? "true" : "false";
  output += ",\"knights_slightly_more_prone_to_injury\":";
  output += character.knights_slightly_more_prone_to_injury ? "true"
                                                            : "false";
  output += ",\"blademaster_traits_more_common\":";
  output += character.blademaster_traits_more_common ? "true" : "false";
  output += ",\"innovations\":";
  AppendNamedBools(output, character.innovations);
  output += ",\"traditions\":";
  AppendNamedBools(output, character.traditions);
  output += ",\"culture_parameters\":";
  AppendNamedBools(output, character.culture_parameters);
  output += ",\"is_acclaimed\":";
  output += character.is_acclaimed ? "true" : "false";
  output += ",\"can_be_acclaimed\":";
  output += character.can_be_acclaimed ? "true" : "false";
  output += ",\"accolade\":";
  AppendOptionalId(output, character.accolade);
  output += ",\"accolade_has_men_at_arms_category\":";
  output += character.accolade_has_men_at_arms_category ? "true" : "false";
  output += ",\"accolade_parameters\":";
  AppendNamedBools(output, character.accolade_parameters);
  output += ",\"conqueror_variable_present\":";
  output += character.conqueror_variable_present ? "true" : "false";
  output += ",\"attribute_unlock_variables\":";
  AppendNamedBools(output, character.attribute_unlock_variables);
  output += ",\"hold_court_8050_knight\":";
  AppendOptionalId(output, character.hold_court_8050_knight);
  output += ",\"employer_hold_court_8050_promise\":";
  AppendOptionalId(output, character.employer_hold_court_8050_promise);
  output += ",\"liege_accolade_progress_raw\":";
  AppendSigned(output, character.liege_accolade_progress_raw);
  output += ",\"ai_extreme_conqueror_modifier\":";
  output += character.ai_extreme_conqueror_modifier ? "true" : "false";
  output += ",\"garuda_court_position\":";
  output += character.garuda_court_position ? "true" : "false";
  output += ",\"government_is_nomadic\":";
  output += character.government_is_nomadic ? "true" : "false";
  output += '}';
}

void AppendCharacters(std::string &output,
                      const std::vector<game::CombatPhaseCharacterV3> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendCharacter(output, values[index]);
  }
  output += ']';
}

void AppendArmies(std::string &output,
                   const std::vector<game::CombatPhaseArmyV3> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &army = values[index];
    output += "{\"army_id\":";
    AppendSigned(output, army.army_id);
    output += ",\"native_carmy_id\":";
    AppendSigned(output, army.native_carmy_id);
    output += ",\"encounter_role\":";
    AppendString(output, army.encounter_role);
    output += ",\"maa_regiment_count_raw\":";
    AppendSigned(output, army.maa_regiment_count_raw);
    output += ",\"maa_counts_raw\":";
    AppendNamedSigned(output, army.maa_counts_raw);
    output += '}';
  }
  output += ']';
}

void AppendCandidateSourceProof(
    std::string &output,
    const game::CombatPhaseCandidateSourceProofV3 &proof) {
  output += "{\"policy\":";
  AppendString(output, proof.policy);
  output += ",\"source_vector_equivalence\":";
  output += proof.source_vector_equivalence ? "true" : "false";
  output += ",\"sequence_sha256\":";
  AppendString(output, proof.sequence_sha256);
  output += ",\"ordered_sources\":[";
  for (std::size_t index = 0; index < proof.ordered_sources.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &source = proof.ordered_sources[index];
    output += "{\"role\":";
    AppendString(output, source.role);
    output += ",\"source_army_id\":";
    AppendSigned(output, source.source_army_id);
    output += ",\"source_regiment_id\":";
    AppendNullableId(output, source.source_regiment_id);
    output += ",\"character_id\":";
    AppendSigned(output, source.character_id);
    output += '}';
  }
  output += "]}";
}

void AppendSides(std::string &output,
                 const std::vector<game::CombatPhaseSideV3> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &side = values[index];
    output += "{\"side_index\":";
    AppendSigned(output, side.side_index);
    output += ",\"encounter_role\":";
    AppendString(output, side.encounter_role);
    output += ",\"ordered_army_ids\":";
    AppendIdArray(output, side.ordered_army_ids);
    output += ",\"ordered_character_ids\":";
    AppendIdArray(output, side.ordered_character_ids);
    output += ",\"ordered_commander_ids\":";
    AppendIdArray(output, side.ordered_commander_ids);
    output += ",\"ordered_knight_ids\":";
    AppendIdArray(output, side.ordered_knight_ids);
    output += ",\"primary_participant_character_id\":";
    AppendSigned(output, side.primary_participant_character_id);
    output += ",\"primary_source_army_id\":";
    AppendSigned(output, side.primary_source_army_id);
    output += ",\"commander_character_id\":";
    AppendNullableId(output, side.commander_character_id);
    output += ",\"side_strength_raw\":";
    AppendSigned(output, side.side_strength_raw);
    output += ",\"side_army_size_raw\":";
    AppendSigned(output, side.side_army_size_raw);
    output += ",\"candidate_source_proof\":";
    AppendCandidateSourceProof(output, side.candidate_source_proof);
    output += '}';
  }
  output += ']';
}

void AppendSupply(std::string &output,
                  const game::CombatAdvantageSupplyInputV3TestOnly &supply) {
  output += "{\"selected_key\":";
  AppendString(output, supply.selected_key);
  output += ",\"selected_effect_identity\":";
  AppendString(output, supply.selected_effect_identity);
  output += ",\"selected_effect_points\":";
  AppendSigned(output, supply.selected_effect_points);
  output += ",\"eligible_soldiers_total\":";
  AppendSigned(output, supply.eligible_soldiers_total);
  output += ",\"eligible_soldiers_supplied\":";
  AppendSigned(output, supply.eligible_soldiers_supplied);
  output += ",\"eligible_soldiers_running_low\":";
  AppendSigned(output, supply.eligible_soldiers_running_low);
  output += ",\"eligible_soldiers_starving\":";
  AppendSigned(output, supply.eligible_soldiers_starving);
  output += '}';
}

void AppendAdvantageSideInputs(
    std::string &output,
    const std::vector<game::CombatAdvantageSideInputV3TestOnly> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &side = values[index];
    output += "{\"side\":";
    AppendString(output, side.side);
    output += ",\"primary_army_id\":";
    AppendSigned(output, side.primary_army_id);
    output += ",\"ordered_army_ids\":";
    AppendIdArray(output, side.ordered_army_ids);
    output += ",\"supply\":";
    AppendSupply(output, side.supply);
    output += ",\"primary_army_gathering_raw\":";
    AppendSigned(output, side.primary_army_gathering_raw);
    output += ",\"owner_character_id\":";
    AppendSigned(output, side.owner_character_id);
    output += ",\"owner_debt_selector_raw\":";
    AppendSigned(output, side.owner_debt_selector_raw);
    output += ",\"treasury_debt_selector_raw\":";
    if (side.treasury_debt_selector_observable) {
      AppendSigned(output, side.treasury_debt_selector_raw);
    } else {
      output += "null";
    }
    output += '}';
  }
  output += ']';
}

void AppendConstructorSources(
    std::string &output,
    const std::vector<game::CombatAdvantageConstructorSourceV3TestOnly>
        &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &source = values[index];
    output += "{\"stage_order\":";
    AppendSigned(output, source.stage_order);
    output += ",\"append_order\":";
    AppendNullableId(output, source.append_order);
    output += ",\"stage\":";
    AppendString(output, source.stage);
    output += ",\"side\":";
    AppendString(output, source.side);
    output += ",\"source_key\":";
    if (source.selected) {
      AppendString(output, source.source_key);
    } else {
      output += "null";
    }
    output += ",\"effect_advantage_points\":";
    if (source.selected) {
      AppendSigned(output, source.effect_advantage_points);
    } else {
      output += "null";
    }
    output += ",\"scale_raw\":";
    AppendSigned(output, source.scale_raw);
    output += ",\"signed_contribution_raw\":";
    AppendSigned(output, source.signed_contribution_raw);
    output += ",\"accumulator_before_raw\":";
    AppendSigned(output, source.accumulator_before_raw);
    output += ",\"accumulator_after_raw\":";
    AppendSigned(output, source.accumulator_after_raw);
    output += ",\"selected\":";
    output += source.selected ? "true" : "false";
    output += ",\"applied\":";
    output += source.applied ? "true" : "false";
    output += ",\"skip_reason\":";
    if (source.applied) {
      output += "null";
    } else {
      AppendString(output, source.skip_reason);
    }
    output += '}';
  }
  output += ']';
}

void AppendResolvedSide(
    std::string &output,
    const game::CombatResolvedDynamicSideV3TestOnly &side) {
  output += "{\"side\":";
  AppendString(output, side.side);
  output += ",\"battle_commander_character_id\":";
  AppendNullableId(output, side.battle_commander_selected
                               ? side.battle_commander_character_id
                               : -1);
  output += ",\"battle_commander_selected\":";
  output += side.battle_commander_selected ? "true" : "false";
  output += ",\"battle_commander_selection\":\"native_0x264D790\"";
  output += ",\"primary_army_gathering_raw\":";
  AppendSigned(output, side.primary_army_gathering_raw);
  output += ",\"gathering\":";
  output += side.primary_army_gathering_raw > 0 ? "true" : "false";
  output += ",\"relation_kind_raw\":";
  AppendSigned(output, side.relation_kind_raw);
  output += ",\"roll_points\":";
  AppendSigned(output, side.roll_points);
  output += ",\"roll_raw\":";
  AppendSigned(output, side.roll_raw);
  output += ",\"target_conditionals_residual_raw\":";
  AppendSigned(output, side.target_conditionals_residual_raw);
  output += ",\"commander_dynamic_raw\":";
  AppendSigned(output, side.commander_dynamic_raw);
  output += ",\"side_dynamic_raw\":";
  AppendSigned(output, side.side_dynamic_raw);
  output += ",\"side_total_raw\":";
  AppendSigned(output, side.side_total_raw);
  output += ",\"contribution_to_resolved_raw\":";
  AppendSigned(output, side.contribution_to_resolved_raw);
  output += '}';
}


} // namespace

PhaseBindings BindPhaseImage(std::uintptr_t base, std::string_view hash) noexcept {
  PhaseBindings result{};
  if (!base || hash != kExecutableSha256) return result;
  result.enabled = true;
  result.construct_side = reinterpret_cast<ConstructPhaseSide>(base + kConstructPhaseSideRva);
  result.populate_side = reinterpret_cast<PopulatePhaseSide>(base + kPopulatePhaseSideRva);
  result.select_commander = reinterpret_cast<SelectPhaseCommander>(base + kSelectPhaseCommanderRva);
  result.refresh_strength = reinterpret_cast<RefreshPhaseStrength>(base + kRefreshPhaseStrengthRva);
  result.read_strength = reinterpret_cast<ReadPhaseStrength>(base + kReadPhaseStrengthRva);
  result.destroy_side = reinterpret_cast<DestroyPhaseSide>(base + kDestroyPhaseSideRva);
  result.resolve_advantage = reinterpret_cast<ResolvePhaseAdvantage>(base + kResolvePhaseAdvantageRva);
  result.read_dynamic = reinterpret_cast<ReadPhaseDynamic>(base + kReadPhaseDynamicRva);
  result.province_has_holding = reinterpret_cast<PhaseProvincePredicate>(base + kPhaseProvinceHasHoldingRva);
  result.combat = BindCombatImage(base, hash);
  result.traits = phase_character::BindImage(base, hash);
  result.definitions = BindPhaseDefinitionsImage(base, hash);
  result.image_base = base;
  result.culture = phase_culture::BindImage(base, hash);
  result.advantage = BindAdvantageImage(base, hash, result.combat);
  result.misc = BindPhaseMiscImage(base, hash);
  result.commander_dynamic = reinterpret_cast<PhaseCommanderDynamic>(base + kPhaseCommanderDynamicRva);
  result.side_modifier = reinterpret_cast<PhaseSideModifier>(base + kPhaseSideModifierRva);
  result.relation_kind = reinterpret_cast<PhaseRelationKind>(base + kPhaseRelationKindRva);
  result.combat_primary_vtable = base + kPhaseCombatPrimaryVtableRva;
  result.combat_secondary_vtable = base + kPhaseCombatSecondaryVtableRva;
  return result;
}

ReadNativeCombatPhaseResult ReadNativeCombatPhase(
    const PhaseBindings &bindings, const PhaseEnvironment &environment,
    const game::Snapshot &scope, const game::CombatSimulationInputsSnapshot &base,
    NativeCombatPhase &output) noexcept {
  output = {};
  if (!bindings.enabled || !bindings.construct_side || !bindings.populate_side ||
      !bindings.select_commander || !bindings.refresh_strength || !bindings.read_strength ||
      !bindings.destroy_side || !bindings.resolve_advantage || !bindings.read_dynamic ||
      !bindings.province_has_holding || !environment.resolve_internal_army ||
      !environment.resolve_character || !environment.resolve_province ||
      !environment.read_army_gathering) return ReadNativeCombatPhaseResult::unavailable;
  if (!scope.paused) return ReadNativeCombatPhaseResult::requires_paused;
  if (!scope.has_played_character || !scope.played_character_alive)
    return ReadNativeCombatPhaseResult::no_played_character;
  if (!base.input_observation_ready || base.armies.empty() ||
      base.scenario.attacker_army_ids.empty() || base.scenario.defender_army_ids.empty() ||
      !base.target_province.available ||
      !base.target_province.defender_context.available ||
      base.target_province.defender_context.holding_defender_status !=
          game::CombatObservationStatus::available)
    return ReadNativeCombatPhaseResult::base_inputs_unavailable;
  try {
    const auto fail = [&output](std::string_view reason) {
      output = {};
      output.unavailable_reason = reason;
      return ReadNativeCombatPhaseResult::native_phase_unavailable;
    };
    std::array<std::vector<SourceArmy>, 2> sources;
    std::array<bool, 2> gathering{};
    for (std::size_t side = 0; side < 2; ++side) {
      const auto &requested = side == 0 ? base.scenario.attacker_army_ids :
                                         base.scenario.defender_army_ids;
      if (requested.size() > 65'536) return fail("phase_army_count_unavailable");
      for (const auto id : requested) {
        const game::CombatArmyInputsSnapshot *input = nullptr;
        for (const auto &row : base.armies) {
          if (row.army_id != id) continue;
          if (input) return fail("phase_army_identity_unavailable");
          input = &row;
        }
        if (!input || !input->available || !input->native_carmy_id_observable ||
            input->native_carmy_id <= 0 || input->commander.status ==
            game::CombatObservationStatus::unavailable)
          return fail("phase_army_inputs_unavailable");
        void *army = environment.resolve_internal_army(environment.context, input->native_carmy_id);
        if (!army || Load<std::int32_t>(army, 0x10) != input->native_carmy_id ||
            Load<std::int32_t>(army, 0x124) != id)
          return fail("phase_native_army_unavailable");
        sources[side].push_back({input, army});
      }
      if (!environment.read_army_gathering(environment.context,
                                          sources[side].front().input->native_carmy_id,
                                          gathering[side]))
        return fail("phase_gathering_unavailable");
    }
    void *target = environment.resolve_province(environment.context, base.target_province_id);
    if (!target) return fail("phase_target_unavailable");
    LocalCombat local{};
    local.destroy = bindings.destroy_side;
    Store<std::uintptr_t>(local.shell.data(), 0, bindings.combat_primary_vtable);
    Store<std::int32_t>(local.shell.data(), 8, -1);
    Store<std::uint32_t>(local.shell.data(), 0x0C, 0x436F6D62);
    Store<std::uintptr_t>(local.shell.data(), 0x10, bindings.combat_secondary_vtable);
    Store<std::int32_t>(local.shell.data(), 0x18, -1);
    Store<void *>(local.shell.data(), 0x6B8, target);
    Store<std::uint8_t>(local.shell.data(), 0x6FC, 1);
    Store<std::uint8_t>(local.shell.data(), 0x6FD, bindings.province_has_holding(target) ? 1 : 0);
    Store<std::uint8_t>(local.shell.data(), 0x6FE,
                       base.target_province.defender_context.holding_defender ? 1 : 0);
    std::array<void *, 2> commanders{};
    for (std::size_t side = 0; side < 2; ++side) {
      void *object = local.side(side);
      if (bindings.construct_side(object, local.shell.data()) != object)
        return fail("phase_side_constructor_unavailable");
      ++local.constructed;
      if (Load<std::uint32_t>(object, 0x340) != 0x436F5369)
        return fail("phase_side_tag_unavailable");
      void *allocator = Load<void *>(object, 0x50);
      if (!allocator) return fail("phase_population_allocator_unavailable");
      Store<void *>(local.local[side].data(), 0x48, allocator);
      Store<void *>(object, 0xC8, local.local[side].data());
      for (const auto &army : sources[side]) bindings.populate_side(object, army.native);
      auto &row = output.sides[side];
      std::string source_reason;
      if (!ValidateSideSources(object, sources[side], environment, side, row, source_reason))
        return fail(source_reason);
      Store<std::uint8_t>(object, kPhaseGatheringOffset, gathering[side] ? 1 : 0);
      void *commander = bindings.select_commander(object);
      if (!commander) return fail("phase_commander_unavailable");
      row.commander_character_id = Load<std::int32_t>(commander, 0x18);
      commanders[side] = commander;
      if (row.commander_character_id != -1 &&
          environment.resolve_character(environment.context, row.commander_character_id) != commander)
        return fail("phase_commander_identity_unavailable");
      Store<std::int32_t>(object, 0x74, row.commander_character_id);
      Store<std::int32_t>(local.local[side].data(), 8, row.commander_character_id);
      row.primary_participant_character_id = Load<std::int32_t>(object, 0x70);
      row.army_size_raw = Load<std::int64_t>(object, 0xA8);
      bindings.refresh_strength(object);
    }
    NonReligiousAdvantagePlan plan{};
    if (bindings.advantage.enabled) {
      if (!BuildNonReligiousAdvantagePlan(bindings.advantage, environment, base, commanders, plan) ||
          !plan.nonreligious_available)
        return fail("phase_nonreligious_constructor_plan_unavailable:" +
                    (plan.unavailable_reason.empty() ? std::string("unspecified") :
                                                       plan.unavailable_reason));
      if (!AllocatePhaseLedger(local.side(0), plan.ledgers[0]) ||
          !AllocatePhaseLedger(local.side(1), plan.ledgers[1]))
        return fail("phase_constructor_ledger_allocation_unavailable");
      Store<std::int64_t>(local.shell.data(), 0x6C8, plan.model.base_static_accumulator_raw);
      Store<std::uint8_t>(local.shell.data(), 0x6FE, plan.holding_defender ? 1 : 0);
      output.nonreligious_constructor_ready = true;
      output.nonreligious_advantage_model = std::move(plan.model);
    }
    bindings.resolve_advantage(local.shell.data());
    for (std::size_t side = 0; side < 2; ++side) {
      auto &row = output.sides[side];
      row.strength_raw = bindings.read_strength(local.side(side));
      if (bindings.read_dynamic(local.shell.data(), &row.dynamic_advantage_raw,
                                static_cast<std::int32_t>(side), nullptr) !=
          &row.dynamic_advantage_raw)
        return fail("phase_dynamic_result_unavailable");
      if (Load<std::uint32_t>(local.side(side), 0x340) != 0x436F5369)
        return fail("phase_side_tag_changed");
    }
    const auto original_total = Load<std::int64_t>(local.shell.data(), 0x710);
    const auto constructor_total = Load<std::int64_t>(local.shell.data(), 0x6C8);
    const auto left = output.sides[0].dynamic_advantage_raw;
    const auto right = output.sides[1].dynamic_advantage_raw;
    if ((right > 0 && left < std::numeric_limits<std::int64_t>::min() + right) ||
        (right < 0 && left > std::numeric_limits<std::int64_t>::max() + right) ||
        ((left - right > 0 && constructor_total >
          std::numeric_limits<std::int64_t>::max() - (left - right)) ||
         (left - right < 0 && constructor_total <
          std::numeric_limits<std::int64_t>::min() - (left - right))) ||
        original_total != constructor_total + (left - right))
      return fail("phase_dynamic_resolution_mismatch");
    output.dynamic_advantage_at_zero_roll_raw = left - right;
    if (bindings.commander_dynamic && bindings.side_modifier && bindings.relation_kind) {
      auto &resolved = output.nonreligious_advantage_model.resolved_dynamic;
      resolved.side_0_dynamic_raw = left;
      resolved.side_1_dynamic_raw = right;
      resolved.resolved_advantage_at_zero_roll_raw = original_total;
      resolved.original_total_helper_raw = original_total;
      resolved.original_total_helper_match = true;
      for (std::size_t i = 0; i < 2; ++i) {
        game::CombatResolvedDynamicSideV3TestOnly row{};
        row.side = i == 0 ? "attacker" : "defender";
        row.battle_commander_character_id = output.sides[i].commander_character_id;
        row.battle_commander_selected = row.battle_commander_character_id != -1;
        row.relation_kind_raw = bindings.relation_kind(local.shell.data(), static_cast<std::int32_t>(i));
        row.primary_army_gathering_raw = Load<std::int32_t>(sources[i].front().native, 0x1D0);
        if (bindings.commander_dynamic(local.shell.data(), &row.commander_dynamic_raw,
                                       commanders[i], static_cast<std::int32_t>(i),
                                       row.relation_kind_raw, nullptr) != &row.commander_dynamic_raw ||
            bindings.side_modifier(local.shell.data(), &row.side_dynamic_raw,
                                   static_cast<std::byte *>(local.side(i)) + 0x110,
                                   static_cast<std::int32_t>(i), row.relation_kind_raw,
                                   nullptr) != &row.side_dynamic_raw)
          return fail("phase_dynamic_component_unavailable");
        row.side_total_raw = output.sides[i].dynamic_advantage_raw;
        row.target_conditionals_residual_raw = row.side_total_raw - row.commander_dynamic_raw - row.side_dynamic_raw;
        row.contribution_to_resolved_raw = i == 0 ? row.side_total_raw : -row.side_total_raw;
        resolved.sides.push_back(std::move(row));
      }
    }
    if (!local.cleanup()) return fail("phase_population_cleanup_unavailable");
    output.available = true;
    return ReadNativeCombatPhaseResult::available;
  } catch (...) {
    output = {};
    return ReadNativeCombatPhaseResult::unavailable;
  }
}

bool ReadContextualAdvantageInputs(
    const PhaseBindings &bindings, const game::Snapshot &scope,
    const game::CombatSimulationInputsSnapshot &base,
    game::ContextualAdvantageSnapshot &output) noexcept {
  output = {};
  output.attempted = true;
  output.target_province_id = base.target_province_id;
  try {
    const auto fail = [&](std::string reason) {
      output = {};
      output.attempted = true;
      output.target_province_id = base.target_province_id;
      output.unavailable_reason = "contextual_advantage:" + std::move(reason);
      return false;
    };
    if (!bindings.advantage.enabled || !bindings.commander_dynamic ||
        !bindings.side_modifier || !bindings.relation_kind)
      return fail("nonreligious_context_bindings_unavailable");
    PhaseEnvironment environment{const_cast<CombatBindings *>(&bindings.combat),
                                 ResolveEnvironmentArmy, ResolveEnvironmentCharacter,
                                 ResolveEnvironmentProvince, ReadEnvironmentGathering,
                                 ResolveEnvironmentRegiment};
    NativeCombatPhase native{};
    const auto result = ReadNativeCombatPhase(bindings, environment, scope, base, native);
    if (result != ReadNativeCombatPhaseResult::available) {
      std::string reason = native.unavailable_reason;
      if (reason.empty()) {
        switch (result) {
        case ReadNativeCombatPhaseResult::requires_paused: reason = "requires_paused"; break;
        case ReadNativeCombatPhaseResult::no_played_character: reason = "no_played_character"; break;
        case ReadNativeCombatPhaseResult::base_inputs_unavailable: reason = "base_inputs_unavailable"; break;
        default: reason = "native_phase_unavailable"; break;
        }
      }
      return fail(std::move(reason));
    }
    const auto &model = native.nonreligious_advantage_model;
    const auto &resolved = model.resolved_dynamic;
    if (!native.available || !native.nonreligious_constructor_ready ||
        resolved.sides.size() != 2 || !resolved.original_total_helper_match)
      return fail("nonreligious_context_components_unavailable");
    for (std::size_t i = 0; i < 2; ++i) {
      const auto &dynamic = resolved.sides[i];
      game::ContextualAdvantageSideSnapshot side{};
      side.side_index = static_cast<std::int32_t>(i);
      side.ordered_public_cunit_ids = native.sides[i].ordered_army_ids;
      side.selected_commander_character_id = native.sides[i].commander_character_id;
      side.relation_kind_raw = dynamic.relation_kind_raw;
      side.commander_dynamic_raw = dynamic.commander_dynamic_raw;
      side.side_dynamic_raw = dynamic.side_dynamic_raw;
      side.target_conditionals_residual_raw = dynamic.target_conditionals_residual_raw;
      side.side_total_raw = dynamic.side_total_raw;
      output.sides.push_back(std::move(side));
    }
    output.base_nonreligious_accumulator_raw = model.base_static_accumulator_raw;
    output.synthetic_zero_roll_total_raw = resolved.original_total_helper_raw;
    output.synthetic_helper_total_match = resolved.original_total_helper_match;
    output.available = true;
    return true;
  } catch (...) {
    output = {};
    output.attempted = true;
    output.target_province_id = base.target_province_id;
    output.unavailable_reason = "contextual_advantage:read_exception";
    return false;
  }
}

game::ReadCombatSimulationInputsV3Result ReadCombatPhaseInputs(
    const PhaseBindings &bindings, const PhaseEnvironment &environment,
    const game::Snapshot &scope, const game::CombatSimulationInputsSnapshot &base,
    game::CombatPhaseInputsV3 &output) noexcept {
  output = {};
  using Result = game::ReadCombatSimulationInputsV3Result;
  if (!bindings.enabled) return Result::unavailable;
  if (!scope.paused) return Result::requires_paused;
  if (!scope.has_played_character || !scope.played_character_alive) return Result::no_played_character;
  if (!base.input_observation_ready) return Result::base_inputs_unavailable;
  try {
    NonReligiousPhaseOperands observed{};
    const bool ready = ReadNonReligiousPhaseOperands(bindings, environment, scope, base, observed);
    output = std::move(observed.fields);
    output.available = false;
    output.unavailable_reason = ready ? "phase_religion_and_rites_implementation_pending" :
        "phase_nonreligious_operand_unavailable:" +
        (observed.failed_domains.empty() ? std::string("unspecified") : observed.failed_domains.front());
    return Result::phase_inputs_unavailable;
  } catch (...) {
    output = {};
    return Result::unavailable;
  }
}

game::ReadCombatSimulationInputsV3Result ReadCombatSimulationInputsV3(
    const PhaseBindings &bindings, const game::Snapshot &scope,
    const game::CombatSimulationInputsRequest &request,
    game::CombatSimulationInputsV3Snapshot &output) noexcept {
  output = {};
  using Result = game::ReadCombatSimulationInputsV3Result;
  const auto result = ReadCombatSimulationInputs(bindings.combat, scope, request,
                                                 output.base_inputs);
  switch (result) {
  case game::ReadCombatSimulationInputsResult::requires_paused: return Result::requires_paused;
  case game::ReadCombatSimulationInputsResult::no_played_character: return Result::no_played_character;
  case game::ReadCombatSimulationInputsResult::invalid_arguments: return Result::invalid_arguments;
  case game::ReadCombatSimulationInputsResult::target_province_not_found: return Result::target_province_not_found;
  case game::ReadCombatSimulationInputsResult::army_not_in_scope: return Result::army_not_in_scope;
  case game::ReadCombatSimulationInputsResult::invalid_encounter: return Result::invalid_encounter;
  case game::ReadCombatSimulationInputsResult::partial: return Result::base_inputs_unavailable;
  case game::ReadCombatSimulationInputsResult::unavailable: return Result::unavailable;
  case game::ReadCombatSimulationInputsResult::available: break;
  }
  PhaseEnvironment environment{const_cast<CombatBindings *>(&bindings.combat),
                               ResolveEnvironmentArmy, ResolveEnvironmentCharacter,
                               ResolveEnvironmentProvince, ReadEnvironmentGathering,
                               ResolveEnvironmentRegiment};
  return ReadCombatPhaseInputs(bindings, environment, scope, output.base_inputs,
                              output.phase_event_inputs);
}

bool ReadNonReligiousPhaseOperands(
    const PhaseBindings &bindings, const PhaseEnvironment &environment,
    const game::Snapshot &scope, const game::CombatSimulationInputsSnapshot &base,
    NonReligiousPhaseOperands &output) noexcept {
  output = {};
  try {
    const auto native_result = ReadNativeCombatPhase(bindings, environment, scope, base,
                                                     output.native_sides);
    if (native_result != ReadNativeCombatPhaseResult::available) {
      std::string reason = output.native_sides.unavailable_reason;
      if (reason.empty()) {
        switch (native_result) {
        case ReadNativeCombatPhaseResult::requires_paused: reason = "phase_requires_paused"; break;
        case ReadNativeCombatPhaseResult::no_played_character: reason = "phase_no_played_character"; break;
        case ReadNativeCombatPhaseResult::base_inputs_unavailable: reason = "phase_base_inputs_unavailable"; break;
        case ReadNativeCombatPhaseResult::unavailable: reason = "phase_bindings_environment_or_exception_unavailable"; break;
        default: reason = "phase_native_unavailable"; break;
        }
      }
      output.failed_domains.push_back("native_sides:" + reason);
      output.fields.unavailable_reason = "phase_nonreligious_operand_unavailable:" +
                                        output.failed_domains.back();
      return false;
    }
    output.completed_domains.push_back("native_sides");
    for (std::size_t i = 0; i < 2; ++i) {
      const auto &native = output.native_sides.sides[i];
      game::CombatPhaseSideV3 side{};
      side.side_index = static_cast<std::int32_t>(i);
      side.encounter_role = i == 0 ? "attacker" : "defender";
      side.ordered_army_ids = native.ordered_army_ids;
      side.primary_participant_character_id = native.primary_participant_character_id;
      side.primary_source_army_id = native.ordered_army_ids.front();
      side.commander_character_id = native.commander_character_id;
      side.side_strength_raw = native.strength_raw;
      side.side_army_size_raw = native.army_size_raw;
      side.candidate_source_proof.ordered_sources = native.ordered_candidates;
      if (!CandidateSourceSequenceDigestV3(static_cast<std::int32_t>(i),
                                           native.ordered_candidates,
                                           side.candidate_source_proof.sequence_sha256)) {
        output.failed_domains.push_back("candidate_source_digest"); return false;
      }
      side.candidate_source_proof.source_vector_equivalence = native.source_vector_equivalence;
      for (const auto &source : native.ordered_candidates) {
        if (source.role == "commander") side.ordered_commander_ids.push_back(source.character_id);
        else side.ordered_knight_ids.push_back(source.character_id);
        auto found = std::find_if(output.fields.characters.begin(), output.fields.characters.end(),
                                 [&source](const auto &row) {
          return row.character_id == source.character_id && row.source_army_id == source.source_army_id;
        });
        if (found != output.fields.characters.end()) {
          if (found->source_regiment_id != -1 || source.role != "knight") {
            output.failed_domains.push_back("candidate_role_merge"); return false;
          }
          found->source_regiment_id = source.source_regiment_id;
          found->phase_roles.push_back("knight");
        } else {
          game::CombatPhaseCharacterV3 row{};
          row.character_id = source.character_id;
          row.source_army_id = source.source_army_id;
          row.source_regiment_id = source.source_regiment_id;
          row.encounter_role = side.encounter_role;
          row.phase_roles = {source.role};
          output.fields.characters.push_back(std::move(row));
          side.ordered_character_ids.push_back(source.character_id);
        }
      }
      output.fields.sides.push_back(std::move(side));
    }
    // DTO roster order is per v2 army (commander, then that army's knights).
    // The native candidate proof intentionally keeps its different ordering:
    // all commanders, then all knights within each CCombatSide.
    std::vector<game::CombatPhaseCharacterV3> ordered_characters;
    ordered_characters.reserve(output.fields.characters.size());
    for (const auto &army : base.armies) {
      for (auto &character : output.fields.characters) {
        if (character.source_army_id == army.army_id)
          ordered_characters.push_back(std::move(character));
      }
    }
    if (ordered_characters.size() != output.fields.characters.size()) {
      output.failed_domains.push_back("candidate_roster_army_order"); return false;
    }
    output.fields.characters = std::move(ordered_characters);
    for (auto &side : output.fields.sides) {
      side.ordered_character_ids.clear();
      for (const auto &character : output.fields.characters) {
        if (character.encounter_role == side.encounter_role)
          side.ordered_character_ids.push_back(character.character_id);
      }
    }
    bool traits_ready = bindings.traits.enabled;
    for (auto &character : output.fields.characters) {
      void *object = environment.resolve_character(environment.context, character.character_id);
      if (!object || !phase_character::ReadPhaseCharacterIdentityTraits(bindings.traits,
                                                                       object, character))
        traits_ready = false;
    }
    (traits_ready ? output.completed_domains : output.failed_domains).push_back("identity_traits_tracks");
    bool culture_ready = bindings.culture.enabled;
    std::string culture_failure;
    for (auto &character : output.fields.characters) {
      void *object = environment.resolve_character(environment.context, character.character_id);
      std::string leaf_reason;
      const bool observed = object && phase_culture::ReadPhaseCharacterCultureRelations(
          bindings.culture, object, character, &leaf_reason);
      if (!observed) {
        culture_ready = false;
        if (culture_failure.empty()) {
          culture_failure = "culture_relations_perks:character=" +
              std::to_string(character.character_id) + ':' +
              (!object ? std::string("native_character_unavailable") :
               leaf_reason.empty() ? std::string("culture_operand_unavailable") : leaf_reason);
        }
      }
    }
    (culture_ready ? output.completed_domains : output.failed_domains).push_back(
        culture_ready ? "culture_relations_perks" :
        culture_failure.empty() ? "culture_relations_perks:bindings_unavailable" : culture_failure);
    PhaseMiscDefinitionContext misc_definitions{};
    bool misc_ready = BuildPhaseMiscDefinitions(bindings.misc, misc_definitions);
    if (misc_ready) {
      for (auto &character : output.fields.characters) {
        void *object = environment.resolve_character(environment.context, character.character_id);
        if (!object || !ReadPhaseCharacterMisc(bindings.misc, misc_definitions, object, character))
          misc_ready = false;
      }
    }
    (misc_ready ? output.completed_domains : output.failed_domains).push_back("variables_accolade_government_court");
    PhaseDifficulty difficulty{};
    if (ReadPhaseDifficulty(bindings.definitions, difficulty)) {
      output.fields.easy_difficulty = difficulty.easy;
      output.fields.very_easy_difficulty = difficulty.very_easy;
      output.completed_domains.push_back("difficulty_rules");
    } else output.failed_domains.push_back("difficulty_rules");
    auto definitions = bindings.definitions;
    definitions.regiment_context = environment.context;
    definitions.resolve_regiment = environment.resolve_regiment;
    bool armies_ready = true;
    for (const auto &army : base.armies) {
      game::CombatPhaseArmyV3 row{};
      if (!ReadPhaseArmyMaa(definitions, army, row)) armies_ready = false;
      else output.fields.armies.push_back(std::move(row));
    }
    (armies_ready ? output.completed_domains : output.failed_domains).push_back("army_maa_counts");
    (output.native_sides.nonreligious_constructor_ready ? output.completed_domains :
        output.failed_domains).push_back("nonreligious_constructor_ledger");
    (output.native_sides.nonreligious_advantage_model.resolved_dynamic.original_total_helper_match &&
       output.native_sides.nonreligious_advantage_model.resolved_dynamic.sides.size() == 2 ?
       output.completed_domains : output.failed_domains).push_back("resolved_dynamic_components");
    output.fields.advantage_model = output.native_sides.nonreligious_advantage_model;
    output.non_religious_ready = output.failed_domains.empty();
    output.fields.unavailable_reason = output.non_religious_ready ?
        "phase_religion_and_rites_implementation_pending" :
        "phase_nonreligious_operand_unavailable:" + output.failed_domains.front();
    return output.non_religious_ready;
  } catch (...) {
    output = {};
    output.failed_domains.push_back("native_phase_operands_exception");
    return false;
  }
}

std::string SerializeCombatPhaseInputsV3(const game::CombatPhaseInputsV3 &inputs) {
  // Internal diagnostic only. Field values and new-build provenance remain
  // reviewable while the complete v3 capability is absent from production.
  std::string output;
  output.reserve(32'768);
  output += "{\"status\":\"unavailable\",\"game_version\":\"1.20.0.2\",\"executable_sha256\":";
  AppendString(output, kExecutableSha256);
  output += ",\"contract_stage\":";
  AppendString(output, kPhaseContractStage);
  output += ",\"source_delta_sha256\":";
  AppendString(output, kPhaseSourceDeltaSha256);
  output += ",\"nonreligious_ast_sha256\":";
  AppendString(output, kPhaseNonReligiousAstSha256);
  output += ",\"nonreligious_ast_source_ready\":true,\"ast_source_counts\":{\"event_rows\":";
  AppendSigned(output, kPhaseAstEventRows);
  output += ",\"source_definitions\":";
  AppendSigned(output, kPhaseAstSourceDefinitions);
  output += ",\"deferred_opaque_nodes\":";
  AppendSigned(output, kPhaseAstDeferredOpaqueNodes);
  output += "},\"complete_phase_inputs_ready\":false,\"current_build_ast_ready\":false,"
            "\"deferred_domains\":[\"religion_and_rites\"],\"nonreligious_fields_ready\":";
  output += inputs.unavailable_reason == "phase_religion_and_rites_implementation_pending" ? "true" : "false";
  output += ",\"nonreligious_fields\":{\"characters\":";
  AppendCharacters(output, inputs.characters);
  output += ",\"armies\":";
  AppendArmies(output, inputs.armies);
  output += ",\"sides\":";
  AppendSides(output, inputs.sides);
  output += ",\"game_rules\":{\"easy_difficulty\":";
  output += inputs.easy_difficulty ? "true" : "false";
  output += ",\"very_easy_difficulty\":";
  output += inputs.very_easy_difficulty ? "true" : "false";
  output += "}},\"nonreligious_advantage_model\":{\"complete_advantage_model_ready\":false,"
            "\"scale\":100000,\"observation_origin\":";
  const auto &model = inputs.advantage_model;
  AppendString(output, model.observation_origin);
  output += ",\"constructor_sources\":";
  AppendConstructorSources(output, model.constructor_sources);
  output += ",\"side_inputs\":";
  AppendAdvantageSideInputs(output, model.side_inputs);
  output += ",\"base_static_accumulator_raw\":";
  AppendSigned(output, model.base_static_accumulator_raw);
  output += ",\"resolved_dynamic\":{\"context_mode\":\"temporary_unregistered_local_context\","
            "\"roll_policy\":\"zero_in_query_sampled_offline\",\"sides\":[";
  const auto &dynamic = model.resolved_dynamic;
  for (std::size_t index = 0; index < dynamic.sides.size(); ++index) {
    if (index != 0) output += ',';
    AppendResolvedSide(output, dynamic.sides[index]);
  }
  output += "],\"side_0_dynamic_raw\":";
  AppendSigned(output, dynamic.side_0_dynamic_raw);
  output += ",\"side_1_dynamic_raw\":";
  AppendSigned(output, dynamic.side_1_dynamic_raw);
  output += ",\"resolved_advantage_at_zero_roll_raw\":";
  AppendSigned(output, dynamic.resolved_advantage_at_zero_roll_raw);
  output += ",\"original_total_helper_raw\":";
  AppendSigned(output, dynamic.original_total_helper_raw);
  output += ",\"original_total_helper_match\":";
  output += dynamic.original_total_helper_match ? "true" : "false";
  output += "}},\"unavailable_reason\":";
  AppendString(output, inputs.unavailable_reason);
  output += '}';
  return output;
}

std::string SerializeNonReligiousPhaseOperands(const NonReligiousPhaseOperands &inputs) {
  std::string output = "{\"nonreligious_ready\":";
  output += inputs.non_religious_ready ? "true" : "false";
  output += ",\"completed_domains\":";
  AppendStringArray(output, inputs.completed_domains);
  output += ",\"failed_domains\":";
  AppendStringArray(output, inputs.failed_domains);
  output += ",\"deferred_domains\":";
  AppendStringArray(output, inputs.deferred_domains);
  output += ",\"phase_diagnostic\":";
  output += SerializeCombatPhaseInputsV3(inputs.fields);
  output += '}';
  return output;
}
} // namespace xar::ck3_12002
